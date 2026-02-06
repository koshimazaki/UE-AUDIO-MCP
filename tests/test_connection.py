"""Tests for WwiseConnection singleton."""

from __future__ import annotations

import ue_audio_mcp.connection as conn_module
from ue_audio_mcp.connection import WwiseConnection, get_wwise_connection


def test_singleton_returns_same_instance():
    conn_module._connection = None
    a = get_wwise_connection()
    b = get_wwise_connection()
    assert a is b
    conn_module._connection = None


def test_is_connected_with_mock(wwise_conn):
    assert wwise_conn.is_connected() is True


def test_is_connected_false_when_no_client():
    conn = WwiseConnection()
    assert conn.is_connected() is False


def test_disconnect(wwise_conn):
    wwise_conn.disconnect()
    assert wwise_conn.client is None
    assert wwise_conn.is_connected() is False


def test_call_forwards_to_client(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.object.get", {"return": [{"id": "abc"}]})
    result = wwise_conn.call(
        "ak.wwise.core.object.get",
        args={"waql": "$ from type sound"},
        options={"return": ["id"]},
    )
    assert result == {"return": [{"id": "abc"}]}
    assert mock_waapi.calls[-1][0] == "ak.wwise.core.object.get"


def test_call_raises_when_disconnected():
    conn = WwiseConnection()
    try:
        conn.call("ak.wwise.core.getInfo")
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "Not connected" in str(e)
