"""Actor and camera control tools for staging UE scenes."""

from __future__ import annotations

import json
import math
from typing import Any

from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _check_ue5_result, _error, _ok, logged_tool
from ue_audio_mcp.ue5_connection import get_ue5_connection


def _valid_vec3(value: list[float] | None, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)):
        return f"{name} must be [x, y, z]"
    if len(value) < 3:
        return f"{name} must be [x, y, z]"
    if not all(
        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))
        for v in value[:3]
    ):
        return f"{name} values must be numbers"
    return None


def _send_camera_command(cmd: dict[str, Any]) -> str:
    conn = get_ue5_connection()
    try:
        result = conn.send_command(cmd)
        if err := _check_ue5_result(result):
            return _error(err)
        return _ok(result)
    except Exception as e:
        return _error(str(e))


def _focus_editor_camera_command(actor: str, active_viewport_only: bool = True) -> str:
    return _send_camera_command({
        "action": "focus_editor_camera",
        "actor": actor,
        "active_viewport_only": active_viewport_only,
    })


@mcp.tool()
@logged_tool
def find_actor(query: str = "", class_filter: str = "", limit: int = 50) -> str:
    """Find actors in the current editor or PIE world.

    Args:
        query: Optional label/name/path substring.
        class_filter: Optional class-name substring, e.g. "Character", "CameraActor".
        limit: Maximum actors to return, clamped by the plugin.
    """
    if limit <= 0:
        return _error("limit must be > 0")
    return _send_camera_command({
        "action": "find_actor",
        "query": query,
        "class_filter": class_filter,
        "limit": limit,
    })


@mcp.tool()
@logged_tool
def set_actor_transform(
    actor: str,
    location: list[float] | None = None,
    rotation: list[float] | None = None,
    focus_camera: bool = False,
) -> str:
    """Move and/or rotate an actor in the current editor or PIE world.

    Args:
        actor: Actor label, object name, or full path returned by find_actor.
        location: Optional world position as [x, y, z].
        rotation: Optional rotation as [pitch, yaw, roll] in degrees.
        focus_camera: Also frame the actor in the active editor viewport.
    """
    if not actor or not actor.strip():
        return _error("actor cannot be empty")
    if location is None and rotation is None:
        return _error("provide at least one of location or rotation")
    if err := _valid_vec3(location, "location"):
        return _error(err)
    if err := _valid_vec3(rotation, "rotation"):
        return _error(err)

    cmd: dict[str, Any] = {"action": "set_actor_transform", "actor": actor}
    if location is not None:
        cmd["location"] = location
    if rotation is not None:
        cmd["rotation"] = rotation

    result_json = _send_camera_command(cmd)
    if not focus_camera:
        return result_json

    result = json.loads(result_json)
    if result.get("status") != "ok":
        return result_json

    focus_result = json.loads(_focus_editor_camera_command(actor))
    if focus_result.get("status") == "ok":
        result["focused_camera"] = True
    else:
        result.setdefault("warnings", []).append(
            f"focus_camera failed: {focus_result.get('message', 'unknown error')}"
        )
    return json.dumps(result)


@mcp.tool()
@logged_tool
def focus_editor_camera(actor: str, active_viewport_only: bool = True) -> str:
    """Frame an actor in the Unreal Editor viewport camera.

    Args:
        actor: Actor label, object name, or full path returned by find_actor.
        active_viewport_only: When true, move only the active viewport camera.
    """
    if not actor or not actor.strip():
        return _error("actor cannot be empty")
    return _focus_editor_camera_command(actor, active_viewport_only)


@mcp.tool()
@logged_tool
def set_view_target(actor: str, blend_time: float = 0.0, player_index: int = 0) -> str:
    """Set the runtime player camera view target to an actor.

    This is intended for PIE/simulation. Use focus_editor_camera for the editor viewport.

    Args:
        actor: Actor label, object name, or full path returned by find_actor.
        blend_time: Camera blend duration in seconds.
        player_index: Local player/controller index.
    """
    if not actor or not actor.strip():
        return _error("actor cannot be empty")
    if blend_time < 0:
        return _error("blend_time must be >= 0")
    if player_index < 0:
        return _error("player_index must be >= 0")
    return _send_camera_command({
        "action": "set_view_target",
        "actor": actor,
        "blend_time": blend_time,
        "player_index": player_index,
    })


@mcp.tool()
@logged_tool
def possess_pawn(actor: str, player_index: int = 0, set_view_target_on_possess: bool = True) -> str:
    """Possess a Pawn/Character with a runtime player controller.

    Args:
        actor: Pawn/Character label, object name, or full path returned by find_actor.
        player_index: Local player/controller index.
        set_view_target_on_possess: Also set the possessed pawn as the camera target.
    """
    if not actor or not actor.strip():
        return _error("actor cannot be empty")
    if player_index < 0:
        return _error("player_index must be >= 0")
    return _send_camera_command({
        "action": "possess_pawn",
        "actor": actor,
        "player_index": player_index,
        "set_view_target": set_view_target_on_possess,
    })
