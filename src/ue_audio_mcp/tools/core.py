"""Core WAAPI tools — connect, info, query, save, raw execute."""

from __future__ import annotations

import json
import logging

from ue_audio_mcp.connection import get_wwise_connection
from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _error, _ok

log = logging.getLogger(__name__)


@mcp.tool()
def wwise_connect(url: str = "") -> str:
    """Connect to Wwise via WAAPI.

    Args:
        url: WebSocket URL (default ws://127.0.0.1:8080/waapi)
    """
    conn = get_wwise_connection()
    try:
        info = conn.connect(url or None)
        version = info.get("version", {}).get("displayName", "unknown")
        return _ok({"version": version, "info": info})
    except Exception as e:
        return _error(f"Cannot connect to Wwise: {e}")


@mcp.tool()
def wwise_get_info() -> str:
    """Get Wwise application info (version, platform, project)."""
    conn = get_wwise_connection()
    try:
        info = conn.call("ak.wwise.core.getInfo")
        return _ok({"info": info})
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def wwise_query(waql: str, return_fields: str = '["id", "name", "type", "path"]') -> str:
    """Query Wwise objects using WAQL.

    Args:
        waql: WAQL query string (e.g. '$ from type sound')
        return_fields: JSON array of fields to return
    """
    conn = get_wwise_connection()
    try:
        fields = json.loads(return_fields)
    except json.JSONDecodeError:
        return _error(f"Invalid return_fields JSON: {return_fields}")

    try:
        result = conn.call(
            "ak.wwise.core.object.get",
            {"waql": waql},
            {"return": fields},
        )
        items = result.get("return", [])
        return _ok({"count": len(items), "results": items})
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def wwise_save() -> str:
    """Save the current Wwise project."""
    conn = get_wwise_connection()
    try:
        conn.call("ak.wwise.core.project.save")
        return _ok({"message": "Project saved"})
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def execute_waapi(uri: str, args_json: str = "{}", options_json: str = "{}") -> str:
    """Execute any WAAPI call directly (escape hatch).

    Args:
        uri: WAAPI function URI (e.g. ak.wwise.core.object.getTypes)
        args_json: JSON string of arguments
        options_json: JSON string of options
    """
    conn = get_wwise_connection()
    try:
        args = json.loads(args_json)
    except json.JSONDecodeError:
        return _error(f"Invalid args_json: {args_json}")
    try:
        options = json.loads(options_json)
    except json.JSONDecodeError:
        return _error(f"Invalid options_json: {options_json}")

    try:
        result = conn.call(uri, args or None, options or None)
        return _ok({"result": result})
    except Exception as e:
        return _error(str(e))
