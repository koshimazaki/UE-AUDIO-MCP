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

    # UE 5.7: Graph variables
    {"name": "AddGraphVariable", "category": "variables", "description": "Add a typed variable to the graph", "params": ["Name", "DataType", "DefaultValue"]},
    {"name": "AddGraphVariableGetNode", "category": "variables", "description": "Add a getter node for a graph variable", "params": ["VariableName"]},
    {"name": "AddGraphVariableSetNode", "category": "variables", "description": "Add a setter node for a graph variable", "params": ["VariableName"]},
    {"name": "AddGraphVariableGetDelayedNode", "category": "variables", "description": "Add a delayed getter (reads previous frame value)", "params": ["VariableName"]},
    {"name": "RemoveGraphVariable", "category": "variables", "description": "Remove a variable from the graph", "params": ["VariableName"]},
    {"name": "GetGraphVariableDefault", "category": "variables", "description": "Get default value of a graph variable", "params": ["VariableName"]},

    # UE 5.7: Graph pages
    {"name": "AddGraphPage", "category": "pages", "description": "Add a new page to the graph for organization", "params": ["PageName"]},
    {"name": "RemoveGraphPage", "category": "pages", "description": "Remove a graph page", "params": ["PageName"]},
    {"name": "ResetGraphPages", "category": "pages", "description": "Reset all graph pages to default", "params": []},

    # UE 5.7: Viewmodel / Preset widget
    {"name": "InitializeBuilder", "category": "viewmodel", "description": "Initialize MetaSoundEditorViewModel from a builder instance", "params": ["MetaSoundEditorViewModel", "Builder"]},
    {"name": "InitializeMetaSound", "category": "viewmodel", "description": "Initialize MetaSoundEditorViewModel from a MetaSound asset", "params": ["MetaSoundEditorViewModel", "MetaSoundAsset"]},
    {"name": "SetLiteralWidgetInputViewmodels", "category": "viewmodel", "description": "Bind a literal widget (knob/slider) to MetaSoundEditorViewModel", "params": ["LiteralWidget", "MetaSoundViewmodel", "WorldContext"]},
    {"name": "GetSupportedMetaSounds", "category": "viewmodel", "description": "Interface function: specify which MetaSound assets a preset widget supports", "params": ["SupportAllPresets", "ExcludedMetaSounds", "IncludedMetaSounds"]},

    # UE 5.7: Transactions (undo/redo observation)
    {"name": "AddTransactionListener", "category": "transactions", "description": "Register a listener for builder graph transactions (undo/redo)", "params": ["Listener"]},
    {"name": "RemoveTransactionListener", "category": "transactions", "description": "Unregister a transaction listener", "params": ["Listener"]},
    {"name": "GetLastTransactionRegistered", "category": "transactions", "description": "Get the most recently registered transaction for undo tracking", "params": []},

    # UE 5.7: Live updates
    {"name": "SetLiveUpdatesEnabled", "category": "live_update", "description": "Enable or disable real-time topology changes while auditioning", "params": ["bEnabled"]},

    # UE 5.7: Expanded connections
    {"name": "ConnectNodeInputToGraphInput", "category": "connections", "description": "Connect a node input pin directly to a graph-level input", "params": ["Node", "InputPin", "GraphInputName"]},
    {"name": "ConnectNodeOutputToGraphOutput", "category": "connections", "description": "Connect a node output pin directly to a graph-level output", "params": ["Node", "OutputPin", "GraphOutputName"]},
    {"name": "DisconnectNodesByInterfaceBindings", "category": "connections", "description": "Disconnect all connections made via interface bindings between two nodes", "params": ["FromNode", "ToNode"]},

    # UE 5.7: Expanded metadata
    {"name": "FindMemberMetadata", "category": "metadata", "description": "Find metadata attached to a graph member (node, input, output)", "params": ["MemberID", "MetadataKey"]},
    {"name": "SetMemberMetadata", "category": "metadata", "description": "Set metadata on a graph member", "params": ["MemberID", "MetadataKey", "MetadataValue"]},
    {"name": "ClearMemberMetadata", "category": "metadata", "description": "Remove metadata from a graph member", "params": ["MemberID", "MetadataKey"]},
    {"name": "FindGraphComment", "category": "metadata", "description": "Find an existing graph comment by ID", "params": ["CommentID"]},
    {"name": "FindOrAddGraphComment", "category": "metadata", "description": "Find or create a graph comment at a position", "params": ["CommentText", "X", "Y"]},
    {"name": "RemoveGraphComment", "category": "metadata", "description": "Remove a graph comment by ID", "params": ["CommentID"]},
    {"name": "SetNodeCommentVisible", "category": "metadata", "description": "Toggle visibility of a node's comment bubble", "params": ["Node", "bVisible"]},

    # UE 5.7: Expanded conversion
    {"name": "GetReferencedPresetAsset", "category": "conversion", "description": "Get the parent asset that a preset references", "params": []},

    # UE 5.7: Expanded query
    {"name": "GetGraphInputNames", "category": "query", "description": "List all graph-level input names", "params": []},
    {"name": "GetGraphOutputNames", "category": "query", "description": "List all graph-level output names", "params": []},
    {"name": "FindGraphInputNode", "category": "query", "description": "Find the node handle for a named graph input", "params": ["InputName"]},
    {"name": "FindGraphOutputNode", "category": "query", "description": "Find the node handle for a named graph output", "params": ["OutputName"]},
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
    {
        "name": "First Person Footfalls",
        "tutorial": "Creating First Person Footfalls with MetaSounds",
        "url": "https://dev.epicgames.com/community/learning/recommended-community-tutorial/WzJ/creating-first-person-footfalls-with-metasounds",
        "layers": ["blueprint", "metasounds"],
        "blueprint_template": "blueprints/footfalls_simple.json",
        "metasound_template": "metasounds/footfalls_simple.json",
        "description": "Random footfall samples with timed repeat, graceful stop via custom trigger, Blueprint velocity+ground check with DoOnce gate",
        "tags": ["footsteps", "movement", "first_person", "random", "trigger_repeat"],
    },
    {
        "name": "Random Audio Playback",
        "tutorial": "Random audio file playback in MetaSound - Ambient Sounds",
        "url": "https://dev.epicgames.com/community/learning/tutorials/random-audio-metasound",
        "layers": ["metasounds"],
        "metasound_template": "metasounds/random_playback.json",
        "description": "Weighted random WaveAsset selection with timed repetition. OnPlay → Trigger Repeat (Period) → Random Get picks from array using Weights float array for probability control (e.g. [0.1, 0.1, 0.7, 0.1] = 70% index 2). No-repeat guarantee prevents consecutive duplicates. Core building block for ambient, footsteps, and variation-based sounds.",
        "tags": ["random", "ambient", "weighted", "variation", "trigger_repeat", "building_block"],
    },
    {
        "name": "Ambient Stingers with Trigger Boxes",
        "tutorial": "Ambient Sounds - Stingers, Transitions & Day/Night Cycles",
        "url": "https://dev.epicgames.com/community/learning/tutorials/ambient-sounds-metasound",
        "layers": ["blueprint", "metasounds"],
        "blueprint_template": "blueprints/ambient_stingers.json",
        "metasound_template": "metasounds/ambient_stingers.json",
        "description": "Multi-layer ambient with trigger-box crossfades. Base ambient loop + birds/bugs layers faded in via InterpTo (3s). Level Blueprint fires named triggers through Audio Parameter Interface.",
        "tags": ["ambient", "stingers", "trigger_box", "crossfade", "interp", "layers", "level_blueprint"],
    },
    {
        "name": "MetaSound Preset Widget",
        "tutorial": "Creating MetaSound Preset Widgets (UE 5.7)",
        "url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-metasound-preset-widgets",
        "layers": ["blueprint"],
        "blueprint_template": "blueprints/metasound_preset_widget.json",
        "description": "Editor Utility Widget with custom knob/slider UI for MetaSound presets. OnPresetWidgetConstructed caches Builder, Construct initializes viewmodel, SetLiteralWidgetInputViewmodels binds float knobs. TechAudioTools plugin (5.7+).",
        "tags": ["preset", "widget", "ui", "viewmodel", "editor", "knob", "5.7", "TechAudioTools"],
    },
    {
        "name": "Sample Player with Loop Controls",
        "tutorial": "Random audio file playback in MetaSound - Ambient Sounds",
        "url": "https://dev.epicgames.com/community/learning/tutorials/random-audio-metasound",
        "layers": ["metasounds"],
        "metasound_template": "metasounds/sample_player.json",
        "description": "Minimal stereo Wave Player with Loop Start and Loop Duration exposed as slider inputs. Scrub Loop Start to find clean loop points. Duration -1.0 loops whole file. Simplest possible MetaSound Source.",
        "tags": ["playback", "loop", "sample", "slider", "minimal", "building_block"],
    },
    {
        "name": "Subtractive Synthesis",
        "tutorial": "Subtractive synthesis with MetaSounds - Noise + LFO + Filter",
        "url": "https://dev.epicgames.com/community/learning/tutorials/metasound-subtractive-synthesis",
        "layers": ["metasounds"],
        "metasound_template": "metasounds/subtractive_synth.json",
        "description": "Classic subtractive synthesis: White Noise → Mono Mixer → Biquad Filter (Band Pass). LFO (Sine) sweeps cutoff between 300 Hz and 20 kHz. Frequency input controls LFO rate (0.096 Hz default = slow sweep). Bandwidth controls filter resonance. Produces wind, sci-fi ambience, evolving textures.",
        "tags": ["synthesis", "subtractive", "noise", "lfo", "filter", "bandpass", "procedural"],
    },
    {
        "name": "SFX Synth Generator",
        "tutorial": "MetaSoundSource SFX Generator (open source UE5.7 plugin)",
        "url": "https://github.com/metasoundsource/sfx-generator",
        "layers": ["metasounds", "blueprint"],
        "metasound_template": "metasounds/sfx_synth.json",
        "description": "Complete modular SFX synthesizer: 5-oscillator Generator (Pulse/Triangle/Saw/Sine/Noise) → Spectral Effects (WaveShaper/BitCrusher/RingMod) → Crossfade Filter (LP/BP/HP with AD envelope) → Amplifier (Envelope + AM LFO) → Temporal Effects (Delay/Plate Reverb/4x Flanger send bus). Normalized 0-1 inputs mapped via Linear To Log Frequency. Multistage pitch jumps for laser/sci-fi. Wave Writer for recording output. Preset system: one Source, many parameter snapshots = many sounds. Blueprint Editor Widget with knobs, randomize, lock, record toggle.",
        "tags": ["synthesis", "sfx", "generator", "procedural", "preset", "modular", "oscillator", "filter", "effects", "waveshaper", "bitcrusher", "reverb", "flanger", "delay"],
    },
    {
        "name": "Mono Synth (Minimoog-style)",
        "tutorial": "Minimoog-style mono synthesizer with MetaSounds",
        "url": "https://dev.epicgames.com/community/learning/tutorials/metasound-mono-synth",
        "layers": ["blueprint", "metasounds"],
        "blueprint_template": "blueprints/set_float_parameter.json",
        "metasound_template": "metasounds/mono_synth.json",
        "description": "Minimoog-inspired mono synth: Saw + Pink Noise + Square → Mono Mixer (4) → Biquad Filter (Low Pass). Looping AD Envelope sweeps filter cutoff via Map Range (base Cutoff → Filter env amount). MSP_Sequencer steps MIDI notes with Glide portamento. MSP_ADControl splits Period by attack/decay ratio. Blueprint uses Event Tick → Set Float Parameter for real-time knob updates.",
        "tags": ["synthesis", "mono", "minimoog", "sequencer", "envelope", "filter", "oscillator", "procedural"],
    },
]


# ===================================================================
# UE4 Sound Cue → UE5 MetaSounds Conversion Map
# ===================================================================
# Source: 207 uasset entries from "Ambient and Procedural Sound Design"
# (Stevens & Raybould, UE 4.23-4.24, Epic official learning path).
# Sound Cues are legacy but still work in UE5. MetaSounds replaces them
# for procedural audio. Blueprint patterns transfer directly.

UE4_TO_UE5_CONVERSION: list[dict] = [
    # --- Sound Cue Nodes → MetaSounds Equivalents ---
    {
        "ue4_node": "Random",
        "ue4_system": "Sound Cue",
        "ue4_description": "Picks random input from N connected Sound Waves. Weight per input.",
        "ue5_equivalent": "Random Get (WaveAssetArray)",
        "ue5_system": "MetaSounds",
        "ue5_notes": "Use WaveAsset[] input + No Repeats. Weights via Float[] input.",
        "example_from": "as_ab_ao_birds_combined, as_ab_ao_Frog_01_Cue",
    },
    {
        "ue4_node": "Delay",
        "ue4_system": "Sound Cue",
        "ue4_description": "Adds random delay (min/max) before playing the connected sound.",
        "ue5_equivalent": "Trigger Delay / Random Float + Trigger Delay",
        "ue5_system": "MetaSounds",
        "ue5_notes": "Random Float(Min,Max) → Trigger Delay(Duration) → Wave Player(Play).",
        "example_from": "as_ab_ao_village_Blue_Tit, as_ab_ao_Pigeon",
    },
    {
        "ue4_node": "Looping",
        "ue4_system": "Sound Cue",
        "ue4_description": "Loops the connected sound continuously.",
        "ue5_equivalent": "Wave Player (Loop=true)",
        "ue5_system": "MetaSounds",
        "ue5_notes": "Set Loop bool input to true. Loop Start/Duration for partial loops.",
        "example_from": "AL_Meadow_With_Wind, as_ab_sl_flies_looping",
    },
    {
        "ue4_node": "Modulator (Pitch)",
        "ue4_system": "Sound Cue",
        "ue4_description": "Randomizes pitch within min/max range on each play.",
        "ue5_equivalent": "Random Float → Wave Player (Pitch Shift)",
        "ue5_system": "MetaSounds",
        "ue5_notes": "Random Float(Min,Max) output → Pitch Shift input on Wave Player.",
        "example_from": "Procedural Sound Design: Modulation Approaches tutorial",
    },
    {
        "ue4_node": "Modulator (Volume)",
        "ue4_system": "Sound Cue",
        "ue4_description": "Randomizes volume within min/max range on each play.",
        "ue5_equivalent": "Random Float → Multiply (Audio by Float)",
        "ue5_system": "MetaSounds",
        "ue5_notes": "Random Float → Multiply gain on audio signal.",
        "example_from": "Procedural Sound Design: Modulation Approaches tutorial",
    },
    {
        "ue4_node": "Concatenator",
        "ue4_system": "Sound Cue",
        "ue4_description": "Plays connected sounds in sequence (one after another).",
        "ue5_equivalent": "Wave Player (On Finished) → next Wave Player (Play)",
        "ue5_system": "MetaSounds",
        "ue5_notes": "Chain On Finished triggers. Or use Trigger Sequence for round-robin.",
        "example_from": "Sequential ambient events",
    },
    {
        "ue4_node": "Switch (by parameter)",
        "ue4_system": "Sound Cue",
        "ue4_description": "Selects input based on integer/bool parameter at runtime.",
        "ue5_equivalent": "Trigger Route / MSP_Switch_3Inputs",
        "ue5_system": "MetaSounds",
        "ue5_notes": "Trigger Route for N outputs by index. Or build custom Patch for switching.",
        "example_from": "Switching Sounds for Fake Occlusion tutorial",
    },
    {
        "ue4_node": "Crossfade by Param",
        "ue4_system": "Sound Cue",
        "ue4_description": "Crossfades between inputs based on a float parameter.",
        "ue5_equivalent": "MSP_CrossFadeByParam_3Inputs / Crossfade (Audio, 2)",
        "ue5_system": "MetaSounds",
        "ue5_notes": "For 2 inputs: Crossfade (Audio, 2). For 3+: build custom Patch with Map Range → gains.",
        "example_from": "Distance-based weapon tails (Craig Owen)",
    },
    {
        "ue4_node": "Mixer",
        "ue4_system": "Sound Cue",
        "ue4_description": "Mixes multiple sound inputs with individual volume controls.",
        "ue5_equivalent": "Mono Mixer / Stereo Mixer",
        "ue5_system": "MetaSounds",
        "ue5_notes": "Mono Mixer(N) for mono, Stereo Mixer(N) for stereo. Per-input Gain.",
        "example_from": "Layered ambient beds, vehicle engine layers",
    },
    {
        "ue4_node": "Attenuation",
        "ue4_system": "Sound Cue",
        "ue4_description": "Distance-based volume falloff settings.",
        "ue5_equivalent": "Sound Attenuation asset (unchanged)",
        "ue5_system": "UE5 (same system)",
        "ue5_notes": "Sound Attenuation assets work identically in UE5. No conversion needed.",
        "example_from": "93 attenuation presets from Ambient Procedural Sound project",
    },
    # --- Blueprint Audio Functions (UE4→UE5, mostly unchanged) ---
    {
        "ue4_node": "SpawnSoundAtLocation",
        "ue4_system": "Blueprint",
        "ue4_description": "Spawns a 3D sound at a world location. Fire-and-forget.",
        "ue5_equivalent": "SpawnSoundAtLocation (unchanged)",
        "ue5_system": "Blueprint (same API)",
        "ue5_notes": "Works identically. Can now reference MetaSounds Source instead of Sound Cue.",
        "example_from": "Audio_Fairy_01_Public, Fish_Splash_DEMO",
    },
    {
        "ue4_node": "SpawnSoundAttached",
        "ue4_system": "Blueprint",
        "ue4_description": "Spawns a sound attached to a component (follows it).",
        "ue5_equivalent": "SpawnSoundAttached (unchanged)",
        "ue5_system": "Blueprint (same API)",
        "ue5_notes": "Works identically. Add SetFloatParameter for MetaSounds graph inputs.",
        "example_from": "Audio_Cave_Door_bp_01, Player Oriented Sound Blueprint",
    },
    {
        "ue4_node": "Audio Volume (Ambient Zone)",
        "ue4_system": "Level Design",
        "ue4_description": "Volume actor with interior/exterior audio settings for occlusion.",
        "ue5_equivalent": "Audio Gameplay Volume",
        "ue5_system": "UE5 (upgraded)",
        "ue5_notes": "UE5 Audio Gameplay Volumes extend Audio Volumes with submix routing and effect profiles.",
        "example_from": "Ambient Zones for Occlusion, Dynamic Occlusion tutorials",
    },
    {
        "ue4_node": "Sound Cue (general)",
        "ue4_system": "Sound Cue",
        "ue4_description": "Node-based audio graph for randomization, modulation, layering.",
        "ue5_equivalent": "MetaSounds Source",
        "ue5_system": "MetaSounds",
        "ue5_notes": "MetaSounds replaces Sound Cues for all procedural audio. Sound Cues still work for simple playback but cannot do DSP synthesis, filters, or real-time parameter modulation.",
        "example_from": "All 48 Sound Cues from Ambient Procedural Sound project",
    },
]
