"""Tests for template tools — complete game audio system generators."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.templates import (
    template_ambient,
    template_footsteps,
    template_gunshot,
    template_ui_sound,
    template_weather_states,
)


def _parse(result: str) -> dict:
    return json.loads(result)


def _setup_mock(mock_waapi):
    """Set up common mock responses for template operations."""
    # Object creation returns incrementing IDs
    call_count = {"n": 0}
    original_call = mock_waapi.call

    def counting_call(uri, args=None, options=None):
        mock_waapi.calls.append((uri, args, options))
        if uri == "ak.wwise.core.object.create":
            call_count["n"] += 1
            return {"id": f"guid-{call_count['n']}", "name": (args or {}).get("name", "obj")}
        if uri in mock_waapi._responses:
            return mock_waapi._responses[uri]
        return None

    mock_waapi.call = counting_call


def _get_calls(mock_waapi, uri: str) -> list:
    """Get all calls made to a specific URI."""
    return [(args, opts) for u, args, opts in mock_waapi.calls if u == uri]


def _has_call(mock_waapi, uri: str) -> bool:
    return any(u == uri for u, _, _ in mock_waapi.calls)


# --- Gunshot ---

def test_template_gunshot(wwise_conn, mock_waapi):
    _setup_mock(mock_waapi)
    result = _parse(template_gunshot("Pistol", 4, 200))
    assert result["status"] == "ok"
    assert result["template"] == "gunshot"
    assert result["weapon_name"] == "Pistol"
    assert result["num_variations"] == 4
    assert len(result["sound_ids"]) == 4
    # Verify undo group lifecycle
    assert _has_call(mock_waapi, "ak.wwise.core.undo.beginGroup")
    assert _has_call(mock_waapi, "ak.wwise.core.undo.endGroup")
    # Verify pitch randomization was actually applied to sounds
    prop_calls = _get_calls(mock_waapi, "ak.wwise.core.object.setProperty")
    pitch_min_calls = [a for a, _ in prop_calls if a and a.get("property") == "PitchModMin"]
    pitch_max_calls = [a for a, _ in prop_calls if a and a.get("property") == "PitchModMax"]
    assert len(pitch_min_calls) == 4  # one per variation
    assert len(pitch_max_calls) == 4
    assert pitch_min_calls[0]["value"] == -100  # half of 200 cents
    assert pitch_max_calls[0]["value"] == 100


def test_template_gunshot_invalid_variations(wwise_conn, mock_waapi):
    result = _parse(template_gunshot("X", 0))
    assert result["status"] == "error"
    assert "num_variations" in result["message"]


# --- Footsteps ---

def test_template_footsteps(wwise_conn, mock_waapi):
    _setup_mock(mock_waapi)
    result = _parse(template_footsteps('["Stone", "Sand"]'))
    assert result["status"] == "ok"
    assert result["template"] == "footsteps"
    assert "Stone" in result["surfaces"]
    assert "Sand" in result["surfaces"]
    assert _has_call(mock_waapi, "ak.wwise.core.switchContainer.addAssignment")
    assert _has_call(mock_waapi, "ak.wwise.core.undo.beginGroup")


def test_template_footsteps_invalid_json(wwise_conn):
    result = _parse(template_footsteps("not-json"))
    assert result["status"] == "error"


def test_template_footsteps_no_switch_group(wwise_conn, mock_waapi):
    _setup_mock(mock_waapi)
    result = _parse(template_footsteps('["Tile"]', with_switch_group=False))
    assert result["status"] == "ok"
    assert result["switch_group_id"] is None


# --- Ambient ---

def test_template_ambient(wwise_conn, mock_waapi):
    _setup_mock(mock_waapi)
    result = _parse(template_ambient('["Rain_Light", "Rain_Heavy"]', "Rain_Intensity"))
    assert result["status"] == "ok"
    assert result["template"] == "ambient"
    assert result["rtpc_parameter"] == "Rain_Intensity"
    assert len(result["sound_ids"]) == 2
    # Verify looping was set on sounds
    prop_calls = _get_calls(mock_waapi, "ak.wwise.core.object.setProperty")
    loop_calls = [a for a, _ in prop_calls if a and a.get("property") == "IsLoopingEnabled"]
    assert len(loop_calls) == 2


def test_template_ambient_invalid_json(wwise_conn):
    result = _parse(template_ambient("bad"))
    assert result["status"] == "error"


# --- UI Sound ---

def test_template_ui_sound(wwise_conn, mock_waapi):
    _setup_mock(mock_waapi)
    result = _parse(template_ui_sound("Hover"))
    assert result["status"] == "ok"
    assert result["template"] == "ui_sound"
    # Verify bus routing was set
    assert _has_call(mock_waapi, "ak.wwise.core.object.setReference")


# --- Weather States ---

def test_template_weather_states(wwise_conn, mock_waapi):
    _setup_mock(mock_waapi)
    result = _parse(template_weather_states('["Sunny", "Rainy", "Snowy"]'))
    assert result["status"] == "ok"
    assert result["template"] == "weather_states"
    assert "Sunny" in result["states"]
    assert "Rainy" in result["sounds"]
    assert _has_call(mock_waapi, "ak.wwise.core.switchContainer.addAssignment")
    assert _has_call(mock_waapi, "ak.wwise.core.undo.beginGroup")
    assert _has_call(mock_waapi, "ak.wwise.core.undo.endGroup")


def test_template_weather_states_invalid_json(wwise_conn):
    result = _parse(template_weather_states("nope"))
    assert result["status"] == "error"
