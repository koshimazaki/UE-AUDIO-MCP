"""Tests for MetaSounds Builder tools — ms_build_graph, ms_create_source, etc."""

from __future__ import annotations

import copy
import json
import os

from ue_audio_mcp.knowledge.metasound_nodes import (
    CLASS_NAME_TO_DISPLAY,
    class_name_to_display,
    infer_class_type,
)
from ue_audio_mcp.tools.ms_builder import (
    ms_add_node,
    ms_audition,
    ms_build_graph,
    ms_connect_pins,
    ms_create_source,
    ms_export_graph,
    ms_save_asset,
    ms_set_default,
    _inline_convert,
)


def _load_template(name: str) -> dict:
    """Load a MetaSounds template for testing."""
    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "src", "ue_audio_mcp", "templates", "metasounds",
    )
    with open(os.path.join(template_dir, f"{name}.json")) as f:
        return json.load(f)


# -- ms_build_graph ----------------------------------------------------------

def test_build_graph_valid(ue5_conn, mock_ue5_plugin):
    spec = _load_template("ui_sound")
    mock_ue5_plugin.set_response("create_builder", {"status": "ok"})
    result = json.loads(ms_build_graph(json.dumps(spec)))
    assert result["status"] == "ok"
    assert result["commands_sent"] > 0
    assert len(mock_ue5_plugin.commands) == result["commands_sent"]


def test_build_graph_invalid_json(ue5_conn):
    result = json.loads(ms_build_graph("not json"))
    assert result["status"] == "error"
    assert "Invalid" in result["message"]


def test_build_graph_validation_error(ue5_conn):
    bad_spec = {"name": "test", "asset_type": "Source", "nodes": [], "connections": [
        {"from_node": "nonexistent", "from_pin": "x", "to_node": "also_gone", "to_pin": "y"}
    ]}
    result = json.loads(ms_build_graph(json.dumps(bad_spec)))
    assert result["status"] == "error"
    assert "validation error" in result["message"]


def test_build_graph_not_connected():
    import ue_audio_mcp.ue5_connection as ue5_module
    ue5_module._connection = None
    spec = _load_template("ui_sound")
    result = json.loads(ms_build_graph(json.dumps(spec)))
    assert result["status"] == "error"
    assert "Not connected" in result["message"]
    ue5_module._connection = None


def test_build_graph_command_sequence(ue5_conn, mock_ue5_plugin):
    spec = _load_template("gunshot")
    result = json.loads(ms_build_graph(json.dumps(spec)))
    assert result["status"] == "ok"
    actions = [c["action"] for c in mock_ue5_plugin.commands]
    assert actions[0] == "create_builder"
    assert actions[-1] == "build_to_asset"
    assert "add_node" in actions
    assert "connect" in actions


# -- ms_create_source --------------------------------------------------------

def test_create_source(ue5_conn, mock_ue5_plugin):
    result = json.loads(ms_create_source("MySound", "Source"))
    assert result["status"] == "ok"
    assert "Created Source" in result["message"]
    assert mock_ue5_plugin.commands[-1]["action"] == "create_builder"


def test_create_source_invalid_type(ue5_conn):
    result = json.loads(ms_create_source("MySound", "InvalidType"))
    assert result["status"] == "error"
    assert "Invalid asset_type" in result["message"]


# -- ms_add_node -------------------------------------------------------------

def test_add_node(ue5_conn, mock_ue5_plugin):
    result = json.loads(ms_add_node("Sine", "osc1", 100, 200))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "add_node"
    assert cmd["node_type"] == "Sine"
    assert cmd["position"] == [100, 200]


def test_add_node_unknown(ue5_conn):
    result = json.loads(ms_add_node("NonexistentNode", "n1"))
    assert result["status"] == "error"
    assert "Unknown node_type" in result["message"]


# -- ms_connect_pins ---------------------------------------------------------

def test_connect_pins(ue5_conn, mock_ue5_plugin):
    result = json.loads(ms_connect_pins("osc1", "Audio", "mixer1", "Audio 0"))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "connect"
    assert cmd["from_node"] == "osc1"
    assert cmd["to_pin"] == "Audio 0"


# -- ms_set_default ----------------------------------------------------------

def test_set_default(ue5_conn, mock_ue5_plugin):
    result = json.loads(ms_set_default("osc1", "Frequency", "440.0"))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "set_default"
    assert cmd["value"] == 440.0  # parsed from JSON string


def test_set_default_string_value(ue5_conn, mock_ue5_plugin):
    result = json.loads(ms_set_default("player1", "WaveAsset", "mysound"))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["value"] == "mysound"  # kept as string


# -- ms_save_asset -----------------------------------------------------------

def test_save_asset(ue5_conn, mock_ue5_plugin):
    result = json.loads(ms_save_asset("TestAsset", "/Game/Audio/"))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "build_to_asset"
    assert cmd["path"] == "/Game/Audio/"


def test_save_asset_invalid_path(ue5_conn):
    result = json.loads(ms_save_asset("Bad", "/tmp/outside/"))
    assert result["status"] == "error"
    assert "/Game/" in result["message"]


def test_save_asset_traversal_path(ue5_conn):
    result = json.loads(ms_save_asset("Bad", "/Game/../etc/"))
    assert result["status"] == "error"
    assert ".." in result["message"]


# -- ms_audition -------------------------------------------------------------

def test_audition(ue5_conn, mock_ue5_plugin):
    result = json.loads(ms_audition("TestSound"))
    assert result["status"] == "ok"
    assert "TestSound" in result["message"]
    assert mock_ue5_plugin.commands[-1]["action"] == "audition"


def test_audition_not_connected():
    import ue_audio_mcp.ue5_connection as ue5_module
    ue5_module._connection = None
    result = json.loads(ms_audition())
    assert result["status"] == "error"
    assert "Not connected" in result["message"]
    ue5_module._connection = None


# -- ms_export_graph ---------------------------------------------------------

MOCK_EXPORT_RESPONSE = {
    "status": "ok",
    "asset_path": "/Game/Audio/TestSound",
    "asset_type": "Source",
    "is_preset": False,
    "interfaces": ["UE.Source.OneShot"],
    "graph_inputs": [
        {"name": "OnPlay", "type": "Trigger"},
        {"name": "Frequency", "type": "Float", "default": 440.0},
    ],
    "graph_outputs": [
        {"name": "Out Mono", "type": "Audio"},
        {"name": "OnFinished", "type": "Trigger"},
    ],
    "variables": [],
    "nodes": [
        {
            "node_id": "guid-input-onplay",
            "class_name": "OnPlay",
            "name": "OnPlay",
            "class_type": "Input",
            "x": -400, "y": 0,
            "inputs": [], "outputs": [{"name": "OnPlay", "type": "Trigger"}],
        },
        {
            "node_id": "guid-input-freq",
            "class_name": "Frequency",
            "name": "Frequency",
            "class_type": "Input",
            "x": -400, "y": 100,
            "inputs": [], "outputs": [{"name": "Frequency", "type": "Float"}],
        },
        {
            "node_id": "guid-output-mono",
            "class_name": "Out Mono",
            "name": "Out Mono",
            "class_type": "Output",
            "x": 400, "y": 0,
            "inputs": [{"name": "Out Mono", "type": "Audio"}], "outputs": [],
        },
        {
            "node_id": "guid-output-finished",
            "class_name": "OnFinished",
            "name": "OnFinished",
            "class_type": "Output",
            "x": 400, "y": 100,
            "inputs": [{"name": "OnFinished", "type": "Trigger"}], "outputs": [],
        },
        {
            "node_id": "guid-sine",
            "class_name": "UE::Sine::Audio",
            "name": "Sine",
            "class_type": "External",
            "x": 0, "y": 0,
            "inputs": [
                {"name": "Frequency", "type": "Float", "default": 440.0},
                {"name": "Enabled", "type": "Bool", "default": True},
            ],
            "outputs": [{"name": "Audio", "type": "Audio"}],
        },
        {
            "node_id": "guid-env",
            "class_name": "UE::AD Envelope::Audio",
            "name": "AD Envelope",
            "class_type": "External",
            "x": 0, "y": 200,
            "inputs": [
                {"name": "Trigger", "type": "Trigger"},
                {"name": "Attack", "type": "Float", "default": 0.01},
                {"name": "Decay", "type": "Float", "default": 0.1},
            ],
            "outputs": [
                {"name": "Envelope", "type": "Audio"},
                {"name": "OnDone", "type": "Trigger"},
            ],
        },
    ],
    "edges": [
        {"from_node": "guid-input-freq", "from_pin": "Frequency", "to_node": "guid-sine", "to_pin": "Frequency"},
        {"from_node": "guid-input-onplay", "from_pin": "OnPlay", "to_node": "guid-env", "to_pin": "Trigger"},
        {"from_node": "guid-sine", "from_pin": "Audio", "to_node": "guid-output-mono", "to_pin": "Out Mono"},
        {"from_node": "guid-env", "from_pin": "OnDone", "to_node": "guid-output-finished", "to_pin": "OnFinished"},
    ],
}


def test_export_graph_basic(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("export_metasound", MOCK_EXPORT_RESPONSE)
    result = json.loads(ms_export_graph("/Game/Audio/TestSound"))
    assert result["status"] == "ok"
    assert "6 nodes" in result["message"]
    assert "4 edges" in result["message"]
    assert result["export"]["asset_type"] == "Source"
    assert mock_ue5_plugin.commands[-1]["action"] == "export_metasound"


def test_export_graph_invalid_path(ue5_conn):
    result = json.loads(ms_export_graph("/tmp/bad"))
    assert result["status"] == "error"
    assert "/Game/" in result["message"]


def test_export_graph_traversal_path(ue5_conn):
    result = json.loads(ms_export_graph("/Game/../etc/passwd"))
    assert result["status"] == "error"
    assert ".." in result["message"]


def test_export_graph_not_connected():
    import ue_audio_mcp.ue5_connection as ue5_module
    ue5_module._connection = None
    result = json.loads(ms_export_graph("/Game/Audio/Test"))
    assert result["status"] == "error"
    assert "Not connected" in result["message"]
    ue5_module._connection = None


def test_export_graph_with_template(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("export_metasound", MOCK_EXPORT_RESPONSE)
    result = json.loads(ms_export_graph("/Game/Audio/TestSound", convert_to_template=True))
    assert result["status"] == "ok"
    assert "template" in result
    template = result["template"]
    assert template["name"] == "TestSound"
    assert template["asset_type"] == "Source"
    assert len(template["nodes"]) == 2  # only External nodes
    assert len(template["connections"]) == 4
    assert "template generated" in result["message"]


def test_export_graph_error_response(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("export_metasound", {
        "status": "error", "message": "Asset not found"
    })
    result = json.loads(ms_export_graph("/Game/Audio/Missing"))
    assert result["status"] == "error"
    assert "Asset not found" in result["message"]


# -- _inline_convert ---------------------------------------------------------

def test_inline_convert_basic():
    template = _inline_convert(MOCK_EXPORT_RESPONSE)
    assert template["name"] == "TestSound"
    assert template["asset_type"] == "Source"
    assert template["interfaces"] == ["UE.Source.OneShot"]
    assert len(template["inputs"]) == 2
    assert len(template["outputs"]) == 2
    assert len(template["nodes"]) == 2
    assert len(template["connections"]) == 4


def test_inline_convert_node_types():
    template = _inline_convert(MOCK_EXPORT_RESPONSE)
    node_types = {n["node_type"] for n in template["nodes"]}
    assert "Sine" in node_types
    # "AD Envelope" matches the base name in METASOUND_NODES before variant check
    assert "AD Envelope" in node_types or "AD Envelope (Audio)" in node_types


def test_inline_convert_graph_boundary():
    template = _inline_convert(MOCK_EXPORT_RESPONSE)
    # Input/Output nodes should become __graph__ in connections
    graph_from = [c for c in template["connections"] if c["from_node"] == "__graph__"]
    graph_to = [c for c in template["connections"] if c["to_node"] == "__graph__"]
    assert len(graph_from) == 2  # OnPlay and Frequency inputs
    assert len(graph_to) == 2    # Out Mono and OnFinished outputs


def test_inline_convert_defaults():
    template = _inline_convert(MOCK_EXPORT_RESPONSE)
    sine = [n for n in template["nodes"] if n["node_type"] == "Sine"][0]
    assert "defaults" in sine
    assert sine["defaults"]["Frequency"] == 440.0


def test_inline_convert_variables():
    export_with_vars = copy.deepcopy(MOCK_EXPORT_RESPONSE)
    export_with_vars["variables"] = [
        {"name": "TargetCutoff", "type": "Float", "default": 1000.0, "id": "var-guid"},
    ]
    template = _inline_convert(export_with_vars)
    assert "variables" in template
    assert len(template["variables"]) == 1
    assert template["variables"][0]["name"] == "TargetCutoff"
    assert template["variables"][0]["default"] == 1000.0
    assert "id" not in template["variables"][0]  # id should be stripped


def test_inline_convert_duplicate_node_names():
    """Two nodes with the same display name must get unique short IDs."""
    export = copy.deepcopy(MOCK_EXPORT_RESPONSE)
    # Add a second Sine node
    export["nodes"].append({
        "node_id": "guid-sine-2",
        "class_name": "UE::Sine::Audio",
        "name": "Sine",
        "class_type": "External",
        "x": 200, "y": 0,
        "inputs": [{"name": "Frequency", "type": "Float", "default": 880.0}],
        "outputs": [{"name": "Audio", "type": "Audio"}],
    })
    template = _inline_convert(export)
    node_ids = [n["id"] for n in template["nodes"]]
    # All IDs must be unique
    assert len(node_ids) == len(set(node_ids)), f"Duplicate IDs: {node_ids}"
    # Should have sine and sine_2
    assert "sine" in node_ids
    assert "sine_2" in node_ids


def test_inline_convert_empty_graph():
    """An export with zero external nodes should produce empty nodes/connections."""
    export = {
        "status": "ok",
        "asset_path": "/Game/Audio/Empty",
        "asset_type": "Source",
        "interfaces": [],
        "graph_inputs": [],
        "graph_outputs": [],
        "variables": [],
        "nodes": [],
        "edges": [],
    }
    template = _inline_convert(export)
    assert template["name"] == "Empty"
    assert template["nodes"] == []
    assert template["connections"] == []


def test_inline_convert_dotted_asset_path():
    """Asset paths like /Game/Audio/MySound.MySound should extract 'MySound'."""
    export = copy.deepcopy(MOCK_EXPORT_RESPONSE)
    export["asset_path"] = "/Game/Audio/MySound.MySound"
    template = _inline_convert(export)
    assert template["name"] == "MySound"


def test_inline_convert_variable_class_types():
    """VariableAccessor/Mutator nodes should map to sentinel node types."""
    export = copy.deepcopy(MOCK_EXPORT_RESPONSE)
    export["nodes"].append({
        "node_id": "guid-var-get",
        "class_name": "TargetCutoff",
        "name": "TargetCutoff",
        "class_type": "VariableAccessor",
        "x": 0, "y": 300,
        "inputs": [], "outputs": [{"name": "TargetCutoff", "type": "Float"}],
    })
    export["nodes"].append({
        "node_id": "guid-var-set",
        "class_name": "TargetCutoff",
        "name": "TargetCutoff",
        "class_type": "VariableMutator",
        "x": 0, "y": 400,
        "inputs": [{"name": "TargetCutoff", "type": "Float"}], "outputs": [],
    })
    template = _inline_convert(export)
    types = {n["node_type"] for n in template["nodes"]}
    assert "__variable_get__" in types
    assert "__variable_set__" in types


# -- CLASS_NAME_TO_DISPLAY shared dict tests ---------------------------------

def test_class_name_to_display_exact():
    """Exact dict lookups should work for all entries."""
    assert class_name_to_display("UE::Sine::Audio") == "Sine"
    assert class_name_to_display("UE::AD Envelope::Audio") == "AD Envelope (Audio)"
    assert class_name_to_display("AudioMixer::Audio Mixer (Mono, 2)::None") == "Audio Mixer (Mono, 2)"
    assert class_name_to_display("Convert::Float::Int32") == "Float To Int"
    assert class_name_to_display("Convert::Int32::Float") == "Int To Float"


def test_class_name_to_display_fuzzy():
    """Fuzzy fallback should match by Name part from METASOUND_NODES."""
    # "Compressor" is registered — fuzzy via name_part
    assert class_name_to_display("SomeNamespace::Compressor::SomeVariant") == "Compressor"


def test_class_name_to_display_case_insensitive():
    """Case-insensitive fallback for nodes not in explicit dict."""
    # "BPM To Seconds" is registered — try case-insensitive
    result = class_name_to_display("CustomNS::bpm to seconds::None")
    assert result == "BPM To Seconds"


def test_class_name_to_display_unknown():
    """Unknown class names should return None."""
    assert class_name_to_display("Unknown::NotANode::None") is None
    assert class_name_to_display("") is None


# -- infer_class_type tests --------------------------------------------------

def test_infer_class_type_input():
    assert infer_class_type("Input::OnPlay") == "Input"


def test_infer_class_type_output():
    assert infer_class_type("Output::OutMono") == "Output"


def test_infer_class_type_variable_accessor():
    assert infer_class_type("VariableAccessor::MyCutoff") == "VariableAccessor"


def test_infer_class_type_variable_mutator():
    assert infer_class_type("VariableMutator::MyCutoff") == "VariableMutator"


def test_infer_class_type_external():
    assert infer_class_type("UE::Sine::Audio") == "External"
    assert infer_class_type("") == "External"


# -- _inline_convert with inferred class_type --------------------------------

def test_inline_convert_infer_class_type_from_class_name():
    """When class_type is missing, it should be inferred from class_name prefix."""
    export = {
        "status": "ok",
        "asset_path": "/Game/Audio/InferTest",
        "asset_type": "Source",
        "interfaces": [],
        "graph_inputs": [],
        "graph_outputs": [],
        "variables": [],
        "nodes": [
            {
                "node_id": "guid-input-play",
                "class_name": "Input::OnPlay",
                "name": "OnPlay",
                # No class_type field — should be inferred as "Input"
                "x": -400, "y": 0,
                "inputs": [], "outputs": [{"name": "OnPlay", "type": "Trigger"}],
            },
            {
                "node_id": "guid-output-mono",
                "class_name": "Output::OutMono",
                "name": "Out Mono",
                # No class_type field — should be inferred as "Output"
                "x": 400, "y": 0,
                "inputs": [{"name": "Out Mono", "type": "Audio"}], "outputs": [],
            },
            {
                "node_id": "guid-sine",
                "class_name": "UE::Sine::Audio",
                "name": "Sine",
                # No class_type field — should be inferred as "External"
                "x": 0, "y": 0,
                "inputs": [{"name": "Frequency", "type": "Float", "default": 440.0}],
                "outputs": [{"name": "Audio", "type": "Audio"}],
            },
        ],
        "edges": [
            {"from_node": "guid-sine", "from_pin": "Audio", "to_node": "guid-output-mono", "to_pin": "Out Mono"},
        ],
    }
    template = _inline_convert(export)
    assert template["name"] == "InferTest"
    # Only the Sine node should be in nodes (Input/Output become __graph__)
    assert len(template["nodes"]) == 1
    assert template["nodes"][0]["node_type"] == "Sine"
    # Edge should use __graph__ for the output node
    assert len(template["connections"]) == 1
    assert template["connections"][0]["to_node"] == "__graph__"


def test_inline_convert_class_name_dict_resolves_audio_mixer():
    """AudioMixer namespace nodes should resolve via CLASS_NAME_TO_DISPLAY."""
    export = copy.deepcopy(MOCK_EXPORT_RESPONSE)
    export["nodes"].append({
        "node_id": "guid-mixer",
        "class_name": "AudioMixer::Audio Mixer (Mono, 2)::None",
        "name": "Audio Mixer (Mono, 2)",
        "class_type": "External",
        "x": 100, "y": 100,
        "inputs": [{"name": "In 0", "type": "Audio"}],
        "outputs": [{"name": "Out", "type": "Audio"}],
    })
    template = _inline_convert(export)
    mixer_nodes = [n for n in template["nodes"] if "Audio Mixer" in n["node_type"]]
    assert len(mixer_nodes) == 1
    assert mixer_nodes[0]["node_type"] == "Audio Mixer (Mono, 2)"


def test_inline_convert_skip_init_variable_nodes():
    """InitVariable (class_type=Variable) nodes should be skipped entirely."""
    export = copy.deepcopy(MOCK_EXPORT_RESPONSE)
    export["nodes"].append({
        "node_id": "guid-initvar",
        "class_name": "InitVariable::MyCutoff",
        "name": "MyCutoff",
        "class_type": "Variable",
        "x": 0, "y": 500,
        "inputs": [], "outputs": [],
    })
    # Add an edge from initvar to sine (should be skipped)
    export["edges"].append({
        "from_node": "guid-initvar", "from_pin": "Value",
        "to_node": "guid-sine", "to_pin": "Frequency",
    })
    template = _inline_convert(export)
    # InitVariable should not appear in nodes
    node_types = {n["node_type"] for n in template["nodes"]}
    assert "InitVariable::MyCutoff" not in node_types
    # Edge involving __skip__ should be dropped
    skip_edges = [c for c in template["connections"]
                  if "initvar" in c.get("from_node", "") or "initvar" in c.get("to_node", "")]
    assert len(skip_edges) == 0


# -- bp_export_audio tests ---------------------------------------------------

def test_bp_export_audio(ue5_conn, mock_ue5_plugin):
    from ue_audio_mcp.tools.blueprints import bp_export_audio
    mock_ue5_plugin.set_response("export_audio_blueprint", {
        "status": "ok",
        "asset_path": "/Game/Blueprints/BP_Test",
        "blueprint_name": "BP_Test",
        "audio_nodes": 3,
        "total_nodes": 7,
        "nodes": [],
        "edges": [],
    })
    result = json.loads(bp_export_audio("/Game/Blueprints/BP_Test"))
    assert result["status"] == "ok"
    assert result["blueprint_name"] == "BP_Test"
    assert mock_ue5_plugin.commands[-1]["action"] == "export_audio_blueprint"


def test_bp_export_audio_empty_path(ue5_conn):
    from ue_audio_mcp.tools.blueprints import bp_export_audio
    result = json.loads(bp_export_audio(""))
    assert result["status"] == "error"
    assert "empty" in result["message"]


def test_bp_export_audio_not_connected():
    import ue_audio_mcp.ue5_connection as ue5_module
    from ue_audio_mcp.tools.blueprints import bp_export_audio
    ue5_module._connection = None
    result = json.loads(bp_export_audio("/Game/Blueprints/BP_Test"))
    assert result["status"] == "error"
    assert "Not connected" in result["message"]
    ue5_module._connection = None
