"""GraphSpec schema for MetaSounds -- defines, validates, and transforms graphs.

A GraphSpec is a plain dict describing a complete MetaSound graph:
nodes, connections, graph-level inputs/outputs, and interfaces.
``validate_graph`` checks structural and semantic correctness.
``graph_to_builder_commands`` converts a valid spec into a sequential list
of Builder API commands the UE5 C++ plugin can execute.

All validation is against the canonical catalogues in
``metasound_data_types`` and ``metasound_nodes``.
"""

from __future__ import annotations

from typing import Any

from ue_audio_mcp.knowledge.metasound_data_types import (
    ASSET_TYPES,
    INTERFACES,
    PIN_COMPATIBILITY,
    PIN_TYPES,
)
from ue_audio_mcp.knowledge.metasound_nodes import METASOUND_NODES

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

#: Top-level fields that MUST be present in every GraphSpec.
GRAPH_SPEC_FIELDS: set[str] = {"name", "asset_type", "nodes", "connections"}

#: Sentinel node ID representing the graph boundary (inputs/outputs).
GRAPH_BOUNDARY: str = "__graph__"

#: Special node types for graph variable access (skip METASOUND_NODES lookup).
VARIABLE_GET_TYPE: str = "__variable_get__"
VARIABLE_SET_TYPE: str = "__variable_set__"
VARIABLE_GET_DELAYED_TYPE: str = "__variable_get_delayed__"
_VARIABLE_NODE_TYPES: set[str] = {VARIABLE_GET_TYPE, VARIABLE_SET_TYPE, VARIABLE_GET_DELAYED_TYPE}

#: Default output path for generated assets.
DEFAULT_ASSET_PATH: str = "/Game/Audio/Generated/"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_graph(spec: dict[str, Any]) -> list[str]:
    """Validate a GraphSpec dict and return a list of error strings.

    An empty list means the spec is valid.  Errors are accumulated so the
    caller sees *all* problems in one pass rather than fixing them one at a
    time.
    """
    errors: list[str] = []

    # -- 1. Required top-level fields ---------------------------------------
    missing = GRAPH_SPEC_FIELDS - set(spec.keys())
    if missing:
        errors.append(f"Missing required top-level fields: {sorted(missing)}")
        # If critical fields are missing we can't continue meaningfully
        return errors

    # -- 2. Asset type -------------------------------------------------------
    asset_type = spec["asset_type"]
    if asset_type not in ASSET_TYPES:
        errors.append(
            f"Invalid asset_type '{asset_type}'. "
            f"Must be one of: {sorted(ASSET_TYPES)}"
        )

    # -- 3. Interfaces -------------------------------------------------------
    interfaces: list[str] = spec.get("interfaces", [])
    for iface in interfaces:
        if iface not in INTERFACES:
            errors.append(
                f"Unknown interface '{iface}'. "
                f"Valid interfaces: {sorted(INTERFACES)}"
            )

    # -- 3b. Variables (optional) --------------------------------------------
    variables: list[dict] = spec.get("variables", [])
    variable_names: set[str] = set()
    for var in variables:
        vname = var.get("name", "<missing>")
        vtype = var.get("type", "<missing>")
        if vname in variable_names:
            errors.append(f"Duplicate variable name: '{vname}'")
        variable_names.add(vname)
        if vtype not in PIN_TYPES:
            errors.append(
                f"Variable '{vname}' has invalid type '{vtype}'. "
                f"Must be one of: {sorted(PIN_TYPES)}"
            )

    # -- 4. Node definitions -------------------------------------------------
    nodes: list[dict] = spec["nodes"]
    node_map: dict[str, dict] = {}  # id -> node spec
    seen_ids: set[str] = set()

    for node in nodes:
        nid = node.get("id", "<missing>")

        # Duplicate IDs
        if nid in seen_ids:
            errors.append(f"Duplicate node ID: '{nid}'")
        seen_ids.add(nid)

        # Node type existence — variable node types skip METASOUND_NODES lookup
        ntype = node.get("node_type", "<missing>")
        if ntype in _VARIABLE_NODE_TYPES:
            # Validate that variable_name references a declared variable
            var_name = node.get("variable_name", "")
            if var_name and var_name not in variable_names:
                errors.append(
                    f"Node '{nid}' references undeclared variable '{var_name}'. "
                    f"Declared variables: {sorted(variable_names)}"
                )
            node_map[nid] = node
        elif ntype not in METASOUND_NODES:
            errors.append(
                f"Node '{nid}' references unknown node_type '{ntype}'"
            )
        else:
            node_map[nid] = node

    # Build lookup structures for pin resolution
    def _resolve_variable_type(var_name: str) -> str | None:
        """Return the declared type for a variable, or None."""
        for var in variables:
            if var["name"] == var_name:
                return var.get("type")
        return None

    def _resolve_output_pin(node_id: str, pin_name: str) -> str | None:
        """Return the pin type for an output, or None if not found."""
        if node_id == GRAPH_BOUNDARY:
            # Graph-level inputs act as outputs (they feed *into* the graph)
            for pin in spec.get("inputs", []):
                if pin["name"] == pin_name:
                    return pin["type"]
            return None
        node_spec = node_map.get(node_id)
        if node_spec is None:
            return None
        ntype = node_spec.get("node_type", "")
        # Variable get nodes output the variable's type
        if ntype in (VARIABLE_GET_TYPE, VARIABLE_GET_DELAYED_TYPE):
            var_name = node_spec.get("variable_name", "")
            return _resolve_variable_type(var_name)
        node_def = METASOUND_NODES.get(ntype)
        if node_def is None:
            return None
        for pin in node_def["outputs"]:
            if pin["name"] == pin_name:
                return pin["type"]
        return None

    def _resolve_input_pin(node_id: str, pin_name: str) -> str | None:
        """Return the pin type for an input, or None if not found."""
        if node_id == GRAPH_BOUNDARY:
            # Graph-level outputs act as inputs (they receive from the graph)
            for pin in spec.get("outputs", []):
                if pin["name"] == pin_name:
                    return pin["type"]
            return None
        node_spec = node_map.get(node_id)
        if node_spec is None:
            return None
        ntype = node_spec.get("node_type", "")
        # Variable set nodes accept Value (variable's type) and Execute (Trigger)
        if ntype == VARIABLE_SET_TYPE:
            var_name = node_spec.get("variable_name", "")
            if pin_name == "Execute":
                return "Trigger"
            if pin_name == "Value":
                return _resolve_variable_type(var_name)
            return None
        node_def = METASOUND_NODES.get(ntype)
        if node_def is None:
            return None
        for pin in node_def["inputs"]:
            if pin["name"] == pin_name:
                return pin["type"]
        return None

    # -- 5. Connections ------------------------------------------------------
    connections: list[dict] = spec["connections"]
    connected_inputs: set[tuple[str, str]] = set()  # (node_id, pin_name)

    for conn in connections:
        from_node = conn.get("from_node", "<missing>")
        from_pin = conn.get("from_pin", "<missing>")
        to_node = conn.get("to_node", "<missing>")
        to_pin = conn.get("to_pin", "<missing>")

        # Validate source node exists
        if from_node != GRAPH_BOUNDARY and from_node not in seen_ids:
            errors.append(
                f"Connection from_node '{from_node}' does not exist"
            )
            continue

        # Validate destination node exists
        if to_node != GRAPH_BOUNDARY and to_node not in seen_ids:
            errors.append(
                f"Connection to_node '{to_node}' does not exist"
            )
            continue

        # Validate pins exist
        from_type = _resolve_output_pin(from_node, from_pin)
        if from_type is None:
            errors.append(
                f"Output pin '{from_pin}' not found on node '{from_node}'"
            )

        to_type = _resolve_input_pin(to_node, to_pin)
        if to_type is None:
            errors.append(
                f"Input pin '{to_pin}' not found on node '{to_node}'"
            )

        # Pin type compatibility
        if from_type is not None and to_type is not None:
            compatible_targets = PIN_COMPATIBILITY.get(from_type, set())
            if to_type not in compatible_targets:
                errors.append(
                    f"Type mismatch: '{from_node}.{from_pin}' outputs "
                    f"'{from_type}' but '{to_node}.{to_pin}' expects "
                    f"'{to_type}' (compatible targets for '{from_type}': "
                    f"{sorted(compatible_targets)})"
                )

        # Track which inputs are connected
        connected_inputs.add((to_node, to_pin))

    # -- 5b. Default pin names must match node inputs -------------------------
    for node in nodes:
        nid = node.get("id", "<missing>")
        ntype = node.get("node_type", "")
        if ntype in _VARIABLE_NODE_TYPES:
            continue
        node_def = METASOUND_NODES.get(ntype)
        if node_def is None:
            continue
        valid_input_names = {p["name"] for p in node_def["inputs"]}
        for default_key in node.get("defaults", {}):
            if default_key not in valid_input_names:
                errors.append(
                    f"Node '{nid}' ({ntype}): default key "
                    f"'{default_key}' does not match any input pin. "
                    f"Valid inputs: {sorted(valid_input_names)}"
                )

    # -- 6. Required inputs must be connected --------------------------------
    for node in nodes:
        nid = node.get("id", "<missing>")
        ntype = node.get("node_type", "")
        # Variable nodes have dynamic pins — skip required-input check
        if ntype in _VARIABLE_NODE_TYPES:
            continue
        node_def = METASOUND_NODES.get(ntype)
        if node_def is None:
            continue  # already reported in step 4

        defaults = node.get("defaults", {})
        for input_pin in node_def["inputs"]:
            if not input_pin.get("required", False):
                continue
            pin_name = input_pin["name"]
            is_connected = (nid, pin_name) in connected_inputs
            has_default = pin_name in defaults or "default" in input_pin
            if not is_connected and not has_default:
                errors.append(
                    f"Node '{nid}' ({ntype}): required input "
                    f"'{pin_name}' is neither connected nor has a default"
                )

    # -- 7. Interface pins present as graph I/O ------------------------------
    graph_input_names = {p["name"] for p in spec.get("inputs", [])}
    graph_output_names = {p["name"] for p in spec.get("outputs", [])}

    for iface_name in interfaces:
        iface_def = INTERFACES.get(iface_name)
        if iface_def is None:
            continue  # already reported in step 3

        for pin in iface_def.get("inputs", []):
            if pin["name"] not in graph_input_names:
                errors.append(
                    f"Interface '{iface_name}' requires graph input "
                    f"'{pin['name']}' but it is missing"
                )

        for pin in iface_def.get("outputs", []):
            if pin["name"] not in graph_output_names:
                errors.append(
                    f"Interface '{iface_name}' requires graph output "
                    f"'{pin['name']}' but it is missing"
                )

    return errors


# ---------------------------------------------------------------------------
# Builder command generation
# ---------------------------------------------------------------------------

def graph_to_builder_commands(
    spec: dict[str, Any],
    *,
    asset_path: str = DEFAULT_ASSET_PATH,
) -> list[dict[str, Any]]:
    """Convert a validated GraphSpec into a sequence of Builder API commands.

    The caller is responsible for calling ``validate_graph`` first.
    This function assumes the spec is valid and produces commands in the
    correct dependency order:

        1. create_builder
        2. add_interface  (one per interface)
        3. add_graph_input / add_graph_output  (graph-level I/O)
        4. add_node  (one per node)
        5. set_default  (one per non-None default on each node)
        6. connect  (one per connection)
        7. build_to_asset

    Parameters
    ----------
    spec : dict
        A valid GraphSpec dict.
    asset_path : str
        UE content path where the asset will be saved.

    Returns
    -------
    list[dict]
        Ordered list of command dicts, each with an ``"action"`` key.
    """
    commands: list[dict[str, Any]] = []
    name = spec["name"]

    # 1. Create builder
    commands.append({
        "action": "create_builder",
        "asset_type": spec["asset_type"],
        "name": name,
    })

    # 2. Interfaces
    for iface in spec.get("interfaces", []):
        commands.append({
            "action": "add_interface",
            "interface": iface,
        })

    # 2b. Graph variables (between interfaces and graph I/O)
    for var in spec.get("variables", []):
        var_cmd: dict[str, Any] = {
            "action": "add_graph_variable",
            "name": var["name"],
            "type": var["type"],
        }
        if "default" in var:
            var_cmd["default"] = var["default"]
        commands.append(var_cmd)

    # 3. Graph-level inputs
    for pin in spec.get("inputs", []):
        cmd: dict[str, Any] = {
            "action": "add_graph_input",
            "name": pin["name"],
            "type": pin["type"],
        }
        if "default" in pin:
            cmd["default"] = pin["default"]
        commands.append(cmd)

    # 4. Graph-level outputs
    for pin in spec.get("outputs", []):
        commands.append({
            "action": "add_graph_output",
            "name": pin["name"],
            "type": pin["type"],
        })

    # 5. Nodes (variable nodes emit special commands)
    for node in spec["nodes"]:
        ntype = node["node_type"]
        if ntype == VARIABLE_GET_TYPE:
            commands.append({
                "action": "add_variable_get_node",
                "id": node["id"],
                "variable_name": node["variable_name"],
            })
        elif ntype == VARIABLE_GET_DELAYED_TYPE:
            commands.append({
                "action": "add_variable_get_node",
                "id": node["id"],
                "variable_name": node["variable_name"],
                "delayed": True,
            })
        elif ntype == VARIABLE_SET_TYPE:
            commands.append({
                "action": "add_variable_set_node",
                "id": node["id"],
                "variable_name": node["variable_name"],
            })
        else:
            commands.append({
                "action": "add_node",
                "id": node["id"],
                "node_type": ntype,
                "position": node.get("position", [0, 0]),
            })

    # 6. Defaults (skip variable nodes — they have no user-settable defaults)
    for node in spec["nodes"]:
        if node["node_type"] in _VARIABLE_NODE_TYPES:
            continue
        defaults = node.get("defaults", {})
        for input_name, value in defaults.items():
            commands.append({
                "action": "set_default",
                "node_id": node["id"],
                "input": input_name,
                "value": value,
            })

    # 7. Connections
    for conn in spec["connections"]:
        commands.append({
            "action": "connect",
            "from_node": conn["from_node"],
            "from_pin": conn["from_pin"],
            "to_node": conn["to_node"],
            "to_pin": conn["to_pin"],
        })

    # 8. Build to asset
    commands.append({
        "action": "build_to_asset",
        "name": name,
        "path": asset_path,
    })

    return commands
