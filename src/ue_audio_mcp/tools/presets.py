"""Preset swap, morph, and macro trigger tools.

3 high-level tools for creative sound design:
  - ms_preset_swap: Create a preset variant from an existing MetaSound
  - ms_preset_morph: Build a MetaSound that interpolates between two param sets
  - ms_macro_trigger: Execute a named sequence of param changes
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _error, _ok
from ue_audio_mcp.ue5_connection import get_ue5_connection

log = logging.getLogger(__name__)


def _is_connected() -> bool:
    """Check if UE5 plugin is connected."""
    conn = get_ue5_connection()
    return conn.is_connected()


def _send(cmd: dict) -> dict:
    """Send a command to UE5 plugin."""
    conn = get_ue5_connection()
    return conn.send_command(cmd)


@mcp.tool()
def ms_preset_swap(
    preset_name: str,
    referenced_asset: str,
    overrides_json: str = "{}",
    asset_path: str = "/Game/Audio/Generated/",
) -> str:
    """Create a preset variant from an existing MetaSound asset.

    A preset shares the referenced asset's graph topology but overrides
    specific input defaults. Use this to create weapon/surface/character
    variants without duplicating the graph.

    Args:
        preset_name: Name for the new preset asset
        referenced_asset: Content path of the source MetaSound to reference
        overrides_json: JSON object of input_name -> value overrides
        asset_path: Content path for the output asset
    """
    try:
        overrides = json.loads(overrides_json)
    except (json.JSONDecodeError, ValueError):
        return _error("Invalid overrides_json — must be valid JSON object")

    if not isinstance(overrides, dict):
        return _error("overrides_json must be a JSON object")

    if not asset_path.startswith("/Game/"):
        return _error("asset_path must start with /Game/")

    # Build command sequence
    commands: list[dict[str, Any]] = [
        {"action": "create_builder", "asset_type": "Preset", "name": preset_name},
        {"action": "convert_to_preset", "referenced_asset": referenced_asset},
    ]

    # Apply overrides as defaults on the preset's exposed inputs
    for input_name, value in overrides.items():
        commands.append({
            "action": "set_default",
            "node_id": "__graph__",
            "input": input_name,
            "value": value,
        })

    commands.append({
        "action": "build_to_asset",
        "name": preset_name,
        "path": asset_path,
    })

    if not _is_connected():
        return _ok({
            "message": "Preset swap planned (offline mode)",
            "mode": "planned",
            "preset_name": preset_name,
            "referenced_asset": referenced_asset,
            "overrides": overrides,
            "command_count": len(commands),
            "commands": commands,
        })

    # Execute
    results = []
    for i, cmd in enumerate(commands):
        try:
            result = _send(cmd)
            results.append(result)
        except Exception as e:
            return _error("Command {} ({}) failed: {}".format(
                i + 1, cmd.get("action", "?"), e
            ))

    return _ok({
        "message": "Created preset '{}' from '{}'".format(preset_name, referenced_asset),
        "mode": "executed",
        "preset_name": preset_name,
        "referenced_asset": referenced_asset,
        "overrides": overrides,
        "command_count": len(commands),
        "results": results,
    })


@mcp.tool()
def ms_preset_morph(
    name: str,
    param_set_a_json: str,
    param_set_b_json: str,
    asset_path: str = "/Game/Audio/Generated/",
) -> str:
    """Build a MetaSound Source that morphs between two parameter sets.

    Creates a Source with a Morph input (0.0-1.0) that smoothly
    interpolates each parameter between set A (Morph=0) and set B (Morph=1).
    Uses Map Range nodes for each parameter and InterpTo for smooth transitions.

    Args:
        name: Name for the morph MetaSound asset
        param_set_a_json: JSON object of param_name -> value at Morph=0
        param_set_b_json: JSON object of param_name -> value at Morph=1
        asset_path: Content path for the output asset
    """
    try:
        set_a = json.loads(param_set_a_json)
        set_b = json.loads(param_set_b_json)
    except (json.JSONDecodeError, ValueError):
        return _error("Invalid JSON in param_set_a_json or param_set_b_json")

    if not isinstance(set_a, dict) or not isinstance(set_b, dict):
        return _error("Both param sets must be JSON objects")

    # Params must match
    if set(set_a.keys()) != set(set_b.keys()):
        return _error("param_set_a and param_set_b must have the same keys. "
                       "A has: {}, B has: {}".format(
                           sorted(set_a.keys()), sorted(set_b.keys())))

    if not set_a:
        return _error("At least one parameter required for morphing")

    if not asset_path.startswith("/Game/"):
        return _error("asset_path must start with /Game/")

    # Build graph spec for the morph MetaSound
    commands: list[dict[str, Any]] = [
        {"action": "create_builder", "asset_type": "Source", "name": name},
        {"action": "add_interface", "interface": "UE.Source.Looping"},
        {"action": "add_graph_input", "name": "Morph", "type": "Float", "default": "0.0"},
    ]

    # Add graph inputs for each morphable parameter
    for param_name in sorted(set_a.keys()):
        commands.append({
            "action": "add_graph_input",
            "name": param_name,
            "type": "Float",
            "default": str(set_a[param_name]),
        })

    # Add Map Range + InterpTo nodes per parameter
    node_id = 0
    morph_outputs: dict[str, str] = {}  # param_name -> interp node id

    for param_name in sorted(set_a.keys()):
        map_id = "map_{}".format(node_id)
        interp_id = "interp_{}".format(node_id)

        # Map Range: Morph (0-1) -> param value (A-B)
        commands.append({
            "action": "add_node", "id": map_id,
            "node_type": "Map Range", "position": [200, node_id * 200],
        })
        commands.append({"action": "set_default", "node_id": map_id, "input": "In Range A", "value": 0.0})
        commands.append({"action": "set_default", "node_id": map_id, "input": "In Range B", "value": 1.0})
        commands.append({"action": "set_default", "node_id": map_id, "input": "Out Range A", "value": float(set_a[param_name])})
        commands.append({"action": "set_default", "node_id": map_id, "input": "Out Range B", "value": float(set_b[param_name])})

        # InterpTo: smooth the mapped value
        commands.append({
            "action": "add_node", "id": interp_id,
            "node_type": "InterpTo", "position": [500, node_id * 200],
        })
        commands.append({"action": "set_default", "node_id": interp_id, "input": "Interp Time", "value": 5.0})

        # Wire: Morph -> Map Range -> InterpTo
        commands.append({"action": "connect", "from_node": "__graph__", "from_pin": "Morph", "to_node": map_id, "to_pin": "In"})
        commands.append({"action": "connect", "from_node": map_id, "from_pin": "Out Value", "to_node": interp_id, "to_pin": "Target"})

        morph_outputs[param_name] = interp_id
        node_id += 1

    commands.append({"action": "build_to_asset", "name": name, "path": asset_path})

    if not _is_connected():
        return _ok({
            "message": "Preset morph planned (offline mode)",
            "mode": "planned",
            "name": name,
            "param_set_a": set_a,
            "param_set_b": set_b,
            "morph_params": sorted(set_a.keys()),
            "command_count": len(commands),
            "commands": commands,
        })

    # Execute
    results = []
    for i, cmd in enumerate(commands):
        try:
            result = _send(cmd)
            results.append(result)
        except Exception as e:
            return _error("Command {} ({}) failed: {}".format(
                i + 1, cmd.get("action", "?"), e
            ))

    return _ok({
        "message": "Built morph MetaSound '{}' with {} parameters".format(name, len(set_a)),
        "mode": "executed",
        "name": name,
        "morph_params": sorted(set_a.keys()),
        "command_count": len(commands),
        "results": results,
    })


@mcp.tool()
def ms_macro_trigger(
    name: str,
    steps_json: str,
) -> str:
    """Execute a named sequence of parameter changes and/or preset swaps.

    Each step is a dict with:
      - "action": "set_default" or "convert_to_preset"
      - Plus action-specific fields (node_id/input/value or referenced_asset)

    Useful for cinematic audio cues, dynamic music transitions, and
    scripted sound design sequences.

    Args:
        name: Descriptive name for this macro sequence
        steps_json: JSON array of step dicts
    """
    try:
        steps = json.loads(steps_json)
    except (json.JSONDecodeError, ValueError):
        return _error("Invalid steps_json — must be valid JSON array")

    if not isinstance(steps, list):
        return _error("steps_json must be a JSON array")

    if not steps:
        return _error("At least one step is required")

    ALLOWED_ACTIONS = {"set_default", "convert_to_preset", "convert_from_preset"}

    # Validate steps
    commands: list[dict[str, Any]] = []
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            return _error("Step {} must be a JSON object".format(i + 1))

        action = step.get("action", "")
        if action not in ALLOWED_ACTIONS:
            return _error("Step {}: invalid action '{}'. Must be one of: {}".format(
                i + 1, action, ", ".join(sorted(ALLOWED_ACTIONS))
            ))

        commands.append(step)

    if not _is_connected():
        return _ok({
            "message": "Macro '{}' planned (offline mode)".format(name),
            "mode": "planned",
            "name": name,
            "step_count": len(commands),
            "commands": commands,
        })

    # Execute
    results = []
    for i, cmd in enumerate(commands):
        try:
            result = _send(cmd)
            results.append(result)
        except Exception as e:
            return _error("Step {} ({}) failed: {}".format(
                i + 1, cmd.get("action", "?"), e
            ))

    return _ok({
        "message": "Macro '{}' executed ({} steps)".format(name, len(commands)),
        "mode": "executed",
        "name": name,
        "step_count": len(commands),
        "results": results,
    })
