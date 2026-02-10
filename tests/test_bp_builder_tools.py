"""Tests for Blueprint Builder tools — bp_open_blueprint, bp_add_bp_node, etc."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.bp_builder import (
    bp_open_blueprint,
    bp_add_bp_node,
    bp_connect_bp_pins,
    bp_set_bp_pin,
    bp_compile_blueprint,
    bp_register_existing,
    bp_list_node_pins,
    bp_wire_audio_param,
)


# -- bp_open_blueprint -------------------------------------------------------

def test_open_blueprint_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("bp_open_blueprint", {
        "status": "ok",
        "blueprint_name": "BP_Character",
    })
    result = json.loads(bp_open_blueprint("/Game/Blueprints/BP_Character"))
    assert result["status"] == "ok"
    assert result["blueprint_name"] == "BP_Character"


def test_open_blueprint_empty_path(ue5_conn):
    result = json.loads(bp_open_blueprint(""))
    assert result["status"] == "error"
    assert "empty" in result["message"]


def test_open_blueprint_path_traversal(ue5_conn):
    result = json.loads(bp_open_blueprint("/Game/../../../etc/passwd"))
    assert result["status"] == "error"
    assert ".." in result["message"]


def test_open_blueprint_not_found(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("bp_open_blueprint", {
        "status": "error",
        "message": "Could not load Blueprint at '/Game/NoExist'",
    })
    result = json.loads(bp_open_blueprint("/Game/NoExist"))
    assert result["status"] == "error"
    assert "Could not load" in result["message"]


def test_open_blueprint_not_connected():
    import ue_audio_mcp.ue5_connection as ue5_module
    ue5_module._connection = None
    result = json.loads(bp_open_blueprint("/Game/BP_Test"))
    assert result["status"] == "error"
    assert "Not connected" in result["message"]
    ue5_module._connection = None


# -- bp_add_bp_node ----------------------------------------------------------

def test_add_call_function_node(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("bp_add_node", {
        "status": "ok", "id": "set_param", "node_kind": "CallFunction",
    })
    result = json.loads(bp_add_bp_node(
        node_id="set_param",
        node_kind="CallFunction",
        function_name="SetFloatParameter",
        position_x=100, position_y=200,
    ))
    assert result["status"] == "ok"
    assert result["id"] == "set_param"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "bp_add_node"
    assert cmd["function_name"] == "SetFloatParameter"
    assert cmd["position"] == [100, 200]


def test_add_custom_event_node(ue5_conn, mock_ue5_plugin):
    result = json.loads(bp_add_bp_node(
        node_id="my_event",
        node_kind="CustomEvent",
        event_name="OnAudioTrigger",
    ))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["event_name"] == "OnAudioTrigger"


def test_add_variable_get_node(ue5_conn, mock_ue5_plugin):
    result = json.loads(bp_add_bp_node(
        node_id="get_speed",
        node_kind="VariableGet",
        variable_name="Speed",
    ))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["variable_name"] == "Speed"


def test_add_variable_set_node(ue5_conn, mock_ue5_plugin):
    result = json.loads(bp_add_bp_node(
        node_id="set_speed",
        node_kind="VariableSet",
        variable_name="Speed",
    ))
    assert result["status"] == "ok"


def test_add_node_invalid_kind(ue5_conn):
    result = json.loads(bp_add_bp_node(
        node_id="test", node_kind="InvalidKind",
    ))
    assert result["status"] == "error"
    assert "Invalid node_kind" in result["message"]


def test_add_node_empty_id(ue5_conn):
    result = json.loads(bp_add_bp_node(
        node_id="", node_kind="CallFunction", function_name="Play",
    ))
    assert result["status"] == "error"
    assert "empty" in result["message"]


def test_add_call_function_missing_name(ue5_conn):
    result = json.loads(bp_add_bp_node(
        node_id="test", node_kind="CallFunction",
    ))
    assert result["status"] == "error"
    assert "function_name" in result["message"]


def test_add_custom_event_missing_name(ue5_conn):
    result = json.loads(bp_add_bp_node(
        node_id="test", node_kind="CustomEvent",
    ))
    assert result["status"] == "error"
    assert "event_name" in result["message"]


def test_add_variable_get_missing_name(ue5_conn):
    result = json.loads(bp_add_bp_node(
        node_id="test", node_kind="VariableGet",
    ))
    assert result["status"] == "error"
    assert "variable_name" in result["message"]


def test_add_node_disallowed_function(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("bp_add_node", {
        "status": "error",
        "message": "Function 'DestroyActor' is not in the audio allowlist",
    })
    result = json.loads(bp_add_bp_node(
        node_id="bad", node_kind="CallFunction",
        function_name="DestroyActor",
    ))
    assert result["status"] == "error"
    assert "allowlist" in result["message"]


# -- bp_connect_bp_pins ------------------------------------------------------

def test_connect_pins_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("bp_connect_pins", {
        "status": "ok",
        "connection": "tick.then -> set_param.execute",
    })
    result = json.loads(bp_connect_bp_pins("tick", "then", "set_param", "execute"))
    assert result["status"] == "ok"
    assert "tick.then" in result["connection"]


def test_connect_pins_unknown_node(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("bp_connect_pins", {
        "status": "error",
        "message": "Unknown node 'nonexistent' — register it first",
    })
    result = json.loads(bp_connect_bp_pins("nonexistent", "out", "also_gone", "in"))
    assert result["status"] == "error"
    assert "Unknown node" in result["message"]


def test_connect_pins_empty_params(ue5_conn):
    result = json.loads(bp_connect_bp_pins("", "out", "node2", "in"))
    assert result["status"] == "error"


# -- bp_set_bp_pin -----------------------------------------------------------

def test_set_pin_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("bp_set_pin_default", {
        "status": "ok", "node_id": "set_param",
        "pin_name": "InName", "value": "Speed",
    })
    result = json.loads(bp_set_bp_pin("set_param", "InName", "Speed"))
    assert result["status"] == "ok"
    assert result["value"] == "Speed"


def test_set_pin_empty_node(ue5_conn):
    result = json.loads(bp_set_bp_pin("", "InName", "val"))
    assert result["status"] == "error"


def test_set_pin_empty_pin_name(ue5_conn):
    result = json.loads(bp_set_bp_pin("node", "", "val"))
    assert result["status"] == "error"


def test_set_pin_unknown_node(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("bp_set_pin_default", {
        "status": "error", "message": "Unknown node 'nope'",
    })
    result = json.loads(bp_set_bp_pin("nope", "InName", "val"))
    assert result["status"] == "error"


# -- bp_compile_blueprint ----------------------------------------------------

def test_compile_success(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("bp_compile", {
        "status": "ok", "compile_result": "success", "messages": [],
    })
    result = json.loads(bp_compile_blueprint())
    assert result["status"] == "ok"
    assert result["compile_result"] == "success"


def test_compile_no_active_bp(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("bp_compile", {
        "status": "error",
        "message": "No active Blueprint — call bp_open_blueprint first",
    })
    result = json.loads(bp_compile_blueprint())
    assert result["status"] == "error"
    assert "No active Blueprint" in result["message"]


# -- bp_register_existing ----------------------------------------------------

def test_register_existing_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("bp_register_existing_node", {
        "status": "ok", "id": "tick",
        "node_class": "K2Node_Event", "title": "Event Tick",
    })
    result = json.loads(bp_register_existing("tick", "ABCD1234-5678-90AB-CDEF-1234567890AB"))
    assert result["status"] == "ok"
    assert result["id"] == "tick"
    assert result["node_class"] == "K2Node_Event"


def test_register_existing_invalid_guid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("bp_register_existing_node", {
        "status": "error", "message": "Invalid GUID format: 'not-a-guid'",
    })
    result = json.loads(bp_register_existing("test", "not-a-guid"))
    assert result["status"] == "error"
    assert "GUID" in result["message"]


def test_register_existing_empty_id(ue5_conn):
    result = json.loads(bp_register_existing("", "some-guid"))
    assert result["status"] == "error"
    assert "empty" in result["message"]


def test_register_existing_empty_guid(ue5_conn):
    result = json.loads(bp_register_existing("test", ""))
    assert result["status"] == "error"
    assert "empty" in result["message"]


# -- bp_list_node_pins -------------------------------------------------------

def test_list_pins_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("bp_list_pins", {
        "status": "ok", "node_id": "set_param", "pin_count": 3,
        "pins": [
            {"name": "execute", "direction": "input", "type": "exec"},
            {"name": "Target", "direction": "input", "type": "object"},
            {"name": "then", "direction": "output", "type": "exec"},
        ],
    })
    result = json.loads(bp_list_node_pins("set_param"))
    assert result["status"] == "ok"
    assert result["pin_count"] == 3
    assert len(result["pins"]) == 3


def test_list_pins_empty_id(ue5_conn):
    result = json.loads(bp_list_node_pins(""))
    assert result["status"] == "error"


# -- bp_wire_audio_param (high-level) ----------------------------------------

def test_wire_audio_param_full(ue5_conn, mock_ue5_plugin):
    """Full pipeline: open -> register source -> add node -> set pin -> connect -> compile."""
    mock_ue5_plugin.set_response("bp_open_blueprint", {
        "status": "ok", "blueprint_name": "BP_Character",
    })
    mock_ue5_plugin.set_response("bp_register_existing_node", {
        "status": "ok", "id": "_source",
    })
    mock_ue5_plugin.set_response("bp_add_node", {
        "status": "ok", "id": "_set_param",
    })
    mock_ue5_plugin.set_response("bp_set_pin_default", {
        "status": "ok",
    })
    mock_ue5_plugin.set_response("bp_connect_pins", {
        "status": "ok",
    })
    mock_ue5_plugin.set_response("bp_compile", {
        "status": "ok", "compile_result": "success",
    })

    result = json.loads(bp_wire_audio_param(
        asset_path="/Game/BP_Character",
        param_name="Speed",
        source_node_guid="ABCD-1234",
        source_pin="ReturnValue",
    ))
    assert result["status"] == "ok"
    assert "Speed" in result["message"]
    assert "opened" in result["steps"]
    assert "registered_source" in result["steps"]
    assert "added_set_float_parameter" in result["steps"]
    assert "set_param_name" in result["steps"]
    assert "connected_source" in result["steps"]
    assert "compiled" in result["steps"]

    # Verify command sequence
    actions = [c["action"] for c in mock_ue5_plugin.commands]
    assert actions == [
        "bp_open_blueprint",
        "bp_register_existing_node",
        "bp_add_node",
        "bp_set_pin_default",
        "bp_connect_pins",
        "bp_compile",
    ]


def test_wire_audio_param_no_source(ue5_conn, mock_ue5_plugin):
    """Without source node: open -> add -> set pin -> compile (no register/connect)."""
    mock_ue5_plugin.set_response("bp_open_blueprint", {"status": "ok"})
    mock_ue5_plugin.set_response("bp_add_node", {"status": "ok"})
    mock_ue5_plugin.set_response("bp_set_pin_default", {"status": "ok"})
    mock_ue5_plugin.set_response("bp_compile", {
        "status": "ok", "compile_result": "success",
    })

    result = json.loads(bp_wire_audio_param(
        asset_path="/Game/BP_Test",
        param_name="Volume",
    ))
    assert result["status"] == "ok"
    actions = [c["action"] for c in mock_ue5_plugin.commands]
    assert "bp_register_existing_node" not in actions
    assert "bp_connect_pins" not in actions


def test_wire_audio_param_empty_path(ue5_conn):
    result = json.loads(bp_wire_audio_param(asset_path="", param_name="Speed"))
    assert result["status"] == "error"
    assert "empty" in result["message"]


def test_wire_audio_param_empty_param(ue5_conn):
    result = json.loads(bp_wire_audio_param(asset_path="/Game/BP_Test", param_name=""))
    assert result["status"] == "error"
    assert "empty" in result["message"]


def test_wire_audio_param_open_fails(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("bp_open_blueprint", {
        "status": "error", "message": "Not found",
    })
    result = json.loads(bp_wire_audio_param(
        asset_path="/Game/NoExist", param_name="Speed",
    ))
    assert result["status"] == "error"
    assert "Open failed" in result["message"]
