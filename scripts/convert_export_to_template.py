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

from ue_audio_mcp.knowledge.metasound_nodes import METASOUND_NODES


# ---------------------------------------------------------------------------
# Class name -> display name mapping (reverse of C++ NodeRegistry)
# ---------------------------------------------------------------------------

# Known class_name patterns -> display names (from AudioMCPNodeRegistry.h)
CLASS_NAME_TO_DISPLAY: dict[str, str] = {
    "UE::Sine::Audio": "Sine",
    "UE::Saw::Audio": "Saw",
    "UE::Square::Audio": "Square",
    "UE::Triangle::Audio": "Triangle",
    "UE::LFO::Audio": "LFO",
    "UE::Noise::Audio": "Noise",
    "UE::Wave Player::Mono": "Wave Player (Mono)",
    "UE::Wave Player::Stereo": "Wave Player (Stereo)",
    "UE::AD Envelope::Audio": "AD Envelope (Audio)",
    "UE::AD Envelope::Float": "AD Envelope (Float)",
    "UE::Decay Envelope::Audio": "Decay Envelope",
    "UE::Compressor::Audio": "Compressor",
    "UE::Ladder Filter::Audio": "Ladder Filter",
    "UE::State Variable Filter::Audio": "State Variable Filter",
    "UE::One-Pole Low Pass Filter::Audio": "One-Pole Low Pass Filter",
    "UE::One-Pole High Pass Filter::Audio": "One-Pole High Pass Filter",
    "UE::Biquad Filter::Audio": "Biquad Filter",
    "UE::Bitcrusher::Audio": "BitCrusher",
    "UE::Chorus::Audio": "Chorus",
    "UE::Delay::Audio": "Delay (Audio)",
    "UE::Delay::Time": "Delay (Time)",
    "UE::Flanger::Audio": "Flanger (Effects)",
    "UE::Phaser::Audio": "Phaser",
    "UE::Stereo Delay::Audio": "Stereo Delay",
    "UE::Freeverb::Stereo": "Freeverb (Stereo)",
    "UE::Plate Reverb::Stereo": "Plate Reverb (Stereo)",
    "UE::Add::Audio": "Add (Audio)",
    "UE::Add::Float": "Add (Float)",
    "UE::Add::Int32": "Add (Int32)",
    "UE::Subtract::Audio": "Subtract (Audio)",
    "UE::Subtract::Float": "Subtract (Float)",
    "UE::Multiply::Audio": "Multiply (Audio)",
    "UE::Multiply::Float": "Multiply (Float)",
    "UE::Divide::Float": "Divide (Float)",
    "UE::Modulo::Float": "Modulo (Float)",
    "UE::Clamp::Audio": "Clamp (Audio)",
    "UE::Clamp::Float": "Clamp (Float)",
    "UE::Map Range::Float": "Map Range (Float)",
    "UE::Mix Stereo::Audio": "Stereo Mixer",
    "UE::Mono Mixer::Audio": "Mono Mixer",
    "UE::Stereo Panner::Audio": "Stereo Panner",
    "UE::ITD Panner::Audio": "ITD Panner",
    "UE::Gain::Audio": "Gain",
    "UE::MidiNoteToFrequency::Float": "MIDI To Frequency",
    "UE::FrequencyToMidi::Float": "Frequency To MIDI",
    "UE::SemitoneToFrequencyMultiplier::Float": "Semitone To Freq Multiplier",
    "UE::BPM To Seconds::Float": "BPM To Seconds",
    "UE::Trigger Repeat::Audio": "Trigger Repeat",
    "UE::Trigger Counter::Audio": "Trigger Counter",
    "UE::Trigger Route::Audio": "Trigger Route",
    "UE::Trigger Sequence::Audio": "Trigger Sequence",
    "UE::Random Get::Audio": "Random Get (Audio)",
    "UE::Random Get::Float": "Random Get (Float)",
    "UE::InterpTo::Float": "InterpTo (Float)",
    "UE::InterpTo::Audio": "InterpTo (Audio)",
    "UE::Crossfade::Audio": "Crossfade",
    "UE::Ring Modulator::Audio": "Ring Modulator",
    "UE::WaveShaper::Audio": "WaveShaper",
    "UE::Envelope Follower::Audio": "Envelope Follower (Utility)",
    "UE::Linear To Log Frequency::Float": "Linear To Log Frequency",
    "UE::Trigger On Threshold::Audio": "Trigger On Threshold",
    "UE::Send To Audio Bus::Audio": "Send To Audio Bus",
}


def class_name_to_display(class_name: str) -> str | None:
    """Convert a UE class_name like 'UE::Sine::Audio' to display name 'Sine'.

    Returns None if no mapping found.
    """
    if class_name in CLASS_NAME_TO_DISPLAY:
        return CLASS_NAME_TO_DISPLAY[class_name]

    # Try fuzzy: extract the Name part from Namespace::Name::Variant
    parts = class_name.split("::")
    if len(parts) >= 2:
        name_part = parts[1].strip()
        variant = parts[2].strip() if len(parts) >= 3 else ""

        # Check direct name match
        if name_part in METASOUND_NODES:
            return name_part

        # Check "Name (Variant)" pattern
        if variant:
            with_variant = f"{name_part} ({variant})"
            if with_variant in METASOUND_NODES:
                return with_variant

    return None


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
    # Extract asset name from path
    asset_path = export_data.get("asset_path", "")
    asset_name = asset_path.rstrip("/").split("/")[-1].split(".")[-1]
    if "." in asset_name:
        asset_name = asset_name.split(".")[-1]

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

    for i, node in enumerate(nodes_raw):
        node_id = node.get("node_id", "")
        class_type = node.get("class_type", "External")
        node_name = node.get("name", f"node_{i}")

        if class_type == "Input":
            input_nodes[node_id] = node_name
            guid_to_short[node_id] = "__graph__"
        elif class_type == "Output":
            output_nodes[node_id] = node_name
            guid_to_short[node_id] = "__graph__"
        elif class_type in ("Variable", "VariableAccessor", "VariableMutator", "VariableDeferred"):
            short = _make_short_id(node_name, i)
            guid_to_short[node_id] = short
            external_nodes.append(node)
        else:
            short = _make_short_id(node_name, i)
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

    # Convert edges to template connections
    template["connections"] = []
    edges = export_data.get("edges", [])
    for edge in edges:
        from_guid = edge.get("from_node", "")
        to_guid = edge.get("to_node", "")
        from_pin = edge.get("from_pin", "")
        to_pin = edge.get("to_pin", "")

        from_short = guid_to_short.get(from_guid, from_guid)
        to_short = guid_to_short.get(to_guid, to_guid)

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


def _make_short_id(name: str, index: int) -> str:
    """Convert a node name to a short, snake_case ID."""
    short = re.sub(r"[^a-zA-Z0-9\s]", "", name).strip().lower()
    short = re.sub(r"\s+", "_", short)
    if not short:
        short = f"node_{index}"
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
