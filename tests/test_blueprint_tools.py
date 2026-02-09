"""Tests for Blueprint tools — bp_search, bp_node_info, bp_list_categories, bp_call_function, bp_scan_blueprint."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.blueprints import (
    bp_call_function,
    bp_list_assets,
    bp_list_categories,
    bp_node_info,
    bp_scan_blueprint,
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
    # Use a node that exists in bp_node_specs.json but NOT in curated data
    result = json.loads(bp_node_info("AIMoveTo"))
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


# -- bp_list_assets ----------------------------------------------------------

_LIST_ASSETS_RESPONSE = {
    "status": "ok",
    "message": "Found 42 Blueprint assets under '/Game/' (42 shown)",
    "total": 42,
    "shown": 42,
    "path": "/Game/",
    "class_filter": "Blueprint",
    "assets": [
        {"path": "/Game/BP_Char.BP_Char", "name": "BP_Char", "class": "Blueprint", "package_path": "/Game"},
        {"path": "/Game/BP_Enemy.BP_Enemy", "name": "BP_Enemy", "class": "Blueprint", "package_path": "/Game"},
    ],
}


def test_list_assets_success(ue5_conn, mock_ue5_plugin, knowledge_db):
    mock_ue5_plugin.set_response("list_assets", _LIST_ASSETS_RESPONSE)
    result = json.loads(bp_list_assets("Blueprint", "/Game/"))
    assert result["status"] == "ok"
    assert result["total"] == 42
    assert len(result["assets"]) == 2
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "list_assets"
    assert cmd["class_filter"] == "Blueprint"
    assert cmd["recursive_classes"] is True


def test_list_assets_metasounds(ue5_conn, mock_ue5_plugin, knowledge_db):
    mock_ue5_plugin.set_response("list_assets", {
        "status": "ok", "total": 5, "shown": 5, "assets": [],
    })
    result = json.loads(bp_list_assets("MetaSoundSource"))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["class_filter"] == "MetaSoundSource"


def test_list_assets_not_connected(knowledge_db):
    import ue_audio_mcp.ue5_connection as ue5_module
    ue5_module._connection = None
    result = json.loads(bp_list_assets())
    assert result["status"] == "error"
    assert "Not connected" in result["message"]
    ue5_module._connection = None


def test_list_assets_error_response(ue5_conn, mock_ue5_plugin, knowledge_db):
    mock_ue5_plugin.set_response("list_assets", {
        "status": "error", "message": "Unknown class_filter 'Bogus'",
    })
    result = json.loads(bp_list_assets("Bogus"))
    assert result["status"] == "error"
    assert "Unknown" in result["message"]


# -- bp_scan_blueprint -------------------------------------------------------

_SCAN_RESPONSE = {
    "status": "ok",
    "message": "Scanned 'BP_Character': 2 graphs, 45 nodes (3 audio-relevant)",
    "asset_path": "/Game/BP_Character",
    "blueprint_name": "BP_Character",
    "parent_class": "Character",
    "blueprint_type": "Blueprint",
    "total_nodes": 45,
    "graphs": [
        {
            "name": "EventGraph",
            "type": "ubergraph",
            "total_nodes": 40,
            "shown_nodes": 40,
            "nodes": [
                {
                    "type": "Event",
                    "title": "Event BeginPlay",
                    "event_name": "ReceiveBeginPlay",
                    "audio_relevant": False,
                    "x": 0, "y": 0,
                },
                {
                    "type": "CallFunction",
                    "title": "Play Sound at Location",
                    "function_name": "PlaySoundAtLocation",
                    "function_class": "GameplayStatics",
                    "audio_relevant": True,
                    "x": 200, "y": 100,
                },
            ],
        },
    ],
    "audio_summary": {
        "has_audio": True,
        "audio_node_count": 3,
        "audio_functions": ["PlaySoundAtLocation", "PostEvent", "SetRTPCValue"],
    },
}


def test_scan_blueprint_success(ue5_conn, mock_ue5_plugin, knowledge_db):
    mock_ue5_plugin.set_response("scan_blueprint", _SCAN_RESPONSE)
    result = json.loads(bp_scan_blueprint("/Game/BP_Character"))
    assert result["status"] == "ok"
    assert result["blueprint_name"] == "BP_Character"
    assert result["parent_class"] == "Character"
    assert result["total_nodes"] == 45
    assert len(result["graphs"]) == 1
    assert result["graphs"][0]["name"] == "EventGraph"
    assert result["audio_summary"]["has_audio"] is True
    assert "PlaySoundAtLocation" in result["audio_summary"]["audio_functions"]
    # Verify command sent correctly
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "scan_blueprint"
    assert cmd["asset_path"] == "/Game/BP_Character"
    assert cmd["audio_only"] is False
    assert cmd["include_pins"] is False


def test_scan_blueprint_audio_only(ue5_conn, mock_ue5_plugin, knowledge_db):
    mock_ue5_plugin.set_response("scan_blueprint", _SCAN_RESPONSE)
    result = json.loads(bp_scan_blueprint("/Game/BP_Character", audio_only=True))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["audio_only"] is True


def test_scan_blueprint_with_pins(ue5_conn, mock_ue5_plugin, knowledge_db):
    mock_ue5_plugin.set_response("scan_blueprint", _SCAN_RESPONSE)
    result = json.loads(bp_scan_blueprint("/Game/BP_Character", include_pins=True))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["include_pins"] is True


def test_scan_blueprint_empty_path(ue5_conn, knowledge_db):
    result = json.loads(bp_scan_blueprint(""))
    assert result["status"] == "error"
    assert "empty" in result["message"].lower()


def test_scan_blueprint_not_connected(knowledge_db):
    import ue_audio_mcp.ue5_connection as ue5_module
    ue5_module._connection = None
    result = json.loads(bp_scan_blueprint("/Game/BP_Character"))
    assert result["status"] == "error"
    assert "Not connected" in result["message"]
    ue5_module._connection = None


def test_scan_blueprint_error_response(ue5_conn, mock_ue5_plugin, knowledge_db):
    mock_ue5_plugin.set_response("scan_blueprint", {
        "status": "error",
        "message": "Asset '/Game/Missing' not found",
    })
    result = json.loads(bp_scan_blueprint("/Game/Missing"))
    assert result["status"] == "error"
    assert "not found" in result["message"]
