"""Tests for event & mixing tools."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.events import (
    wwise_assign_switch,
    wwise_create_event,
    wwise_set_attenuation,
    wwise_set_rtpc,
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


def test_set_rtpc(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.object.create", {"id": "gp-1"})
    points = json.dumps([
        {"x": 0, "y": -96, "shape": "SCurve"},
        {"x": 100, "y": 0, "shape": "SCurve"},
    ])
    result = _parse(wwise_set_rtpc(
        "RTPC_Wind",
        "\\Actor-Mixer Hierarchy\\Default Work Unit\\Wind",
        "Volume",
        points,
    ))
    assert result["status"] == "ok"
    assert result["game_parameter_id"] == "gp-1"


def test_set_rtpc_invalid_points(wwise_conn):
    result = _parse(wwise_set_rtpc("GP", "\\foo", "Volume", "not-json"))
    assert result["status"] == "error"
    assert "Invalid curve_points" in result["message"]


def test_set_rtpc_too_few_points(wwise_conn):
    result = _parse(wwise_set_rtpc("GP", "\\foo", "Volume", '[{"x":0,"y":0,"shape":"Linear"}]'))
    assert result["status"] == "error"
    assert "at least 2 points" in result["message"]


def test_set_rtpc_invalid_shape(wwise_conn):
    points = json.dumps([
        {"x": 0, "y": 0, "shape": "Banana"},
        {"x": 100, "y": 0, "shape": "Linear"},
    ])
    result = _parse(wwise_set_rtpc("GP", "\\foo", "Volume", points))
    assert result["status"] == "error"
    assert "Invalid curve shape" in result["message"]


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
