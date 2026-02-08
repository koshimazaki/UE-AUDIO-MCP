#!/usr/bin/env python3
"""Test script for live UE5 Audio MCP plugin connection.

Usage:
    python scripts/test_live_ue5.py                    # Run all tests
    python scripts/test_live_ue5.py list_nodes          # List available node classes
    python scripts/test_live_ue5.py list_nodes Sine     # Search for Sine nodes
    python scripts/test_live_ue5.py sine_tone           # Build a sine tone patch
"""

import json
import socket
import struct
import sys


def send_command(sock, cmd):
    payload = json.dumps(cmd).encode("utf-8")
    sock.sendall(struct.pack(">I", len(payload)) + payload)
    header = sock.recv(4)
    if len(header) < 4:
        raise ConnectionError("Server closed connection")
    length = struct.unpack(">I", header)[0]
    data = b""
    while len(data) < length:
        chunk = sock.recv(min(length - len(data), 65536))
        if not chunk:
            raise ConnectionError("Server closed connection")
        data += chunk
    return json.loads(data.decode("utf-8"))


def connect(host="127.0.0.1", port=9877):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    sock.connect((host, port))
    return sock


def test_ping(sock):
    print("\n--- PING ---")
    resp = send_command(sock, {"action": "ping"})
    print(f"  Status: {resp.get('status')}")
    return resp.get("status") == "ok"


def test_list_nodes(sock, filter_str=""):
    print(f"\n--- LIST NODE CLASSES (filter='{filter_str}') ---")
    cmd = {"action": "list_node_classes", "limit": 500}
    if filter_str:
        cmd["filter"] = filter_str
    resp = send_command(sock, cmd)
    if resp.get("status") != "ok":
        print(f"  ERROR: {resp.get('message')}")
        return False
    nodes = resp.get("nodes", [])
    print(f"  Total: {resp.get('total', 0)}, Shown: {len(nodes)}")
    for node in nodes:
        print(f"    {node['class_name']}")
    return True


def test_sine_tone(sock):
    """Build a sine tone: Sine -> Multiply(Audio by Float) -> Audio Output."""
    print("\n--- BUILD SINE TONE ---")

    # UE 5.7 correct pin names:
    # - Sine: outputs "Audio", inputs "Frequency"
    # - Multiply (Audio by Float): inputs "PrimaryOperand" (audio), "AdditionalOperands" (float), output "Out"
    # - Source graph outputs: "Audio:0" (mono)
    commands = [
        {"action": "create_builder", "asset_type": "Source", "name": "MCP_SineTone"},
        {"action": "add_node", "id": "sine1", "node_type": "Sine"},
        {"action": "set_default", "node_id": "sine1", "input": "Frequency", "value": 440.0},
        {"action": "add_node", "id": "gain1", "node_type": "Multiply (Audio by Float)"},
        {"action": "set_default", "node_id": "gain1", "input": "AdditionalOperands", "value": 0.25},
        {"action": "connect", "from_node": "sine1", "from_pin": "Audio",
         "to_node": "gain1", "to_pin": "PrimaryOperand"},
        {"action": "connect", "from_node": "gain1", "from_pin": "Out",
         "to_node": "__graph__", "to_pin": "Audio:0"},
        {"action": "audition"},
    ]

    for i, cmd in enumerate(commands):
        action = cmd["action"]
        resp = send_command(sock, cmd)
        status = resp.get("status", "unknown")
        msg = resp.get("message", "")

        if status == "ok":
            print(f"  [{i+1}/{len(commands)}] OK: {action} -- {msg}")
        else:
            print(f"  [{i+1}/{len(commands)}] FAIL: {action} -- {msg}")
            return False

    print("\n  Sine tone should be audible!")
    return True


def test_full_pipeline(sock):
    results = {}
    results["ping"] = test_ping(sock)

    print("\n--- DISCOVER NODES ---")
    cmd = {"action": "list_node_classes", "filter": "Sine", "limit": 5}
    resp = send_command(sock, cmd)
    if resp.get("status") == "ok":
        nodes = resp.get("nodes", [])
        sine_found = any(n["class_name"] == "UE::Sine::Audio" for n in nodes)
        print(f"  UE::Sine::Audio found: {sine_found}")
        results["discover"] = sine_found
    else:
        results["discover"] = False

    results["sine_tone"] = test_sine_tone(sock)

    print("\n" + "=" * 50)
    print("RESULTS:")
    for test, passed in results.items():
        icon = "PASS" if passed else "FAIL"
        print(f"  [{icon}] {test}")
    print("=" * 50)
    return all(results.values())


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    filter_str = sys.argv[2] if len(sys.argv) > 2 else ""

    print("Connecting to UE5 Audio MCP on 127.0.0.1:9877...")
    try:
        sock = connect()
    except ConnectionRefusedError:
        print("ERROR: Could not connect. Is UE Editor running with UEAudioMCP plugin?")
        sys.exit(1)

    try:
        if mode == "list_nodes":
            test_list_nodes(sock, filter_str)
        elif mode == "sine_tone":
            test_sine_tone(sock)
        elif mode == "ping":
            test_ping(sock)
        elif mode == "full":
            success = test_full_pipeline(sock)
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown mode: {mode}")
            sys.exit(1)
    finally:
        sock.close()


if __name__ == "__main__":
    main()
