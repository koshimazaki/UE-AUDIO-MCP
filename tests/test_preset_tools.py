"""Tests for preset swap, morph, and macro trigger tools."""

from __future__ import annotations

import json

import pytest

from ue_audio_mcp.tools.presets import ms_preset_swap, ms_preset_morph, ms_macro_trigger


def _parse(result: str) -> dict:
    return json.loads(result)


# ---------------------------------------------------------------------------
# ms_preset_swap
# ---------------------------------------------------------------------------

class TestPresetSwap:
    """Preset swap tool tests."""

    def test_swap_offline(self):
        result = _parse(ms_preset_swap(
            "MyPreset",
            "/Game/Audio/BaseSynth",
            '{"Cutoff": 2000.0, "Gain": 0.5}',
        ))
        assert result["status"] == "ok"
        assert result["mode"] == "planned"
        assert result["preset_name"] == "MyPreset"
        assert result["referenced_asset"] == "/Game/Audio/BaseSynth"
        assert result["overrides"]["Cutoff"] == 2000.0
        assert result["command_count"] > 0

    def test_swap_commands_sequence(self):
        result = _parse(ms_preset_swap(
            "TestPreset",
            "/Game/Audio/Source",
            '{"Volume": 0.8}',
        ))
        cmds = result["commands"]
        actions = [c["action"] for c in cmds]
        assert actions[0] == "create_builder"
        assert "convert_to_preset" in actions
        assert actions[-1] == "build_to_asset"

    def test_swap_no_overrides(self):
        result = _parse(ms_preset_swap("Clean", "/Game/Audio/Base"))
        assert result["status"] == "ok"
        assert result["overrides"] == {}

    def test_swap_invalid_json(self):
        result = _parse(ms_preset_swap("X", "/Game/Audio/Y", "not-json"))
        assert result["status"] == "error"
        assert "Invalid" in result["message"]

    def test_swap_overrides_not_object(self):
        result = _parse(ms_preset_swap("X", "/Game/Audio/Y", "[1,2]"))
        assert result["status"] == "error"
        assert "JSON object" in result["message"]

    def test_swap_invalid_path(self):
        result = _parse(ms_preset_swap("X", "/Game/Audio/Y", "{}", "/Bad/Path"))
        assert result["status"] == "error"
        assert "/Game/" in result["message"]

    def test_swap_online(self, ue5_conn, mock_ue5_plugin):
        result = _parse(ms_preset_swap(
            "OnlinePreset",
            "/Game/Audio/Base",
            '{"Freq": 880}',
        ))
        assert result["status"] == "ok"
        assert result["mode"] == "executed"
        assert len(mock_ue5_plugin.commands) == result["command_count"]


# ---------------------------------------------------------------------------
# ms_preset_morph
# ---------------------------------------------------------------------------

class TestPresetMorph:
    """Preset morph tool tests."""

    def test_morph_offline(self):
        result = _parse(ms_preset_morph(
            "MorphSound",
            '{"Cutoff": 500, "Gain": 0.3}',
            '{"Cutoff": 8000, "Gain": 1.0}',
        ))
        assert result["status"] == "ok"
        assert result["mode"] == "planned"
        assert result["morph_params"] == ["Cutoff", "Gain"]
        assert result["command_count"] > 0

    def test_morph_commands_have_map_range(self):
        result = _parse(ms_preset_morph(
            "Test",
            '{"Freq": 200}',
            '{"Freq": 2000}',
        ))
        cmds = result["commands"]
        node_types = [c.get("node_type", "") for c in cmds if c["action"] == "add_node"]
        assert "Map Range" in node_types
        assert "InterpTo" in node_types

    def test_morph_mismatched_keys(self):
        result = _parse(ms_preset_morph(
            "Bad",
            '{"A": 1}',
            '{"B": 2}',
        ))
        assert result["status"] == "error"
        assert "same keys" in result["message"]

    def test_morph_empty_params(self):
        result = _parse(ms_preset_morph("Empty", "{}", "{}"))
        assert result["status"] == "error"
        assert "At least one" in result["message"]

    def test_morph_invalid_json(self):
        result = _parse(ms_preset_morph("X", "bad", "bad"))
        assert result["status"] == "error"

    def test_morph_online(self, ue5_conn, mock_ue5_plugin):
        result = _parse(ms_preset_morph(
            "OnlineMorph",
            '{"Vol": 0.2}',
            '{"Vol": 1.0}',
        ))
        assert result["status"] == "ok"
        assert result["mode"] == "executed"


# ---------------------------------------------------------------------------
# ms_macro_trigger
# ---------------------------------------------------------------------------

class TestMacroTrigger:
    """Macro trigger tool tests."""

    def test_macro_offline(self):
        steps = json.dumps([
            {"action": "set_default", "node_id": "filter", "input": "Cutoff Frequency", "value": 500},
            {"action": "set_default", "node_id": "gain", "input": "B", "value": 0.3},
        ])
        result = _parse(ms_macro_trigger("DarkMode", steps))
        assert result["status"] == "ok"
        assert result["mode"] == "planned"
        assert result["step_count"] == 2

    def test_macro_invalid_json(self):
        result = _parse(ms_macro_trigger("X", "not-json"))
        assert result["status"] == "error"

    def test_macro_not_array(self):
        result = _parse(ms_macro_trigger("X", '{"a": 1}'))
        assert result["status"] == "error"
        assert "array" in result["message"]

    def test_macro_empty_steps(self):
        result = _parse(ms_macro_trigger("X", "[]"))
        assert result["status"] == "error"
        assert "At least one" in result["message"]

    def test_macro_invalid_action(self):
        result = _parse(ms_macro_trigger("X", '[{"action": "bad_action"}]'))
        assert result["status"] == "error"
        assert "invalid action" in result["message"]

    def test_macro_online(self, ue5_conn, mock_ue5_plugin):
        steps = json.dumps([
            {"action": "set_default", "node_id": "n1", "input": "Freq", "value": 1000},
        ])
        result = _parse(ms_macro_trigger("TestMacro", steps))
        assert result["status"] == "ok"
        assert result["mode"] == "executed"
        assert len(mock_ue5_plugin.commands) == 1
