"""Blueprint Builder tools — add nodes, connect pins, and compile Blueprints via UE5 plugin.

8 tools for additive Blueprint modification: open, add nodes (allowlisted),
connect pins, set defaults, compile, register existing nodes, list pins,
and a high-level wire-audio-param helper.

Requires an active UE5 plugin connection (ue5_connect).
"""

from __future__ import annotations

import json
import logging

from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _error, _ok
from ue_audio_mcp.ue5_connection import get_ue5_connection

log = logging.getLogger(__name__)


@mcp.tool()
def bp_open_blueprint(asset_path: str) -> str:
    """Open a Blueprint asset for editing via the UE5 plugin.

    Must be called before adding nodes or connecting pins.
    Resets any previously registered node handles.

    Args:
        asset_path: Blueprint asset path (e.g. "/Game/Blueprints/BP_Character")
    """
    if not asset_path.strip():
        return _error("asset_path cannot be empty")
    if ".." in asset_path:
        return _error("asset_path must not contain '..'")

    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "bp_open_blueprint",
            "asset_path": asset_path,
        })
        if result.get("status") == "error":
            return _error(result.get("message", "bp_open_blueprint failed"))
        return _ok(result)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def bp_add_bp_node(
    node_id: str,
    node_kind: str,
    function_name: str = "",
    event_name: str = "",
    variable_name: str = "",
    position_x: int = 0,
    position_y: int = 0,
) -> str:
    """Add a node to the active Blueprint's event graph.

    Supports 4 node kinds:
    - CallFunction: Audio-allowlisted functions (SetFloatParameter, PlaySound2D, etc.)
    - CustomEvent: User-defined events
    - VariableGet: Read a Blueprint variable (must pre-exist)
    - VariableSet: Write a Blueprint variable (must pre-exist)

    Args:
        node_id: Unique ID for this node (used in connect/set_pin calls)
        node_kind: One of: CallFunction, CustomEvent, VariableGet, VariableSet
        function_name: Required for CallFunction — the function to call
        event_name: Required for CustomEvent — the event name
        variable_name: Required for VariableGet/VariableSet — the variable name
        position_x: Editor X position
        position_y: Editor Y position
    """
    valid_kinds = {"CallFunction", "CustomEvent", "VariableGet", "VariableSet"}
    if node_kind not in valid_kinds:
        return _error("Invalid node_kind '{}'. Must be one of: {}".format(
            node_kind, ", ".join(sorted(valid_kinds))
        ))
    if not node_id.strip():
        return _error("node_id cannot be empty")

    cmd = {
        "action": "bp_add_node",
        "id": node_id,
        "node_kind": node_kind,
        "position": [position_x, position_y],
    }

    if node_kind == "CallFunction":
        if not function_name:
            return _error("CallFunction requires function_name")
        cmd["function_name"] = function_name
    elif node_kind == "CustomEvent":
        if not event_name:
            return _error("CustomEvent requires event_name")
        cmd["event_name"] = event_name
    elif node_kind in ("VariableGet", "VariableSet"):
        if not variable_name:
            return _error("{} requires variable_name".format(node_kind))
        cmd["variable_name"] = variable_name

    conn = get_ue5_connection()
    try:
        result = conn.send_command(cmd)
        if result.get("status") == "error":
            return _error(result.get("message", "bp_add_node failed"))
        return _ok(result)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def bp_connect_bp_pins(
    from_node: str,
    from_pin: str,
    to_node: str,
    to_pin: str,
) -> str:
    """Connect two pins between registered Blueprint nodes.

    Both nodes must be registered (via bp_add_bp_node or bp_register_existing).

    Args:
        from_node: Source node ID
        from_pin: Source output pin name
        to_node: Destination node ID
        to_pin: Destination input pin name
    """
    if not all([from_node, from_pin, to_node, to_pin]):
        return _error("All pin params required: from_node, from_pin, to_node, to_pin")

    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "bp_connect_pins",
            "from_node": from_node,
            "from_pin": from_pin,
            "to_node": to_node,
            "to_pin": to_pin,
        })
        if result.get("status") == "error":
            return _error(result.get("message", "bp_connect_pins failed"))
        return _ok(result)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def bp_set_bp_pin(node_id: str, pin_name: str, value: str) -> str:
    """Set a default value on a Blueprint node's input pin.

    Args:
        node_id: Registered node ID
        pin_name: Input pin name
        value: Default value as string
    """
    if not node_id.strip():
        return _error("node_id cannot be empty")
    if not pin_name.strip():
        return _error("pin_name cannot be empty")

    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "bp_set_pin_default",
            "node_id": node_id,
            "pin_name": pin_name,
            "value": value,
        })
        if result.get("status") == "error":
            return _error(result.get("message", "bp_set_pin_default failed"))
        return _ok(result)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def bp_compile_blueprint() -> str:
    """Compile the active Blueprint.

    Returns compile status and any compiler messages.
    Must have called bp_open_blueprint first.
    """
    conn = get_ue5_connection()
    try:
        result = conn.send_command({"action": "bp_compile"})
        if result.get("status") == "error":
            return _error(result.get("message", "bp_compile failed"))
        return _ok(result)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def bp_register_existing(node_id: str, node_guid: str) -> str:
    """Register an existing Blueprint node by its GUID so it can be wired to.

    Use bp_scan_blueprint with include_pins=true to find node GUIDs,
    then register them here before connecting pins.

    Args:
        node_id: MCP handle ID you want to use for this node
        node_guid: The node's FGuid string from the Blueprint scan
    """
    if not node_id.strip():
        return _error("node_id cannot be empty")
    if not node_guid.strip():
        return _error("node_guid cannot be empty")

    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "bp_register_existing_node",
            "id": node_id,
            "node_guid": node_guid,
        })
        if result.get("status") == "error":
            return _error(result.get("message", "bp_register_existing_node failed"))
        return _ok(result)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def bp_list_node_pins(node_id: str) -> str:
    """List all pins on a registered Blueprint node.

    Returns pin name, direction, type, default value, and connection status.

    Args:
        node_id: Registered node ID
    """
    if not node_id.strip():
        return _error("node_id cannot be empty")

    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "bp_list_pins",
            "node_id": node_id,
        })
        if result.get("status") == "error":
            return _error(result.get("message", "bp_list_pins failed"))
        return _ok(result)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def bp_wire_audio_param(
    asset_path: str,
    param_name: str,
    source_node_guid: str = "",
    source_pin: str = "",
) -> str:
    """High-level: wire a SetFloatParameter call into a Blueprint.

    Opens the Blueprint, optionally registers a source node,
    adds a SetFloatParameter call, sets the parameter name,
    connects the source if provided, and compiles.

    Args:
        asset_path: Blueprint asset path
        param_name: MetaSounds parameter name (e.g. "Speed", "Intensity")
        source_node_guid: Optional GUID of existing node to wire as value source
        source_pin: Output pin name on the source node for the float value
    """
    if not asset_path.strip():
        return _error("asset_path cannot be empty")
    if not param_name.strip():
        return _error("param_name cannot be empty")

    conn = get_ue5_connection()
    steps = []

    try:
        # 1. Open Blueprint
        result = conn.send_command({
            "action": "bp_open_blueprint",
            "asset_path": asset_path,
        })
        if result.get("status") == "error":
            return _error("Open failed: {}".format(result.get("message", "")))
        steps.append("opened")

        # 2. Register source node if provided
        if source_node_guid:
            result = conn.send_command({
                "action": "bp_register_existing_node",
                "id": "_source",
                "node_guid": source_node_guid,
            })
            if result.get("status") == "error":
                return _error("Register source failed: {}".format(result.get("message", "")))
            steps.append("registered_source")

        # 3. Add SetFloatParameter node
        result = conn.send_command({
            "action": "bp_add_node",
            "id": "_set_param",
            "node_kind": "CallFunction",
            "function_name": "SetFloatParameter",
            "position": [400, 200],
        })
        if result.get("status") == "error":
            return _error("Add node failed: {}".format(result.get("message", "")))
        steps.append("added_set_float_parameter")

        # 4. Set the parameter name
        result = conn.send_command({
            "action": "bp_set_pin_default",
            "node_id": "_set_param",
            "pin_name": "InName",
            "value": param_name,
        })
        if result.get("status") == "error":
            return _error("Set pin failed: {}".format(result.get("message", "")))
        steps.append("set_param_name")

        # 5. Connect source if provided
        if source_node_guid and source_pin:
            result = conn.send_command({
                "action": "bp_connect_pins",
                "from_node": "_source",
                "from_pin": source_pin,
                "to_node": "_set_param",
                "to_pin": "InFloat",
            })
            if result.get("status") == "error":
                return _error("Connect failed: {}".format(result.get("message", "")))
            steps.append("connected_source")

        # 6. Compile
        result = conn.send_command({"action": "bp_compile"})
        compile_ok = result.get("status") != "error"
        steps.append("compiled" if compile_ok else "compile_failed")

        return _ok({
            "message": "Wired SetFloatParameter('{}') into {}".format(param_name, asset_path),
            "steps": steps,
            "compile_result": result.get("compile_result", "unknown"),
        })

    except Exception as e:
        return _error("Wire failed at step {}: {}".format(len(steps), e))
