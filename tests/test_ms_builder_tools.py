"""Tests for MetaSounds Builder tools — ms_build_graph, ms_create_source, etc."""

from __future__ import annotations

import json
import os

from ue_audio_mcp.tools.ms_builder import (
    ms_add_node,
    ms_audition,
    ms_build_graph,
    ms_connect_pins,
    ms_create_source,
    ms_save_asset,
    ms_set_default,
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
