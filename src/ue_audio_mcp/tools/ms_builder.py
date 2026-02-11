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
from ue_audio_mcp.knowledge.metasound_nodes import (
    METASOUND_NODES,
    CLASS_NAME_TO_DISPLAY,
    class_name_to_display,
    infer_class_type,
)
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
        template = _inline_convert(result)
        response["template"] = template
        response["message"] += " (template generated)"

    return _ok(response)


@mcp.tool()
def ms_sync_from_engine(
    update_db: bool = False,
    filter: str = "",
    limit: int = 5000,
) -> str:
    """Sync MetaSounds node catalogue from the running UE5 engine.

    Calls the list_metasound_nodes command to get ALL registered node classes
    with their complete pin specs directly from the engine registry. Updates
    the in-memory METASOUND_NODES dict and optionally the SQLite DB.

    Args:
        update_db: If True, also upsert nodes into the SQLite knowledge DB
        filter: Optional substring filter for node class names
        limit: Max nodes to fetch (default 5000)

    Returns:
        JSON summary: total nodes, new nodes added, existing nodes updated, categories.
    """
    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "list_metasound_nodes",
            "include_pins": True,
            "include_metadata": True,
            "filter": filter,
            "limit": limit,
        })
    except Exception as e:
        return _error(str(e))

    if result.get("status") != "ok":
        return _error(result.get("message", "list_metasound_nodes failed"))

    engine_nodes = result.get("nodes", [])
    if not engine_nodes:
        return _ok({
            "message": "No nodes returned from engine",
            "total": 0, "new": 0, "updated": 0,
        })

    new_count = 0
    updated_count = 0
    categories: dict[str, int] = {}

    for enode in engine_nodes:
        node_def = _engine_node_to_nodedef(enode)
        if node_def is None:
            continue

        cat = node_def["category"]
        categories[cat] = categories.get(cat, 0) + 1
        name = node_def["name"]

        if name in METASOUND_NODES:
            # Update existing: replace pins (engine is ground truth)
            existing = METASOUND_NODES[name]
            existing["inputs"] = node_def["inputs"]
            existing["outputs"] = node_def["outputs"]
            if node_def.get("description"):
                existing["description"] = node_def["description"]
            updated_count += 1
        else:
            METASOUND_NODES[name] = node_def
            new_count += 1

        # Update CLASS_NAME_TO_DISPLAY reverse mapping
        class_name = enode.get("class_name", "")
        if class_name and name and class_name not in CLASS_NAME_TO_DISPLAY:
            CLASS_NAME_TO_DISPLAY[class_name] = name

    # Optionally update SQLite
    db_updated = 0
    if update_db:
        try:
            from ue_audio_mcp.knowledge.db import get_db
            db = get_db()
            for enode in engine_nodes:
                node_def = _engine_node_to_nodedef(enode)
                if node_def:
                    db.insert_node(node_def)
                    db_updated += 1
        except Exception as e:
            log.warning("DB update failed: %s", e)

    # Reset search index so it rebuilds with new nodes
    try:
        from ue_audio_mcp.tools.metasounds import _reset_search_index
        _reset_search_index()
    except Exception:
        pass

    return _ok({
        "message": "Synced {} nodes from engine ({} new, {} updated)".format(
            len(engine_nodes), new_count, updated_count
        ),
        "total": len(engine_nodes),
        "new": new_count,
        "updated": updated_count,
        "db_updated": db_updated,
        "categories": dict(sorted(categories.items())),
        "catalogue_size": len(METASOUND_NODES),
    })


def _engine_node_to_nodedef(enode: dict) -> dict | None:
    """Convert an engine node dict to our NodeDef format.

    Returns None if the node cannot be mapped (e.g. missing name).
    """
    class_name = enode.get("class_name", "")
    raw_name = enode.get("name", "")
    variant = enode.get("variant", "")

    if not raw_name:
        return None

    # Build display name: "Name" or "Name (Variant)" for non-None variants
    if variant and variant != "None":
        display_name = "{} ({})".format(raw_name, variant)
    else:
        display_name = raw_name

    # Check if we already know this node by class_name lookup
    existing_display = class_name_to_display(class_name)
    if existing_display and existing_display in METASOUND_NODES:
        display_name = existing_display

    # Map category from engine metadata or infer from namespace
    category = _infer_category(enode)

    # Build pins
    inputs = []
    for pin in enode.get("inputs", []):
        pin_type = _normalize_pin_type(pin.get("type", ""))
        inp: dict = {"name": pin["name"], "type": pin_type, "required": True}
        if "default" in pin and pin["default"] is not None:
            inp["default"] = pin["default"]
        inputs.append(inp)

    outputs = []
    for pin in enode.get("outputs", []):
        pin_type = _normalize_pin_type(pin.get("type", ""))
        outputs.append({"name": pin["name"], "type": pin_type})

    # Description and tags
    description = enode.get("description", "")
    if not description:
        description = "{} MetaSounds node.".format(display_name)

    tags = []
    for kw in enode.get("keywords", []):
        tags.append(kw.lower())
    if not tags:
        tags = [raw_name.lower().replace(" ", "_")]

    return {
        "name": display_name,
        "category": category,
        "description": description,
        "inputs": inputs,
        "outputs": outputs,
        "tags": tags,
        "complexity": 1,
        "class_name": class_name,
    }


def _normalize_pin_type(engine_type: str) -> str:
    """Normalize engine pin type names to our catalogue format.

    Examples: 'Audio' stays 'Audio', 'Enum:ENoiseType' → 'Enum',
    'MetasoundFrontend:Trigger' → 'Trigger'.
    """
    if not engine_type:
        return "Audio"
    # Strip namespace prefixes
    if ":" in engine_type:
        parts = engine_type.split(":")
        # Keep the last meaningful part
        base = parts[-1].strip()
        # Check if it's an enum
        if "Enum" in engine_type or engine_type.startswith("E"):
            return "Enum"
        return base if base else engine_type
    return engine_type


# Map of known category keywords to our category names
_CATEGORY_MAP = {
    "generator": "Generators",
    "oscillator": "Generators",
    "wave player": "Generators",
    "filter": "Filters",
    "envelope": "Envelopes",
    "dynamics": "Dynamics",
    "effect": "Effects",
    "delay": "Effects",
    "reverb": "Effects",
    "chorus": "Effects",
    "math": "Math",
    "arithmetic": "Math",
    "mix": "Mix",
    "mixer": "Mix",
    "panner": "Spatialization",
    "spatial": "Spatialization",
    "trigger": "Triggers",
    "music": "Music",
    "midi": "Music",
    "random": "Random",
    "convert": "Converters",
    "analysis": "Analysis",
    "io": "IO",
    "gain": "Gain",
    "debug": "Debug",
}


def _infer_category(enode: dict) -> str:
    """Infer a catalogue category from engine node metadata."""
    # Try engine category field first
    cat = enode.get("category", "")
    if cat:
        cat_lower = cat.lower()
        for keyword, mapped in _CATEGORY_MAP.items():
            if keyword in cat_lower:
                return mapped
        # Use the last segment of category hierarchy as-is
        return cat.split("|")[-1].strip() if "|" in cat else cat

    # Fall back to namespace/name heuristics
    ns = enode.get("namespace", "").lower()
    name = enode.get("name", "").lower()
    combined = "{} {}".format(ns, name)
    for keyword, mapped in _CATEGORY_MAP.items():
        if keyword in combined:
            return mapped

    return "Other"


def _inline_convert(export_data: dict) -> dict:
    """Convert export JSON to template format using shared CLASS_NAME_TO_DISPLAY.

    Handles missing class_type by inferring from class_name prefix.
    """
    import re

    asset_path = export_data.get("asset_path", "")
    raw_name = asset_path.rstrip("/").split("/")[-1]
    asset_name = raw_name.split(".")[-1] if "." in raw_name else raw_name

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
    used_ids: set[str] = set()
    template["nodes"] = []

    for i, node in enumerate(export_data.get("nodes", [])):
        nid = node.get("node_id", "")
        class_name = node.get("class_name", "")
        name = node.get("name", "node_{}".format(i))

        # Infer class_type if missing (older get_node_locations format)
        ct = node.get("class_type") or infer_class_type(class_name)

        if ct == "Input":
            input_nodes[nid] = name
            guid_to_short[nid] = "__graph__"
            continue
        if ct == "Output":
            output_nodes[nid] = name
            guid_to_short[nid] = "__graph__"
            continue
        if ct == "Variable":
            # InitVariable nodes are internal — skip
            guid_to_short[nid] = "__skip__"
            continue

        short = re.sub(r"[^a-zA-Z0-9\s]", "", name).strip().lower()
        short = re.sub(r"\s+", "_", short) or "node_{}".format(i)
        base = short
        counter = 2
        while short in used_ids:
            short = "{}_{}".format(base, counter)
            counter += 1
        used_ids.add(short)
        guid_to_short[nid] = short

        # Determine node_type: dict first, then fuzzy, then raw class_name
        if ct == "VariableAccessor":
            node_type = "__variable_get__"
        elif ct == "VariableMutator":
            node_type = "__variable_set__"
        elif ct == "VariableDeferred":
            node_type = "__variable_get_delayed__"
        else:
            display = class_name_to_display(class_name)
            node_type = display if display else class_name

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

    # Edges — skip connections involving __skip__ nodes
    template["connections"] = []
    for edge in export_data.get("edges", []):
        fg, tg = edge.get("from_node", ""), edge.get("to_node", "")
        fp, tp = edge.get("from_pin", ""), edge.get("to_pin", "")
        fs = guid_to_short.get(fg, fg)
        ts = guid_to_short.get(tg, tg)
        if fs == "__skip__" or ts == "__skip__":
            continue
        if fs == "__graph__" and fg in input_nodes:
            fp = input_nodes[fg]
        if ts == "__graph__" and tg in output_nodes:
            tp = output_nodes[tg]
        template["connections"].append({
            "from_node": fs, "from_pin": fp,
            "to_node": ts, "to_pin": tp,
        })

    return template
