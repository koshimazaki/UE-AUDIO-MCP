"""Template tools — generate complete game audio systems from parameters.

All templates wrap operations in undo groups for atomic rollback.
"""

from __future__ import annotations

import json
import logging

from ue_audio_mcp.connection import get_wwise_connection
from ue_audio_mcp.knowledge.wwise_types import DEFAULT_PATHS, EVENT_ACTION_TYPES
from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _error, _ok

log = logging.getLogger(__name__)


def _begin_undo(conn, label: str) -> None:
    conn.call("ak.wwise.core.undo.beginGroup")
    conn._undo_label = label


def _end_undo(conn) -> None:
    label = getattr(conn, "_undo_label", "MCP Template")
    conn.call("ak.wwise.core.undo.endGroup", {
        "displayName": label,
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


# ---------------------------------------------------------------------------
# AAA project structure definition
# ---------------------------------------------------------------------------

AAA_BUS_STRUCTURE: dict = {
    "AmbientMaster": {
        "type": "Bus",
        "children": {
            "2DAmbience": {"type": "Bus"},
            "3DAmbience": {"type": "Bus"},
            "AmbientBeds": {
                "type": "Bus",
                "children": {
                    "2DAmbientBeds": {"type": "Bus"},
                },
            },
        },
    },
    "NPCMaster": {
        "type": "Bus",
        "children": {
            "NPCFootsteps": {"type": "Bus"},
            "NPCVoice": {"type": "Bus"},
        },
    },
    "PlayerMaster": {
        "type": "Bus",
        "children": {
            "PlayerLocomotion": {
                "type": "Bus",
                "children": {
                    "PlayerFootsteps": {"type": "Bus"},
                },
            },
            "PlayerWeapons": {"type": "Bus"},
        },
    },
    "UIMaster": {
        "type": "Bus",
    },
    "MusicMaster": {
        "type": "Bus",
    },
    "Reverbs": {
        "type": "AuxBus",
        "children": {
            "LargeRoom": {"type": "AuxBus"},
            "SmallRoom": {"type": "AuxBus"},
            "Cave": {"type": "AuxBus"},
            "Outdoor": {"type": "AuxBus"},
        },
    },
}

AAA_ACTOR_WORK_UNITS: list[str] = [
    "Player_Locomotion",
    "Player_Weapons",
    "NPC_Locomotion",
    "NPC_Voice",
    "Ambience",
    "UI",
    "Music",
]

AAA_EVENT_WORK_UNITS: list[str] = [
    "Player",
    "NPC",
    "Locomotion",
    "Ambience",
    "UI",
    "Music",
]

AAA_SWITCH_GROUPS: dict[str, list[str]] = {
    "Surface_Type": ["Concrete", "Wood", "Grass", "Metal", "Gravel", "Water", "Sand", "Snow"],
    "Footstep_Type": ["Walk", "Run", "Sprint", "Land", "Jump"],
}

AAA_STATE_GROUPS: dict[str, list[str]] = {
    "Weather": ["Clear", "Cloudy", "LightRain", "HeavyRain", "Storm", "Snow"],
    "PlayerState": ["Alive", "Dead", "Paused", "InMenu"],
    "Zone": ["Interior", "Exterior", "Underwater", "Cave"],
}


def _create_bus_tree(conn, parent_path: str, tree: dict, created: dict) -> None:
    """Recursively create a bus hierarchy from a nested dict."""
    for name, spec in tree.items():
        obj_type = spec.get("type", "Bus")
        bus = _create(conn, parent_path, obj_type, name)
        bus_id = bus["id"]
        created[name] = {"id": bus_id, "type": obj_type}
        children = spec.get("children")
        if children:
            _create_bus_tree(conn, bus_id, children, created)


@mcp.tool()
def template_aaa_setup(
    bus_structure: str = "",
    actor_work_units: str = "",
    event_work_units: str = "",
    switch_groups: str = "",
    state_groups: str = "",
    include_reverbs: bool = True,
) -> str:
    """Create a complete AAA Wwise project structure (Bjorn Jacobson method).

    Creates separate Work Units for merge-safe version control, structured bus
    hierarchy for clear signal routing, and switch/state groups for runtime control.

    Naming convention: Type_Owner_Category_Action_Material_Variation
    Example: sfx_plyr_loc_walking_dirt_01

    Everything goes into dedicated Work Units — nothing in Default Work Unit.

    Args:
        bus_structure: JSON override for bus tree (default: AAA standard with
            AmbientMaster, NPCMaster, PlayerMaster, UIMaster, MusicMaster, Reverbs)
        actor_work_units: JSON array of Actor-Mixer Work Unit names
            (default: Player_Locomotion, Player_Weapons, NPC_Locomotion, NPC_Voice,
            Ambience, UI, Music)
        event_work_units: JSON array of Event Work Unit names
            (default: Player, NPC, Locomotion, Ambience, UI, Music)
        switch_groups: JSON dict of SwitchGroup name -> values array
            (default: Surface_Type, Footstep_Type)
        state_groups: JSON dict of StateGroup name -> values array
            (default: Weather, PlayerState, Zone)
        include_reverbs: Create Reverb AuxBuses (LargeRoom, SmallRoom, Cave, Outdoor)
    """
    # Parse overrides or use defaults
    try:
        buses = json.loads(bus_structure) if bus_structure else AAA_BUS_STRUCTURE
    except json.JSONDecodeError:
        return _error(f"Invalid bus_structure JSON: {bus_structure}")

    try:
        actor_wus = json.loads(actor_work_units) if actor_work_units else AAA_ACTOR_WORK_UNITS
    except json.JSONDecodeError:
        return _error(f"Invalid actor_work_units JSON: {actor_work_units}")

    try:
        event_wus = json.loads(event_work_units) if event_work_units else AAA_EVENT_WORK_UNITS
    except json.JSONDecodeError:
        return _error(f"Invalid event_work_units JSON: {event_work_units}")

    try:
        sw_groups = json.loads(switch_groups) if switch_groups else AAA_SWITCH_GROUPS
    except json.JSONDecodeError:
        return _error(f"Invalid switch_groups JSON: {switch_groups}")

    try:
        st_groups = json.loads(state_groups) if state_groups else AAA_STATE_GROUPS
    except json.JSONDecodeError:
        return _error(f"Invalid state_groups JSON: {state_groups}")

    if not include_reverbs:
        buses = {k: v for k, v in buses.items() if k != "Reverbs"}

    conn = get_wwise_connection()

    try:
        _begin_undo(conn, "AAA Project Setup")

        result: dict = {
            "template": "aaa_setup",
            "buses": {},
            "actor_work_units": {},
            "event_work_units": {},
            "switch_groups": {},
            "state_groups": {},
        }

        # --- 1. Master Mixer bus hierarchy ---
        master_bus = DEFAULT_PATHS["master_bus"]
        _create_bus_tree(conn, master_bus, buses, result["buses"])

        # --- 2. Actor-Mixer Work Units (separate .wwu files) ---
        actor_root = "\\Actor-Mixer Hierarchy"
        for wu_name in actor_wus:
            wu = _create(conn, actor_root, "WorkUnit", wu_name)
            result["actor_work_units"][wu_name] = wu["id"]

        # --- 3. Event Work Units (separate .wwu files) ---
        event_root = "\\Events"
        for wu_name in event_wus:
            wu = _create(conn, event_root, "WorkUnit", wu_name)
            result["event_work_units"][wu_name] = wu["id"]

        # --- 4. Switch Groups ---
        for sg_name, values in sw_groups.items():
            sg = _create(conn, DEFAULT_PATHS["switches"], "SwitchGroup", sg_name)
            sg_id = sg["id"]
            switch_ids = {}
            for val in values:
                sw = _create(conn, sg_id, "Switch", val)
                switch_ids[val] = sw["id"]
            result["switch_groups"][sg_name] = {
                "id": sg_id,
                "values": switch_ids,
            }

        # --- 5. State Groups ---
        for sg_name, values in st_groups.items():
            sg = _create(conn, DEFAULT_PATHS["states"], "StateGroup", sg_name)
            sg_id = sg["id"]
            state_ids = {}
            for val in values:
                st = _create(conn, sg_id, "State", val)
                state_ids[val] = st["id"]
            result["state_groups"][sg_name] = {
                "id": sg_id,
                "values": state_ids,
            }

        _end_undo(conn)

        # Summary counts
        result["summary"] = {
            "buses_created": len(result["buses"]),
            "actor_work_units_created": len(result["actor_work_units"]),
            "event_work_units_created": len(result["event_work_units"]),
            "switch_groups_created": len(result["switch_groups"]),
            "state_groups_created": len(result["state_groups"]),
        }

        return _ok(result)
    except Exception as e:
        _cancel_undo(conn)
        return _error(str(e))


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

        # Create Sound children with pitch randomization
        half_pitch = pitch_randomization // 2
        sound_ids = []
        for i in range(num_variations):
            sound = _create(conn, cid, "Sound", f"{weapon_name}_Shot_{i + 1:02d}")
            sid = sound["id"]
            _set_prop(conn, sid, "EnableMidiNoteTracking", False)
            _set_prop(conn, sid, "PitchModMin", -half_pitch)
            _set_prop(conn, sid, "PitchModMax", half_pitch)
            sound_ids.append(sid)

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
