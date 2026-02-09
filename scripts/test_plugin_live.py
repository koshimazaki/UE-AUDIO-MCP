#!/usr/bin/env python3
"""Live test script for UE5 AudioMCP C++ plugin.

Connects to the plugin via TCP on 127.0.0.1:9877 and exercises
each command. Run this WHILE UE5 editor has the plugin loaded.

Protocol: Flat JSON — all fields at top level next to "action".
The plugin uses a single active builder (no builder_id needed).

Usage:
    python scripts/test_plugin_live.py
    python scripts/test_plugin_live.py --command ping
"""

import argparse
import json
import socket
import struct
import sys

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9877
TIMEOUT = 30.0
HEADER_SIZE = 4


def send_command(sock, command):
    payload = json.dumps(command).encode("utf-8")
    header = struct.pack(">I", len(payload))
    sock.sendall(header + payload)
    raw_header = recv_exact(sock, HEADER_SIZE)
    (length,) = struct.unpack(">I", raw_header)
    raw_body = recv_exact(sock, length)
    return json.loads(raw_body.decode("utf-8"))


def recv_exact(sock, size):
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Connection closed")
        data.extend(chunk)
    return bytes(data)


def _ok(resp, label):
    s = resp.get("status")
    msg = resp.get("message", resp.get("error", ""))
    print(f"  {label}: {s} - {msg}")
    return resp


# ── Test cases (param names match C++ plugin exactly) ─────────────────

def test_ping(sock):
    resp = send_command(sock, {"action": "ping"})
    assert resp.get("status") == "ok", f"Ping failed: {resp}"
    print(f"  Engine: {resp.get('engine')} {resp.get('version')}")
    print(f"  Project: {resp.get('project')}")
    print(f"  Features: {resp.get('features', [])}")
    return resp


def test_unknown_action(sock):
    resp = send_command(sock, {"action": "does_not_exist"})
    assert resp.get("status") == "error", f"Expected error: {resp}"
    print(f"  Correctly rejected unknown action")
    return resp


def test_create_builder(sock, name="TestGraph_MCP"):
    # params: name, asset_type (Source/Patch/Preset)
    resp = send_command(sock, {"action": "create_builder", "name": name, "asset_type": "Source"})
    assert resp.get("status") == "ok", f"create_builder failed: {resp}"
    print(f"  Created builder: {resp.get('name')} ({resp.get('asset_type')})")
    return resp


def test_add_interface(sock):
    # params: interface
    return _ok(send_command(sock, {"action": "add_interface", "interface": "OnPlay"}), "add_interface")


def test_add_graph_input(sock):
    # params: name, type, [default]
    resp = send_command(sock, {"action": "add_graph_input", "name": "Frequency", "type": "Float"})
    assert resp.get("status") == "ok", f"add_graph_input failed: {resp}"
    print(f"  Input added: Frequency (Float)")
    return resp


def test_add_graph_output(sock):
    # params: name, type
    resp = send_command(sock, {"action": "add_graph_output", "name": "Out Audio", "type": "Audio"})
    assert resp.get("status") == "ok", f"add_graph_output failed: {resp}"
    print(f"  Output added: Out Audio (Audio)")
    return resp


def test_add_node(sock, node_id="Osc1", node_type="Sine"):
    # params: id, node_type, [position]
    resp = send_command(sock, {"action": "add_node", "id": node_id, "node_type": node_type})
    assert resp.get("status") == "ok", f"add_node failed: {resp}"
    print(f"  Node added: {node_type} (id={node_id})")
    return resp


def test_set_default(sock, node_id="Osc1", input_name="Frequency", value="440.0"):
    # params: node_id, input, value
    return _ok(send_command(sock, {
        "action": "set_default", "node_id": node_id, "input": input_name, "value": value
    }), "set_default")


def test_connect(sock, from_node, from_pin, to_node, to_pin):
    # params: from_node, from_pin, to_node, to_pin
    resp = send_command(sock, {
        "action": "connect",
        "from_node": from_node, "from_pin": from_pin,
        "to_node": to_node, "to_pin": to_pin
    })
    print(f"  connect {from_node}:{from_pin} -> {to_node}:{to_pin}: {resp.get('status')}")
    return resp


def test_add_graph_variable(sock):
    # params: name, type, [default]
    return _ok(send_command(sock, {
        "action": "add_graph_variable", "name": "MyVar", "type": "Float"
    }), "add_graph_variable")


def test_add_variable_get_node(sock):
    # params: id, variable_name, [delayed]
    return _ok(send_command(sock, {
        "action": "add_variable_get_node", "id": "GetMyVar", "variable_name": "MyVar"
    }), "add_variable_get_node")


def test_add_variable_set_node(sock):
    # params: id, variable_name
    return _ok(send_command(sock, {
        "action": "add_variable_set_node", "id": "SetMyVar", "variable_name": "MyVar"
    }), "add_variable_set_node")


def test_get_graph_input_names(sock):
    resp = send_command(sock, {"action": "get_graph_input_names"})
    print(f"  get_graph_input_names: {resp.get('status')} - names: {resp.get('names', [])}")
    return resp


def test_set_live_updates(sock, enabled=True):
    # params: enabled
    return _ok(send_command(sock, {"action": "set_live_updates", "enabled": enabled}), "set_live_updates")


def test_build_to_asset(sock, name="TestMCP", path="/Game/Audio"):
    # params: name, path
    return _ok(send_command(sock, {"action": "build_to_asset", "name": name, "path": path}), "build_to_asset")


def test_audition(sock):
    return _ok(send_command(sock, {"action": "audition"}), "audition")


def test_convert_to_preset(sock, referenced_asset="/Game/Audio/TestMCP"):
    # params: referenced_asset
    return _ok(send_command(sock, {
        "action": "convert_to_preset", "referenced_asset": referenced_asset
    }), "convert_to_preset")


def test_call_function(sock):
    # params: function, [object_path], [args]
    return _ok(send_command(sock, {
        "action": "call_function",
        "object_path": "/Script/Engine.Default__KismetSystemLibrary",
        "function": "GetPlatformUserName"
    }), "call_function")


def test_list_assets(sock, class_filter="Blueprint", path="/Game/"):
    """List all assets of a given class under a path.
    params: class_filter (optional), path (optional), recursive_classes (optional), limit (optional)
    """
    resp = send_command(sock, {
        "action": "list_assets",
        "class_filter": class_filter,
        "path": path,
        "recursive_classes": True,
    })
    status = resp.get("status")
    if status == "ok":
        total = resp.get("total", 0)
        shown = resp.get("shown", 0)
        print(f"  Found {total} {class_filter} assets ({shown} shown)")
        for a in resp.get("assets", [])[:10]:
            print(f"    {a['name']} ({a['class']}) — {a['path']}")
        if total > 10:
            print(f"    ... and {total - 10} more")
    else:
        print(f"  list_assets: {status} - {resp.get('message', '')}")
    return resp


def test_scan_blueprint(sock, asset_path=None):
    """Scan a Blueprint for graph nodes and audio relevance.
    params: asset_path (required), audio_only (optional), include_pins (optional)
    """
    if not asset_path:
        # Try a common default; caller should override for their project
        asset_path = "/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter"

    resp = send_command(sock, {
        "action": "scan_blueprint",
        "asset_path": asset_path,
        "audio_only": False,
        "include_pins": False,
    })
    status = resp.get("status")
    if status == "ok":
        bp_name = resp.get("blueprint_name", "?")
        parent = resp.get("parent_class", "?")
        total = resp.get("total_nodes", 0)
        graphs = resp.get("graphs", [])
        audio = resp.get("audio_summary", {})
        print(f"  Blueprint: {bp_name} (parent: {parent})")
        print(f"  Graphs: {len(graphs)}, Nodes: {total}, Audio nodes: {audio.get('audio_node_count', 0)}")
        if audio.get("audio_functions"):
            print(f"  Audio functions: {audio['audio_functions']}")
        for g in graphs:
            print(f"    [{g['type']}] {g['name']}: {g.get('shown_nodes', 0)} nodes")
    else:
        print(f"  scan_blueprint: {status} - {resp.get('message', '')}")
    return resp


# ── Full test suite ───────────────────────────────────────────────────

def run_full_suite(sock, blueprint_path=None):
    passed = 0
    failed = 0
    errs = []

    all_tests = [
        ("ping", lambda: test_ping(sock)),
        ("unknown_action", lambda: test_unknown_action(sock)),
        ("create_builder", lambda: test_create_builder(sock)),
        ("add_interface", lambda: test_add_interface(sock)),
        ("add_graph_input", lambda: test_add_graph_input(sock)),
        ("add_graph_output", lambda: test_add_graph_output(sock)),
        ("add_node (Sine)", lambda: test_add_node(sock)),
        ("set_default (440Hz)", lambda: test_set_default(sock)),
        ("connect (Osc->Output)", lambda: test_connect(sock, "Osc1", "Audio", "__graph__", "Out Audio")),
        ("connect (Input->Osc)", lambda: test_connect(sock, "__graph__", "Frequency", "Osc1", "Frequency")),
        ("add_graph_variable", lambda: test_add_graph_variable(sock)),
        ("add_variable_get_node", lambda: test_add_variable_get_node(sock)),
        ("add_variable_set_node", lambda: test_add_variable_set_node(sock)),
        ("get_graph_input_names", lambda: test_get_graph_input_names(sock)),
        ("set_live_updates", lambda: test_set_live_updates(sock)),
        ("build_to_asset", lambda: test_build_to_asset(sock)),
        ("audition", lambda: test_audition(sock)),
        ("call_function", lambda: test_call_function(sock)),
        ("list_assets", lambda: test_list_assets(sock)),
        ("scan_blueprint", lambda: test_scan_blueprint(sock, blueprint_path)),
    ]

    for name, fn in all_tests:
        print(f"\n[TEST] {name}")
        try:
            fn()
            passed += 1
            print(f"  PASS")
        except Exception as e:
            failed += 1
            errs.append((name, str(e)))
            print(f"  FAIL: {e}")

    return passed, failed, errs


def run_single(sock, command_name):
    needs_builder = {
        "add_interface", "add_graph_input", "add_graph_output",
        "add_node", "set_default", "connect",
        "add_graph_variable", "add_variable_get_node", "add_variable_set_node",
        "get_graph_input_names", "set_live_updates",
        "build_to_asset", "audition", "convert_to_preset",
    }

    if command_name in needs_builder:
        print("[SETUP] Creating builder first...")
        test_create_builder(sock, f"Test_{command_name}")
        if command_name in ("set_default", "connect"):
            test_add_node(sock)
        if command_name == "connect":
            test_add_graph_output(sock)
        if command_name in ("add_variable_get_node", "add_variable_set_node"):
            test_add_graph_variable(sock)

    dispatch = {
        "ping": lambda: test_ping(sock),
        "unknown_action": lambda: test_unknown_action(sock),
        "create_builder": lambda: test_create_builder(sock),
        "add_interface": lambda: test_add_interface(sock),
        "add_graph_input": lambda: test_add_graph_input(sock),
        "add_graph_output": lambda: test_add_graph_output(sock),
        "add_node": lambda: test_add_node(sock),
        "set_default": lambda: test_set_default(sock),
        "connect": lambda: test_connect(sock, "Osc1", "Audio", "__graph__", "Out Audio"),
        "add_graph_variable": lambda: test_add_graph_variable(sock),
        "add_variable_get_node": lambda: test_add_variable_get_node(sock),
        "add_variable_set_node": lambda: test_add_variable_set_node(sock),
        "get_graph_input_names": lambda: test_get_graph_input_names(sock),
        "set_live_updates": lambda: test_set_live_updates(sock),
        "build_to_asset": lambda: test_build_to_asset(sock),
        "audition": lambda: test_audition(sock),
        "convert_to_preset": lambda: test_convert_to_preset(sock),
        "call_function": lambda: test_call_function(sock),
        "list_assets": lambda: test_list_assets(sock),
        "scan_blueprint": lambda: test_scan_blueprint(sock),
    }

    if command_name not in dispatch:
        print(f"Unknown: {command_name}. Available: {', '.join(sorted(dispatch.keys()))}")
        return
    print(f"\n[TEST] {command_name}")
    dispatch[command_name]()


def main():
    parser = argparse.ArgumentParser(description="Live test for UE5 AudioMCP plugin")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--command", "-c", help="Run single command test")
    parser.add_argument("--blueprint", "-b", help="Blueprint asset path for scan_blueprint test")
    args = parser.parse_args()

    print("=" * 60)
    print("AudioMCP Plugin Live Test")
    print(f"Connecting to {args.host}:{args.port}...")
    print("=" * 60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((args.host, args.port))
        print("Connected!\n")
    except (OSError, ConnectionError) as e:
        print(f"\nFAILED to connect: {e}")
        print("\nMake sure:")
        print("  1. UE5 Editor is running")
        print("  2. UEAudioMCP plugin is enabled")
        print("  3. Plugin is listening on port 9877")
        sys.exit(1)

    try:
        if args.command:
            run_single(sock, args.command)
        else:
            passed, failed, errors = run_full_suite(sock, args.blueprint)
            print("\n" + "=" * 60)
            print(f"RESULTS: {passed} passed, {failed} failed")
            print("=" * 60)
            if errors:
                print("\nFailed tests:")
                for name, err in errors:
                    print(f"  {name}: {err}")
            sys.exit(1 if failed > 0 else 0)
    finally:
        sock.close()


if __name__ == "__main__":
    main()
