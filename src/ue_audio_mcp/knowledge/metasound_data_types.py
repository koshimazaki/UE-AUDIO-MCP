"""Static MetaSounds knowledge — pin types, asset types, interfaces, categories.

All values sourced from research/research_metasounds_game_audio.md and
Epic's MetaSounds Reference Guide.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Pin (data) types — what flows between nodes
# ---------------------------------------------------------------------------
PIN_TYPES: dict[str, str] = {
    "Audio": "Signal buffers for DSP manipulation",
    "Trigger": "Sample-accurate execution signals (modular synthesis style)",
    "Float": "Block-rate numeric values",
    "Int32": "Integer values",
    "Bool": "Boolean flags",
    "Time": "Duration values",
    "String": "Labels / debugging text",
    "UObject": "Asset references (USoundWave, etc.)",
    "Enum": "Enumerated variables",
    "WaveAsset": "Sound file references (USoundWave)",
    # Array variants
    "Audio[]": "Array of Audio buffers",
    "Trigger[]": "Array of Triggers",
    "Float[]": "Array of Floats",
    "Int32[]": "Array of Int32s",
    "Bool[]": "Array of Bools",
    "Time[]": "Array of Time values",
    "String[]": "Array of Strings",
    "WaveAsset[]": "Array of WaveAsset references",
}

# ---------------------------------------------------------------------------
# Asset types — top-level MetaSound assets
# ---------------------------------------------------------------------------
ASSET_TYPES: dict[str, dict] = {
    "Source": {
        "description": "Self-contained audio generator — playable",
        "playable": True,
        "key_use": "Final playable sound",
    },
    "Patch": {
        "description": "Reusable node subgraph — not directly playable",
        "playable": False,
        "key_use": "Shared logic (e.g., random pitch, array player)",
    },
    "Preset": {
        "description": "Read-only graph from parent + input overrides",
        "playable": None,  # depends on parent
        "key_use": "Variants (same gun, different settings)",
    },
}

# ---------------------------------------------------------------------------
# Built-in interfaces — standard I/O contracts
# ---------------------------------------------------------------------------
INTERFACES: dict[str, dict] = {
    "UE.Source.OneShot": {
        "description": "One-shot playback with play trigger and finished signal",
        "inputs": [
            {"name": "OnPlay", "type": "Trigger"},
        ],
        "outputs": [
            {"name": "OnFinished", "type": "Trigger"},
            {"name": "Out Mono", "type": "Audio"},
            {"name": "Out Stereo L", "type": "Audio"},
            {"name": "Out Stereo R", "type": "Audio"},
        ],
    },
    "UE.Source.Looping": {
        "description": "Looping playback with play/stop triggers",
        "inputs": [
            {"name": "OnPlay", "type": "Trigger"},
            {"name": "OnStop", "type": "Trigger"},
        ],
        "outputs": [
            {"name": "OnFinished", "type": "Trigger"},
            {"name": "OnLooped", "type": "Trigger"},
            {"name": "Out Mono", "type": "Audio"},
            {"name": "Out Stereo L", "type": "Audio"},
            {"name": "Out Stereo R", "type": "Audio"},
        ],
    },
    "UE.Source.Default": {
        "description": "Default playback with play trigger and stereo output",
        "inputs": [
            {"name": "OnPlay", "type": "Trigger"},
        ],
        "outputs": [
            {"name": "OnFinished", "type": "Trigger"},
            {"name": "Out Mono", "type": "Audio"},
            {"name": "Out Stereo L", "type": "Audio"},
            {"name": "Out Stereo R", "type": "Audio"},
        ],
    },
    "UE.Attenuation": {
        "description": "Distance-based volume falloff",
        "inputs": [
            {"name": "Distance", "type": "Float"},
        ],
        "outputs": [],
    },
    "UE.Spatialization": {
        "description": "3D positioning via azimuth/elevation",
        "inputs": [
            {"name": "Azimuth", "type": "Float"},
            {"name": "Elevation", "type": "Float"},
        ],
        "outputs": [],
    },
}

# ---------------------------------------------------------------------------
# Node categories — groups for browsing
# ---------------------------------------------------------------------------
NODE_CATEGORIES: list[str] = [
    "Generators",
    "Wave Players",
    "Envelopes",
    "Filters",
    "Delays",
    "Dynamics",
    "Triggers",
    "Arrays",
    "Math",
    "Mix",
    "Spatialization",
    "Music",
    "Random",
    "Debug",
    "External IO",
    "General",
    "Patches",
]

# ---------------------------------------------------------------------------
# Pin compatibility — which types can connect to which
# ---------------------------------------------------------------------------
PIN_COMPATIBILITY: dict[str, set[str]] = {
    "Audio": {"Audio", "Float"},
    "Trigger": {"Trigger"},
    "Float": {"Float", "Audio", "Time"},  # Float can connect to Time inputs (seconds)
    "Int32": {"Int32", "Float"},  # Int32 can connect to Float inputs
    "Bool": {"Bool"},
    "Time": {"Time", "Float"},  # Time can connect to Float inputs
    "String": {"String"},
    "UObject": {"UObject", "WaveAsset"},
    "Enum": {"Enum", "Int32"},
    "WaveAsset": {"WaveAsset", "UObject"},
    # Array types match their own type only
    "Audio[]": {"Audio[]"},
    "Trigger[]": {"Trigger[]"},
    "Float[]": {"Float[]"},
    "Int32[]": {"Int32[]"},
    "Bool[]": {"Bool[]"},
    "Time[]": {"Time[]"},
    "String[]": {"String[]"},
    "WaveAsset[]": {"WaveAsset[]"},
}

# ---------------------------------------------------------------------------
# Builder API handle types — for graph spec validation
# ---------------------------------------------------------------------------
BUILDER_HANDLE_TYPES: dict[str, str] = {
    "MetaSoundNodeHandle": "Reference to a node in the graph",
    "MetaSoundNodeOutputHandle": "Reference to a specific output pin",
    "MetaSoundNodeInputHandle": "Reference to a specific input pin",
}
