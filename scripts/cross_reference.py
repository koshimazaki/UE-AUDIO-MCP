#!/usr/bin/env python3
"""Cross-reference engine exports against hand-curated catalogues.

Compares MetaSounds node classes and Blueprint functions between what
the running UE5 engine reports vs. what our curated catalogues contain.

Usage:
    python scripts/cross_reference.py --metasounds    # MS engine vs catalogue
    python scripts/cross_reference.py --blueprints    # BP engine vs catalogue
    python scripts/cross_reference.py --all           # Both
    python scripts/cross_reference.py --all --from-json exports/  # Use saved JSON

Without --from-json, reads from the curated catalogues only (offline mode).
With --from-json, reads engine exports from the specified directory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Ensure package is importable when running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))


# ---------------------------------------------------------------------------
# MetaSounds cross-reference
# ---------------------------------------------------------------------------

def cross_ref_metasounds(engine_json_path: str | None = None) -> dict:
    """Compare MetaSounds engine exports against catalogue.

    Returns a report dict with matched, missing_from_engine, missing_from_catalogue.
    """
    from ue_audio_mcp.knowledge.metasound_nodes import (
        METASOUND_NODES,
        CLASS_NAME_TO_DISPLAY,
        DISPLAY_TO_CLASS,
    )

    # Build catalogue index: class_name -> display_name
    cat_by_class: dict[str, str] = {}
    cat_by_name: dict[str, dict] = {}
    for name, node in METASOUND_NODES.items():
        cn = node.get("class_name", "")
        cat_by_name[name] = node
        if cn:
            cat_by_class[cn] = name

    # Load engine data if available
    engine_nodes: list[dict] = []
    if engine_json_path and os.path.isfile(engine_json_path):
        with open(engine_json_path, encoding="utf-8") as f:
            data = json.load(f)
        engine_nodes = data.get("nodes", [])

    if not engine_nodes:
        # Offline mode: just report catalogue stats
        with_cn = sum(1 for n in METASOUND_NODES.values() if n.get("class_name"))
        return {
            "mode": "offline",
            "catalogue_total": len(METASOUND_NODES),
            "with_class_name": with_cn,
            "without_class_name": len(METASOUND_NODES) - with_cn,
            "class_name_coverage": "{}/{} ({}%)".format(
                with_cn, len(METASOUND_NODES),
                100 * with_cn // max(len(METASOUND_NODES), 1)),
        }

    # Deduplicate engine nodes by class_name
    seen: set[str] = set()
    unique_engine: list[dict] = []
    for node in engine_nodes:
        cn = node.get("class_name", "")
        if cn and cn not in seen:
            seen.add(cn)
            unique_engine.append(node)

    engine_by_class: dict[str, dict] = {}
    for node in unique_engine:
        cn = node.get("class_name", "")
        if cn:
            engine_by_class[cn] = node

    # Cross-reference
    matched = []
    pin_mismatches = []
    missing_from_engine = []
    missing_from_catalogue = []

    # Check catalogue nodes against engine
    for name, node in sorted(METASOUND_NODES.items()):
        cn = node.get("class_name", "")
        if not cn:
            missing_from_engine.append({"name": name, "reason": "no class_name in catalogue"})
            continue

        if cn in engine_by_class:
            enode = engine_by_class[cn]
            matched.append({"name": name, "class_name": cn})

            # Compare pins
            cat_inputs = {p["name"]: p.get("type", "") for p in node.get("inputs", [])}
            eng_inputs = {p["name"]: p.get("type", "") for p in enode.get("inputs", [])}
            cat_outputs = {p["name"]: p.get("type", "") for p in node.get("outputs", [])}
            eng_outputs = {p["name"]: p.get("type", "") for p in enode.get("outputs", [])}

            changes = []
            for pn in sorted(set(eng_inputs) - set(cat_inputs)):
                changes.append("+input: {} ({})".format(pn, eng_inputs[pn]))
            for pn in sorted(set(cat_inputs) - set(eng_inputs)):
                changes.append("-input: {} ({})".format(pn, cat_inputs[pn]))
            for pn in sorted(set(cat_inputs) & set(eng_inputs)):
                if cat_inputs[pn] != eng_inputs[pn]:
                    changes.append("~input: {} {} -> {}".format(pn, cat_inputs[pn], eng_inputs[pn]))
            for pn in sorted(set(eng_outputs) - set(cat_outputs)):
                changes.append("+output: {} ({})".format(pn, eng_outputs[pn]))
            for pn in sorted(set(cat_outputs) - set(eng_outputs)):
                changes.append("-output: {} ({})".format(pn, cat_outputs[pn]))
            for pn in sorted(set(cat_outputs) & set(eng_outputs)):
                if cat_outputs[pn] != eng_outputs[pn]:
                    changes.append("~output: {} {} -> {}".format(pn, cat_outputs[pn], eng_outputs[pn]))

            if changes:
                pin_mismatches.append({"name": name, "class_name": cn, "changes": changes})
        else:
            missing_from_engine.append({"name": name, "class_name": cn})

    # Check engine nodes not in catalogue
    for cn, enode in sorted(engine_by_class.items()):
        if cn not in cat_by_class:
            display = CLASS_NAME_TO_DISPLAY.get(cn)
            missing_from_catalogue.append({
                "class_name": cn,
                "display_name": display or enode.get("name", ""),
                "inputs": len(enode.get("inputs", [])),
                "outputs": len(enode.get("outputs", [])),
            })

    return {
        "mode": "engine",
        "catalogue_total": len(METASOUND_NODES),
        "engine_total": len(unique_engine),
        "matched": len(matched),
        "pin_mismatches": len(pin_mismatches),
        "missing_from_engine": len(missing_from_engine),
        "missing_from_catalogue": len(missing_from_catalogue),
        "matched_list": matched,
        "pin_mismatch_details": pin_mismatches,
        "missing_from_engine_list": missing_from_engine,
        "missing_from_catalogue_list": missing_from_catalogue,
    }


# ---------------------------------------------------------------------------
# Blueprint cross-reference
# ---------------------------------------------------------------------------

def cross_ref_blueprints(engine_json_path: str | None = None) -> dict:
    """Compare Blueprint engine exports against catalogue.

    Cross-reference key: (class_name, function_name).
    """
    from ue_audio_mcp.knowledge.blueprint_scraped import load_scraped_nodes

    cat_nodes = load_scraped_nodes()

    # Build catalogue index: (class_name, func_name) -> entry
    cat_by_key: dict[str, dict] = {}
    for name, node in cat_nodes.items():
        cls = node.get("target", "")
        key = "{}.{}".format(cls, name)
        cat_by_key[key] = {"name": name, "class_name": cls, **node}

    # Load engine data if available
    engine_funcs: list[dict] = []
    if engine_json_path and os.path.isfile(engine_json_path):
        with open(engine_json_path, encoding="utf-8") as f:
            data = json.load(f)
        engine_funcs = data.get("functions", [])

    if not engine_funcs:
        return {
            "mode": "offline",
            "catalogue_total": len(cat_nodes),
            "functions": len(cat_nodes),
            "classes": len(set(n.get("target", "") for n in cat_nodes.values())),
        }

    # Deduplicate engine funcs
    seen: set[str] = set()
    unique_funcs: list[dict] = []
    for func in engine_funcs:
        key = "{}.{}".format(func.get("class_name", ""), func.get("name", ""))
        if key not in seen:
            seen.add(key)
            unique_funcs.append(func)

    engine_by_key: dict[str, dict] = {}
    for func in unique_funcs:
        key = "{}.{}".format(func.get("class_name", ""), func.get("name", ""))
        engine_by_key[key] = func

    # Cross-reference
    matched = []
    param_mismatches = []
    missing_from_engine = []
    missing_from_catalogue = []

    for key, cat_entry in sorted(cat_by_key.items()):
        if key in engine_by_key:
            matched.append({"key": key, "name": cat_entry["name"], "class_name": cat_entry["class_name"]})

            # Compare params
            efunc = engine_by_key[key]
            cat_params = {p["name"]: p.get("type", "") for p in cat_entry.get("inputs", [])}
            eng_params = {p["name"]: p.get("type", "")
                          for p in efunc.get("params", [])
                          if p.get("direction", "in") == "in"}

            changes = []
            for pn in sorted(set(eng_params) - set(cat_params)):
                changes.append("+param: {} ({})".format(pn, eng_params[pn]))
            for pn in sorted(set(cat_params) - set(eng_params)):
                changes.append("-param: {} ({})".format(pn, cat_params[pn]))

            if changes:
                param_mismatches.append({"key": key, "changes": changes})
        else:
            missing_from_engine.append({"key": key, "name": cat_entry["name"]})

    # Engine funcs not in catalogue (only audio-relevant)
    for key, efunc in sorted(engine_by_key.items()):
        if key not in cat_by_key:
            missing_from_catalogue.append({
                "key": key,
                "name": efunc.get("name", ""),
                "class_name": efunc.get("class_name", ""),
                "params": len(efunc.get("params", [])),
            })

    return {
        "mode": "engine",
        "catalogue_total": len(cat_nodes),
        "engine_total": len(unique_funcs),
        "matched": len(matched),
        "param_mismatches": len(param_mismatches),
        "missing_from_engine": len(missing_from_engine),
        "missing_from_catalogue": len(missing_from_catalogue),
        "matched_list": matched,
        "param_mismatch_details": param_mismatches,
        "missing_from_engine_list": missing_from_engine,
        "missing_from_catalogue_list": missing_from_catalogue,
    }


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _print_report(title: str, report: dict) -> None:
    print("\n" + "=" * 60)
    print("  " + title)
    print("=" * 60)

    if report.get("mode") == "offline":
        print("Mode: OFFLINE (no engine exports found)")
        for k, v in report.items():
            if k != "mode":
                print("  {}: {}".format(k, v))
        return

    print("Catalogue:              {} entries".format(report.get("catalogue_total", 0)))
    print("Engine:                 {} entries".format(report.get("engine_total", 0)))
    print("Matched:                {}".format(report.get("matched", 0)))

    mismatch_key = "pin_mismatches" if "pin_mismatches" in report else "param_mismatches"
    print("With mismatches:        {}".format(report.get(mismatch_key, 0)))
    print("Missing from engine:    {}".format(report.get("missing_from_engine", 0)))
    print("Missing from catalogue: {}".format(report.get("missing_from_catalogue", 0)))

    # Details
    mismatch_details = report.get("pin_mismatch_details") or report.get("param_mismatch_details") or []
    if mismatch_details:
        print("\n--- Mismatches ---")
        for m in mismatch_details[:20]:
            label = m.get("name") or m.get("key", "?")
            print("  {}:".format(label))
            for c in m.get("changes", []):
                print("    {}".format(c))
        if len(mismatch_details) > 20:
            print("  ... and {} more".format(len(mismatch_details) - 20))

    missing_cat = report.get("missing_from_catalogue_list", [])
    if missing_cat:
        print("\n--- Missing from catalogue (in engine only) ---")
        for m in missing_cat[:30]:
            cn = m.get("class_name", "")
            name = m.get("display_name") or m.get("name", "")
            print("  {}: {}".format(cn, name))
        if len(missing_cat) > 30:
            print("  ... and {} more".format(len(missing_cat) - 30))

    missing_eng = report.get("missing_from_engine_list", [])
    if missing_eng:
        print("\n--- Missing from engine (catalogue only) ---")
        for m in missing_eng[:30]:
            name = m.get("name") or m.get("key", "")
            reason = m.get("reason", "")
            suffix = " ({})".format(reason) if reason else ""
            print("  {}{}".format(name, suffix))
        if len(missing_eng) > 30:
            print("  ... and {} more".format(len(missing_eng) - 30))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-reference engine exports against curated catalogues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--metasounds", action="store_true", help="MetaSounds only")
    group.add_argument("--blueprints", action="store_true", help="Blueprints only")
    group.add_argument("--all", action="store_true", help="Both (default)")
    parser.add_argument("--from-json", metavar="DIR", default="",
                        help="Directory with engine export JSON files")
    args = parser.parse_args()

    # Default to --all when no flag specified
    if not args.metasounds and not args.blueprints:
        args.all = True
    do_ms = args.metasounds or args.all
    do_bp = args.blueprints or args.all

    json_dir = args.from_json or os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "exports")

    if do_ms:
        ms_json = os.path.join(json_dir, "all_metasound_nodes.json")
        report = cross_ref_metasounds(ms_json if os.path.isfile(ms_json) else None)
        _print_report("MetaSounds Cross-Reference", report)

    if do_bp:
        # Try audio-only first, then all
        bp_json = os.path.join(json_dir, "blueprint_functions_audio.json")
        if not os.path.isfile(bp_json):
            bp_json = os.path.join(json_dir, "blueprint_functions_all.json")
        report = cross_ref_blueprints(bp_json if os.path.isfile(bp_json) else None)
        _print_report("Blueprint Cross-Reference", report)


if __name__ == "__main__":
    main()
