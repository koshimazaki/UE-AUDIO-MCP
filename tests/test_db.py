"""Tests for SQLite knowledge database + embedding search."""

from __future__ import annotations

import json

from ue_audio_mcp.knowledge.db import KnowledgeDB


def test_insert_and_query_node():
    db = KnowledgeDB(":memory:")
    db.insert_node({
        "name": "Sine",
        "category": "Generators",
        "description": "Sine wave oscillator",
        "inputs": [{"name": "Frequency", "type": "Float", "required": True}],
        "outputs": [{"name": "Audio", "type": "Audio"}],
        "tags": ["oscillator", "generator"],
        "complexity": 1,
    })
    nodes = db.query_nodes(name="Sine")
    assert len(nodes) == 1
    assert nodes[0]["name"] == "Sine"
    assert nodes[0]["inputs"][0]["type"] == "Float"
    db.close()


def test_query_nodes_by_category():
    db = KnowledgeDB(":memory:")
    for name in ("Sine", "Saw"):
        db.insert_node({
            "name": name, "category": "Generators", "description": name,
            "inputs": [], "outputs": [], "tags": [], "complexity": 1,
        })
    db.insert_node({
        "name": "Delay", "category": "Delays", "description": "Delay",
        "inputs": [], "outputs": [], "tags": [], "complexity": 2,
    })
    assert len(db.query_nodes(category="Generators")) == 2
    assert len(db.query_nodes(category="Delays")) == 1
    db.close()


def test_query_nodes_by_tag():
    db = KnowledgeDB(":memory:")
    db.insert_node({
        "name": "Biquad Filter", "category": "Filters",
        "description": "IIR filter",
        "inputs": [], "outputs": [],
        "tags": ["filter", "underwater", "lowpass"],
        "complexity": 2,
    })
    results = db.query_nodes(tag="underwater")
    assert len(results) == 1
    assert results[0]["name"] == "Biquad Filter"
    assert len(db.query_nodes(tag="nonexistent")) == 0
    db.close()


def test_count_nodes_by_category():
    db = KnowledgeDB(":memory:")
    for name in ("Sine", "Saw", "Square"):
        db.insert_node({
            "name": name, "category": "Generators", "description": name,
            "inputs": [], "outputs": [], "tags": [], "complexity": 1,
        })
    counts = db.count_nodes_by_category()
    assert counts["Generators"] == 3
    db.close()


def test_insert_and_query_waapi():
    db = KnowledgeDB(":memory:")
    db.insert_waapi({
        "uri": "ak.wwise.core.object.create",
        "namespace": "core.object",
        "operation": "create",
        "description": "Create a Wwise object",
    })
    results = db.query_waapi(namespace="core.object")
    assert len(results) == 1
    assert results[0]["operation"] == "create"
    results = db.query_waapi(operation="create")
    assert len(results) == 1
    db.close()


def test_error_patterns_increment():
    db = KnowledgeDB(":memory:")
    db.store_error("sig1", "apply fix A")
    db.store_error("sig1", "apply fix A")
    db.store_error("sig1", "apply fix B")
    errors = db.query_errors("sig1")
    assert len(errors) == 2
    fix_a = [e for e in errors if e["fix"] == "apply fix A"][0]
    assert fix_a["success_count"] == 2
    db.close()


def test_table_counts():
    db = KnowledgeDB(":memory:")
    counts = db.table_counts()
    assert all(v == 0 for v in counts.values())
    assert "metasound_nodes" in counts
    assert "blueprint_audio" in counts
    assert "blueprint_nodes_scraped" in counts
    db.close()


def test_is_seeded():
    db = KnowledgeDB(":memory:")
    assert db.is_seeded() is False
    db.insert_node({
        "name": "Test", "category": "Test", "description": "Test",
        "inputs": [], "outputs": [], "tags": [], "complexity": 1,
    })
    assert db.is_seeded() is True
    db.close()


def test_seed_database():
    from ue_audio_mcp.knowledge.seed import seed_database
    db = KnowledgeDB(":memory:")
    counts = seed_database(db)
    assert counts["metasound_nodes"] >= 100
    assert counts["waapi_functions"] >= 20
    assert counts["wwise_types"] >= 15
    assert counts["audio_patterns"] == 6
    assert counts["blueprint_audio"] >= 20
    assert counts["blueprint_nodes_scraped"] >= 40  # 55 curated audio functions
    assert sum(counts.values()) >= 300
    db.close()


def test_wwise_type_descriptions_not_generic():
    from ue_audio_mcp.knowledge.seed import seed_database
    db = KnowledgeDB(":memory:")
    seed_database(db)
    rows = db._fetch("SELECT type_name, description FROM wwise_types")
    for row in rows:
        assert not row["description"].startswith("Wwise "), (
            "Generic description for {}: {}".format(row["type_name"], row["description"])
        )
    db.close()


def test_like_escape_percent():
    db = KnowledgeDB(":memory:")
    db.insert_node({
        "name": "Test%Node", "category": "Generators",
        "description": "Has percent in name",
        "inputs": [], "outputs": [], "tags": ["weird%tag"], "complexity": 1,
    })
    db.insert_node({
        "name": "TestXNode", "category": "Generators",
        "description": "Normal node",
        "inputs": [], "outputs": [], "tags": ["normal"], "complexity": 1,
    })
    # A naive LIKE with unescaped % would match both; escaped should match only the literal %
    results = db.query_nodes(tag="weird%tag")
    assert len(results) == 1
    assert results[0]["name"] == "Test%Node"
    db.close()


def test_like_escape_underscore():
    db = KnowledgeDB(":memory:")
    db.insert_node({
        "name": "A_B", "category": "Filters",
        "description": "Has underscore",
        "inputs": [], "outputs": [], "tags": ["a_b"], "complexity": 1,
    })
    db.insert_node({
        "name": "AXB", "category": "Filters",
        "description": "No underscore",
        "inputs": [], "outputs": [], "tags": ["axb"], "complexity": 1,
    })
    # Unescaped _ matches any char; escaped should only match literal _
    results = db.query_nodes(tag="a_b")
    assert len(results) == 1
    assert results[0]["name"] == "A_B"
    db.close()


def test_insert_and_query_blueprint_scraped():
    db = KnowledgeDB(":memory:")
    db.insert_blueprint_scraped({
        "name": "PlaySound2D",
        "target": "Gameplay Statics",
        "category": "audio",
        "description": "Play a 2D sound",
        "inputs": [{"type": "exec", "name": "In"}, {"type": "object", "name": "Sound"}],
        "outputs": [{"type": "exec", "name": "Out"}],
    })
    rows = db.query_blueprint_scraped(name="PlaySound2D")
    assert len(rows) == 1
    assert rows[0]["target"] == "Gameplay Statics"
    assert len(rows[0]["inputs"]) == 2
    db.close()


def test_query_scraped_by_category():
    db = KnowledgeDB(":memory:")
    db.insert_blueprint_scraped({"name": "NodeA", "category": "audio"})
    db.insert_blueprint_scraped({"name": "NodeB", "category": "physics"})
    rows = db.query_blueprint_scraped(category="audio")
    assert len(rows) == 1
    assert rows[0]["name"] == "NodeA"
    db.close()


def test_query_scraped_by_target():
    db = KnowledgeDB(":memory:")
    db.insert_blueprint_scraped({"name": "NodeA", "target": "Audio Component"})
    db.insert_blueprint_scraped({"name": "NodeB", "target": "Gameplay Statics"})
    rows = db.query_blueprint_scraped(target="Audio Component")
    assert len(rows) == 1
    assert rows[0]["name"] == "NodeA"
    db.close()


def test_search_blueprint_scraped():
    db = KnowledgeDB(":memory:")
    db.insert_blueprint_scraped({"name": "PlaySound2D", "description": "Play a 2D sound"})
    db.insert_blueprint_scraped({"name": "SetVolume", "description": "Set audio volume"})
    results = db.search_blueprint_scraped("sound")
    assert len(results) == 1
    assert results[0]["name"] == "PlaySound2D"
    db.close()


def test_table_counts_includes_scraped():
    db = KnowledgeDB(":memory:")
    counts = db.table_counts()
    assert "blueprint_nodes_scraped" in counts
    assert counts["blueprint_nodes_scraped"] == 0
    db.insert_blueprint_scraped({"name": "TestNode"})
    counts = db.table_counts()
    assert counts["blueprint_nodes_scraped"] == 1
    db.close()


def test_seed_includes_scraped():
    from ue_audio_mcp.knowledge.seed import seed_database
    db = KnowledgeDB(":memory:")
    counts = seed_database(db)
    assert "blueprint_nodes_scraped" in counts
    assert counts["blueprint_nodes_scraped"] >= 40  # 55 curated audio functions
    db.close()


def test_embedding_search():
    from ue_audio_mcp.knowledge.metasound_nodes import METASOUND_NODES
    from ue_audio_mcp.knowledge.embeddings import build_index_from_nodes

    idx = build_index_from_nodes(METASOUND_NODES)
    results = idx.search("random variation")
    assert len(results) > 0
    names = [r[0] for r in results[:3]]
    assert any("Random" in n for n in names)

    results = idx.search("spatial 3d binaural")
    names = [r[0] for r in results[:3]]
    assert "ITD Panner" in names


def test_embedding_save_load(tmp_path):
    from ue_audio_mcp.knowledge.metasound_nodes import METASOUND_NODES
    from ue_audio_mcp.knowledge.embeddings import build_index_from_nodes, EmbeddingIndex

    idx = build_index_from_nodes(METASOUND_NODES)
    path = str(tmp_path / "test_index.npz")
    idx.save(path)

    loaded = EmbeddingIndex.load(path)
    original = idx.search("delay echo", top_k=3)
    reloaded = loaded.search("delay echo", top_k=3)
    assert original == reloaded
