"""Event & mixing tools — create events, RTPC, switch assignment, attenuation."""

from __future__ import annotations

import json
import logging

from ue_audio_mcp.connection import get_wwise_connection
from ue_audio_mcp.knowledge.wwise_types import (
    CURVE_TYPES,
    DEFAULT_PATHS,
    EVENT_ACTION_TYPES,
)
from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _error, _ok

log = logging.getLogger(__name__)


@mcp.tool()
def wwise_create_event(
    name: str,
    target_path: str,
    action_type: str = "Play",
    event_parent: str = "",
) -> str:
    """Create a Wwise Event with an Action targeting an object.

    Args:
        name: Event name (e.g. Play_Gunshot_Rifle)
        target_path: Path to the target object the action acts on
        action_type: Action type name (Play, Stop, Pause, etc.)
        event_parent: Parent path for the event (default: Events\\Default Work Unit)
    """
    if action_type not in EVENT_ACTION_TYPES:
        return _error(
            f"Invalid action_type '{action_type}'. "
            f"Valid: {sorted(EVENT_ACTION_TYPES.keys())}"
        )

    parent = event_parent or DEFAULT_PATHS["events"]
    action_int = EVENT_ACTION_TYPES[action_type]

    conn = get_wwise_connection()
    try:
        result = conn.call("ak.wwise.core.object.create", {
            "parent": parent,
            "type": "Event",
            "name": name,
            "onNameConflict": "merge",
            "children": [
                {
                    "type": "Action",
                    "name": "",
                    "@ActionType": action_int,
                    "@Target": target_path,
                }
            ],
        })
        return _ok({"event_id": result.get("id"), "name": name, "action": action_type})
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def wwise_create_game_parameter(
    name: str,
    min_value: float = 0.0,
    max_value: float = 100.0,
    default_value: float = 50.0,
) -> str:
    """Create a Game Parameter (RTPC) in Wwise.

    Creates the GameParameter object. To bind it as an RTPC curve on a
    specific property, use execute_waapi with ak.wwise.core.object.setRTPCCurve
    or configure the binding in the Wwise Authoring GUI.

    Args:
        name: GameParameter name (e.g. RTPC_Wind_Intensity)
        min_value: Minimum range value
        max_value: Maximum range value
        default_value: Default value
    """
    if min_value >= max_value:
        return _error("min_value ({}) must be less than max_value ({})".format(min_value, max_value))
    if not (min_value <= default_value <= max_value):
        return _error("default_value ({}) must be between min_value ({}) and max_value ({})".format(
            default_value, min_value, max_value))

    conn = get_wwise_connection()
    try:
        conn.call("ak.wwise.core.undo.beginGroup")
        try:
            gp_result = conn.call("ak.wwise.core.object.create", {
                "parent": DEFAULT_PATHS["game_parameters"],
                "type": "GameParameter",
                "name": name,
                "onNameConflict": "merge",
            })
            gp_id = gp_result.get("id")

            # Set range properties
            conn.call("ak.wwise.core.object.setProperty", {
                "object": gp_id,
                "property": "RangeMin",
                "value": min_value,
            })
            conn.call("ak.wwise.core.object.setProperty", {
                "object": gp_id,
                "property": "RangeMax",
                "value": max_value,
            })
            conn.call("ak.wwise.core.object.setProperty", {
                "object": gp_id,
                "property": "InitialValue",
                "value": default_value,
            })
        finally:
            conn.call("ak.wwise.core.undo.endGroup", {
                "displayName": "Create GameParameter: {}".format(name),
            })

        return _ok({
            "game_parameter_id": gp_id,
            "name": name,
            "range": [min_value, max_value],
            "default": default_value,
        })
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def wwise_assign_switch(
    switch_container_path: str,
    child_path: str,
    switch_value: str,
) -> str:
    """Assign a child object to a switch/state value in a SwitchContainer.

    Args:
        switch_container_path: Path to the SwitchContainer (for context only)
        child_path: GUID or path of the child to assign
        switch_value: GUID or path of the switch/state value
    """
    conn = get_wwise_connection()
    try:
        conn.call("ak.wwise.core.switchContainer.addAssignment", {
            "child": child_path,
            "stateOrSwitch": switch_value,
        })
        return _ok({
            "container": switch_container_path,
            "child": child_path,
            "switch_value": switch_value,
        })
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def wwise_set_attenuation(
    name: str,
    curve_type: str,
    curve_points: str,
    parent_path: str = "",
) -> str:
    """Create an Attenuation ShareSet and set its distance curve.

    Args:
        name: Attenuation name
        curve_type: Curve type (VolumeDryUsage, LowPassFilterUsage, etc.)
        curve_points: JSON array of {x, y, shape} points
        parent_path: Parent path (default: Attenuations\\Default Work Unit)
    """
    if curve_type not in CURVE_TYPES:
        return _error(
            f"Invalid curve_type '{curve_type}'. Valid: {sorted(CURVE_TYPES)}"
        )

    try:
        points = json.loads(curve_points)
    except json.JSONDecodeError:
        return _error(f"Invalid curve_points JSON: {curve_points}")

    if not isinstance(points, list) or len(points) < 2:
        return _error("curve_points must be a JSON array with at least 2 points")

    parent = parent_path or DEFAULT_PATHS["attenuations"]

    conn = get_wwise_connection()
    try:
        # Create the Attenuation ShareSet
        att_result = conn.call("ak.wwise.core.object.create", {
            "parent": parent,
            "type": "Attenuation",
            "name": name,
            "onNameConflict": "merge",
        })
        att_id = att_result.get("id")

        # Set the curve
        conn.call("ak.wwise.core.object.setAttenuationCurve", {
            "object": att_id,
            "curveType": curve_type,
            "use": "Custom",
            "points": points,
        })

        return _ok({"attenuation_id": att_id, "name": name, "curve_type": curve_type})
    except Exception as e:
        return _error(str(e))
