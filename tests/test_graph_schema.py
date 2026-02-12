"""Tests for graph spec validation and builder command generation."""

from __future__ import annotations

from ue_audio_mcp.knowledge.graph_schema import (
    validate_graph,
    graph_to_builder_commands,
    GRAPH_SPEC_FIELDS,
    GRAPH_BOUNDARY,
    VARIABLE_GET_TYPE,
    VARIABLE_SET_TYPE,
    VARIABLE_GET_DELAYED_TYPE,
)


def _valid_spec():
    """Return a minimal valid graph spec."""
    return {
        "name": "TestSound",
        "asset_type": "Source",
        "interfaces": ["UE.Source.OneShot"],
        "inputs": [{"name": "OnPlay", "type": "Trigger"}],
        "outputs": [
            {"name": "Out Mono", "type": "Audio"},
            {"name": "Out Stereo L", "type": "Audio"},
            {"name": "Out Stereo R", "type": "Audio"},
            {"name": "OnFinished", "type": "Trigger"},
        ],
        "nodes": [
            {"id": "sine1", "node_type": "Sine", "defaults": {"Frequency": 440.0}, "position": [100, 100]},
        ],
        "connections": [
            {"from_node": "sine1", "from_pin": "Audio", "to_node": "__graph__", "to_pin": "Out Mono"},
        ],
    }


def test_valid_graph():
    errors = validate_graph(_valid_spec())
    assert errors == []


def test_missing_required_fields():
    errors = validate_graph({"name": "X"})
    assert any("Missing" in e for e in errors)


def test_invalid_asset_type():
    spec = _valid_spec()
    spec["asset_type"] = "BadType"
    errors = validate_graph(spec)
    assert any("BadType" in e for e in errors)


def test_unknown_node_type():
    spec = _valid_spec()
    spec["nodes"] = [{"id": "x", "node_type": "FakeNode", "defaults": {}, "position": [0, 0]}]
    spec["connections"] = []
    errors = validate_graph(spec)
    assert any("FakeNode" in e for e in errors)


def test_duplicate_node_ids():
    spec = _valid_spec()
    spec["nodes"] = [
        {"id": "dup", "node_type": "Sine", "defaults": {}, "position": [0, 0]},
        {"id": "dup", "node_type": "Sine", "defaults": {}, "position": [100, 0]},
    ]
    spec["connections"] = []
    errors = validate_graph(spec)
    assert any("Duplicate" in e for e in errors)


def test_type_mismatch():
    spec = _valid_spec()
    spec["nodes"] = [
        {"id": "sine1", "node_type": "Sine", "defaults": {}, "position": [0, 0]},
        {"id": "log1", "node_type": "Print Log", "defaults": {}, "position": [200, 0]},
    ]
    spec["connections"] = [
        {"from_node": "sine1", "from_pin": "Audio", "to_node": "log1", "to_pin": "Label"},
    ]
    errors = validate_graph(spec)
    assert any("Type mismatch" in e for e in errors)


def test_nonexistent_connection_target():
    spec = _valid_spec()
    spec["connections"] = [
        {"from_node": "sine1", "from_pin": "Audio", "to_node": "ghost", "to_pin": "Audio"},
    ]
    errors = validate_graph(spec)
    assert any("ghost" in e for e in errors)


def test_unknown_interface():
    spec = _valid_spec()
    spec["interfaces"] = ["UE.Source.NonExistent"]
    errors = validate_graph(spec)
    assert any("NonExistent" in e for e in errors)


def test_graph_boundary_wiring():
    spec = {
        "name": "PatchTest",
        "asset_type": "Patch",
        "interfaces": [],
        "inputs": [{"name": "Freq", "type": "Float"}],
        "outputs": [{"name": "Out", "type": "Audio"}],
        "nodes": [
            {"id": "s1", "node_type": "Sine", "defaults": {}, "position": [0, 0]},
        ],
        "connections": [
            {"from_node": "__graph__", "from_pin": "Freq", "to_node": "s1", "to_pin": "Frequency"},
            {"from_node": "s1", "from_pin": "Audio", "to_node": "__graph__", "to_pin": "Out"},
        ],
    }
    errors = validate_graph(spec)
    assert errors == []


def test_builder_commands_order():
    spec = _valid_spec()
    cmds = graph_to_builder_commands(spec)
    actions = [c["action"] for c in cmds]
    assert actions[0] == "create_builder"
    assert actions[-1] == "build_to_asset"
    assert "add_interface" in actions
    assert "add_node" in actions
    assert "connect" in actions


def test_builder_commands_set_default():
    spec = _valid_spec()
    cmds = graph_to_builder_commands(spec)
    defaults = [c for c in cmds if c["action"] == "set_default"]
    assert len(defaults) == 1
    assert defaults[0]["input"] == "Frequency"
    assert defaults[0]["value"] == 440.0


def test_graph_spec_fields_constant():
    assert GRAPH_SPEC_FIELDS == {"name", "asset_type", "nodes", "connections"}


def test_graph_boundary_constant():
    assert GRAPH_BOUNDARY == "__graph__"


# ---------------------------------------------------------------------------
# Variable support
# ---------------------------------------------------------------------------

def _var_spec():
    """Return a graph spec with variables and variable nodes."""
    return {
        "name": "VarTest",
        "asset_type": "Patch",
        "interfaces": [],
        "variables": [
            {"name": "Health", "type": "Float", "default": 100.0},
        ],
        "inputs": [{"name": "Trigger", "type": "Trigger"}],
        "outputs": [{"name": "Out", "type": "Float"}],
        "nodes": [
            {"id": "get_health", "node_type": "__variable_get__", "variable_name": "Health", "position": [0, 0], "defaults": {}},
            {"id": "set_health", "node_type": "__variable_set__", "variable_name": "Health", "position": [0, 200], "defaults": {}},
        ],
        "connections": [
            {"from_node": "get_health", "from_pin": "Value", "to_node": "__graph__", "to_pin": "Out"},
            {"from_node": "__graph__", "from_pin": "Trigger", "to_node": "set_health", "to_pin": "Execute"},
        ],
    }


def test_variable_spec_valid():
    errors = validate_graph(_var_spec())
    assert errors == []


def test_variable_duplicate_name():
    spec = _var_spec()
    spec["variables"].append({"name": "Health", "type": "Int32"})
    errors = validate_graph(spec)
    assert any("Duplicate variable" in e for e in errors)


def test_variable_invalid_type():
    spec = _var_spec()
    spec["variables"] = [{"name": "X", "type": "FakeType"}]
    spec["nodes"] = []
    spec["connections"] = []
    errors = validate_graph(spec)
    assert any("invalid type" in e for e in errors)


def test_variable_node_undeclared():
    spec = _var_spec()
    spec["variables"] = []  # remove declaration
    errors = validate_graph(spec)
    assert any("undeclared variable" in e for e in errors)


def test_variable_commands_emitted():
    spec = _var_spec()
    cmds = graph_to_builder_commands(spec)
    actions = [c["action"] for c in cmds]
    assert "add_graph_variable" in actions
    assert "add_variable_get_node" in actions
    assert "add_variable_set_node" in actions
    # Variable commands should appear before graph I/O but after interfaces
    var_idx = actions.index("add_graph_variable")
    assert var_idx > 0  # after create_builder
    get_idx = actions.index("add_variable_get_node")
    set_idx = actions.index("add_variable_set_node")
    assert get_idx > var_idx
    assert set_idx > var_idx


def test_variable_no_set_default_for_variable_nodes():
    spec = _var_spec()
    cmds = graph_to_builder_commands(spec)
    set_defaults = [c for c in cmds if c["action"] == "set_default"]
    var_node_ids = {"get_health", "set_health"}
    for sd in set_defaults:
        assert sd["node_id"] not in var_node_ids
