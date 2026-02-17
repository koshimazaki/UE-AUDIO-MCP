"""World audio setup tools — AnimNotify, emitters, import, surfaces, volumes.

5 tools for placing audio elements in the UE5 world: animation notifies,
spatial audio emitters, sound file import, physical surface types, and
audio volumes with reverb.

Requires an active UE5 plugin connection (ue5_connect).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _error, _ok, _validate_asset_path
from ue_audio_mcp.ue5_connection import get_ue5_connection

log = logging.getLogger(__name__)


@mcp.tool()
def place_anim_notify(
    animation_path: str,
    time: float,
    sound: str = "",
    notify_name: str = "Footstep",
) -> str:
    """Place an AnimNotify_PlaySound on an animation at a specific time.

    This is the proper way to sync sounds to animation frames (e.g. footsteps
    at the exact moment each foot hits the ground).

    Args:
        animation_path: Animation asset path (e.g. "/Game/Characters/Anims/Walk")
        time: Time in seconds where the notify fires
        sound: Optional SoundBase asset path to play
        notify_name: Name for the notify event (default "Footstep")
    """
    if err := _validate_asset_path(animation_path, "animation_path"):
        return _error(err)
    if time < 0:
        return _error("time must be >= 0")

    conn = get_ue5_connection()
    try:
        cmd: dict[str, Any] = {
            "action": "place_anim_notify",
            "animation_path": animation_path,
            "time": time,
            "notify_name": notify_name,
        }
        if sound:
            cmd["sound"] = sound
        result = conn.send_command(cmd)
        if result.get("status") == "error":
            return _error(result.get("message", "place_anim_notify failed"))
        warns = []
        if not sound:
            warns.append(
                "No sound asset specified — AnimNotify will fire but play silence. "
                "Set 'sound' to a SoundBase/MetaSound asset path."
            )
        return _ok(result, warnings=warns or None)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def spawn_audio_emitter(
    sound: str,
    location: list[float],
    name: str = "MCP_AudioEmitter",
    auto_play: bool = True,
) -> str:
    """Spawn a persistent AmbientSound actor at a world location.

    Creates a spatial audio source that gets louder as the player approaches.
    Perfect for environmental sounds (campfire, waterfall, machinery).

    Args:
        sound: SoundBase/MetaSound asset path (e.g. "/Game/Audio/Ambient/Fire")
        location: World position as [x, y, z]
        name: Label for the emitter actor
        auto_play: Whether to start playing immediately (default True)
    """
    if err := _validate_asset_path(sound, "sound"):
        return _error(err)
    if not location or len(location) < 3:
        return _error("location must be [x, y, z]")

    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "spawn_audio_emitter",
            "sound": sound,
            "location": location,
            "name": name,
            "auto_play": auto_play,
        })
        if result.get("status") == "error":
            return _error(result.get("message", "spawn_audio_emitter failed"))
        return _ok(result)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def import_sound_file(
    file_path: str,
    dest_folder: str,
) -> str:
    """Import a .wav or .ogg sound file from disk into the UE5 Content folder.

    Args:
        file_path: Absolute path to the audio file on disk
        dest_folder: Destination folder in Content (e.g. "/Game/Audio/SFX")
    """
    if not file_path.strip():
        return _error("file_path cannot be empty")
    if ".." in file_path:
        return _error("file_path must not contain '..'")
    if err := _validate_asset_path(dest_folder, "dest_folder"):
        return _error(err)

    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "import_sound_file",
            "file_path": file_path,
            "dest_folder": dest_folder,
        })
        if result.get("status") == "error":
            return _error(result.get("message", "import_sound_file failed"))
        return _ok(result)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def set_physical_surface(
    material_path: str,
    surface_type: str,
) -> str:
    """Set the surface type on a Physical Material (creates it if needed).

    Surface types drive material-dependent sounds — e.g. footsteps on
    grass vs metal vs wood produce different sounds.

    Args:
        material_path: Physical Material asset path (e.g. "/Game/Materials/PM_Grass")
        surface_type: Surface type name (e.g. "Grass", "Metal", "Wood", "SurfaceType1")
    """
    if err := _validate_asset_path(material_path, "material_path"):
        return _error(err)
    if not surface_type.strip():
        return _error("surface_type cannot be empty")

    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "set_physical_surface",
            "material_path": material_path,
            "surface_type": surface_type,
        })
        if result.get("status") == "error":
            return _error(result.get("message", "set_physical_surface failed"))
        warns = []
        if result.get("surface_index", -1) == 0:
            warns.append(
                "Surface resolved to Default (index 0). Footstep raycasts "
                "won't distinguish this material. Configure custom surface "
                "types in Project Settings > Physics > Physical Surface."
            )
        return _ok(result, warnings=warns or None)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def place_audio_volume(
    location: list[float],
    extent: list[float] | None = None,
    name: str = "MCP_AudioVolume",
    reverb_effect: str = "",
    priority: float = 0.0,
) -> str:
    """Place an AudioVolume actor — defines an ambient audio zone.

    When the player enters this volume, reverb/interior settings activate.
    Use for rooms, caves, outdoor areas with different acoustic properties.

    Args:
        location: World position as [x, y, z]
        extent: Half-size of the volume box as [x, y, z] (default [500,500,500])
        name: Label for the volume actor
        reverb_effect: Optional ReverbEffect asset path
        priority: Volume priority (higher = takes precedence when overlapping)
    """
    if not location or len(location) < 3:
        return _error("location must be [x, y, z]")

    conn = get_ue5_connection()
    try:
        cmd: dict[str, Any] = {
            "action": "place_audio_volume",
            "location": location,
            "name": name,
            "priority": priority,
        }
        if extent and len(extent) >= 3:
            cmd["extent"] = extent
        if reverb_effect:
            cmd["reverb_effect"] = reverb_effect
        result = conn.send_command(cmd)
        if result.get("status") == "error":
            return _error(result.get("message", "place_audio_volume failed"))
        return _ok(result)
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def spawn_blueprint_actor(
    blueprint_path: str,
    location: list[float] | None = None,
    rotation: list[float] | None = None,
    label: str = "",
) -> str:
    """Spawn an instance of a Blueprint actor into the editor level.

    Use this to place a character/object in the scene so you can see it
    while wiring up audio. Great for demos and iterative sound design —
    spawn it, open its Blueprint, wire sounds, compile, hear it live.

    Args:
        blueprint_path: Blueprint asset path (e.g. "/Game/Blueprints/BP_Creature")
        location: World position as [x, y, z] (default origin)
        rotation: Rotation as [pitch, yaw, roll] in degrees (default zero)
        label: Optional display label for the spawned actor
    """
    if err := _validate_asset_path(blueprint_path, "blueprint_path"):
        return _error(err)

    conn = get_ue5_connection()
    try:
        cmd: dict[str, Any] = {
            "action": "spawn_blueprint_actor",
            "blueprint_path": blueprint_path,
        }
        if location and len(location) >= 3:
            cmd["location"] = location
        if rotation and len(rotation) >= 3:
            cmd["rotation"] = rotation
        if label:
            cmd["label"] = label
        result = conn.send_command(cmd)
        if result.get("status") == "error":
            return _error(result.get("message", "spawn_blueprint_actor failed"))
        return _ok(result)
    except Exception as e:
        return _error(str(e))
