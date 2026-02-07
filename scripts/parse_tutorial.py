#!/usr/bin/env python3
"""Parse Epic tutorial text into structured workflow JSON.

Takes raw step-by-step instructions from Epic's UE5 documentation and
produces machine-readable Blueprint/MetaSounds workflow templates.

Supports 6 instruction patterns:
  1. CREATE  — "Add/Create/Place a [NodeType] node"
  2. DRAG    — "Drag off [Pin] and create/add [NodeType]"
  3. SET     — "Enter/Set/Type [Value] for/in [Pin]"
  4. CONNECT — "Connect [Node.Pin] to [Node.Pin]"
  5. ASSET   — "Select [Asset] in/for [Property]"
  6. REMOVE  — "Remove/Disconnect/Delete [connection]"

Usage:
    python scripts/parse_tutorial.py tutorial_text.txt --name "Wind Blueprint"
    python scripts/parse_tutorial.py --text "Step 1: Add a..." --name "Bomb"
    python scripts/parse_tutorial.py --validate workflow.json

Outputs:
    Structured JSON workflow in our template format (same as metasounds/*.json)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# --- Instruction types ---

@dataclass
class CreateInstr:
    """Create a new node."""
    node_type: str
    node_id: str = ""
    from_pin: str = ""
    from_node: str = ""
    position: tuple[int, int] = (0, 0)

@dataclass
class SetInstr:
    """Set a value on a pin/property."""
    node_id: str
    pin_name: str
    value: str

@dataclass
class ConnectInstr:
    """Connect two pins."""
    from_node: str
    from_pin: str
    to_node: str
    to_pin: str

@dataclass
class AssetInstr:
    """Select an asset for a property."""
    node_id: str
    property_name: str
    asset: str

@dataclass
class RemoveInstr:
    """Remove a connection."""
    node_id: str
    pin_name: str


# --- Node name normalisation ---

NODE_ALIASES = {
    "Spawn Sound 2D": "SpawnSound2D",
    "Spawn Sound at Location": "SpawnSoundAtLocation",
    "Play Sound 2D": "PlaySound2D",
    "Play Sound at Location": "PlaySoundAtLocation",
    "Event BeginPlay": "EventBeginPlay",
    "Event Tick": "EventTick",
    "Event End Play": "EventEndPlay",
    "Get Player Pawn": "GetPlayerPawn",
    "Get Velocity": "GetVelocity",
    "Vector Length": "VectorLength",
    "Get Actor Forward Vector": "GetActorForwardVector",
    "Get Actor Location": "GetActorLocation",
    "Set Float Parameter": "SetFloatParameter",
    "Set Integer Parameter": "SetIntegerParameter",
    "Set Boolean Parameter": "SetBooleanParameter",
    "Set Wave Parameter": "SetWaveParameter",
    "Make Literal Float": "MakeLiteralFloat",
    "Make Literal Int": "MakeLiteralInt",
    "Make Literal Bool": "MakeLiteralBool",
    "For Each Loop": "ForEachLoop",
    "Break Vector": "BreakVector",
    "Make Vector": "MakeVector",
    "Spawn Sound Attached": "SpawnSoundAttached",
    "Add Spectral Analysis Delegate": "AddSpectralAnalysisDelegate",
    "Make Full Spectrum Spectral Analysis Band Settings": "MakeFullSpectrumSpectralAnalysisBandSettings",
    "Get Actor Scale 3D": "GetActorScale3D",
    "Set Actor Scale 3D": "SetActorScale3D",
    "Is Shift Down": "IsInputKeyDown",
    "Get Modifier Keys State": "GetModifierKeysState",
}


def _make_id(name: str, existing_ids: set[str]) -> str:
    """Generate a unique snake_case ID from a node name."""
    raw = re.sub(r'[^a-zA-Z0-9]', '_', name)
    raw = re.sub(r'([a-z])([A-Z])', r'\1_\2', raw)
    raw = re.sub(r'_+', '_', raw).strip('_').lower()

    if raw not in existing_ids:
        existing_ids.add(raw)
        return raw

    for i in range(2, 100):
        candidate = f"{raw}_{i}"
        if candidate not in existing_ids:
            existing_ids.add(candidate)
            return candidate
    return raw


def _clean(text: str) -> str:
    """Strip markdown/HTML artifacts."""
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'`', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()


# --- Pattern matchers ---

RE_CREATE = re.compile(
    r'(?:add|create|place|search for and (?:add|select)|right-click and (?:add|create))\s+'
    r'(?:a\s+|an\s+)?'
    r'(?:new\s+)?'
    r'(.+?)\s*(?:node|nodes?)\b',
    re.IGNORECASE
)

RE_DRAG = re.compile(
    r'(?:drag\s+off|from)\s+(?:the\s+)?(.+?)\s+'
    r'(?:output\s+)?(?:pin\s+)?'
    r'(?:and\s+)?(?:create|add|select)\s+'
    r'(?:a\s+|an\s+)?(.+?)\s*(?:node|$)',
    re.IGNORECASE
)

RE_SET = re.compile(
    r'(?:enter|set|type|input|change)\s+'
    r'(.+?)\s+'
    r'(?:for|in|into|as|to)\s+(?:the\s+)?'
    r'(.+?)(?:\s+(?:input|pin|field|property|value))?\s*$',
    re.IGNORECASE
)

RE_SET_ALT = re.compile(
    r'(?:set\s+)?(?:the\s+)?(.+?)\s+'
    r'(?:to|=)\s+(.+)',
    re.IGNORECASE
)

RE_CONNECT = re.compile(
    r'connect\s+(?:the\s+)?(.+?)\s+'
    r'(?:output\s+)?(?:pin\s+)?(?:to|into)\s+(?:the\s+)?(.+?)(?:\s+(?:input|pin))?\s*$',
    re.IGNORECASE
)

RE_ASSET = re.compile(
    r'(?:select|choose|pick)\s+'
    r'(.+?)\s+'
    r'(?:in|for|as)\s+(?:the\s+)?'
    r'(.+?)(?:\s+(?:dropdown|property|field|selector))?\s*$',
    re.IGNORECASE
)

RE_REMOVE = re.compile(
    r'(?:remove|disconnect|delete|break)\s+'
    r'(?:the\s+)?(?:connection\s+)?(?:from\s+|to\s+)?'
    r'(.+)',
    re.IGNORECASE
)


def parse_step(text: str, existing_ids: set[str], nodes: dict) -> list:
    """Parse a single instruction step into structured instructions."""
    text = _clean(text)
    instructions = []

    # Try DRAG first (more specific than CREATE)
    m = RE_DRAG.search(text)
    if m:
        pin_ref = m.group(1).strip()
        node_type = m.group(2).strip()
        canonical = NODE_ALIASES.get(node_type, node_type)
        nid = _make_id(canonical, existing_ids)
        instr = CreateInstr(
            node_type=canonical,
            node_id=nid,
            from_pin=pin_ref,
        )
        nodes[nid] = canonical
        instructions.append(instr)
        return instructions

    # Try CONNECT
    m = RE_CONNECT.search(text)
    if m:
        src = m.group(1).strip()
        dst = m.group(2).strip()
        instructions.append(ConnectInstr(
            from_node="", from_pin=src,
            to_node="", to_pin=dst,
        ))
        return instructions

    # Try SET
    m = RE_SET.search(text)
    if m:
        val = m.group(1).strip()
        pin = m.group(2).strip()
        instructions.append(SetInstr(node_id="", pin_name=pin, value=val))
        return instructions

    # Try CREATE
    m = RE_CREATE.search(text)
    if m:
        node_type = m.group(1).strip()
        canonical = NODE_ALIASES.get(node_type, node_type)
        nid = _make_id(canonical, existing_ids)
        instr = CreateInstr(node_type=canonical, node_id=nid)
        nodes[nid] = canonical
        instructions.append(instr)
        return instructions

    # Try ASSET
    m = RE_ASSET.search(text)
    if m:
        asset = m.group(1).strip()
        prop = m.group(2).strip()
        instructions.append(AssetInstr(node_id="", property_name=prop, asset=asset))
        return instructions

    # Try REMOVE
    m = RE_REMOVE.search(text)
    if m:
        target = m.group(1).strip()
        instructions.append(RemoveInstr(node_id="", pin_name=target))
        return instructions

    return instructions


def parse_tutorial_text(text: str) -> list:
    """Parse full tutorial text into a list of instructions."""
    all_instructions = []
    existing_ids: set[str] = set()
    nodes: dict[str, str] = {}

    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Remove step numbering
        line = re.sub(r'^\d+[\.\)]\s*', '', line)
        line = re.sub(r'^[-\u2022]\s*', '', line)
        line = re.sub(r'^Step\s+\d+[:\.]?\s*', '', line, flags=re.IGNORECASE)

        if not line or len(line) < 5:
            continue

        instructions = parse_step(line, existing_ids, nodes)
        for instr in instructions:
            all_instructions.append({
                "raw": line,
                "parsed": instr,
            })

    return all_instructions


# --- Workflow builder ---

@dataclass
class WorkflowTemplate:
    """A complete Blueprint or MetaSounds workflow."""
    name: str
    workflow_type: str  # "blueprint" or "metasounds"
    description: str = ""
    source_url: str = ""
    nodes: list = field(default_factory=list)
    connections: list = field(default_factory=list)
    defaults: list = field(default_factory=list)
    assets: list = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "type": self.workflow_type,
            "description": self.description,
            "source_url": self.source_url,
            "nodes": self.nodes,
            "connections": self.connections,
            "defaults": self.defaults,
            "assets": self.assets,
        }


def build_workflow(
    name: str,
    workflow_type: str,
    instructions: list,
    description: str = "",
    source_url: str = "",
) -> WorkflowTemplate:
    """Build a WorkflowTemplate from parsed instructions."""
    wf = WorkflowTemplate(
        name=name,
        workflow_type=workflow_type,
        description=description,
        source_url=source_url,
    )

    x, y = 0, 0
    x_step, y_step = 300, 200

    for item in instructions:
        instr = item["parsed"]

        if isinstance(instr, CreateInstr):
            wf.nodes.append({
                "id": instr.node_id,
                "node_type": instr.node_type,
                "position": [x, y],
            })
            if instr.from_pin and instr.from_node:
                wf.connections.append({
                    "from_node": instr.from_node,
                    "from_pin": instr.from_pin,
                    "to_node": instr.node_id,
                    "to_pin": "In",
                })
            x += x_step
            if x > 1500:
                x = 0
                y += y_step

        elif isinstance(instr, ConnectInstr):
            wf.connections.append({
                "from_node": instr.from_node,
                "from_pin": instr.from_pin,
                "to_node": instr.to_node,
                "to_pin": instr.to_pin,
            })

        elif isinstance(instr, SetInstr):
            wf.defaults.append({
                "node_id": instr.node_id,
                "pin": instr.pin_name,
                "value": instr.value,
            })

        elif isinstance(instr, AssetInstr):
            wf.assets.append({
                "node_id": instr.node_id,
                "property": instr.property_name,
                "asset": instr.asset,
            })

    return wf


# --- Validator ---

def validate_workflow(workflow: dict, node_specs: dict | None = None) -> list[str]:
    """Validate a workflow template. Returns list of issues."""
    issues = []

    if "nodes" not in workflow:
        issues.append("Missing 'nodes' array")
    if "connections" not in workflow:
        issues.append("Missing 'connections' array")

    if not workflow.get("nodes"):
        issues.append("Empty nodes array")
        return issues

    node_ids = set()
    for node in workflow["nodes"]:
        nid = node.get("id", "")
        if not nid:
            issues.append(f"Node missing 'id': {node}")
        elif nid in node_ids:
            issues.append(f"Duplicate node id: {nid}")
        node_ids.add(nid)

    for conn in workflow.get("connections", []):
        fn = conn.get("from_node", "")
        tn = conn.get("to_node", "")
        if fn and fn != "__graph__" and fn not in node_ids:
            issues.append(f"Connection references unknown from_node: {fn}")
        if tn and tn != "__graph__" and tn not in node_ids:
            issues.append(f"Connection references unknown to_node: {tn}")

    if node_specs:
        for node in workflow["nodes"]:
            ntype = node.get("node_type", "")
            if ntype and ntype not in node_specs:
                compact = ntype.replace(" ", "")
                if compact not in node_specs:
                    issues.append(f"Unknown node type: {ntype} (not in scraped specs)")

    return issues


# --- CLI ---

def main():
    ap = argparse.ArgumentParser(description="Parse Epic tutorial text into workflow JSON")
    ap.add_argument("file", nargs="?", help="Text file with tutorial instructions")
    ap.add_argument("--text", help="Direct tutorial text (instead of file)")
    ap.add_argument("--name", default="Untitled", help="Workflow name")
    ap.add_argument("--type", choices=["blueprint", "metasounds"], default="blueprint")
    ap.add_argument("--description", default="")
    ap.add_argument("--url", default="", help="Source tutorial URL")
    ap.add_argument("--validate", help="Validate an existing workflow JSON file")
    ap.add_argument("--specs", help="Path to bp_node_specs.json for validation")
    ap.add_argument("--output", "-o", help="Output JSON file")
    args = ap.parse_args()

    if args.validate:
        with open(args.validate) as f:
            workflow = json.load(f)
        specs = None
        if args.specs:
            with open(args.specs) as f:
                specs = json.load(f)
        issues = validate_workflow(workflow, specs)
        if issues:
            for i in issues:
                print(f"  - {i}")
            sys.exit(1)
        else:
            print("Workflow is valid.")
            sys.exit(0)

    if args.file:
        text = Path(args.file).read_text()
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    instructions = parse_tutorial_text(text)
    print(f"Parsed {len(instructions)} instructions:")
    for item in instructions:
        instr = item["parsed"]
        print(f"  {type(instr).__name__:15s} | {item['raw'][:70]}")

    wf = build_workflow(
        name=args.name,
        workflow_type=args.type,
        instructions=instructions,
        description=args.description,
        source_url=args.url,
    )

    result = wf.to_json()

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nWritten to {args.output}")
    else:
        print(f"\n{json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()
