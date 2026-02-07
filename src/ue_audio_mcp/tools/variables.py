"""MetaSounds graph variable tools — add/read/write graph variables via UE5 plugin.

2 tools for UE 5.7 graph variable support:
  - ms_add_variable: Add a typed variable to the current MetaSound graph
  - ms_add_variable_node: Add a Get/Set/GetDelayed variable accessor node
"""

from __future__ import annotations

import logging

from ue_audio_mcp.knowledge.metasound_data_types import PIN_TYPES
from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _error, _ok
from ue_audio_mcp.ue5_connection import get_ue5_connection

log = logging.getLogger(__name__)

VALID_VARIABLE_NODE_MODES = {"get", "set", "get_delayed"}


@mcp.tool()
def ms_add_variable(name: str, type: str, default_value: str = "") -> str:
    """Add a graph variable to the current MetaSounds builder (UE 5.7+).

    Graph variables store state within a MetaSound graph, readable and
    writable by Get/Set Variable nodes.

    Args:
        name: Variable name (must be unique within the graph)
        type: Data type (Float, Int32, Bool, Trigger, Audio, Time, String)
        default_value: Optional default value as string
    """
    if type not in PIN_TYPES:
        return _error("Invalid type '{}'. Must be one of: {}".format(
            type, ", ".join(sorted(t for t in PIN_TYPES if "[]" not in t))
        ))

    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "add_graph_variable",
            "name": name,
            "type": type,
            "default": default_value,
        })
        return _ok({
            "message": "Added graph variable '{}' ({})".format(name, type),
            "result": result,
        })
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def ms_add_variable_node(
    node_id: str,
    variable_name: str,
    mode: str = "get",
) -> str:
    """Add a Get, Set, or GetDelayed variable node to the current graph.

    Args:
        node_id: Unique ID for this node instance
        variable_name: Name of the graph variable to access
        mode: Access mode — "get" (read current), "set" (write), or "get_delayed" (read previous frame)
    """
    if mode not in VALID_VARIABLE_NODE_MODES:
        return _error("Invalid mode '{}'. Must be one of: {}".format(
            mode, ", ".join(sorted(VALID_VARIABLE_NODE_MODES))
        ))

    if mode == "set":
        action = "add_variable_set_node"
        cmd = {
            "action": action,
            "id": node_id,
            "variable_name": variable_name,
        }
    else:
        action = "add_variable_get_node"
        cmd = {
            "action": action,
            "id": node_id,
            "variable_name": variable_name,
            "delayed": mode == "get_delayed",
        }

    conn = get_ue5_connection()
    try:
        result = conn.send_command(cmd)
        return _ok({
            "message": "Added {} variable node '{}' for '{}'".format(mode, node_id, variable_name),
            "result": result,
        })
    except Exception as e:
        return _error(str(e))
