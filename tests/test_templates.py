"""Tests for template tools — complete game audio system generators."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.templates import (
    template_aaa_setup,
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


# --- AAA Project Setup ---

def test_aaa_setup_defaults(wwise_conn, mock_waapi):
    _setup_mock(mock_waapi)
    result = _parse(template_aaa_setup())
    assert result["status"] == "ok"
    assert result["template"] == "aaa_setup"

    # Check buses created
    buses = result["buses"]
    assert "AmbientMaster" in buses
    assert "PlayerMaster" in buses
    assert "NPCMaster" in buses
    assert "UIMaster" in buses
    assert "MusicMaster" in buses
    assert "Reverbs" in buses

    # Check nested buses were traversed (child buses are also in flat dict)
    assert "PlayerFootsteps" in buses
    assert "2DAmbience" in buses
    assert "3DAmbience" in buses

    # Check Work Units
    assert len(result["actor_work_units"]) == 7
    assert "Player_Locomotion" in result["actor_work_units"]
    assert "NPC_Locomotion" in result["actor_work_units"]

    assert len(result["event_work_units"]) == 6
    assert "Player" in result["event_work_units"]
    assert "Locomotion" in result["event_work_units"]

    # Check Switch Groups
    assert "Surface_Type" in result["switch_groups"]
    assert "Concrete" in result["switch_groups"]["Surface_Type"]["values"]

    # Check State Groups
    assert "Weather" in result["state_groups"]
    assert "Clear" in result["state_groups"]["Weather"]["values"]

    # Verify undo group lifecycle
    assert _has_call(mock_waapi, "ak.wwise.core.undo.beginGroup")
    assert _has_call(mock_waapi, "ak.wwise.core.undo.endGroup")

    # Summary counts
    assert result["summary"]["buses_created"] > 0
    assert result["summary"]["actor_work_units_created"] == 7
    assert result["summary"]["event_work_units_created"] == 6
    assert result["summary"]["switch_groups_created"] == 2
    assert result["summary"]["state_groups_created"] == 3


def test_aaa_setup_no_reverbs(wwise_conn, mock_waapi):
    _setup_mock(mock_waapi)
    result = _parse(template_aaa_setup(include_reverbs=False))
    assert result["status"] == "ok"
    assert "Reverbs" not in result["buses"]
    assert "LargeRoom" not in result["buses"]


def test_aaa_setup_custom_work_units(wwise_conn, mock_waapi):
    _setup_mock(mock_waapi)
    result = _parse(template_aaa_setup(
        actor_work_units='["Vehicles", "Creatures"]',
        event_work_units='["Gameplay", "Cinematic"]',
    ))
    assert result["status"] == "ok"
    assert "Vehicles" in result["actor_work_units"]
    assert "Creatures" in result["actor_work_units"]
    assert len(result["actor_work_units"]) == 2
    assert "Gameplay" in result["event_work_units"]
    assert len(result["event_work_units"]) == 2


def test_aaa_setup_custom_switch_state_groups(wwise_conn, mock_waapi):
    _setup_mock(mock_waapi)
    result = _parse(template_aaa_setup(
        switch_groups='{"Weapon_Type": ["Pistol", "Rifle", "Shotgun"]}',
        state_groups='{"GamePhase": ["Menu", "InGame", "Cutscene"]}',
    ))
    assert result["status"] == "ok"
    assert "Weapon_Type" in result["switch_groups"]
    assert "Pistol" in result["switch_groups"]["Weapon_Type"]["values"]
    assert "GamePhase" in result["state_groups"]
    assert "InGame" in result["state_groups"]["GamePhase"]["values"]


def test_aaa_setup_invalid_json(wwise_conn):
    result = _parse(template_aaa_setup(bus_structure="not-json"))
    assert result["status"] == "error"

    result = _parse(template_aaa_setup(actor_work_units="bad"))
    assert result["status"] == "error"

    result = _parse(template_aaa_setup(switch_groups="{bad"))
    assert result["status"] == "error"


def test_aaa_setup_work_units_created_at_hierarchy_root(wwise_conn, mock_waapi):
    """Work Units must be created at hierarchy roots, not inside Default Work Unit."""
    _setup_mock(mock_waapi)
    _parse(template_aaa_setup(
        actor_work_units='["TestWU"]',
        event_work_units='["TestEventWU"]',
    ))
    create_calls = _get_calls(mock_waapi, "ak.wwise.core.object.create")
    # Find WorkUnit creation calls
    wu_calls = [
        a for a, _ in create_calls
        if a and a.get("type") == "WorkUnit"
    ]
    # Actor WU parent should be hierarchy root
    actor_wu = [a for a in wu_calls if a.get("name") == "TestWU"]
    assert actor_wu[0]["parent"] == "\\Actor-Mixer Hierarchy"
    # Event WU parent should be hierarchy root
    event_wu = [a for a in wu_calls if a.get("name") == "TestEventWU"]
    assert event_wu[0]["parent"] == "\\Events"


def test_aaa_setup_buses_under_master(wwise_conn, mock_waapi):
    """Top-level buses must be children of Master Audio Bus."""
    _setup_mock(mock_waapi)
    _parse(template_aaa_setup())
    create_calls = _get_calls(mock_waapi, "ak.wwise.core.object.create")
    bus_calls = [
        a for a, _ in create_calls
        if a and a.get("type") in ("Bus", "AuxBus")
    ]
    # First bus created should have Master Audio Bus as parent
    master_bus = "\\Master-Mixer Hierarchy\\Default Work Unit\\Master Audio Bus"
    top_level = [a for a in bus_calls if a.get("parent") == master_bus]
    assert len(top_level) >= 5  # AmbientMaster, NPCMaster, PlayerMaster, UIMaster, MusicMaster, Reverbs
