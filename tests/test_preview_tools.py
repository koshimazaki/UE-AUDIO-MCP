"""Tests for preview tools — transport and soundbank generation."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.preview import wwise_generate_banks, wwise_preview


def _parse(result: str) -> dict:
    return json.loads(result)


def test_preview_play(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.transport.create", {"transport": 42})
    mock_waapi.set_response("ak.wwise.core.transport.executeAction", None)
    result = _parse(wwise_preview("\\Events\\Default Work Unit\\Play_Gunshot"))
    assert result["status"] == "ok"
    assert result["action"] == "play"
    assert result["transport_id"] == 42


def test_preview_stop_filtered(wwise_conn, mock_waapi):
    """Stop only transports matching the given object_path."""
    path = "\\Events\\Default Work Unit\\Play_Gunshot"
    mock_waapi.set_response("ak.wwise.core.transport.getList", {
        "list": [
            {"transport": 42, "object": path},
            {"transport": 43, "object": "\\Events\\Default Work Unit\\Other"},
        ],
    })
    mock_waapi.set_response("ak.wwise.core.transport.executeAction", None)
    mock_waapi.set_response("ak.wwise.core.transport.destroy", None)
    result = _parse(wwise_preview(path, "stop"))
    assert result["status"] == "ok"
    assert result["transports_stopped"] == 1  # only matching transport


def test_preview_stop_all(wwise_conn, mock_waapi):
    """Stop with empty object_path stops all transports."""
    mock_waapi.set_response("ak.wwise.core.transport.getList", {
        "list": [{"transport": 42}, {"transport": 43}],
    })
    mock_waapi.set_response("ak.wwise.core.transport.executeAction", None)
    mock_waapi.set_response("ak.wwise.core.transport.destroy", None)
    result = _parse(wwise_preview("", "stop"))
    assert result["status"] == "ok"
    assert result["transports_stopped"] == 2


def test_preview_invalid_action(wwise_conn):
    result = _parse(wwise_preview("\\foo", "rewind"))
    assert result["status"] == "error"
    assert "Invalid action" in result["message"]


def test_generate_banks(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.soundbank.generate", {"logs": []})
    result = _parse(wwise_generate_banks('["Weapons_Bank", "UI_Bank"]'))
    assert result["status"] == "ok"
    assert result["banks_generated"] == 2
    assert result["names"] == ["Weapons_Bank", "UI_Bank"]


def test_generate_banks_invalid_json(wwise_conn):
    result = _parse(wwise_generate_banks("not-json"))
    assert result["status"] == "error"
    assert "Invalid bank_names" in result["message"]


def test_generate_banks_empty_array(wwise_conn):
    result = _parse(wwise_generate_banks("[]"))
    assert result["status"] == "error"
    assert "non-empty" in result["message"]
