"""Tests for World Audio Setup tools — place_anim_notify, spawn_audio_emitter, etc."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.world_setup import (
    place_anim_notify,
    spawn_audio_emitter,
    import_sound_file,
    set_physical_surface,
    place_audio_volume,
)


# -- place_anim_notify -------------------------------------------------------

def test_place_anim_notify_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("place_anim_notify", {
        "status": "ok",
        "animation": "/Game/Anims/Walk",
        "notify_name": "Footstep",
        "time": 0.3,
        "animation_length": 1.2,
    })
    result = json.loads(place_anim_notify(
        animation_path="/Game/Anims/Walk",
        time=0.3,
        sound="/Game/Audio/Footstep",
        notify_name="Footstep",
    ))
    assert result["status"] == "ok"
    assert result["notify_name"] == "Footstep"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "place_anim_notify"
    assert cmd["time"] == 0.3
    assert cmd["sound"] == "/Game/Audio/Footstep"


def test_place_anim_notify_empty_path(ue5_conn):
    result = json.loads(place_anim_notify(animation_path="", time=0.5))
    assert result["status"] == "error"
    assert "empty" in result["message"]


def test_place_anim_notify_path_traversal(ue5_conn):
    result = json.loads(place_anim_notify(
        animation_path="/Game/" + ".." + "/" + ".." + "/etc/passwd", time=0.5,
    ))
    assert result["status"] == "error"
    assert ".." in result["message"]


def test_place_anim_notify_bad_prefix(ue5_conn):
    result = json.loads(place_anim_notify(
        animation_path="/Bad/Anims/Walk", time=0.5,
    ))
    assert result["status"] == "error"
    assert "/Game/" in result["message"]


def test_place_anim_notify_negative_time(ue5_conn):
    result = json.loads(place_anim_notify(
        animation_path="/Game/Anims/Walk", time=-1.0,
    ))
    assert result["status"] == "error"
    assert "time" in result["message"].lower()


def test_place_anim_notify_no_sound_warns(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("place_anim_notify", {
        "status": "ok",
        "animation": "/Game/Anims/Walk",
        "notify_name": "Step",
        "time": 0.5,
    })
    result = json.loads(place_anim_notify(
        animation_path="/Game/Anims/Walk", time=0.5, notify_name="Step",
    ))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert "sound" not in cmd
    assert "warnings" in result
    assert any("silence" in w for w in result["warnings"])


def test_place_anim_notify_with_sound_no_warning(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("place_anim_notify", {
        "status": "ok",
        "animation": "/Game/Anims/Walk",
        "notify_name": "Footstep",
        "time": 0.3,
    })
    result = json.loads(place_anim_notify(
        animation_path="/Game/Anims/Walk", time=0.3,
        sound="/Game/Audio/Step",
    ))
    assert result["status"] == "ok"
    assert "warnings" not in result


def test_place_anim_notify_not_connected():
    import ue_audio_mcp.ue5_connection as ue5_module
    ue5_module._connection = None
    result = json.loads(place_anim_notify(
        animation_path="/Game/Anims/Walk", time=0.5,
    ))
    assert result["status"] == "error"
    assert "Not connected" in result["message"]
    ue5_module._connection = None


# -- spawn_audio_emitter -----------------------------------------------------

def test_spawn_emitter_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("spawn_audio_emitter", {
        "status": "ok",
        "name": "Campfire",
        "sound": "/Game/Audio/Fire",
        "location": [100.0, 200.0, 0.0],
        "auto_play": True,
    })
    result = json.loads(spawn_audio_emitter(
        sound="/Game/Audio/Fire",
        location=[100.0, 200.0, 0.0],
        name="Campfire",
    ))
    assert result["status"] == "ok"
    assert result["name"] == "Campfire"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "spawn_audio_emitter"
    assert cmd["location"] == [100.0, 200.0, 0.0]


def test_spawn_emitter_empty_sound(ue5_conn):
    result = json.loads(spawn_audio_emitter(sound="", location=[0, 0, 0]))
    assert result["status"] == "error"
    assert "empty" in result["message"]


def test_spawn_emitter_bad_prefix(ue5_conn):
    result = json.loads(spawn_audio_emitter(
        sound="/tmp/local_file", location=[0, 0, 0],
    ))
    assert result["status"] == "error"
    assert "/Game/" in result["message"]


def test_spawn_emitter_bad_location(ue5_conn):
    result = json.loads(spawn_audio_emitter(
        sound="/Game/Audio/Fire", location=[1.0, 2.0],
    ))
    assert result["status"] == "error"
    assert "location" in result["message"].lower()


def test_spawn_emitter_auto_play_false(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("spawn_audio_emitter", {
        "status": "ok", "auto_play": False,
    })
    result = json.loads(spawn_audio_emitter(
        sound="/Game/Audio/Hum", location=[0, 0, 0], auto_play=False,
    ))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["auto_play"] is False


# -- import_sound_file -------------------------------------------------------

def test_import_sound_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("import_sound_file", {
        "status": "ok",
        "asset_path": "/Game/Audio/SFX/bang",
        "asset_name": "bang",
        "source_file": "/tmp/bang.wav",
        "format": "wav",
    })
    result = json.loads(import_sound_file(
        file_path="/tmp/bang.wav",
        dest_folder="/Game/Audio/SFX",
    ))
    assert result["status"] == "ok"
    assert result["asset_name"] == "bang"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "import_sound_file"


def test_import_sound_empty_path(ue5_conn):
    result = json.loads(import_sound_file(file_path="", dest_folder="/Game/Audio"))
    assert result["status"] == "error"
    assert "empty" in result["message"]


def test_import_sound_empty_dest(ue5_conn):
    result = json.loads(import_sound_file(file_path="/tmp/a.wav", dest_folder=""))
    assert result["status"] == "error"
    assert "empty" in result["message"]


def test_import_sound_path_traversal(ue5_conn):
    bad_path = "/tmp/" + ".." + "/" + ".." + "/etc/passwd"
    result = json.loads(import_sound_file(
        file_path=bad_path,
        dest_folder="/Game/Audio",
    ))
    assert result["status"] == "error"
    assert ".." in result["message"]


# -- set_physical_surface ----------------------------------------------------

def test_set_surface_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("set_physical_surface", {
        "status": "ok",
        "material_path": "/Game/Materials/PM_Grass",
        "surface_type": "Grass",
        "surface_enum": "Grass",
        "surface_index": 1,
        "created": False,
    })
    result = json.loads(set_physical_surface(
        material_path="/Game/Materials/PM_Grass",
        surface_type="Grass",
    ))
    assert result["status"] == "ok"
    assert result["surface_type"] == "Grass"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "set_physical_surface"


def test_set_surface_empty_path(ue5_conn):
    result = json.loads(set_physical_surface(material_path="", surface_type="Grass"))
    assert result["status"] == "error"
    assert "empty" in result["message"]


def test_set_surface_empty_type(ue5_conn):
    result = json.loads(set_physical_surface(
        material_path="/Game/Materials/PM_Grass", surface_type="",
    ))
    assert result["status"] == "error"
    assert "empty" in result["message"]


def test_set_surface_path_traversal(ue5_conn):
    bad_path = "/Game/" + ".." + "/Materials/PM_Evil"
    result = json.loads(set_physical_surface(
        material_path=bad_path, surface_type="Metal",
    ))
    assert result["status"] == "error"
    assert ".." in result["message"]


def test_set_surface_default_warns(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("set_physical_surface", {
        "status": "ok",
        "material_path": "/Game/Materials/PM_Test",
        "surface_type": "Default",
        "surface_enum": "Default",
        "surface_index": 0,
        "created": False,
    })
    result = json.loads(set_physical_surface(
        material_path="/Game/Materials/PM_Test",
        surface_type="Default",
    ))
    assert result["status"] == "ok"
    assert "warnings" in result
    assert any("Default" in w for w in result["warnings"])


def test_set_surface_non_default_no_warning(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("set_physical_surface", {
        "status": "ok",
        "material_path": "/Game/Materials/PM_Grass",
        "surface_type": "Grass",
        "surface_index": 1,
        "created": False,
    })
    result = json.loads(set_physical_surface(
        material_path="/Game/Materials/PM_Grass",
        surface_type="Grass",
    ))
    assert result["status"] == "ok"
    assert "warnings" not in result


def test_set_surface_creates_new(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("set_physical_surface", {
        "status": "ok",
        "material_path": "/Game/Materials/PM_NewMetal",
        "surface_type": "Metal",
        "created": True,
    })
    result = json.loads(set_physical_surface(
        material_path="/Game/Materials/PM_NewMetal",
        surface_type="Metal",
    ))
    assert result["status"] == "ok"
    assert result["created"] is True


# -- place_audio_volume ------------------------------------------------------

def test_place_volume_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("place_audio_volume", {
        "status": "ok",
        "name": "CaveReverb",
        "location": [1000, 2000, 0],
        "extent": [500, 500, 300],
        "priority": 1.0,
    })
    result = json.loads(place_audio_volume(
        location=[1000.0, 2000.0, 0.0],
        extent=[500.0, 500.0, 300.0],
        name="CaveReverb",
        priority=1.0,
    ))
    assert result["status"] == "ok"
    assert result["name"] == "CaveReverb"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "place_audio_volume"
    assert cmd["extent"] == [500.0, 500.0, 300.0]


def test_place_volume_bad_location(ue5_conn):
    result = json.loads(place_audio_volume(location=[1.0]))
    assert result["status"] == "error"
    assert "location" in result["message"].lower()


def test_place_volume_defaults(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("place_audio_volume", {
        "status": "ok",
        "name": "MCP_AudioVolume",
        "location": [0, 0, 0],
        "extent": [500, 500, 500],
        "priority": 0.0,
    })
    result = json.loads(place_audio_volume(location=[0, 0, 0]))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["name"] == "MCP_AudioVolume"
    assert cmd["priority"] == 0.0
    assert "extent" not in cmd  # default handled server-side


def test_place_volume_with_reverb(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("place_audio_volume", {
        "status": "ok",
        "reverb_effect": "/Game/Audio/Reverb/Cave",
    })
    result = json.loads(place_audio_volume(
        location=[0, 0, 0],
        reverb_effect="/Game/Audio/Reverb/Cave",
    ))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["reverb_effect"] == "/Game/Audio/Reverb/Cave"


# -- spawn_blueprint_actor ---------------------------------------------------

from ue_audio_mcp.tools.world_setup import spawn_blueprint_actor


def test_spawn_actor_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("spawn_blueprint_actor", {
        "status": "ok",
        "actor_label": "MyCreature",
        "actor_class": "BP_Creature_C",
        "blueprint": "/Game/creature/BP_Creature",
        "location": [100.0, 200.0, 0.0],
        "rotation": [0.0, 90.0, 0.0],
    })
    result = json.loads(spawn_blueprint_actor(
        blueprint_path="/Game/creature/BP_Creature",
        location=[100.0, 200.0, 0.0],
        rotation=[0.0, 90.0, 0.0],
        label="MyCreature",
    ))
    assert result["status"] == "ok"
    assert result["actor_label"] == "MyCreature"
    assert result["actor_class"] == "BP_Creature_C"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "spawn_blueprint_actor"
    assert cmd["location"] == [100.0, 200.0, 0.0]
    assert cmd["rotation"] == [0.0, 90.0, 0.0]
    assert cmd["label"] == "MyCreature"


def test_spawn_actor_empty_path(ue5_conn):
    result = json.loads(spawn_blueprint_actor(blueprint_path=""))
    assert result["status"] == "error"
    assert "empty" in result["message"]


def test_spawn_actor_path_traversal(ue5_conn):
    bad = "/Game/" + ".." + "/Evil"
    result = json.loads(spawn_blueprint_actor(blueprint_path=bad))
    assert result["status"] == "error"
    assert ".." in result["message"]


def test_spawn_actor_defaults(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("spawn_blueprint_actor", {
        "status": "ok",
        "actor_label": "BP_Creature",
        "actor_class": "BP_Creature_C",
        "blueprint": "/Game/creature/BP_Creature",
        "location": [0, 0, 0],
        "rotation": [0, 0, 0],
    })
    result = json.loads(spawn_blueprint_actor(
        blueprint_path="/Game/creature/BP_Creature",
    ))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert "location" not in cmd  # default handled server-side
    assert "rotation" not in cmd
    assert "label" not in cmd


def test_spawn_actor_with_location_only(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("spawn_blueprint_actor", {
        "status": "ok",
        "location": [500, 0, 100],
    })
    result = json.loads(spawn_blueprint_actor(
        blueprint_path="/Game/BP_Test",
        location=[500.0, 0.0, 100.0],
    ))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["location"] == [500.0, 0.0, 100.0]
    assert "rotation" not in cmd


def test_spawn_actor_not_connected():
    import ue_audio_mcp.ue5_connection as ue5_module
    ue5_module._connection = None
    result = json.loads(spawn_blueprint_actor(
        blueprint_path="/Game/BP_Test",
    ))
    assert result["status"] == "error"
    assert "Not connected" in result["message"]
    ue5_module._connection = None
