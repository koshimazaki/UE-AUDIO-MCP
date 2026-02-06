"""Template tools — generate complete game audio systems from parameters.

All templates wrap operations in undo groups for atomic rollback.
"""

from __future__ import annotations

import json
import logging

from ue_audio_mcp.connection import get_wwise_connection
from ue_audio_mcp.knowledge.wwise_types import DEFAULT_PATHS, EVENT_ACTION_TYPES
from ue_audio_mcp.server import mcp

log = logging.getLogger(__name__)


def _ok(data: dict | None = None) -> str:
    result = {"status": "ok"}
    if data:
        result.update(data)
    return json.dumps(result)


def _error(message: str) -> str:
    return json.dumps({"status": "error", "message": message})


def _begin_undo(conn, label: str) -> None:
    conn.call("ak.wwise.core.undo.beginGroup")


def _end_undo(conn) -> None:
    conn.call("ak.wwise.core.undo.endGroup", {
        "displayName": "MCP Template",
    })


def _cancel_undo(conn) -> None:
    try:
        conn.call("ak.wwise.core.undo.cancelGroup")
    except Exception:
        pass


def _create(conn, parent: str, obj_type: str, name: str) -> dict:
    return conn.call("ak.wwise.core.object.create", {
        "parent": parent,
        "type": obj_type,
        "name": name,
        "onNameConflict": "merge",
    })


def _set_prop(conn, obj_id: str, prop: str, value) -> None:
    conn.call("ak.wwise.core.object.setProperty", {
        "object": obj_id,
        "property": prop,
        "value": value,
    })


def _create_event(conn, name: str, target_id: str, action: str = "Play") -> dict:
    return conn.call("ak.wwise.core.object.create", {
        "parent": DEFAULT_PATHS["events"],
        "type": "Event",
        "name": name,
        "onNameConflict": "merge",
        "children": [{
            "type": "Action",
            "name": "",
            "@ActionType": EVENT_ACTION_TYPES[action],
            "@Target": target_id,
        }],
    })


@mcp.tool()
def template_gunshot(
    weapon_name: str = "Rifle",
    num_variations: int = 3,
    pitch_randomization: int = 100,
) -> str:
    """Create a complete gunshot system: RandomSequenceContainer + Sound children + Event.

    Args:
        weapon_name: Weapon name (used in object naming)
        num_variations: Number of sound variation slots to create
        pitch_randomization: Pitch randomization range in cents (stored as note)
    """
    if num_variations < 1 or num_variations > 50:
        return _error("num_variations must be between 1 and 50")

    conn = get_wwise_connection()
    parent = DEFAULT_PATHS["actor_mixer"]

    try:
        _begin_undo(conn, "Template: Gunshot")

        # Create RandomSequenceContainer
        container = _create(conn, parent, "RandomSequenceContainer", f"Gunshot_{weapon_name}")
        cid = container["id"]
        _set_prop(conn, cid, "RandomOrSequence", 0)
        _set_prop(conn, cid, "NormalOrShuffle", 1)

        # Create Sound children
        sound_ids = []
        for i in range(num_variations):
            sound = _create(conn, cid, "Sound", f"{weapon_name}_Shot_{i + 1:02d}")
            sound_ids.append(sound["id"])

        # Create Play event
        event = _create_event(conn, f"Play_Gunshot_{weapon_name}", cid)

        _end_undo(conn)

        return _ok({
            "template": "gunshot",
            "container_id": cid,
            "sound_ids": sound_ids,
            "event_id": event["id"],
            "weapon_name": weapon_name,
            "num_variations": num_variations,
            "pitch_randomization_cents": pitch_randomization,
        })
    except Exception as e:
        _cancel_undo(conn)
        return _error(str(e))


@mcp.tool()
def template_footsteps(
    surface_types: str = '["Concrete", "Wood", "Grass", "Metal", "Gravel", "Water"]',
    with_switch_group: bool = True,
) -> str:
    """Create a surface-switched footstep system: SwitchGroup + SwitchContainer + per-surface RandomSeq + Event.

    Args:
        surface_types: JSON array of surface type names
        with_switch_group: Create the SwitchGroup (set false if it already exists)
    """
    try:
        surfaces = json.loads(surface_types)
    except json.JSONDecodeError:
        return _error(f"Invalid surface_types JSON: {surface_types}")

    if not isinstance(surfaces, list) or not surfaces:
        return _error("surface_types must be a non-empty JSON array")

    conn = get_wwise_connection()
    parent = DEFAULT_PATHS["actor_mixer"]

    try:
        _begin_undo(conn, "Template: Footsteps")

        switch_ids = {}
        sg_id = None

        if with_switch_group:
            # Create SwitchGroup
            sg = _create(conn, DEFAULT_PATHS["switches"], "SwitchGroup", "Surface_Type")
            sg_id = sg["id"]

            # Create switch values
            for surface in surfaces:
                sw = _create(conn, sg_id, "Switch", surface)
                switch_ids[surface] = sw["id"]

        # Create SwitchContainer
        sc = _create(conn, parent, "SwitchContainer", "Footstep_Surface")
        sc_id = sc["id"]

        # Set switch group reference
        if sg_id:
            conn.call("ak.wwise.core.object.setReference", {
                "object": sc_id,
                "reference": "SwitchGroupOrStateGroup",
                "value": sg_id,
            })

        # Create per-surface RandomSequenceContainers and assign
        child_ids = {}
        for surface in surfaces:
            rc = _create(conn, sc_id, "RandomSequenceContainer", f"Footstep_{surface}")
            child_ids[surface] = rc["id"]

            if surface in switch_ids:
                conn.call("ak.wwise.core.switchContainer.addAssignment", {
                    "child": rc["id"],
                    "stateOrSwitch": switch_ids[surface],
                })

        # Create Play event
        event = _create_event(conn, "Play_Footstep", sc_id)

        _end_undo(conn)

        return _ok({
            "template": "footsteps",
            "switch_container_id": sc_id,
            "switch_group_id": sg_id,
            "surfaces": child_ids,
            "event_id": event["id"],
        })
    except Exception as e:
        _cancel_undo(conn)
        return _error(str(e))


@mcp.tool()
def template_ambient(
    layer_names: str = '["Wind_Light", "Wind_Medium", "Wind_Heavy"]',
    rtpc_parameter_name: str = "Wind_Intensity",
) -> str:
    """Create an RTPC-driven ambient blend system: GameParameter + BlendContainer + looped Sounds + Event.

    Args:
        layer_names: JSON array of layer/sound names
        rtpc_parameter_name: Name for the RTPC GameParameter
    """
    try:
        layers = json.loads(layer_names)
    except json.JSONDecodeError:
        return _error(f"Invalid layer_names JSON: {layer_names}")

    if not isinstance(layers, list) or not layers:
        return _error("layer_names must be a non-empty JSON array")

    conn = get_wwise_connection()
    parent = DEFAULT_PATHS["actor_mixer"]

    try:
        _begin_undo(conn, "Template: Ambient")

        # Create GameParameter
        gp = _create(conn, DEFAULT_PATHS["game_parameters"], "GameParameter", f"RTPC_{rtpc_parameter_name}")
        gp_id = gp["id"]

        # Create BlendContainer
        blend = _create(conn, parent, "BlendContainer", f"Ambient_{rtpc_parameter_name}")
        blend_id = blend["id"]

        # Create looped Sound children
        sound_ids = []
        for layer in layers:
            sound = _create(conn, blend_id, "Sound", layer)
            sid = sound["id"]
            _set_prop(conn, sid, "IsLoopingEnabled", True)
            _set_prop(conn, sid, "IsLoopingInfinite", True)
            sound_ids.append(sid)

        # Create Play event
        event = _create_event(conn, f"Play_Ambient_{rtpc_parameter_name}", blend_id)

        _end_undo(conn)

        return _ok({
            "template": "ambient",
            "blend_container_id": blend_id,
            "game_parameter_id": gp_id,
            "sound_ids": sound_ids,
            "event_id": event["id"],
            "rtpc_parameter": rtpc_parameter_name,
        })
    except Exception as e:
        _cancel_undo(conn)
        return _error(str(e))


@mcp.tool()
def template_ui_sound(
    sound_name: str = "Click",
    bus_path: str = "",
) -> str:
    """Create a non-spatial UI sound: ActorMixer(UI) + Sound + Event + bus routing.

    Args:
        sound_name: Name for the UI sound
        bus_path: Output bus path (default: Master Audio Bus)
    """
    conn = get_wwise_connection()
    parent = DEFAULT_PATHS["actor_mixer"]
    bus = bus_path or DEFAULT_PATHS["master_bus"]

    try:
        _begin_undo(conn, "Template: UI Sound")

        # Create UI ActorMixer
        ui_mixer = _create(conn, parent, "ActorMixer", "UI")
        ui_id = ui_mixer["id"]

        # Create Sound
        sound = _create(conn, ui_id, "Sound", f"UI_{sound_name}")
        sound_id = sound["id"]

        # Route to bus
        conn.call("ak.wwise.core.object.setReference", {
            "object": sound_id,
            "reference": "OutputBus",
            "value": bus,
        })

        # Create Play event
        event = _create_event(conn, f"Play_UI_{sound_name}", sound_id)

        _end_undo(conn)

        return _ok({
            "template": "ui_sound",
            "actor_mixer_id": ui_id,
            "sound_id": sound_id,
            "event_id": event["id"],
            "bus": bus,
        })
    except Exception as e:
        _cancel_undo(conn)
        return _error(str(e))


@mcp.tool()
def template_weather_states(
    weather_states: str = '["Clear", "Cloudy", "LightRain", "HeavyRain", "Storm", "Snow"]',
) -> str:
    """Create a state-driven weather ambient system: StateGroup + SwitchContainer + per-state Sounds + Event.

    Args:
        weather_states: JSON array of weather state names
    """
    try:
        states = json.loads(weather_states)
    except json.JSONDecodeError:
        return _error(f"Invalid weather_states JSON: {weather_states}")

    if not isinstance(states, list) or not states:
        return _error("weather_states must be a non-empty JSON array")

    conn = get_wwise_connection()
    parent = DEFAULT_PATHS["actor_mixer"]

    try:
        _begin_undo(conn, "Template: Weather States")

        # Create StateGroup
        sg = _create(conn, DEFAULT_PATHS["states"], "StateGroup", "Weather")
        sg_id = sg["id"]

        # Create state values
        state_ids = {}
        for state_name in states:
            s = _create(conn, sg_id, "State", state_name)
            state_ids[state_name] = s["id"]

        # Create SwitchContainer
        sc = _create(conn, parent, "SwitchContainer", "Ambience_Weather")
        sc_id = sc["id"]

        # Reference the StateGroup
        conn.call("ak.wwise.core.object.setReference", {
            "object": sc_id,
            "reference": "SwitchGroupOrStateGroup",
            "value": sg_id,
        })

        # Create per-state Sounds and assign
        sound_ids = {}
        for state_name in states:
            sound = _create(conn, sc_id, "Sound", f"Weather_{state_name}")
            sid = sound["id"]
            _set_prop(conn, sid, "IsLoopingEnabled", True)
            _set_prop(conn, sid, "IsLoopingInfinite", True)
            sound_ids[state_name] = sid

            conn.call("ak.wwise.core.switchContainer.addAssignment", {
                "child": sid,
                "stateOrSwitch": state_ids[state_name],
            })

        # Create Play event
        event = _create_event(conn, "Play_Weather_Ambience", sc_id)

        _end_undo(conn)

        return _ok({
            "template": "weather_states",
            "switch_container_id": sc_id,
            "state_group_id": sg_id,
            "states": state_ids,
            "sounds": sound_ids,
            "event_id": event["id"],
        })
    except Exception as e:
        _cancel_undo(conn)
        return _error(str(e))
