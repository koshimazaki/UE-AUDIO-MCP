"""MetaSounds Builder API tools — send commands to UE5 plugin via TCP.

8 tools that wrap the Builder API command protocol from graph_schema.py.
Requires an active UE5 plugin connection (ue5_connect).
"""

from __future__ import annotations

import json
import logging

from ue_audio_mcp.knowledge.graph_schema import (
    graph_to_builder_commands,
    validate_graph,
)
from ue_audio_mcp.knowledge.metasound_nodes import METASOUND_NODES
from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _error, _ok
from ue_audio_mcp.ue5_connection import get_ue5_connection

log = logging.getLogger(__name__)

VALID_ASSET_TYPES = {"Source", "Patch", "Preset"}


@mcp.tool()
def ms_build_graph(graph_spec: str) -> str:
    """Validate a graph spec, convert to Builder commands, and send all to UE5.

    This is the high-level tool that does everything: validate, convert,
    and execute the full command sequence via the UE5 plugin.

    Args:
        graph_spec: JSON string of the MetaSounds graph specification
    """
    try:
        spec = json.loads(graph_spec)
    except (json.JSONDecodeError, ValueError):
        return _error("Invalid graph_spec JSON")

    errors = validate_graph(spec)
    if errors:
        return _error("Graph has {} validation error(s): {}".format(
            len(errors), "; ".join(errors[:5])
        ))

    commands = graph_to_builder_commands(spec)
    conn = get_ue5_connection()

    results = []
    for i, cmd in enumerate(commands):
        try:
            result = conn.send_command(cmd)
            results.append(result)
        except Exception as e:
            return _error("Command {} ({}) failed: {}".format(
                i + 1, cmd.get("action", "?"), e
            ))

    return _ok({
        "message": "Graph '{}' built successfully".format(spec["name"]),
        "commands_sent": len(commands),
        "results": results,
    })


@mcp.tool()
def ms_create_source(name: str, asset_type: str = "Source") -> str:
    """Create a new MetaSounds source builder in UE5.

    Args:
        name: Name for the MetaSound asset
        asset_type: Asset type — Source, Patch, or Preset
    """
    if asset_type not in VALID_ASSET_TYPES:
        return _error("Invalid asset_type '{}'. Must be one of: {}".format(
            asset_type, ", ".join(sorted(VALID_ASSET_TYPES))
        ))
    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "create_builder",
            "asset_type": asset_type,
            "name": name,
        })
        return _ok({"message": "Created {} '{}'".format(asset_type, name), "result": result})
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def ms_add_node(
    node_type: str,
    node_id: str,
    position_x: int = 0,
    position_y: int = 0,
) -> str:
    """Add a MetaSounds node to the current graph.

    Args:
        node_type: Node type name (e.g. "Sine", "Wave Player (Mono)")
        node_id: Unique ID for this node instance
        position_x: Editor X position
        position_y: Editor Y position
    """
    if node_type not in METASOUND_NODES:
        return _error("Unknown node_type '{}'. Use ms_search_nodes to find valid types.".format(
            node_type
        ))
    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "add_node",
            "id": node_id,
            "node_type": node_type,
            "position": [position_x, position_y],
        })
        return _ok({"message": "Added node '{}' ({})".format(node_id, node_type), "result": result})
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def ms_connect_pins(
    from_node: str,
    from_pin: str,
    to_node: str,
    to_pin: str,
) -> str:
    """Connect two node pins in the current MetaSounds graph.

    Args:
        from_node: Source node ID
        from_pin: Source output pin name
        to_node: Destination node ID
        to_pin: Destination input pin name
    """
    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "connect",
            "from_node": from_node,
            "from_pin": from_pin,
            "to_node": to_node,
            "to_pin": to_pin,
        })
        return _ok({
            "message": "Connected {}.{} -> {}.{}".format(from_node, from_pin, to_node, to_pin),
            "result": result,
        })
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def ms_set_default(node_id: str, input_name: str, value: str) -> str:
    """Set a default value for a node input pin.

    Args:
        node_id: Node instance ID
        input_name: Input pin name
        value: Default value (JSON-encoded for complex types)
    """
    # Try to parse as JSON for numeric/bool/object values
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, ValueError):
        parsed = value

    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "set_default",
            "node_id": node_id,
            "input": input_name,
            "value": parsed,
        })
        return _ok({
            "message": "Set {}.{} = {}".format(node_id, input_name, parsed),
            "result": result,
        })
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def ms_save_asset(name: str, path: str = "/Game/Audio/Generated/") -> str:
    """Build the current MetaSounds graph to a UE5 asset.

    Args:
        name: Asset name
        path: Content path (default /Game/Audio/Generated/)
    """
    if not path.startswith("/Game/"):
        return _error("Path must start with /Game/ (got '{}')".format(path))
    if ".." in path:
        return _error("Path must not contain '..'")
    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "build_to_asset",
            "name": name,
            "path": path,
        })
        return _ok({
            "message": "Saved asset '{}' to {}".format(name, path),
            "result": result,
        })
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def ms_open_in_editor() -> str:
    """Open the last built MetaSound asset in the UE5 MetaSounds editor.

    Must call ms_save_asset first to create a .uasset on disk.
    Opens the graph editor showing all nodes and connections visually.
    """
    conn = get_ue5_connection()
    try:
        result = conn.send_command({"action": "open_in_editor"})
        return _ok({
            "message": "Opened MetaSound asset in editor",
            "result": result,
        })
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def ms_convert_to_preset(referenced_asset: str) -> str:
    """Convert the current MetaSounds builder to a preset of a referenced asset.

    The builder's graph becomes read-only, inheriting the referenced asset's
    topology. Only exposed input defaults can be overridden.

    Args:
        referenced_asset: Content path of the source MetaSound (e.g. /Game/Audio/MySynth)
    """
    if not referenced_asset.startswith("/Game/"):
        return _error("referenced_asset must start with /Game/ (got '{}')".format(referenced_asset))
    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "convert_to_preset",
            "referenced_asset": referenced_asset,
        })
        return _ok({
            "message": "Converted to preset of '{}'".format(referenced_asset),
            "result": result,
        })
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def ms_audition(name: str = "") -> str:
    """Preview/audition the current MetaSounds graph in the editor.

    Args:
        name: Optional asset name to audition (empty = current)
    """
    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "audition",
            "name": name,
        })
        return _ok({"message": "Auditioning" + (" '{}'".format(name) if name else ""), "result": result})
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def ms_stop_audition() -> str:
    """Stop any currently playing MetaSounds audition preview."""
    conn = get_ue5_connection()
    try:
        result = conn.send_command({"action": "stop_audition"})
        return _ok({"message": "Audition stopped", "result": result})
    except Exception as e:
        return _error(str(e))
