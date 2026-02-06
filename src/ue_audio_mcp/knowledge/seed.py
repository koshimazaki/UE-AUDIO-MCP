"""Seed the knowledge database from static Python data.

Called on first run (when metasound_nodes table is empty).
Populates all 8 tables from existing knowledge modules and research data.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ue_audio_mcp.knowledge.db import KnowledgeDB

log = logging.getLogger(__name__)


def seed_database(db: KnowledgeDB) -> dict[str, int]:
    """Populate all tables from static data. Returns counts per table."""
    counts: dict[str, int] = {}

    counts["metasound_nodes"] = _seed_metasound_nodes(db)
    counts["wwise_types"] = _seed_wwise_types(db)
    counts["waapi_functions"] = _seed_waapi_functions(db)
    counts["audio_patterns"] = _seed_audio_patterns(db)
    counts["ue_game_examples"] = _seed_game_examples(db)
    counts["blueprint_audio"] = _seed_blueprint_audio(db)
    counts["blueprint_core"] = _seed_blueprint_core(db)

    total = sum(counts.values())
    log.info("Seeded knowledge DB: %d total entries %s", total, counts)
    return counts


def _seed_metasound_nodes(db: KnowledgeDB) -> int:
    from ue_audio_mcp.knowledge.metasound_nodes import METASOUND_NODES

    for node in METASOUND_NODES.values():
        db.insert_node(node)
    return len(METASOUND_NODES)


def _seed_wwise_types(db: KnowledgeDB) -> int:
    from ue_audio_mcp.knowledge.wwise_types import (
        OBJECT_TYPES,
        COMMON_PROPERTIES,
        DEFAULT_PATHS,
    )

    count = 0
    type_categories = {
        "Sound": "audio_object",
        "RandomSequenceContainer": "container",
        "SwitchContainer": "container",
        "BlendContainer": "container",
        "ActorMixer": "container",
        "Event": "event",
        "Action": "event",
        "Bus": "bus",
        "AuxBus": "bus",
        "WorkUnit": "structure",
        "Folder": "structure",
        "Attenuation": "shareset",
        "SoundBank": "output",
        "GameParameter": "game_sync",
        "SwitchGroup": "game_sync",
        "Switch": "game_sync",
        "StateGroup": "game_sync",
        "State": "game_sync",
        "Trigger": "game_sync",
    }
    for type_name in OBJECT_TYPES:
        cat = type_categories.get(type_name, "other")
        path = DEFAULT_PATHS.get(type_name.lower(), "")
        db.insert_wwise_type({
            "type_name": type_name,
            "category": cat,
            "description": "Wwise {} object".format(type_name),
            "properties": list(COMMON_PROPERTIES.keys()),
        })
        count += 1
    return count


def _seed_waapi_functions(db: KnowledgeDB) -> int:
    """Seed WAAPI functions from the waapi_functions catalogue."""
    from ue_audio_mcp.knowledge.waapi_functions import WAAPI_FUNCTIONS

    for uri, func in WAAPI_FUNCTIONS.items():
        operation = uri.rsplit(".", 1)[-1]
        db.insert_waapi({
            "uri": uri,
            "namespace": func["namespace"],
            "operation": operation,
            "description": func["description"],
            "params": func.get("params", []),
            "returns": func.get("returns"),
        })
    return len(WAAPI_FUNCTIONS)


def _seed_audio_patterns(db: KnowledgeDB) -> int:
    """Seed the 6 game audio patterns."""
    patterns = [
        {
            "name": "gunshot",
            "pattern_type": "weapon",
            "description": "Non-repetitive weapon fire with layered components and pitch randomization",
            "complexity": 3,
            "key_nodes": ["Random Get", "Wave Player (Mono)", "ADSR Envelope (Audio)", "Stereo Mixer", "Random Float"],
        },
        {
            "name": "footsteps",
            "pattern_type": "movement",
            "description": "Surface-aware randomized footstep audio with per-surface filtering",
            "complexity": 3,
            "key_nodes": ["Trigger Route", "Array Random Get", "Wave Player (Mono)", "AD Envelope (Audio)", "One-Pole Low Pass Filter"],
        },
        {
            "name": "ambient",
            "pattern_type": "environment",
            "description": "Looping layered environmental audio with natural variation",
            "complexity": 4,
            "key_nodes": ["Wave Player (Stereo)", "Trigger Repeat", "Random Get", "Stereo Panner", "LFO"],
        },
        {
            "name": "spatial",
            "pattern_type": "spatialization",
            "description": "3D positioned audio with binaural rendering",
            "complexity": 2,
            "key_nodes": ["ITD Panner", "Stereo Panner", "Mid-Side Encode/Decode"],
        },
        {
            "name": "ui_sound",
            "pattern_type": "interface",
            "description": "Non-spatial UI feedback sounds with procedural synthesis option",
            "complexity": 2,
            "key_nodes": ["Sine", "AD Envelope (Audio)", "Trigger Route", "Wave Player (Mono)"],
        },
        {
            "name": "weather_states",
            "pattern_type": "state_switch",
            "description": "Game state driven audio transitions between weather profiles",
            "complexity": 4,
            "key_nodes": ["Trigger Route", "Crossfade", "InterpTo", "Dynamic Filter", "Wave Player (Stereo)"],
        },
    ]
    for p in patterns:
        db.insert_pattern(p)
    return len(patterns)


def _seed_game_examples(db: KnowledgeDB) -> int:
    """Seed UE game reference implementations."""
    examples = [
        {
            "name": "lyra_whizby",
            "game": "Lyra",
            "system_type": "weapon",
            "description": "Bullet flyby with incoming/receding phases and reflection system",
            "details": {"patch": "lib_Whizby", "features": ["8-tap delay", "frequency clamping", "convolution reverb"]},
        },
        {
            "name": "lyra_dovetail",
            "game": "Lyra",
            "system_type": "transition",
            "description": "Blends previous audio with new results using stereo balance",
            "details": {"patch": "lib_DovetailClip"},
        },
        {
            "name": "lyra_ambient",
            "game": "Lyra",
            "system_type": "ambient",
            "description": "Randomized ambient sounds with initial delays",
            "details": {"patch": "mx_PlayAmbientElement", "features": ["random delays", "environmental variation"]},
        },
        {
            "name": "lyra_music",
            "game": "Lyra",
            "system_type": "music",
            "description": "5-layer vertical music remixing with intensity tracking",
            "details": {"patch": "mx_Stingers", "layers": ["bass", "percussion-deep", "percussion-light", "pad", "lead"]},
        },
        {
            "name": "lyra_submix",
            "game": "Lyra",
            "system_type": "routing",
            "description": "Submix architecture: Master > UI/SFX/Music/Voice/Reverb",
            "details": {"buses": ["UISubmix", "SFXSubmix", "MusicSubmix", "VoiceSubmix", "ReverbSubmix"]},
        },
    ]
    for ex in examples:
        db.insert_example(ex)
    return len(examples)


def _seed_blueprint_audio(db: KnowledgeDB) -> int:
    """Seed Blueprint audio functions from the blueprint_audio catalogue."""
    from ue_audio_mcp.knowledge.blueprint_audio import BLUEPRINT_AUDIO_FUNCTIONS

    # Source uses 'category' for class name (GameplayStatics, AudioComponent, etc.)
    # Map to UE5 class prefixes for the class_name DB column
    _CLASS_MAP = {
        "GameplayStatics": "UGameplayStatics",
        "AudioComponent": "UAudioComponent",
        "AudioVolume": "AAudioVolume",
        "Quartz": "UQuartzSubsystem",
    }
    for name, func in BLUEPRINT_AUDIO_FUNCTIONS.items():
        source_cat = func["category"]
        db.insert_blueprint_audio({
            "name": name,
            "class_name": _CLASS_MAP.get(source_cat, source_cat),
            "category": source_cat.lower(),
            "description": func["description"],
            "params": func.get("params", []),
            "returns": func.get("returns"),
            "tags": func.get("tags", []),
        })
    return len(BLUEPRINT_AUDIO_FUNCTIONS)


def _seed_blueprint_core(db: KnowledgeDB) -> int:
    """Seed essential Blueprint core nodes for audio integration."""
    nodes = [
        {"name": "Branch", "class_name": "UK2Node_IfThenElse", "category": "flow_control",
         "description": "Conditional branching based on bool", "tags": ["if", "condition", "branch"]},
        {"name": "Sequence", "class_name": "UK2Node_ExecutionSequence", "category": "flow_control",
         "description": "Execute outputs in sequence", "tags": ["sequence", "order", "sequential"]},
        {"name": "ForEachLoop", "class_name": "UK2Node_ForEachLoop", "category": "flow_control",
         "description": "Iterate over an array", "tags": ["loop", "array", "iterate"]},
        {"name": "Delay", "class_name": "UK2Node_Delay", "category": "flow_control",
         "description": "Delay execution by time", "tags": ["delay", "timer", "wait"]},
        {"name": "DoOnce", "class_name": "UK2Node_DoOnce", "category": "flow_control",
         "description": "Execute only once until reset", "tags": ["once", "gate"]},
        {"name": "Gate", "class_name": "UK2Node_Gate", "category": "flow_control",
         "description": "Open/close execution gate", "tags": ["gate", "control"]},
        {"name": "FlipFlop", "class_name": "UK2Node_FlipFlop", "category": "flow_control",
         "description": "Alternate between two outputs", "tags": ["toggle", "alternate"]},
        {"name": "Select", "class_name": "UK2Node_Select", "category": "flow_control",
         "description": "Select output based on index", "tags": ["select", "switch", "index"]},
        {"name": "SwitchOnInt", "class_name": "UK2Node_SwitchInteger", "category": "flow_control",
         "description": "Switch execution based on integer value", "tags": ["switch", "integer"]},
        {"name": "SwitchOnString", "class_name": "UK2Node_SwitchString", "category": "flow_control",
         "description": "Switch execution based on string value", "tags": ["switch", "string"]},
        {"name": "SwitchOnEnum", "class_name": "UK2Node_SwitchEnum", "category": "flow_control",
         "description": "Switch execution based on enum value", "tags": ["switch", "enum"]},
        {"name": "EventBeginPlay", "class_name": "UK2Node_Event", "category": "events",
         "description": "Called when actor begins play", "tags": ["begin", "start", "init"]},
        {"name": "EventTick", "class_name": "UK2Node_Event", "category": "events",
         "description": "Called every frame", "tags": ["tick", "frame", "update"]},
        {"name": "EventActorBeginOverlap", "class_name": "UK2Node_Event", "category": "events",
         "description": "Called when actor begins overlapping", "tags": ["overlap", "trigger", "collision"]},
        {"name": "EventActorEndOverlap", "class_name": "UK2Node_Event", "category": "events",
         "description": "Called when actor stops overlapping", "tags": ["overlap", "end", "collision"]},
        {"name": "EventHit", "class_name": "UK2Node_Event", "category": "events",
         "description": "Called when actor is hit by something", "tags": ["hit", "collision", "impact"]},
        {"name": "CustomEvent", "class_name": "UK2Node_CustomEvent", "category": "events",
         "description": "Custom event that can be called from other blueprints", "tags": ["custom", "event", "call"]},
        {"name": "SetTimerByFunctionName", "class_name": "UKismetSystemLibrary", "category": "timer",
         "description": "Set a timer to call a function", "tags": ["timer", "delay", "repeat"]},
        {"name": "ClearTimer", "class_name": "UKismetSystemLibrary", "category": "timer",
         "description": "Clear an active timer", "tags": ["timer", "clear", "stop"]},
        {"name": "LineTraceByChannel", "class_name": "UKismetSystemLibrary", "category": "trace",
         "description": "Cast a ray and return hit results", "tags": ["raycast", "trace", "collision", "surface"]},
        {"name": "SphereTraceByChannel", "class_name": "UKismetSystemLibrary", "category": "trace",
         "description": "Cast a sphere and return hit results", "tags": ["trace", "sphere", "collision"]},
        {"name": "GetPhysicalMaterial", "class_name": "UPrimitiveComponent", "category": "physics",
         "description": "Get physical material from hit result (for surface detection)", "tags": ["material", "surface", "footstep"]},
        {"name": "GetActorLocation", "class_name": "AActor", "category": "transform",
         "description": "Get actor world location", "tags": ["location", "position", "world"]},
        {"name": "GetActorRotation", "class_name": "AActor", "category": "transform",
         "description": "Get actor world rotation", "tags": ["rotation", "orientation"]},
        {"name": "GetDistanceTo", "class_name": "AActor", "category": "transform",
         "description": "Get distance between two actors", "tags": ["distance", "attenuation"]},
        {"name": "MakeArray", "class_name": "UK2Node_MakeArray", "category": "utility",
         "description": "Create an array from individual values", "tags": ["array", "create"]},
        {"name": "MakeStruct", "class_name": "UK2Node_MakeStruct", "category": "utility",
         "description": "Create a struct from individual values", "tags": ["struct", "create"]},
        {"name": "SpawnActor", "class_name": "UGameplayStatics", "category": "spawn",
         "description": "Spawn an actor in the world", "tags": ["spawn", "create", "actor"]},
        {"name": "GetPlayerController", "class_name": "UGameplayStatics", "category": "player",
         "description": "Get the player controller", "tags": ["player", "controller"]},
        {"name": "GetPlayerCameraManager", "class_name": "UGameplayStatics", "category": "player",
         "description": "Get the player camera manager (listener position)", "tags": ["camera", "listener", "spatial"]},
        {"name": "RandomFloatInRange", "class_name": "UKismetMathLibrary", "category": "math",
         "description": "Random float between min and max", "tags": ["random", "float", "range"]},
        {"name": "RandomIntegerInRange", "class_name": "UKismetMathLibrary", "category": "math",
         "description": "Random integer between min and max", "tags": ["random", "integer", "range"]},
        {"name": "Lerp", "class_name": "UKismetMathLibrary", "category": "math",
         "description": "Linear interpolation between two values", "tags": ["interpolation", "lerp", "blend"]},
        {"name": "FInterpTo", "class_name": "UKismetMathLibrary", "category": "math",
         "description": "Float interpolation with speed", "tags": ["interpolation", "smooth", "transition"]},
        {"name": "MapRangeClamped", "class_name": "UKismetMathLibrary", "category": "math",
         "description": "Map value from one range to another (clamped)", "tags": ["map", "range", "remap", "normalize"]},
        {"name": "Clamp", "class_name": "UKismetMathLibrary", "category": "math",
         "description": "Clamp value between min and max", "tags": ["clamp", "limit"]},
    ]
    for n in nodes:
        db.insert_blueprint_core(n)
    return len(nodes)
