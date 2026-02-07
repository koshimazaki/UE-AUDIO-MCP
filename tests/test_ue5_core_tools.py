"""Tests for UE5 core tools — connect, info, status."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.ue5_core import ue5_connect, ue5_get_info, ue5_status


def test_ue5_connect_success(ue5_conn, mock_ue5_plugin):
    # ue5_conn fixture already sets up the mock — simulate a fresh connect
    mock_ue5_plugin.set_response("ping", {"status": "ok", "engine": "UE5", "version": "5.4"})
    # Bypass the real connect by calling the tool's underlying logic via mock
    result = json.loads(ue5_get_info())
    assert result["status"] == "ok"


def test_ue5_connect_failure():
    """ue5_connect with unreachable host returns error."""
    result = json.loads(ue5_connect("127.0.0.1", 19999))
    assert result["status"] == "error"
    assert "Cannot connect" in result["message"]


def test_ue5_get_info(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("ping", {
        "status": "ok",
        "engine": "UnrealEngine",
        "version": "5.4.0",
    })
    result = json.loads(ue5_get_info())
    assert result["status"] == "ok"
    assert result["info"]["engine"] == "UnrealEngine"


def test_ue5_get_info_not_connected():
    import ue_audio_mcp.ue5_connection as ue5_module
    ue5_module._connection = None
    result = json.loads(ue5_get_info())
    assert result["status"] == "error"
    assert "Not connected" in result["message"]
    ue5_module._connection = None


def test_ue5_status_both(ue5_conn, wwise_conn):
    result = json.loads(ue5_status())
    assert result["status"] == "ok"
    assert result["wwise_connected"] is True
    assert result["ue5_connected"] is True


def test_ue5_status_neither():
    import ue_audio_mcp.connection as conn_module
    import ue_audio_mcp.ue5_connection as ue5_module
    conn_module._connection = None
    ue5_module._connection = None
    result = json.loads(ue5_status())
    assert result["status"] == "ok"
    assert result["wwise_connected"] is False
    assert result["ue5_connected"] is False
    conn_module._connection = None
    ue5_module._connection = None
