"""Tests for MetaSounds knowledge query tools."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.metasounds import (
    ms_list_nodes,
    ms_node_info,
    ms_search_nodes,
    ms_list_categories,
)


def _parse(result: str) -> dict:
    return json.loads(result)


def test_ms_list_nodes_all(knowledge_db):
    result = _parse(ms_list_nodes())
    assert result["status"] == "ok"
    assert result["count"] >= 100


def test_ms_list_nodes_by_category(knowledge_db):
    result = _parse(ms_list_nodes(category="Filters"))
    assert result["status"] == "ok"
    assert result["count"] >= 5
    assert all(n["category"] == "Filters" for n in result["nodes"])


def test_ms_list_nodes_by_tag(knowledge_db):
    result = _parse(ms_list_nodes(tag="oscillator"))
    assert result["status"] == "ok"
    assert result["count"] >= 1


def test_ms_node_info_found(knowledge_db):
    result = _parse(ms_node_info("Sine"))
    assert result["status"] == "ok"
    assert result["node"]["name"] == "Sine"
    assert len(result["node"]["inputs"]) > 0
    assert len(result["node"]["outputs"]) > 0


def test_ms_node_info_not_found(knowledge_db):
    result = _parse(ms_node_info("NonExistentNode"))
    assert result["status"] == "error"
    assert "not found" in result["message"]


def test_ms_node_info_suggests(knowledge_db):
    result = _parse(ms_node_info("biquad"))
    assert result["status"] == "error"
    assert "Biquad Filter" in result["message"]


def test_ms_search_nodes(knowledge_db):
    result = _parse(ms_search_nodes("delay echo"))
    assert result["status"] == "ok"
    assert result["count"] > 0
    names = [r["name"] for r in result["results"]]
    assert "Delay" in names


def test_ms_list_categories(knowledge_db):
    result = _parse(ms_list_categories())
    assert result["status"] == "ok"
    assert result["count"] == 16
    assert result["total_nodes"] >= 100
    assert "Filters" in result["categories"]
    assert "Generators" in result["categories"]
