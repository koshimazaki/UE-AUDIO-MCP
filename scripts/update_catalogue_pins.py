#!/usr/bin/env python3
"""Update catalogue pin definitions from engine exports.

Reads the engine export JSON (source of truth for pin names/types/defaults)
and patches the catalogue JSON to match. Preserves catalogue-only fields
like ``required``, ``description``, ``tags``, ``complexity``, and ``mcp_notes``.

Usage:
    python scripts/update_catalogue_pins.py                    # Dry-run (show changes)
    python scripts/update_catalogue_pins.py --apply            # Apply to catalogue JSON
    python scripts/update_catalogue_pins.py --apply --export   # Apply + regenerate catalogues
    python scripts/update_catalogue_pins.py --update-source    # Also patch metasound_nodes.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

# Ensure package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ue_audio_mcp.knowledge.node_schema import normalize_pin_type
from ue_audio_mcp.knowledge.metasound_nodes import (
    METASOUND_NODES,
    CLASS_NAME_TO_DISPLAY,
)

# Paths
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_SCRIPT_DIR)
_ENGINE_EXPORT = os.path.join(_ROOT, "exports", "all_metasound_nodes.json")
_CATALOGUE_JSON = os.path.join(
    _ROOT, "src", "ue_audio_mcp", "knowledge", "metasound_catalogue.json",
)
_METASOUND_NODES_PY = os.path.join(
    _ROOT, "src", "ue_audio_mcp", "knowledge", "metasound_nodes.py",
)


def _load_engine_nodes(path: str) -> dict[str, dict]:
    """Load engine export and index by class_name."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    result: dict[str, dict] = {}
    for node in data.get("nodes", []):
        cn = node.get("class_name", "")
        if cn and cn not in result:
            result[cn] = node
    return result


def _normalize_engine_pin(pin: dict) -> dict:
    """Convert engine pin to catalogue format."""
    return {
        "name": pin["name"],
        "type": normalize_pin_type(pin.get("type", "")),
    }


def _pins_match(cat_pins: list[dict], eng_pins: list[dict]) -> bool:
    """Check if catalogue pins match engine pins (names + normalized types)."""
    if len(cat_pins) != len(eng_pins):
        return False
    cat_set = {(p["name"], normalize_pin_type(p.get("type", ""))) for p in cat_pins}
    eng_set = {(p["name"], normalize_pin_type(p.get("type", ""))) for p in eng_pins}
    return cat_set == eng_set


def _merge_pins(cat_pins: list[dict], eng_pins: list[dict]) -> list[dict]:
    """Merge engine pins into catalogue pins, preserving catalogue-only fields.

    Engine owns: name, type, default.
    Catalogue owns: required, description (if present).
    """
    # Index catalogue pins by name for fast lookup
    cat_by_name: dict[str, dict] = {p["name"]: p for p in cat_pins}

    merged = []
    for epin in eng_pins:
        norm_type = normalize_pin_type(epin.get("type", ""))
        new_pin: dict = {
            "name": epin["name"],
            "type": norm_type,
        }

        # Preserve catalogue-only fields if matching by name
        cat_pin = cat_by_name.get(epin["name"])
        if cat_pin:
            if "required" in cat_pin:
                new_pin["required"] = cat_pin["required"]
            if "description" in cat_pin:
                new_pin["description"] = cat_pin["description"]

        # Engine default wins
        if "default" in epin and epin["default"] is not None:
            new_pin["default"] = epin["default"]
        elif cat_pin and "default" in cat_pin:
            new_pin["default"] = cat_pin["default"]

        merged.append(new_pin)

    return merged


def _format_pin_diff(label: str, cat_pins: list[dict], eng_pins: list[dict]) -> list[str]:
    """Format human-readable diff between catalogue and engine pins."""
    changes = []
    cat_by_name = {p["name"]: p for p in cat_pins}
    eng_by_name = {p["name"]: p for p in eng_pins}
    cat_names = set(cat_by_name)
    eng_names = set(eng_by_name)

    for name in sorted(eng_names - cat_names):
        etype = normalize_pin_type(eng_by_name[name].get("type", ""))
        changes.append(f"  +{label}: {name} ({etype})")
    for name in sorted(cat_names - eng_names):
        ctype = normalize_pin_type(cat_by_name[name].get("type", ""))
        changes.append(f"  -{label}: {name} ({ctype})")
    for name in sorted(cat_names & eng_names):
        ct = normalize_pin_type(cat_by_name[name].get("type", ""))
        et = normalize_pin_type(eng_by_name[name].get("type", ""))
        if ct != et:
            changes.append(f"  ~{label}: {name} {ct} -> {et}")

    return changes


def compute_updates(engine_path: str) -> tuple[list[dict], dict]:
    """Compute pin updates needed.

    Returns (updates_list, stats_dict).
    Each update: {"name", "class_name", "input_changes", "output_changes",
                   "new_inputs", "new_outputs"}
    """
    engine_by_class = _load_engine_nodes(engine_path)

    updates = []
    stats = {"checked": 0, "matched": 0, "updated": 0, "skipped_no_cn": 0,
             "skipped_not_in_engine": 0, "total_pin_changes": 0}

    for name, node in sorted(METASOUND_NODES.items()):
        cn = node.get("class_name", "")
        if not cn:
            stats["skipped_no_cn"] += 1
            continue

        if cn not in engine_by_class:
            stats["skipped_not_in_engine"] += 1
            continue

        stats["checked"] += 1
        enode = engine_by_class[cn]

        cat_inputs = node.get("inputs", [])
        cat_outputs = node.get("outputs", [])
        eng_inputs = enode.get("inputs", [])
        eng_outputs = enode.get("outputs", [])

        inputs_ok = _pins_match(cat_inputs, eng_inputs)
        outputs_ok = _pins_match(cat_outputs, eng_outputs)

        if inputs_ok and outputs_ok:
            stats["matched"] += 1
            continue

        input_changes = _format_pin_diff("input", cat_inputs, eng_inputs)
        output_changes = _format_pin_diff("output", cat_outputs, eng_outputs)
        pin_count = len(input_changes) + len(output_changes)

        updates.append({
            "name": name,
            "class_name": cn,
            "input_changes": input_changes,
            "output_changes": output_changes,
            "new_inputs": _merge_pins(cat_inputs, eng_inputs),
            "new_outputs": _merge_pins(cat_outputs, eng_outputs),
        })
        stats["updated"] += 1
        stats["total_pin_changes"] += pin_count

    return updates, stats


def apply_to_catalogue_json(updates: list[dict], catalogue_path: str) -> None:
    """Apply pin updates to the catalogue JSON file."""
    with open(catalogue_path, encoding="utf-8") as f:
        catalogue = json.load(f)

    # Index by name for fast lookup
    nodes_by_name: dict[str, dict] = {}
    for node in catalogue.get("nodes", []):
        nodes_by_name[node["name"]] = node

    applied = 0
    for upd in updates:
        cat_node = nodes_by_name.get(upd["name"])
        if not cat_node:
            continue
        cat_node["inputs"] = upd["new_inputs"]
        cat_node["outputs"] = upd["new_outputs"]
        applied += 1

    with open(catalogue_path, "w", encoding="utf-8") as f:
        json.dump(catalogue, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Applied {applied} node updates to {catalogue_path}")


def apply_to_source(updates: list[dict], source_path: str) -> None:
    """Apply pin updates to metasound_nodes.py source file.

    Best-effort: finds _register(_node("NodeName", ... blocks
    and replaces the inputs/outputs lists.
    """
    with open(source_path, encoding="utf-8") as f:
        content = f.read()

    applied = 0
    skipped = 0

    for upd in updates:
        name = upd["name"]
        escaped_name = re.escape(name)
        pattern = re.compile(
            r'(_register\(_node\(\s*\n\s*"' + escaped_name + r'".*?\n\)\))',
            re.DOTALL,
        )
        match = pattern.search(content)
        if not match:
            skipped += 1
            continue

        block = match.group(1)

        new_inputs_str = _format_pins_as_source(upd["new_inputs"], is_input=True)
        new_outputs_str = _format_pins_as_source(upd["new_outputs"], is_input=False)

        new_block = _replace_pin_lists(block, new_inputs_str, new_outputs_str)
        if new_block and new_block != block:
            content = content.replace(block, new_block)
            applied += 1
        else:
            skipped += 1

    with open(source_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Source: applied {applied}, skipped {skipped} of {len(updates)} updates to {source_path}")


def _format_pins_as_source(pins: list[dict], is_input: bool) -> str:
    """Format pins as Python source code for metasound_nodes.py."""
    lines = []
    for pin in pins:
        name = pin["name"]
        ptype = pin["type"]
        if is_input:
            parts = [f'_in("{name}", "{ptype}"']
            req = pin.get("required")
            default = pin.get("default")
            if req is False:
                parts.append(", required=False")
            if default is not None:
                parts.append(f", default={_format_default(default)}")
            parts.append(")")
            lines.append("     " + "".join(parts))
        else:
            lines.append(f'     _out("{name}", "{ptype}")')
    return ",\n".join(lines)


def _format_default(val: object) -> str:
    """Format a default value for Python source."""
    if isinstance(val, bool):
        return str(val)
    if isinstance(val, (int, float)):
        return repr(val)
    if isinstance(val, str):
        return f'"{val}"'
    return repr(val)


def _replace_pin_lists(block: str, new_inputs: str, new_outputs: str) -> str | None:
    """Replace input and output pin lists in a _register(_node(...)) block."""
    brackets = _find_bracket_pairs(block)
    if len(brackets) < 2:
        return None

    # First bracket pair = inputs, second = outputs
    inp_start, inp_end = brackets[0]
    out_start, out_end = brackets[1]

    new_block = (
        block[:inp_start]
        + "[" + new_inputs + "]"
        + block[inp_end + 1:out_start]
        + "[" + new_outputs + "]"
        + block[out_end + 1:]
    )
    return new_block


def _find_bracket_pairs(text: str) -> list[tuple[int, int]]:
    """Find balanced [...] pairs in text, skipping nested brackets."""
    pairs = []
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "[":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0 and start >= 0:
                pairs.append((start, i))
                start = -1
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update catalogue pins from engine exports",
    )
    parser.add_argument("--engine-json", default=_ENGINE_EXPORT,
                        help="Path to engine export JSON")
    parser.add_argument("--catalogue-json", default=_CATALOGUE_JSON,
                        help="Path to catalogue JSON")
    parser.add_argument("--apply", action="store_true",
                        help="Apply changes to catalogue JSON")
    parser.add_argument("--export", action="store_true",
                        help="Regenerate catalogue JSONs after applying")
    parser.add_argument("--update-source", action="store_true",
                        help="Also patch metasound_nodes.py (best-effort)")
    args = parser.parse_args()

    if not os.path.isfile(args.engine_json):
        print(f"Engine export not found: {args.engine_json}")
        print("Run: python scripts/sync_nodes_from_engine.py  (with UE Editor running)")
        sys.exit(1)

    updates, stats = compute_updates(args.engine_json)

    # Print summary
    print("=" * 60)
    print("  Pin Update Report")
    print("=" * 60)
    print(f"Checked:           {stats['checked']} nodes with class_name")
    print(f"Already match:     {stats['matched']}")
    print(f"Need update:       {stats['updated']}")
    print(f"Total pin changes: {stats['total_pin_changes']}")
    print(f"Skipped (no CN):   {stats['skipped_no_cn']}")
    print(f"Skipped (not in engine): {stats['skipped_not_in_engine']}")

    if updates:
        print(f"\n--- Changes ({len(updates)} nodes) ---")
        for upd in updates:
            print(f"\n  {upd['name']}  ({upd['class_name']})")
            for line in upd["input_changes"]:
                print(f"    {line}")
            for line in upd["output_changes"]:
                print(f"    {line}")

    if not args.apply:
        if updates:
            print(f"\nDry run. Use --apply to write changes.")
        return

    # Apply to catalogue JSON
    apply_to_catalogue_json(updates, args.catalogue_json)

    # Optionally patch source
    if args.update_source:
        apply_to_source(updates, _METASOUND_NODES_PY)

    # Optionally regenerate catalogue exports
    if args.export:
        print("\nRegenerating catalogue exports...")
        import subprocess
        subprocess.run(
            [sys.executable, os.path.join(_SCRIPT_DIR, "export_catalogues.py")],
            check=True,
        )

    print("\nDone. Next steps:")
    print("  1. Reseed DB:  python -c \"from ue_audio_mcp.knowledge.db import get_knowledge_db; from ue_audio_mcp.knowledge.seed import seed_database; db = get_knowledge_db(); seed_database(db)\"")
    print("  2. Cross-ref:  python scripts/cross_reference.py --metasounds")
    print("  3. Templates:  python scripts/verify_templates.py")
    print("  4. Tests:      python -m pytest tests/ -x -q")


if __name__ == "__main__":
    main()
