"""Tests for graph variable tools."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.variables import ms_add_variable, ms_add_variable_node


def _parse(result: str) -> dict:
    return json.loads(result)


class TestAddVariable:
    """ms_add_variable tool tests."""

    def test_add_variable_online(self, ue5_conn, mock_ue5_plugin):
        result = _parse(ms_add_variable("Health", "Float", "100.0"))
        assert result["status"] == "ok"
        assert "Health" in result["message"]
        assert mock_ue5_plugin.commands[-1]["action"] == "add_graph_variable"

    def test_add_variable_invalid_type(self, ue5_conn, mock_ue5_plugin):
        result = _parse(ms_add_variable("X", "InvalidType"))
        assert result["status"] == "error"
        assert "Invalid type" in result["message"]

    def test_add_variable_offline(self):
        """Offline — should raise since UE5 not connected."""
        result = _parse(ms_add_variable("Var1", "Float"))
        assert result["status"] == "error"


class TestAddVariableNode:
    """ms_add_variable_node tool tests."""

    def test_get_node_online(self, ue5_conn, mock_ue5_plugin):
        result = _parse(ms_add_variable_node("get1", "Health", "get"))
        assert result["status"] == "ok"
        assert "get" in result["message"]
        cmd = mock_ue5_plugin.commands[-1]
        assert cmd["action"] == "add_variable_get_node"
        assert cmd["variable_name"] == "Health"
        assert cmd.get("delayed") is False

    def test_set_node_online(self, ue5_conn, mock_ue5_plugin):
        result = _parse(ms_add_variable_node("set1", "Health", "set"))
        assert result["status"] == "ok"
        cmd = mock_ue5_plugin.commands[-1]
        assert cmd["action"] == "add_variable_set_node"

    def test_delayed_get_node_online(self, ue5_conn, mock_ue5_plugin):
        result = _parse(ms_add_variable_node("getd1", "Prev", "get_delayed"))
        assert result["status"] == "ok"
        cmd = mock_ue5_plugin.commands[-1]
        assert cmd["action"] == "add_variable_get_node"
        assert cmd["delayed"] is True

    def test_invalid_mode(self, ue5_conn, mock_ue5_plugin):
        result = _parse(ms_add_variable_node("x", "Var", "invalid"))
        assert result["status"] == "error"
        assert "Invalid mode" in result["message"]

    def test_offline(self):
        """Offline — should raise since UE5 not connected."""
        result = _parse(ms_add_variable_node("n1", "Var", "get"))
        assert result["status"] == "error"
