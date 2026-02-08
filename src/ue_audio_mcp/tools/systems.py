"""Orchestration layer — build_audio_system tool.

Wires all 3 layers (Wwise + MetaSounds + Blueprints) into a single tool
that generates complete audio systems from a pattern name.

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

    Available patterns: gunshot, footsteps, ambient, spatial, ui_sound, weather, preset_morph, macro_sequence.

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
