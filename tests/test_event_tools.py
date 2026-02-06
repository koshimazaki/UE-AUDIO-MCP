"""Tests for event & mixing tools."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.events import (
    wwise_assign_switch,
    wwise_create_event,
    wwise_create_game_parameter,
    wwise_set_attenuation,
)


def _parse(result: str) -> dict:
    return json.loads(result)


def test_create_event(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.object.create", {"id": "evt-1", "name": "Play_Gunshot"})
    result = _parse(wwise_create_event(
        "Play_Gunshot",
        "\\Actor-Mixer Hierarchy\\Default Work Unit\\Gunshot",
    ))
    assert result["status"] == "ok"
    assert result["event_id"] == "evt-1"
    assert result["action"] == "Play"
    # Verify @ActionType was passed as integer 1
    call_args = mock_waapi.calls[-1][1]
    assert call_args["children"][0]["@ActionType"] == 1


def test_create_event_stop_action(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.object.create", {"id": "evt-2", "name": "Stop_Music"})
    result = _parse(wwise_create_event(
        "Stop_Music",
        "\\Actor-Mixer Hierarchy\\Default Work Unit\\Music",
        action_type="Stop",
    ))
    assert result["status"] == "ok"
    assert result["action"] == "Stop"
    call_args = mock_waapi.calls[-1][1]
    assert call_args["children"][0]["@ActionType"] == 2


def test_create_event_invalid_action(wwise_conn):
    result = _parse(wwise_create_event("Evt", "\\foo", action_type="Explode"))
    assert result["status"] == "error"
    assert "Invalid action_type" in result["message"]


def test_create_game_parameter(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.object.create", {"id": "gp-1"})
    mock_waapi.set_response("ak.wwise.core.object.setProperty", None)
    result = _parse(wwise_create_game_parameter("RTPC_Wind"))
    assert result["status"] == "ok"
    assert result["game_parameter_id"] == "gp-1"
    assert result["name"] == "RTPC_Wind"
    assert result["range"] == [0.0, 100.0]
    assert result["default"] == 50.0


def test_create_game_parameter_custom_range(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.object.create", {"id": "gp-2"})
    mock_waapi.set_response("ak.wwise.core.object.setProperty", None)
    result = _parse(wwise_create_game_parameter(
        "RTPC_Speed", min_value=0.0, max_value=300.0, default_value=60.0,
    ))
    assert result["status"] == "ok"
    assert result["range"] == [0.0, 300.0]
    assert result["default"] == 60.0
    # Verify setProperty was called for range/default (3 calls)
    prop_calls = [
        (args, opts) for uri, args, opts in mock_waapi.calls
        if uri == "ak.wwise.core.object.setProperty"
    ]
    assert len(prop_calls) == 3


def test_assign_switch(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.switchContainer.addAssignment", None)
    result = _parse(wwise_assign_switch(
        "\\Actor-Mixer Hierarchy\\Default Work Unit\\Footsteps",
        "child-guid-123",
        "switch-guid-456",
    ))
    assert result["status"] == "ok"
    assert result["child"] == "child-guid-123"


def test_set_attenuation(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.object.create", {"id": "att-1"})
    mock_waapi.set_response("ak.wwise.core.object.setAttenuationCurve", None)
    points = json.dumps([
        {"x": 0, "y": 0, "shape": "Linear"},
        {"x": 100, "y": -200, "shape": "Exp3"},
    ])
    result = _parse(wwise_set_attenuation("MyAtten", "VolumeDryUsage", points))
    assert result["status"] == "ok"
    assert result["attenuation_id"] == "att-1"


def test_set_attenuation_invalid_curve_type(wwise_conn):
    points = json.dumps([{"x": 0, "y": 0, "shape": "Linear"}, {"x": 1, "y": 1, "shape": "Linear"}])
    result = _parse(wwise_set_attenuation("A", "BadCurve", points))
    assert result["status"] == "error"
    assert "Invalid curve_type" in result["message"]
