#!/usr/bin/env python3
"""Parse UE5 MetaSounds editor graph exports into our JSON template format.

Parses the "Copy full snippet" format from MetaSounds Editor — the
Begin Object / End Object blocks with CustomProperties Pin data.

This is the golden data source: exact node class names, pin types,
default values, positions, and connections directly from the engine.

Usage:
    python scripts/parse_metasound_export.py export.txt -o template.json
    python scripts/parse_metasound_export.py --text "Begin Object..." --name Snare

Input format (from MetaSounds Editor > Right-click > Copy):
    Begin Object Class=/Script/MetasoundEditor.MetasoundEditorGraphExternalNode ...
       ClassName=(Namespace="UE",Name="Noise",Variant="Audio")
       NodePosX=-336
       NodePosY=336
       CustomProperties Pin (PinId=...,PinName="Audio",Direction="EGPD_Output",...)
    End Object
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Pin:
    pin_id: str
    name: str
    category: str  # Audio, Float, Trigger, etc.
    direction: str  # input or output
    default_value: str = ""
    linked_to: list[tuple[str, str]] = field(default_factory=list)  # [(node_name, pin_id)]


@dataclass
class MSNode:
    obj_name: str  # MetasoundEditorGraphExternalNode_0
    node_class: str  # Full class string
    namespace: str  # UE, AD Envelope, etc.
    name: str  # Noise, State Variable Filter, etc.
    variant: str  # Audio, Float, etc.
    pos_x: int = 0
    pos_y: int = 0
    node_type: str = "external"  # external, input, output
    input_name: str = ""  # For graph I/O nodes: the interface member name
    pins: list[Pin] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        if self.variant:
            return f"{self.name} ({self.variant})"
        return self.name


def parse_class_name(breadcrumb: str) -> tuple[str, str, str]:
    """Parse ClassName=(Namespace="X",Name="Y",Variant="Z")."""
    ns = re.search(r'Namespace="([^"]*)"', breadcrumb)
    nm = re.search(r'Name="([^"]*)"', breadcrumb)
    vr = re.search(r'Variant="([^"]*)"', breadcrumb)
    return (
        ns.group(1) if ns else "",
        nm.group(1) if nm else "",
        vr.group(1) if vr else "",
    )


def parse_pin(pin_text: str) -> Pin:
    """Parse a CustomProperties Pin(...) line."""
    pid = re.search(r'PinId=([A-F0-9]+)', pin_text)
    pname = re.search(r'PinName="([^"]*)"', pin_text)
    pcat = re.search(r'PinType\.PinCategory="([^"]*)"', pin_text)
    pdir = re.search(r'Direction="EGPD_Output"', pin_text)
    pdef = re.search(r'DefaultValue="([^"]*)"', pin_text)
    linked = re.findall(r'LinkedTo=\(([^)]+)\)', pin_text)

    links = []
    if linked:
        # Format: "NodeName PinId,NodeName2 PinId2,..."
        for item in linked[0].split(','):
            item = item.strip()
            if ' ' in item:
                parts = item.split()
                links.append((parts[0], parts[1]))

    return Pin(
        pin_id=pid.group(1) if pid else "",
        name=pname.group(1) if pname else "",
        category=pcat.group(1) if pcat else "",
        direction="output" if pdir else "input",
        default_value=pdef.group(1) if pdef else "",
        linked_to=links,
    )


def parse_export(text: str) -> list[MSNode]:
    """Parse the full export text into MSNode list."""
    nodes = []

    # Split into Begin Object...End Object blocks
    blocks = re.findall(
        r'Begin Object\s+Class=([^\s]+)\s+Name="([^"]+)".*?End Object',
        text, re.DOTALL
    )

    for block_class, block_name in blocks:
        # Get full block text
        pattern = rf'Begin Object\s+Class={re.escape(block_class)}\s+Name="{re.escape(block_name)}"(.*?)End Object'
        m = re.search(pattern, text, re.DOTALL)
        if not m:
            continue
        block_text = m.group(1)

        # Determine node type
        if "GraphInputNode" in block_class:
            node_type = "input"
        elif "GraphOutputNode" in block_class:
            node_type = "output"
        else:
            node_type = "external"

        # Parse class name from ClassName= or Breadcrumb=
        cn_match = re.search(r'ClassName=\(([^)]+)\)', block_text)
        bc_match = re.search(r'Breadcrumb=\(.*?ClassName=\(([^)]+)\)', block_text)
        class_str = ""
        namespace, name, variant = "", "", ""

        if cn_match:
            class_str = cn_match.group(1)
            namespace, name, variant = parse_class_name(class_str)
        elif bc_match:
            class_str = bc_match.group(1)
            namespace, name, variant = parse_class_name(class_str)

        # For input/output nodes, get the member name
        input_name = ""
        if node_type == "input":
            mn = re.search(r'MemberName="([^"]*)"', block_text)
            if mn:
                input_name = mn.group(1)
            name = name or input_name
            namespace = namespace or "Input"
        elif node_type == "output":
            mn = re.search(r'MemberName="([^"]*)"', block_text)
            if mn:
                input_name = mn.group(1)
            name = name or input_name
            namespace = namespace or "Output"

        # Positions
        px = re.search(r'NodePosX=(-?\d+)', block_text)
        py = re.search(r'NodePosY=(-?\d+)', block_text)

        # Parse pins
        pins = []
        for pin_match in re.finditer(r'CustomProperties Pin \((.+?)\)\s*$', block_text, re.MULTILINE):
            pin = parse_pin(pin_match.group(1))
            pins.append(pin)

        node = MSNode(
            obj_name=block_name,
            node_class=class_str,
            namespace=namespace,
            name=name,
            variant=variant,
            pos_x=int(px.group(1)) if px else 0,
            pos_y=int(py.group(1)) if py else 0,
            node_type=node_type,
            input_name=input_name,
            pins=pins,
        )
        nodes.append(node)

    return nodes


def make_safe_id(name: str) -> str:
    """Convert node object name to safe ID."""
    # MetasoundEditorGraphExternalNode_0 -> external_0
    name = name.replace("MetasoundEditorGraph", "")
    name = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
    return name.lower().strip('_')


def nodes_to_template(nodes: list[MSNode], name: str = "Untitled") -> dict:
    """Convert parsed nodes to our JSON template format."""
    # Build pin_id -> (node_obj_name, pin_name) lookup
    pin_lookup: dict[str, tuple[str, str]] = {}
    for node in nodes:
        for pin in node.pins:
            pin_lookup[pin.pin_id] = (node.obj_name, pin.name)

    # Build obj_name -> safe_id mapping
    id_map = {}
    for node in nodes:
        if node.node_type == "input":
            id_map[node.obj_name] = "__graph__"
        elif node.node_type == "output":
            id_map[node.obj_name] = "__graph__"
        else:
            id_map[node.obj_name] = make_safe_id(node.obj_name)

    # Collect graph inputs/outputs
    graph_inputs = []
    graph_outputs = []
    for node in nodes:
        if node.node_type == "input":
            for pin in node.pins:
                if pin.direction == "output":
                    graph_inputs.append({"name": node.input_name or pin.name, "type": pin.category})
        elif node.node_type == "output":
            for pin in node.pins:
                if pin.direction == "input":
                    graph_outputs.append({"name": node.input_name or pin.name, "type": pin.category})

    # Build node entries
    template_nodes = []
    for node in nodes:
        if node.node_type in ("input", "output"):
            continue  # Graph I/O is handled as __graph__

        safe_id = id_map[node.obj_name]
        entry = {
            "id": safe_id,
            "node_type": node.display_name,
            "node_class": {
                "namespace": node.namespace,
                "name": node.name,
                "variant": node.variant,
            },
            "position": [node.pos_x, node.pos_y],
        }

        # Collect defaults
        defaults = {}
        for pin in node.pins:
            if pin.direction == "input" and pin.default_value:
                defaults[pin.name] = _parse_value(pin.default_value, pin.category)
        if defaults:
            entry["defaults"] = defaults

        template_nodes.append(entry)

    # Build connections
    connections = []
    for node in nodes:
        for pin in node.pins:
            if pin.direction == "output" and pin.linked_to:
                from_id = id_map.get(node.obj_name, node.obj_name)
                from_pin = pin.name
                if node.node_type == "input":
                    from_pin = node.input_name or pin.name

                for target_name, target_pin_id in pin.linked_to:
                    if target_pin_id in pin_lookup:
                        target_node_name, target_pin_name = pin_lookup[target_pin_id]
                        to_id = id_map.get(target_node_name, target_node_name)

                        # For output nodes, use the member name
                        if to_id == "__graph__":
                            for n in nodes:
                                if n.obj_name == target_node_name and n.node_type == "output":
                                    target_pin_name = n.input_name or target_pin_name

                        connections.append({
                            "from_node": from_id,
                            "from_pin": from_pin,
                            "to_node": to_id,
                            "to_pin": target_pin_name,
                        })

    return {
        "name": name,
        "asset_type": "Source",
        "description": f"Imported from UE5 MetaSounds editor export ({len(template_nodes)} nodes)",
        "inputs": graph_inputs,
        "outputs": graph_outputs,
        "nodes": template_nodes,
        "connections": connections,
    }


def _parse_value(val: str, category: str) -> object:
    """Parse string default value to appropriate Python type."""
    if category == "Bool":
        return val.lower() == "true"
    if category in ("Float", "Time"):
        try:
            return float(val)
        except ValueError:
            return val
    if category == "Int32":
        try:
            return int(val)
        except ValueError:
            return val
    return val


# --- CLI ---

def main():
    ap = argparse.ArgumentParser(description="Parse UE5 MetaSounds graph exports")
    ap.add_argument("file", nargs="?", help="File with export text")
    ap.add_argument("--text", help="Direct export text")
    ap.add_argument("--name", default="Untitled", help="Template name")
    ap.add_argument("-o", "--output", help="Output JSON file")
    ap.add_argument("--summary", action="store_true", help="Print summary only")
    args = ap.parse_args()

    if args.file:
        text = Path(args.file).read_text()
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    nodes = parse_export(text)
    print(f"Parsed {len(nodes)} nodes:")
    for n in nodes:
        pin_in = sum(1 for p in n.pins if p.direction == "input")
        pin_out = sum(1 for p in n.pins if p.direction == "output")
        class_info = f"{n.namespace}::{n.name}"
        if n.variant:
            class_info += f" ({n.variant})"
        print(f"  [{n.node_type:8s}] {class_info:40s} pos=({n.pos_x},{n.pos_y}) pins={pin_in}in/{pin_out}out")

    if args.summary:
        return

    template = nodes_to_template(nodes, args.name)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(template, f, indent=2)
        print(f"\nWritten to {args.output}")
    else:
        print(f"\n{json.dumps(template, indent=2)}")


if __name__ == "__main__":
    main()
