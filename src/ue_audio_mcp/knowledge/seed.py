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
    """Seed core WAAPI functions from research data."""
    functions = [
        {"uri": "ak.wwise.core.getInfo", "namespace": "core", "operation": "getInfo",
         "description": "Get Wwise application info and version"},
        {"uri": "ak.wwise.core.object.create", "namespace": "core.object", "operation": "create",
         "description": "Create a Wwise object in the hierarchy"},
        {"uri": "ak.wwise.core.object.delete", "namespace": "core.object", "operation": "delete",
         "description": "Delete a Wwise object"},
        {"uri": "ak.wwise.core.object.get", "namespace": "core.object", "operation": "get",
         "description": "Query objects using WAQL"},
        {"uri": "ak.wwise.core.object.set", "namespace": "core.object", "operation": "set",
         "description": "Set object properties in bulk"},
        {"uri": "ak.wwise.core.object.setProperty", "namespace": "core.object", "operation": "setProperty",
         "description": "Set a single property on an object"},
        {"uri": "ak.wwise.core.object.setReference", "namespace": "core.object", "operation": "setReference",
         "description": "Set a reference (e.g. OutputBus) on an object"},
        {"uri": "ak.wwise.core.object.setAttenuationCurve", "namespace": "core.object", "operation": "setAttenuationCurve",
         "description": "Set attenuation curve points"},
        {"uri": "ak.wwise.core.object.getTypes", "namespace": "core.object", "operation": "getTypes",
         "description": "Get all available object types"},
        {"uri": "ak.wwise.core.object.getPropertyInfo", "namespace": "core.object", "operation": "getPropertyInfo",
         "description": "Get property metadata for a type"},
        {"uri": "ak.wwise.core.object.copy", "namespace": "core.object", "operation": "copy",
         "description": "Copy an object to a new location"},
        {"uri": "ak.wwise.core.object.move", "namespace": "core.object", "operation": "move",
         "description": "Move an object to a new location"},
        {"uri": "ak.wwise.core.audio.import", "namespace": "core.audio", "operation": "import",
         "description": "Import audio files into Wwise"},
        {"uri": "ak.wwise.core.project.save", "namespace": "core.project", "operation": "save",
         "description": "Save the Wwise project"},
        {"uri": "ak.wwise.core.transport.create", "namespace": "core.transport", "operation": "create",
         "description": "Create a transport for playback"},
        {"uri": "ak.wwise.core.transport.destroy", "namespace": "core.transport", "operation": "destroy",
         "description": "Destroy a transport"},
        {"uri": "ak.wwise.core.transport.executeAction", "namespace": "core.transport", "operation": "executeAction",
         "description": "Play/stop/pause a transport"},
        {"uri": "ak.wwise.core.transport.getList", "namespace": "core.transport", "operation": "getList",
         "description": "List all active transports"},
        {"uri": "ak.wwise.core.soundbank.generate", "namespace": "core.soundbank", "operation": "generate",
         "description": "Generate SoundBanks"},
        {"uri": "ak.wwise.core.undo.beginGroup", "namespace": "core.undo", "operation": "beginGroup",
         "description": "Begin an undo group for atomic operations"},
        {"uri": "ak.wwise.core.undo.endGroup", "namespace": "core.undo", "operation": "endGroup",
         "description": "End an undo group"},
        {"uri": "ak.wwise.core.undo.cancelGroup", "namespace": "core.undo", "operation": "cancelGroup",
         "description": "Cancel an undo group and rollback"},
        {"uri": "ak.wwise.core.switchContainer.addAssignment", "namespace": "core.switchContainer", "operation": "addAssignment",
         "description": "Assign a child to a switch value"},
        {"uri": "ak.wwise.core.switchContainer.removeAssignment", "namespace": "core.switchContainer", "operation": "removeAssignment",
         "description": "Remove a switch assignment"},
        {"uri": "ak.wwise.core.remote.connect", "namespace": "core.remote", "operation": "connect",
         "description": "Connect to a remote Wwise instance"},
        {"uri": "ak.wwise.core.remote.disconnect", "namespace": "core.remote", "operation": "disconnect",
         "description": "Disconnect from remote Wwise"},
        {"uri": "ak.wwise.core.remote.getAvailableConsoles", "namespace": "core.remote", "operation": "getAvailableConsoles",
         "description": "List available remote consoles"},
        {"uri": "ak.wwise.core.profiler.startCapture", "namespace": "core.profiler", "operation": "startCapture",
         "description": "Start profiler capture"},
        {"uri": "ak.wwise.core.profiler.stopCapture", "namespace": "core.profiler", "operation": "stopCapture",
         "description": "Stop profiler capture"},
        {"uri": "ak.wwise.core.profiler.getVoices", "namespace": "core.profiler", "operation": "getVoices",
         "description": "Get active voices from profiler"},
        {"uri": "ak.wwise.ui.getSelectedObjects", "namespace": "ui", "operation": "getSelectedObjects",
         "description": "Get currently selected objects in Wwise UI"},
        {"uri": "ak.wwise.ui.commands.execute", "namespace": "ui.commands", "operation": "execute",
         "description": "Execute a Wwise UI command"},
    ]
    for func in functions:
        db.insert_waapi(func)
    return len(functions)


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
    """Seed Blueprint audio functions from UGameplayStatics + UAudioComponent."""
    functions = [
        {"name": "PlaySound2D", "class_name": "UGameplayStatics", "category": "playback",
         "description": "Play a sound at the listener location (no attenuation)", "tags": ["ui", "2d", "play"]},
        {"name": "PlaySoundAtLocation", "class_name": "UGameplayStatics", "category": "playback",
         "description": "Play sound at a world location with optional attenuation", "tags": ["3d", "spatial", "play"]},
        {"name": "SpawnSoundAtLocation", "class_name": "UGameplayStatics", "category": "playback",
         "description": "Spawn audio component at location (returns handle)", "tags": ["3d", "spawn", "persistent"]},
        {"name": "SpawnSoundAttached", "class_name": "UGameplayStatics", "category": "playback",
         "description": "Spawn audio component attached to a scene component", "tags": ["attached", "follow", "spawn"]},
        {"name": "SetBaseSoundMix", "class_name": "UGameplayStatics", "category": "mixing",
         "description": "Set the base sound mix for the game", "tags": ["mix", "global"]},
        {"name": "PushSoundMixModifier", "class_name": "UGameplayStatics", "category": "mixing",
         "description": "Push a sound mix modifier onto the stack", "tags": ["mix", "modifier", "push"]},
        {"name": "PopSoundMixModifier", "class_name": "UGameplayStatics", "category": "mixing",
         "description": "Pop a sound mix modifier from the stack", "tags": ["mix", "modifier", "pop"]},
        {"name": "SetSoundMixClassOverride", "class_name": "UGameplayStatics", "category": "mixing",
         "description": "Override a sound class with new properties", "tags": ["mix", "class", "override"]},
        {"name": "ActivateReverbEffect", "class_name": "UGameplayStatics", "category": "effects",
         "description": "Activate a reverb effect with priority", "tags": ["reverb", "effect", "activate"]},
        {"name": "DeactivateReverbEffect", "class_name": "UGameplayStatics", "category": "effects",
         "description": "Deactivate a reverb effect", "tags": ["reverb", "effect", "deactivate"]},
        {"name": "Play", "class_name": "UAudioComponent", "category": "component",
         "description": "Play the audio component", "tags": ["play", "component"]},
        {"name": "Stop", "class_name": "UAudioComponent", "category": "component",
         "description": "Stop the audio component", "tags": ["stop", "component"]},
        {"name": "SetPaused", "class_name": "UAudioComponent", "category": "component",
         "description": "Pause/unpause the audio component", "tags": ["pause", "component"]},
        {"name": "SetFloatParameter", "class_name": "UAudioComponent", "category": "parameter",
         "description": "Set a float parameter on MetaSound", "tags": ["parameter", "float", "metasound"]},
        {"name": "SetIntParameter", "class_name": "UAudioComponent", "category": "parameter",
         "description": "Set an int parameter on MetaSound", "tags": ["parameter", "int", "metasound"]},
        {"name": "SetBoolParameter", "class_name": "UAudioComponent", "category": "parameter",
         "description": "Set a bool parameter on MetaSound", "tags": ["parameter", "bool", "metasound"]},
        {"name": "SetTriggerParameter", "class_name": "UAudioComponent", "category": "parameter",
         "description": "Execute a trigger parameter on MetaSound", "tags": ["parameter", "trigger", "metasound"]},
        {"name": "SetWaveParameter", "class_name": "UAudioComponent", "category": "parameter",
         "description": "Set a wave asset parameter on MetaSound", "tags": ["parameter", "wave", "metasound"]},
        {"name": "SetVolumeMultiplier", "class_name": "UAudioComponent", "category": "property",
         "description": "Set volume multiplier (0.0-1.0)", "tags": ["volume", "property"]},
        {"name": "SetPitchMultiplier", "class_name": "UAudioComponent", "category": "property",
         "description": "Set pitch multiplier", "tags": ["pitch", "property"]},
        {"name": "AdjustAttenuation", "class_name": "UAudioComponent", "category": "spatialization",
         "description": "Change attenuation settings at runtime", "tags": ["attenuation", "spatial"]},
        {"name": "SetSubmixSend", "class_name": "UAudioComponent", "category": "routing",
         "description": "Set send level to a submix", "tags": ["submix", "routing", "send"]},
        {"name": "GetPlayState", "class_name": "UAudioComponent", "category": "query",
         "description": "Get current play state (playing/stopped/paused)", "tags": ["state", "query"]},
        {"name": "IsPlaying", "class_name": "UAudioComponent", "category": "query",
         "description": "Check if audio component is currently playing", "tags": ["state", "query", "check"]},
    ]
    for f in functions:
        db.insert_blueprint_audio(f)
    return len(functions)


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
