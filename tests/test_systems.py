"""Tests for the orchestration layer — build_audio_system tool."""

from __future__ import annotations

import json

import pytest

from ue_audio_mcp.tools.systems import (
    AAA_AUDIO_CATEGORIES,
    PATTERNS,
    build_aaa_project,
    build_audio_system,
)


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
        assert result["layers"]["blueprint"]["mode"] == "planned"

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


# ---------------------------------------------------------------------------
# Integration spec — Wwise JSON templates with cross-layer links
# ---------------------------------------------------------------------------

class TestIntegrationSpec:
    """Wwise JSON templates provide signal_flow, audiolink, and cross-layer links."""

    def test_gunshot_has_integration(self):
        result = _parse(build_audio_system("gunshot"))
        assert "integration" in result
        assert result["integration"] is not None

    def test_integration_signal_flow(self):
        result = _parse(build_audio_system("gunshot"))
        flow = result["integration"]["signal_flow"]
        assert len(flow) > 0
        assert any("BLUEPRINT" in step for step in flow)
        assert any("WWISE" in step for step in flow)
        assert any("METASOUNDS" in step for step in flow)

    def test_integration_audiolink(self):
        result = _parse(build_audio_system("gunshot"))
        al = result["integration"]["audiolink"]
        assert al is not None
        assert al["enabled"] is True
        assert al["direction"] == "MetaSounds → Wwise"
        assert "setup_steps" in al
        assert len(al["setup_steps"]) > 0

    def test_integration_metasound_link(self):
        result = _parse(build_audio_system("footsteps"))
        ms_link = result["integration"]["metasound_link"]
        assert ms_link is not None
        assert ms_link["template"] == "metasounds/footsteps.json"
        assert "parameter_mapping" in ms_link
        assert len(ms_link["parameter_mapping"]) > 0

    def test_integration_blueprint_link(self):
        result = _parse(build_audio_system("weather"))
        bp_link = result["integration"]["blueprint_link"]
        assert bp_link is not None
        assert bp_link["template"] == "blueprints/wind_system.json"
        assert "parameter_mapping" in bp_link
        assert len(bp_link["parameter_mapping"]) > 0
        assert "states_set" in bp_link
        assert "Weather" in bp_link["states_set"]

    def test_all_wwise_patterns_have_integration(self):
        """Every pattern with a wwise_json should return integration spec."""
        for name, cfg in PATTERNS.items():
            result = _parse(build_audio_system(name))
            if cfg.get("wwise_json"):
                assert result["integration"] is not None, \
                    "{} should have integration".format(name)
            else:
                assert result["integration"] is None, \
                    "{} should not have integration".format(name)

    def test_connection_map_has_audiolink_bus(self):
        result = _parse(build_audio_system("ambient"))
        conn = result["connections"]
        assert "audiolink_bus" in conn
        assert conn["audiolink_bus"] == "AudioLink_Ambience"

    def test_connection_wiring_has_types(self):
        result = _parse(build_audio_system("weather"))
        wiring = result["connections"]["wiring"]
        types = {w["type"] for w in wiring}
        assert "event" in types
        assert "state" in types
        assert "param" in types
        assert "audiolink" in types

    def test_spatial_no_integration(self):
        result = _parse(build_audio_system("spatial"))
        assert result["integration"] is None

    def test_blueprint_layers_now_planned(self):
        """Most patterns should now have bp_template linked."""
        linked = 0
        for name, cfg in PATTERNS.items():
            if cfg.get("bp_template"):
                result = _parse(build_audio_system(name))
                bp = result["layers"]["blueprint"]
                assert bp["mode"] == "planned", \
                    "{} blueprint should be planned".format(name)
                linked += 1
        assert linked >= 7  # All except macro_sequence


# ---------------------------------------------------------------------------
# AAA Project Orchestrator — build_aaa_project
# ---------------------------------------------------------------------------

class TestAAAProjectOffline:
    """build_aaa_project in offline mode — returns planned specs for all categories."""

    def test_aaa_project_offline_all_categories(self):
        result = _parse(build_aaa_project())
        assert result["status"] == "ok"
        assert result["mode"] == "offline"
        assert result["summary"]["total_categories"] == len(AAA_AUDIO_CATEGORIES)
        assert result["summary"]["infrastructure_mode"] == "planned"
        assert result["summary"]["routing_applied"] == 0
        assert result["summary"]["moves_applied"] == 0

    def test_aaa_project_offline_categories_present(self):
        result = _parse(build_aaa_project())
        for cat_key in AAA_AUDIO_CATEGORIES:
            assert cat_key in result["categories"], \
                "Missing category: {}".format(cat_key)
            cat = result["categories"][cat_key]
            assert "system" in cat
            assert cat["system"]["status"] == "ok"

    def test_aaa_project_offline_infrastructure_planned(self):
        result = _parse(build_aaa_project())
        infra = result["infrastructure"]
        assert infra["mode"] == "planned"
        assert "description" in infra

    def test_aaa_project_offline_each_category_has_layers(self):
        result = _parse(build_aaa_project())
        for cat_key, cat in result["categories"].items():
            system = cat["system"]
            assert "layers" in system, "{} missing layers".format(cat_key)
            assert system["layers"]["metasounds"]["mode"] == "planned", \
                "{} MS not planned".format(cat_key)

    def test_aaa_project_offline_manifest_shape(self):
        result = _parse(build_aaa_project())
        assert "categories_built" in result
        assert "infrastructure" in result
        assert "categories" in result
        assert "routing" in result
        assert "moves" in result
        assert "summary" in result
        assert isinstance(result["routing"], list)
        assert isinstance(result["moves"], list)


class TestAAAProjectCustomCategories:
    """build_aaa_project with category filter."""

    def test_single_category(self):
        result = _parse(build_aaa_project(categories="player_footsteps"))
        assert result["status"] == "ok"
        assert result["summary"]["total_categories"] == 1
        assert "player_footsteps" in result["categories"]
        assert "player_weapons" not in result["categories"]

    def test_multiple_categories(self):
        result = _parse(build_aaa_project(categories="player_footsteps,ui,weather"))
        assert result["status"] == "ok"
        assert result["summary"]["total_categories"] == 3
        assert set(result["categories_built"]) == {"player_footsteps", "ui", "weather"}

    def test_invalid_category(self):
        result = _parse(build_aaa_project(categories="nonexistent"))
        assert result["status"] == "error"
        assert "Unknown categories" in result["message"]

    def test_invalid_setup_params(self):
        result = _parse(build_aaa_project(setup_params="not-json"))
        assert result["status"] == "error"
        assert "Invalid setup_params" in result["message"]

    def test_setup_params_not_object(self):
        result = _parse(build_aaa_project(setup_params="[1,2]"))
        assert result["status"] == "error"
        assert "JSON object" in result["message"]


class TestAAAProjectWwiseOnly:
    """build_aaa_project with Wwise connected."""

    def test_aaa_project_wwise_only(self, wwise_conn, mock_waapi):
        _setup_wwise_mock(mock_waapi)
        result = _parse(build_aaa_project())
        assert result["status"] == "ok"
        assert result["mode"] == "wwise_only"
        assert result["infrastructure"]["mode"] == "executed"
        assert result["summary"]["total_categories"] == len(AAA_AUDIO_CATEGORIES)

    def test_aaa_project_bus_routing(self, wwise_conn, mock_waapi):
        """Verify setReference calls for bus routing."""
        _setup_wwise_mock(mock_waapi)
        result = _parse(build_aaa_project(categories="player_weapons"))
        assert result["status"] == "ok"
        routing = result["routing"]
        assert len(routing) > 0, "Bus routing should have been applied"
        assert routing[0]["category"] == "player_weapons"
        assert routing[0]["status"] == "ok"

    def test_aaa_project_work_unit_moves(self, wwise_conn, mock_waapi):
        """Verify move calls to correct work units."""
        _setup_wwise_mock(mock_waapi)
        result = _parse(build_aaa_project(categories="player_footsteps"))
        assert result["status"] == "ok"
        moves = result["moves"]
        assert len(moves) > 0, "Work unit moves should have been applied"
        move_types = [m["type"] for m in moves]
        assert "actor_mixer" in move_types or "event" in move_types

    def test_aaa_project_wwise_setreference_calls(self, wwise_conn, mock_waapi):
        """Verify actual WAAPI setReference and move calls were made."""
        _setup_wwise_mock(mock_waapi)
        _parse(build_aaa_project(categories="ui"))
        # Check that setReference was called for bus routing
        set_ref_calls = [
            c for c in mock_waapi.calls
            if c[0] == "ak.wwise.core.object.setReference"
        ]
        assert len(set_ref_calls) > 0, "setReference should have been called for bus routing"
        # Check that move was called for work unit organization
        move_calls = [
            c for c in mock_waapi.calls
            if c[0] == "ak.wwise.core.object.move"
        ]
        assert len(move_calls) > 0, "move should have been called for work unit organization"
        # Infrastructure creates many objects too
        create_calls = [
            c for c in mock_waapi.calls
            if c[0] == "ak.wwise.core.object.create"
        ]
        assert len(create_calls) > 10  # buses + work units + switches + states


class TestAAAProjectCategoryMapping:
    """Verify AAA_AUDIO_CATEGORIES structure is consistent."""

    def test_all_categories_reference_valid_patterns(self):
        for cat_key, cat_cfg in AAA_AUDIO_CATEGORIES.items():
            assert cat_cfg["pattern"] in PATTERNS, \
                "{} references unknown pattern '{}'".format(cat_key, cat_cfg["pattern"])

    def test_all_categories_have_required_fields(self):
        required = {"pattern", "name", "bus", "bus_path", "actor_work_unit", "event_work_unit"}
        for cat_key, cat_cfg in AAA_AUDIO_CATEGORIES.items():
            missing = required - set(cat_cfg.keys())
            assert not missing, \
                "{} missing fields: {}".format(cat_key, missing)

    def test_category_names_are_unique(self):
        names = [cfg["name"] for cfg in AAA_AUDIO_CATEGORIES.values()]
        assert len(names) == len(set(names)), "Duplicate category names"

    def test_category_bus_paths_are_valid(self):
        for cat_key, cat_cfg in AAA_AUDIO_CATEGORIES.items():
            bus_path = cat_cfg["bus_path"]
            assert bus_path.startswith("\\"), \
                "{} bus_path should start with backslash".format(cat_key)
            assert cat_cfg["bus"] in bus_path, \
                "{} bus '{}' not found in bus_path".format(cat_key, cat_cfg["bus"])
