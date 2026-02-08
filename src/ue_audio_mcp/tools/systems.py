"""Orchestration layer — build_audio_system + build_aaa_project tools.

Wires all 3 layers (Wwise + MetaSounds + Blueprints) into a single tool
that generates complete audio systems from a pattern name.

build_aaa_project goes further: creates AAA Wwise infrastructure, then
generates content for every audio category, routes outputs to correct
buses, and moves objects to dedicated work units.

Auto-detects connection state for graceful degradation:
  Full:       Wwise + UE5 running  -> executes everything, returns IDs
  Wwise-only: Just Wwise           -> executes Wwise, returns MS commands + BP spec
  Offline:    Nothing running       -> returns all 3 specs as JSON (dry-run)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from ue_audio_mcp.connection import get_wwise_connection
from ue_audio_mcp.knowledge.graph_schema import graph_to_builder_commands, validate_graph
from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _error, _ok
from ue_audio_mcp.ue5_connection import get_ue5_connection

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pattern registry
# ---------------------------------------------------------------------------

PATTERNS: dict[str, dict[str, Any]] = {
    "gunshot": {
        "ms_template": "gunshot",
        "wwise_template": "gunshot",
        "wwise_json": "gunshot",
        "bp_template": "weapon_burst_control",
        "default_params": {
            "wwise": {"weapon_name": "Rifle", "num_variations": 3, "pitch_randomization": 100},
            "metasounds": {},
            "blueprint": {},
        },
        "connections": {
            "wwise_event": "Play_Gunshot_{name}",
            "metasound_asset": "MS_{name}_Gunshot",
            "audiolink_bus": "AudioLink_Weapons",
            "wiring": [
                {"from": "blueprint.PostEvent", "to": "wwise.event.Play_Gunshot_{name}", "type": "event"},
                {"from": "wwise.event.Play", "to": "metasound.OnPlay", "type": "trigger"},
                {"from": "blueprint.SetRTPCValue", "to": "wwise.rtpc.RTPC_Gunshot_Distance", "type": "rtpc"},
                {"from": "blueprint.SetFloatParameter('Distance')", "to": "metasound.Distance", "type": "param"},
                {"from": "metasound.Output", "to": "wwise.bus.AudioLink_Weapons", "type": "audiolink"},
            ],
        },
    },
    "footsteps": {
        "ms_template": "footsteps",
        "wwise_template": "footsteps",
        "wwise_json": "footsteps",
        "bp_template": "footfalls_simple",
        "default_params": {
            "wwise": {
                "surface_types": ["Concrete", "Grass", "Metal"],
                "with_switch_group": True,
            },
            "metasounds": {},
            "blueprint": {},
        },
        "connections": {
            "wwise_event": "Play_Footstep",
            "metasound_asset": "MS_{name}_Footsteps",
            "audiolink_bus": "AudioLink_Foley",
            "wiring": [
                {"from": "blueprint.PostEvent", "to": "wwise.event.Play_Footstep", "type": "event"},
                {"from": "blueprint.SetSwitch('Surface_Type')", "to": "wwise.switch.Surface_Type", "type": "switch"},
                {"from": "blueprint.SetIntParameter('SurfaceType')", "to": "metasound.SurfaceType", "type": "param"},
                {"from": "wwise.event.Play", "to": "metasound.OnPlay", "type": "trigger"},
                {"from": "blueprint.SetRTPCValue", "to": "wwise.rtpc.RTPC_Footstep_Speed", "type": "rtpc"},
                {"from": "metasound.Output", "to": "wwise.bus.AudioLink_Foley", "type": "audiolink"},
            ],
        },
    },
    "ambient": {
        "ms_template": "ambient",
        "wwise_template": "ambient",
        "wwise_json": "ambient",
        "bp_template": "ambient_height_wind",
        "default_params": {
            "wwise": {
                "layer_names": ["Wind_Light", "Wind_Medium", "Wind_Heavy"],
                "rtpc_parameter_name": "Wind_Intensity",
            },
            "metasounds": {},
            "blueprint": {},
        },
        "connections": {
            "wwise_event": "Play_Ambient_{name}",
            "metasound_asset": "MS_{name}_Ambient",
            "audiolink_bus": "AudioLink_Ambience",
            "wiring": [
                {"from": "blueprint.PostEvent", "to": "wwise.event.Play_Ambient_{name}", "type": "event"},
                {"from": "blueprint.SetRTPCValue", "to": "wwise.rtpc.RTPC_Wind_Intensity", "type": "rtpc"},
                {"from": "blueprint.SetFloatParameter('Intensity')", "to": "metasound.Intensity", "type": "param"},
                {"from": "wwise.event.Play", "to": "metasound.OnPlay", "type": "trigger"},
                {"from": "metasound.Output", "to": "wwise.bus.AudioLink_Ambience", "type": "audiolink"},
            ],
        },
    },
    "spatial": {
        "ms_template": "spatial",
        "wwise_template": None,
        "wwise_json": None,
        "bp_template": "spatial_attenuation",
        "default_params": {
            "wwise": {},
            "metasounds": {},
            "blueprint": {},
        },
        "connections": {
            "wwise_event": None,
            "metasound_asset": "MS_{name}_Spatial",
            "wiring": [
                {"from": "blueprint.SetFloatParameter('Distance')", "to": "metasound.Distance", "type": "param"},
            ],
        },
    },
    "ui_sound": {
        "ms_template": "ui_sound",
        "wwise_template": "ui_sound",
        "wwise_json": "ui_sound",
        "bp_template": "set_float_parameter",
        "default_params": {
            "wwise": {"sound_name": "Click", "bus_path": ""},
            "metasounds": {},
            "blueprint": {},
        },
        "connections": {
            "wwise_event": "Play_UI_{name}",
            "metasound_asset": "MS_{name}_UI",
            "audiolink_bus": "AudioLink_UI",
            "wiring": [
                {"from": "blueprint.PostEvent", "to": "wwise.event.Play_UI_{name}", "type": "event"},
                {"from": "wwise.event.Play", "to": "metasound.OnPlay", "type": "trigger"},
                {"from": "metasound.Output", "to": "wwise.bus.AudioLink_UI", "type": "audiolink"},
            ],
        },
    },
    "weather": {
        "ms_template": "weather",
        "wwise_template": "weather_states",
        "wwise_json": "weather",
        "bp_template": "wind_system",
        "default_params": {
            "wwise": {
                "weather_states": ["Clear", "Cloudy", "LightRain", "HeavyRain", "Storm", "Snow"],
            },
            "metasounds": {},
            "blueprint": {},
        },
        "connections": {
            "wwise_event": "Play_Weather_Ambience",
            "metasound_asset": "MS_{name}_Weather",
            "audiolink_bus": "AudioLink_Weather",
            "wiring": [
                {"from": "blueprint.PostEvent", "to": "wwise.event.Play_Weather_Ambience", "type": "event"},
                {"from": "blueprint.SetState('Weather')", "to": "wwise.state.Weather", "type": "state"},
                {"from": "blueprint.SetIntParameter('WeatherState')", "to": "metasound.WeatherState", "type": "param"},
                {"from": "blueprint.SetRTPCValue", "to": "wwise.rtpc.RTPC_Weather_Intensity", "type": "rtpc"},
                {"from": "blueprint.SetFloatParameter('Intensity')", "to": "metasound.Intensity", "type": "param"},
                {"from": "wwise.event.Play", "to": "metasound.OnPlay", "type": "trigger"},
                {"from": "metasound.Output", "to": "wwise.bus.AudioLink_Weather", "type": "audiolink"},
            ],
        },
    },
    "preset_morph": {
        "ms_template": "preset_morph",
        "wwise_template": None,
        "wwise_json": None,
        "bp_template": "set_float_parameter",
        "default_params": {
            "wwise": {},
            "metasounds": {},
            "blueprint": {},
        },
        "connections": {
            "wwise_event": None,
            "metasound_asset": "MS_{name}_PresetMorph",
            "wiring": [
                {"from": "blueprint.SetFloatParameter('Morph')", "to": "metasound.Morph", "type": "param"},
            ],
        },
    },
    "macro_sequence": {
        "ms_template": "macro_sequence",
        "wwise_template": None,
        "wwise_json": None,
        "bp_template": None,
        "default_params": {
            "wwise": {},
            "metasounds": {},
            "blueprint": {},
        },
        "connections": {
            "wwise_event": None,
            "metasound_asset": "MS_{name}_MacroSequence",
            "wiring": [
                {"from": "blueprint.MacroStep1", "to": "metasound.MacroStep1", "type": "trigger"},
                {"from": "blueprint.MacroStep2", "to": "metasound.MacroStep2", "type": "trigger"},
                {"from": "blueprint.MacroStep3", "to": "metasound.MacroStep3", "type": "trigger"},
            ],
        },
    },
    "sfx_generator": {
        "ms_template": "sfx_generator",
        "wwise_template": None,
        "wwise_json": None,
        "bp_template": None,
        "default_params": {
            "wwise": {},
            "metasounds": {"BaseFrequency": 440.0, "AmpDuration": 1.0},
            "blueprint": {},
        },
        "connections": {
            "wwise_event": None,
            "metasound_asset": "MS_{name}_SFXGenerator",
            "wiring": [
                {"from": "blueprint.PlayMetaSound", "to": "metasound.OnPlay", "type": "trigger"},
                {"from": "blueprint.SetFloatParameter('BaseFrequency')", "to": "metasound.BaseFrequency", "type": "param"},
                {"from": "blueprint.SetFloatParameter('FilterCutoff')", "to": "metasound.FilterCutoff", "type": "param"},
                {"from": "blueprint.SetFloatParameter('FilterType')", "to": "metasound.FilterType", "type": "param"},
            ],
        },
    },
    "vehicle_engine": {
        "ms_template": "vehicle_engine",
        "wwise_template": None,
        "wwise_json": "vehicle_engine",
        "bp_template": None,
        "default_params": {
            "wwise": {"vehicle_name": "Speeder"},
            "metasounds": {},
            "blueprint": {},
        },
        "connections": {
            "wwise_event": "Play_Vehicle_{name}",
            "metasound_asset": "MS_{name}_Engine",
            "audiolink_bus": "AudioLink_Vehicles",
            "wiring": [
                {"from": "blueprint.PostEvent", "to": "wwise.event.Play_Vehicle_{name}", "type": "event"},
                {"from": "wwise.event.Play", "to": "metasound.OnPlay", "type": "trigger"},
                {"from": "blueprint.SetRTPCValue", "to": "wwise.rtpc.RTPC_Vehicle_RPM", "type": "rtpc"},
                {"from": "blueprint.PostTrigger('TurboStartTrigger')", "to": "metasound.TurboStartTrigger", "type": "trigger"},
                {"from": "blueprint.PostTrigger('TurboStopTrigger')", "to": "metasound.TurboStopTrigger", "type": "trigger"},
                {"from": "metasound.Output", "to": "wwise.bus.AudioLink_Vehicles", "type": "audiolink"},
            ],
        },
    },
    "sid_synth": {
        "ms_template": "sid_chip_tune",
        "wwise_template": None,
        "wwise_json": None,
        "bp_template": None,
        "default_params": {
            "wwise": {},
            "metasounds": {"Lead Freq": 440.0, "Bass Freq": 110.0, "Filter Cutoff": 0.45},
            "blueprint": {},
        },
        "connections": {
            "wwise_event": None,
            "metasound_asset": "MS_{name}_SIDSynth",
            "wiring": [
                {"from": "blueprint.PlayMetaSound", "to": "metasound.OnPlay", "type": "trigger"},
                {"from": "blueprint.SetFloatParameter('Lead Freq')", "to": "metasound.Lead Freq", "type": "param"},
                {"from": "blueprint.SetFloatParameter('Bass Freq')", "to": "metasound.Bass Freq", "type": "param"},
                {"from": "blueprint.SetFloatParameter('Filter Cutoff')", "to": "metasound.Filter Cutoff", "type": "param"},
                {"from": "blueprint.SetFloatParameter('Volume')", "to": "metasound.Volume", "type": "param"},
            ],
        },
    },
}

# Map wwise_template names to template functions (imported lazily)
_WWISE_TEMPLATE_FUNCS: dict[str, str] = {
    "gunshot": "template_gunshot",
    "footsteps": "template_footsteps",
    "ambient": "template_ambient",
    "ui_sound": "template_ui_sound",
    "weather_states": "template_weather_states",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_template_dir(subdir: str) -> str:
    """Return absolute path to a templates subdirectory."""
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "templates", subdir,
    )


def _load_wwise_json(template_name: str) -> dict[str, Any] | None:
    """Load a Wwise integration JSON template (cross-layer spec)."""
    if template_name is None:
        return None
    template_path = os.path.join(
        _get_template_dir("wwise"), "{}.json".format(template_name)
    )
    if not os.path.isfile(template_path):
        return None
    with open(template_path) as f:
        return json.load(f)


def _load_ms_template(template_name: str, ms_params: dict) -> dict[str, Any]:
    """Load a MetaSounds template JSON and apply param overrides."""
    template_path = os.path.join(
        _get_template_dir("metasounds"), "{}.json".format(template_name)
    )
    if not os.path.isfile(template_path):
        return {"error": "MetaSounds template not found: {}".format(template_name)}

    with open(template_path) as f:
        spec = json.load(f)

    # Apply node-level overrides: {"node_id.input_name": value}
    if ms_params:
        node_map = {n["id"]: n for n in spec.get("nodes", [])}
        for key, value in ms_params.items():
            parts = key.split(".", 1)
            if len(parts) != 2:
                continue
            node_id, input_name = parts
            node = node_map.get(node_id)
            if node is None:
                continue
            node.setdefault("defaults", {})[input_name] = value

    return spec


def _load_bp_template(template_name: str, bp_params: dict) -> dict[str, Any] | None:
    """Load a Blueprint template JSON if it exists. Returns None if missing."""
    template_path = os.path.join(
        _get_template_dir("blueprints"), "{}.json".format(template_name)
    )
    if not os.path.isfile(template_path):
        return None

    with open(template_path) as f:
        spec = json.load(f)

    # Apply overrides to node defaults
    if bp_params:
        node_map = {n["id"]: n for n in spec.get("nodes", [])}
        for key, value in bp_params.items():
            parts = key.split(".", 1)
            if len(parts) != 2:
                continue
            node_id, input_name = parts
            node = node_map.get(node_id)
            if node is None:
                continue
            node.setdefault("defaults", {})[input_name] = value

    return spec


def _build_wwise_layer(
    pattern_cfg: dict,
    wwise_params: dict,
    asset_name: str,
) -> dict[str, Any]:
    """Execute Wwise template or return planned calls.

    Returns dict with "mode" ("executed" | "planned" | "skipped"),
    plus template results or parameter spec.
    """
    wwise_template = pattern_cfg["wwise_template"]
    if wwise_template is None:
        return {"mode": "skipped", "reason": "No Wwise template for this pattern"}

    func_name = _WWISE_TEMPLATE_FUNCS.get(wwise_template)
    if func_name is None:
        return {"mode": "skipped", "reason": "Unknown Wwise template: {}".format(wwise_template)}

    # Check connection
    wwise = get_wwise_connection()
    if not wwise.is_connected():
        # Return planned params -- what WOULD be sent
        return {
            "mode": "planned",
            "template": wwise_template,
            "function": func_name,
            "params": wwise_params,
        }

    # Execute the template function
    from ue_audio_mcp.tools import templates as tmpl_mod

    template_fn = getattr(tmpl_mod, func_name)

    # Map params to function kwargs based on template type
    kwargs = _map_wwise_params(wwise_template, wwise_params, asset_name)

    result_json = template_fn(**kwargs)
    result = json.loads(result_json)
    if result.get("status") == "error":
        return {"mode": "error", "reason": result.get("message", "Wwise template failed"), "result": result}
    return {"mode": "executed", "result": result}


def _map_wwise_params(template_name: str, params: dict, asset_name: str) -> dict:
    """Map user-facing params to the actual template function kwargs."""
    if template_name == "gunshot":
        return {
            "weapon_name": params.get("weapon_name", asset_name),
            "num_variations": params.get("num_variations", 3),
            "pitch_randomization": params.get("pitch_randomization", 100),
        }
    if template_name == "footsteps":
        surfaces = params.get("surface_types", ["Concrete", "Grass", "Metal"])
        return {
            "surface_types": json.dumps(surfaces) if isinstance(surfaces, list) else surfaces,
            "with_switch_group": params.get("with_switch_group", True),
        }
    if template_name == "ambient":
        layers = params.get("layer_names", ["Wind_Light", "Wind_Medium", "Wind_Heavy"])
        return {
            "layer_names": json.dumps(layers) if isinstance(layers, list) else layers,
            "rtpc_parameter_name": params.get("rtpc_parameter_name", "Wind_Intensity"),
        }
    if template_name == "ui_sound":
        return {
            "sound_name": params.get("sound_name", asset_name),
            "bus_path": params.get("bus_path", ""),
        }
    if template_name == "weather_states":
        states = params.get("weather_states", ["Clear", "Cloudy", "LightRain", "HeavyRain", "Storm", "Snow"])
        return {
            "weather_states": json.dumps(states) if isinstance(states, list) else states,
        }
    return {}


def _build_metasounds_layer(
    pattern_cfg: dict,
    ms_params: dict,
    asset_name: str,
) -> dict[str, Any]:
    """Load MS template, validate, convert to commands, optionally execute."""
    ms_template = pattern_cfg["ms_template"]
    if ms_template is None:
        return {"mode": "skipped", "reason": "No MetaSounds template for this pattern"}

    spec = _load_ms_template(ms_template, ms_params)
    if "error" in spec:
        return {"mode": "error", "reason": spec["error"]}

    # Override asset name
    spec["name"] = asset_name

    # Validate
    errors = validate_graph(spec)
    if errors:
        return {
            "mode": "error",
            "reason": "Graph validation failed with {} error(s)".format(len(errors)),
            "validation_errors": errors,
            "graph_spec": spec,
        }

    # Convert to Builder commands
    commands = graph_to_builder_commands(spec)

    # Check UE5 connection
    ue5 = get_ue5_connection()
    if not ue5.is_connected():
        return {
            "mode": "planned",
            "graph_spec": spec,
            "command_count": len(commands),
            "commands": commands,
        }

    # Execute all commands
    results = []
    for i, cmd in enumerate(commands):
        try:
            result = ue5.send_command(cmd)
            results.append(result)
        except Exception as e:
            return {
                "mode": "error",
                "reason": "Command {} ({}) failed: {}".format(i + 1, cmd.get("action", "?"), e),
                "commands_sent": i,
                "commands_total": len(commands),
            }

    return {
        "mode": "executed",
        "graph_spec": spec,
        "command_count": len(commands),
        "results": results,
    }


def _build_blueprint_layer(
    pattern_cfg: dict,
    bp_params: dict,
) -> dict[str, Any]:
    """Load BP template if available. Always returns spec (no execution)."""
    bp_template = pattern_cfg.get("bp_template")
    if bp_template is None:
        return {"mode": "skipped", "reason": "No Blueprint template for this pattern (coming soon)"}

    spec = _load_bp_template(bp_template, bp_params)
    if spec is None:
        return {"mode": "skipped", "reason": "Blueprint template file not found: {}".format(bp_template)}

    return {"mode": "planned", "spec": spec}


def _build_connection_map(
    pattern_cfg: dict,
    asset_name: str,
    wwise_result: dict,
    ms_result: dict,
) -> dict[str, Any]:
    """Build the cross-layer connection map."""
    conn_cfg = pattern_cfg.get("connections", {})

    # Resolve name placeholders
    wwise_event = conn_cfg.get("wwise_event")
    if wwise_event:
        wwise_event = wwise_event.format(name=asset_name)

    ms_asset = conn_cfg.get("metasound_asset", "").format(name=asset_name)

    # Extract IDs if Wwise was executed
    wwise_ids = {}
    if wwise_result.get("mode") == "executed":
        wr = wwise_result.get("result", {})
        if wr.get("status") == "ok":
            wwise_ids = {
                k: v for k, v in wr.items()
                if k.endswith("_id") or k.endswith("_ids")
            }

    # Resolve wiring placeholders
    wiring = []
    for w in conn_cfg.get("wiring", []):
        entry = {}
        for k, v in w.items():
            entry[k] = v.format(name=asset_name) if isinstance(v, str) else v
        wiring.append(entry)

    return {
        "wwise_event": wwise_event,
        "metasound_asset": ms_asset,
        "audiolink_bus": conn_cfg.get("audiolink_bus"),
        "wwise_ids": wwise_ids,
        "wiring": wiring,
    }


# ---------------------------------------------------------------------------
# Public tool
# ---------------------------------------------------------------------------

@mcp.tool()
def build_audio_system(
    pattern: str,
    name: str = "",
    params_json: str = "{}",
) -> str:
    """Build a complete 3-layer audio system (Wwise + MetaSounds + Blueprints) from a pattern.

    Auto-detects which backends are connected and degrades gracefully:
    - Full (Wwise + UE5): executes everything, returns created IDs
    - Wwise-only: executes Wwise, returns MetaSounds commands for later
    - Offline: returns all 3 layer specs as JSON (dry-run preview)

    Available patterns: gunshot, footsteps, ambient, spatial, ui_sound, weather, preset_morph, macro_sequence, sfx_generator, vehicle_engine.

    Args:
        pattern: Pattern name (e.g. "gunshot", "footsteps")
        name: Asset name prefix (defaults to pattern name)
        params_json: JSON overrides for all 3 layers, e.g. {"wwise": {"num_variations": 5}}
    """
    # 1. Validate pattern
    if pattern not in PATTERNS:
        return _error(
            "Unknown pattern '{}'. Available: {}".format(
                pattern, ", ".join(sorted(PATTERNS))
            )
        )

    # 2. Parse and merge params
    try:
        user_params = json.loads(params_json)
    except (json.JSONDecodeError, ValueError):
        return _error("Invalid params_json -- must be valid JSON")

    if not isinstance(user_params, dict):
        return _error("params_json must be a JSON object")

    pattern_cfg = PATTERNS[pattern]
    defaults = pattern_cfg["default_params"]
    asset_name = name or pattern.replace("_", " ").title().replace(" ", "")

    # Merge per-layer params
    wwise_params = {**defaults.get("wwise", {}), **user_params.get("wwise", {})}
    ms_params = {**defaults.get("metasounds", {}), **user_params.get("metasounds", {})}
    bp_params = {**defaults.get("blueprint", {}), **user_params.get("blueprint", {})}

    # 3. Detect connection mode
    wwise_connected = get_wwise_connection().is_connected()
    ue5_connected = get_ue5_connection().is_connected()

    if wwise_connected and ue5_connected:
        mode = "full"
    elif wwise_connected:
        mode = "wwise_only"
    else:
        mode = "offline"

    # 4. Build all 3 layers
    wwise_result = _build_wwise_layer(pattern_cfg, wwise_params, asset_name)
    ms_result = _build_metasounds_layer(pattern_cfg, ms_params, asset_name)
    bp_result = _build_blueprint_layer(pattern_cfg, bp_params)

    # 5. Build connection map
    connections = _build_connection_map(pattern_cfg, asset_name, wwise_result, ms_result)

    # 6. Load Wwise integration spec (cross-layer JSON)
    wwise_json_spec = _load_wwise_json(pattern_cfg.get("wwise_json"))
    integration = None
    if wwise_json_spec:
        integration = {
            "signal_flow": wwise_json_spec.get("signal_flow", []),
            "audiolink": wwise_json_spec.get("audiolink"),
            "metasound_link": wwise_json_spec.get("metasound_link"),
            "blueprint_link": wwise_json_spec.get("blueprint_link"),
        }

    # 7. Check for layer-level errors
    layer_errors = []
    for layer_name, result in [("wwise", wwise_result), ("metasounds", ms_result), ("blueprint", bp_result)]:
        if result.get("mode") == "error":
            layer_errors.append("{}: {}".format(layer_name, result.get("reason", "unknown error")))

    return _ok({
        "pattern": pattern,
        "name": asset_name,
        "mode": mode,
        "layers": {
            "wwise": wwise_result,
            "metasounds": ms_result,
            "blueprint": bp_result,
        },
        "connections": connections,
        "integration": integration,
        "errors": layer_errors,
    })


# ---------------------------------------------------------------------------
# AAA Project Orchestrator
# ---------------------------------------------------------------------------

AAA_AUDIO_CATEGORIES: dict[str, dict[str, Any]] = {
    "player_footsteps": {
        "pattern": "footsteps",
        "name": "Player_Footsteps",
        "bus": "PlayerFootsteps",
        "bus_path": "\\Master-Mixer Hierarchy\\Default Work Unit\\Master Audio Bus\\PlayerMaster\\PlayerLocomotion\\PlayerFootsteps",
        "actor_work_unit": "Player_Locomotion",
        "event_work_unit": "Player",
        "params": {
            "wwise": {
                "surface_types": ["Concrete", "Grass", "Metal", "Wood", "Gravel"],
                "with_switch_group": True,
            },
        },
    },
    "player_weapons": {
        "pattern": "gunshot",
        "name": "Player_Rifle",
        "bus": "PlayerWeapons",
        "bus_path": "\\Master-Mixer Hierarchy\\Default Work Unit\\Master Audio Bus\\PlayerMaster\\PlayerWeapons",
        "actor_work_unit": "Player_Weapons",
        "event_work_unit": "Player",
        "params": {
            "wwise": {"weapon_name": "Rifle", "num_variations": 4, "pitch_randomization": 120},
        },
    },
    "npc_footsteps": {
        "pattern": "footsteps",
        "name": "NPC_Footsteps",
        "bus": "NPCFootsteps",
        "bus_path": "\\Master-Mixer Hierarchy\\Default Work Unit\\Master Audio Bus\\NPCMaster\\NPCFootsteps",
        "actor_work_unit": "NPC_Locomotion",
        "event_work_unit": "NPC",
        "params": {
            "wwise": {
                "surface_types": ["Concrete", "Grass", "Metal"],
                "with_switch_group": True,
            },
        },
    },
    "ambient_wind": {
        "pattern": "ambient",
        "name": "Ambient_Wind",
        "bus": "3DAmbience",
        "bus_path": "\\Master-Mixer Hierarchy\\Default Work Unit\\Master Audio Bus\\AmbientMaster\\3DAmbience",
        "actor_work_unit": "Ambience",
        "event_work_unit": "Ambience",
        "params": {
            "wwise": {
                "layer_names": ["Wind_Light", "Wind_Medium", "Wind_Heavy"],
                "rtpc_parameter_name": "Wind_Intensity",
            },
        },
    },
    "weather": {
        "pattern": "weather",
        "name": "Weather_System",
        "bus": "2DAmbience",
        "bus_path": "\\Master-Mixer Hierarchy\\Default Work Unit\\Master Audio Bus\\AmbientMaster\\2DAmbience",
        "actor_work_unit": "Ambience",
        "event_work_unit": "Ambience",
        "params": {
            "wwise": {
                "weather_states": ["Clear", "Cloudy", "LightRain", "HeavyRain", "Storm", "Snow"],
            },
        },
    },
    "ui": {
        "pattern": "ui_sound",
        "name": "UI_Click",
        "bus": "UIMaster",
        "bus_path": "\\Master-Mixer Hierarchy\\Default Work Unit\\Master Audio Bus\\UIMaster",
        "actor_work_unit": "UI",
        "event_work_unit": "UI",
        "params": {
            "wwise": {"sound_name": "Click", "bus_path": ""},
        },
    },
}


def _route_to_bus(conn, object_ref: str, bus_path: str) -> dict[str, Any]:
    """Set OutputBus reference on a Wwise container to route to an AAA bus.

    Args:
        object_ref: GUID or Wwise path of the object to route.
        bus_path: Wwise path of the target bus.
    """
    try:
        conn.call("ak.wwise.core.object.setReference", {
            "object": object_ref,
            "reference": "OutputBus",
            "value": bus_path,
        })
        return {"status": "ok", "object": object_ref, "bus": bus_path}
    except Exception as e:
        return {"status": "error", "object": object_ref, "bus": bus_path, "error": str(e)}


def _move_to_work_unit(conn, object_ref: str, work_unit_path: str) -> dict[str, Any]:
    """Move a Wwise object from Default WU to a named Work Unit.

    Args:
        object_ref: GUID or Wwise path of the object to move.
        work_unit_path: Wwise path of the destination Work Unit.
    """
    try:
        conn.call("ak.wwise.core.object.move", {
            "object": object_ref,
            "parent": work_unit_path,
            "onNameConflict": "merge",
        })
        return {"status": "ok", "object": object_ref, "destination": work_unit_path}
    except Exception as e:
        return {"status": "error", "object": object_ref, "destination": work_unit_path, "error": str(e)}


@mcp.tool()
def build_aaa_project(
    categories: str = "",
    setup_params: str = "{}",
) -> str:
    """Build a complete AAA audio project: infrastructure + content for all categories.

    Creates AAA Wwise infrastructure (buses, work units, switches, states),
    then generates 3-layer content (Wwise + MetaSounds + Blueprints) for each
    audio category, routes outputs to correct buses, and moves objects to
    dedicated work units.

    Auto-detects connection state:
    - Full (Wwise + UE5): creates infrastructure, builds all content, routes + moves
    - Wwise-only: creates infrastructure, builds Wwise content, returns MS commands
    - Offline: returns complete manifest of what would be created (dry-run)

    Args:
        categories: Comma-separated category filter (default: all).
            Available: player_footsteps, player_weapons, npc_footsteps,
            ambient_wind, weather, ui
        setup_params: JSON overrides for template_aaa_setup, e.g.
            {"include_reverbs": false}
    """
    # 1. Parse category filter
    if categories.strip():
        requested = [c.strip() for c in categories.split(",")]
        invalid = [c for c in requested if c not in AAA_AUDIO_CATEGORIES]
        if invalid:
            return _error(
                "Unknown categories: {}. Available: {}".format(
                    ", ".join(invalid),
                    ", ".join(sorted(AAA_AUDIO_CATEGORIES)),
                )
            )
        active_categories = {k: AAA_AUDIO_CATEGORIES[k] for k in requested}
    else:
        active_categories = dict(AAA_AUDIO_CATEGORIES)

    # 2. Parse setup params
    try:
        setup_kw = json.loads(setup_params)
    except (json.JSONDecodeError, ValueError):
        return _error("Invalid setup_params — must be valid JSON")

    if not isinstance(setup_kw, dict):
        return _error("setup_params must be a JSON object")

    # 3. Detect connection mode
    wwise = get_wwise_connection()
    ue5 = get_ue5_connection()
    wwise_connected = wwise.is_connected()
    ue5_connected = ue5.is_connected()

    if wwise_connected and ue5_connected:
        mode = "full"
    elif wwise_connected:
        mode = "wwise_only"
    else:
        mode = "offline"

    # 4. Create AAA infrastructure
    infrastructure: dict[str, Any]
    if wwise_connected:
        from ue_audio_mcp.tools.templates import template_aaa_setup
        try:
            setup_result = json.loads(template_aaa_setup(**setup_kw))
        except TypeError as e:
            return _error("Invalid setup_params key: {}".format(e))
        if setup_result.get("status") != "ok":
            return _error("AAA setup failed: {}".format(
                setup_result.get("message", "unknown error")
            ))
        infrastructure = {
            "mode": "executed",
            "buses": setup_result.get("buses", {}),
            "actor_work_units": setup_result.get("actor_work_units", {}),
            "event_work_units": setup_result.get("event_work_units", {}),
            "switch_groups": setup_result.get("switch_groups", {}),
            "state_groups": setup_result.get("state_groups", {}),
            "summary": setup_result.get("summary", {}),
        }
    else:
        infrastructure = {
            "mode": "planned",
            "description": "AAA Wwise infrastructure (buses, work units, switches, states)",
            "setup_params": setup_kw,
        }

    # 5. Build content for each category
    category_results: dict[str, Any] = {}
    routing_results: list[dict[str, Any]] = []
    move_results: list[dict[str, Any]] = []

    for cat_key, cat_cfg in active_categories.items():
        pattern = cat_cfg["pattern"]
        name = cat_cfg["name"]
        params = cat_cfg.get("params", {})

        # Build the 3-layer audio system
        system_result_json = build_audio_system(
            pattern=pattern,
            name=name,
            params_json=json.dumps(params),
        )
        system_result = json.loads(system_result_json)

        category_results[cat_key] = {
            "pattern": pattern,
            "name": name,
            "bus": cat_cfg["bus"],
            "actor_work_unit": cat_cfg["actor_work_unit"],
            "event_work_unit": cat_cfg["event_work_unit"],
            "system": system_result,
        }

        # 6. Post-process: route to bus + move to work units (Wwise connected only)
        if wwise_connected and system_result.get("status") == "ok":
            wwise_layer = system_result.get("layers", {}).get("wwise", {})
            wwise_result_data = wwise_layer.get("result", {})

            # Find the main container ID from the Wwise result.
            # Each template returns a different key for its top-level container:
            #   gunshot -> container_id, footsteps/weather -> switch_container_id,
            #   ambient -> blend_container_id, ui_sound -> actor_mixer_id or sound_id
            container_id = (
                wwise_result_data.get("container_id")
                or wwise_result_data.get("switch_container_id")
                or wwise_result_data.get("blend_container_id")
                or wwise_result_data.get("actor_mixer_id")
            )
            if container_id:
                # Route container to correct bus
                route = _route_to_bus(wwise, container_id, cat_cfg["bus_path"])
                routing_results.append({"category": cat_key, **route})

                # Move container to correct actor-mixer work unit
                actor_wu_path = "\\Actor-Mixer Hierarchy\\{}".format(cat_cfg["actor_work_unit"])
                move = _move_to_work_unit(wwise, container_id, actor_wu_path)
                move_results.append({"category": cat_key, "type": "actor_mixer", **move})

            # Move event to correct event work unit
            event_id = wwise_result_data.get("event_id")
            if event_id:
                event_wu_path = "\\Events\\{}".format(cat_cfg["event_work_unit"])
                move = _move_to_work_unit(wwise, event_id, event_wu_path)
                move_results.append({"category": cat_key, "type": "event", **move})

    # 7. Build manifest
    return _ok({
        "mode": mode,
        "categories_built": list(category_results.keys()),
        "infrastructure": infrastructure,
        "categories": category_results,
        "routing": routing_results,
        "moves": move_results,
        "summary": {
            "total_categories": len(category_results),
            "infrastructure_mode": infrastructure["mode"],
            "routing_applied": len(routing_results),
            "moves_applied": len(move_results),
        },
    })
