#!/usr/bin/env python3
"""Sync MetaSounds node catalogue from a running UE5 engine.

Connects to the UE5 AudioMCP plugin via TCP and fetches ALL registered
MetaSounds node classes with their complete pin specs from the engine
registry (ISearchEngine::FindAllClasses).

Usage:
    python scripts/sync_nodes_from_engine.py
    python scripts/sync_nodes_from_engine.py --save-json
    python scripts/sync_nodes_from_engine.py --save-json --update-db
    python scripts/sync_nodes_from_engine.py --diff-only
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
# TCP helpers (same protocol as scan_project.py)
# ---------------------------------------------------------------------------

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9877
TIMEOUT = 60.0
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

def _build_diff(engine_nodes: list[dict], catalogue: dict) -> dict:
    """Compare engine nodes against current catalogue, return diff report."""
    from ue_audio_mcp.tools.ms_builder import _engine_node_to_nodedef

    new_nodes = []
    updated_nodes = []
    pin_changes = []

    for enode in engine_nodes:
        node_def = _engine_node_to_nodedef(enode)
        if node_def is None:
            continue

        name = node_def["name"]
        if name not in catalogue:
            new_nodes.append({
                "name": name,
                "class_name": enode.get("class_name", ""),
                "inputs": len(node_def["inputs"]),
                "outputs": len(node_def["outputs"]),
                "category": node_def["category"],
            })
        else:
            existing = catalogue[name]
            # Compare pins
            old_in = {p["name"]: p["type"] for p in existing.get("inputs", [])}
            new_in = {p["name"]: p["type"] for p in node_def.get("inputs", [])}
            old_out = {p["name"]: p["type"] for p in existing.get("outputs", [])}
            new_out = {p["name"]: p["type"] for p in node_def.get("outputs", [])}

            changes = []
            # Added inputs
            for pn in sorted(set(new_in) - set(old_in)):
                changes.append("+input: {} ({})".format(pn, new_in[pn]))
            # Removed inputs
            for pn in sorted(set(old_in) - set(new_in)):
                changes.append("-input: {} ({})".format(pn, old_in[pn]))
            # Type changes
            for pn in sorted(set(old_in) & set(new_in)):
                if old_in[pn] != new_in[pn]:
                    changes.append("~input: {} {} -> {}".format(pn, old_in[pn], new_in[pn]))
            # Added outputs
            for pn in sorted(set(new_out) - set(old_out)):
                changes.append("+output: {} ({})".format(pn, new_out[pn]))
            # Removed outputs
            for pn in sorted(set(old_out) - set(new_out)):
                changes.append("-output: {} ({})".format(pn, old_out[pn]))
            # Type changes
            for pn in sorted(set(old_out) & set(new_out)):
                if old_out[pn] != new_out[pn]:
                    changes.append("~output: {} {} -> {}".format(pn, old_out[pn], new_out[pn]))

            if changes:
                updated_nodes.append(name)
                pin_changes.append({"node": name, "changes": changes})

    return {
        "new_nodes": new_nodes,
        "updated_nodes": updated_nodes,
        "pin_changes": pin_changes,
        "new_count": len(new_nodes),
        "updated_count": len(updated_nodes),
        "total_pin_changes": sum(len(pc["changes"]) for pc in pin_changes),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Sync MetaSounds nodes from UE5 engine")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Plugin host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Plugin port")
    parser.add_argument("--filter", default="", help="Substring filter for node names")
    parser.add_argument("--limit", type=int, default=10000, help="Max nodes to fetch")
    parser.add_argument("--save-json", action="store_true",
                        help="Save raw JSON to exports/all_metasound_nodes.json")
    parser.add_argument("--diff-only", action="store_true",
                        help="Only show diff, don't update anything")
    parser.add_argument("--update-db", action="store_true",
                        help="Update SQLite knowledge DB")
    args = parser.parse_args()

    # Connect
    print("Connecting to UE5 plugin at {}:{}...".format(args.host, args.port))
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((args.host, args.port))
    except (OSError, ConnectionError) as e:
        print("ERROR: Cannot connect: {}".format(e))
        sys.exit(1)

    # Ping
    ping = send_command(sock, {"action": "ping"})
    print("Connected: {} {} ({})".format(
        ping.get("engine", "?"), ping.get("version", "?"), ping.get("project", "?")))

    # Fetch all nodes
    print("Fetching node classes (limit={}, filter='{}')...".format(args.limit, args.filter))
    t0 = time.time()
    result = send_command(sock, {
        "action": "list_metasound_nodes",
        "include_pins": True,
        "include_metadata": True,
        "filter": args.filter,
        "limit": args.limit,
    })
    elapsed = time.time() - t0

    sock.close()

    if result.get("status") != "ok":
        print("ERROR: {}".format(result.get("message", "Unknown error")))
        sys.exit(1)

    engine_nodes = result.get("nodes", [])
    total = result.get("total", len(engine_nodes))
    shown = result.get("shown", len(engine_nodes))
    print("Received {} nodes ({} total matched) in {:.1f}s".format(shown, total, elapsed))

    # Save raw JSON
    if args.save_json:
        export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
        os.makedirs(export_dir, exist_ok=True)
        export_path = os.path.join(export_dir, "all_metasound_nodes.json")
        with open(export_path, "w") as f:
            json.dump({"total": total, "shown": shown, "nodes": engine_nodes}, f, indent=2)
        print("Saved raw JSON to {}".format(export_path))

    # Diff against current catalogue
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
    from ue_audio_mcp.knowledge.metasound_nodes import METASOUND_NODES

    diff = _build_diff(engine_nodes, METASOUND_NODES)

    print("\n--- Diff Report ---")
    print("Current catalogue: {} nodes".format(len(METASOUND_NODES)))
    print("Engine registry:   {} nodes".format(len(engine_nodes)))
    print("New nodes:         {}".format(diff["new_count"]))
    print("Updated nodes:     {}".format(diff["updated_count"]))
    print("Pin changes:       {}".format(diff["total_pin_changes"]))

    if diff["new_nodes"]:
        print("\nNew nodes:")
        for nn in diff["new_nodes"][:50]:
            print("  + {} [{}] ({} in, {} out)".format(
                nn["name"], nn["class_name"], nn["inputs"], nn["outputs"]))
        if len(diff["new_nodes"]) > 50:
            print("  ... and {} more".format(len(diff["new_nodes"]) - 50))

    if diff["pin_changes"]:
        print("\nPin changes:")
        for pc in diff["pin_changes"][:30]:
            print("  {}:".format(pc["node"]))
            for change in pc["changes"]:
                print("    {}".format(change))
        if len(diff["pin_changes"]) > 30:
            print("  ... and {} more nodes with changes".format(
                len(diff["pin_changes"]) - 30))

    if args.diff_only:
        print("\n(diff-only mode, no updates applied)")
        return

    # Update in-memory catalogue
    from ue_audio_mcp.tools.ms_builder import _engine_node_to_nodedef
    from ue_audio_mcp.knowledge.metasound_nodes import CLASS_NAME_TO_DISPLAY

    new_added = 0
    for enode in engine_nodes:
        node_def = _engine_node_to_nodedef(enode)
        if node_def is None:
            continue
        name = node_def["name"]
        if name in METASOUND_NODES:
            METASOUND_NODES[name]["inputs"] = node_def["inputs"]
            METASOUND_NODES[name]["outputs"] = node_def["outputs"]
        else:
            METASOUND_NODES[name] = node_def
            new_added += 1
        class_name = enode.get("class_name", "")
        if class_name and name and class_name not in CLASS_NAME_TO_DISPLAY:
            CLASS_NAME_TO_DISPLAY[class_name] = name

    print("\nCatalogue updated: {} total nodes ({} new)".format(
        len(METASOUND_NODES), new_added))

    # Update DB
    if args.update_db:
        try:
            from ue_audio_mcp.knowledge.db import KnowledgeDB
            db = KnowledgeDB()
            count = 0
            for enode in engine_nodes:
                node_def = _engine_node_to_nodedef(enode)
                if node_def:
                    db.insert_node(node_def)
                    count += 1
            db.close()
            print("SQLite DB updated: {} nodes upserted".format(count))
        except Exception as e:
            print("WARNING: DB update failed: {}".format(e))


if __name__ == "__main__":
    main()
