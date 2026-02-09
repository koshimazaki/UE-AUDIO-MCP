#!/usr/bin/env python3
"""Comprehensive UE5 project audio scanner.

Connects to the UE5 AudioMCP plugin via TCP and exports:
- All Blueprint nodes (with audio-relevant ones highlighted)
- All MetaSounds patches/sources with full graph data (nodes + connections)
- All audio assets (SoundWave, SoundCue, etc.)
- Cross-references: which Blueprints trigger/link to which MetaSounds

Usage:
    python scripts/scan_project.py --full-export
    python scripts/scan_project.py --full-export --import-db --rebuild-embeddings
    python scripts/scan_project.py --audio-only --include-pins
    python scripts/scan_project.py --path /Game/Blueprints
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


class TCPConnection:
    """Auto-reconnecting TCP connection to the UE5 plugin."""

    def __init__(self, host: str, port: int, timeout: float = TIMEOUT):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: socket.socket | None = None

    def _connect(self):
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(self.timeout)
        self._sock.connect((self.host, self.port))

    def send(self, command: dict, retries: int = 3) -> dict:
        """Send command with auto-reconnect on connection errors."""
        for attempt in range(retries + 1):
            if self._sock is None:
                try:
                    self._connect()
                except (OSError, ConnectionError):
                    if attempt < retries:
                        time.sleep(1.0 + attempt)
                        continue
                    raise
            try:
                return send_command(self._sock, command)
            except (ConnectionError, OSError, BrokenPipeError):
                self._sock = None
                if attempt < retries:
                    time.sleep(1.0 + attempt)
                else:
                    raise

    def close(self):
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None


# ---------------------------------------------------------------------------
# Scan operations
# ---------------------------------------------------------------------------

def list_assets(
    conn: "TCPConnection",
    class_filter: str = "Blueprint",
    path: str = "/Game/",
    limit: int = 5000,
) -> list[dict]:
    """List all assets of a given class under a path."""
    resp = conn.send({
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
    conn: "TCPConnection",
    asset_path: str,
    audio_only: bool = False,
    include_pins: bool = False,
) -> dict:
    """Deep-scan a single Blueprint."""
    return conn.send({
        "action": "scan_blueprint",
        "asset_path": asset_path,
        "audio_only": audio_only,
        "include_pins": include_pins,
    })


def get_node_locations(conn: "TCPConnection", asset_path: str) -> dict:
    """Read MetaSounds graph structure (nodes + connections) from a saved asset."""
    return conn.send({
        "action": "get_node_locations",
        "asset_path": asset_path,
    })


def extract_cross_references(
    bp_scan_results: list[dict],
    ms_paths: list[str],
) -> dict:
    """Extract cross-references between Blueprints and MetaSounds/audio assets.

    Scans BP node data for references to MetaSounds assets, Sound assets,
    and audio-related function calls that trigger playback.
    """
    AUDIO_PLAY_FUNCTIONS = {
        "PlaySound2D", "PlaySoundAtLocation", "SpawnSoundAtLocation",
        "SpawnSound2D", "PlayDialogue2D", "PlayDialogueAtLocation",
        "SpawnDialogue2D", "SpawnDialogueAtLocation",
    }
    AUDIO_KEYWORDS = {"MetaSound", "Sound", "Audio", "Ak", "Wwise", "PostEvent"}

    bp_to_metasound = []
    bp_to_sound = []
    audio_triggers = []

    # Build a set of MS asset names for matching
    ms_names = set()
    for p in ms_paths:
        # "/Game/Audio/MySynth.MySynth" → "MySynth"
        name = p.rsplit(".", 1)[-1] if "." in p else p.rsplit("/", 1)[-1]
        ms_names.add(name.lower())

    for bp in bp_scan_results:
        if bp.get("status") != "ok":
            continue
        bp_path = bp.get("asset_path", "")
        bp_name = bp.get("blueprint_name", "")

        for graph in bp.get("graphs", []):
            for node in graph.get("nodes", []):
                node_type = node.get("type", "")
                fn_name = node.get("function_name", "")
                fn_class = node.get("function_class", "")
                title = node.get("title", "")

                # Detect playback triggers
                if fn_name in AUDIO_PLAY_FUNCTIONS:
                    audio_triggers.append({
                        "bp_path": bp_path,
                        "bp_name": bp_name,
                        "function": fn_name,
                        "class": fn_class,
                        "graph": graph.get("name", ""),
                    })

                # Detect MetaSounds references via function class or title
                text_to_check = f"{fn_name} {fn_class} {title}".lower()
                if "metasound" in text_to_check:
                    bp_to_metasound.append({
                        "bp_path": bp_path,
                        "bp_name": bp_name,
                        "reference": fn_name or title,
                        "class": fn_class,
                        "node_type": node_type,
                    })

                # Detect Sound asset references
                if any(kw.lower() in text_to_check for kw in AUDIO_KEYWORDS):
                    if node.get("audio_relevant"):
                        bp_to_sound.append({
                            "bp_path": bp_path,
                            "bp_name": bp_name,
                            "reference": fn_name or title,
                            "class": fn_class,
                            "node_type": node_type,
                            "audio_relevant": True,
                        })

    return {
        "bp_to_metasound": bp_to_metasound,
        "bp_to_sound": bp_to_sound,
        "audio_triggers": audio_triggers,
        "summary": {
            "bps_referencing_metasounds": len(set(r["bp_name"] for r in bp_to_metasound)),
            "bps_with_audio_playback": len(set(t["bp_name"] for t in audio_triggers)),
            "total_audio_references": len(bp_to_sound),
            "total_playback_triggers": len(audio_triggers),
        },
    }


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
    for fn in db._fetch("SELECT uri, namespace, description FROM waapi_functions"):
        entries.append({
            "name": f"waapi:{fn['uri']}",
            "text": f"{fn['uri']} {fn.get('namespace', '')} {fn.get('description', '')}",
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
        description="Comprehensive UE5 project audio scanner"
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--path", default="/Game/",
                        help="Asset path prefix to scan (default: /Game/)")
    parser.add_argument("--audio-only", action="store_true",
                        help="Only include audio-relevant nodes in BP scan results")
    parser.add_argument("--include-pins", action="store_true",
                        help="Include full pin details per node")
    parser.add_argument("--scan-audio-assets", action="store_true",
                        help="Also list MetaSounds, SoundWaves, SoundCues")
    parser.add_argument("--full-export", action="store_true",
                        help="Full export: all nodes, pins, audio assets, MS graphs, cross-refs")
    parser.add_argument("--output", "-o", default=None,
                        help="Output JSON file (default: project_scan.json)")
    parser.add_argument("--project", "-p", default=None,
                        help="Project name for DB import (auto-detected from ping)")
    parser.add_argument("--import-db", action="store_true",
                        help="Import results into knowledge DB")
    parser.add_argument("--rebuild-embeddings", action="store_true",
                        help="Rebuild TF-IDF embeddings after import")
    args = parser.parse_args()

    # --full-export enables everything
    if args.full_export:
        args.include_pins = True
        args.scan_audio_assets = True

    # --- Connect ---
    print("=" * 60)
    print("AudioMCP Project Scanner")
    print(f"Connecting to {args.host}:{args.port}...")
    if args.full_export:
        print("Mode: FULL EXPORT (all nodes + MS graphs + cross-refs)")
    print("=" * 60)

    conn = TCPConnection(args.host, args.port)
    try:
        conn._connect()
    except (OSError, ConnectionError) as e:
        print(f"\nFAILED to connect: {e}")
        print("Make sure UE5 Editor is running with UEAudioMCP plugin enabled.")
        sys.exit(1)

    try:
        # --- Ping to get project info ---
        ping = conn.send({"action": "ping"})
        project_name = args.project or ping.get("project", "UnknownProject")
        engine_ver = f"{ping.get('engine', '?')} {ping.get('version', '?')}"
        features = ping.get("features", [])
        print(f"Connected to: {engine_ver}")
        print(f"Project: {project_name}")
        print(f"Features: {', '.join(features)}")
        print()

        results = {
            "project": project_name,
            "engine": engine_ver,
            "features": features,
            "scan_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scan_mode": "full_export" if args.full_export else "standard",
        }

        # --- Phase 1: List Blueprints ---
        phase_total = 5 if args.full_export else 3
        print(f"[1/{phase_total}] Listing Blueprint assets...")
        bp_assets = list_assets(conn, "Blueprint", args.path)
        print(f"  Found {len(bp_assets)} Blueprint assets under {args.path}")
        results["blueprint_count"] = len(bp_assets)

        # --- Phase 2: Scan each Blueprint (ALL nodes, not audio-only for full export) ---
        print(f"\n[2/{phase_total}] Scanning {len(bp_assets)} Blueprints...")
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

            try:
                result = scan_blueprint(conn, path, args.audio_only, args.include_pins)
                if result.get("status") == "ok":
                    scan_results.append(result)
                    if result.get("audio_summary", {}).get("has_audio"):
                        audio_count += 1
                else:
                    errors += 1
                    scan_results.append({"status": "error", "path": path, "message": result.get("message", "")})
            except (ConnectionError, OSError) as e:
                errors += 1
                scan_results.append({"status": "error", "path": path, "message": str(e)})

        elapsed_bp = time.time() - t0
        print(f"\r  {'':80s}")  # Clear progress line
        print(f"  Scanned {len(bp_assets)} BPs in {elapsed_bp:.1f}s "
              f"({audio_count} audio-relevant, {errors} errors)")

        results["blueprints"] = scan_results
        results["audio_relevant_count"] = audio_count
        results["error_count"] = errors

        # --- Phase 3: Audio assets + MetaSounds graph reading ---
        all_ms_paths = []
        if args.scan_audio_assets:
            print(f"\n[3/{phase_total}] Listing & scanning audio assets...")
            audio_assets = {}
            for cls in ["MetaSoundSource", "MetaSoundPatch", "SoundWave", "SoundCue",
                         "SoundAttenuation", "SoundClass", "SoundMix", "ReverbEffect"]:
                assets = list_assets(conn, cls, args.path)
                audio_assets[cls] = [{"path": a["path"], "name": a["name"]} for a in assets]
                if assets:
                    print(f"  {cls}: {len(assets)}")
                if cls in ("MetaSoundSource", "MetaSoundPatch"):
                    all_ms_paths.extend(a["path"] for a in assets)
            results["audio_assets"] = audio_assets

            # Read MetaSounds graph structures
            if all_ms_paths:
                print(f"\n  Reading {len(all_ms_paths)} MetaSounds graph structures...")
                ms_graphs = []
                ms_errors = 0
                for i, ms_path in enumerate(all_ms_paths):
                    ms_name = ms_path.rsplit(".", 1)[-1] if "." in ms_path else ms_path.rsplit("/", 1)[-1]
                    pct = (i + 1) / len(all_ms_paths) * 100
                    bar_done = int(pct / 4)
                    bar = "\u2588" * bar_done + "\u2591" * (25 - bar_done)
                    print(f"\r  {bar} {pct:5.1f}% ({i+1}/{len(all_ms_paths)}) {ms_name:<40s}", end="", flush=True)

                    resp = get_node_locations(conn, ms_path)
                    if resp.get("status") == "ok":
                        ms_graphs.append({
                            "path": ms_path,
                            "name": ms_name,
                            "nodes": resp.get("nodes", []),
                            "edges": resp.get("edges", []),
                            "node_count": len(resp.get("nodes", [])),
                            "edge_count": len(resp.get("edges", [])),
                        })
                    else:
                        ms_errors += 1
                        ms_graphs.append({
                            "path": ms_path,
                            "name": ms_name,
                            "status": "error",
                            "message": resp.get("message", ""),
                        })

                print(f"\r  {'':80s}")
                ok_count = len(all_ms_paths) - ms_errors
                total_ms_nodes = sum(g.get("node_count", 0) for g in ms_graphs)
                total_ms_edges = sum(g.get("edge_count", 0) for g in ms_graphs)
                print(f"  Read {ok_count} MetaSounds graphs "
                      f"({total_ms_nodes} nodes, {total_ms_edges} edges, {ms_errors} errors)")
                results["metasounds_graphs"] = ms_graphs
        else:
            print(f"\n[3/{phase_total}] Skipping audio assets (use --scan-audio-assets or --full-export)")

        # --- Phase 4: Cross-references ---
        if args.full_export:
            print(f"\n[4/{phase_total}] Extracting cross-references...")
            xrefs = extract_cross_references(scan_results, all_ms_paths)
            results["cross_references"] = xrefs
            xsum = xrefs["summary"]
            print(f"  BPs referencing MetaSounds: {xsum['bps_referencing_metasounds']}")
            print(f"  BPs with audio playback:    {xsum['bps_with_audio_playback']}")
            print(f"  Total audio references:     {xsum['total_audio_references']}")
            print(f"  Total playback triggers:    {xsum['total_playback_triggers']}")

        # --- Phase 5: Save results ---
        output_file = args.output or "project_scan.json"
        print(f"\n[{phase_total}/{phase_total}] Saving results to {output_file}...")
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
        elapsed_total = time.time() - t0
        print("\n" + "=" * 60)
        print("SCAN SUMMARY")
        print("=" * 60)
        print(f"  Project:          {project_name}")
        print(f"  Engine:           {engine_ver}")
        print(f"  Blueprints:       {len(bp_assets)}")
        print(f"  Audio-relevant:   {audio_count}")
        total_nodes = sum(r.get("total_nodes", 0) for r in scan_results if r.get("status") == "ok")
        print(f"  Total BP nodes:   {total_nodes}")
        if "metasounds_graphs" in results:
            ms_count = len([g for g in results["metasounds_graphs"] if "nodes" in g])
            print(f"  MetaSounds:       {ms_count} graphs")
        if "audio_assets" in results:
            for cls, items in results["audio_assets"].items():
                if items:
                    print(f"  {cls + ':':20s}{len(items)}")
        print(f"  Errors:           {errors}")
        print(f"  Scan time:        {elapsed_total:.1f}s")
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

        # Print MetaSounds graphs
        if "metasounds_graphs" in results:
            graphs_ok = [g for g in results["metasounds_graphs"] if "nodes" in g]
            if graphs_ok:
                print(f"\n  MetaSounds Graphs:")
                for g in graphs_ok:
                    print(f"    {g['name']:<35s} [{g['node_count']} nodes, {g['edge_count']} edges]")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
