"""Blueprint tools — search, inspect, and execute Blueprint nodes.

Queries across curated (blueprint_audio, blueprint_core) and
scraped (blueprint_nodes_scraped) tables.
"""

from __future__ import annotations

import json
import logging

from ue_audio_mcp.knowledge.db import get_knowledge_db
from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _error, _ok
from ue_audio_mcp.ue5_connection import get_ue5_connection

log = logging.getLogger(__name__)


_VALID_SOURCES = {"all", "curated", "scraped"}


@mcp.tool()
def bp_search(query: str, category: str = "", source: str = "all") -> str:
    """Search Blueprint nodes by name or description.

    Searches across curated and scraped Blueprint data.

    Args:
        query: Search term (matched against name and description)
        category: Optional category filter
        source: Data source — "all", "curated", or "scraped"
    """
    if not query.strip():
        return _error("Query cannot be empty")
    if source not in _VALID_SOURCES:
        return _error("Invalid source '{}'. Must be one of: {}".format(
            source, ", ".join(sorted(_VALID_SOURCES))
        ))

    db = get_knowledge_db()
    results = []

    if source in ("all", "curated"):
        for r in db.search_blueprint_curated(query, category or None):
            results.append({
                "name": r["name"],
                "category": r.get("category", ""),
                "description": r.get("description", ""),
                "source": "curated",
            })

    if source in ("all", "scraped"):
        scraped = db.search_blueprint_scraped(query)
        if category:
            cat_lower = category.lower()
            scraped = [r for r in scraped if cat_lower in r.get("category", "").lower()
                       or cat_lower in r.get("target", "").lower()]
        for r in scraped:
            results.append({
                "name": r["name"],
                "category": r.get("target", r.get("category", "")),
                "description": r.get("description", ""),
                "source": "scraped",
            })

    # Deduplicate by name, prefer scraped (richer data)
    seen = {}
    for r in results:
        name = r["name"]
        if name not in seen or r.get("source") == "scraped":
            seen[name] = r
    deduped = sorted(seen.values(), key=lambda x: x["name"])

    return _ok({"count": len(deduped), "results": deduped})


@mcp.tool()
def bp_node_info(node_name: str) -> str:
    """Get full Blueprint node info including pin specs.

    Prefers scraped data (richer pin info), falls back to curated.

    Args:
        node_name: Exact node name (e.g. "PlaySound2D", "SpawnSoundAtLocation")
    """
    db = get_knowledge_db()

    # Try scraped first (has full input/output pin specs)
    scraped = db.query_blueprint_scraped(name=node_name)
    if scraped:
        node = scraped[0]
        return _ok({
            "name": node["name"],
            "target": node.get("target", ""),
            "category": node.get("category", ""),
            "description": node.get("description", ""),
            "inputs": node.get("inputs", []),
            "outputs": node.get("outputs", []),
            "source": "scraped",
        })

    # Fall back to curated tables
    curated = db.query_blueprint_curated_by_name(node_name)
    if curated:
        node = curated[0]
        return _ok({
            "name": node["name"],
            "class_name": node.get("class_name", ""),
            "category": node.get("category", ""),
            "description": node.get("description", ""),
            "params": node.get("params", []),
            "returns": node.get("returns", {}),
            "tags": node.get("tags", []),
            "source": "curated",
        })

    return _error("Node '{}' not found in any Blueprint table".format(node_name))


@mcp.tool()
def bp_list_categories(source: str = "all") -> str:
    """List Blueprint node categories with counts.

    Args:
        source: Data source — "all", "curated", or "scraped"
    """
    if source not in _VALID_SOURCES:
        return _error("Invalid source '{}'. Must be one of: {}".format(
            source, ", ".join(sorted(_VALID_SOURCES))
        ))

    db = get_knowledge_db()
    categories: dict[str, int] = {}

    if source in ("all", "curated"):
        for row in db.list_blueprint_curated_categories():
            cat = row["category"]
            categories[cat] = categories.get(cat, 0) + row["cnt"]

    if source in ("all", "scraped"):
        scraped = db.query_blueprint_scraped()
        target_counts: dict[str, int] = {}
        for row in scraped:
            cat = row.get("target") or "uncategorized"
            target_counts[cat] = target_counts.get(cat, 0) + 1
        for cat, cnt in target_counts.items():
            categories[cat] = categories.get(cat, 0) + cnt

    sorted_cats = [
        {"category": k, "count": v}
        for k, v in sorted(categories.items())
    ]
    return _ok({"count": len(sorted_cats), "categories": sorted_cats})


@mcp.tool()
def bp_call_function(function_name: str, args_json: str = "{}") -> str:
    """Execute a Blueprint function via the UE5 plugin.

    Args:
        function_name: Blueprint function name to call
        args_json: JSON string of function arguments
    """
    try:
        args = json.loads(args_json)
    except (json.JSONDecodeError, ValueError):
        return _error("Invalid args_json: {}".format(args_json))

    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "call_function",
            "function": function_name,
            "args": args,
        })
        return _ok({"function": function_name, "result": result})
    except Exception as e:
        return _error(str(e))
