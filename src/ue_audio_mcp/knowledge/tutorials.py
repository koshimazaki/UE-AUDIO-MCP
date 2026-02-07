"""Structured knowledge extracted from Epic's official UE5 audio tutorials.

Data sources:
  - MetaSounds Quick Start (bomb + wind)
  - Audio Modulation Quick Start
  - Quartz Quick Start
  - WaveTables Quick Start
  - Procedural Music tutorial
  - Audio Gameplay Volumes
  - Soundscape Quick Start
  - MetaSound Builder API reference (109 functions)
  - MetaSounds Reference Guide (type system)
  - MetaSound Function Nodes Reference (107+ nodes)
  - Spatialization Overview
  - Sound Attenuation (8 subsystems)
  - Ambisonics/Soundfield
  - Submixes Overview
  - Volume Proxies Quick Start
  - Audio Console Commands

Used by:
  - Knowledge DB seeder (seed.py)
  - Semantic search
  - Agent context
"""
from __future__ import annotations


# ===================================================================
# MetaSounds Type System (from Reference Guide)
# ===================================================================

METASOUND_PIN_TYPES = {
    "Trigger": {
        "description": "Pulse signal, fires once then resets",
        "color": "white",
        "connectable_to": ["Trigger"],
    },
    "Audio": {
        "description": "Audio-rate signal (sample buffer)",
        "color": "blue",
        "connectable_to": ["Audio"],
    },
    "Float": {
        "description": "32-bit floating point number",
        "color": "green",
        "connectable_to": ["Float", "Audio"],
        "note": "Float->Audio is control-rate, not sample-rate",
    },
    "Int32": {
        "description": "32-bit signed integer",
        "color": "teal",
        "connectable_to": ["Int32", "Float"],
    },
    "Bool": {
        "description": "Boolean true/false",
        "color": "red",
        "connectable_to": ["Bool"],
    },
    "Time": {
        "description": "Duration in seconds",
        "color": "orange",
        "connectable_to": ["Time", "Float"],
    },
    "String": {
        "description": "Text string",
        "color": "magenta",
        "connectable_to": ["String"],
    },
    "WaveAsset": {
        "description": "Reference to a .wav file in Content",
        "color": "purple",
        "connectable_to": ["WaveAsset"],
    },
    "Enum": {
        "description": "Enumeration value",
        "color": "yellow",
        "connectable_to": ["Enum"],
    },
}

# Implicit conversions allowed
METASOUND_TYPE_CONVERSIONS = [
    ("Int32", "Float"),
    ("Float", "Audio"),
    ("Time", "Float"),
    ("Bool", "Int32"),
]

METASOUND_INTERFACES = {
    "UE.Source.OneShot": {
        "description": "Single-play source with OnPlay trigger and OnFinished",
        "inputs": [{"name": "OnPlay", "type": "Trigger"}],
        "outputs": [
            {"name": "Out Left", "type": "Audio"},
            {"name": "Out Right", "type": "Audio"},
            {"name": "OnFinished", "type": "Trigger"},
        ],
    },
    "UE.Source.Looping": {
        "description": "Continuous looping source",
        "inputs": [{"name": "OnPlay", "type": "Trigger"}],
        "outputs": [
            {"name": "Out Left", "type": "Audio"},
            {"name": "Out Right", "type": "Audio"},
            {"name": "OnFinished", "type": "Trigger"},
        ],
    },
    "UE.Attenuation": {
        "description": "Distance-based volume control",
        "inputs": [{"name": "Distance", "type": "Float"}],
        "outputs": [{"name": "Gain", "type": "Float"}],
    },
    "UE.Spatialization": {
        "description": "3D positioning and panning",
        "inputs": [
            {"name": "Azimuth", "type": "Float"},
            {"name": "Elevation", "type": "Float"},
        ],
        "outputs": [],
    },
}

METASOUND_ASSET_TYPES = {
    "Source": "Playable audio asset (like a Sound Wave replacement)",
    "Patch": "Reusable subgraph (like a function/macro)",
    "Preset": "Parameter override on an existing Source or Patch",
}


# ===================================================================
# MetaSound Builder API (109 Blueprint functions)
# ===================================================================

BUILDER_API_FUNCTIONS = [
    # Source/Graph creation
    {"name": "CreateSourceBuilder", "category": "creation", "description": "Create a new MetaSound Source builder", "params": ["Name"]},
    {"name": "CreateSourcePresetBuilder", "category": "creation", "description": "Create a preset from an existing source", "params": ["Name", "ReferencedSource"]},
    {"name": "CreatePatchBuilder", "category": "creation", "description": "Create a reusable patch builder", "params": ["Name"]},
    {"name": "CreatePatchPresetBuilder", "category": "creation", "description": "Create a preset from an existing patch", "params": ["Name", "ReferencedPatch"]},

    # Node operations
    {"name": "AddNode", "category": "nodes", "description": "Add a node to the graph by class name", "params": ["ClassName"]},
    {"name": "AddNodeByClassName", "category": "nodes", "description": "Add node using full class path", "params": ["ClassName"]},
    {"name": "RemoveNode", "category": "nodes", "description": "Remove a node from the graph", "params": ["NodeHandle"]},
    {"name": "FindNodeClassVersion", "category": "nodes", "description": "Get version of a node class", "params": ["ClassName"]},
    {"name": "FindNodeClassIsNative", "category": "nodes", "description": "Check if node class is native C++", "params": ["ClassName"]},

    # Connection operations
    {"name": "ConnectNodes", "category": "connections", "description": "Connect output pin to input pin", "params": ["FromNode", "FromPin", "ToNode", "ToPin"]},
    {"name": "ConnectNodesByInterfaceBindings", "category": "connections", "description": "Connect nodes using interface definitions", "params": ["FromNode", "ToNode"]},
    {"name": "DisconnectNodes", "category": "connections", "description": "Disconnect two connected pins", "params": ["FromNode", "FromPin", "ToNode", "ToPin"]},
    {"name": "DisconnectNodeInput", "category": "connections", "description": "Disconnect all connections to an input", "params": ["Node", "InputPin"]},
    {"name": "DisconnectNodeOutput", "category": "connections", "description": "Disconnect all connections from an output", "params": ["Node", "OutputPin"]},
    {"name": "NodesAreConnected", "category": "connections", "description": "Check if two pins are connected", "params": ["FromNode", "FromPin", "ToNode", "ToPin"]},
    {"name": "GetNodeInputIsConstructorPin", "category": "connections", "description": "Check if input is set at construction only", "params": ["Node", "InputPin"]},
    {"name": "GetNodeInputClassDefault", "category": "connections", "description": "Get default value for a node input", "params": ["Node", "InputPin"]},

    # Input/Output (graph-level)
    {"name": "AddGraphInputNode", "category": "graph_io", "description": "Add an input to the graph", "params": ["Name", "DataType", "DefaultValue"]},
    {"name": "AddGraphOutputNode", "category": "graph_io", "description": "Add an output from the graph", "params": ["Name", "DataType"]},
    {"name": "RemoveGraphInputNode", "category": "graph_io", "description": "Remove a graph input", "params": ["Name"]},
    {"name": "RemoveGraphOutputNode", "category": "graph_io", "description": "Remove a graph output", "params": ["Name"]},

    # Interface operations
    {"name": "AddInterface", "category": "interfaces", "description": "Add a MetaSound interface to the graph", "params": ["InterfaceName"]},
    {"name": "RemoveInterface", "category": "interfaces", "description": "Remove interface from graph", "params": ["InterfaceName"]},
    {"name": "FindInterfaceInputNodes", "category": "interfaces", "description": "Find nodes providing interface inputs", "params": ["InterfaceName"]},
    {"name": "FindInterfaceOutputNodes", "category": "interfaces", "description": "Find nodes consuming interface outputs", "params": ["InterfaceName"]},

    # Node defaults
    {"name": "SetNodeInputDefault", "category": "defaults", "description": "Set default value for node input", "params": ["Node", "InputPin", "Value"]},
    {"name": "GetNodeInputDefault", "category": "defaults", "description": "Get current default value", "params": ["Node", "InputPin"]},
    {"name": "RemoveNodeInputDefault", "category": "defaults", "description": "Remove default, reverting to class default", "params": ["Node", "InputPin"]},

    # Document / metadata
    {"name": "SetGraphDisplayName", "category": "metadata", "description": "Set display name for the graph", "params": ["DisplayName"]},
    {"name": "SetNodeLocation", "category": "metadata", "description": "Set visual position in editor", "params": ["Node", "X", "Y"]},
    {"name": "SetNodeComment", "category": "metadata", "description": "Set comment text on a node", "params": ["Node", "Comment"]},

    # Audition / Preview
    {"name": "Audition", "category": "preview", "description": "Play the graph in-editor for preview", "params": []},
    {"name": "StopAudition", "category": "preview", "description": "Stop in-editor preview", "params": []},
    {"name": "IsAuditioning", "category": "preview", "description": "Check if currently auditioning", "params": []},

    # Build / Export
    {"name": "BuildToAsset", "category": "build", "description": "Compile graph to a UE asset", "params": ["PackagePath", "AssetName"]},
    {"name": "BuildAndOverwriteAsset", "category": "build", "description": "Compile and replace existing asset", "params": ["ExistingAsset"]},
    {"name": "IsPreset", "category": "build", "description": "Check if this builder is a preset", "params": []},
    {"name": "GetRootGraphHandle", "category": "build", "description": "Get handle to the root graph", "params": []},

    # Conversion
    {"name": "ConvertFromPreset", "category": "conversion", "description": "Convert preset back to full graph", "params": []},
    {"name": "ConvertToPreset", "category": "conversion", "description": "Convert graph to preset of reference", "params": ["ReferencedAsset"]},

    # Query
    {"name": "FindNodeInputParent", "category": "query", "description": "Find parent node of an input pin", "params": ["InputPin"]},
    {"name": "FindNodeOutputParent", "category": "query", "description": "Find parent node of an output pin", "params": ["OutputPin"]},
    {"name": "GetNodeInputData", "category": "query", "description": "Get metadata about an input pin", "params": ["Node", "InputPin"]},
    {"name": "GetNodeOutputData", "category": "query", "description": "Get metadata about an output pin", "params": ["Node", "OutputPin"]},
    {"name": "ContainsNode", "category": "query", "description": "Check if graph contains a node", "params": ["NodeHandle"]},
    {"name": "ContainsNodeInput", "category": "query", "description": "Check if node has named input", "params": ["Node", "InputPin"]},
    {"name": "ContainsNodeOutput", "category": "query", "description": "Check if node has named output", "params": ["Node", "OutputPin"]},
    {"name": "GetNodeInputs", "category": "query", "description": "List all inputs on a node", "params": ["NodeHandle"]},
    {"name": "GetNodeOutputs", "category": "query", "description": "List all outputs on a node", "params": ["NodeHandle"]},
]


# ===================================================================
# Spatialization Methods
# ===================================================================

SPATIALIZATION_METHODS = {
    "Panning": {
        "description": "Traditional channel-based panning for speaker layouts",
        "algorithms": {
            "Linear": "Simple linear crossfade between channels",
            "EqualPower": "Constant-power panning (default, -3dB at center)",
            "VBAP": "Vector Base Amplitude Panning for arbitrary speaker layouts",
        },
    },
    "Binaural": {
        "description": "Headphone-based 3D audio using HRTF filters",
        "features": ["HRTF (Head-Related Transfer Function)", "ITD (Interaural Time Difference)", "ILD (Interaural Level Difference)"],
        "plugins": ["Built-in UE5", "Resonance Audio (Google)", "Steam Audio (Valve)"],
        "console_cmd": "au.EnableBinauralAudioForAllSpatialSounds 1",
    },
    "Soundfield": {
        "description": "Ambisonics-based spatial audio encoding",
        "orders": {"First": "4 channels (W, X, Y, Z)", "Note": "UE5 only supports first-order"},
        "channel_orderings": ["FuMa (Furse-Malham)", "ACN (Ambisonic Channel Number)"],
        "normalization": ["SN3D", "N3D"],
    },
}


# ===================================================================
# Sound Attenuation Subsystems
# ===================================================================

ATTENUATION_SUBSYSTEMS = {
    "Volume": {
        "description": "Distance-based volume falloff",
        "params": ["InnerRadius", "FalloffDistance", "FalloffMode", "dBAttenuationAtMax"],
        "falloff_modes": ["Linear", "Logarithmic", "Inverse", "LogReverse", "NaturalSound", "Custom"],
    },
    "Spatialization": {
        "description": "3D positioning method selection",
        "params": ["SpatializationMethod", "SpatializationPlugin"],
        "methods": ["Panning", "Binaural"],
    },
    "AirAbsorption": {
        "description": "Frequency-dependent distance attenuation (high freqs absorbed more)",
        "params": ["bEnableAirAbsorption", "AirAbsorptionMethod"],
        "methods": ["Linear", "CustomCurve"],
    },
    "ListenerFocus": {
        "description": "Camera/listener direction-based volume scaling",
        "params": ["FocusAzimuth", "NonFocusAzimuth", "FocusDistanceScale", "NonFocusDistanceScale",
                   "FocusPriorityScale", "NonFocusPriorityScale", "FocusVolumeAttenuation", "NonFocusVolumeAttenuation"],
    },
    "Reverb": {
        "description": "Distance-based reverb send amount",
        "params": ["bEnableReverbSend", "ReverbSendMethod", "ReverbWetLevelMin", "ReverbWetLevelMax"],
    },
    "Occlusion": {
        "description": "Line-of-sight obstruction (walls, objects)",
        "params": ["bEnableOcclusion", "OcclusionTraceChannel", "OcclusionLowPassFilterFrequency",
                   "OcclusionVolumeAttenuation", "OcclusionInterpolationTime"],
    },
    "Priority": {
        "description": "Voice priority for channel management",
        "params": ["bAttenuationPriority", "PriorityAttenuationMin", "PriorityAttenuationMax",
                   "PriorityAttenuationDistanceMin", "PriorityAttenuationDistanceMax"],
    },
    "SubmixSend": {
        "description": "Distance-based submix routing",
        "params": ["SubmixSendMethod", "SubmixSendDistanceMin", "SubmixSendDistanceMax",
                   "SubmixSendVolumeMin", "SubmixSendVolumeMax"],
    },
}


# ===================================================================
# Audio Console Commands (categorised)
# ===================================================================

AUDIO_CONSOLE_COMMANDS = {
    "metasounds": [
        {"cmd": "au.MetaSound.BlockRate", "type": "int", "default": 100, "description": "Block rate (blocks/sec) for MetaSounds processing"},
        {"cmd": "au.MetaSound.EnableAsyncGeneratorBuilder", "type": "bool", "default": True, "description": "Async MetaSoundGenerator building"},
        {"cmd": "au.MetaSound.DisableWaveCachePriming", "type": "bool", "default": True, "description": "Disable Wave Cache Priming"},
        {"cmd": "au.MetaSound.WavePlayer.SimulateSeek", "type": "bool", "default": False, "description": "Simulate seek by sampling and discarding"},
    ],
    "spatialization": [
        {"cmd": "au.AllowAudioSpatialization", "type": "bool", "default": True, "description": "Enable audio spatialization"},
        {"cmd": "au.DisableBinauralSpatialization", "type": "bool", "default": False, "description": "Disable HRTF binaural rendering"},
        {"cmd": "au.EnableBinauralAudioForAllSpatialSounds", "type": "bool", "default": False, "description": "Force binaural on all spatial sounds"},
        {"cmd": "au.DisableDistanceAttenuation", "type": "bool", "default": False, "description": "Disable distance-based volume falloff"},
        {"cmd": "au.DisableStereoSpread", "type": "bool", "default": False, "description": "Render from single point, no spread"},
    ],
    "submixes": [
        {"cmd": "au.BypassAllSubmixEffects", "type": "bool", "default": False, "description": "Bypass all submix effects"},
        {"cmd": "au.DisableReverbSubmix", "type": "bool", "default": False, "description": "Disable reverb submix"},
        {"cmd": "au.DisableSubmixEffectEQ", "type": "bool", "default": True, "description": "Disable EQ submix"},
    ],
    "streaming": [
        {"cmd": "au.MaxConcurrentStreams", "type": "int", "default": None, "description": "Max concurrent audio streams"},
        {"cmd": "au.streamcaching.ResizeAudioCacheTo", "type": "float", "default": None, "description": "Audio cache size in MB"},
        {"cmd": "au.streamcaching.FlushAudioCache", "type": "bool", "default": False, "description": "Flush non-retained cached audio"},
    ],
    "quartz": [
        {"cmd": "au.Quartz.HeadlessClockSampleRate", "type": "int", "default": None, "description": "Quartz clock sample rate without mixer"},
        {"cmd": "au.Quartz.MaxSubscribersToUpdatePerTick", "type": "int", "default": 0, "description": "Max Quartz subscriber updates per tick"},
    ],
    "visualization": [
        {"cmd": "au.3dVisualize.ActiveSounds", "type": "int", "default": 0, "description": "Active sounds visualization mode (0-5)"},
        {"cmd": "au.3dVisualize.Attenuation", "type": "bool", "default": False, "description": "Visualize attenuation spheres"},
        {"cmd": "au.3dVisualize.Listeners", "type": "bool", "default": False, "description": "Visualize listener positions"},
    ],
}


# ===================================================================
# Tutorial Workflow Catalogue
# ===================================================================

TUTORIAL_WORKFLOWS = [
    {
        "name": "Wind System",
        "tutorial": "MetaSounds Quick Start",
        "url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-quick-start",
        "layers": ["blueprint", "metasounds"],
        "blueprint_template": "blueprints/wind_system.json",
        "metasound_template": "metasounds/wind.json",
        "description": "Player speed drives wind noise filter cutoff",
        "tags": ["procedural", "wind", "environment", "movement"],
    },
    {
        "name": "Bomb Fuse",
        "tutorial": "MetaSounds Quick Start",
        "url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-quick-start",
        "layers": ["blueprint", "metasounds"],
        "blueprint_template": "blueprints/bomb_fuse.json",
        "metasound_template": "metasounds/gunshot.json",
        "description": "Timer-triggered explosion with fuse countdown",
        "tags": ["timer", "explosion", "gameplay", "oneshot"],
    },
    {
        "name": "Spectral Analysis",
        "tutorial": "Submixes Overview",
        "url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-submixes-in-unreal-engine",
        "layers": ["blueprint"],
        "blueprint_template": "blueprints/spectral_analysis.json",
        "description": "Analyze frequency spectrum from submix for visualizers",
        "tags": ["analysis", "spectrum", "visualizer", "submix"],
    },
    {
        "name": "Volume Proxy",
        "tutorial": "Volume Proxies Quick Start",
        "url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/volume-proxies-quick-start",
        "layers": ["blueprint"],
        "blueprint_template": "blueprints/volume_proxy.json",
        "description": "Scale audio volume proxy with mouse wheel, condition interface with shift key",
        "tags": ["volume", "proxy", "interface", "interaction"],
    },
    {
        "name": "Quartz Beat Sync",
        "tutorial": "Quartz Quick Start",
        "url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/quartz-quick-start-in-unreal-engine",
        "layers": ["blueprint"],
        "blueprint_template": "blueprints/quartz_beat_sync.json",
        "description": "Sample-accurate beat-synchronized playback with quantized events",
        "tags": ["music", "rhythm", "beat", "quartz", "timing"],
    },
    {
        "name": "Audio Modulation",
        "tutorial": "Audio Modulation Quick Start",
        "url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/audio-modulation-quick-start-in-unreal-engine",
        "layers": ["blueprint"],
        "blueprint_template": "blueprints/audio_modulation.json",
        "description": "Control Bus driven audio modulation from game state",
        "tags": ["modulation", "control_bus", "dynamic", "mix"],
    },
    {
        "name": "Soundscape Ambient",
        "tutorial": "Soundscape Quick Start",
        "url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/soundscape-quick-start",
        "layers": ["blueprint"],
        "blueprint_template": "blueprints/soundscape_ambient.json",
        "description": "Procedural ambient via GameplayTags and Palette/Color system",
        "tags": ["ambient", "environment", "soundscape", "procedural"],
    },
    {
        "name": "Spatial Attenuation",
        "tutorial": "Sound Attenuation + Spatialization Overview",
        "url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/sound-attenuation-in-unreal-engine",
        "layers": ["blueprint"],
        "blueprint_template": "blueprints/spatial_attenuation.json",
        "description": "3D spatialized sound with distance attenuation, following actor",
        "tags": ["3d", "spatial", "attenuation", "position"],
    },
    {
        "name": "Submix Recording",
        "tutorial": "Submixes Overview",
        "url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-submixes-in-unreal-engine",
        "layers": ["blueprint"],
        "blueprint_template": "blueprints/submix_recording.json",
        "description": "Record submix output to WAV file",
        "tags": ["recording", "submix", "capture", "wav"],
    },
]
