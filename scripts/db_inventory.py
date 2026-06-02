#!/usr/bin/env python3
"""Report knowledge DB, source catalogue, and engine export counts.

This avoids mixing seeded catalogue rows, runtime audit history, and live
engine export snapshots into one ambiguous "knowledge entries" number.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from ue_audio_mcp.knowledge.db import DEFAULT_DB_PATH, KnowledgeDB  # noqa: E402


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _source_counts() -> dict[str, int]:
    from ue_audio_mcp.knowledge.blueprint_audio import BLUEPRINT_AUDIO_FUNCTIONS
    from ue_audio_mcp.knowledge.blueprint_scraped import load_scraped_nodes
    from ue_audio_mcp.knowledge.metasound_nodes import (
        CLASS_NAME_TO_DISPLAY,
        METASOUND_NODES,
    )
    from ue_audio_mcp.knowledge.waapi_functions import WAAPI_FUNCTIONS

    return {
        "metasound_nodes_py": len(METASOUND_NODES),
        "metasound_class_mappings": len(CLASS_NAME_TO_DISPLAY),
        "waapi_functions_py": len(WAAPI_FUNCTIONS),
        "blueprint_audio_py": len(BLUEPRINT_AUDIO_FUNCTIONS),
        "blueprint_scraped_loader": len(load_scraped_nodes()),
    }


def _catalogue_json_counts() -> dict[str, int]:
    ms = _load_json(ROOT / "src/ue_audio_mcp/knowledge/metasound_catalogue.json")
    bp = _load_json(ROOT / "src/ue_audio_mcp/knowledge/blueprint_audio_catalogue.json")
    return {
        "metasound_catalogue_json": len(ms.get("nodes", [])),
        "blueprint_catalogue_json": len(bp.get("functions", [])),
        "blueprint_catalogue_events": len(bp.get("events", [])),
        "blueprint_catalogue_allowlist": len(bp.get("allowlist", [])),
    }


def _engine_export_counts() -> dict[str, int]:
    ms = _load_json(ROOT / "exports/all_metasound_nodes.json")
    bp_audio = _load_json(ROOT / "exports/blueprint_functions_audio.json")
    bp_all = _load_json(ROOT / "exports/blueprint_functions_all.json")
    return {
        "metasound_export_total": int(ms.get("total", 0) or 0),
        "metasound_export_shown": len(ms.get("nodes", [])),
        "blueprint_audio_export_total": int(bp_audio.get("total", 0) or 0),
        "blueprint_audio_export_shown": len(bp_audio.get("functions", [])),
        "blueprint_all_export_total": int(bp_all.get("total", 0) or 0),
        "blueprint_all_export_shown": len(bp_all.get("functions", [])),
    }


def build_report(db_path: str, ensure_seeded: bool = True) -> dict[str, Any]:
    db = KnowledgeDB(db_path)
    try:
        seed_counts = db.ensure_seeded() if ensure_seeded else {}
        catalogue_counts = db.catalogue_counts()
        runtime_counts = db.runtime_counts()
        table_counts = db.table_counts()
        return {
            "db_path": db_path,
            "seed_ran": bool(seed_counts),
            "seed_counts": seed_counts,
            "seed_status": db.seed_status(),
            "catalogue_total": sum(catalogue_counts.values()),
            "catalogue_counts": catalogue_counts,
            "runtime_total": sum(runtime_counts.values()),
            "runtime_counts": runtime_counts,
            "table_counts": table_counts,
            "source_counts": _source_counts(),
            "catalogue_json_counts": _catalogue_json_counts(),
            "engine_export_counts": _engine_export_counts(),
        }
    finally:
        db.close()


def _print_group(title: str, data: dict[str, Any]) -> None:
    print(title)
    for key, value in data.items():
        print("  {}: {}".format(key, value))


def print_text(report: dict[str, Any]) -> None:
    print("Knowledge DB Inventory")
    print("DB path: {}".format(report["db_path"]))
    print("Seeded: {}".format("yes" if report["seed_status"]["seeded"] else "no"))
    if report["seed_status"]["missing"]:
        print("Missing seed data: {}".format(", ".join(report["seed_status"]["missing"])))
    if report["seed_ran"]:
        _print_group("Seed counts", report["seed_counts"])
    print("Catalogue total: {}".format(report["catalogue_total"]))
    _print_group("Catalogue DB counts", report["catalogue_counts"])
    print("Runtime total: {}".format(report["runtime_total"]))
    _print_group("Runtime DB counts", report["runtime_counts"])
    _print_group("Source Python counts", report["source_counts"])
    _print_group("Catalogue JSON counts", report["catalogue_json_counts"])
    _print_group("Engine export counts", report["engine_export_counts"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Report UE Audio MCP DB inventory")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite DB path")
    parser.add_argument("--no-seed", action="store_true", help="Do not seed missing data")
    parser.add_argument("--json", action="store_true", help="Print JSON")
    args = parser.parse_args()

    report = build_report(args.db, ensure_seeded=not args.no_seed)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text(report)


if __name__ == "__main__":
    main()
