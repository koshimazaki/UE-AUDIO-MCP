#!/usr/bin/env python3
"""Export verified knowledge catalogues to JSON files.

Regenerates catalogue JSONs from in-memory Python data (the single source of truth).
Both files are human-readable, git-trackable, and loadable by seed.py / blueprint_scraped.py.

Usage:
    python scripts/export_catalogues.py              # export both
    python scripts/export_catalogues.py --ms-only    # MetaSounds only
    python scripts/export_catalogues.py --bp-only    # Blueprint only
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Ensure package is importable when running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ue_audio_mcp.knowledge.metasound_nodes import (
    CLASS_NAME_TO_DISPLAY,
    METASOUND_NODES,
)
from ue_audio_mcp.knowledge.blueprint_audio import BLUEPRINT_AUDIO_FUNCTIONS


# -- Paths -------------------------------------------------------------------
_KNOWLEDGE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "src", "ue_audio_mcp", "knowledge",
)
MS_CATALOGUE_PATH = os.path.join(_KNOWLEDGE_DIR, "metasound_catalogue.json")
BP_CATALOGUE_PATH = os.path.join(_KNOWLEDGE_DIR, "blueprint_audio_catalogue.json")


# -- MCP notes per category --------------------------------------------------
_MS_CATEGORY_NOTES: dict[str, str] = {
    "Generators": "Use as audio source in MetaSounds layer. Trigger from Blueprint events, expose Frequency as graph input for BP SetFloatParameter.",
    "Wave Players": "Sample playback node. Wire WaveAsset from graph input, trigger Play from Blueprint. Use Mono for 3D, Stereo for music/ambience.",
    "Envelopes": "Shape amplitude/parameter over time. Trigger pin connects to Blueprint events. Use Audio variant for audio-rate modulation, Float for control-rate.",
    "Filters": "Chain after generators. Wire cutoff/resonance from BP params via SetFloatParameter. Use Biquad for general EQ, Ladder for resonant synth.",
    "Effects": "Chain after generators/filters. Expose mix/feedback params to Blueprint for runtime control. Route wet signal to Wwise via AudioLink.",
    "Dynamics": "Compressor/limiter for loudness management. Place before final output. Expose threshold as BP param for adaptive mixing.",
    "Math": "Arithmetic on audio/float signals. Use Multiply for volume control, Add for mixing, MapRange for parameter scaling from BP values.",
    "Mix": "Combine multiple audio streams. Use Stereo Mixer for L/R panning, Mono Mixer for summing layers before effects chain.",
    "Spatialization": "3D positioning nodes. ITD Panner for binaural, Stereo Panner for simple L/R. Wire azimuth/elevation from BP actor transforms.",
    "Music": "MIDI/pitch utilities. Convert MIDI note numbers from BP Int32 params to Hz. Use BPM To Seconds for tempo-synced timing.",
    "Triggers": "Event routing and timing. Trigger Repeat for looping patterns, Trigger Route for surface-type switching from BP enums.",
    "Random": "Variation and randomization. Random Get for round-robin sample selection, Random Float for pitch/timing humanization.",
    "Converters": "Type conversion between Audio/Float/Int32/Time/Bool. Essential glue between different signal types in the graph.",
    "Interpolation": "Smooth parameter transitions. InterpTo for gradual value changes, Crossfade for blending between sources.",
    "Gain": "Volume control with dB scaling. Place in signal chain for level management. Wire gain from BP float param.",
    "Utility": "Analysis and routing nodes. Envelope Follower for sidechain, Audio To Float for metering back to Blueprint.",
    "SID Chip": "ReSID-based C64 sound emulation. 3-voice + filter. Wire gate triggers and frequencies from Blueprint for chiptune synthesis.",
}

_MS_NODE_NOTES: dict[str, str] = {
    "Sine": "Pure tone, ideal for UI beeps and FM carrier. Wire Frequency from BP SetFloatParameter.",
    "Saw": "Bright subtractive synth source. Chain with filter for classic analog sound.",
    "Square": "Hollow synth tone. Pulse Width for PWM from BP param. Good for chiptune and bass.",
    "SuperOscillator": "Multi-voice unison. Use for thick pads/leads. Wire Voices+Detune from BP for morphing.",
    "Wave Player (Mono)": "Primary sample player. Use for one-shot SFX (gunshots, footsteps). Mono for 3D spatialization.",
    "Wave Player (Stereo)": "Stereo sample player. Use for music, ambience. Not spatializable -- use for non-positional audio.",
    "AD Envelope (Audio)": "Percussive envelope -- no sustain. Ideal for hits, transients. Trigger from BP events.",
    "ADSR Envelope (Audio)": "Full ADSR for sustained sounds. Gate trigger from BP, expose Attack/Release as params.",
    "Biquad Filter": "Versatile 2nd-order filter. Wire Type+Frequency+Gain from BP for runtime EQ control.",
    "Ladder Filter": "Resonant 4-pole filter. Classic synth sound. Wire cutoff from BP for filter sweeps.",
    "State Variable Filter": "Multi-mode filter (LP/HP/BP/Notch). Wire mode select from BP enum param.",
    "Dynamic Filter": "Filter with audio-rate cutoff input. Use for envelope-following or LFO modulation.",
    "Delay (Audio)": "Echo/delay effect. Expose DelayTime+Feedback to BP for runtime delay control.",
    "Stereo Delay": "Ping-pong delay. Use for stereo width on ambience/music layers.",
    "Freeverb (Stereo)": "Algorithmic reverb. Use before AudioLink bridge to Wwise for pre-reverb.",
    "ITD Panner": "Binaural panner with interaural time difference. Wire Angle from BP actor azimuth.",
    "Stereo Panner": "Simple L/R panning. Wire Pan from BP for positional audio.",
    "Trigger Repeat": "Looping trigger generator. Use for rhythmic patterns, ambient loops.",
    "Trigger Route": "Route triggers by index. Use for surface-type switching (footsteps) from BP Int32.",
    "Random Get (Audio)": "Round-robin random selection. Use for variation (multiple gunshot layers).",
    "MIDI To Frequency": "Convert MIDI note (Int32) to Hz (Float). Wire from BP for musical pitch control.",
    "Crossfade": "Blend between two audio sources. Wire blend factor from BP for state transitions.",
    "InterpTo (Float)": "Smoothly interpolate to target value. Use for parameter smoothing from BP changes.",
    "Compressor": "Dynamic range control. Place before output for loudness management.",
    "LFO": "Low-frequency modulation source. Route to filter cutoff or volume for movement.",
    "Envelope Follower (Utility)": "Track amplitude of audio signal. Send back to BP via output for sidechain.",
    "Send To Audio Bus": "Route audio to UE submix bus. Connect to AudioLink for Wwise routing.",
}


def _reverse_class_name_map() -> dict[str, str]:
    """Build display_name -> class_name mapping (first match wins)."""
    rev: dict[str, str] = {}
    for cn, dn in CLASS_NAME_TO_DISPLAY.items():
        if dn not in rev:
            rev[dn] = cn
    return rev


def export_metasound_catalogue() -> str:
    """Export MetaSounds catalogue to JSON. Returns path."""
    display_to_class = _reverse_class_name_map()

    nodes = []
    for name, node in sorted(METASOUND_NODES.items()):
        entry = {
            "name": name,
            "category": node["category"],
            "description": node["description"],
            "inputs": node["inputs"],
            "outputs": node["outputs"],
            "tags": node["tags"],
            "complexity": node.get("complexity", 1),
        }
        # Add class_name if we have a mapping
        cn = display_to_class.get(name)
        if cn:
            entry["class_name"] = cn

        # Add MCP notes: node-specific first, then category fallback
        note = _MS_NODE_NOTES.get(name) or _MS_CATEGORY_NOTES.get(node["category"])
        if note:
            entry["mcp_notes"] = note

        nodes.append(entry)

    catalogue = {
        "_meta": {
            "description": "Verified MetaSounds node catalogue -- generated from metasound_nodes.py",
            "node_count": len(nodes),
            "categories": sorted(set(n["category"] for n in nodes)),
            "source": "scripts/export_catalogues.py",
        },
        "nodes": nodes,
    }

    with open(MS_CATALOGUE_PATH, "w", encoding="utf-8") as f:
        json.dump(catalogue, f, indent=2, ensure_ascii=False)

    return MS_CATALOGUE_PATH


def export_blueprint_catalogue() -> str:
    """Export Blueprint audio catalogue to JSON. Returns path."""

    # -- Functions --
    functions = []
    for name, func in sorted(BLUEPRINT_AUDIO_FUNCTIONS.items()):
        entry = {
            "name": name,
            "class_name": func["category"],
            "description": func["description"],
            "params": func.get("params", []),
            "returns": func.get("returns"),
            "tags": func.get("tags", []),
        }
        functions.append(entry)

    # -- Events --
    events = [
        {"name": "BeginPlay", "description": "Called when actor starts playing. Use for audio component setup and initial sound triggers.",
         "mcp_notes": "Common starting point for audio initialization. Spawn AudioComponents here."},
        {"name": "EndPlay", "description": "Called when actor is destroyed or level unloads. Use for cleanup.",
         "mcp_notes": "Stop all sounds and release AudioComponent references."},
        {"name": "BeginOverlap", "description": "Triggered when actor enters collision volume. Use for zone-based audio.",
         "mcp_notes": "Wire to SetRTPCValue or PostEvent for ambient zone transitions."},
        {"name": "EndOverlap", "description": "Triggered when actor exits collision volume.",
         "mcp_notes": "Fade out zone audio, reset RTPC values."},
        {"name": "OnAudioPlaybackPercent", "description": "Fires at playback percentage milestones.",
         "mcp_notes": "Use for syncing visuals to audio progress."},
        {"name": "OnAudioFinished", "description": "Fires when audio component finishes playback.",
         "mcp_notes": "Chain to next sound or trigger gameplay event."},
        {"name": "OnAudioMultiEnvelopeValue", "description": "Returns envelope value during playback for amplitude tracking.",
         "mcp_notes": "Wire to visual effects for audio-reactive gameplay."},
        {"name": "OnQuartzMetronomeEvent", "description": "Fires on Quartz clock beat/bar boundaries.",
         "mcp_notes": "Use for music-synced gameplay actions and audio quantization."},
        {"name": "OnSubmixSpectralAnalysis", "description": "Returns spectral analysis data from submix.",
         "mcp_notes": "Use for frequency-reactive visuals or adaptive audio."},
        {"name": "Tick", "description": "Called every frame. Use sparingly for continuous audio parameter updates.",
         "mcp_notes": "Wire distance calculations to SetFloatParameter for continuous spatial audio."},
    ]

    # -- Categories --
    categories = [
        {"name": "Audio|Playback", "description": "Sound playback functions (Play, Spawn, Stop)"},
        {"name": "Audio|Parameters", "description": "MetaSounds parameter setting (SetFloat/Int/Bool/TriggerParameter)"},
        {"name": "Audio|Components", "description": "AudioComponent lifecycle (Create, Attach, Destroy)"},
        {"name": "Audio|Volume", "description": "Volume and fade control (AdjustVolume, FadeIn, FadeOut)"},
        {"name": "Audio|Spatial", "description": "3D positioning and attenuation"},
        {"name": "Audio|SoundMix", "description": "Sound mix modifiers and EQ"},
        {"name": "Audio|Submix", "description": "Submix sends and routing"},
        {"name": "Wwise|Events", "description": "Wwise event posting (PostEvent, PostAkEvent)"},
        {"name": "Wwise|RTPC", "description": "Wwise real-time parameter control (SetRTPCValue)"},
        {"name": "Wwise|Switches", "description": "Wwise switch/state setting (SetSwitch, SetState)"},
        {"name": "Quartz|Clock", "description": "Quartz clock creation and control"},
        {"name": "Quartz|Quantization", "description": "Beat/bar quantization and subscriptions"},
    ]

    # -- MCP patterns --
    mcp_patterns = {
        "gunshot": {
            "description": "Weapon fire with layered samples and pitch randomization",
            "bp_functions": ["PlaySoundAtLocation", "SpawnSoundAtLocation"],
            "ms_nodes": ["Random Get", "Wave Player (Mono)", "ADSR Envelope (Audio)", "Stereo Mixer"],
            "wwise_flow": "RandomSequenceContainer > Sound variations > pitch randomization",
        },
        "footsteps": {
            "description": "Surface-aware randomized footstep audio",
            "bp_functions": ["PlaySoundAtLocation", "AudioComponent.SetIntParameter"],
            "ms_nodes": ["Trigger Route", "Wave Player (Mono)", "AD Envelope (Audio)", "One-Pole Low Pass Filter"],
            "wwise_flow": "SwitchContainer by surface > RandomSequence per surface",
        },
        "ambient": {
            "description": "Looping layered environmental audio with natural variation",
            "bp_functions": ["SpawnSoundAtLocation", "AudioComponent.SetFloatParameter", "AudioComponent.AdjustVolume"],
            "ms_nodes": ["Wave Player (Stereo)", "Trigger Repeat", "LFO", "Stereo Panner"],
            "wwise_flow": "BlendContainer > RTPC-driven layer volumes > zone triggers",
        },
        "spatial": {
            "description": "3D positioned audio with binaural rendering",
            "bp_functions": ["SpawnSoundAttached", "AudioComponent.AdjustAttenuation"],
            "ms_nodes": ["ITD Panner", "Stereo Panner"],
            "wwise_flow": "3D Spatialization > HRTF > distance attenuation",
        },
        "ui_sound": {
            "description": "Non-spatial UI feedback sounds",
            "bp_functions": ["PlaySound2D", "SpawnSound2D"],
            "ms_nodes": ["Sine", "AD Envelope (Audio)", "Wave Player (Mono)"],
            "wwise_flow": "Direct to UI bus, no spatialization",
        },
        "weather_states": {
            "description": "Game state driven audio transitions",
            "bp_functions": ["AudioComponent.SetFloatParameter", "AudioComponent.FadeIn", "AudioComponent.FadeOut"],
            "ms_nodes": ["Trigger Route", "Crossfade", "InterpTo", "Wave Player (Stereo)"],
            "wwise_flow": "StateGroup-driven SwitchContainer > crossfade transitions",
        },
    }

    # -- Allowlist (audio functions permitted by the C++ Blueprint builder) --
    allowlist = [
        # AudioComponent parameter setting
        "SetFloatParameter", "SetIntParameter", "SetBoolParameter",
        "SetStringParameter", "SetWaveParameter", "ExecuteTriggerParameter",
        # Playback
        "PlaySound2D", "PlaySoundAtLocation", "SpawnSoundAtLocation",
        "SpawnSound2D", "Play", "Stop", "SetPaused", "IsPlaying",
        "FadeIn", "FadeOut", "AdjustVolume",
        # Properties
        "SetVolumeMultiplier", "SetPitchMultiplier", "SetSound",
        # Spatial
        "SetWorldLocation", "SetWorldRotation", "GetDistanceTo", "GetActorLocation",
        # Sound mix
        "SetSoundMixClassOverride", "PushSoundMixModifier", "PopSoundMixModifier",
        # Wwise (AkComponent)
        "PostEvent", "PostAkEvent", "SetRTPCValue", "SetSwitch", "SetState", "PostTrigger",
        # Math helpers
        "Multiply_FloatFloat", "Add_FloatFloat", "Subtract_FloatFloat",
        "Divide_FloatFloat", "MapRangeClamped", "Lerp", "FClamp",
        # Logging
        "PrintString",
    ]

    catalogue = {
        "_meta": {
            "description": "Verified Blueprint audio function catalogue -- generated from blueprint_audio.py",
            "function_count": len(functions),
            "source": "scripts/export_catalogues.py",
        },
        "functions": functions,
        "events": events,
        "categories": categories,
        "mcp_patterns": mcp_patterns,
        "allowlist": sorted(allowlist),
    }

    with open(BP_CATALOGUE_PATH, "w", encoding="utf-8") as f:
        json.dump(catalogue, f, indent=2, ensure_ascii=False)

    return BP_CATALOGUE_PATH


def main() -> None:
    parser = argparse.ArgumentParser(description="Export verified knowledge catalogues to JSON")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--ms-only", action="store_true", help="Export MetaSounds catalogue only")
    group.add_argument("--bp-only", action="store_true", help="Export Blueprint catalogue only")
    args = parser.parse_args()

    if not args.bp_only:
        path = export_metasound_catalogue()
        count = len(METASOUND_NODES)
        print(f"Exported {count} MetaSounds nodes -> {path}")

    if not args.ms_only:
        path = export_blueprint_catalogue()
        count = len(BLUEPRINT_AUDIO_FUNCTIONS)
        print(f"Exported {count} Blueprint functions -> {path}")


if __name__ == "__main__":
    main()
