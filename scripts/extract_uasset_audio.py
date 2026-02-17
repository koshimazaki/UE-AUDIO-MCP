#!/usr/bin/env python3
"""Extract Blueprint and audio data from UE4/UE5 .uasset binaries via `strings`.

Scans a UE project's Content/Audio folder and extracts:
- Blueprint nodes (functions, events, variables, components)
- Sound Cue structure (references, node types)
- Attenuation settings (shape, distance, properties)
- Sound Classes & Mixes hierarchy
- Effects (source/submix presets, parameters)
- Reverb settings
- Concurrency rules
- Asset cross-references

Output: JSON file with structured data for knowledge DB import.
"""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


# ── Patterns to extract ──────────────────────────────────────────────────

# Asset references: /Game/Audio/...
RE_GAME_REF = re.compile(r"^/Game/(.+)$")
# Script modules: /Script/Engine, /Script/Synthesis, etc.
RE_SCRIPT_REF = re.compile(r"^/Script/(\w+)$")
# Blueprint function calls
RE_CALLFUNC = re.compile(r"^CallFunc_(\w+?)(?:_ReturnValue)?$")
# Blueprint event bindings
RE_EVENT = re.compile(r"^BndEvt__(\w+?)_K2Node_(\w+?)_\d+_(\w+)__DelegateSignature$")
# Variable declarations
RE_GENVAR = re.compile(r"^(\w+)_GEN_VARIABLE$")
# UE class types (from strings that appear as standalone identifiers)
UE_AUDIO_CLASSES = {
    "SoundCue", "SoundWave", "SoundAttenuation", "SoundClass", "SoundMix",
    "SoundConcurrency", "SoundSubmix", "SoundSourceBus", "SoundEffectSourcePreset",
    "SoundEffectSubmixPreset", "SoundEffectSourcePresetChain",
    "AudioComponent", "AmbientSound", "AudioVolume",
    "ReverbEffect", "ReverbSettings",
    "SourceEffectStereoDelayPreset", "SourceEffectFilterPreset",
    "SourceEffectChorusPreset", "SourceEffectEnvelopeFollowerPreset",
    "MetaSoundSource", "MetaSoundPatch",
    "SoundscapeColor", "SoundscapePalette",
}

# Attenuation properties
ATTENUATION_PROPS = {
    "AttenuationShape", "AttenuationShapeExtents", "FalloffDistance",
    "OmniRadius", "StereoSpread", "bAttenuate", "bAttenuateWithLPF",
    "bSpatialize", "bEnableOcclusion", "bEnableReverbSend",
    "bEnableFocusInterpolation", "bEnableListenerFocus",
    "bApplyNormalizationToStereoSounds", "AttenuationDistance",
    "AttenuationOcclusion", "AttenuationReverbSend",
    "AttenuationSpatialization", "AttenuationAirAbsorption",
    "AttenuationListenerFocus", "AttenuationPluginSettings",
    "AbsorptionMethod", "SpatializationAlgorithm",
    "MaxDistance", "MinDistance", "LPFRadiusMin", "LPFRadiusMax",
    "LPFFrequencyAtMin", "LPFFrequencyAtMax",
    "HPFFrequencyAtMin", "HPFFrequencyAtMax",
}

# Effect parameters
EFFECT_PARAMS = {
    "DelayTimeMsec", "Feedback", "WetLevel", "DryLevel",
    "FilterFrequency", "FilterQ", "FilterType",
    "ChorusDepth", "ChorusFrequency", "ChorusFeedback", "ChorusSpread",
    "Gain", "GainDb", "Density", "Diffusion",
    "AirAbsorptionGainHF", "DecayTime", "DecayHFRatio",
    "ReflectionsGain", "ReflectionsDelay",
    "LateReverbGain", "LateReverbDelay",
}

# Blueprint audio functions we care about
BP_AUDIO_FUNCTIONS = {
    "PlaySound2D", "PlaySoundAtLocation", "SpawnSoundAtLocation",
    "SpawnSound2D", "SpawnSoundAttached", "SetSound", "Stop",
    "FadeIn", "FadeOut", "AdjustVolume", "SetVolumeMultiplier",
    "SetPitchMultiplier", "SetBoolParameter", "SetFloatParameter",
    "SetIntParameter", "SetWaveParameter", "SetTriggerParameter",
    "IsPlaying", "GetPlayState",
    "SetSoundMixClassOverride", "PushSoundMixModifier",
    "PopSoundMixModifier", "ClearSoundMixModifiers",
    "ActivateReverbEffect", "DeactivateReverbEffect",
    "SetSubmixEffectChainOverride", "ClearSubmixEffectChainOverride",
    "GetPhysicsLinearVelocity", "VSize", "MapRangeClamped",
    "RandomFloatInRange", "RandomFloat",
    "SetRelativeLocation", "GetWorldLocation",
    "GetDistanceTo", "GetActorLocation",
    "MakeVector", "BreakVector",
    "SetScalarParameterValue", "SetVectorParameterValue",
    "Greater_FloatFloat", "Less_FloatFloat",
    "Multiply_FloatFloat", "Add_FloatFloat", "Subtract_FloatFloat",
    "Clamp", "Lerp", "MapRangeUnclamped",
    "SetActorHiddenInGame", "SetActorTickEnabled",
    "K2_SetActorLocation", "K2_GetActorRotation",
    "SetVisibility", "SetActive",
    "GetTimelineValue", "PlayFromStart", "SetPlayRate",
    "OnComponentBeginOverlap", "OnComponentEndOverlap",
    "EventTick", "EventBeginPlay",
}


def extract_strings(filepath):
    """Run `strings` on a binary file and return lines."""
    try:
        result = subprocess.run(
            ["strings", filepath],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.splitlines()
    except Exception:
        return []


def classify_asset(filepath, lines):
    """Classify and extract data from a single .uasset file."""
    basename = Path(filepath).stem
    rel_path = str(filepath).split("/Content/")[-1] if "/Content/" in str(filepath) else basename

    # Two-pass classification: collect all type indicators, then decide with priority
    # This avoids misclassifying SoundWave as SoundClass (SoundWaves reference SoundClass)
    type_indicators = set()
    for line in lines:
        if line in ("SoundAttenuation", "SoundAttenuationSettings"):
            type_indicators.add("attenuation")
        elif line in ("SoundClass",):
            type_indicators.add("sound_class")
        elif line in ("SoundMix", "SoundMixModifier"):
            type_indicators.add("sound_mix")
        elif line in ("SoundConcurrency", "SoundConcurrencySettings"):
            type_indicators.add("concurrency")
        elif line in ("ReverbEffect",):
            type_indicators.add("reverb")
        elif "SoundEffectSourcePreset" in line or "SoundEffectSubmixPreset" in line:
            type_indicators.add("effect")
        elif line == "SoundSubmix":
            type_indicators.add("submix")
        elif line == "SoundSourceBus":
            type_indicators.add("source_bus")
        elif line in ("SoundCue",):
            type_indicators.add("sound_cue")
        elif line in ("SoundWave",):
            type_indicators.add("sound_wave")
        elif line in ("MetaSoundSource", "MetaSoundPatch"):
            type_indicators.add("metasound")
        elif "BlueprintGeneratedClass" in line:
            type_indicators.add("blueprint")
        elif "CurveFloat" in line or line == "RichCurve":
            type_indicators.add("curve")

    # Priority: more specific types win over generic ones
    # SoundWave/SoundCue beat SoundClass (since waves reference their class)
    # Blueprint beats everything (BP wraps audio components)
    # Effect/Submix/SourceBus are very specific
    PRIORITY = [
        "blueprint", "metasound", "effect", "submix", "source_bus",
        "reverb", "concurrency", "attenuation", "sound_mix",
        "sound_cue", "sound_wave", "curve", "sound_class",
    ]
    asset_type = "unknown"
    for t in PRIORITY:
        if t in type_indicators:
            asset_type = t
            break

    data = {
        "name": basename,
        "path": rel_path,
        "type": asset_type,
        "references": [],
        "script_modules": [],
    }

    # Extract by type
    functions = set()
    events = []
    variables = set()
    components = set()
    audio_classes = set()
    properties = set()
    effect_params = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Asset references
        m = RE_GAME_REF.match(line)
        if m:
            ref = m.group(1)
            if basename not in ref.split(".")[-1]:
                data["references"].append("/Game/" + ref)
            continue

        # Script modules
        m = RE_SCRIPT_REF.match(line)
        if m:
            data["script_modules"].append(m.group(1))
            continue

        # Blueprint function calls
        m = RE_CALLFUNC.match(line)
        if m:
            func = m.group(1)
            functions.add(func)
            continue

        # Events
        m = RE_EVENT.match(line)
        if m:
            component, node_type, delegate = m.groups()
            events.append({
                "component": component,
                "node_type": node_type,
                "delegate": delegate,
            })
            continue

        # Variables
        m = RE_GENVAR.match(line)
        if m:
            variables.add(m.group(1))
            continue

        # Audio classes
        if line in UE_AUDIO_CLASSES:
            audio_classes.add(line)

        # Attenuation properties
        if line in ATTENUATION_PROPS:
            properties.add(line)

        # Effect parameters
        if line in EFFECT_PARAMS:
            effect_params[line] = True

        # Components
        if line.endswith("Component") and not line.startswith("b"):
            components.add(line)

    if functions:
        data["functions"] = sorted(functions)
    if events:
        data["events"] = events
    if variables:
        data["variables"] = sorted(variables)
    if components:
        data["components"] = sorted(components)
    if audio_classes:
        data["audio_classes"] = sorted(audio_classes)
    if properties:
        data["properties"] = sorted(properties)
    if effect_params:
        data["effect_params"] = sorted(effect_params.keys())

    data["references"] = sorted(set(data["references"]))
    data["script_modules"] = sorted(set(data["script_modules"]))

    return data


def scan_project(content_audio_path):
    """Scan all .uasset files under Content/Audio/."""
    results = {
        "project_info": {},
        "blueprints": [],
        "sound_cues": [],
        "attenuations": [],
        "sound_classes": [],
        "sound_mixes": [],
        "effects": [],
        "submixes": [],
        "source_buses": [],
        "reverbs": [],
        "concurrency": [],
        "curves": [],
        "sound_waves": [],
        "metasounds": [],
        "unknown": [],
    }

    audio_path = Path(content_audio_path)
    uassets = sorted(
        p for p in audio_path.rglob("*.uasset")
        if not p.name.startswith("._")
    )

    print("Found {} .uasset files".format(len(uassets)))

    if uassets:
        first_lines = extract_strings(str(uassets[0]))
        for line in first_lines:
            if "++UE4" in line or "++UE5" in line:
                results["project_info"]["engine_version"] = line
                break

    type_map = {
        "blueprint": "blueprints",
        "sound_cue": "sound_cues",
        "attenuation": "attenuations",
        "sound_class": "sound_classes",
        "sound_mix": "sound_mixes",
        "effect": "effects",
        "submix": "submixes",
        "source_bus": "source_buses",
        "reverb": "reverbs",
        "concurrency": "concurrency",
        "curve": "curves",
        "sound_wave": "sound_waves",
        "metasound": "metasounds",
        "unknown": "unknown",
    }

    for i, uasset in enumerate(uassets):
        if (i + 1) % 100 == 0:
            print("  Processing {}/{}...".format(i + 1, len(uassets)))

        lines = extract_strings(str(uasset))
        if not lines:
            continue

        data = classify_asset(str(uasset), lines)
        category = type_map.get(data["type"], "unknown")
        results[category].append(data)

    results["summary"] = {
        cat: len(items) for cat, items in results.items()
        if isinstance(items, list)
    }

    return results


def build_knowledge_entries(scan_results):
    """Convert scan results to knowledge DB entries."""
    entries = []

    # 1. Blueprint audio patterns
    for bp in scan_results["blueprints"]:
        audio_funcs = [f for f in bp.get("functions", []) if f in BP_AUDIO_FUNCTIONS]
        if not audio_funcs:
            continue

        entry = {
            "category": "blueprint_audio_pattern",
            "name": bp["name"],
            "description": "Audio blueprint using: {}".format(", ".join(audio_funcs[:5])),
            "functions": audio_funcs,
            "components": bp.get("components", []),
            "variables": bp.get("variables", []),
            "events": bp.get("events", []),
            "references": [r for r in bp.get("references", []) if "/Audio/" in r],
            "source": "uasset_extraction",
        }
        entries.append(entry)

    # 2. Attenuation presets
    for att in scan_results["attenuations"]:
        entry = {
            "category": "attenuation_preset",
            "name": att["name"],
            "properties": att.get("properties", []),
            "references": att.get("references", []),
            "source": "uasset_extraction",
        }
        entries.append(entry)

    # 3. Sound classes
    for sc in scan_results["sound_classes"]:
        entry = {
            "category": "sound_class",
            "name": sc["name"],
            "references": sc.get("references", []),
            "source": "uasset_extraction",
        }
        entries.append(entry)

    # 4. Effects
    for fx in scan_results["effects"]:
        entry = {
            "category": "audio_effect",
            "name": fx["name"],
            "audio_classes": fx.get("audio_classes", []),
            "effect_params": fx.get("effect_params", []),
            "references": fx.get("references", []),
            "source": "uasset_extraction",
        }
        entries.append(entry)

    # 5. Submixes
    for sub in scan_results["submixes"]:
        entry = {
            "category": "submix",
            "name": sub["name"],
            "references": sub.get("references", []),
            "source": "uasset_extraction",
        }
        entries.append(entry)

    # 6. Source buses
    for bus in scan_results["source_buses"]:
        entry = {
            "category": "source_bus",
            "name": bus["name"],
            "references": bus.get("references", []),
            "source": "uasset_extraction",
        }
        entries.append(entry)

    # 7. Reverbs
    for rev in scan_results["reverbs"]:
        entry = {
            "category": "reverb_preset",
            "name": rev["name"],
            "references": rev.get("references", []),
            "source": "uasset_extraction",
        }
        entries.append(entry)

    # 8. Sound cues with interesting structure
    for cue in scan_results["sound_cues"]:
        refs = [r for r in cue.get("references", []) if "/Audio/" in r]
        if len(refs) >= 2:
            entry = {
                "category": "sound_cue",
                "name": cue["name"],
                "references": refs,
                "audio_classes": cue.get("audio_classes", []),
                "source": "uasset_extraction",
            }
            entries.append(entry)

    # 9. MetaSounds (if any)
    for ms in scan_results["metasounds"]:
        entry = {
            "category": "metasound_example",
            "name": ms["name"],
            "references": ms.get("references", []),
            "audio_classes": ms.get("audio_classes", []),
            "source": "uasset_extraction",
        }
        entries.append(entry)

    return entries


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_uasset_audio.py <path_to_Content/Audio>")
        print("Example: python extract_uasset_audio.py '/path/to/YourProject/Content/Audio'")
        sys.exit(1)

    audio_path = sys.argv[1]
    if not os.path.isdir(audio_path):
        print("Error: {} is not a directory".format(audio_path))
        sys.exit(1)

    output_dir = Path(__file__).parent

    print("Scanning: {}".format(audio_path))
    results = scan_project(audio_path)

    raw_path = output_dir / "uasset_scan_results.json"
    with open(raw_path, "w") as f:
        json.dump(results, f, indent=2)
    print("\nRaw scan saved to: {}".format(raw_path))

    print("\n-- Summary --")
    for cat, count in results["summary"].items():
        if count > 0:
            print("  {}: {}".format(cat, count))

    entries = build_knowledge_entries(results)
    kb_path = output_dir / "uasset_knowledge_entries.json"
    with open(kb_path, "w") as f:
        json.dump(entries, f, indent=2)
    print("\nKnowledge entries: {} -> {}".format(len(entries), kb_path))

    cats = defaultdict(int)
    for e in entries:
        cats[e["category"]] += 1
    print("\n-- Knowledge Entries by Category --")
    for cat, count in sorted(cats.items()):
        print("  {}: {}".format(cat, count))


if __name__ == "__main__":
    main()
