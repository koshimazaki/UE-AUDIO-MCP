"""Static Wwise knowledge — object types, properties, references, defaults.

All values sourced from WAAPI documentation and research/research_waapi_mcp_server.md.
Phase 1: static Python dicts. Phase 2: migrated to Cloudflare D1.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Object types accepted by ak.wwise.core.object.create
# ---------------------------------------------------------------------------
OBJECT_TYPES: set[str] = {
    "Sound",
    "RandomSequenceContainer",
    "SwitchContainer",
    "BlendContainer",
    "ActorMixer",
    "Event",
    "Action",
    "Bus",
    "AuxBus",
    "WorkUnit",
    "Folder",
    "Attenuation",
    "SoundBank",
    "GameParameter",
    "SwitchGroup",
    "Switch",
    "StateGroup",
    "State",
    "Trigger",
}

# ---------------------------------------------------------------------------
# Common property names for ak.wwise.core.object.setProperty
# ---------------------------------------------------------------------------
COMMON_PROPERTIES: dict[str, str] = {
    "Volume": "dB offset (-200 to 200)",
    "Pitch": "Cents offset (-2400 to 2400)",
    "Lowpass": "Low-pass filter (0-100)",
    "Highpass": "High-pass filter (0-100)",
    "MakeUpGain": "Make-up gain in dB",
    "InitialDelay": "Initial delay in seconds",
    "Priority": "Voice priority (0-100)",
    "PriorityDistanceOffset": "Priority offset by distance",
    "UserAuxSendVolume0": "Aux send 0 volume in dB",
    "UserAuxSendVolume1": "Aux send 1 volume in dB",
    "UserAuxSendVolume2": "Aux send 2 volume in dB",
    "UserAuxSendVolume3": "Aux send 3 volume in dB",
    "GameAuxSendVolume": "Game-defined aux send volume",
    "OutputBusVolume": "Output bus volume in dB",
    "OutputBusHighpass": "Output bus high-pass (0-100)",
    "OutputBusLowpass": "Output bus low-pass (0-100)",
    "IsLoopingEnabled": "Enable looping (bool)",
    "IsLoopingInfinite": "Infinite loop (bool)",
    "LoopCount": "Number of loops (int, 0 = infinite if IsLoopingInfinite)",
    "RandomOrSequence": "0 = Random, 1 = Sequence",
    "NormalOrShuffle": "0 = Normal, 1 = Shuffle",
    "IsNonCachable": "Disable caching (bool)",
    "IsStreamingEnabled": "Enable streaming (bool)",
    "IsZeroLatency": "Zero-latency streaming (bool)",
}

# ---------------------------------------------------------------------------
# Common references for ak.wwise.core.object.setReference
# ---------------------------------------------------------------------------
COMMON_REFERENCES: dict[str, str] = {
    "OutputBus": "Output bus path or GUID",
    "Attenuation": "Attenuation ShareSet path or GUID",
    "SwitchGroupOrStateGroup": "Switch/State group for SwitchContainers",
    "Conversion": "Audio conversion ShareSet",
    "Effect0": "Effect slot 0",
    "Effect1": "Effect slot 1",
    "Effect2": "Effect slot 2",
    "Effect3": "Effect slot 3",
}

# ---------------------------------------------------------------------------
# Default hierarchy paths in a new Wwise project
# ---------------------------------------------------------------------------
DEFAULT_PATHS: dict[str, str] = {
    "actor_mixer": "\\Actor-Mixer Hierarchy\\Default Work Unit",
    "events": "\\Events\\Default Work Unit",
    "switches": "\\Switches\\Default Work Unit",
    "states": "\\States\\Default Work Unit",
    "game_parameters": "\\Game Parameters\\Default Work Unit",
    "triggers": "\\Triggers\\Default Work Unit",
    "soundbanks": "\\SoundBanks\\Default Work Unit",
    "master_bus": "\\Master-Mixer Hierarchy\\Default Work Unit\\Master Audio Bus",
    "attenuations": "\\Attenuations\\Default Work Unit",
}

# ---------------------------------------------------------------------------
# Event action types — @ActionType integer values
# ---------------------------------------------------------------------------
EVENT_ACTION_TYPES: dict[str, int] = {
    "Play": 1,
    "Stop": 2,
    "StopAll": 3,
    "Pause": 4,
    "Resume": 5,
    "Break": 6,
    "Mute": 7,
    "UnMute": 8,
    "SetVolume": 9,
    "SetPitch": 10,
    "SetLPF": 11,
    "SetHPF": 12,
    "SetBusVolume": 13,
    "SetState": 14,
    "SetSwitch": 15,
    "SetRTPC": 16,
    "SetGameParameter": 17,
    "Seek": 18,
}

# ---------------------------------------------------------------------------
# Name conflict modes for onNameConflict param
# ---------------------------------------------------------------------------
NAME_CONFLICT_MODES: set[str] = {"merge", "rename", "replace", "fail"}

# ---------------------------------------------------------------------------
# Import operation modes for ak.wwise.core.audio.import
# ---------------------------------------------------------------------------
IMPORT_OPERATIONS: set[str] = {"createNew", "useExisting", "replaceExisting"}

# ---------------------------------------------------------------------------
# Attenuation curve types for ak.wwise.core.object.setAttenuationCurve
# ---------------------------------------------------------------------------
CURVE_TYPES: set[str] = {
    "VolumeDryUsage",
    "VolumeWetGameUsage",
    "VolumeWetUserUsage",
    "LowPassFilterUsage",
    "HighPassFilterUsage",
    "SpreadUsage",
    "FocusUsage",
}

# ---------------------------------------------------------------------------
# Curve point shapes for attenuation/RTPC points
# ---------------------------------------------------------------------------
CURVE_SHAPES: set[str] = {
    "Linear",
    "Log1",
    "Log2",
    "Log3",
    "SCurve",
    "Exp1",
    "Exp2",
    "Exp3",
    "Constant",
}

# ---------------------------------------------------------------------------
# Transport actions for ak.wwise.core.transport.executeAction
# ---------------------------------------------------------------------------
TRANSPORT_ACTIONS: set[str] = {"play", "stop", "pause"}
