"""Tests for Blueprint tools — bp_search, bp_node_info, bp_list_categories, bp_call_function."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.blueprints import (
    bp_call_function,
    bp_list_categories,
    bp_node_info,
    bp_search,
)


# -- bp_search ---------------------------------------------------------------

def test_search_by_name(knowledge_db):
    result = json.loads(bp_search("Play"))
    assert result["status"] == "ok"
    assert result["count"] > 0
    names = [r["name"] for r in result["results"]]
    assert any("Play" in n for n in names)


def test_search_by_description(knowledge_db):
    result = json.loads(bp_search("sound"))
    assert result["status"] == "ok"
    assert result["count"] > 0


def test_search_with_category(knowledge_db):
    result = json.loads(bp_search("Play", category="audio"))
    assert result["status"] == "ok"
    # Every result should have a category related to "audio"
    for r in result["results"]:
        cat = r.get("category", "").lower()
        source = r.get("source", "")
        # Curated results are pre-filtered by SQL; scraped filtered in Python
        if source == "curated":
            assert "audio" in cat, "Curated result '{}' has non-audio category '{}'".format(
                r["name"], cat
            )


def test_search_empty_query(knowledge_db):
    result = json.loads(bp_search(""))
    assert result["status"] == "error"
    assert "empty" in result["message"].lower()


def test_search_no_results(knowledge_db):
    result = json.loads(bp_search("zzzznonexistentnodezzz"))
    assert result["status"] == "ok"
    assert result["count"] == 0


def test_search_curated_only(knowledge_db):
    result = json.loads(bp_search("Play", source="curated"))
    assert result["status"] == "ok"
    for r in result["results"]:
        assert r.get("source") == "curated"


def test_search_scraped_only(knowledge_db):
    result = json.loads(bp_search("Sound", source="scraped"))
    assert result["status"] == "ok"
    for r in result["results"]:
        assert r.get("source") == "scraped"


def test_search_invalid_source(knowledge_db):
    result = json.loads(bp_search("Play", source="bogus"))
    assert result["status"] == "error"
    assert "Invalid source" in result["message"]


# -- bp_node_info ------------------------------------------------------------

def test_node_info_scraped(knowledge_db):
    """Scraped nodes should include inputs/outputs pin specs."""
    # Use a node we know exists in the scraped sample data
    result = json.loads(bp_node_info("CreateSound2D"))
    assert result["status"] == "ok"
    assert result["source"] == "scraped"
    assert "inputs" in result
    assert isinstance(result["inputs"], list)


def test_node_info_curated(knowledge_db):
    """Curated nodes should include params/returns."""
    # PlaySoundAtLocation is in curated but NOT in scraped data
    result = json.loads(bp_node_info("PlaySoundAtLocation"))
    assert result["status"] == "ok"
    assert result["source"] == "curated"


def test_node_info_not_found(knowledge_db):
    result = json.loads(bp_node_info("ZZZNonexistentNodeZZZ"))
    assert result["status"] == "error"
    assert "not found" in result["message"]


# -- bp_list_categories ------------------------------------------------------

def test_list_categories_all(knowledge_db):
    result = json.loads(bp_list_categories("all"))
    assert result["status"] == "ok"
    assert result["count"] > 0
    assert all("category" in c and "count" in c for c in result["categories"])


def test_list_categories_scraped(knowledge_db):
    result = json.loads(bp_list_categories("scraped"))
    assert result["status"] == "ok"
    # Scraped data uses target field as category
    assert result["count"] >= 1


# -- bp_call_function --------------------------------------------------------

def test_call_function_success(ue5_conn, mock_ue5_plugin, knowledge_db):
    mock_ue5_plugin.set_response("call_function", {"status": "ok", "result": "done"})
    result = json.loads(bp_call_function("PlaySound2D", '{"sound": "test.wav"}'))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "call_function"
    assert cmd["function"] == "PlaySound2D"
    assert cmd["args"]["sound"] == "test.wav"


def test_call_function_not_connected(knowledge_db):
    import ue_audio_mcp.ue5_connection as ue5_module
    ue5_module._connection = None
    result = json.loads(bp_call_function("PlaySound2D"))
    assert result["status"] == "error"
    assert "Not connected" in result["message"]
    ue5_module._connection = None


def test_call_function_invalid_json(ue5_conn, knowledge_db):
    result = json.loads(bp_call_function("PlaySound2D", "not json"))
    assert result["status"] == "error"
    assert "Invalid" in result["message"]
