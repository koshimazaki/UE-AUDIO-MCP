"""MCP tools for MetaSounds graph spec operations.

3 tools: ms_validate_graph, ms_graph_to_commands, ms_graph_from_template.
"""

from __future__ import annotations

import json
import os

from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _ok, _error


@mcp.tool()
def ms_validate_graph(graph_spec: str) -> str:
    """Validate a MetaSounds graph specification.

    Checks node types exist, pin names are valid, type compatibility,
    required inputs are connected, no duplicate IDs.

    Args:
        graph_spec: JSON string of the graph specification

    Returns:
        JSON with validation result: errors list (empty = valid).
    """
    try:
        spec = json.loads(graph_spec)
    except (json.JSONDecodeError, ValueError):
        return _error("Invalid graph_spec JSON")

    from ue_audio_mcp.knowledge.graph_schema import validate_graph
    errors = validate_graph(spec)

    if errors:
        return _ok({"valid": False, "error_count": len(errors), "errors": errors})
    return _ok({"valid": True, "error_count": 0, "errors": []})


@mcp.tool()
def ms_graph_to_commands(graph_spec: str) -> str:
    """Convert a validated graph spec to Builder API command sequence.

    The command sequence can be sent to the UE5 plugin (Phase 3) to
    construct the MetaSound asset via the Builder API.

    Args:
        graph_spec: JSON string of a valid graph specification

    Returns:
        JSON with ordered command list for the Builder API.
    """
    try:
        spec = json.loads(graph_spec)
    except (json.JSONDecodeError, ValueError):
        return _error("Invalid graph_spec JSON")

    from ue_audio_mcp.knowledge.graph_schema import validate_graph, graph_to_builder_commands
    errors = validate_graph(spec)
    if errors:
        return _error("Graph has {} validation error(s): {}".format(
            len(errors), "; ".join(errors[:3])
        ))

    commands = graph_to_builder_commands(spec)
    return _ok({"command_count": len(commands), "commands": commands})


@mcp.tool()
def ms_graph_from_template(
    template_name: str,
    params: str = "{}",
) -> str:
    """Generate a complete graph spec from a template.

    Available templates: gunshot, footsteps, ambient, spatial, ui_sound, weather, vehicle_engine, sfx_generator.

    Args:
        template_name: Template name (e.g. "gunshot", "footsteps")
        params: JSON string of template parameters (overrides defaults)

    Returns:
        JSON with the complete graph specification ready for validation.
    """
    valid_templates = {"gunshot", "footsteps", "ambient", "spatial", "ui_sound", "weather", "vehicle_engine", "sfx_generator"}
    if template_name not in valid_templates:
        return _error("Unknown template '{}'. Available: {}".format(
            template_name, ", ".join(sorted(valid_templates))
        ))

    try:
        param_dict = json.loads(params)
    except (json.JSONDecodeError, ValueError):
        return _error("Invalid params JSON")

    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "templates", "metasounds",
    )
    template_path = os.path.join(template_dir, "{}.json".format(template_name))

    if not os.path.isfile(template_path):
        return _error("Template file not found: {}".format(template_name))

    with open(template_path) as f:
        spec = json.load(f)

    # Apply JSON-level param overrides: {"node_id.input_name": value}
    if param_dict:
        node_map = {n["id"]: n for n in spec.get("nodes", [])}
        for key, value in param_dict.items():
            parts = key.split(".", 1)
            if len(parts) != 2:
                continue
            node_id, input_name = parts
            node = node_map.get(node_id)
            if node is None:
                continue
            node.setdefault("defaults", {})[input_name] = value

    from ue_audio_mcp.knowledge.graph_schema import validate_graph
    errors = validate_graph(spec)

    return _ok({
        "template": template_name,
        "graph_spec": spec,
        "valid": len(errors) == 0,
        "validation_errors": errors,
    })
