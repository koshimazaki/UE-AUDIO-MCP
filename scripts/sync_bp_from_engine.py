#!/usr/bin/env python3
"""Sync Blueprint function catalogue from a running UE5 engine.

Connects to the UE5 AudioMCP plugin via TCP and fetches all registered
BlueprintCallable UFunctions with their parameter signatures.

Usage:
    python scripts/sync_bp_from_engine.py                           # audio-only, quick
    python scripts/sync_bp_from_engine.py --all --save-json         # ALL ~26K functions, batch by class
    python scripts/sync_bp_from_engine.py --all --update-db         # full sync + write to DB
    python scripts/sync_bp_from_engine.py --audio-only --update-db  # audio subset
    python scripts/sync_bp_from_engine.py --diff-only               # compare without writing
    python scripts/sync_bp_from_engine.py --class-filter GameplayStatics --save-json
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
TIMEOUT = 120.0
HEADER_SIZE = 4
RECONNECT_DELAY = 0.5
MAX_RECONNECT_RETRIES = 3


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


def connect(host: str, port: int) -> socket.socket:
    """Create and return a connected TCP socket."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)
    sock.connect((host, port))
    return sock


def reconnect(host: str, port: int, retries: int = MAX_RECONNECT_RETRIES) -> socket.socket:
    """Reconnect with progressive delay. Raises on failure."""
    for attempt in range(retries):
        delay = RECONNECT_DELAY * (attempt + 1)
        sys.stderr.write("  Reconnecting (attempt {}/{}, {:.1f}s delay)...\n".format(
            attempt + 1, retries, delay))
        time.sleep(delay)
        try:
            return connect(host, port)
        except (OSError, ConnectionError):
            continue
    raise ConnectionError("Failed to reconnect after {} attempts".format(retries))


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
# Batch-by-class sync (for --all mode)
# ---------------------------------------------------------------------------

def _fetch_all_by_class(host: str, port: int, include_pins: bool = True) -> list[dict]:
    """Fetch ALL Blueprint functions by iterating per-class.

    Resilient to TCP drops: reconnects automatically between classes.
    Flow:
      1. list_blueprint_functions(list_classes_only=true) -> class names + counts
      2. For each class: list_blueprint_functions(class_filter=X, include_pins=True)
      3. Merge all results
    """
    # Step 1: Get class list (paginated — class list can be huge)
    PAGE_SIZE = 2000  # class entries are tiny (~50 bytes each)
    sock = connect(host, port)
    ping = send_command(sock, {"action": "ping"})
    sys.stdout.write("Connected: {} {} ({})\n".format(
        ping.get("engine", "?"), ping.get("version", "?"), ping.get("project", "?")))

    classes: list[dict] = []
    offset = 0
    while True:
        sys.stdout.write("\r  Fetching class list (offset={})...".format(offset))
        sys.stdout.flush()
        try:
            result = send_command(sock, {
                "action": "list_blueprint_functions",
                "list_classes_only": True,
                "limit": PAGE_SIZE,
                "offset": offset,
            })
        except (OSError, ConnectionError):
            sys.stderr.write("\n  Connection dropped, reconnecting...\n")
            try:
                sock = reconnect(host, port)
                continue
            except ConnectionError as e:
                sys.stderr.write("  FATAL: Cannot reconnect: {}\n".format(e))
                sys.exit(1)

        if result.get("status") != "ok":
            sys.stderr.write("\nERROR: {}\n".format(result.get("message", "?")))
            sys.exit(1)

        page = result.get("classes", [])
        classes.extend(page)
        total_classes_matched = result.get("total_classes", 0)

        if len(page) < PAGE_SIZE or len(classes) >= total_classes_matched:
            break
        offset += len(page)

    sock.close()
    sys.stdout.write("\n")
    total_classes = len(classes)
    total_expected = result.get("total_functions", 0)
    sys.stdout.write("Found {} classes with {} total functions\n".format(
        total_classes, total_expected))

    # Step 2: Fetch per class
    all_funcs: list[dict] = []
    failed_classes: list[str] = []
    sock = connect(host, port)

    for i, cls_info in enumerate(classes):
        cls_name = cls_info["class_name"]
        cls_count = cls_info.get("function_count", 0)

        # Progress
        pct = (i + 1) * 100 // total_classes
        sys.stdout.write("\r  [{:3d}%] {}/{} classes | {} funcs | Fetching: {} ({})...".format(
            pct, i + 1, total_classes, len(all_funcs), cls_name, cls_count))
        sys.stdout.flush()

        try:
            result = send_command(sock, {
                "action": "list_blueprint_functions",
                "class_filter": cls_name,
                "include_pins": include_pins,
                "limit": 5000,  # per-class limit (no class has 5K functions)
            })
            if result.get("status") == "ok":
                funcs = result.get("functions", [])
                all_funcs.extend(funcs)
            else:
                failed_classes.append(cls_name)
        except (OSError, ConnectionError):
            # TCP dropped — reconnect and retry this class
            failed_classes.append(cls_name)
            try:
                sock = reconnect(host, port)
            except ConnectionError:
                sys.stderr.write("\nFATAL: Cannot reconnect. Got {} functions so far.\n".format(
                    len(all_funcs)))
                break

    sys.stdout.write("\n")  # newline after progress

    if failed_classes:
        sys.stderr.write("WARNING: Failed to fetch {} classes: {}\n".format(
            len(failed_classes), ", ".join(failed_classes[:20])))

    try:
        sock.close()
    except Exception:
        pass

    return all_funcs


# ---------------------------------------------------------------------------
# Single-shot fetch (original mode)
# ---------------------------------------------------------------------------

def _fetch_single_shot(
    host: str, port: int,
    audio_only: bool, filter_str: str, class_filter: str,
    include_pins: bool, limit: int,
) -> tuple[list[dict], int]:
    """Fetch functions with auto-pagination. Returns (funcs, total_matched)."""
    PAGE_SIZE = 100
    sock = connect(host, port)
    ping = send_command(sock, {"action": "ping"})
    sys.stdout.write("Connected: {} {} ({})\n".format(
        ping.get("engine", "?"), ping.get("version", "?"), ping.get("project", "?")))

    all_funcs: list[dict] = []
    offset = 0
    total = None

    while True:
        sys.stdout.write("\r  Fetching (offset={}, audio_only={}, filter='{}', class='{}')...".format(
            offset, audio_only, filter_str, class_filter))
        sys.stdout.flush()

        try:
            result = send_command(sock, {
                "action": "list_blueprint_functions",
                "include_pins": include_pins,
                "audio_only": audio_only,
                "filter": filter_str,
                "class_filter": class_filter,
                "limit": PAGE_SIZE,
                "offset": offset,
            })
        except (OSError, ConnectionError):
            sys.stderr.write("\n  Connection dropped, reconnecting...\n")
            time.sleep(RECONNECT_DELAY)
            try:
                sock = reconnect(host, port)
                continue  # retry same offset
            except ConnectionError as e:
                sys.stderr.write("  FATAL: Cannot reconnect: {}\n".format(e))
                break

        if result.get("status") != "ok":
            sys.stderr.write("\nERROR: {}\n".format(result.get("message", "?")))
            sys.exit(1)

        page = result.get("functions", [])
        if total is None:
            total = result.get("total", 0)
        all_funcs.extend(page)

        if len(page) < PAGE_SIZE or len(all_funcs) >= min(total, limit):
            break
        offset += len(page)

    sock.close()
    sys.stdout.write("\nReceived {} functions ({} total) in {} pages\n".format(
        len(all_funcs), total, (len(all_funcs) + PAGE_SIZE - 1) // PAGE_SIZE))
    return all_funcs, total or len(all_funcs)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Sync Blueprint functions from UE5 engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="Plugin host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Plugin port")
    parser.add_argument("--filter", default="", help="Substring filter for function/class names")
    parser.add_argument("--class-filter", default="", help="Exact class name filter")
    parser.add_argument("--audio-only", action="store_true",
                        help="Only fetch audio-relevant functions")
    parser.add_argument("--all", action="store_true", dest="fetch_all",
                        help="Fetch ALL functions (batch by class, auto-reconnect)")
    parser.add_argument("--no-pins", action="store_true",
                        help="Skip pin data (faster, smaller payload)")
    parser.add_argument("--limit", type=int, default=10000,
                        help="Max functions per request (ignored with --all)")
    parser.add_argument("--save-json", action="store_true",
                        help="Save raw JSON to exports/")
    parser.add_argument("--diff-only", action="store_true",
                        help="Only show diff against current DB, don't update")
    parser.add_argument("--update-db", action="store_true",
                        help="Update SQLite knowledge DB")
    args = parser.parse_args()

    include_pins = not args.no_pins
    t0 = time.time()

    # --- Fetch ---
    if args.fetch_all:
        sys.stdout.write("=== Full engine sync (batch by class) ===\n")
        engine_funcs = _fetch_all_by_class(args.host, args.port, include_pins)
        total = len(engine_funcs)
    else:
        engine_funcs, total = _fetch_single_shot(
            args.host, args.port,
            args.audio_only, args.filter, args.class_filter,
            include_pins, args.limit,
        )

    elapsed = time.time() - t0
    raw_count = len(engine_funcs)

    # Deduplicate by (class_name, name) — engine may return duplicates across pages
    seen_keys: set[str] = set()
    unique_funcs: list[dict] = []
    for func in engine_funcs:
        key = "{}.{}".format(func.get("class_name", ""), func.get("name", ""))
        if key not in seen_keys:
            seen_keys.add(key)
            unique_funcs.append(func)
    if raw_count != len(unique_funcs):
        sys.stdout.write("Deduplicated: {} -> {} unique functions ({} duplicates removed)\n".format(
            raw_count, len(unique_funcs), raw_count - len(unique_funcs)))
    engine_funcs = unique_funcs

    # Class summary
    classes: dict[str, int] = {}
    for func in engine_funcs:
        cls = func.get("class_name", "Unknown")
        classes[cls] = classes.get(cls, 0) + 1
    sys.stdout.write("Total: {} functions from {} classes in {:.1f}s\n".format(
        len(engine_funcs), len(classes), elapsed))

    # --- Save JSON ---
    if args.save_json:
        export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
        os.makedirs(export_dir, exist_ok=True)
        suffix = "audio" if args.audio_only else "all"
        export_path = os.path.join(export_dir, "blueprint_functions_{}.json".format(suffix))
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump({
                "total": total,
                "shown": len(engine_funcs),
                "class_count": len(classes),
                "functions": engine_funcs,
            }, f, indent=2)
        size_mb = os.path.getsize(export_path) / (1024 * 1024)
        sys.stdout.write("Saved JSON ({:.1f}MB): {}\n".format(size_mb, export_path))

    # --- Diff against current DB ---
    db = None
    try:
        from ue_audio_mcp.knowledge.db import get_knowledge_db
        db = get_knowledge_db()
        existing_rows = db.query_blueprint_scraped()
        existing = {row["name"]: row for row in existing_rows}
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
        pass  # singleton DB, don't close
        sys.stdout.write("\n(diff-only mode, no updates applied)\n")
        return

    # --- Update DB ---
    try:
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
    finally:
        pass  # singleton DB, don't close


if __name__ == "__main__":
    main()
