"""Tests for core WAAPI tools."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.core import (
    execute_waapi,
    wwise_connect,
    wwise_get_info,
    wwise_query,
    wwise_save,
)


def _parse(result: str) -> dict:
    return json.loads(result)


def test_wwise_connect_success(wwise_conn, mock_waapi, monkeypatch):
    """wwise_connect returns version info on success."""
    import ue_audio_mcp.connection as conn_mod

    # Simulate a fresh connection by patching connect() to use the mock
    def fake_connect(self, url=None):
        self._client = mock_waapi
        return mock_waapi.call("ak.wwise.core.getInfo")

    monkeypatch.setattr(conn_mod.WwiseConnection, "connect", fake_connect)
    result = _parse(wwise_connect())
    assert result["status"] == "ok"
    assert "Wwise 2024" in result["version"]


def test_wwise_connect_failure(wwise_conn, monkeypatch):
    """wwise_connect returns error when Wwise is not running."""
    import ue_audio_mcp.connection as conn_mod

    def fake_connect(self, url=None):
        raise Exception("Connection refused")

    monkeypatch.setattr(conn_mod.WwiseConnection, "connect", fake_connect)
    result = _parse(wwise_connect())
    assert result["status"] == "error"
    assert "Cannot connect" in result["message"]


def test_wwise_get_info(wwise_conn, mock_waapi):
    result = _parse(wwise_get_info())
    assert result["status"] == "ok"
    assert "info" in result
    assert result["info"]["version"]["year"] == 2024


def test_wwise_query(wwise_conn, mock_waapi):
    mock_waapi.set_response(
        "ak.wwise.core.object.get",
        {"return": [{"id": "abc", "name": "TestSound", "type": "Sound", "path": "\\foo"}]},
    )
    result = _parse(wwise_query("$ from type sound"))
    assert result["status"] == "ok"
    assert result["count"] == 1
    assert result["results"][0]["name"] == "TestSound"


def test_wwise_query_invalid_fields(wwise_conn):
    result = _parse(wwise_query("$ from type sound", return_fields="not-json"))
    assert result["status"] == "error"
    assert "Invalid return_fields" in result["message"]


def test_wwise_save(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.project.save", None)
    result = _parse(wwise_save())
    assert result["status"] == "ok"


def test_execute_waapi(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.object.getTypes", {"types": ["Sound", "Event"]})
    result = _parse(execute_waapi("ak.wwise.core.object.getTypes"))
    assert result["status"] == "ok"
    assert result["result"]["types"] == ["Sound", "Event"]


def test_execute_waapi_invalid_args(wwise_conn):
    result = _parse(execute_waapi("ak.wwise.core.getInfo", args_json="{bad}"))
    assert result["status"] == "error"
    assert "Invalid args_json" in result["message"]
