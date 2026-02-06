"""Tests for MetaSounds graph MCP tools."""

from __future__ import annotations

import json

import pytest

from ue_audio_mcp.tools.ms_graph import (
    ms_validate_graph,
    ms_graph_to_commands,
    ms_graph_from_template,
)


def _parse(result: str) -> dict:
    return json.loads(result)


def _valid_spec_json():
    return json.dumps({
        "name": "TestSound",
        "asset_type": "Source",
        "interfaces": ["UE.Source.OneShot"],
        "inputs": [{"name": "OnPlay", "type": "Trigger"}],
        "outputs": [
            {"name": "Out Mono", "type": "Audio"},
            {"name": "Out Stereo L", "type": "Audio"},
            {"name": "Out Stereo R", "type": "Audio"},
            {"name": "OnFinished", "type": "Trigger"},
        ],
        "nodes": [
            {"id": "sine1", "node_type": "Sine", "defaults": {"Frequency": 440.0}, "position": [100, 100]},
        ],
        "connections": [
            {"from_node": "sine1", "from_pin": "Audio", "to_node": "__graph__", "to_pin": "Out Mono"},
        ],
    })


def test_validate_graph_valid(knowledge_db):
    result = _parse(ms_validate_graph(_valid_spec_json()))
    assert result["status"] == "ok"
    assert result["valid"] is True
    assert result["error_count"] == 0


def test_validate_graph_invalid_json(knowledge_db):
    result = _parse(ms_validate_graph("not-json"))
    assert result["status"] == "error"
    assert "Invalid" in result["message"]


def test_validate_graph_bad_node(knowledge_db):
    spec = json.loads(_valid_spec_json())
    spec["nodes"] = [{"id": "x", "node_type": "FakeNode", "defaults": {}, "position": [0, 0]}]
    spec["connections"] = []
    result = _parse(ms_validate_graph(json.dumps(spec)))
    assert result["status"] == "ok"
    assert result["valid"] is False
    assert result["error_count"] > 0


def test_graph_to_commands_valid(knowledge_db):
    result = _parse(ms_graph_to_commands(_valid_spec_json()))
    assert result["status"] == "ok"
    assert result["command_count"] > 0
    actions = [c["action"] for c in result["commands"]]
    assert "create_builder" in actions
    assert "build_to_asset" in actions


def test_graph_to_commands_invalid(knowledge_db):
    spec = json.loads(_valid_spec_json())
    spec["nodes"] = [{"id": "x", "node_type": "FakeNode", "defaults": {}, "position": [0, 0]}]
    spec["connections"] = []
    result = _parse(ms_graph_to_commands(json.dumps(spec)))
    assert result["status"] == "error"
    assert "validation error" in result["message"]


def test_graph_to_commands_invalid_json(knowledge_db):
    result = _parse(ms_graph_to_commands("not-json"))
    assert result["status"] == "error"


def test_graph_from_template_unknown(knowledge_db):
    result = _parse(ms_graph_from_template("nonexistent"))
    assert result["status"] == "error"
    assert "Unknown template" in result["message"]


def test_graph_from_template_invalid_params(knowledge_db):
    result = _parse(ms_graph_from_template("gunshot", "not-json"))
    assert result["status"] == "error"
    assert "Invalid params" in result["message"]


# -- Step 5: param override tests ------------------------------------------

def test_graph_from_template_with_params(knowledge_db):
    result = _parse(ms_graph_from_template(
        "gunshot", '{"adsr.Attack": 0.01, "random_pitch.Min": -2.0}'
    ))
    assert result["status"] == "ok"
    spec = result["graph_spec"]
    nodes_by_id = {n["id"]: n for n in spec["nodes"]}
    assert nodes_by_id["adsr"]["defaults"]["Attack"] == 0.01
    assert nodes_by_id["random_pitch"]["defaults"]["Min"] == -2.0


def test_graph_from_template_unknown_param_ignored(knowledge_db):
    result = _parse(ms_graph_from_template(
        "gunshot", '{"nonexistent_node.Foo": 99}'
    ))
    assert result["status"] == "ok"
    assert result["valid"] is True


# -- Step 6: positive template tests ---------------------------------------

ALL_TEMPLATES = ["gunshot", "footsteps", "ambient", "spatial", "ui_sound", "weather"]


@pytest.mark.parametrize("template_name", ALL_TEMPLATES)
def test_template_loads_and_validates(knowledge_db, template_name):
    result = _parse(ms_graph_from_template(template_name))
    assert result["status"] == "ok"
    assert result["template"] == template_name
    spec = result["graph_spec"]
    assert spec["name"]
    assert spec["asset_type"] in ("Source", "Patch", "Preset")
    assert len(spec["nodes"]) >= 1
    assert len(spec["connections"]) >= 1
    assert result["valid"] is True, "Validation errors: {}".format(result["validation_errors"])


def test_template_to_commands_roundtrip(knowledge_db):
    """Every template should produce valid Builder API commands."""
    for template_name in ALL_TEMPLATES:
        tmpl_result = _parse(ms_graph_from_template(template_name))
        assert tmpl_result["valid"] is True, "{} invalid".format(template_name)
        spec_json = json.dumps(tmpl_result["graph_spec"])
        cmd_result = _parse(ms_graph_to_commands(spec_json))
        assert cmd_result["status"] == "ok", "{} commands failed".format(template_name)
        actions = [c["action"] for c in cmd_result["commands"]]
        assert actions[0] == "create_builder"
        assert actions[-1] == "build_to_asset"
