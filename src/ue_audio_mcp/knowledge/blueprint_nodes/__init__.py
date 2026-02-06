"""UE5 Blueprint node catalogue -- 1000+ verified nodes.

Package organized by domain. All data sourced from:
- Epic official UE5 C++ API (UKismetMathLibrary, UKismetSystemLibrary, etc.)
- dev.epicgames.com Blueprint API reference
- Audiokinetic Wwise UE5 Integration documentation

Sub-modules register nodes into BLUEPRINT_NODES via _n() at import time.
"""
from __future__ import annotations

from collections import Counter


BLUEPRINT_NODES: dict[str, dict] = {}


def _n(name: str, cls: str, cat: str, desc: str,
       tags: list[str] | None = None) -> None:
    """Register a Blueprint node."""
    BLUEPRINT_NODES[name] = {
        "name": name,
        "class_name": cls,
        "category": cat,
        "description": desc,
        "tags": tags or [],
    }


# Import all sub-modules -- each calls _n() at module scope
from ue_audio_mcp.knowledge.blueprint_nodes import (  # noqa: E402,F401
    flow_control,
    math_core,
    math_spatial,
    math_utility,
    string_array,
    audio,
    gameplay,
    collision_physics,
    input_nodes,
    rendering,
    system,
)


# ===================================================================
# QUERY HELPERS
# ===================================================================

def get_nodes_by_category(category: str) -> list[dict]:
    """Return all nodes in a category."""
    return [n for n in BLUEPRINT_NODES.values() if n["category"] == category]


def get_nodes_by_tag(tag: str) -> list[dict]:
    """Return all nodes with a specific tag."""
    return [n for n in BLUEPRINT_NODES.values() if tag in n["tags"]]


def search_nodes(query: str) -> list[dict]:
    """Substring search across name, tags, description. Ranked by relevance."""
    query_lower = query.lower()
    terms = query_lower.split()
    scored: list[tuple[int, dict]] = []
    for node in BLUEPRINT_NODES.values():
        score = 0
        name_lower = node["name"].lower()
        desc_lower = node["description"].lower()
        tags_str = " ".join(node["tags"])
        for term in terms:
            if term in name_lower:
                score += 3
            if term in tags_str:
                score += 2
            if term in desc_lower:
                score += 1
        if score > 0:
            scored.append((score, node))
    scored.sort(key=lambda x: -x[0])
    return [n for _, n in scored]


def get_all_categories() -> dict[str, int]:
    """Return {category: count} sorted by count descending."""
    cats = Counter(n["category"] for n in BLUEPRINT_NODES.values())
    return dict(cats.most_common())
