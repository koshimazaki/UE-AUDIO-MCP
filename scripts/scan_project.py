#!/usr/bin/env python3
"""Batch scan all Blueprints in a UE5 project for audio-relevant nodes.

Connects to the UE5 AudioMCP plugin via TCP, lists all Blueprint assets,
deep-scans each one, and saves aggregated results. Optionally imports
findings into the knowledge DB with TF-IDF embeddings.

Usage:
    python scripts/scan_project.py
    python scripts/scan_project.py --path /Game/Blueprints
    python scripts/scan_project.py --audio-only --import-db
    python scripts/scan_project.py --scan-audio-assets
    python scripts/scan_project.py --project MyGame --import-db --rebuild-embeddings
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import struct
import sys
import time

# ---------------------------------------------------------------------------
# TCP helpers (same protocol as test_plugin_live.py)
# ---------------------------------------------------------------------------

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9877
TIMEOUT = 30.0
HEADER_SIZE = 4


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Connection closed")
        data.extend(chunk)
    return bytes(data)


def send_command(sock: socket.socket, command: dict) -> dict:
    payload = json.dumps(command).encode("utf-8")
    header = struct.pack(">I", len(payload))
    sock.sendall(header + payload)
    raw_header = _recv_exact(sock, HEADER_SIZE)
    (length,) = struct.unpack(">I", raw_header)
    raw_body = _recv_exact(sock, length)
    return json.loads(raw_body.decode("utf-8"))


# ---------------------------------------------------------------------------
# Scan operations
# ---------------------------------------------------------------------------

def list_assets(
    sock: socket.socket,
    class_filter: str = "Blueprint",
    path: str = "/Game/",
    limit: int = 5000,
) -> list[dict]:
    """List all assets of a given class under a path."""
    resp = send_command(sock, {
        "action": "list_assets",
        "class_filter": class_filter,
        "path": path,
        "recursive_classes": True,
        "limit": limit,
    })
    if resp.get("status") != "ok":
        raise RuntimeError(f"list_assets failed: {resp.get('message')}")
    return resp.get("assets", [])


def scan_blueprint(
    sock: socket.socket,
    asset_path: str,
    audio_only: bool = False,
    include_pins: bool = False,
) -> dict:
    """Deep-scan a single Blueprint."""
    return send_command(sock, {
        "action": "scan_blueprint",
        "asset_path": asset_path,
        "audio_only": audio_only,
        "include_pins": include_pins,
    })


# ---------------------------------------------------------------------------
# Knowledge DB import
# ---------------------------------------------------------------------------

def import_to_db(
    scan_results: list[dict],
    project_name: str,
    rebuild_embeddings: bool = False,
) -> dict:
    """Import scan results into the knowledge DB.

    Populates project_blueprints table with graph node data extracted
    from scan results. Optionally rebuilds TF-IDF embeddings.

    Returns summary dict with counts.
    """
    # Import here so the script works standalone without the package
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from ue_audio_mcp.knowledge.db import get_knowledge_db

    db = get_knowledge_db()
    imported = 0
    audio_bps = 0

    for result in scan_results:
        if result.get("status") != "ok":
            continue

        bp_name = result.get("blueprint_name", "")
        if not bp_name:
            continue

        # Extract structured data for the DB
        audio_summary = result.get("audio_summary", {})
        graphs = result.get("graphs", [])

        # Collect all function names, events, variables from all graphs
        functions = []
        events = []
        variables = []
        components = []  # Not available from graph scan, but keep schema compat

        for graph in graphs:
            for node in graph.get("nodes", []):
                node_type = node.get("type", "")
                if node_type == "CallFunction":
                    fn = node.get("function_name", "")
                    fc = node.get("function_class", "")
                    if fn:
                        entry = {"name": fn, "class": fc, "audio": node.get("audio_relevant", False)}
                        if entry not in functions:
                            functions.append(entry)
                elif node_type in ("Event", "CustomEvent"):
                    ev = node.get("event_name", node.get("title", ""))
                    if ev and ev not in events:
                        events.append(ev)
                elif node_type in ("VariableGet", "VariableSet"):
                    vn = node.get("variable_name", "")
                    if vn and vn not in variables:
                        variables.append(vn)

        bp_entry = {
            "name": bp_name,
            "description": (
                f"{result.get('parent_class', '')} blueprint, "
                f"{result.get('total_nodes', 0)} nodes, "
                f"{audio_summary.get('audio_node_count', 0)} audio-relevant. "
                f"Audio functions: {', '.join(audio_summary.get('audio_functions', []))}"
            ),
            "functions": functions,
            "variables": variables,
            "components": components,
            "events": events,
            "references": [result.get("asset_path", "")],
        }

        db.insert_project_blueprint(bp_entry, project_name)
        imported += 1
        if audio_summary.get("has_audio"):
            audio_bps += 1

    db._conn.commit()

    summary = {
        "imported": imported,
        "audio_relevant": audio_bps,
        "project": project_name,
    }

    # Rebuild embeddings if requested
    if rebuild_embeddings and imported > 0:
        summary["embeddings"] = _rebuild_embeddings(db, project_name)

    return summary


def _rebuild_embeddings(db, project_name: str) -> dict:
    """Rebuild TF-IDF embeddings including project Blueprint data."""
    from ue_audio_mcp.knowledge.embeddings import EmbeddingIndex

    # Gather all searchable entries: existing nodes + project BPs
    entries = []

    # MetaSounds nodes
    for node in db._fetch("SELECT name, category, description FROM metasound_nodes"):
        entries.append({
            "name": f"ms:{node['name']}",
            "text": f"{node['name']} {node.get('category', '')} {node.get('description', '')}",
        })

    # WAAPI functions
    for fn in db._fetch("SELECT name, namespace, description FROM waapi_functions"):
        entries.append({
            "name": f"waapi:{fn['name']}",
            "text": f"{fn['name']} {fn.get('namespace', '')} {fn.get('description', '')}",
        })

    # Project Blueprints
    bps = db.query_project_blueprints(project=project_name)
    for bp in bps:
        funcs_raw = bp.get("functions", "[]")
        funcs = json.loads(funcs_raw) if isinstance(funcs_raw, str) else funcs_raw
        events_raw = bp.get("events", "[]")
        events = json.loads(events_raw) if isinstance(events_raw, str) else events_raw

        func_names = [f["name"] if isinstance(f, dict) else f for f in funcs]
        text_parts = [
            bp["name"],
            bp.get("description", ""),
            " ".join(func_names),
            " ".join(events if isinstance(events, list) else []),
        ]
        entries.append({
            "name": f"bp:{bp['name']}",
            "text": " ".join(text_parts),
        })

    if not entries:
        return {"status": "skip", "reason": "no entries"}

    index = EmbeddingIndex(entries)
    save_path = os.path.join(
        os.path.dirname(__file__), "..", "src", "ue_audio_mcp", "knowledge",
        "project_embeddings.npz",
    )
    index.save(save_path)
    return {"status": "ok", "entries": len(entries), "path": save_path}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Batch scan UE5 project Blueprints for audio-relevant nodes"
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--path", default="/Game/",
                        help="Asset path prefix to scan (default: /Game/)")
    parser.add_argument("--audio-only", action="store_true",
                        help="Only include audio-relevant nodes in scan results")
    parser.add_argument("--include-pins", action="store_true",
                        help="Include full pin details per node")
    parser.add_argument("--scan-audio-assets", action="store_true",
                        help="Also scan MetaSounds, SoundWaves, SoundCues")
    parser.add_argument("--output", "-o", default=None,
                        help="Output JSON file (default: project_scan.json)")
    parser.add_argument("--project", "-p", default=None,
                        help="Project name for DB import (auto-detected from ping)")
    parser.add_argument("--import-db", action="store_true",
                        help="Import results into knowledge DB")
    parser.add_argument("--rebuild-embeddings", action="store_true",
                        help="Rebuild TF-IDF embeddings after import")
    args = parser.parse_args()

    # --- Connect ---
    print("=" * 60)
    print("AudioMCP Project Scanner")
    print(f"Connecting to {args.host}:{args.port}...")
    print("=" * 60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((args.host, args.port))
    except (OSError, ConnectionError) as e:
        print(f"\nFAILED to connect: {e}")
        print("Make sure UE5 Editor is running with UEAudioMCP plugin enabled.")
        sys.exit(1)

    try:
        # --- Ping to get project info ---
        ping = send_command(sock, {"action": "ping"})
        project_name = args.project or ping.get("project", "UnknownProject")
        print(f"Connected to: {ping.get('engine', '?')} {ping.get('version', '?')}")
        print(f"Project: {project_name}")
        print()

        results = {"project": project_name, "scan_time": time.strftime("%Y-%m-%d %H:%M:%S")}

        # --- Phase 1: List Blueprints ---
        print("[1/3] Listing Blueprint assets...")
        bp_assets = list_assets(sock, "Blueprint", args.path)
        print(f"  Found {len(bp_assets)} Blueprint assets under {args.path}")
        results["blueprint_count"] = len(bp_assets)

        # --- Phase 2: Scan each Blueprint ---
        print(f"\n[2/3] Scanning {len(bp_assets)} Blueprints...")
        scan_results = []
        audio_count = 0
        errors = 0
        t0 = time.time()

        for i, asset in enumerate(bp_assets):
            path = asset["path"]
            name = asset["name"]
            pct = (i + 1) / len(bp_assets) * 100 if bp_assets else 100
            bar_done = int(pct / 4)
            bar = "\u2588" * bar_done + "\u2591" * (25 - bar_done)
            print(f"\r  {bar} {pct:5.1f}% ({i+1}/{len(bp_assets)}) {name:<40s}", end="", flush=True)

            result = scan_blueprint(sock, path, args.audio_only, args.include_pins)
            if result.get("status") == "ok":
                scan_results.append(result)
                if result.get("audio_summary", {}).get("has_audio"):
                    audio_count += 1
            else:
                errors += 1
                scan_results.append({"status": "error", "path": path, "message": result.get("message", "")})

        elapsed = time.time() - t0
        print(f"\r  {'':80s}")  # Clear progress line
        print(f"  Scanned {len(bp_assets)} BPs in {elapsed:.1f}s "
              f"({audio_count} audio-relevant, {errors} errors)")

        results["blueprints"] = scan_results
        results["audio_relevant_count"] = audio_count
        results["error_count"] = errors

        # --- Phase 2b: Audio assets (optional) ---
        if args.scan_audio_assets:
            print("\n[2b] Scanning audio assets...")
            audio_assets = {}
            for cls in ["MetaSoundSource", "MetaSoundPatch", "SoundWave", "SoundCue"]:
                assets = list_assets(sock, cls, args.path)
                audio_assets[cls] = [a["path"] for a in assets]
                print(f"  {cls}: {len(assets)}")
            results["audio_assets"] = audio_assets

        # --- Phase 3: Save results ---
        output_file = args.output or "project_scan.json"
        print(f"\n[3/3] Saving results to {output_file}...")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        file_size = os.path.getsize(output_file)
        print(f"  Saved ({file_size / 1024:.1f} KB)")

        # --- Optional: Import to DB ---
        if args.import_db:
            print(f"\n[DB] Importing to knowledge DB (project={project_name})...")
            summary = import_to_db(
                scan_results,
                project_name,
                rebuild_embeddings=args.rebuild_embeddings,
            )
            print(f"  Imported {summary['imported']} BPs ({summary['audio_relevant']} audio-relevant)")
            if "embeddings" in summary:
                emb = summary["embeddings"]
                if emb.get("status") == "ok":
                    print(f"  Embeddings rebuilt: {emb['entries']} entries")
                else:
                    print(f"  Embeddings: {emb.get('reason', 'skipped')}")

        # --- Summary ---
        print("\n" + "=" * 60)
        print("SCAN SUMMARY")
        print("=" * 60)
        print(f"  Project:          {project_name}")
        print(f"  Blueprints:       {len(bp_assets)}")
        print(f"  Audio-relevant:   {audio_count}")
        total_nodes = sum(r.get("total_nodes", 0) for r in scan_results if r.get("status") == "ok")
        print(f"  Total nodes:      {total_nodes}")
        print(f"  Errors:           {errors}")
        print(f"  Scan time:        {elapsed:.1f}s")
        print(f"  Output:           {output_file}")

        # Print audio-relevant BPs
        if audio_count > 0:
            print(f"\n  Audio Blueprints:")
            for r in scan_results:
                if r.get("status") != "ok":
                    continue
                audio = r.get("audio_summary", {})
                if audio.get("has_audio"):
                    funcs = ", ".join(audio.get("audio_functions", [])[:5])
                    print(f"    {r['blueprint_name']:<35s} [{audio['audio_node_count']} nodes] {funcs}")

    finally:
        sock.close()


if __name__ == "__main__":
    main()
