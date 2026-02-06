"""MCP tools for MetaSounds knowledge queries.

4 tools: ms_list_nodes, ms_node_info, ms_search_nodes, ms_list_categories.
"""

from __future__ import annotations

import json

from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _ok, _error
from ue_audio_mcp.knowledge.metasound_nodes import (
    METASOUND_NODES,
    get_all_categories,
    get_nodes_by_category,
    get_nodes_by_tag,
    search_nodes,
)

_search_index = None


def _get_search_index():
    """Return the cached TF-IDF search index, building it once on first call."""
    global _search_index
    if _search_index is None:
        from ue_audio_mcp.knowledge.embeddings import build_index_from_nodes
        _search_index = build_index_from_nodes(METASOUND_NODES)
    return _search_index


def _reset_search_index():
    """Reset the cached search index (for testing)."""
    global _search_index
    _search_index = None


@mcp.tool()
def ms_list_nodes(
    category: str = "",
    tag: str = "",
) -> str:
    """List MetaSounds nodes, optionally filtered by category or tag.

    Args:
        category: Filter by category (e.g. "Filters", "Generators")
        tag: Filter by tag (e.g. "underwater", "oscillator")

    Returns:
        JSON with node list including name, category, description, and pin counts.
    """
    if category and tag:
        nodes = [
            n for n in get_nodes_by_category(category)
            if tag.lower() in [t.lower() for t in n.get("tags", [])]
        ]
    elif category:
        nodes = [n for n in get_nodes_by_category(category)]
    elif tag:
        nodes = [n for n in get_nodes_by_tag(tag)]
    else:
        nodes = list(METASOUND_NODES.values())

    summary = []
    for n in nodes:
        summary.append({
            "name": n["name"],
            "category": n["category"],
            "description": n["description"],
            "inputs": len(n.get("inputs", [])),
            "outputs": len(n.get("outputs", [])),
            "tags": n.get("tags", []),
        })

    return _ok({"count": len(summary), "nodes": summary})


@mcp.tool()
def ms_node_info(node_name: str) -> str:
    """Get full details for a specific MetaSounds node.

    Args:
        node_name: Exact node name (e.g. "Biquad Filter", "Wave Player (Mono)")

    Returns:
        JSON with complete node definition including all pins and defaults.
    """
    node = METASOUND_NODES.get(node_name)
    if not node:
        close_matches = search_nodes(node_name)[:5]
        suggestions = [m["name"] for m in close_matches]
        return _error(
            "Node '{}' not found. Did you mean: {}".format(
                node_name, ", ".join(suggestions) if suggestions else "(no matches)"
            )
        )
    return _ok({"node": node})


@mcp.tool()
def ms_search_nodes(query: str) -> str:
    """Semantic search for MetaSounds nodes by description or purpose.

    Uses TF-IDF embeddings for meaning-based search with tag fallback.
    Examples: "underwater effect", "random variation", "smooth transition"

    Args:
        query: Natural language search query

    Returns:
        JSON with ranked results (name, score, category, description).
    """
    try:
        idx = _get_search_index()
        results = idx.search(query, top_k=10)
        ranked = []
        for name, score in results:
            node = METASOUND_NODES.get(name, {})
            ranked.append({
                "name": name,
                "score": round(score, 4),
                "category": node.get("category", ""),
                "description": node.get("description", ""),
                "tags": node.get("tags", []),
            })
        return _ok({"query": query, "count": len(ranked), "results": ranked})
    except Exception:
        # Fallback to substring search if embeddings unavailable
        results = search_nodes(query)[:10]
        ranked = []
        for node in results:
            ranked.append({
                "name": node["name"],
                "score": 1.0,
                "category": node["category"],
                "description": node["description"],
                "tags": node.get("tags", []),
            })
        return _ok({"query": query, "count": len(ranked), "results": ranked})


@mcp.tool()
def ms_list_categories() -> str:
    """List all MetaSounds node categories with counts.

    Returns:
        JSON with category names and node counts.
    """
    cats = get_all_categories()
    return _ok({
        "count": len(cats),
        "total_nodes": sum(cats.values()),
        "categories": cats,
    })
