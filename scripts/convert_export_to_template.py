#!/usr/bin/env python3
"""Convert enhanced MetaSounds export JSON to reusable graph templates.

Reads the JSON produced by the C++ FExportMetaSoundCommand (via TCP or
editor menu export) and converts each asset into the template format
used by graph_schema.py and build_audio_system.

Usage:
    # Convert all graphs from an export file
    python scripts/convert_export_to_template.py metasound_export.json

    # Convert and save to templates directory
    python scripts/convert_export_to_template.py metasound_export.json --save

    # Convert a single asset by name
    python scripts/convert_export_to_template.py metasound_export.json --asset MCP_Gunshot

    # Validate converted templates
    python scripts/convert_export_to_template.py metasound_export.json --validate
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ue_audio_mcp.knowledge.metasound_nodes import (
    METASOUND_NODES,
    CLASS_NAME_TO_DISPLAY,
    class_name_to_display,
    infer_class_type,
)


# ---------------------------------------------------------------------------
# Converter
# ---------------------------------------------------------------------------

def convert_export_to_template(export_data: dict) -> dict:
    """Convert a single MetaSounds export (from FExportMetaSoundCommand) to template format.

    Args:
        export_data: Dict with keys: asset_path, asset_type, is_preset, interfaces,
                     graph_inputs, graph_outputs, variables, nodes, edges

    Returns:
        Template dict compatible with graph_schema.py validate_graph()
    """
    # Extract asset name from path: /Game/Audio/MySound.MySound -> MySound
    asset_path = export_data.get("asset_path", "")
    raw_name = asset_path.rstrip("/").split("/")[-1]
    asset_name = raw_name.split(".")[-1] if "." in raw_name else raw_name

    template: dict = {
        "name": asset_name,
        "asset_type": export_data.get("asset_type", "Source"),
        "description": f"Exported from {asset_path}",
    }

    # Interfaces
    interfaces = export_data.get("interfaces", [])
    if interfaces:
        template["interfaces"] = interfaces

    # Graph inputs
    graph_inputs = export_data.get("graph_inputs", [])
    if graph_inputs:
        template["inputs"] = []
        for gi in graph_inputs:
            inp: dict = {"name": gi["name"], "type": gi["type"]}
            if "default" in gi and gi["default"] is not None:
                inp["default"] = gi["default"]
            template["inputs"].append(inp)

    # Graph outputs
    graph_outputs = export_data.get("graph_outputs", [])
    if graph_outputs:
        template["outputs"] = []
        for go in graph_outputs:
            template["outputs"].append({"name": go["name"], "type": go["type"]})

    # Variables
    variables = export_data.get("variables", [])
    if variables:
        template["variables"] = []
        for var in variables:
            v: dict = {"name": var["name"], "type": var["type"]}
            if "default" in var and var["default"] is not None:
                v["default"] = var["default"]
            template["variables"].append(v)

    # Build node_id -> node_id mapping (GUID -> short ID)
    # Also identify Input/Output class_type nodes for __graph__ wiring
    nodes_raw = export_data.get("nodes", [])
    guid_to_short: dict[str, str] = {}
    input_nodes: dict[str, str] = {}   # node_guid -> pin_name (graph input)
    output_nodes: dict[str, str] = {}  # node_guid -> pin_name (graph output)
    external_nodes: list[dict] = []
    used_ids: set[str] = set()

    for i, node in enumerate(nodes_raw):
        node_id = node.get("node_id", "")
        class_name = node.get("class_name", "")
        class_type = node.get("class_type") or infer_class_type(class_name)
        node_name = node.get("name", f"node_{i}")

        if class_type == "Input":
            input_nodes[node_id] = node_name
            guid_to_short[node_id] = "__graph__"
        elif class_type == "Output":
            output_nodes[node_id] = node_name
            guid_to_short[node_id] = "__graph__"
        elif class_type == "Variable":
            guid_to_short[node_id] = "__skip__"
        else:
            short = _make_short_id(node_name, i, used_ids)
            guid_to_short[node_id] = short
            external_nodes.append(node)

    # Convert external nodes to template format
    template["nodes"] = []
    for node in external_nodes:
        node_id = node.get("node_id", "")
        short_id = guid_to_short.get(node_id, node_id)
        class_name = node.get("class_name", "")
        class_type = node.get("class_type", "External")

        # Determine node_type
        if class_type in ("VariableAccessor",):
            node_type = "__variable_get__"
        elif class_type in ("VariableMutator",):
            node_type = "__variable_set__"
        elif class_type in ("VariableDeferred",):
            node_type = "__variable_get_delayed__"
        else:
            display = class_name_to_display(class_name)
            if display:
                node_type = display
            else:
                # Keep the class_name as-is -- the C++ plugin accepts :: names
                node_type = class_name

        entry: dict = {
            "id": short_id,
            "node_type": node_type,
        }

        # Position
        x = node.get("x", 0)
        y = node.get("y", 0)
        if x != 0 or y != 0:
            entry["position"] = [int(x), int(y)]

        # Defaults from input pins
        defaults: dict = {}
        for pin in node.get("inputs", []):
            if "default" in pin and pin["default"] is not None:
                defaults[pin["name"]] = pin["default"]
        if defaults:
            entry["defaults"] = defaults

        # Comment
        comment = node.get("comment", "")
        if comment:
            entry["comment"] = comment

        template["nodes"].append(entry)

    # Convert edges to template connections (skip __skip__ nodes)
    template["connections"] = []
    edges = export_data.get("edges", [])
    for edge in edges:
        from_guid = edge.get("from_node", "")
        to_guid = edge.get("to_node", "")
        from_pin = edge.get("from_pin", "")
        to_pin = edge.get("to_pin", "")

        from_short = guid_to_short.get(from_guid, from_guid)
        to_short = guid_to_short.get(to_guid, to_guid)

        if from_short == "__skip__" or to_short == "__skip__":
            continue

        # For Input nodes connecting to external nodes, the "from_pin"
        # should be the graph input name (which is the node name for Input class_type)
        if from_short == "__graph__" and from_guid in input_nodes:
            from_pin = input_nodes[from_guid]

        # For external nodes connecting to Output nodes, the "to_pin"
        # should be the graph output name
        if to_short == "__graph__" and to_guid in output_nodes:
            to_pin = output_nodes[to_guid]

        template["connections"].append({
            "from_node": from_short,
            "from_pin": from_pin,
            "to_node": to_short,
            "to_pin": to_pin,
        })

    return template


def _make_short_id(name: str, index: int, used: set[str] | None = None) -> str:
    """Convert a node name to a unique, snake_case ID."""
    short = re.sub(r"[^a-zA-Z0-9\s]", "", name).strip().lower()
    short = re.sub(r"\s+", "_", short)
    if not short:
        short = f"node_{index}"
    if used is not None:
        base = short
        counter = 2
        while short in used:
            short = f"{base}_{counter}"
            counter += 1
        used.add(short)
    return short


# ---------------------------------------------------------------------------
# Batch conversion
# ---------------------------------------------------------------------------

def convert_export_file(
    export_path: str,
    asset_filter: str | None = None,
    validate: bool = False,
    save: bool = False,
) -> list[dict]:
    """Convert all MetaSounds from an export JSON file.

    Args:
        export_path: Path to the JSON export file
        asset_filter: Optional asset name to filter
        validate: Run validate_graph on results
        save: Save templates to templates directory

    Returns:
        List of converted template dicts
    """
    with open(export_path) as f:
        data = json.load(f)

    # Handle both single-asset and multi-asset formats
    if "metasounds" in data:
        assets = data["metasounds"]
    elif "asset_path" in data:
        assets = [data]
    else:
        print(f"Unrecognized export format in {export_path}")
        return []

    templates = []
    for asset in assets:
        if asset.get("status") != "ok":
            continue

        asset_path = asset.get("asset_path", "")
        asset_name = asset_path.rstrip("/").split("/")[-1]

        if asset_filter and asset_filter not in asset_name:
            continue

        print(f"Converting: {asset_path}")
        template = convert_export_to_template(asset)
        templates.append(template)

        # Validate
        if validate:
            from ue_audio_mcp.knowledge.graph_schema import validate_graph
            errors = validate_graph(template)
            if errors:
                print(f"  VALIDATION ERRORS ({len(errors)}):")
                for err in errors[:10]:
                    print(f"    - {err}")
            else:
                print(f"  OK: {len(template['nodes'])} nodes, {len(template['connections'])} connections")

        # Save
        if save:
            template_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "src", "ue_audio_mcp", "templates", "metasounds",
            )
            os.makedirs(template_dir, exist_ok=True)

            filename = re.sub(r"[^a-zA-Z0-9_]", "_", template["name"]).lower()
            out_path = os.path.join(template_dir, f"{filename}.json")
            with open(out_path, "w") as f:
                json.dump(template, f, indent=2)
            print(f"  Saved: {out_path}")

    return templates


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert MetaSounds export JSON to reusable graph templates"
    )
    parser.add_argument("export_file", help="Path to the export JSON file")
    parser.add_argument("--asset", help="Filter by asset name substring")
    parser.add_argument("--validate", action="store_true", help="Validate converted templates")
    parser.add_argument("--save", action="store_true", help="Save templates to templates directory")
    parser.add_argument("--json", action="store_true", help="Print templates as JSON to stdout")

    args = parser.parse_args()

    if not os.path.exists(args.export_file):
        print(f"File not found: {args.export_file}")
        sys.exit(1)

    templates = convert_export_file(
        args.export_file,
        asset_filter=args.asset,
        validate=args.validate,
        save=args.save,
    )

    print(f"\nConverted {len(templates)} template(s)")

    if args.json:
        print(json.dumps(templates, indent=2))


if __name__ == "__main__":
    main()
