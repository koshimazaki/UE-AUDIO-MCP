"""Tests for UE5PluginConnection singleton."""

from __future__ import annotations

import pytest

import ue_audio_mcp.ue5_connection as ue5_module
from ue_audio_mcp.ue5_connection import UE5PluginConnection, get_ue5_connection


def test_singleton_returns_same_instance():
    ue5_module._connection = None
    a = get_ue5_connection()
    b = get_ue5_connection()
    assert a is b
    ue5_module._connection = None


def test_connect_failure():
    """Connecting to a non-existent server raises ConnectionError."""
    conn = UE5PluginConnection()
    with pytest.raises(ConnectionError, match="Cannot connect"):
        conn.connect("127.0.0.1", 19999)


def test_disconnect(ue5_conn):
    ue5_conn.disconnect()
    assert ue5_conn._sock is None
    assert ue5_conn.is_connected() is False


def test_is_connected_true(ue5_conn):
    assert ue5_conn.is_connected() is True


def test_is_connected_false_when_no_socket():
    conn = UE5PluginConnection()
    assert conn.is_connected() is False


def test_send_command(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("get_info", {"engine": "UE5", "version": "5.4"})
    result = ue5_conn.send_command({"action": "get_info"})
    assert result["engine"] == "UE5"
    assert mock_ue5_plugin.commands[-1]["action"] == "get_info"


def test_send_command_not_connected():
    conn = UE5PluginConnection()
    with pytest.raises(RuntimeError, match="Not connected"):
        conn.send_command({"action": "ping"})
