#!/usr/bin/env python3
"""Verify all MetaSounds templates against catalogue + engine export data.

Checks:
1. Every node_type in templates exists in METASOUND_NODES catalogue
2. Every pin referenced in connections exists on the node definition
3. Every default key matches an actual input pin name
4. Pin types are compatible across connections
5. Cross-reference node pins against engine export (all_metasound_nodes.json)
6. CLASS_NAME_TO_DISPLAY has no broken forward mappings

Usage:
    python scripts/verify_templates.py
    python scripts/verify_templates.py --engine-check   # also check vs engine JSON
    python scripts/verify_templates.py --verbose         # show per-template detail
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from ue_audio_mcp.knowledge.graph_schema import validate_graph
from ue_audio_mcp.knowledge.metasound_nodes import (
    CLASS_NAME_TO_DISPLAY,
    METASOUND_NODES,
)

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "src", "ue_audio_mcp", "templates", "metasounds",
)

ENGINE_EXPORT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "exports", "all_metasound_nodes.json",
)

BP_TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "src", "ue_audio_mcp", "templates", "blueprints",
)


def load_engine_nodes(path):
    """Load engine export and build lookup by display name."""
    with open(path) as f:
        data = json.load(f)
    by_class = {}
    by_name = {}
    for node in data["nodes"]:
        by_class[node["class_name"]] = node
        name = node["name"]
        by_name.setdefault(name, []).append(node)
    return {"by_class": by_class, "by_name": by_name, "total": data["total"]}


def verify_class_name_mappings():
    """Check CLASS_NAME_TO_DISPLAY has no broken forward mappings."""
    errors = []
    for class_name, display_name in CLASS_NAME_TO_DISPLAY.items():
        if display_name not in METASOUND_NODES:
            errors.append(
                f"CLASS_NAME_TO_DISPLAY['{class_name}'] -> '{display_name}' "
                f"but '{display_name}' not in METASOUND_NODES"
            )
    return errors


def find_class_name_for(ntype):
    """Find class_name for a display name via catalogue or reverse mapping."""
    node_def = METASOUND_NODES.get(ntype)
    if node_def:
        cn = node_def.get("class_name", "")
        if cn:
            return cn
    for cn, dn in CLASS_NAME_TO_DISPLAY.items():
        if dn == ntype:
            return cn
    return ""


def verify_ms_templates(verbose=False):
    """Validate all MS templates via graph_schema.validate_graph."""
    total = 0
    passed = 0
    all_errors = []

    for fname in sorted(os.listdir(TEMPLATE_DIR)):
        if not fname.endswith(".json"):
            continue
        total += 1
        path = os.path.join(TEMPLATE_DIR, fname)
        with open(path) as f:
            spec = json.load(f)

        errors = validate_graph(spec)
        if errors:
            all_errors.append(f"\n  {fname} ({len(errors)} errors):")
            for e in errors:
                all_errors.append(f"    - {e}")
        else:
            passed += 1
            if verbose:
                node_count = len(spec.get("nodes", []))
                conn_count = len(spec.get("connections", []))
                print(f"  OK  {fname} ({node_count} nodes, {conn_count} connections)")

    return total, passed, all_errors


def verify_engine_pins(verbose=False):
    """Cross-check template node pins against engine export."""
    if not os.path.exists(ENGINE_EXPORT):
        return ["ENGINE EXPORT NOT FOUND: " + ENGINE_EXPORT]

    engine = load_engine_nodes(ENGINE_EXPORT)
    issues = []

    for fname in sorted(os.listdir(TEMPLATE_DIR)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(TEMPLATE_DIR, fname)
        with open(path) as f:
            spec = json.load(f)

        for node in spec.get("nodes", []):
            ntype = node.get("node_type", "")
            nid = node.get("id", "")

            if ntype.startswith("__"):
                continue

            class_name = find_class_name_for(ntype)
            if not class_name:
                if verbose:
                    issues.append(
                        f"  INFO {fname}:{nid} - '{ntype}' has no class_name "
                        f"(cannot verify vs engine)"
                    )
                continue

            engine_node = engine["by_class"].get(class_name)
            if not engine_node:
                issues.append(
                    f"  WARN {fname}:{nid} - class_name '{class_name}' "
                    f"not in engine export"
                )
                continue

            engine_inputs = {p["name"] for p in engine_node.get("inputs", [])}

            for dkey in node.get("defaults", {}):
                if dkey not in engine_inputs:
                    issues.append(
                        f"  PIN MISMATCH {fname}:{nid} - default '{dkey}' "
                        f"not in engine inputs {sorted(engine_inputs)}"
                    )

        for conn in spec.get("connections", []):
            from_node = conn["from_node"]
            from_pin = conn["from_pin"]
            to_node = conn["to_node"]
            to_pin = conn["to_pin"]

            if from_node != "__graph__":
                src = next((n for n in spec["nodes"] if n["id"] == from_node), None)
                if src and not src["node_type"].startswith("__"):
                    src_class = find_class_name_for(src["node_type"])
                    if src_class:
                        eng = engine["by_class"].get(src_class)
                        if eng:
                            eng_outs = {p["name"] for p in eng.get("outputs", [])}
                            if from_pin not in eng_outs and eng_outs:
                                issues.append(
                                    f"  PIN MISMATCH {fname}: {from_node}.{from_pin} "
                                    f"not in engine outputs {sorted(eng_outs)}"
                                )

            if to_node != "__graph__":
                dst = next((n for n in spec["nodes"] if n["id"] == to_node), None)
                if dst and not dst["node_type"].startswith("__"):
                    dst_class = find_class_name_for(dst["node_type"])
                    if dst_class:
                        eng = engine["by_class"].get(dst_class)
                        if eng:
                            eng_ins = {p["name"] for p in eng.get("inputs", [])}
                            if to_pin not in eng_ins and eng_ins:
                                issues.append(
                                    f"  PIN MISMATCH {fname}: {to_node}.{to_pin} "
                                    f"not in engine inputs {sorted(eng_ins)}"
                                )

    return issues


def verify_bp_templates(verbose=False):
    """Basic structural check on BP templates."""
    total = 0
    issues = []

    bp_cat_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "src", "ue_audio_mcp", "knowledge", "blueprint_audio_catalogue.json",
    )
    allowlist = set()
    if os.path.exists(bp_cat_path):
        with open(bp_cat_path) as f:
            bp_data = json.load(f)
        allowlist = set(bp_data.get("allowlist", []))

    for fname in sorted(os.listdir(BP_TEMPLATE_DIR)):
        if not fname.endswith(".json"):
            continue
        total += 1
        path = os.path.join(BP_TEMPLATE_DIR, fname)
        with open(path) as f:
            spec = json.load(f)

        if "name" not in spec:
            issues.append(f"  {fname}: missing 'name'")
        if "nodes" not in spec and "steps" not in spec:
            issues.append(f"  {fname}: missing 'nodes' or 'steps'")

        for node in spec.get("nodes", []):
            func = node.get("function", "")
            if func and allowlist and func not in allowlist:
                issues.append(f"  {fname}: function '{func}' not in allowlist")

        if verbose and not any(fname in i for i in issues):
            print(f"  OK  {fname}")

    return total, issues


def main():
    parser = argparse.ArgumentParser(description="Verify templates against DB + engine")
    parser.add_argument("--engine-check", action="store_true",
                        help="Cross-check vs engine JSON")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("TEMPLATE VERIFICATION REPORT")
    print("=" * 60)

    # 1. CLASS_NAME_TO_DISPLAY integrity
    print(f"\n[1] CLASS_NAME_TO_DISPLAY ({len(CLASS_NAME_TO_DISPLAY)} entries)")
    cn_errors = verify_class_name_mappings()
    if cn_errors:
        print(f"  BROKEN FORWARD MAPPINGS: {len(cn_errors)}")
        for e in cn_errors:
            print(f"  {e}")
    else:
        print(f"  All {len(CLASS_NAME_TO_DISPLAY)} mappings resolve to catalogue nodes")

    # 2. MetaSounds templates
    print(f"\n[2] MetaSounds Templates ({TEMPLATE_DIR})")
    ms_total, ms_passed, ms_errors = verify_ms_templates(args.verbose)
    print(f"  {ms_passed}/{ms_total} templates pass validation")
    if ms_errors:
        for e in ms_errors:
            print(e)

    # 3. Engine pin cross-check
    if args.engine_check:
        print(f"\n[3] Engine Pin Cross-Check ({ENGINE_EXPORT})")
        pin_issues = verify_engine_pins(args.verbose)
        if pin_issues:
            mismatches = [i for i in pin_issues if "PIN MISMATCH" in i]
            warnings = [i for i in pin_issues if "WARN" in i]
            infos = [i for i in pin_issues if "INFO" in i]
            print(f"  Pin mismatches: {len(mismatches)}")
            print(f"  Warnings: {len(warnings)}")
            print(f"  Info (no class_name): {len(infos)}")
            for i in mismatches:
                print(i)
            for i in warnings:
                print(i)
            if args.verbose:
                for i in infos:
                    print(i)
        else:
            print("  All template pins match engine data")

    # 4. Blueprint templates
    print(f"\n[4] Blueprint Templates ({BP_TEMPLATE_DIR})")
    bp_total, bp_issues = verify_bp_templates(args.verbose)
    print(f"  {bp_total} templates checked")
    if bp_issues:
        for i in bp_issues:
            print(i)
    else:
        print("  All BP templates pass structural checks")

    # 5. Summary
    print("\n" + "=" * 60)
    total_issues = len(cn_errors) + len(ms_errors) + len(bp_issues)
    if total_issues == 0:
        print(f"ALL CLEAR: {ms_total} MS + {bp_total} BP templates verified")
    else:
        print(f"ISSUES FOUND: {total_issues} total")
    print("=" * 60)

    return 1 if total_issues > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
