#!/usr/bin/env python3
"""Sync Blueprint function catalogue from a running UE5 engine.

Connects to the UE5 AudioMCP plugin via TCP and fetches all registered
BlueprintCallable UFunctions with their parameter signatures.

Usage:
    python scripts/sync_bp_from_engine.py
    python scripts/sync_bp_from_engine.py --save-json
    python scripts/sync_bp_from_engine.py --audio-only --save-json --update-db
    python scripts/sync_bp_from_engine.py --diff-only
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import struct
import sys
import time

# Ensure package is importable when running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

# ---------------------------------------------------------------------------
# TCP helpers (same protocol as sync_nodes_from_engine.py)
# ---------------------------------------------------------------------------

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9877
TIMEOUT = 120.0  # BP enumeration can be slow with large projects
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
# Diff logic
# ---------------------------------------------------------------------------

def _build_diff(engine_funcs: list[dict], existing: dict[str, dict]) -> dict:
    """Compare engine functions against current scraped DB entries."""
    from ue_audio_mcp.tools.bp_builder import _engine_func_to_bp_scraped

    new_funcs = []
    updated_funcs = []
    pin_changes = []

    for func in engine_funcs:
        bp_entry = _engine_func_to_bp_scraped(func)
        if bp_entry is None:
            continue

        name = bp_entry["name"]
        if name not in existing:
            new_funcs.append({
                "name": name,
                "class": bp_entry.get("target", ""),
                "category": bp_entry.get("category", ""),
                "inputs": len(bp_entry.get("inputs", [])),
                "outputs": len(bp_entry.get("outputs", [])),
            })
        else:
            old = existing[name]
            old_inputs = {p["name"]: p.get("type", "") for p in old.get("inputs", [])}
            new_inputs = {p["name"]: p.get("type", "") for p in bp_entry.get("inputs", [])}
            old_outputs = {p["name"]: p.get("type", "") for p in old.get("outputs", [])}
            new_outputs = {p["name"]: p.get("type", "") for p in bp_entry.get("outputs", [])}

            changes = []
            for pn in sorted(set(new_inputs) - set(old_inputs)):
                changes.append("+input: {} ({})".format(pn, new_inputs[pn]))
            for pn in sorted(set(old_inputs) - set(new_inputs)):
                changes.append("-input: {} ({})".format(pn, old_inputs[pn]))
            for pn in sorted(set(old_inputs) & set(new_inputs)):
                if old_inputs[pn] != new_inputs[pn]:
                    changes.append("~input: {} {} -> {}".format(pn, old_inputs[pn], new_inputs[pn]))
            for pn in sorted(set(new_outputs) - set(old_outputs)):
                changes.append("+output: {} ({})".format(pn, new_outputs[pn]))
            for pn in sorted(set(old_outputs) - set(new_outputs)):
                changes.append("-output: {} ({})".format(pn, old_outputs[pn]))
            for pn in sorted(set(old_outputs) & set(new_outputs)):
                if old_outputs[pn] != new_outputs[pn]:
                    changes.append("~output: {} {} -> {}".format(pn, old_outputs[pn], new_outputs[pn]))

            if changes:
                updated_funcs.append(name)
                pin_changes.append({"function": name, "changes": changes})

    return {
        "new_funcs": new_funcs,
        "updated_funcs": updated_funcs,
        "pin_changes": pin_changes,
        "new_count": len(new_funcs),
        "updated_count": len(updated_funcs),
        "total_pin_changes": sum(len(pc["changes"]) for pc in pin_changes),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Sync Blueprint functions from UE5 engine")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Plugin host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Plugin port")
    parser.add_argument("--filter", default="", help="Substring filter for function/class names")
    parser.add_argument("--class-filter", default="", help="Exact class name filter")
    parser.add_argument("--audio-only", action="store_true",
                        help="Only fetch audio-relevant functions")
    parser.add_argument("--limit", type=int, default=10000, help="Max functions to fetch")
    parser.add_argument("--save-json", action="store_true",
                        help="Save raw JSON to exports/all_blueprint_functions.json")
    parser.add_argument("--diff-only", action="store_true",
                        help="Only show diff against current DB, don't update")
    parser.add_argument("--update-db", action="store_true",
                        help="Update SQLite knowledge DB")
    args = parser.parse_args()

    # Connect
    sys.stdout.write("Connecting to UE5 plugin at {}:{}...\n".format(args.host, args.port))
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((args.host, args.port))
    except (OSError, ConnectionError) as e:
        sys.stderr.write("ERROR: Cannot connect: {}\n".format(e))
        sys.exit(1)

    # Ping
    ping = send_command(sock, {"action": "ping"})
    sys.stdout.write("Connected: {} {} ({})\n".format(
        ping.get("engine", "?"), ping.get("version", "?"), ping.get("project", "?")))

    # Fetch functions
    sys.stdout.write("Fetching blueprint functions (limit={}, audio_only={}, filter='{}', class='{}')...\n".format(
        args.limit, args.audio_only, args.filter, args.class_filter))
    t0 = time.time()
    result = send_command(sock, {
        "action": "list_blueprint_functions",
        "include_pins": True,
        "audio_only": args.audio_only,
        "filter": args.filter,
        "class_filter": args.class_filter,
        "limit": args.limit,
    })
    elapsed = time.time() - t0

    sock.close()

    if result.get("status") != "ok":
        sys.stderr.write("ERROR: {}\n".format(result.get("message", "Unknown error")))
        sys.exit(1)

    engine_funcs = result.get("functions", [])
    total = result.get("total", len(engine_funcs))
    shown = result.get("shown", len(engine_funcs))
    sys.stdout.write("Received {} functions ({} total matched) in {:.1f}s\n".format(shown, total, elapsed))

    # Class summary
    classes: dict[str, int] = {}
    for func in engine_funcs:
        cls = func.get("class_name", "Unknown")
        classes[cls] = classes.get(cls, 0) + 1
    sys.stdout.write("From {} classes\n".format(len(classes)))

    # Save raw JSON
    if args.save_json:
        export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
        os.makedirs(export_dir, exist_ok=True)
        export_path = os.path.join(export_dir, "all_blueprint_functions.json")
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump({"total": total, "shown": shown, "functions": engine_funcs}, f, indent=2)
        sys.stdout.write("Saved raw JSON to {}\n".format(export_path))

    # Diff against current DB
    try:
        from ue_audio_mcp.knowledge.db import KnowledgeDB
        db = KnowledgeDB()
        existing_rows = db.query_blueprint_scraped()
        existing = {row["name"]: row for row in existing_rows}
        # Deserialize JSON string fields
        for row in existing.values():
            if isinstance(row.get("inputs"), str):
                row["inputs"] = json.loads(row["inputs"])
            if isinstance(row.get("outputs"), str):
                row["outputs"] = json.loads(row["outputs"])
        db_available = True
    except Exception as e:
        sys.stderr.write("WARNING: Could not load existing DB: {}\n".format(e))
        existing = {}
        db_available = False

    diff = _build_diff(engine_funcs, existing)

    sys.stdout.write("\n--- Diff Report ---\n")
    sys.stdout.write("Current DB:        {} functions\n".format(len(existing)))
    sys.stdout.write("Engine registry:   {} functions\n".format(len(engine_funcs)))
    sys.stdout.write("New functions:     {}\n".format(diff["new_count"]))
    sys.stdout.write("Updated functions: {}\n".format(diff["updated_count"]))
    sys.stdout.write("Pin changes:       {}\n".format(diff["total_pin_changes"]))

    if diff["new_funcs"]:
        sys.stdout.write("\nNew functions:\n")
        for nf in diff["new_funcs"][:50]:
            sys.stdout.write("  + {}.{} [{}] ({} in, {} out)\n".format(
                nf["class"], nf["name"], nf["category"],
                nf["inputs"], nf["outputs"]))
        if len(diff["new_funcs"]) > 50:
            sys.stdout.write("  ... and {} more\n".format(len(diff["new_funcs"]) - 50))

    if diff["pin_changes"]:
        sys.stdout.write("\nPin changes:\n")
        for pc in diff["pin_changes"][:30]:
            sys.stdout.write("  {}:\n".format(pc["function"]))
            for change in pc["changes"]:
                sys.stdout.write("    {}\n".format(change))
        if len(diff["pin_changes"]) > 30:
            sys.stdout.write("  ... and {} more functions with changes\n".format(
                len(diff["pin_changes"]) - 30))

    if args.diff_only:
        sys.stdout.write("\n(diff-only mode, no updates applied)\n")
        return

    # Update DB (reuse existing db instance)
    if args.update_db and db_available:
        try:
            from ue_audio_mcp.tools.bp_builder import _engine_func_to_bp_scraped
            converted = []
            for func in engine_funcs:
                bp_entry = _engine_func_to_bp_scraped(func)
                if bp_entry:
                    converted.append(bp_entry)
            db.insert_blueprint_scraped_batch(converted)
            sys.stdout.write("\nSQLite DB updated: {} functions upserted\n".format(len(converted)))
        except Exception as e:
            sys.stderr.write("WARNING: DB update failed: {}\n".format(e))
    elif args.update_db and not db_available:
        sys.stderr.write("\nWARNING: Cannot update DB -- database not available\n")


if __name__ == "__main__":
    main()
