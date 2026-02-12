"""MetaSounds node catalogue -- complete reference for graph generation.

Every node that the MCP server can place in a MetaSound graph is defined here
with its inputs, outputs, tags, and complexity rating.  The catalogue is the
single source of truth consumed by:
  - The Builder API bridge (graph spec -> UE5 C++ plugin)
  - The D1/Vectorize knowledge seeder (bulk upload)
  - The semantic search tool (tag + description matching)

All data sourced from research/research_metasounds_game_audio.md Section 2
and Epic's MetaSounds Function Nodes Reference Guide.
"""

from __future__ import annotations


# ===================================================================
# Helper type aliases (for readability only -- not enforced at runtime)
# ===================================================================
Pin = dict          # {"name": str, "type": str}
InputPin = dict     # {"name": str, "type": str, "required": bool, "default": ...}
NodeDef = dict      # full node definition


def _in(name: str, type_: str, *, required: bool = True, default: object = None) -> InputPin:
    """Build an input pin descriptor."""
    pin: InputPin = {"name": name, "type": type_, "required": required}
    if default is not None:
        pin["default"] = default
    return pin


def _out(name: str, type_: str) -> Pin:
    """Build an output pin descriptor."""
    return {"name": name, "type": type_}


def _node(
    name: str,
    category: str,
    description: str,
    inputs: list[InputPin],
    outputs: list[Pin],
    tags: list[str],
    complexity: int = 1,
    class_name: str = "",
) -> NodeDef:
    """Build a node definition dict."""
    return {
        "name": name,
        "class_name": class_name,
        "category": category,
        "description": description,
        "inputs": inputs,
        "outputs": outputs,
        "tags": tags,
        "complexity": complexity,
    }


# ===================================================================
# METASOUND_NODES  --  keyed by node name, ~150 entries
# ===================================================================

METASOUND_NODES: dict[str, NodeDef] = {}


def _register(node: NodeDef) -> None:
    """Insert a node into the global catalogue."""
    METASOUND_NODES[node["name"]] = node


# -------------------------------------------------------------------
# Generators  (13 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Additive Synth", "Generators",
    "Generates audio from a bank of sine partials with controllable amplitudes.",
    [_in("Base Frequency", "Float"),
     _in("HarmonicMultipliers", "Array", required=False),
     _in("Amplitudes", "Array", required=False),
     _in("Phases", "Array", required=False),
     _in("Pan Amounts", "Array", required=False)],
    [_out("Out Left / Right Audio", "Audio")],
    ["oscillator", "additive", "synthesis", "harmonics", "partials"],
    complexity=3,
))

_register(_node(
    "Saw", "Generators",
    "Band-limited sawtooth oscillator.",
    [_in("Enabled", "Bool", default=True),
     _in("Bi Polar", "Bool", required=False, default=False),
     _in("Frequency", "Float", default=440.0),
     _in("Modulation", "Audio", required=False),
     _in("Sync", "Trigger", required=False),
     _in("Phase Offset", "Float", required=False, default=0.0),
     _in("Glide", "Float", required=False, default=0.0),
     _in("Type", "Enum", required=False)],
    [_out("Audio", "Audio")],
    ["oscillator", "sawtooth", "saw", "synthesis", "subtractive", "bright", "fm"],
    complexity=1,
))

_register(_node(
    "Sine", "Generators",
    "Pure sine wave oscillator.",
    [_in("Enabled", "Bool", default=True),
     _in("Bi Polar", "Bool", required=False, default=False),
     _in("Frequency", "Float", default=440.0),
     _in("Modulation", "Audio", required=False),
     _in("Sync", "Trigger", required=False),
     _in("Phase Offset", "Float", required=False, default=0.0),
     _in("Glide", "Float", required=False, default=0.0),
     _in("Type", "Enum", required=False)],
    [_out("Audio", "Audio")],
    ["oscillator", "sine", "synthesis", "pure", "tone", "fundamental", "fm"],
    complexity=1,
))

_register(_node(
    "Square", "Generators",
    "Band-limited square wave oscillator.",
    [_in("Enabled", "Bool", default=True),
     _in("Bi Polar", "Bool", required=False, default=False),
     _in("Frequency", "Float", default=440.0),
     _in("Modulation", "Audio", required=False),
     _in("Sync", "Trigger", required=False),
     _in("Phase Offset", "Float", required=False, default=0.0),
     _in("Glide", "Float", required=False, default=0.0),
     _in("Type", "Enum", required=False),
     _in("Pulse Width", "Float", required=False, default=0.5)],
    [_out("Audio", "Audio")],
    ["oscillator", "square", "synthesis", "hollow", "pulse", "fm", "pwm"],
    complexity=1,
))

_register(_node(
    "Triangle", "Generators",
    "Band-limited triangle wave oscillator.",
    [_in("Frequency", "Float", default=440.0),
     _in("Enabled", "Bool", default=True),
     _in("Bi Polar", "Bool", required=False, default=False),
     _in("Modulation", "Audio", required=False),
     _in("Sync", "Trigger", required=False),
     _in("Phase Offset", "Float", required=False, default=0.0),
     _in("Glide", "Float", required=False, default=0.0)],
    [_out("Audio", "Audio")],
    ["oscillator", "triangle", "synthesis", "mellow", "soft", "fm"],
    complexity=1,
))

_register(_node(
    "SuperOscillator", "Generators",
    "Multi-voice oscillator with waveform type selection, detuning, glide, and pulse-width control. "
    "Mono variant. Voices stacks unison voices with Detune spread. Entropy adds random per-voice drift. "
    "Blend crossfades between voices. Glide adds portamento between pitch changes. "
    "Limit Output prevents clipping when stacking many voices. Type: Saw/Square/Sine/Triangle. "
    "Best practice: send MIDI ints from Blueprint, convert to Hz with MIDI To Frequency inside MetaSounds.",
    [_in("Enabled", "Bool", default=True),
     _in("Type", "Enum", required=False, default="Saw"),
     _in("Limit Output", "Bool", default=True),
     _in("Voices", "Int32", required=False, default=16),
     _in("Frequency", "Float", default=440.0),
     _in("Modulation", "Audio", required=False),
     _in("Detune", "Float", required=False, default=-0.25),
     _in("Entropy", "Float", required=False, default=0.0),
     _in("Blend", "Float", required=False, default=0.0),
     _in("Glide", "Float", required=False, default=0.0),
     _in("Pulse Width", "Float", required=False, default=0.5),
     _in("Width", "Float", required=False)],
    [_out("Audio", "Audio")],
    ["oscillator", "super", "synthesis", "waveform", "morph", "pulse width",
     "unison", "detune", "voices", "glide", "pad", "synth"],
    complexity=3,
))

_register(_node(
    "WaveTable Oscillator", "Generators",
    "Oscillator that reads from a wavetable for arbitrary waveforms.",
    [_in("WaveTable", "WaveAsset", required=False),
     _in("Play", "Trigger", required=False),
     _in("Stop", "Trigger", required=False),
     _in("Freq", "Int32"),
     _in("Sync", "Trigger", required=False),
     _in("Phase Modulator", "Audio", required=False)],
    [_out("Out", "Audio")],
    ["oscillator", "wavetable", "synthesis", "waveform"],
    complexity=3,
))

_register(_node(
    "WaveTable Player", "Generators",
    "Plays a wavetable at a given position for single-cycle waveform use.",
    [_in("Play", "Trigger", required=False),
     _in("Stop", "Trigger", required=False),
     _in("Sync", "Trigger", required=False),
     _in("Bank", "WaveAsset"),
     _in("Index", "Int32"),
     _in("Pitch Shift", "Float"),
     _in("Loop", "Bool", required=False, default=False)],
    [_out("Mono Out", "Audio"),
     _out("On Finished", "Trigger")],
    ["wavetable", "player", "synthesis", "waveform"],
    complexity=2,
))

_register(_node(
    "Low Frequency Noise", "Generators",
    "Generates smooth random noise at low frequencies for organic modulation.",
    [_in("Seed", "Int32", required=False, default=-1),
     _in("Rate", "Float"),
     _in("Reset Seed", "Trigger", required=False),
     _in("Sync", "Trigger", required=False),
     _in("Interpolation", "Enum", required=False),
     _in("Rate Jitter", "Float", required=False),
     _in("Step Limit", "Float", required=False),
     _in("Min Value", "Float", required=False),
     _in("Max Value", "Float", required=False)],
    [_out("Out", "Audio"),
     _out("Normalized", "Float")],
    ["noise", "modulation", "random", "organic", "drift", "lfo"],
    complexity=2,
))

_register(_node(
    "Low-Frequency Oscillator", "Generators",
    "LFO for modulation: sine, saw, square, triangle, sample-and-hold shapes. "
    "Pin names verified from engine exports.",
    [_in("Frequency", "Float"),
     _in("Shape", "Enum", required=False),
     _in("Min Value", "Float", required=False),
     _in("Max Value", "Float", required=False),
     _in("Sync", "Trigger", required=False),
     _in("Phase Offset", "Float", required=False),
     _in("Pulse Width", "Float", required=False)],
    [_out("Out", "Float")],
    ["lfo", "modulation", "tremolo", "vibrato", "wobble", "sweep"],
    complexity=2,
    class_name="UE::LFO::Audio",
))

_register(_node(
    "Noise (Pink)", "Generators",
    "Pink noise generator (1/f spectrum, equal energy per octave).",
    [_in("Seed", "Int32", required=False, default=-1)],
    [_out("Audio", "Audio")],
    ["noise", "pink", "warm", "natural", "broadband"],
    complexity=1,
))

_register(_node(
    "Noise (White)", "Generators",
    "White noise generator (flat spectrum, equal energy per frequency).",
    [_in("Seed", "Int32", required=False, default=-1)],
    [_out("Audio", "Audio")],
    ["noise", "white", "bright", "hiss", "broadband"],
    complexity=1,
))

_register(_node(
    "Perlin Noise", "Generators",
    "Perlin-noise-based signal for smooth organic modulation.",
    [_in("Seed", "Int32", required=False, default=-1),
     _in("X", "Float"),
     _in("Layers", "Int32", required=False),
     _in("Min Value", "Float", required=False),
     _in("Max Value", "Float", required=False)],
    [_out("Normalized", "Float")],
    ["noise", "perlin", "organic", "modulation", "smooth", "procedural"],
    complexity=2,
))

_register(_node(
    "Noise", "Generators",
    "Generic noise generator with selectable type (White, Pink, etc.). "
    "Engine class: UE::Noise::Audio. Pin names verified from exports.",
    [_in("Seed", "Int32", required=False, default=-1),
     _in("Type", "Enum", required=False)],
    [_out("Audio", "Audio")],
    ["noise", "white", "pink", "generator", "broadband", "hiss"],
    complexity=1,
    class_name="UE::Noise::Audio",
))


# -------------------------------------------------------------------
# Wave Players  (7 nodes)
# -------------------------------------------------------------------

_WAVE_PLAYER_INPUTS: list[InputPin] = [
    _in("Play", "Trigger", required=False),
    _in("Stop", "Trigger", required=False),
    _in("Wave Asset", "WaveAsset"),
    _in("Start Time", "Time", required=False),
    _in("Pitch Shift", "Float", required=False),
    _in("Loop", "Bool", default=True),
    _in("Loop Start", "Time", required=False),
    _in("Loop Duration", "Time", required=False, default=-1.0),
    _in("Maintain Audio Sync", "Bool", required=False),
]

_WAVE_PLAYER_OUTPUTS_MONO: list[Pin] = [
    _out("On Play", "Trigger"),
    _out("On Finished", "Trigger"),
    _out("On Nearly Finished", "Trigger"),
    _out("On Looped", "Trigger"),
    _out("On Cue Point", "Trigger"),
    _out("Cue Point ID", "Int32"),
    _out("Cue Point Label", "String"),
    _out("Loop Percent", "Float"),
    _out("Playback Location", "Float"),
    _out("Playback Time", "Float"),
    _out("Out Mono", "Audio"),
]

_WAVE_PLAYER_OUTPUTS_STEREO: list[Pin] = [
    _out("On Play", "Trigger"),
    _out("On Finished", "Trigger"),
    _out("On Nearly Finished", "Trigger"),
    _out("On Looped", "Trigger"),
    _out("On Cue Point", "Trigger"),
    _out("Cue Point ID", "Int32"),
    _out("Cue Point Label", "String"),
    _out("Loop Percent", "Float"),
    _out("Playback Location", "Float"),
    _out("Playback Time", "Time"),
    _out("Out Left", "Audio"),
    _out("Out Right", "Audio"),
]

for _ch, _desc, _outs, _cx in [
    ("Mono", "Mono wave file player with pitch shift, looping, and trigger outputs.",
     _WAVE_PLAYER_OUTPUTS_MONO, 1),
    ("Stereo", "Stereo wave file player with L/R outputs and looping.",
     _WAVE_PLAYER_OUTPUTS_STEREO, 1),
    ("Quad", "Quad (4-channel) wave file player.",
     [_out(f"Audio {i}", "Audio") for i in range(4)]
     + [_out("OnFinished", "Trigger"), _out("OnLooped", "Trigger"),
        _out("OnNearlyFinished", "Trigger")], 2),
    ("5.1", "5.1 surround wave file player.",
     [_out(f"Audio {ch}", "Audio") for ch in ("FL", "FR", "FC", "LFE", "SL", "SR")]
     + [_out("OnFinished", "Trigger"), _out("OnLooped", "Trigger"),
        _out("OnNearlyFinished", "Trigger")], 3),
    ("7.1", "7.1 surround wave file player.",
     [_out(f"Audio {ch}", "Audio") for ch in ("FL", "FR", "FC", "LFE", "SL", "SR", "BL", "BR")]
     + [_out("OnFinished", "Trigger"), _out("OnLooped", "Trigger"),
        _out("OnNearlyFinished", "Trigger")], 3),
]:
    _register(_node(
        f"Wave Player ({_ch})", "Wave Players", _desc,
        list(_WAVE_PLAYER_INPUTS), _outs,
        ["wave", "player", "sample", "playback", _ch.lower(), "loop"],
        complexity=_cx,
    ))

# Clean up loop variables
del _ch, _desc, _outs, _cx


# -------------------------------------------------------------------
# Envelopes  (8 nodes -- Audio and Float variants where applicable)
# -------------------------------------------------------------------

_register(_node(
    "AD Envelope", "Envelopes",
    "Attack-Decay envelope — real UE5 node name. "
    "Outputs audio-rate envelope signal. Pin names verified from engine exports.",
    [_in("Trigger", "Trigger"),
     _in("Attack Time", "Time", default=0.01),
     _in("Decay Time", "Time", default=0.1),
     _in("Attack Curve", "Float", required=False, default=1.0),
     _in("Decay Curve", "Float", required=False, default=1.0),
     _in("Looping", "Bool", required=False, default=False),
     _in("Hard Reset", "Bool", required=False, default=False)],
    [_out("On Trigger", "Trigger"),
     _out("On Done", "Trigger"),
     _out("Out Envelope", "Audio")],
    ["envelope", "AD", "attack", "decay", "percussive", "transient", "amplitude"],
    complexity=2,
))

_register(_node(
    "AD Envelope (Audio)", "Envelopes",
    "Attack-Decay envelope outputting audio-rate signal. "
    "Engine variant name: AD Envelope::AD Envelope::Audio. Pins verified from exports.",
    [_in("Trigger", "Trigger"),
     _in("Attack Time", "Time", default=0.01),
     _in("Decay Time", "Time", default=0.1),
     _in("Attack Curve", "Float", required=False, default=1.0),
     _in("Decay Curve", "Float", required=False, default=1.0),
     _in("Looping", "Bool", required=False, default=False),
     _in("Hard Reset", "Bool", required=False, default=False)],
    [_out("On Trigger", "Trigger"),
     _out("On Done", "Trigger"),
     _out("Out Envelope", "Audio")],
    ["envelope", "AD", "attack", "decay", "percussive", "transient", "amplitude"],
    complexity=2,
    class_name="AD Envelope::AD Envelope::Audio",
))

_register(_node(
    "AD Envelope (Float)", "Envelopes",
    "Attack-Decay envelope outputting block-rate float. "
    "Engine variant name: AD Envelope::AD Envelope::Float. Pins verified from exports.",
    [_in("Trigger", "Trigger"),
     _in("Attack Time", "Time", default=0.01),
     _in("Decay Time", "Time", default=0.1),
     _in("Attack Curve", "Float", required=False, default=1.0),
     _in("Decay Curve", "Float", required=False, default=1.0),
     _in("Looping", "Bool", required=False, default=False),
     _in("Hard Reset", "Bool", required=False, default=False)],
    [_out("On Trigger", "Trigger"),
     _out("On Done", "Trigger"),
     _out("Out Envelope", "Float")],
    ["envelope", "AD", "attack", "decay", "percussive", "control"],
    complexity=2,
))

_register(_node(
    "ADSR Envelope (Audio)", "Envelopes",
    "Full ADSR envelope outputting audio-rate signal for sustained sounds. "
    "Has separate Trigger Attack and Trigger Release inputs, NOT a single Trigger. "
    "Pin names verified from engine exports.",
    [_in("Trigger Attack", "Trigger", required=False),
     _in("Trigger Release", "Trigger", required=False),
     _in("Attack Time", "Float", required=False),
     _in("Decay Time", "Float", required=False),
     _in("Sustain Level", "Float", required=False),
     _in("Release Time", "Float", required=False),
     _in("Attack Curve", "Float", required=False),
     _in("Decay Curve", "Float", required=False),
     _in("Release Curve", "Float", required=False),
     _in("Hard Reset", "Bool", required=False)],
    [_out("On Attack Triggered", "Trigger"),
     _out("On Decay Triggered", "Trigger"),
     _out("On Sustain Triggered", "Trigger"),
     _out("On Release Triggered", "Trigger"),
     _out("On Done", "Trigger"),
     _out("Out Envelope", "Audio")],
    ["envelope", "ADSR", "attack", "decay", "sustain", "release", "amplitude", "gate"],
    complexity=2,
    class_name="ADSR Envelope::ADSR Envelope::Audio",
))

_register(_node(
    "ADSR Envelope (Float)", "Envelopes",
    "Full ADSR envelope outputting block-rate float.",
    [_in("Trigger", "Trigger"),
     _in("Attack", "Time", default=0.01),
     _in("Decay", "Time", default=0.1),
     _in("Sustain", "Float", default=0.7),
     _in("Release", "Time", default=0.2)],
    [_out("Envelope", "Float"),
     _out("OnDone", "Trigger")],
    ["envelope", "ADSR", "attack", "decay", "sustain", "release", "control"],
    complexity=2,
))

_register(_node(
    "Crossfade", "Envelopes",
    "Crossfade between two audio signals using a 0-1 control value.",
    [_in("Crossfade Value", "Float"),
     _in("In 0", "Audio"),
     _in("In 1", "Audio")],
    [_out("Out", "Audio")],
    ["crossfade", "blend", "mix", "transition", "morph"],
    complexity=1,
))

_register(_node(
    "WaveTable Envelope", "Envelopes",
    "Envelope shaped by a wavetable for arbitrary envelope curves.",
    [_in("WaveTable", "WaveAsset"),
     _in("Duration", "Time", default=1.0),
     _in("Play", "Trigger"),
     _in("Stop", "Trigger", required=False),
     _in("Pause", "Trigger", required=False),
     _in("Mode", "Enum"),
     _in("Interpolation", "Enum", required=False)],
    [_out("OnFinished", "Trigger"),
     _out("Out", "Audio")],
    ["envelope", "wavetable", "shape", "custom", "curve"],
    complexity=3,
))

_register(_node(
    "Evaluate WaveTable", "Envelopes",
    "Looks up a wavetable value at a given position (0-1).",
    [_in("WaveTable", "WaveAsset", required=False),
     _in("Position", "Float", default=0.0),
     _in("Interpolation", "Enum", required=False)],
    [_out("Value", "Float")],
    ["wavetable", "lookup", "evaluate", "curve", "position"],
    complexity=2,
))

_register(_node(
    "Envelope Follower", "Envelopes",
    "Tracks the amplitude envelope of an incoming audio signal.",
    [_in("In", "Audio"),
     _in("Attack Time", "Time"),
     _in("Release Time", "Time"),
     _in("Peak Mode", "Bool", required=False, default=False)],
    [_out("Envelope", "Float"),
     _out("Audio Envelope", "Audio")],
    ["envelope", "follower", "amplitude", "tracker", "dynamics", "sidechain"],
    complexity=2,
))



_register(_node(
    "Crossfade (Audio, 2)", "Envelopes",
    "Crossfades between two audio signals using control value (0-1).",
    [_in("Crossfade Value", "Float"),
     _in("In 0", "Audio"),
     _in("In 1", "Audio")],
    [_out("Out", "Audio")],
    ["crossfade", "blend", "mix", "transition", "audio"],
    complexity=1,
))


# -------------------------------------------------------------------
# Filters  (10 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Biquad Filter", "Filters",
    "Versatile second-order filter with selectable type (LPF, HPF, BPF, Notch, etc.). "
    "Pin names verified from engine exports.",
    [_in("In", "Audio"),
     _in("Cutoff Frequency", "Float"),
     _in("Bandwidth", "Float"),
     _in("Gain", "Float", required=False),
     _in("Type", "Enum", required=False)],
    [_out("Out", "Audio")],
    ["filter", "biquad", "subtractive", "frequency", "EQ", "lowpass",
     "highpass", "bandpass", "notch", "underwater", "muffled"],
    complexity=2,
    class_name="UE::Biquad Filter::Audio",
))

_register(_node(
    "Dynamic Filter", "Filters",
    "Biquad filter with audio-rate modulation of cutoff frequency.",
    [_in("Audio", "Audio"),
     _in("Cutoff Frequency", "Audio"),
     _in("Bandwidth", "Float", default=1.0),
     _in("FilterType", "Enum", default="LPF"),
     _in("Sidechain", "Audio", required=False),
     _in("Frequency", "Float"),
     _in("Q", "Float"),
     _in("Threshold dB", "Float"),
     _in("Ratio", "Float"),
     _in("Knee", "Float"),
     _in("Range", "Float"),
     _in("Gain (dB)", "Float"),
     _in("AttackTime", "Time"),
     _in("ReleaseTime", "Time"),
     _in("EnvelopeMode", "Enum"),
     _in("AnalogMode", "Enum")],
    [_out("Audio", "Audio")],
    ["filter", "dynamic", "modulation", "sweep", "wah", "envelope filter"],
    complexity=3,
))

_register(_node(
    "Ladder Filter", "Filters",
    "Classic 4-pole ladder filter topology with resonance.",
    [_in("Cutoff Frequency", "Float", default=1000.0),
     _in("Resonance", "Float", default=0.5),
     _in("FilterType", "Enum", default="LPF"),
     _in("In", "Audio")],
    [_out("Out", "Audio")],
    ["filter", "ladder", "moog", "resonance", "analog", "subtractive", "warm"],
    complexity=3,
))

_register(_node(
    "State Variable Filter", "Filters",
    "Simultaneous lowpass, highpass, bandpass, and notch outputs.",
    [_in("Cutoff Frequency", "Float", default=1000.0),
     _in("Resonance", "Float", default=0.5),
     _in("In", "Audio"),
     _in("Band Stop Control", "Float", default=0.0)],
    [_out("Band Pass", "Audio"),
     _out("Low Pass Filter", "Audio"),
     _out("High Pass Filter", "Audio"),
     _out("Band Stop", "Audio")],
    ["filter", "SVF", "state variable", "multimode", "lowpass", "highpass",
     "bandpass", "notch"],
    complexity=3,
))

_register(_node(
    "One-Pole High Pass Filter", "Filters",
    "Simple first-order high-pass filter -- removes low frequencies.",
    [_in("In", "Audio"),
     _in("Cutoff Frequency", "Float", default=200.0)],
    [_out("Out", "Audio")],
    ["filter", "highpass", "onepole", "simple", "rumble removal", "DC block"],
    complexity=1,
))

_register(_node(
    "One-Pole Low Pass Filter", "Filters",
    "Simple first-order low-pass filter -- removes high frequencies.",
    [_in("In", "Audio"),
     _in("Cutoff Frequency", "Float", default=5000.0)],
    [_out("Out", "Audio")],
    ["filter", "lowpass", "onepole", "simple", "muffled", "distance",
     "underwater", "warm"],
    complexity=1,
))

_register(_node(
    "Sample And Hold", "Filters",
    "Samples the input signal value when triggered and holds it until next trigger.",
    [_in("Sample And Hold", "Trigger"),
     _in("In", "Audio")],
    [_out("On Sample And Hold", "Trigger"),
     _out("Out", "Audio")],
    ["sample", "hold", "trigger", "quantize", "step"],
    complexity=1,
))

_register(_node(
    "Bitcrusher", "Filters",
    "Reduces bit depth and/or sample rate for lo-fi distortion effects.",
    [_in("Audio", "Audio"),
     _in("Sample Rate", "Float"),
     _in("Bit Depth", "Float")],
    [_out("Audio", "Audio")],
    ["distortion", "lofi", "retro", "8bit", "bitcrusher", "crush", "chiptune"],
    complexity=2,
))

_register(_node(
    "Mono Band Splitter", "Filters",
    "Splits mono audio into low, mid, and high frequency bands.",
    [_in("In", "Audio")],
    [],
    ["filter", "crossover", "band splitter", "multiband", "EQ"],
    complexity=2,
))

_register(_node(
    "Stereo Band Splitter", "Filters",
    "Splits stereo audio into low, mid, and high frequency bands (L+R pairs).",
    [],
    [],
    ["filter", "crossover", "band splitter", "stereo", "multiband", "EQ"],
    complexity=3,
))


# -------------------------------------------------------------------
# Delays  (5 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Delay", "Delays",
    "Mono delay line with dry/wet mix.",
    [_in("Feedback", "Float", required=False, default=0.3),
     _in("In", "Audio"),
     _in("Delay Time", "Time", required=False, default=0.5),
     _in("Dry Level", "Float", default=1.0),
     _in("Wet Level", "Float", default=1.0),
     _in("Max Delay Time", "Time", required=False)],
    [_out("Out", "Audio")],
    ["delay", "echo", "time", "repeat", "feedback"],
    complexity=2,
))

_register(_node(
    "Stereo Delay", "Delays",
    "Stereo delay with independent L/R delay times and feedback.",
    [_in("In Left", "Audio"),
     _in("In Right", "Audio"),
     _in("Feedback", "Float", required=False, default=0.3),
     _in("Delay Time", "Time", required=False),
     _in("Delay Mode", "Enum", required=False, default="Normal"),
     _in("Delay Ratio", "Float", required=False, default=1.0),
     _in("Dry Level", "Float", default=1.0),
     _in("Wet Level", "Float")],
    [_out("Out Left", "Audio"),
     _out("Out Right", "Audio")],
    ["delay", "stereo", "echo", "ping pong", "time", "spatial"],
    complexity=3,
))

_register(_node(
    "Delay Pitch Shift", "Delays",
    "Pitch shifting via delay line manipulation (granular pitch shift).",
    [_in("In", "Audio"),
     _in("Pitch Shift", "Float"),
     _in("Delay Length", "Time")],
    [_out("Out", "Audio")],
    ["delay", "pitch", "shift", "transpose", "detune"],
    complexity=3,
))

_register(_node(
    "Diffuser", "Delays",
    "Multi-tap diffusion network for reverb-like smearing of transients.",
    [_in("Input Audio", "Audio"),
     _in("Depth", "Float", required=False),
     _in("Feedback", "Float", required=False)],
    [_out("Output Audio", "Audio")],
    ["diffuser", "reverb", "smear", "space", "diffusion", "ambience"],
    complexity=3,
))

_register(_node(
    "Plate Reverb", "Delays",
    "Plate reverb effect — simulates metal plate vibration for dense, smooth reverb tails. "
    "From TechAudioTools SFX Generator (Eric Buchholz). Used as one of three parallel temporal effects "
    "(Delay + Flanger + Plate Reverb) in the send effects section.",
    [_in("Audio", "Audio"),
     _in("Damping", "Float", default=0.5),
     _in("Decay", "Float", default=0.5),
     _in("DryWet", "Float", required=False, default=0.5),
     _in("PreDelay", "Time", required=False, default=0.02)],
    [_out("Audio", "Audio")],
    ["reverb", "plate", "space", "ambience", "tail", "dense", "smooth", "room"],
    complexity=3,
))

_register(_node(
    "Grain Delay", "Delays",
    "Granular delay with grain size, density, and pitch shift controls.",
    [_in("In Audio", "Audio"),
     _in("Grain Spawn", "Trigger", required=False),
     _in("Grain Delay", "Time"),
     _in("Grain Delay Range", "Time", required=False),
     _in("Grain Duration", "Time"),
     _in("Grain Duration Range", "Time", required=False),
     _in("Pitch Shift", "Float"),
     _in("Pitch Shift Range", "Float", required=False),
     _in("Grain Envelope", "Enum", required=False),
     _in("Max Grain Count", "Int32", required=False),
     _in("Feedback Amount", "Float")],
    [_out("Out Audio", "Audio")],
    ["granular", "delay", "grain", "texture", "freeze", "glitch"],
    complexity=4,
))



_register(_node(
    "Delay (Audio)", "Delays",
    "Audio delay line with feedback and wet/dry mix control.",
    [_in("In", "Audio"),
     _in("Delay Time", "Time", default=1.0),
     _in("Dry Level", "Float", default=0.0),
     _in("Wet Level", "Float", default=1.0),
     _in("Feedback", "Float", default=0.0),
     _in("Max Delay Time", "Time", default=5.0),
     _in("Reset", "Trigger", required=False)],
    [_out("Out", "Audio")],
    ["delay", "echo", "audio", "feedback", "time"],
    complexity=2,
))


# -------------------------------------------------------------------
# Dynamics  (4 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Compressor", "Dynamics",
    "Dynamic range compressor with threshold/ratio/knee, parallel mix (Wet/Dry), "
    "optional analog modeling, peak/RMS envelope modes, and upwards compression. "
    "At 30:1 ratio with low threshold acts as brick-wall limiter for vehicle/engine layers.",
    [_in("Audio", "Audio"),
     _in("Ratio", "Float", default=4.0),
     _in("Threshold dB", "Float", default=-20.0),
     _in("Attack Time", "Time", default=0.01),
     _in("Release Time", "Time", default=0.1),
     _in("Lookahead Time", "Time", required=False, default=0.01),
     _in("Knee", "Float", required=False, default=6.0),
     _in("Sidechain", "Audio", required=False),
     _in("Envelope Mode", "Enum", required=False, default="Peak"),
     _in("Analog Mode", "Bool", required=False, default=False),
     _in("Upwards Mode", "Bool", required=False, default=False),
     _in("Wet/Dry", "Float", required=False, default=1.0)],
    [_out("Audio", "Audio"),
     _out("Gain Envelope", "Audio")],
    ["compressor", "dynamics", "loudness", "squeeze", "punch", "sidechain",
     "parallel", "limiter", "vehicle", "engine"],
    complexity=3,
))

_register(_node(
    "Limiter", "Dynamics",
    "Hard limiter / brick-wall limiter preventing signal from exceeding threshold.",
    [_in("Audio", "Audio"),
     _in("Input Gain dB", "Float", required=False),
     _in("Threshold dB", "Float"),
     _in("Release Time", "Time"),
     _in("Knee", "Float", required=False)],
    [_out("Audio", "Audio")],
    ["limiter", "dynamics", "ceiling", "clip", "protect"],
    complexity=2,
))

_register(_node(
    "Decibels to Linear Gain", "Dynamics",
    "Converts a decibel value to a linear gain multiplier.",
    [_in("Decibels", "Float")],
    [_out("Linear Gain", "Float")],
    ["convert", "dB", "linear", "gain", "volume"],
    complexity=1,
))

_register(_node(
    "Linear Gain to Decibels", "Dynamics",
    "Converts a linear gain multiplier to decibel value.",
    [_in("Linear Gain", "Float", default=1.0)],
    [_out("Decibels", "Float")],
    ["convert", "linear", "dB", "gain", "volume"],
    complexity=1,
))


# -------------------------------------------------------------------
# Triggers  (13 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Trigger Accumulate", "Triggers",
    "Counts incoming triggers and fires output when count reaches threshold.",
    [],
    [_out("Out", "Audio")],
    ["trigger", "count", "accumulate", "threshold", "gate"],
    complexity=2,
))

_register(_node(
    "Trigger Any", "Triggers",
    "Fires output when any of its input triggers fire.",
    [_in("Trigger 0", "Trigger"),
     _in("Trigger 1", "Trigger"),
     _in("Trigger 2", "Trigger", required=False),
     _in("Trigger 3", "Trigger", required=False)],
    [_out("Trigger", "Trigger")],
    ["trigger", "any", "or", "combine", "merge"],
    complexity=1,
))

_register(_node(
    "Trigger Compare", "Triggers",
    "Compares a float value to a threshold and fires trigger when condition is met.",
    [_in("Compare", "Trigger")],
    [],
    ["trigger", "compare", "threshold", "condition", "gate"],
    complexity=2,
))

_register(_node(
    "Trigger Compare (Int32)", "Triggers",
    "Compares two Int32 values when triggered and fires True or False. Used for room/state selection.",
    [_in("Compare", "Trigger", required=False),
     _in("A", "Int32"),
     _in("B", "Int32", default=0),
     _in("Type", "Enum", default="Equals")],
    [_out("True", "Trigger"),
     _out("False", "Trigger")],
    ["trigger", "compare", "int32", "equals", "switch", "condition", "gate"],
    complexity=2,
))


_register(_node(
    "Trigger Compare (Float)", "Logic",
    "Compares two float values and fires True or False trigger based on comparison type.",
    [_in("Compare", "Trigger", required=False), _in("A", "Float"), _in("B", "Float"),
     _in("Type", "Enum", required=False)],
    [_out("True", "Trigger"), _out("False", "Trigger")],
    ["compare", "logic", "trigger", "branch", "condition"],
    complexity=1,
    class_name="TriggerCompare::Clamp::Float",
))

_register(_node(
    "Trigger Compare (Bool)", "Logic",
    "Compares two boolean values and fires True or False trigger.",
    [_in("Compare", "Trigger", required=False), _in("A", "Bool"), _in("B", "Bool"),
     _in("Type", "Enum", required=False)],
    [_out("True", "Trigger"), _out("False", "Trigger")],
    ["compare", "logic", "trigger", "branch", "condition"],
    complexity=1,
    class_name="TriggerCompare::Clamp::Bool",
))

_register(_node(
    "Trigger Control", "Triggers",
    "Gates or enables trigger flow based on a boolean control input.",
    [_in("Trigger In", "Trigger"),
     _in("Open", "Trigger", required=False),
     _in("Close", "Trigger", required=False),
     _in("Toggle", "Trigger", required=False),
     _in("Start Closed", "Bool", required=False, default=False)],
    [_out("Trigger Out", "Trigger")],
    ["trigger", "gate", "control", "enable", "disable"],
    complexity=1,
))

_register(_node(
    "Trigger Counter", "Triggers",
    "Counts triggers up or down and exposes the current count. "
    "Pin names verified from engine exports.",
    [_in("In", "Trigger"),
     _in("Reset", "Trigger", required=False),
     _in("Start Value", "Float", required=False, default=0.0),
     _in("Step Size", "Float", required=False, default=1.0),
     _in("Reset Count", "Int32", required=False)],
    [_out("On Trigger", "Trigger"),
     _out("On Reset", "Trigger"),
     _out("Count", "Int32"),
     _out("Value", "Float")],
    ["trigger", "counter", "count", "increment", "decrement"],
    complexity=2,
))

_register(_node(
    "Trigger Delay", "Triggers",
    "Delays a trigger by a specified time duration.",
    [_in("Reset", "Trigger", required=False),
     _in("In", "Audio"),
     _in("Delay Time", "Time")],
    [_out("Out", "Audio")],
    ["trigger", "delay", "time", "postpone", "wait"],
    complexity=1,
))

_register(_node(
    "Trigger Filter", "Triggers",
    "Passes or blocks triggers based on probability. Each incoming trigger has a chance "
    "of passing through (Heads) or being blocked (Tails). Pin names verified from exports.",
    [_in("Trigger", "Trigger"),
     _in("Reset", "Trigger", required=False),
     _in("Seed", "Int32", required=False),
     _in("Probability", "Float", default=0.5)],
    [_out("Heads", "Trigger"),
     _out("Tails", "Trigger")],
    ["trigger", "filter", "gate", "pass", "block", "probability"],
    complexity=1,
    class_name="UE::Trigger Filter::None",
))

_register(_node(
    "Trigger Once", "Triggers",
    "Fires only on the first incoming trigger, ignores all subsequent ones.",
    [_in("Reset", "Trigger", required=False),
     _in("Trigger In", "Trigger"),
     _in("Start Closed", "Bool", required=False, default=False)],
    [_out("Trigger Out", "Trigger")],
    ["trigger", "once", "oneshot", "first", "single"],
    complexity=1,
))

_register(_node(
    "Trigger On Threshold", "Triggers",
    "Fires trigger when a float value crosses a threshold (rising or falling).",
    [_in("Threshold", "Float", default=0.5),
     _in("In", "Audio")],
    [_out("Out", "Audio")],
    ["trigger", "threshold", "crossing", "edge", "detect"],
    complexity=2,
))

_register(_node(
    "Trigger On Value Change", "Triggers",
    "Fires trigger whenever the input value changes.",
    [_in("Value", "Float")],
    [_out("Trigger", "Trigger")],
    ["trigger", "change", "detect", "watch", "monitor"],
    complexity=1,
))

_register(_node(
    "Trigger Pipe", "Triggers",
    "Passes trigger through unchanged -- useful for debugging and routing.",
    [_in("In", "Audio"),
     _in("Reset", "Trigger", required=False),
     _in("Delay Time", "Time", required=False)],
    [_out("Out", "Audio")],
    ["trigger", "pipe", "passthrough", "debug", "routing"],
    complexity=1,
))

_register(_node(
    "Trigger Repeat", "Triggers",
    "Repeats trigger at a regular interval (periodic timer). "
    "Engine class: UE::TriggerRepeat::None. Pin names verified from exports.",
    [_in("Start", "Trigger", required=False),
     _in("Stop", "Trigger", required=False),
     _in("Period", "Time", default=0.5),
     _in("Num Repeats", "Int32", required=False, default=-1)],
    [_out("RepeatOut", "Trigger")],
    ["trigger", "repeat", "timer", "periodic", "interval", "clock", "metronome"],
    complexity=2,
))

_register(_node(
    "Trigger Sequence", "Triggers",
    "Fires output triggers in sequential round-robin order (0, 1, 2, ...). "
    "When Loop is enabled, wraps back to Out 0 after the last output. "
    "Used for cycling through weapon shot layers.",
    [_in("In", "Trigger"),
     _in("Reset", "Trigger", required=False),
     _in("Loop", "Bool", required=False, default=False)],
    [_out("Out 0", "Trigger"),
     _out("Out 1", "Trigger"),
     _out("Out 2", "Trigger")],
    ["trigger", "sequence", "round-robin", "order", "cycle", "step", "rotate"],
    complexity=2,
))

_register(_node(
    "Trigger Route", "Triggers",
    "Routes trigger to one of N outputs based on an integer index.",
    [_in("Trigger", "Trigger"),
     _in("Index", "Int32", default=0),
     _in("NumOutputs", "Int32", default=2)],
    [_out("Trigger 0", "Trigger"),
     _out("Trigger 1", "Trigger"),
     _out("Trigger 2", "Trigger"),
     _out("Trigger 3", "Trigger")],
    ["trigger", "route", "switch", "select", "branch", "demux"],
    complexity=2,
))



_register(_node(
    "Trigger Route (Float, 2)", "Routing",
    "Routes float values to output based on trigger inputs. 2-input variant.",
    [_in("Set 0", "Trigger", required=False), _in("Value 0", "Float"),
     _in("Set 1", "Trigger"), _in("Value 1", "Float")],
    [_out("On Set", "Trigger"), _out("Value", "Float")],
    ["routing", "trigger", "switch", "select"],
    complexity=1,
    class_name="TriggerRoute::Trigger Route (Float, 2)::Float",
))

# -------------------------------------------------------------------
# Arrays  (7 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Array Get", "Arrays",
    "Gets an element from an array at the specified index.",
    [_in("Array", "Float[]"),
     _in("Index", "Int32", default=0)],
    [_out("Value", "Float")],
    ["array", "get", "index", "access", "element"],
    complexity=1,
))

_register(_node(
    "Array Set", "Arrays",
    "Sets an element in an array at the specified index.",
    [_in("Array", "Float[]"),
     _in("Index", "Int32", default=0),
     _in("Value", "Float")],
    [_out("Array", "Float[]")],
    ["array", "set", "index", "modify", "element"],
    complexity=1,
))

_register(_node(
    "Array Get (Int32)", "Arrays",
    "Gets an element from an Int32 array by index.",
    [_in("Index", "Int32"),
     _in("Array", "Int32[]")],
    [_out("Element", "Int32")],
    ["array", "get", "index", "element", "int32"],
    complexity=1,
))

_register(_node(
    "Array Num", "Arrays",
    "Returns the number of elements in an array.",
    [_in("Array", "Float[]")],
    [_out("Num", "Int32")],
    ["array", "count", "length", "size", "num"],
    complexity=1,
))

_register(_node(
    "Random Get (WaveAssetArray)", "Arrays",
    "Gets a random element from a WaveAsset array, optionally weighted. "
    "No Repeats prevents consecutive duplicates. Enable Shared State syncs across instances.",
    [_in("Next", "Trigger", required=False),
     _in("Reset", "Trigger", required=False),
     _in("In Array", "WaveAsset[]"),
     _in("Weights", "Float[]", required=False),
     _in("Seed", "Int32", required=False, default=-1),
     _in("No Repeats", "Int32", required=False, default=1)],
    [_out("On Next", "Trigger"),
     _out("On Reset", "Trigger"),
     _out("Value", "WaveAsset")],
    ["array", "random", "get", "variation", "selection", "weighted", "no-repeat"],
    complexity=2,
))

_register(_node(
    "Array Shuffle", "Arrays",
    "Returns array elements in random order without repeats until exhausted.",
    [_in("Trigger", "Trigger"),
     _in("Array", "WaveAsset[]"),
     _in("Seed", "Int32", required=False, default=-1),
     _in("AutoReset", "Bool", required=False, default=True)],
    [_out("Value", "WaveAsset"),
     _out("Index", "Int32"),
     _out("Trigger", "Trigger")],
    ["array", "shuffle", "random", "no-repeat", "variation", "round-robin"],
    complexity=2,
))

_register(_node(
    "Array Concatenate", "Arrays",
    "Concatenates two arrays into one.",
    [_in("Array A", "Float[]"),
     _in("Array B", "Float[]")],
    [_out("Array", "Float[]")],
    ["array", "concatenate", "join", "merge", "combine", "append"],
    complexity=1,
))

_register(_node(
    "Array Subset", "Arrays",
    "Extracts a contiguous subset of elements from an array.",
    [_in("Array", "Float[]"),
     _in("Start Index", "Int32", default=0),
     _in("Count", "Int32", default=1)],
    [_out("Array", "Float[]")],
    ["array", "subset", "slice", "range", "sub"],
    complexity=1,
))


# -------------------------------------------------------------------
# Math  (15 nodes)
# -------------------------------------------------------------------

# Arithmetic operators -- support Float, Audio, and Int32 variants
# Engine pin names verified from exports: PrimaryOperand, AdditionalOperands, Out
for _op, _symbol, _desc in [
    ("Add", "+", "Adds two values (Float, Audio, or Int32)."),
    ("Subtract", "-", "Subtracts second value from first."),
    ("Multiply", "*", "Multiplies two values (commonly used for amplitude modulation)."),
    ("Divide", "/", "Divides first value by second."),
]:
    for _type in ("Float", "Audio", "Int32"):
        _suffix = f" ({_type})" if _type != "Float" else ""
        _register(_node(
            f"{_op}{_suffix}", "Math",
            f"{_desc} Operates on {_type} data.",
            [_in("PrimaryOperand", _type),
             _in("AdditionalOperands", _type, default=1 if _op == "Multiply" else 0)],
            [_out("Out", _type)],
            ["math", _op.lower(), _symbol, "arithmetic", _type.lower()],
            complexity=1,
        ))

del _op, _symbol, _desc, _type, _suffix

# Special variant: Multiply (Audio by Float) — mixes Audio input with Float gain
_register(_node(
    "Multiply (Audio by Float)", "Math",
    "Multiplies audio signal by a float gain value. Common for volume/amplitude control.",
    [_in("PrimaryOperand", "Audio"),
     _in("AdditionalOperands", "Float", default=1.0)],
    [_out("Out", "Audio")],
    ["math", "multiply", "*", "arithmetic", "gain", "volume", "amplitude"],
    complexity=1,
))

# Unary / utility math
_register(_node(
    "Abs", "Math",
    "Returns the absolute value of a float.",
    [_in("Value", "Float")],
    [_out("Result", "Float")],
    ["math", "abs", "absolute", "magnitude"],
    complexity=1,
))


_register(_node(
    "Log", "Math",
    "Computes the natural logarithm of a float.",
    [_in("Value", "Float")],
    [_out("Result", "Float")],
    ["math", "log", "logarithm", "natural"],
    complexity=1,
))

_register(_node(
    "Power", "Math",
    "Raises base to the power of exponent.",
    [_in("Base", "Float"),
     _in("Exponent", "Float", default=2.0)],
    [_out("Result", "Float")],
    ["math", "power", "exponent", "pow", "square"],
    complexity=1,
))

_register(_node(
    "Modulo", "Math",
    "Returns the remainder of dividing A by B.",
    [_in("A", "Float"),
     _in("B", "Float", default=1.0)],
    [_out("Result", "Float")],
    ["math", "modulo", "remainder", "mod", "wrap"],
    complexity=1,
))


_register(_node(
    "Float Compare", "Math",
    "Compares two float values and outputs a boolean. CompareOp: LessThan, GreaterThan, Equals, LessThanOrEqual, GreaterThanOrEqual.",
    [_in("A", "Float"),
     _in("B", "Float"),
     _in("CompareOp", "Enum", default="LessThan")],
    [_out("Result", "Bool")],
    ["math", "compare", "less", "greater", "equals", "condition", "boolean"],
    complexity=1,
))

_register(_node(
    "Min", "Math",
    "Returns the smaller of two float values.",
    [_in("A", "Float"), _in("B", "Float")],
    [_out("Value", "Float")],
    ["math", "min", "minimum", "compare", "smaller"],
    complexity=1,
))

_register(_node(
    "Max", "Math",
    "Returns the larger of two float values.",
    [_in("A", "Float"), _in("B", "Float")],
    [_out("Value", "Float")],
    ["math", "max", "maximum", "compare", "larger"],
    complexity=1,
))

_register(_node(
    "Filter Q To Bandwidth", "Math",
    "Converts filter Q factor to bandwidth value (octaves).",
    [_in("Q", "Float", default=0.707)],
    [_out("Bandwidth", "Float")],
    ["math", "convert", "Q", "bandwidth", "filter"],
    complexity=1,
))


_register(_node(
    "InterpTo", "Math",
    "Smoothly interpolates from internal value toward target over time. "
    "NO Current input — maintains state internally. Pin names verified from engine exports.",
    [_in("Interp Time", "Time", required=False),
     _in("Target", "Float", required=False)],
    [_out("Value", "Float")],
    ["math", "smooth", "interpolation", "transition", "lerp", "glide", "ease"],
    complexity=2,
    class_name="UE::InterpTo::Audio",
))



_register(_node(
    "Clamp (Audio)", "Math",
    "Clamps audio signal between min and max values.",
    [_in("In", "Audio"),
     _in("Min", "Audio"),
     _in("Max", "Audio")],
    [_out("Value", "Audio")],
    ["math", "clamp", "limit", "audio"],
    complexity=1,
))

_register(_node(
    "Clamp (Float)", "Math",
    "Clamps float value between min and max.",
    [_in("In", "Float"),
     _in("Min", "Float"),
     _in("Max", "Float")],
    [_out("Value", "Float")],
    ["math", "clamp", "limit", "float"],
    complexity=1,
))

_register(_node(
    "Clamp (Int32)", "Math",
    "Clamps integer value between min and max.",
    [_in("In", "Int32"),
     _in("Min", "Int32"),
     _in("Max", "Int32")],
    [_out("Value", "Int32")],
    ["math", "clamp", "limit", "integer"],
    complexity=1,
))

_register(_node(
    "Map Range (Audio)", "Math",
    "Maps audio signal from one range to another.",
    [_in("In", "Audio"),
     _in("In Range A", "Float", default=-1.0),
     _in("In Range B", "Float", default=1.0),
     _in("Out Range A", "Float", default=-1.0),
     _in("Out Range B", "Float", default=1.0),
     _in("Clamped", "Bool", default=True)],
    [_out("Out Value", "Audio")],
    ["math", "map", "range", "scale", "audio"],
    complexity=2,
))

_register(_node(
    "Map Range (Float)", "Math",
    "Maps float value from one range to another.",
    [_in("In", "Float"),
     _in("In Range A", "Float", default=0.0),
     _in("In Range B", "Float", default=1.0),
     _in("Out Range A", "Float", default=0.0),
     _in("Out Range B", "Float", default=1.0),
     _in("Clamped", "Bool", default=True)],
    [_out("Out Value", "Float")],
    ["math", "map", "range", "scale", "float"],
    complexity=2,
))

_register(_node(
    "Map Range (Int32)", "Math",
    "Maps integer value from one range to another.",
    [_in("In", "Int32"),
     _in("In Range A", "Int32", default=0),
     _in("In Range B", "Int32", default=100),
     _in("Out Range A", "Int32", default=0),
     _in("Out Range B", "Int32", default=100),
     _in("Clamped", "Bool", default=True)],
    [_out("Out Value", "Int32")],
    ["math", "map", "range", "scale", "integer"],
    complexity=2,
))

_register(_node(
    "Add (Float)", "Math",
    "Adds two float values.",
    [_in("PrimaryOperand", "Float", default=0.0),
     _in("AdditionalOperands", "Float", default=0.0)],
    [_out("Out", "Float")],
    ["math", "add", "plus", "sum", "float"],
    complexity=1,
))

_register(_node(
    "Subtract (Float)", "Math",
    "Subtracts float values.",
    [_in("PrimaryOperand", "Float", default=0.0),
     _in("AdditionalOperands", "Float", default=0.0)],
    [_out("Out", "Float")],
    ["math", "subtract", "minus", "difference", "float"],
    complexity=1,
))

_register(_node(
    "Multiply (Float)", "Math",
    "Multiplies two float values.",
    [_in("PrimaryOperand", "Float", default=1.0),
     _in("AdditionalOperands", "Float", default=1.0)],
    [_out("Out", "Float")],
    ["math", "multiply", "times", "product", "float"],
    complexity=1,
))

_register(_node(
    "Divide (Float)", "Math",
    "Divides float values.",
    [_in("PrimaryOperand", "Float", default=1.0),
     _in("AdditionalOperands", "Float", default=1.0)],
    [_out("Out", "Float")],
    ["math", "divide", "quotient", "float"],
    complexity=1,
))

_register(_node(
    "InterpTo (Audio)", "Math",
    "Interpolates towards target value over time. Same as InterpTo node. "
    "Pin names verified from engine exports.",
    [_in("Interp Time", "Time"),
     _in("Target", "Float")],
    [_out("Value", "Float")],
    ["math", "interpolate", "smooth", "lerp", "audio"],
    complexity=2,
    class_name="UE::InterpTo::Audio",
))

_register(_node(
    "Semitone To Freq Multiplier", "Math",
    "Converts semitone offset to frequency multiplier.",
    [_in("Semitones", "Float", default=0.0)],
    [_out("Frequency Multiplier", "Float")],
    ["math", "music", "pitch", "semitone", "frequency"],
    complexity=1,
))


# -------------------------------------------------------------------
# Mix  (2 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Mono Mixer", "Mix",
    "Mixes N mono audio inputs into a single mono output with per-input gain. "
    "Real UE5 pin names: In 0..N, Gain 0..N (Lin), Out.",
    [_in("In 0", "Audio"),
     _in("Gain 0", "Float", default=1.0),
     _in("In 1", "Audio", required=False),
     _in("Gain 1", "Float", required=False, default=1.0),
     _in("In 2", "Audio", required=False),
     _in("Gain 2", "Float", required=False, default=1.0),
     _in("In 3", "Audio", required=False),
     _in("Gain 3", "Float", required=False, default=1.0)],
    [_out("Out", "Audio")],
    ["mix", "mixer", "mono", "sum", "combine", "bus"],
    complexity=1,
))

_register(_node(
    "Audio Mixer (Mono, 2)", "Mix",
    "2-input mono mixer — real UE5 node name. Mixes two mono signals with per-input gain.",
    [_in("In 0", "Audio"),
     _in("Gain 0", "Float", default=1.0),
     _in("In 1", "Audio", required=False),
     _in("Gain 1", "Float", required=False, default=1.0)],
    [_out("Out", "Audio")],
    ["mix", "mixer", "mono", "sum", "combine", "audio mixer"],
    complexity=1,
))

_register(_node(
    "Audio Mixer (Mono, 3)", "Mix",
    "3-input mono mixer — real UE5 node name. Mixes three mono signals with per-input gain. "
    "Engine class: AudioMixer::Audio Mixer (Mono, 3)::None. Pin names verified from exports.",
    [_in("In 0", "Audio"),
     _in("Gain 0", "Float", default=1.0),
     _in("In 1", "Audio", required=False),
     _in("Gain 1", "Float", required=False, default=1.0),
     _in("In 2", "Audio", required=False),
     _in("Gain 2", "Float", required=False, default=1.0)],
    [_out("Out", "Audio")],
    ["mix", "mixer", "mono", "sum", "combine", "audio mixer"],
    complexity=1,
))

_register(_node(
    "Audio Mixer (Mono, 4)", "Mix",
    "4-input mono mixer with per-input gain. Pins: In 0..3, Gain 0..3, Out.",
    [_in("In 0", "Audio"),
     _in("Gain 0", "Float", default=1.0),
     _in("In 1", "Audio", required=False),
     _in("Gain 1", "Float", required=False, default=1.0),
     _in("In 2", "Audio", required=False),
     _in("Gain 2", "Float", required=False, default=1.0),
     _in("In 3", "Audio", required=False),
     _in("Gain 3", "Float", required=False, default=1.0)],
    [_out("Out", "Audio")],
    ["mix", "mixer", "mono", "sum", "combine", "audio mixer"],
    complexity=1,
))

_register(_node(
    "Audio Mixer (Stereo, 2)", "Mix",
    "2-input stereo mixer — real UE5 node name. Mixes two stereo pairs with per-input gain. "
    "Pin names use 'In N L/R' format. From Chris Payne Sound Pads project binary extraction.",
    [_in("In 0 L", "Audio"), _in("In 0 R", "Audio"),
     _in("Gain 0", "Float", default=1.0),
     _in("In 1 L", "Audio", required=False), _in("In 1 R", "Audio", required=False),
     _in("Gain 1", "Float", required=False, default=1.0)],
    [_out("Out L", "Audio"),
     _out("Out R", "Audio")],
    ["mix", "mixer", "stereo", "sum", "combine", "audio mixer"],
    complexity=2,
))


_register(_node(
    "Audio Mixer (Stereo, 3)", "Mix",
    "Mixes 3 stereo audio inputs with individual gain controls.",
    [_in("In 0 L", "Audio"), _in("In 0 R", "Audio"), _in("Gain 0", "Float", required=False, default=1.0),
     _in("In 1 L", "Audio"), _in("In 1 R", "Audio"), _in("Gain 1", "Float", required=False, default=1.0),
     _in("In 2 L", "Audio"), _in("In 2 R", "Audio"), _in("Gain 2", "Float", required=False, default=1.0)],
    [_out("Out L", "Audio"), _out("Out R", "Audio")],
    ["mixer", "stereo", "audio", "gain", "summing"],
    complexity=1,
    class_name="AudioMixer::Audio Mixer (Stereo, 3)::None",
))

_register(_node(
    "Stereo Mixer", "Mix",
    "Mixes N stereo audio input pairs into a single stereo output with per-input gain. "
    "Real UE5 pin names: In N L/R, Gain N (Lin), Out L/R. "
    "Variant suffix (N) sets input count: Stereo Mixer (2), (3), (4), (8).",
    [_in("In 0 L", "Audio"), _in("In 0 R", "Audio", required=False),
     _in("Gain 0", "Float", default=1.0),
     _in("In 1 L", "Audio", required=False), _in("In 1 R", "Audio", required=False),
     _in("Gain 1", "Float", required=False, default=1.0),
     _in("In 2 L", "Audio", required=False), _in("In 2 R", "Audio", required=False),
     _in("Gain 2", "Float", required=False, default=1.0),
     _in("In 3 L", "Audio", required=False), _in("In 3 R", "Audio", required=False),
     _in("Gain 3", "Float", required=False, default=1.0)],
    [_out("Out L", "Audio"),
     _out("Out R", "Audio")],
    ["mix", "mixer", "stereo", "sum", "combine", "bus"],
    complexity=2,
))


# -------------------------------------------------------------------
# Spatialization  (3 nodes)
# -------------------------------------------------------------------

_register(_node(
    "ITD Panner", "Spatialization",
    "Interaural Time Difference panner for binaural 3D audio on headphones.",
    [_in("In", "Audio"),
     _in("Angle", "Float"),
     _in("Distance Factor", "Float"),
     _in("Head Width", "Float", required=False)],
    [_out("Out Left", "Audio"),
     _out("Out Right", "Audio")],
    ["spatial", "3d", "binaural", "HRTF", "headphones", "panner", "ITD",
     "azimuth", "elevation"],
    complexity=3,
))

_register(_node(
    "Stereo Panner", "Spatialization",
    "Simple stereo pan from left (-1) to right (+1) for speaker output.",
    [_in("In", "Audio"),
     _in("Pan Amount", "Float")],
    [],
    ["spatial", "pan", "stereo", "speakers", "left", "right", "balance"],
    complexity=1,
))

_register(_node(
    "MSP_HeightEQ_Node", "Spatialization",
    "Height-based EQ for 3D spatialization. Applies frequency shaping based on "
    "azimuth and elevation angles for realistic height perception. From Craig Owen tutorial.",
    [_in("Audio", "Audio"),
     _in("UE.Spatialization.Azimuth", "Float", required=False, default=0.0),
     _in("UE.Spatialization.Elevation", "Float")],
    [_out("Output", "Audio")],
    ["spatial", "height", "EQ", "3d", "binaural", "azimuth", "elevation",
     "spatialization", "HRTF"],
    complexity=2,
))

_register(_node(
    "Mid-Side Encode/Decode", "Spatialization",
    "Converts between stereo L/R and mid/side representation for width control.",
    [_in("Audio L", "Audio"),
     _in("Audio R", "Audio"),
     _in("Mode", "Enum", default="Encode"),
     _in("Width", "Float", required=False, default=1.0)],
    [_out("Out A", "Audio"),
     _out("Out B", "Audio")],
    ["stereo", "width", "mid", "side", "encode", "decode", "spatial", "image"],
    complexity=2,
))


# -------------------------------------------------------------------
# Music  (5 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Frequency To MIDI", "Music",
    "Converts a frequency in Hz to a MIDI note number.",
    [_in("Frequency In", "Float")],
    [_out("Out MIDI", "Float")],
    ["music", "frequency", "MIDI", "convert", "note", "pitch"],
    complexity=1,
))

_register(_node(
    "MIDI To Frequency", "Music",
    "Converts a MIDI note number to frequency in Hz. "
    "Engine class: UE::MIDI To Frequency::Float. Input is Float (supports fractional MIDI). "
    "Best practice: send MIDI values from Blueprint, convert to Hz here inside MetaSounds.",
    [_in("MIDI In", "Float", default=69.0)],
    [_out("Out Frequency", "Float")],
    ["music", "MIDI", "frequency", "convert", "note", "pitch", "Hz"],
    complexity=1,
))

_register(_node(
    "MIDI Note Quantizer", "Music",
    "Quantizes a MIDI note number to the nearest note in a given scale. "
    "Engine class: UE::MIDI Note Quantizer::Audio. All pins are Float type.",
    [_in("Note In", "Float"),
     _in("Root Note", "Float", required=False, default=0.0),
     _in("Scale Range In", "Float", required=False),
     _in("Scale Degrees", "Float[]")],
    [_out("Note Out", "Float")],
    ["music", "MIDI", "quantize", "scale", "snap", "tuning"],
    complexity=2,
))

_register(_node(
    "Scale to Note Array", "Music",
    "Generates an array of MIDI note numbers or frequencies for a musical scale.",
    [_in("Root Note", "Int32", default=60),
     _in("Scale Degrees", "Array", required=False),
     _in("Next", "Trigger", required=False),
     _in("Reset", "Trigger", required=False),
     _in("Seed", "Int32", required=False)],
    [_out("Scale Array Out", "Array"),
     _out("Value", "Float")],
    ["music", "scale", "notes", "array", "melody", "chord"],
    complexity=2,
))

_register(_node(
    "Musical Scale To Note Array", "Music",
    "Generates a note array from a musical scale enum. Real UE5 node name from exports.",
    [_in("Scale Degrees", "Enum", required=False),
     _in("Chord Tones Only", "Bool", required=False, default=False)],
    [_out("Scale Array Out", "Float[]")],
    ["music", "scale", "notes", "array", "chord", "melody"],
    complexity=2,
))

_register(_node(
    "BPM To Seconds", "Music",
    "Converts beats per minute to a time duration per beat in seconds. "
    "Engine class: UE::BPMToSeconds::None. Output is Time type.",
    [_in("BPM", "Float", default=120.0),
     _in("Beat Multiplier", "Float", default=1.0),
     _in("Divisions of Whole Note", "Float", default=4.0)],
    [_out("Seconds", "Time")],
    ["music", "BPM", "tempo", "beat", "time", "clock", "rhythm"],
    complexity=1,
))


# -------------------------------------------------------------------
# Random  (4 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Random Bool", "Random",
    "Generates a random boolean value when triggered.",
    [_in("Trigger", "Trigger"),
     _in("Probability", "Float", required=False, default=0.5),
     _in("Seed", "Int32", required=False, default=-1)],
    [_out("Value", "Bool"),
     _out("Trigger", "Trigger")],
    ["random", "bool", "chance", "probability", "coin flip"],
    complexity=1,
))

_register(_node(
    "Random Float", "Random",
    "Generates a random float within a range when triggered. "
    "Engine class: UE::RandomFloat::None. Pin names verified from exports.",
    [_in("Next", "Trigger"),
     _in("Reset", "Trigger", required=False),
     _in("Seed", "Int32", required=False, default=-1),
     _in("Min", "Float", default=0.0),
     _in("Max", "Float", default=1.0)],
    [_out("On Next", "Trigger"),
     _out("On Reset", "Trigger"),
     _out("Value", "Float")],
    ["random", "float", "variation", "procedural", "range", "jitter"],
    complexity=1,
))

_register(_node(
    "Random Int", "Random",
    "Generates a random integer within a range when triggered. "
    "Engine class: UE::RandomInt32::None. Pin names verified from exports.",
    [_in("Next", "Trigger"),
     _in("Reset", "Trigger", required=False),
     _in("Seed", "Int32", required=False, default=-1),
     _in("Min", "Int32", default=0),
     _in("Max", "Int32", default=10)],
    [_out("On Next", "Trigger"),
     _out("On Reset", "Trigger"),
     _out("Value", "Int32")],
    ["random", "int", "integer", "variation", "procedural", "range"],
    complexity=1,
))

_register(_node(
    "Random Time", "Random",
    "Generates a random time duration within a range when triggered.",
    [_in("Trigger", "Trigger"),
     _in("Min", "Time", default=0.1),
     _in("Max", "Time", default=1.0),
     _in("Seed", "Int32", required=False, default=-1)],
    [_out("Value", "Time"),
     _out("Trigger", "Trigger")],
    ["random", "time", "duration", "variation", "procedural", "interval"],
    complexity=1,
))


# -------------------------------------------------------------------
# Debug  (2 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Get Wave Info", "Debug",
    "Extracts metadata from a WaveAsset: channel count, sample rate, duration.",
    [_in("Wave", "Float", required=False)],
    [_out("Duration", "Time"),
     _out("Path", "String")],
    ["debug", "wave", "info", "metadata", "channels", "sample rate", "duration"],
    complexity=1,
))

_register(_node(
    "Get Wave Duration", "Debug",
    "Returns the duration of a WaveAsset in seconds. Simpler alternative to Get Wave Info.",
    [_in("Wave", "WaveAsset")],
    [_out("Duration", "Time")],
    ["wave", "duration", "length", "time", "info", "utility"],
    complexity=1,
))

_register(_node(
    "Print Log", "Debug",
    "Prints a string to the output log when triggered.",
    [_in("Trigger", "Trigger", required=False),
     _in("Label", "String", required=False, default="MetaSound"),
     _in("Value To Log", "Trigger")],
    [],
    ["debug", "print", "log", "console", "trace"],
    complexity=1,
))


# -------------------------------------------------------------------
# External IO  (2 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Audio Bus Reader", "External IO",
    "Reads audio from a submix bus for routing or analysis.",
    [_in("Audio Bus", "WaveAsset", required=False)],
    [_out("Out X", "Audio")],
    ["bus", "submix", "read", "external", "routing", "input"],
    complexity=2,
))

_register(_node(
    "Wave Writer", "External IO",
    "Records audio to a WAV file on disk.",
    [_in("Filename Prefix", "String"),
     _in("Enabled", "Bool", required=False, default=True),
     _in("In X", "Audio", required=False)],
    [],
    ["wave", "writer", "record", "export", "file", "WAV", "capture"],
    complexity=2,
))


# -------------------------------------------------------------------
# General / Utility  (6 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Flanger", "General",
    "Flanger effect using modulated short delay line.",
    [_in("In Audio", "Audio"),
     _in("Modulation Rate", "Float"),
     _in("Modulation Depth", "Float"),
     _in("Feedback", "Float", required=False, default=0.0),
     _in("Center Delay", "Time", default=0.002),
     _in("Mix Level", "Float", default=0.5)],
    [_out("Out Audio", "Audio")],
    ["modulation", "chorus", "effect", "flanger", "sweep", "jet"],
    complexity=2,
))

_register(_node(
    "Ring Mod", "General",
    "Ring modulator -- multiplies audio by a modulation oscillator.",
    [_in("Audio", "Audio"),
     _in("ModFrequency", "Float", default=440.0),
     _in("DryWet", "Float", required=False, default=1.0)],
    [_out("Audio", "Audio")],
    ["modulation", "metallic", "effect", "ring", "inharmonic", "bell"],
    complexity=2,
))

_register(_node(
    "Wave Shaper", "General",
    "Waveshaping distortion -- soft clipping to hard clipping based on amount.",
    [_in("Audio", "Audio"),
     _in("Amount", "Float", default=0.5),
     _in("DryWet", "Float", required=False, default=1.0)],
    [_out("Audio", "Audio")],
    ["distortion", "saturation", "overdrive", "waveshaper", "clip", "warm",
     "crunch"],
    complexity=2,
))

_register(_node(
    "Get WaveTable From Bank", "General",
    "Extracts a single wavetable from a wavetable bank asset by index.",
    [_in("WaveTableBank", "WaveAsset"),
     _in("TableIndex", "Int32")],
    [_out("Out", "Audio")],
    ["wavetable", "bank", "get", "extract", "index"],
    complexity=1,
))

_register(_node(
    "Send", "General",
    "Routes audio to a named bus or side-chain destination.",
    [_in("Audio", "Audio"),
     _in("Bus Name", "String"),
     _in("SendLevel", "Float", default=1.0)],
    [],
    ["send", "bus", "routing", "sidechain", "aux", "effect send"],
    complexity=1,
))

_register(_node(
    "Convert", "General",
    "Converts between compatible MetaSound data types.",
    [_in("Value", "Float")],
    [_out("Result", "Time")],
    ["convert", "type", "cast", "utility"],
    complexity=1,
))

_register(_node(
    "Audio To Float", "General",
    "Converts an audio-rate signal to a block-rate float value. "
    "Engine class: UE::ConversionAudioToFloat::None. Pin names verified from exports.",
    [_in("In", "Audio")],
    [_out("Out", "Float")],
    ["convert", "audio", "float", "rate", "block", "sample"],
    complexity=1,
))

_register(_node(
    "Float To Int", "General",
    "Converts a Float value to Int32 (truncation).",
    [_in("Value", "Float")],
    [_out("Result", "Int32")],
    ["convert", "float", "int", "cast", "utility"],
    complexity=1,
))

_register(_node(
    "Int To Float", "General",
    "Converts an Int32 value to Float.",
    [_in("Value", "Int32")],
    [_out("Result", "Float")],
    ["convert", "int", "float", "cast", "utility"],
    complexity=1,
))

_register(_node(
    "Float To Time", "General",
    "Converts float value to Time type.",
    [_in("In", "Float")],
    [_out("Out", "Time")],
    ["convert", "float", "time", "type"],
    complexity=1,
))

_register(_node(
    "Time To Float", "General",
    "Converts Time type to float value.",
    [_in("In", "Time")],
    [_out("Out", "Float")],
    ["convert", "time", "float", "type"],
    complexity=1,
))

_register(_node(
    "Send (Audio)", "General",
    "Sends audio to an external address via transmission system.",
    [_in("Address", "Transmission:Address"),
     _in("Audio", "Audio")],
    [],
    ["send", "external", "transmission", "output"],
    complexity=2,
))


_register(_node(
    "Get Variable", "General",
    "Reads the current value of a graph variable.",
    [],
    [_out("Value", "Float")],
    ["variable", "state", "get", "read", "graph variable"],
    complexity=1,
))

_register(_node(
    "Set Variable", "General",
    "Writes a new value to a graph variable. Execute pin triggers the write.",
    [_in("Value", "Float"),
     _in("Execute", "Trigger")],
    [],
    ["variable", "state", "set", "write", "graph variable"],
    complexity=1,
))


# -------------------------------------------------------------------
# Patches (reusable sub-graphs from Craig Owen tutorial)
# -------------------------------------------------------------------

_register(_node(
    "MSP_RandomizationNode", "Patches",
    "Wave asset array player with per-shot pitch and volume randomization. "
    "Selects from WaveAsset array on each Next trigger, applies random pitch/volume offsets. "
    "Used for weapon burst round-robin layers. From Craig Owen weapon burst tutorial.",
    [_in("In Array", "WaveAsset[]"),
     _in("Next", "Trigger"),
     _in("Pitch_RandomMax", "Float", required=False, default=0.0),
     _in("Pitch_RandomMin", "Float", required=False, default=0.0),
     _in("Volume_Master", "Float", required=False, default=1.0),
     _in("Volume_RandomMax", "Float", required=False, default=1.1),
     _in("Volume_RandomMin", "Float", required=False, default=0.9)],
    [_out("On Finished", "Trigger"),
     _out("On Nearly Finished", "Trigger"),
     _out("Out", "Audio"),
     _out("Value", "Float")],
    ["randomization", "wave", "variation", "weapon", "gunshot", "pitch", "volume",
     "patch", "reusable", "round-robin"],
    complexity=3,
))

_register(_node(
    "MSP_CrossFadeByParam_3Inputs", "Patches",
    "3-layer distance crossfade patch. Each layer: Shuffle→WavePlayer→MapRange gain→StereoMixer. "
    "Includes optimization gates (only processes active layers) and Mid-Side mono output. "
    "From Craig Owen weapon audio tutorial.",
    [_in("TriggerStart", "Trigger"),
     _in("InputParameter", "Float", default=0.0),
     _in("WaveAsset_A", "WaveAsset[]"),
     _in("WaveAsset_A_StartFadeOut", "Float", default=5000.0),
     _in("WaveAsset_A_EndFadeOut", "Float", default=7500.0),
     _in("WaveAsset_B", "WaveAsset[]"),
     _in("WaveAsset_B_StartFadeIn", "Float", default=5000.0),
     _in("WaveAsset_B_EndFadeIn", "Float", default=7500.0),
     _in("WaveAsset_B_StartFadeOut", "Float", default=15000.0),
     _in("WaveAsset_B_EndFadeOut", "Float", default=17500.0),
     _in("WaveAsset_C", "WaveAsset[]"),
     _in("WaveAsset_C_StartFadeIn", "Float", default=15000.0),
     _in("WaveAsset_C_EndFadeIn", "Float", default=17500.0)],
    [_out("OnFinished", "Trigger"),
     _out("Output_L", "Audio"),
     _out("Output_R", "Audio"),
     _out("AudioMono", "Audio")],
    ["crossfade", "distance", "layers", "weapon", "tail", "blend", "parameter",
     "patch", "reusable"],
    complexity=4,
))

_register(_node(
    "MSP_Switch_3Inputs", "Patches",
    "Hard switch between 3 WaveAsset array inputs based on an Int32 parameter (0/1/2). "
    "Used for room-size selection in weapon audio. Each input: Shuffle→WavePlayer→StereoMixer.",
    [_in("TriggerStart", "Trigger"),
     _in("InputParameter", "Int32", default=0),
     _in("WaveAsset_A", "WaveAsset[]"),
     _in("WaveAsset_B", "WaveAsset[]"),
     _in("WaveAsset_C", "WaveAsset[]")],
    [_out("OnFinished", "Trigger"),
     _out("Output_L", "Audio"),
     _out("Output_R", "Audio")],
    ["switch", "select", "room", "int32", "hard-switch", "patch", "reusable"],
    complexity=3,
))


# -------------------------------------------------------------------
# Effects — Spectral  (4 nodes, from SFX Generator screenshots)
# -------------------------------------------------------------------

_register(_node(
    "WaveShaper", "Effects",
    "Waveshaping distortion with configurable curve type. Amount controls drive, "
    "Bias shifts DC offset, OutputGain compensates volume. Type: Sine, HardClip, SoftClip, Tanh. "
    "From SFX Generator — first in spectral effects chain.",
    [_in("In", "Audio", required=False),
     _in("Amount", "Float", default=0.0),
     _in("Bias", "Float", required=False, default=0.0),
     _in("OutputGain", "Float", required=False, default=1.0)],
    [_out("Out", "Audio")],
    ["waveshaper", "distortion", "saturation", "overdrive", "shaping", "sine",
     "sfx", "spectral"],
    complexity=2,
))


_register(_node(
    "Ring Modulator", "Effects",
    "Ring modulation — multiplies input signal by a modulator oscillator. "
    "Built-in AD envelope controls modulator depth. Creates metallic, inharmonic tones. "
    "From SFX Generator — last in spectral effects chain.",
    [_in("In Carrier", "Audio", required=False),
     _in("In Modulator", "Audio", required=False)],
    [_out("Out Audio", "Audio")],
    ["ringmod", "ring", "modulator", "metallic", "inharmonic", "am",
     "sfx", "spectral"],
    complexity=3,
))

_register(_node(
    "Crossfade (Audio, 2)", "Effects",
    "Crossfades between two audio inputs based on a float value (0.0 = In 0, 1.0 = In 1). "
    "Used for wet/dry mixing on effects chains. From SFX Generator.",
    [_in("Crossfade Value", "Float", default=0.0),
     _in("In 0", "Audio"),
     _in("In 1", "Audio")],
    [_out("Out", "Audio")],
    ["crossfade", "blend", "mix", "wetdry", "interpolate"],
    complexity=1,
))


# -------------------------------------------------------------------
# Effects — Temporal  (3 nodes, from SFX Generator screenshots)
# -------------------------------------------------------------------

_register(_node(
    "Delay (Time)", "Effects",
    "Audio delay effect with feedback. Delay Time in seconds, "
    "Dry Level controls direct signal, Feedback controls repeats. "
    "From SFX Generator temporal effects section.",
    [_in("In", "Audio", required=False),
     _in("Delay Time", "Time", default=0.3),
     _in("Dry Level", "Float", required=False, default=0.0),
     _in("Feedback", "Float", required=False, default=0.5),
     _in("Wet Level", "Float", required=False),
     _in("Max Delay Time", "Time", required=False)],
    [_out("Out", "Audio")],
    ["delay", "echo", "repeat", "feedback", "temporal", "sfx"],
    complexity=2,
))

_register(_node(
    "Plate Reverb (Stereo)", "Effects",
    "Stereo plate reverb with bypass, separate dry/wet level controls. "
    "From SFX Generator temporal effects section.",
    [_in("Bypass", "Bool", required=False, default=False),
     _in("In Left", "Audio"),
     _in("In Right", "Audio"),
     _in("Dry Level", "Float", required=False, default=0.0),
     _in("Wet Level", "Float", required=False, default=1.0)],
    [_out("Out Left", "Audio"),
     _out("Out Right", "Audio")],
    ["reverb", "plate", "stereo", "space", "room", "temporal", "sfx"],
    complexity=3,
))

## Flanger already registered under General with pins Audio/Audio


# -------------------------------------------------------------------
# Utility — Frequency / Analysis  (4 nodes, from SFX Generator)
# -------------------------------------------------------------------

_register(_node(
    "Linear To Log Frequency", "Utility",
    "Maps a normalized 0-1 value to a logarithmic frequency range (Hz). "
    "Min/Max Domain define input range, Min/Max Range define output Hz range. "
    "Essential for frequency knobs: linear knob → perceptually even pitch. "
    "From SFX Generator base frequency section.",
    [_in("Value", "Float", default=0.5),
     _in("Min Domain", "Float", required=False, default=0.0),
     _in("Max Domain", "Float", required=False, default=1.0),
     _in("Min Range", "Float", required=False, default=20.0),
     _in("Max Range", "Float", required=False, default=20000.0)],
    [_out("Frequency", "Float")],
    ["frequency", "log", "linear", "mapping", "hz", "pitch", "knob",
     "normalize", "sfx"],
    complexity=2,
))

## Envelope Follower already registered under Envelopes with pins Audio/Envelope

_register(_node(
    "Trigger On Threshold (Audio)", "Utility",
    "Fires a trigger when audio signal crosses a threshold. "
    "Type: Rising Edge or Falling Edge. Used with Envelope Follower "
    "to detect when a sound finishes (signal drops below threshold). "
    "From SFX Generator output section.",
    [_in("In", "Audio"),
     _in("Threshold", "Float", default=0.01),
     _in("Type", "Enum", required=False, default="Falling Edge")],
    [_out("Out", "Trigger")],
    ["trigger", "threshold", "gate", "detection", "onset", "offset", "sfx"],
    complexity=2,
))

## Wave Writer already registered under External IO with pins Audio/Filename/Start


# ===================================================================
# Query / search helpers
# ===================================================================

# -------------------------------------------------------------------
# New nodes from Epic MetaSounds Reference (scraped 2026-02-08)
# -------------------------------------------------------------------

_register(_node(
    "ADSR Envelope", "Envelopes",
    "The ADSR Envelope node generates an attack-decay-sustain-release envelope value output when triggered. This node is similar to the AD Envelope node, but it requires a separate release trigger for t...",
    [     _in("Trigger Attack", "Trigger"),
     _in("Trigger Release", "Trigger"),
     _in("Attack Time", "Time"),
     _in("Delay Time", "Time"),
     _in("Sustain Level", "Float"),
     _in("Release Time", "Time"),
     _in("Attack Curve", "Float"),
     _in("Decay Curve", "Float"),
     _in("Release Curve", "Float")],
    [     _out("On Attack Triggered", "Trigger"),
     _out("On Decay Triggered", "Trigger"),
     _out("On Sustain Triggered", "Trigger"),
     _out("On Release Triggered", "Trigger"),
     _out("On Done", "Trigger"),
     _out("Out Envelope", "Audio")],
    ["adsr", "envelope", "envelopes"],
    complexity=2,
))

_register(_node(
    "Concatenate", "Array",
    "The Concatenate node concatenates two arrays on a given trigger.",
    [     _in("Trigger", "Trigger"),
     _in("Left / Right Array", "Array")],
    [     _out("Array", "Array")],
    ["concatenate", "array"],
    complexity=2,
))

_register(_node(
    "Get", "Array",
    "The Get node retrieves an element from an array at the given index.",
    [     _in("Trigger", "Trigger"),
     _in("Array", "Array"),
     _in("Index", "Int32")],
    [     _out("Element", "Float")],
    ["get", "array"],
    complexity=2,
))

_register(_node(
    "Mid-Side Decode", "Spatialization",
    "The Mid-Side Decode node converts a stereo signal with mid and side channels to left and right channels.",
    [     _in("In Mid / Side", "Float"),
     _in("Spread Amount", "Float"),
     _in("Equal Power", "Bool", required=False, default=False)],
    [     _out("Out Left / Right", "Audio")],
    ["mid-side", "decode", "spatialization"],
    complexity=2,
))

_register(_node(
    "Mid-Side Encode", "Spatialization",
    "The Mid-Side Encode node converts a stereo signal with left and right channels to mid and side channels.",
    [     _in("In Left / Right", "Float"),
     _in("Spread Amount", "Float"),
     _in("Equal Power", "Bool", required=False, default=False)],
    [     _out("Out Mid / Side", "Audio")],
    ["mid-side", "encode", "spatialization"],
    complexity=2,
))

_register(_node(
    "Num", "Array",
    "The Num node returns the number of elements in the given array.",
    [     _in("Array", "Array")],
    [     _out("Num", "Int32")],
    ["num", "array"],
    complexity=2,
))

_register(_node(
    "Set", "Array",
    "The Set node sets the value of a specified index in a given array.",
    [     _in("Trigger", "Trigger"),
     _in("Array", "Array"),
     _in("Index", "Int32"),
     _in("Value", "Float")],
    [     _out("Array", "Array")],
    ["set", "array"],
    complexity=2,
))

_register(_node(
    "Shuffle", "Array",
    "The Shuffle node outputs elements from a shuffled array.",
    [     _in("Next", "Trigger"),
     _in("Shuffle", "Array"),
     _in("Reset Seed", "Trigger", required=False),
     _in("In Array", "Array"),
     _in("Seed", "Int32"),
     _in("Auto Shuffle", "Bool"),
     _in("Enabled Shared State", "Bool", required=False, default=False)],
    [     _out("On Next", "Trigger"),
     _out("On Shuffle", "Trigger"),
     _out("On Reset Seed", "Trigger"),
     _out("Value", "Float")],
    ["shuffle", "array"],
    complexity=2,
))

_register(_node(
    "Subset", "Array",
    "The Subset node returns a subset of an input array.",
    [     _in("Trigger", "Trigger"),
     _in("Array", "Array"),
     _in("Start / End Index", "Float")],
    [     _out("Array", "Array")],
    ["subset", "array"],
    complexity=2,
))

_register(_node(
    "Trigger Select", "Triggers",
    "The Trigger Select node passes triggers through to the currently selected output trigger. This node has multiple versions for different input counts (between 2 and 8).",
    [     _in("In", "Audio"),
     _in("Index", "Int32")],
    [     _out("Out X", "Audio")],
    ["trigger", "select", "triggers"],
    complexity=2,
))

_register(_node(
    "Trigger Toggle", "Triggers",
    "The Trigger Toggle node toggles a Bool value on or off.",
    [     _in("On / Off", "Trigger"),
     _in("Init", "Float"),
     _in("Set", "Trigger"),
     _in("Reset", "Trigger", required=False),
     _in("Init Value", "Float"),
     _in("Target Value", "Trigger")],
    [     _out("Out", "Audio"),
     _out("Value", "Float"),
     _out("On Set", "Trigger"),
     _out("On Reset", "Trigger"),
     _out("Output Value", "Float")],
    ["trigger", "toggle", "triggers"],
    complexity=2,
))

_register(_node(
    "Wave Player", "General",
    "The Wave Player node is used to play a Sound Wave asset. There are multiple versions of this node in order to support several different channel configurations, such as Mono, Stereo, Quad (4.0), 5.1...",
    [     _in("Play", "Trigger", required=False),
     _in("Stop", "Trigger", required=False),
     _in("Wave Asset", "WaveAsset"),
     _in("Start Time", "Time", required=False),
     _in("Pitch Shift", "Float", required=False),
     _in("Loop", "Bool", required=False, default=False),
     _in("Loop Start", "Time", required=False),
     _in("Loop Duration", "Time", required=False)],
    [     _out("On Play", "Trigger"),
     _out("On Finished", "Trigger"),
     _out("On Nearly Finished", "Trigger"),
     _out("On Looped", "Trigger"),
     _out("On Cue Point", "Trigger"),
     _out("Cue Point ID", "Int32"),
     _out("Cue Point Label", "String"),
     _out("Loop Percent", "Float"),
     _out("Playback Location", "Float"),
     _out("Out Mono", "Audio")],
    ["wave", "player", "general"],
    complexity=2,
))

# -------------------------------------------------------------------
# ReSID SIDKIT Edition — MOS 6581/8580 emulation nodes (5 nodes)
# -------------------------------------------------------------------

_register(_node(
    "SID Oscillator", "ReSID SIDKIT Edition",
    "MOS 6581/8580 waveform generator. 24-bit accumulator with saw, triangle, pulse, noise, and combined waveforms from actual C64 chip samples.",
    [_in("Frequency", "Float", default=440.0),
     _in("Pulse Width", "Float", required=False, default=0.5),
     _in("Waveform", "Enum:SIDWaveform", default="Sawtooth"),
     _in("Chip Model", "Enum:SIDChipModel", required=False, default="MOS6581")],
    [_out("Out", "Audio")],
    ["sid", "oscillator", "c64", "chiptune", "retro", "waveform"],
    complexity=2,
))

_register(_node(
    "SID Envelope", "ReSID SIDKIT Edition",
    "MOS 6581/8580 ADSR envelope generator with non-linear exponential decay and authentic SID timing including the ADSR delay bug.",
    [_in("Gate", "Trigger"),
     _in("Attack", "Int32", default=0),
     _in("Decay", "Int32", default=9),
     _in("Sustain", "Int32", default=0),
     _in("Release", "Int32", default=9)],
    [_out("Out", "Audio")],
    ["sid", "envelope", "adsr", "c64", "chiptune", "retro"],
    complexity=2,
))

_register(_node(
    "SID Filter", "ReSID SIDKIT Edition",
    "MOS 6581/8580 analog filter emulation. Route any audio through the SID chip's non-linear two-integrator-loop biquad filter with voltage-controlled resistor model.",
    [_in("In", "Audio"),
     _in("Cutoff", "Float", default=0.5),
     _in("Resonance", "Float", required=False, default=0.0),
     _in("Mode", "Enum:SIDFilterMode", default="LowPass"),
     _in("Chip Model", "Enum:SIDChipModel", required=False, default="MOS6581"),
     _in("Res Boost", "Float", required=False, default=0.0)],
    [_out("Out", "Audio")],
    ["sid", "filter", "analog", "c64", "chiptune", "retro", "lo-fi"],
    complexity=2,
))

_register(_node(
    "SID Voice", "ReSID SIDKIT Edition",
    "Complete SID voice: oscillator x envelope. Combines waveform generation with ADSR in a single node for quick patching.",
    [_in("Gate", "Trigger"),
     _in("Frequency", "Float", default=440.0),
     _in("Pulse Width", "Float", required=False, default=0.5),
     _in("Waveform", "Enum:SIDWaveform", default="Sawtooth"),
     _in("Attack", "Int32", default=0),
     _in("Decay", "Int32", default=9),
     _in("Sustain", "Int32", default=0),
     _in("Release", "Int32", default=9),
     _in("Chip Model", "Enum:SIDChipModel", required=False, default="MOS6581")],
    [_out("Out", "Audio")],
    ["sid", "voice", "c64", "chiptune", "retro", "oscillator", "envelope"],
    complexity=2,
))

_register(_node(
    "SID Chip", "ReSID SIDKIT Edition",
    "Complete MOS 6581/8580 SID chip emulation. 3 voices with oscillator+envelope, analog filter, FM cross-modulation, and per-voice volume (SIDKIT extensions).",
    [_in("Gate 1", "Trigger"), _in("Freq 1", "Float", default=440.0),
     _in("PW 1", "Float", required=False, default=0.5),
     _in("Wave 1", "Enum:SIDWaveform", default="Sawtooth"),
     _in("A 1", "Int32", default=0), _in("D 1", "Int32", default=9),
     _in("S 1", "Int32", default=0), _in("R 1", "Int32", default=9),
     _in("Gate 2", "Trigger"), _in("Freq 2", "Float", default=440.0),
     _in("PW 2", "Float", required=False, default=0.5),
     _in("Wave 2", "Enum:SIDWaveform", default="Sawtooth"),
     _in("A 2", "Int32", default=0), _in("D 2", "Int32", default=9),
     _in("S 2", "Int32", default=0), _in("R 2", "Int32", default=9),
     _in("Gate 3", "Trigger"), _in("Freq 3", "Float", default=440.0),
     _in("PW 3", "Float", required=False, default=0.5),
     _in("Wave 3", "Enum:SIDWaveform", default="Sawtooth"),
     _in("A 3", "Int32", default=0), _in("D 3", "Int32", default=9),
     _in("S 3", "Int32", default=0), _in("R 3", "Int32", default=9),
     _in("Filter Cutoff", "Float", default=0.5),
     _in("Filter Resonance", "Float", required=False, default=0.0),
     _in("Filter Mode", "Enum:SIDFilterMode", default="LowPass"),
     _in("Filter Routing", "Int32", default=1),
     _in("Volume", "Float", default=1.0),
     _in("Chip Model", "Enum:SIDChipModel", required=False, default="MOS6581"),
     _in("Res Boost", "Float", required=False, default=0.0)],
    [_out("Out", "Audio"),
     _out("Voice 1 Out", "Audio"),
     _out("Voice 2 Out", "Audio"),
     _out("Voice 3 Out", "Audio")],
    ["sid", "chip", "c64", "chiptune", "retro", "fm", "filter", "3-voice"],
    complexity=4,
))


def get_nodes_by_category(category: str) -> list[NodeDef]:
    """Return all nodes belonging to a category (case-insensitive)."""
    cat_lower = category.lower()
    return [n for n in METASOUND_NODES.values() if n["category"].lower() == cat_lower]


def get_nodes_by_tag(tag: str) -> list[NodeDef]:
    """Return all nodes whose tags list contains the given tag (case-insensitive)."""
    tag_lower = tag.lower()
    return [n for n in METASOUND_NODES.values() if tag_lower in (t.lower() for t in n["tags"])]


def search_nodes(query: str) -> list[NodeDef]:
    """Substring search across node name, tags, and description (case-insensitive).

    Returns a list of matching nodes sorted by relevance:
      1. Name matches first
      2. Tag matches second
      3. Description matches last
    """
    q = query.lower()
    name_hits: list[NodeDef] = []
    tag_hits: list[NodeDef] = []
    desc_hits: list[NodeDef] = []
    seen: set[str] = set()

    for node in METASOUND_NODES.values():
        nid = node["name"]
        if q in node["name"].lower():
            name_hits.append(node)
            seen.add(nid)
        elif any(q in t.lower() for t in node["tags"]):
            tag_hits.append(node)
            seen.add(nid)
        elif q in node["description"].lower():
            if nid not in seen:
                desc_hits.append(node)
    return name_hits + tag_hits + desc_hits


def get_all_categories() -> dict[str, int]:
    """Return a dict of category name -> number of nodes in that category."""
    counts: dict[str, int] = {}
    for node in METASOUND_NODES.values():
        cat = node["category"]
        counts[cat] = counts.get(cat, 0) + 1
    return dict(sorted(counts.items()))


# ===================================================================
# CLASS_NAME_TO_DISPLAY — reverse mapping from UE class names to
# our display names.  Single source of truth used by:
#   - scripts/convert_export_to_template.py
#   - _inline_convert() in tools/ms_builder.py
# ===================================================================

CLASS_NAME_TO_DISPLAY: dict[str, str] = {
    # --- Generators ---
    "UE::Sine::Audio": "Sine",
    "UE::Saw::Audio": "Saw",
    "UE::Square::Audio": "Square",
    "UE::Triangle::Audio": "Triangle",
    "UE::LFO::Audio": "Low-Frequency Oscillator",
    "UE::Noise::Audio": "Noise",
    # --- Wave Players ---
    "UE::Wave Player::Mono": "Wave Player (Mono)",
    "UE::Wave Player::Stereo": "Wave Player (Stereo)",
    # --- Envelopes ---
    "AD Envelope::AD Envelope::Audio": "AD Envelope",
    # --- Dynamics ---
    "UE::Compressor::Audio": "Compressor",
    # --- Filters ---
    "UE::Ladder Filter::Audio": "Ladder Filter",
    "UE::State Variable Filter::Audio": "State Variable Filter",
    "UE::One-Pole Low Pass Filter::Audio": "One-Pole Low Pass Filter",
    "UE::One-Pole High Pass Filter::Audio": "One-Pole High Pass Filter",
    "UE::Biquad Filter::Audio": "Biquad Filter",
    "UE::Bitcrusher::Audio": "Bitcrusher",
    # --- Effects ---
    "UE::Delay::Audio": "Delay (Audio)",
    "UE::Stereo Delay::Audio": "Stereo Delay",
    "UE::Plate Reverb::Stereo": "Plate Reverb (Stereo)",
    # --- Math ---
    "UE::Add::Audio": "Add (Audio)",
    "UE::Add::Float": "Add (Float)",
    "UE::Add::Int32": "Add (Int32)",
    "UE::Subtract::Audio": "Subtract (Audio)",
    "UE::Subtract::Float": "Subtract (Float)",
    "UE::Multiply::Audio": "Multiply (Audio)",
    "UE::Multiply::Float": "Multiply (Float)",
    "UE::Divide::Float": "Divide (Float)",
    # --- Mix ---
    "AudioMixer::Audio Mixer (Mono, 2)::None": "Audio Mixer (Mono, 2)",
    "AudioMixer::Audio Mixer (Stereo, 2)::None": "Audio Mixer (Stereo, 2)",
    # --- Spatialization ---
    # --- Gain ---
    # --- Music ---
    "UE::BPMToSeconds::None": "BPM To Seconds",
    "UE::MIDI To Frequency::Float": "MIDI To Frequency",
    "UE::MIDI Note Quantizer::Audio": "MIDI Note Quantizer",
    "UE::Musical Scale To Note Array::Audio": "Musical Scale To Note Array",
    # --- Triggers ---
    "UE::TriggerRepeat::None": "Trigger Repeat",
    "UE::Trigger Counter::None": "Trigger Counter",
    "UE::Trigger Filter::None": "Trigger Filter",
    # --- Random ---
    "UE::RandomInt32::None": "Random Int",
    "UE::RandomFloat::None": "Random Float",
    # --- Interpolation ---
    "UE::InterpTo::Audio": "InterpTo (Audio)",
    # --- Effects (specific) ---
    "UE::WaveShaper::Audio": "WaveShaper",
    # --- Converters ---
    "Convert::Float::Int32": "Float To Int",
    "Convert::Int32::Float": "Int To Float",
    # --- Engine-verified additions (2026-02-12 audit) ---
    # Fixed/corrected class_names (2026-02-12)
    "AD Envelope::AD Envelope::Audio": "AD Envelope (Audio)",
    "AD Envelope::AD Envelope::Float": "AD Envelope (Float)",
    "Clamp::Clamp::Audio": "Clamp (Audio)",
    "Clamp::Clamp::Float": "Clamp (Float)",
    "Clamp::Clamp::Int32": "Clamp (Int32)",
    "Crossfade::Trigger Route (Audio, 2)::Audio": "Crossfade (Audio, 2)",
    "Delay::Delay::AudioBufferDelayTime": "Delay",
    "MapRange::MapRange::Audio": "Map Range (Audio)",
    "MapRange::MapRange::Float": "Map Range (Float)",
    "MapRange::MapRange::Int32": "Map Range (Int32)",
    "UE::ConversionFloatToTime::None": "Float To Time",
    "UE::ConversionTimeToFloat::None": "Time To Float",
    "UE::Semitone to Frequency Multiplier::Float": "Semitone To Freq Multiplier",
    "Send::Audio::None": "Send (Audio)",
    "TriggerRoute::Trigger Route (Audio, 2)::Audio": "Trigger Route",
    "UE::Envelope Follower::None": "Envelope Follower",
    "UE::Flanger::None": "Flanger",
    "UE::ITD Panner::None": "ITD Panner",
    "UE::Linear To Log Frequency::None": "Linear To Log Frequency",
    "UE::Stereo Panner::None": "Stereo Panner",
    "UE::Trigger Counter::None": "Trigger Counter",
    "UE::TriggerRepeat::None": "Trigger Repeat",
    "UE::TriggerOnThreshold::Audio": "Trigger On Threshold",
    "UE::Trigger Sequence (2)::None": "Trigger Sequence",
    "UE::Frequency to MIDI::Float": "Frequency To MIDI",
    "UE::RingMod::Audio": "Ring Modulator",
    "AudioMixer::Audio Mixer (Mono, 2)::None": "Mono Mixer",
    "AudioMixer::Audio Mixer (Stereo, 2)::None": "Stereo Mixer",
    # Generators
    "UE::Additive Synth::None": "Additive Synth",
    "UE::Perlin Noise (audio)::Audio": "Perlin Noise",
    "UE::Lfo Frequency Noise::Audio": "Low Frequency Noise",
    "UE::SuperOscillatorMono::Audio": "SuperOscillator",
    # Wave Players
    "UE::Wave Player::Quad": "Wave Player (Quad)",
    "UE::Wave Player::5dot1": "Wave Player (5.1)",
    "UE::Wave Player::7dot1": "Wave Player (7.1)",
    "UE::WaveTablePlayer::None": "WaveTable Player",
    "UE::WaveTableOscillator::None": "WaveTable Oscillator",
    # Envelopes
    "ADSR Envelope::ADSR Envelope::Audio": "ADSR Envelope",
    "ADSR Envelope::ADSR Envelope::Float": "ADSR Envelope (Float)",
    "UE::WaveTableEnvelope::None": "WaveTable Envelope",
    "UE::WaveTableEvaluate::None": "Evaluate WaveTable",
    "UE::Envelope Follower::None": "Envelope Follower",
    # Delays
    "UE::Delay Pitch Shift::Audio": "Delay Pitch Shift",
    "UE::Diffuser::Audio": "Diffuser",
    "UE::GrainDelayNode::Audio": "Grain Delay",
    # Dynamics
    "UE::Limiter::Audio": "Limiter",
    "UE::Decibels to Linear Gain::Float": "Decibels to Linear Gain",
    "UE::Linear Gain to Decibels::Float": "Linear Gain to Decibels",
    # Filters
    "UE::DynamicFilter::Audio": "Dynamic Filter",
    "SampleAndHold::Sample And Hold::Audio": "Sample And Hold",
    "BandSplitter::Band Splitter (Mono, 5)::None": "Mono Band Splitter",
    "BandSplitter::Band Splitter (Stereo, 5)::None": "Stereo Band Splitter",
    # Math
    "AbsoluteValue::Abs::Audio": "Abs",
    "UE::Subtract::Int32": "Subtract (Int32)",
    "UE::Multiply::Audio by Float": "Multiply (Audio by Float)",
    "UE::Multiply::Int32": "Multiply (Int32)",
    "UE::Divide::Int32": "Divide (Int32)",
    "Max::Max::Audio": "Max",
    "Min::Min::Audio": "Min",
    "UE::Power::Float": "Power",
    "UE::Logarithm::Float": "Log",
    "UE::Convert Filter Q To Bandwidth::None": "Filter Q To Bandwidth",
    "Print Log::Print Log::Float": "Print Log",
    # Mix
    "AudioMixer::Audio Mixer (Mono, 3)::None": "Audio Mixer (Mono, 3)",
    # Spatialization
    "UE::Mid-Side Decode::Audio": "Mid-Side Decode",
    "UE::Mid-Side Encode::Audio": "Mid-Side Encode",
    # General
    "UE::ConversionAudioToFloat::None": "Audio To Float",
    "UE::RingMod::Audio": "Ring Mod",
    "UE::Get Wave Duration:: ": "Get Wave Duration",
    "UE::WaveWriter::Audio": "Wave Writer",
    "UE::Audio Bus Reader (2)::None": "Audio Bus Reader",
    "Convert::Bool::Float": "Convert",
    # Music
    "UE::Musical Scale To Note Array::Audio": "Scale to Note Array",
    # Random
    "UE::RandomBool::None": "Random Bool",
    "UE::RandomTime::None": "Random Time",
    "Array::Random Get::WaveAsset:Array": "Random Get (WaveAssetArray)",
    # Triggers
    "TriggerAccumulator::Trigger Accumulate (2)::None": "Trigger Accumulate",
    "TriggerAny::Trigger Any (2)::None": "Trigger Any",
    "UE::Trigger Control::None": "Trigger Control",
    "UE::Trigger Delay::None": "Trigger Delay",
    "UE::TriggerOnThreshold::Audio": "Trigger On Threshold (Audio)",
    "UE::Trigger On Value Change::Float": "Trigger On Value Change",
    "UE::Trigger Once::None": "Trigger Once",
    "UE::Trigger Select (2)::None": "Trigger Select",
    "UE::Trigger Toggle::None": "Trigger Toggle",
    # Arrays
    "Array::Concat::Float:Array": "Array Concatenate",
    "Array::Get::Float:Array": "Array Get",
    "Array::Num::Float:Array": "Array Num",
    "Array::Set::Float:Array": "Array Set",
    "Array::Shuffle::Float:Array": "Array Shuffle",
    "Array::Subset::Float:Array": "Array Subset",
    # Crossfade
    "Crossfade::Trigger Route (Audio, 2)::Audio": "Crossfade (Audio, 2)",
    "TriggerRoute::Trigger Route (Float, 2)::Float": "Trigger Route (Float, 2)",
    "AudioMixer::Audio Mixer (Stereo, 3)::None": "Audio Mixer (Stereo, 3)",
    "TriggerCompare::Clamp::Float": "Trigger Compare (Float)",
    "TriggerCompare::Clamp::Bool": "Trigger Compare (Bool)",
}

# ===================================================================
# DISPLAY_TO_CLASS — reverse mapping (display_name -> class_name)
# Built once, used by export_catalogues.py and cross_reference.py.
# ===================================================================

DISPLAY_TO_CLASS: dict[str, str] = {}
for _cn, _dn in CLASS_NAME_TO_DISPLAY.items():
    if _dn not in DISPLAY_TO_CLASS:
        DISPLAY_TO_CLASS[_dn] = _cn
del _cn, _dn

# Extra display->class entries for nodes whose class_name is already claimed
# by another display name in CLASS_NAME_TO_DISPLAY (e.g. UE::Add::Audio
# maps to "Add (Audio)" above, but catalogue also has bare "Add").
_EXTRA_DISPLAY_TO_CLASS: dict[str, str] = {
    "Add": "UE::Add::Audio",
    "Subtract": "UE::Subtract::Audio",
    "Multiply": "UE::Multiply::Audio",
    "Divide": "UE::Divide::Float",
    "Delay": "UE::Delay::Audio",
    "InterpTo": "UE::InterpTo::Audio",
    "Modulo": "UE::Modulo::Int32",
    "Wave Player": "UE::Wave Player::Mono",
    "Wave Shaper": "UE::WaveShaper::Audio",
    "Plate Reverb": "UE::Plate Reverb::Stereo",
    "Flanger": "UE::Flanger::None",
    "Low-Frequency Oscillator": "UE::LFO::Audio",
    "Bitcrusher": "UE::Bitcrusher::Audio",
    # Nodes with same engine class but different display name
    "ADSR Envelope (Audio)": "ADSR Envelope::ADSR Envelope::Audio",
    "Noise (Pink)": "UE::Noise::Audio",
    "Noise (White)": "UE::Noise::Audio",
    "Divide (Audio)": "UE::Divide::Float",  # No Audio variant; closest is Float
    "Mid-Side Encode/Decode": "UE::Mid-Side Encode::Audio",
    # Duplicate catalogue name for same engine node
    "Musical Scale To Note Array": "UE::Musical Scale To Note Array::Audio",
    # Short array aliases (same engine node as Array X variants)
    "Concatenate": "Array::Concat::Float:Array",
    "Get": "Array::Get::Float:Array",
    "Num": "Array::Num::Float:Array",
    "Set": "Array::Set::Float:Array",
    "Shuffle": "Array::Shuffle::Float:Array",
    "Subset": "Array::Subset::Float:Array",
}
for _dn, _cn in _EXTRA_DISPLAY_TO_CLASS.items():
    if _dn not in DISPLAY_TO_CLASS:
        DISPLAY_TO_CLASS[_dn] = _cn
del _dn, _cn

# --- Backfill class_name into every METASOUND_NODES entry ---
for _name, _node_def in METASOUND_NODES.items():
    if not _node_def.get("class_name"):
        _node_def["class_name"] = DISPLAY_TO_CLASS.get(_name, "")
del _name, _node_def


def class_name_to_display(class_name: str) -> str | None:
    """Convert a UE class_name like 'UE::Sine::Audio' to display name 'Sine'.

    Lookup order:
      1. Exact match in CLASS_NAME_TO_DISPLAY
      2. Fuzzy: extract Name part, check METASOUND_NODES
      3. Fuzzy with variant: "Name (Variant)" pattern
      4. Case-insensitive scan of METASOUND_NODES keys

    Returns None if no mapping found.
    """
    # 1. Exact dict lookup
    if class_name in CLASS_NAME_TO_DISPLAY:
        return CLASS_NAME_TO_DISPLAY[class_name]

    # 2-3. Fuzzy from class_name parts
    parts = class_name.split("::")
    if len(parts) >= 2:
        name_part = parts[1].strip()
        variant = parts[2].strip() if len(parts) >= 3 else ""

        # Direct name match
        if name_part in METASOUND_NODES:
            return name_part

        # "Name (Variant)" pattern
        if variant and variant != "None":
            with_variant = f"{name_part} ({variant})"
            if with_variant in METASOUND_NODES:
                return with_variant

        # 4. Case-insensitive scan (slower, last resort)
        name_lower = name_part.lower()
        for node_name in METASOUND_NODES:
            if node_name.lower() == name_lower:
                return node_name

    return None


def infer_class_type(class_name: str) -> str:
    """Infer MetaSounds class_type from class_name prefix.

    Used when export data lacks an explicit class_type field
    (e.g. older get_node_locations format from scan_project.py).
    """
    if not class_name:
        return "External"
    prefix = class_name.split("::")[0] if "::" in class_name else class_name
    _MAP = {
        "Input": "Input",
        "Output": "Output",
        "InitVariable": "Variable",
        "VariableAccessor": "VariableAccessor",
        "VariableMutator": "VariableMutator",
        "VariableDeferredAccessor": "VariableDeferred",
    }
    return _MAP.get(prefix, "External")
