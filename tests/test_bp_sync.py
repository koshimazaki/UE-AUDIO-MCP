"""Tests for Blueprint engine sync — bp_sync_from_engine + helpers."""

from __future__ import annotations

import json

import ue_audio_mcp.ue5_connection as ue5_module
from ue_audio_mcp.tools.bp_builder import (
    bp_sync_from_engine,
    _engine_func_to_bp_scraped,
)


# ---------------------------------------------------------------------------
# Sample engine function responses for testing
# ---------------------------------------------------------------------------

def _make_engine_func(
    name: str = "TestFunc",
    class_name: str = "UAudioComponent",
    category: str = "Audio",
    description: str = "A test function.",
    is_pure: bool = False,
    is_static: bool = False,
    params: list | None = None,
) -> dict:
    """Build a mock engine function dict."""
    return {
        "name": name,
        "class_name": class_name,
        "category": category,
        "description": description,
        "is_pure": is_pure,
        "is_static": is_static,
        "params": params or [],
    }


MOCK_ENGINE_RESPONSE = {
    "status": "ok",
    "message": "Found 5 callable functions (5 shown)",
    "total": 5,
    "shown": 5,
    "functions": [
        _make_engine_func(
            name="SetFloatParameter",
            class_name="UAudioComponent",
            category="Audio|Parameters",
            description="Sets a float parameter on a playing sound.",
            params=[
                {"name": "InName", "type": "FName", "direction": "in"},
                {"name": "InFloat", "type": "float", "direction": "in"},
                {"name": "ReturnValue", "type": "bool", "direction": "return"},
            ],
        ),
        _make_engine_func(
            name="PlaySound2D",
            class_name="UGameplayStatics",
            category="Audio",
            description="Plays a 2D sound.",
            is_static=True,
            params=[
                {"name": "WorldContextObject", "type": "UObject*", "direction": "in"},
                {"name": "Sound", "type": "USoundBase*", "direction": "in"},
                {"name": "VolumeMultiplier", "type": "float", "direction": "in", "default": "1.0"},
            ],
        ),
        _make_engine_func(
            name="GetAudioVolume",
            class_name="UAudioComponent",
            category="Audio|Volume",
            description="Gets the current volume.",
            is_pure=True,
            params=[
                {"name": "ReturnValue", "type": "float", "direction": "return"},
            ],
        ),
        _make_engine_func(
            name="SetRTPCValue",
            class_name="UAkComponent",
            category="Wwise|RTPC",
            description="Sets an RTPC value on the Wwise component.",
            params=[
                {"name": "RTPC", "type": "FString", "direction": "in"},
                {"name": "Value", "type": "float", "direction": "in"},
                {"name": "InterpolationTimeMs", "type": "int32", "direction": "in", "default": "0"},
            ],
        ),
        _make_engine_func(
            name="",
            class_name="",
            category="",
            description="",
            params=[],
        ),
    ],
}


# ---------------------------------------------------------------------------
# _engine_func_to_bp_scraped tests
# ---------------------------------------------------------------------------

class TestEngineFuncToBpScraped:
    def test_basic_conversion(self):
        func = _make_engine_func(
            name="PlaySound2D",
            class_name="UGameplayStatics",
            category="Audio",
            description="Plays a 2D sound.",
            params=[
                {"name": "Sound", "type": "USoundBase*", "direction": "in"},
                {"name": "Volume", "type": "float", "direction": "in", "default": "1.0"},
            ],
        )
        result = _engine_func_to_bp_scraped(func)
        assert result is not None
        assert result["name"] == "PlaySound2D"
        assert result["target"] == "UGameplayStatics"
        assert result["category"] == "Audio"
        assert result["description"] == "Plays a 2D sound."
        assert len(result["inputs"]) == 2
        assert result["inputs"][0]["name"] == "Sound"
        assert result["inputs"][0]["type"] == "USoundBase*"
        assert result["inputs"][1]["default"] == "1.0"

    def test_empty_name_returns_none(self):
        func = _make_engine_func(name="")
        result = _engine_func_to_bp_scraped(func)
        assert result is None

    def test_return_param_goes_to_outputs(self):
        func = _make_engine_func(
            name="GetVolume",
            params=[
                {"name": "ReturnValue", "type": "float", "direction": "return"},
            ],
        )
        result = _engine_func_to_bp_scraped(func)
        assert result is not None
        assert len(result["inputs"]) == 0
        assert len(result["outputs"]) == 1
        assert result["outputs"][0]["name"] == "ReturnValue"
        assert result["outputs"][0]["type"] == "float"

    def test_out_param_goes_to_outputs(self):
        func = _make_engine_func(
            name="GetParams",
            params=[
                {"name": "InName", "type": "FName", "direction": "in"},
                {"name": "OutValue", "type": "float", "direction": "out"},
            ],
        )
        result = _engine_func_to_bp_scraped(func)
        assert result is not None
        assert len(result["inputs"]) == 1
        assert len(result["outputs"]) == 1
        assert result["outputs"][0]["name"] == "OutValue"

    def test_no_params_empty_lists(self):
        func = _make_engine_func(name="DoSomething", params=[])
        result = _engine_func_to_bp_scraped(func)
        assert result is not None
        assert result["inputs"] == []
        assert result["outputs"] == []

    def test_scraped_format_has_required_fields(self):
        func = _make_engine_func(name="TestFunc")
        result = _engine_func_to_bp_scraped(func)
        assert result is not None
        required_fields = ["name", "target", "category", "description",
                           "inputs", "outputs", "slug", "ue_version", "path"]
        for field in required_fields:
            assert field in result, "Missing field: {}".format(field)


# ---------------------------------------------------------------------------
# bp_sync_from_engine tool tests
# ---------------------------------------------------------------------------

class TestBpSyncFromEngine:
    def test_sync_basic(self, ue5_conn, mock_ue5_plugin):
        """Sync with mock response, verify counts."""
        mock_ue5_plugin.set_response("list_blueprint_functions", MOCK_ENGINE_RESPONSE)

        result = json.loads(bp_sync_from_engine())
        assert result["status"] == "ok"
        assert result["total"] == 5
        # Empty-name func is skipped, so converted should be 4
        assert result["converted"] == 4
        assert result["class_count"] > 0

    def test_sync_returns_classes(self, ue5_conn, mock_ue5_plugin):
        """Sync result should include class breakdown."""
        mock_ue5_plugin.set_response("list_blueprint_functions", MOCK_ENGINE_RESPONSE)
        result = json.loads(bp_sync_from_engine())
        assert result["status"] == "ok"
        assert "classes" in result
        assert isinstance(result["classes"], dict)
        assert "UAudioComponent" in result["classes"]

    def test_sync_audio_only_forwarded(self, ue5_conn, mock_ue5_plugin):
        """audio_only param should be forwarded to the engine command."""
        mock_ue5_plugin.set_response("list_blueprint_functions", {
            "status": "ok", "functions": [], "total": 0, "shown": 0,
            "message": "Found 0 callable functions (0 shown)",
        })
        json.loads(bp_sync_from_engine(audio_only=True))
        cmd = mock_ue5_plugin.commands[-1]
        assert cmd["action"] == "list_blueprint_functions"
        assert cmd["audio_only"] is True

    def test_sync_filter_forwarded(self, ue5_conn, mock_ue5_plugin):
        """filter param should be forwarded to the engine command."""
        mock_ue5_plugin.set_response("list_blueprint_functions", {
            "status": "ok", "functions": [], "total": 0, "shown": 0,
            "message": "Found 0 callable functions (0 shown)",
        })
        json.loads(bp_sync_from_engine(filter="Sound"))
        cmd = mock_ue5_plugin.commands[-1]
        assert cmd["filter"] == "Sound"

    def test_sync_class_filter_forwarded(self, ue5_conn, mock_ue5_plugin):
        """class_filter param should be forwarded."""
        mock_ue5_plugin.set_response("list_blueprint_functions", {
            "status": "ok", "functions": [], "total": 0, "shown": 0,
            "message": "Found 0 callable functions (0 shown)",
        })
        json.loads(bp_sync_from_engine(class_filter="UAudioComponent"))
        cmd = mock_ue5_plugin.commands[-1]
        assert cmd["class_filter"] == "UAudioComponent"

    def test_sync_not_connected(self):
        """Should return error when not connected to UE5 plugin."""
        ue5_module._connection = None
        result = json.loads(bp_sync_from_engine())
        assert result["status"] == "error"
        assert "Not connected" in result["message"]
        ue5_module._connection = None

    def test_sync_empty_response(self, ue5_conn, mock_ue5_plugin):
        """Empty function list from engine should return gracefully."""
        mock_ue5_plugin.set_response("list_blueprint_functions", {
            "status": "ok", "functions": [], "total": 0, "shown": 0,
            "message": "Found 0 callable functions (0 shown)",
        })
        result = json.loads(bp_sync_from_engine())
        assert result["status"] == "ok"
        assert result["total"] == 0

    def test_sync_error_response(self, ue5_conn, mock_ue5_plugin):
        """Engine error should be forwarded."""
        mock_ue5_plugin.set_response("list_blueprint_functions", {
            "status": "error", "message": "UClass iteration failed",
        })
        result = json.loads(bp_sync_from_engine())
        assert result["status"] == "error"
        assert "UClass" in result["message"]

    def test_sync_skips_empty_name(self, ue5_conn, mock_ue5_plugin):
        """Functions with empty names should be skipped."""
        mock_ue5_plugin.set_response("list_blueprint_functions", MOCK_ENGINE_RESPONSE)
        result = json.loads(bp_sync_from_engine())
        assert result["status"] == "ok"
        # 5 total, but one has empty name
        assert result["converted"] == 4

    def test_sync_with_db_update(self, ue5_conn, mock_ue5_plugin, knowledge_db):
        """With update_db=True, should upsert into SQLite."""
        mock_ue5_plugin.set_response("list_blueprint_functions", MOCK_ENGINE_RESPONSE)
        result = json.loads(bp_sync_from_engine(update_db=True))
        assert result["status"] == "ok"
        assert result["db_updated"] == 4

        # Verify data is in DB
        rows = knowledge_db.query_blueprint_scraped(name="SetFloatParameter")
        assert len(rows) == 1
        assert rows[0]["target"] == "UAudioComponent"

    def test_sync_db_failure_returns_error(self, ue5_conn, mock_ue5_plugin, monkeypatch):
        """When update_db=True and DB fails, should return error with db_error."""
        mock_ue5_plugin.set_response("list_blueprint_functions", MOCK_ENGINE_RESPONSE)

        def _fail_get_db():
            raise RuntimeError("DB connection failed")

        monkeypatch.setattr(
            "ue_audio_mcp.knowledge.db.get_knowledge_db", _fail_get_db,
        )
        result = json.loads(bp_sync_from_engine(update_db=True))
        assert result["status"] == "error"
        assert "DB update failed" in result["message"]


# ---------------------------------------------------------------------------
# Standalone script diff logic
# ---------------------------------------------------------------------------

class TestScriptDiffLogic:
    def test_build_diff_new_function(self):
        """New functions should appear in diff."""
        from scripts.sync_bp_from_engine import _build_diff

        engine_funcs = [_make_engine_func(
            name="BrandNewAudioFunc",
            class_name="UNewAudioClass",
            category="Audio",
            params=[{"name": "Volume", "type": "float", "direction": "in"}],
        )]
        diff = _build_diff(engine_funcs, {})
        assert diff["new_count"] == 1
        new_names = [f["name"] for f in diff["new_funcs"]]
        assert "BrandNewAudioFunc" in new_names

    def test_build_diff_pin_changes(self):
        """Parameter differences should be detected."""
        from scripts.sync_bp_from_engine import _build_diff

        existing = {
            "SetFloat": {
                "name": "SetFloat",
                "inputs": [{"name": "Value", "type": "float"}],
                "outputs": [],
            },
        }
        engine_funcs = [_make_engine_func(
            name="SetFloat",
            params=[
                {"name": "Value", "type": "float", "direction": "in"},
                {"name": "NewParam", "type": "int32", "direction": "in"},
            ],
        )]
        diff = _build_diff(engine_funcs, existing)
        assert diff["total_pin_changes"] > 0

    def test_build_diff_empty_engine(self):
        """Empty engine list should produce empty diff."""
        from scripts.sync_bp_from_engine import _build_diff

        diff = _build_diff([], {"Func1": {"inputs": [], "outputs": []}})
        assert diff["new_count"] == 0
        assert diff["updated_count"] == 0
