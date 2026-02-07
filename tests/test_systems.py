"""Tests for the orchestration layer — build_audio_system tool."""

from __future__ import annotations

import json

import pytest

from ue_audio_mcp.tools.systems import PATTERNS, build_audio_system


def _parse(result: str) -> dict:
    return json.loads(result)


def _setup_wwise_mock(mock_waapi):
    """Set up counting mock for Wwise object creation."""
    call_count = {"n": 0}

    def counting_call(uri, args=None, options=None):
        mock_waapi.calls.append((uri, args, options))
        if uri == "ak.wwise.core.object.create":
            call_count["n"] += 1
            return {"id": "guid-{}".format(call_count["n"]), "name": (args or {}).get("name", "obj")}
        if uri in mock_waapi._responses:
            return mock_waapi._responses[uri]
        return None

    mock_waapi.call = counting_call


# ---------------------------------------------------------------------------
# Offline mode — both disconnected, returns specs
# ---------------------------------------------------------------------------

class TestOfflineMode:
    """All patterns work offline, returning planned specs."""

    def test_build_gunshot_offline(self):
        result = _parse(build_audio_system("gunshot"))
        assert result["status"] == "ok"
        assert result["mode"] == "offline"
        assert result["pattern"] == "gunshot"
        assert result["layers"]["wwise"]["mode"] == "planned"
        assert result["layers"]["metasounds"]["mode"] == "planned"
        assert result["layers"]["blueprint"]["mode"] == "skipped"

    def test_build_footsteps_offline(self):
        result = _parse(build_audio_system("footsteps"))
        assert result["status"] == "ok"
        assert result["mode"] == "offline"
        assert result["layers"]["wwise"]["mode"] == "planned"
        assert result["layers"]["metasounds"]["mode"] == "planned"

    def test_build_ambient_offline(self):
        result = _parse(build_audio_system("ambient"))
        assert result["status"] == "ok"
        assert result["mode"] == "offline"
        assert result["layers"]["wwise"]["mode"] == "planned"
        assert result["layers"]["metasounds"]["mode"] == "planned"

    def test_build_spatial_offline(self):
        result = _parse(build_audio_system("spatial"))
        assert result["status"] == "ok"
        assert result["mode"] == "offline"
        # spatial has no Wwise template
        assert result["layers"]["wwise"]["mode"] == "skipped"
        assert result["layers"]["metasounds"]["mode"] == "planned"

    def test_build_ui_sound_offline(self):
        result = _parse(build_audio_system("ui_sound"))
        assert result["status"] == "ok"
        assert result["mode"] == "offline"
        assert result["layers"]["wwise"]["mode"] == "planned"
        assert result["layers"]["metasounds"]["mode"] == "planned"

    def test_build_weather_offline(self):
        result = _parse(build_audio_system("weather"))
        assert result["status"] == "ok"
        assert result["mode"] == "offline"
        assert result["layers"]["wwise"]["mode"] == "planned"
        assert result["layers"]["metasounds"]["mode"] == "planned"

    @pytest.mark.parametrize("pattern", sorted(PATTERNS.keys()))
    def test_all_patterns_offline(self, pattern):
        """Every registered pattern returns ok in offline mode."""
        result = _parse(build_audio_system(pattern))
        assert result["status"] == "ok"
        assert result["mode"] == "offline"
        assert result["pattern"] == pattern
        assert "layers" in result
        assert "connections" in result


# ---------------------------------------------------------------------------
# Offline mode — MetaSounds details
# ---------------------------------------------------------------------------

class TestOfflineMetaSounds:
    """MetaSounds layer returns graph spec and builder commands offline."""

    def test_ms_commands_present(self):
        result = _parse(build_audio_system("gunshot"))
        ms = result["layers"]["metasounds"]
        assert ms["mode"] == "planned"
        assert ms["command_count"] > 0
        assert len(ms["commands"]) == ms["command_count"]

    def test_ms_commands_ordered(self):
        result = _parse(build_audio_system("gunshot"))
        cmds = result["layers"]["metasounds"]["commands"]
        actions = [c["action"] for c in cmds]
        assert actions[0] == "create_builder"
        assert actions[-1] == "build_to_asset"

    def test_ms_graph_spec_present(self):
        result = _parse(build_audio_system("footsteps"))
        ms = result["layers"]["metasounds"]
        assert "graph_spec" in ms
        assert ms["graph_spec"]["asset_type"] in ("Source", "Patch", "Preset")

    def test_ms_name_override(self):
        result = _parse(build_audio_system("gunshot", name="MyWeapon"))
        ms = result["layers"]["metasounds"]
        assert ms["graph_spec"]["name"] == "MyWeapon"


# ---------------------------------------------------------------------------
# Offline mode — Wwise planned details
# ---------------------------------------------------------------------------

class TestOfflineWwise:
    """Wwise layer returns planned params offline."""

    def test_wwise_planned_params(self):
        result = _parse(build_audio_system("gunshot"))
        ww = result["layers"]["wwise"]
        assert ww["mode"] == "planned"
        assert ww["template"] == "gunshot"
        assert "params" in ww

    def test_wwise_param_override(self):
        result = _parse(build_audio_system(
            "gunshot",
            params_json='{"wwise": {"num_variations": 7}}'
        ))
        ww = result["layers"]["wwise"]
        assert ww["params"]["num_variations"] == 7


# ---------------------------------------------------------------------------
# Wwise-only mode
# ---------------------------------------------------------------------------

class TestWwiseOnlyMode:
    """Wwise connected, UE5 disconnected."""

    def test_build_gunshot_wwise_only(self, wwise_conn, mock_waapi):
        _setup_wwise_mock(mock_waapi)
        result = _parse(build_audio_system("gunshot"))
        assert result["status"] == "ok"
        assert result["mode"] == "wwise_only"
        assert result["layers"]["wwise"]["mode"] == "executed"
        assert result["layers"]["wwise"]["result"]["status"] == "ok"
        assert result["layers"]["metasounds"]["mode"] == "planned"

    def test_build_footsteps_wwise_only(self, wwise_conn, mock_waapi):
        _setup_wwise_mock(mock_waapi)
        result = _parse(build_audio_system("footsteps"))
        assert result["status"] == "ok"
        assert result["mode"] == "wwise_only"
        assert result["layers"]["wwise"]["mode"] == "executed"

    def test_wwise_result_has_ids(self, wwise_conn, mock_waapi):
        _setup_wwise_mock(mock_waapi)
        result = _parse(build_audio_system("gunshot"))
        ww = result["layers"]["wwise"]["result"]
        assert "container_id" in ww or "event_id" in ww

    def test_spatial_wwise_only_skips_wwise(self, wwise_conn, mock_waapi):
        """spatial has no Wwise template, so Wwise layer is skipped even when connected."""
        result = _parse(build_audio_system("spatial"))
        assert result["mode"] == "wwise_only"
        assert result["layers"]["wwise"]["mode"] == "skipped"


# ---------------------------------------------------------------------------
# Full mode — both connected
# ---------------------------------------------------------------------------

class TestFullMode:
    """Both Wwise and UE5 connected."""

    def test_build_gunshot_full(self, wwise_conn, mock_waapi, ue5_conn, mock_ue5_plugin):
        _setup_wwise_mock(mock_waapi)
        result = _parse(build_audio_system("gunshot"))
        assert result["status"] == "ok"
        assert result["mode"] == "full"
        assert result["layers"]["wwise"]["mode"] == "executed"
        assert result["layers"]["metasounds"]["mode"] == "executed"
        assert result["layers"]["metasounds"]["command_count"] > 0

    def test_build_footsteps_full(self, wwise_conn, mock_waapi, ue5_conn, mock_ue5_plugin):
        _setup_wwise_mock(mock_waapi)
        result = _parse(build_audio_system("footsteps"))
        assert result["status"] == "ok"
        assert result["mode"] == "full"

    def test_ue5_commands_actually_sent(self, wwise_conn, mock_waapi, ue5_conn, mock_ue5_plugin):
        _setup_wwise_mock(mock_waapi)
        result = _parse(build_audio_system("ui_sound"))
        ms = result["layers"]["metasounds"]
        assert ms["mode"] == "executed"
        # MockUE5Plugin should have received commands
        assert len(mock_ue5_plugin.commands) == ms["command_count"]


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestErrors:
    """Invalid inputs and edge cases."""

    def test_invalid_pattern(self):
        result = _parse(build_audio_system("nonexistent"))
        assert result["status"] == "error"
        assert "Unknown pattern" in result["message"]
        assert "gunshot" in result["message"]  # lists available patterns

    def test_invalid_params_json(self):
        result = _parse(build_audio_system("gunshot", params_json="not-json"))
        assert result["status"] == "error"
        assert "Invalid params_json" in result["message"]

    def test_params_not_object(self):
        result = _parse(build_audio_system("gunshot", params_json="[1,2,3]"))
        assert result["status"] == "error"
        assert "JSON object" in result["message"]

    def test_empty_params_ok(self):
        result = _parse(build_audio_system("gunshot", params_json="{}"))
        assert result["status"] == "ok"


# ---------------------------------------------------------------------------
# Connection map
# ---------------------------------------------------------------------------

class TestConnectionMap:
    """Verify cross-layer connection map is built correctly."""

    def test_connection_map_present(self):
        result = _parse(build_audio_system("gunshot", name="Rifle"))
        conn = result["connections"]
        assert "wwise_event" in conn
        assert "metasound_asset" in conn
        assert "wiring" in conn

    def test_connection_map_name_resolution(self):
        result = _parse(build_audio_system("gunshot", name="Shotgun"))
        conn = result["connections"]
        assert "Shotgun" in conn["wwise_event"]
        assert "Shotgun" in conn["metasound_asset"]

    def test_connection_map_wiring(self):
        result = _parse(build_audio_system("footsteps"))
        wiring = result["connections"]["wiring"]
        assert len(wiring) > 0
        assert any("Surface_Type" in w["from"] for w in wiring)

    def test_connection_map_spatial_no_event(self):
        result = _parse(build_audio_system("spatial"))
        conn = result["connections"]
        assert conn["wwise_event"] is None

    def test_connection_map_wwise_ids_when_executed(self, wwise_conn, mock_waapi):
        _setup_wwise_mock(mock_waapi)
        result = _parse(build_audio_system("gunshot"))
        conn = result["connections"]
        assert len(conn["wwise_ids"]) > 0

    def test_connection_map_no_ids_offline(self):
        result = _parse(build_audio_system("gunshot"))
        conn = result["connections"]
        assert conn["wwise_ids"] == {}


# ---------------------------------------------------------------------------
# Name defaulting
# ---------------------------------------------------------------------------

class TestNaming:
    """Asset name defaults and overrides."""

    def test_default_name_from_pattern(self):
        result = _parse(build_audio_system("gunshot"))
        assert result["name"] == "Gunshot"

    def test_default_name_ui_sound(self):
        result = _parse(build_audio_system("ui_sound"))
        assert result["name"] == "UiSound"

    def test_custom_name(self):
        result = _parse(build_audio_system("gunshot", name="AWP"))
        assert result["name"] == "AWP"

    def test_name_in_ms_spec(self):
        result = _parse(build_audio_system("ambient", name="Ocean"))
        ms = result["layers"]["metasounds"]
        assert ms["graph_spec"]["name"] == "Ocean"


# ---------------------------------------------------------------------------
# New patterns: preset_morph and macro_sequence
# ---------------------------------------------------------------------------

class TestPresetMorphPattern:
    """preset_morph pattern in offline mode."""

    def test_preset_morph_offline(self):
        result = _parse(build_audio_system("preset_morph"))
        assert result["status"] == "ok"
        assert result["mode"] == "offline"
        assert result["pattern"] == "preset_morph"
        # No Wwise template
        assert result["layers"]["wwise"]["mode"] == "skipped"
        assert result["layers"]["metasounds"]["mode"] == "planned"

    def test_preset_morph_has_morph_input(self):
        result = _parse(build_audio_system("preset_morph"))
        ms = result["layers"]["metasounds"]
        graph_inputs = [p["name"] for p in ms["graph_spec"].get("inputs", [])]
        assert "Morph" in graph_inputs

    def test_preset_morph_connection_map(self):
        result = _parse(build_audio_system("preset_morph", name="TestMorph"))
        conn = result["connections"]
        assert conn["wwise_event"] is None
        assert "TestMorph" in conn["metasound_asset"]


class TestMacroSequencePattern:
    """macro_sequence pattern in offline mode."""

    def test_macro_sequence_offline(self):
        result = _parse(build_audio_system("macro_sequence"))
        assert result["status"] == "ok"
        assert result["mode"] == "offline"
        assert result["pattern"] == "macro_sequence"
        assert result["layers"]["wwise"]["mode"] == "skipped"
        assert result["layers"]["metasounds"]["mode"] == "planned"

    def test_macro_sequence_has_variables(self):
        result = _parse(build_audio_system("macro_sequence"))
        ms = result["layers"]["metasounds"]
        spec = ms["graph_spec"]
        assert "variables" in spec
        var_names = [v["name"] for v in spec["variables"]]
        assert "TargetCutoff" in var_names
        assert "TargetBandwidth" in var_names

    def test_macro_sequence_has_variable_commands(self):
        result = _parse(build_audio_system("macro_sequence"))
        ms = result["layers"]["metasounds"]
        actions = [c["action"] for c in ms["commands"]]
        assert "add_graph_variable" in actions
        assert "add_variable_set_node" in actions
        assert "add_variable_get_node" in actions

    def test_macro_sequence_connection_map(self):
        result = _parse(build_audio_system("macro_sequence", name="TestMacro"))
        conn = result["connections"]
        assert conn["wwise_event"] is None
        assert "TestMacro" in conn["metasound_asset"]
        wiring_froms = [w["from"] for w in conn["wiring"]]
        assert "blueprint.MacroStep1" in wiring_froms
