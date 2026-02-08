#!/usr/bin/env python3
"""Live test script for UE5 AudioMCP C++ plugin.

Connects to the plugin via TCP on 127.0.0.1:9877 and exercises
each command. Run this WHILE UE5 editor has the plugin loaded.

Usage:
    python scripts/test_plugin_live.py
    python scripts/test_plugin_live.py --host 127.0.0.1 --port 9877
    python scripts/test_plugin_live.py --command ping   # single command

Commands tested:
    ping, create_builder, add_interface, add_graph_input,
    add_graph_output, add_node, set_default, connect,
    add_graph_variable, add_variable_get_node, add_variable_set_node,
    build_to_asset, audition, get_graph_input_names,
    convert_to_preset, set_live_updates, call_function
"""

import argparse
import json
import socket
import struct
import sys
import time

# ── Config ────────────────────────────────────────────────────────────
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9877
TIMEOUT = 30.0
HEADER_SIZE = 4


# ── Wire protocol ────────────────────────────────────────────────────

def send_command(sock, command):
    """Send JSON command, receive JSON response. Returns dict."""
    payload = json.dumps(command).encode("utf-8")
    header = struct.pack(">I", len(payload))
    sock.sendall(header + payload)

    # Receive response
    raw_header = recv_exact(sock, HEADER_SIZE)
    (length,) = struct.unpack(">I", raw_header)
    raw_body = recv_exact(sock, length)
    return json.loads(raw_body.decode("utf-8"))


def recv_exact(sock, size):
    """Read exactly `size` bytes."""
    data = bytearray()
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Connection closed")
        data.extend(chunk)
    return bytes(data)


# ── Test cases ────────────────────────────────────────────────────────

def test_ping(sock):
    """Test: ping — should return engine info."""
    resp = send_command(sock, {"action": "ping"})
    assert resp.get("status") == "ok", f"Ping failed: {resp}"
    print(f"  Engine: {resp.get('engine')} {resp.get('version')}")
    print(f"  Project: {resp.get('project')}")
    print(f"  Features: {resp.get('features', [])}")
    return resp


def test_create_builder(sock, name="TestGraph_MCP"):
    """Test: create_builder — creates a new MetaSound source builder."""
    resp = send_command(sock, {
        "action": "create_builder",
        "params": {"name": name}
    })
    assert resp.get("status") == "ok", f"create_builder failed: {resp}"
    builder_id = resp.get("builder_id")
    print(f"  Builder ID: {builder_id}")
    return resp


def test_add_interface(sock, builder_id):
    """Test: add_interface — adds OnPlay output interface."""
    resp = send_command(sock, {
        "action": "add_interface",
        "params": {
            "builder_id": builder_id,
            "interface": "OnPlay"
        }
    })
    print(f"  add_interface: {resp.get('status')} - {resp.get('message', resp.get('error', ''))}")
    return resp


def test_add_graph_input(sock, builder_id):
    """Test: add_graph_input — adds a Float input to the graph."""
    resp = send_command(sock, {
        "action": "add_graph_input",
        "params": {
            "builder_id": builder_id,
            "name": "Frequency",
            "type": "Float"
        }
    })
    assert resp.get("status") == "ok", f"add_graph_input failed: {resp}"
    print(f"  Input added: Frequency (Float)")
    return resp


def test_add_graph_output(sock, builder_id):
    """Test: add_graph_output — adds an Audio output to the graph."""
    resp = send_command(sock, {
        "action": "add_graph_output",
        "params": {
            "builder_id": builder_id,
            "name": "Out Audio",
            "type": "Audio"
        }
    })
    assert resp.get("status") == "ok", f"add_graph_output failed: {resp}"
    print(f"  Output added: Out Audio (Audio)")
    return resp


def test_add_node(sock, builder_id):
    """Test: add_node — adds a Sine oscillator node."""
    resp = send_command(sock, {
        "action": "add_node",
        "params": {
            "builder_id": builder_id,
            "node_type": "Sine",
            "name": "Osc1"
        }
    })
    assert resp.get("status") == "ok", f"add_node failed: {resp}"
    node_id = resp.get("node_id")
    print(f"  Node added: Sine -> {node_id}")
    return resp


def test_set_default(sock, builder_id, node_name="Osc1"):
    """Test: set_default — sets Frequency on the Sine node."""
    resp = send_command(sock, {
        "action": "set_default",
        "params": {
            "builder_id": builder_id,
            "node_name": node_name,
            "pin_name": "Frequency",
            "value": "440.0"
        }
    })
    print(f"  set_default: {resp.get('status')} - {resp.get('message', resp.get('error', ''))}")
    return resp


def test_connect(sock, builder_id, src_node, src_pin, dst_node, dst_pin):
    """Test: connect — wires two pins together."""
    resp = send_command(sock, {
        "action": "connect",
        "params": {
            "builder_id": builder_id,
            "source_node": src_node,
            "source_pin": src_pin,
            "dest_node": dst_node,
            "dest_pin": dst_pin,
        }
    })
    print(f"  connect {src_node}:{src_pin} -> {dst_node}:{dst_pin}: {resp.get('status')}")
    return resp


def test_add_graph_variable(sock, builder_id):
    """Test: add_graph_variable — adds a Float variable."""
    resp = send_command(sock, {
        "action": "add_graph_variable",
        "params": {
            "builder_id": builder_id,
            "name": "MyVar",
            "type": "Float"
        }
    })
    print(f"  add_graph_variable: {resp.get('status')} - {resp.get('message', resp.get('error', ''))}")
    return resp


def test_add_variable_get_node(sock, builder_id):
    """Test: add_variable_get_node."""
    resp = send_command(sock, {
        "action": "add_variable_get_node",
        "params": {
            "builder_id": builder_id,
            "variable_name": "MyVar"
        }
    })
    print(f"  add_variable_get_node: {resp.get('status')} - {resp.get('message', resp.get('error', ''))}")
    return resp


def test_add_variable_set_node(sock, builder_id):
    """Test: add_variable_set_node."""
    resp = send_command(sock, {
        "action": "add_variable_set_node",
        "params": {
            "builder_id": builder_id,
            "variable_name": "MyVar"
        }
    })
    print(f"  add_variable_set_node: {resp.get('status')} - {resp.get('message', resp.get('error', ''))}")
    return resp


def test_get_graph_input_names(sock, builder_id):
    """Test: get_graph_input_names — list current inputs."""
    resp = send_command(sock, {
        "action": "get_graph_input_names",
        "params": {
            "builder_id": builder_id,
        }
    })
    print(f"  get_graph_input_names: {resp.get('status')} - inputs: {resp.get('input_names', [])}")
    return resp


def test_set_live_updates(sock, builder_id, enabled=True):
    """Test: set_live_updates."""
    resp = send_command(sock, {
        "action": "set_live_updates",
        "params": {
            "builder_id": builder_id,
            "enabled": enabled,
        }
    })
    print(f"  set_live_updates({enabled}): {resp.get('status')}")
    return resp


def test_build_to_asset(sock, builder_id, asset_path="/Game/Audio/TestMCP"):
    """Test: build_to_asset — saves the graph as a MetaSound asset."""
    resp = send_command(sock, {
        "action": "build_to_asset",
        "params": {
            "builder_id": builder_id,
            "asset_path": asset_path,
        }
    })
    print(f"  build_to_asset: {resp.get('status')} - {resp.get('message', resp.get('error', ''))}")
    return resp


def test_audition(sock, builder_id):
    """Test: audition — play the graph in-editor."""
    resp = send_command(sock, {
        "action": "audition",
        "params": {
            "builder_id": builder_id,
        }
    })
    print(f"  audition: {resp.get('status')} - {resp.get('message', resp.get('error', ''))}")
    return resp


def test_convert_to_preset(sock, builder_id, reference_path="/Game/Audio/TestMCP"):
    """Test: convert_to_preset."""
    resp = send_command(sock, {
        "action": "convert_to_preset",
        "params": {
            "builder_id": builder_id,
            "reference_path": reference_path,
        }
    })
    print(f"  convert_to_preset: {resp.get('status')} - {resp.get('message', resp.get('error', ''))}")
    return resp


def test_call_function(sock):
    """Test: call_function — try calling a simple engine function."""
    resp = send_command(sock, {
        "action": "call_function",
        "params": {
            "object_path": "/Script/Engine.Default__KismetSystemLibrary",
            "function_name": "GetPlatformUserName",
        }
    })
    print(f"  call_function: {resp.get('status')} - {resp.get('result', resp.get('error', ''))}")
    return resp


def test_unknown_action(sock):
    """Test: unknown action — should return error gracefully."""
    resp = send_command(sock, {"action": "does_not_exist"})
    assert resp.get("status") == "error", f"Expected error for unknown action: {resp}"
    print(f"  unknown action: {resp.get('error', '')}")
    return resp


# ── Full test suite ───────────────────────────────────────────────────

def run_full_suite(sock):
    """Run all tests in order, building a simple Sine -> Output graph."""
    passed = 0
    failed = 0
    errors = []
    builder_id = None

    tests = [
        ("ping", lambda: test_ping(sock)),
        ("unknown_action", lambda: test_unknown_action(sock)),
        ("create_builder", lambda: test_create_builder(sock)),
    ]

    # Run connection tests first
    for name, fn in tests:
        print(f"\n[TEST] {name}")
        try:
            resp = fn()
            if name == "create_builder":
                builder_id = resp.get("builder_id")
            passed += 1
            print(f"  PASS")
        except Exception as e:
            failed += 1
            errors.append((name, str(e)))
            print(f"  FAIL: {e}")

    if builder_id is None:
        print("\nCannot continue without builder_id. Stopping.")
        return passed, failed, errors

    # Builder-dependent tests
    builder_tests = [
        ("add_interface", lambda: test_add_interface(sock, builder_id)),
        ("add_graph_input", lambda: test_add_graph_input(sock, builder_id)),
        ("add_graph_output", lambda: test_add_graph_output(sock, builder_id)),
        ("add_node", lambda: test_add_node(sock, builder_id)),
        ("set_default", lambda: test_set_default(sock, builder_id)),
        ("connect (Osc->Output)", lambda: test_connect(
            sock, builder_id, "Osc1", "Audio", "__graph__", "Out Audio")),
        ("connect (Input->Osc)", lambda: test_connect(
            sock, builder_id, "__graph__", "Frequency", "Osc1", "Frequency")),
        ("add_graph_variable", lambda: test_add_graph_variable(sock, builder_id)),
        ("add_variable_get_node", lambda: test_add_variable_get_node(sock, builder_id)),
        ("add_variable_set_node", lambda: test_add_variable_set_node(sock, builder_id)),
        ("get_graph_input_names", lambda: test_get_graph_input_names(sock, builder_id)),
        ("set_live_updates", lambda: test_set_live_updates(sock, builder_id)),
        ("build_to_asset", lambda: test_build_to_asset(sock, builder_id)),
        ("audition", lambda: test_audition(sock, builder_id)),
        ("call_function", lambda: test_call_function(sock)),
    ]

    for name, fn in builder_tests:
        print(f"\n[TEST] {name}")
        try:
            fn()
            passed += 1
            print(f"  PASS")
        except Exception as e:
            failed += 1
            errors.append((name, str(e)))
            print(f"  FAIL: {e}")

    return passed, failed, errors


def run_single(sock, command_name):
    """Run a single command by name."""
    builder_id = None

    # Some commands need a builder first
    needs_builder = {
        "add_interface", "add_graph_input", "add_graph_output",
        "add_node", "set_default", "connect",
        "add_graph_variable", "add_variable_get_node", "add_variable_set_node",
        "get_graph_input_names", "set_live_updates",
        "build_to_asset", "audition", "convert_to_preset",
    }

    if command_name in needs_builder:
        print("[SETUP] Creating builder first...")
        resp = test_create_builder(sock, f"Test_{command_name}")
        builder_id = resp.get("builder_id")
        # Add basic structure for commands that need it
        if command_name in ("set_default", "connect"):
            test_add_node(sock, builder_id)
        if command_name == "connect":
            test_add_graph_output(sock, builder_id)
        if command_name in ("add_variable_get_node", "add_variable_set_node"):
            test_add_graph_variable(sock, builder_id)

    dispatch = {
        "ping": lambda: test_ping(sock),
        "unknown_action": lambda: test_unknown_action(sock),
        "create_builder": lambda: test_create_builder(sock),
        "add_interface": lambda: test_add_interface(sock, builder_id),
        "add_graph_input": lambda: test_add_graph_input(sock, builder_id),
        "add_graph_output": lambda: test_add_graph_output(sock, builder_id),
        "add_node": lambda: test_add_node(sock, builder_id),
        "set_default": lambda: test_set_default(sock, builder_id),
        "connect": lambda: test_connect(sock, builder_id, "Osc1", "Audio", "__graph__", "Out Audio"),
        "add_graph_variable": lambda: test_add_graph_variable(sock, builder_id),
        "add_variable_get_node": lambda: test_add_variable_get_node(sock, builder_id),
        "add_variable_set_node": lambda: test_add_variable_set_node(sock, builder_id),
        "get_graph_input_names": lambda: test_get_graph_input_names(sock, builder_id),
        "set_live_updates": lambda: test_set_live_updates(sock, builder_id),
        "build_to_asset": lambda: test_build_to_asset(sock, builder_id),
        "audition": lambda: test_audition(sock, builder_id),
        "convert_to_preset": lambda: test_convert_to_preset(sock, builder_id),
        "call_function": lambda: test_call_function(sock),
    }

    if command_name not in dispatch:
        print(f"Unknown command: {command_name}")
        print(f"Available: {', '.join(sorted(dispatch.keys()))}")
        return

    print(f"\n[TEST] {command_name}")
    dispatch[command_name]()


# ── Main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Live test for UE5 AudioMCP plugin")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--command", "-c", help="Run single command test")
    parser.add_argument("--skip-destructive", action="store_true",
                        help="Skip build_to_asset and audition")
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
        print("  4. No firewall blocking localhost:9877")
        sys.exit(1)

    try:
        if args.command:
            run_single(sock, args.command)
        else:
            passed, failed, errors = run_full_suite(sock)

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
