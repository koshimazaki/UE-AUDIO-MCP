"""Tests for MetaSounds knowledge query tools."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.metasounds import (
    ms_list_nodes,
    ms_node_info,
    ms_search_nodes,
    ms_list_categories,
    _get_search_index,
    _reset_search_index,
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


def test_search_index_cached(knowledge_db):
    _reset_search_index()
    idx1 = _get_search_index()
    idx2 = _get_search_index()
    assert idx1 is idx2
    _reset_search_index()


def test_reset_search_index(knowledge_db):
    _reset_search_index()
    idx1 = _get_search_index()
    _reset_search_index()
    idx2 = _get_search_index()
    assert idx1 is not idx2
    _reset_search_index()


def test_ms_list_nodes_by_category_and_tag(knowledge_db):
    result = _parse(ms_list_nodes(category="Filters", tag="lowpass"))
    assert result["status"] == "ok"
    assert result["count"] >= 1
    for n in result["nodes"]:
        assert n["category"] == "Filters"
        assert "lowpass" in [t.lower() for t in n["tags"]]
