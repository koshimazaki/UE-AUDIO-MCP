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


@mcp.tool()
def ms_export_graph(asset_path: str, convert_to_template: bool = False) -> str:
    """Export a complete MetaSounds graph from UE5 — nodes, pin types, defaults, variables, interfaces.

    Returns the full graph data. Optionally converts to our reusable template format.

    Args:
        asset_path: Content path of the MetaSound asset (e.g. /Game/Audio/MySound)
        convert_to_template: If True, also convert the export to template format
    """
    if not asset_path.startswith("/Game/") and not asset_path.startswith("/Engine/"):
        return _error("asset_path must start with /Game/ or /Engine/ (got '{}')".format(asset_path))
    if ".." in asset_path:
        return _error("asset_path must not contain '..'")

    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "export_metasound",
            "asset_path": asset_path,
        })
    except Exception as e:
        return _error(str(e))

    if result.get("status") != "ok":
        return _error(result.get("message", "Export failed"))

    node_count = len(result.get("nodes", []))
    edge_count = len(result.get("edges", []))
    var_count = len(result.get("variables", []))

    response = {
        "message": "Exported '{}': {} nodes, {} edges, {} variables".format(
            asset_path, node_count, edge_count, var_count
        ),
        "export": result,
    }

    if convert_to_template:
        try:
            from scripts.convert_export_to_template import convert_export_to_template
            template = convert_export_to_template(result)
            response["template"] = template
            response["message"] += " (template generated)"
        except ImportError:
            # scripts dir not on path — use inline conversion
            template = _inline_convert(result)
            response["template"] = template
            response["message"] += " (template generated)"

    return _ok(response)


def _inline_convert(export_data: dict) -> dict:
    """Minimal inline export-to-template conversion (no scripts dependency)."""
    import re

    asset_path = export_data.get("asset_path", "")
    asset_name = asset_path.rstrip("/").split("/")[-1]

    template: dict = {
        "name": asset_name,
        "asset_type": export_data.get("asset_type", "Source"),
    }

    if export_data.get("interfaces"):
        template["interfaces"] = export_data["interfaces"]
    if export_data.get("graph_inputs"):
        template["inputs"] = [
            {k: v for k, v in gi.items() if v is not None}
            for gi in export_data["graph_inputs"]
        ]
    if export_data.get("graph_outputs"):
        template["outputs"] = [
            {"name": go["name"], "type": go["type"]}
            for go in export_data["graph_outputs"]
        ]
    if export_data.get("variables"):
        template["variables"] = [
            {k: v for k, v in var.items() if k != "id" and v is not None}
            for var in export_data["variables"]
        ]

    # Map nodes — Input/Output class_types become __graph__ boundary
    guid_to_short: dict[str, str] = {}
    input_nodes: dict[str, str] = {}
    output_nodes: dict[str, str] = {}
    template["nodes"] = []

    for i, node in enumerate(export_data.get("nodes", [])):
        nid = node.get("node_id", "")
        ct = node.get("class_type", "External")
        name = node.get("name", "node_{}".format(i))

        if ct == "Input":
            input_nodes[nid] = name
            guid_to_short[nid] = "__graph__"
            continue
        if ct == "Output":
            output_nodes[nid] = name
            guid_to_short[nid] = "__graph__"
            continue

        short = re.sub(r"[^a-zA-Z0-9\s]", "", name).strip().lower()
        short = re.sub(r"\s+", "_", short) or "node_{}".format(i)
        guid_to_short[nid] = short

        # Determine node_type from class_name
        class_name = node.get("class_name", "")
        node_type = class_name  # fallback to raw class name
        if ct == "VariableAccessor":
            node_type = "__variable_get__"
        elif ct == "VariableMutator":
            node_type = "__variable_set__"
        elif ct == "VariableDeferred":
            node_type = "__variable_get_delayed__"
        else:
            parts = class_name.split("::")
            if len(parts) >= 2:
                n = parts[1].strip()
                v = parts[2].strip() if len(parts) >= 3 else ""
                if n in METASOUND_NODES:
                    node_type = n
                elif v and "{} ({})".format(n, v) in METASOUND_NODES:
                    node_type = "{} ({})".format(n, v)

        entry: dict = {"id": short, "node_type": node_type}
        x, y = node.get("x", 0), node.get("y", 0)
        if x or y:
            entry["position"] = [int(x), int(y)]
        defaults = {
            p["name"]: p["default"]
            for p in node.get("inputs", [])
            if "default" in p and p["default"] is not None
        }
        if defaults:
            entry["defaults"] = defaults
        template["nodes"].append(entry)

    # Edges
    template["connections"] = []
    for edge in export_data.get("edges", []):
        fg, tg = edge.get("from_node", ""), edge.get("to_node", "")
        fp, tp = edge.get("from_pin", ""), edge.get("to_pin", "")
        fs = guid_to_short.get(fg, fg)
        ts = guid_to_short.get(tg, tg)
        if fs == "__graph__" and fg in input_nodes:
            fp = input_nodes[fg]
        if ts == "__graph__" and tg in output_nodes:
            tp = output_nodes[tg]
        template["connections"].append({
            "from_node": fs, "from_pin": fp,
            "to_node": ts, "to_pin": tp,
        })

    return template
