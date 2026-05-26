"""Tests for UE actor/camera staging tools."""

from __future__ import annotations

import json
import math

from ue_audio_mcp.tools.camera import (
    find_actor,
    focus_editor_camera,
    possess_pawn,
    set_actor_transform,
    set_view_target,
)


def test_find_actor_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("find_actor", {
        "status": "ok",
        "query": "Hero",
        "total": 1,
        "shown": 1,
        "actors": [{"label": "Hero", "class": "BP_Hero_C"}],
    })
    result = json.loads(find_actor("Hero", class_filter="Character", limit=10))
    assert result["status"] == "ok"
    assert result["total"] == 1
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "find_actor"
    assert cmd["query"] == "Hero"
    assert cmd["class_filter"] == "Character"


def test_find_actor_bad_limit(ue5_conn):
    result = json.loads(find_actor(limit=0))
    assert result["status"] == "error"
    assert "limit" in result["message"]


def test_set_actor_transform_location_rotation(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("set_actor_transform", {
        "status": "ok",
        "actor": {"label": "Hero"},
    })
    result = json.loads(set_actor_transform(
        "Hero",
        location=[100.0, 200.0, 50.0],
        rotation=[0.0, 90.0, 0.0],
    ))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "set_actor_transform"
    assert cmd["location"] == [100.0, 200.0, 50.0]
    assert cmd["rotation"] == [0.0, 90.0, 0.0]


def test_set_actor_transform_focus_camera(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("set_actor_transform", {
        "status": "ok",
        "actor": {"label": "Hero"},
    })
    mock_ue5_plugin.set_response("focus_editor_camera", {
        "status": "ok",
        "actor": {"label": "Hero"},
    })
    result = json.loads(set_actor_transform("Hero", location=[0.0, 0.0, 100.0], focus_camera=True))
    assert result["status"] == "ok"
    assert result["focused_camera"] is True
    assert [cmd["action"] for cmd in mock_ue5_plugin.commands[-2:]] == [
        "set_actor_transform",
        "focus_editor_camera",
    ]


def test_set_actor_transform_focus_camera_warning(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("set_actor_transform", {
        "status": "ok",
        "actor": {"label": "Hero"},
    })
    mock_ue5_plugin.set_response("focus_editor_camera", {
        "status": "error",
        "message": "No active viewport",
    })
    result = json.loads(set_actor_transform("Hero", location=[0.0, 0.0, 100.0], focus_camera=True))
    assert result["status"] == "ok"
    assert "focus_camera failed" in result["warnings"][0]


def test_set_actor_transform_rotation_only(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("set_actor_transform", {
        "status": "ok",
        "actor": {"label": "Hero"},
    })
    result = json.loads(set_actor_transform("Hero", rotation=[0.0, 180.0, 0.0]))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert "location" not in cmd
    assert cmd["rotation"] == [0.0, 180.0, 0.0]


def test_set_actor_transform_requires_change(ue5_conn):
    result = json.loads(set_actor_transform("Hero"))
    assert result["status"] == "error"
    assert "location" in result["message"]


def test_set_actor_transform_bad_location(ue5_conn):
    result = json.loads(set_actor_transform("Hero", location=[1.0, 2.0]))
    assert result["status"] == "error"
    assert "location" in result["message"]


def test_set_actor_transform_rejects_non_finite_and_bool(ue5_conn):
    bool_result = json.loads(set_actor_transform("Hero", location=[True, 0.0, 0.0]))
    assert bool_result["status"] == "error"
    assert "numbers" in bool_result["message"]

    nan_result = json.loads(set_actor_transform("Hero", location=[math.nan, 0.0, 0.0]))
    assert nan_result["status"] == "error"
    assert "numbers" in nan_result["message"]


def test_focus_editor_camera_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("focus_editor_camera", {
        "status": "ok",
        "actor": {"label": "Hero"},
        "active_viewport_only": True,
    })
    result = json.loads(focus_editor_camera("Hero"))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "focus_editor_camera"
    assert cmd["actor"] == "Hero"


def test_focus_editor_camera_empty_actor(ue5_conn):
    result = json.loads(focus_editor_camera(""))
    assert result["status"] == "error"
    assert "actor" in result["message"]


def test_set_view_target_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("set_view_target", {
        "status": "ok",
        "actor": {"label": "CameraRig"},
        "blend_time": 0.25,
    })
    result = json.loads(set_view_target("CameraRig", blend_time=0.25, player_index=0))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "set_view_target"
    assert cmd["blend_time"] == 0.25


def test_set_view_target_bad_blend(ue5_conn):
    result = json.loads(set_view_target("CameraRig", blend_time=-1.0))
    assert result["status"] == "error"
    assert "blend_time" in result["message"]


def test_set_view_target_empty_actor(ue5_conn):
    result = json.loads(set_view_target(""))
    assert result["status"] == "error"
    assert "actor" in result["message"]


def test_set_view_target_bad_player_index(ue5_conn):
    result = json.loads(set_view_target("CameraRig", player_index=-1))
    assert result["status"] == "error"
    assert "player_index" in result["message"]


def test_possess_pawn_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("possess_pawn", {
        "status": "ok",
        "actor": {"label": "Hero"},
        "player_index": 0,
    })
    result = json.loads(possess_pawn("Hero", set_view_target_on_possess=False))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "possess_pawn"
    assert cmd["set_view_target"] is False


def test_possess_pawn_empty_actor(ue5_conn):
    result = json.loads(possess_pawn(""))
    assert result["status"] == "error"
    assert "actor" in result["message"]


def test_possess_pawn_bad_player_index(ue5_conn):
    result = json.loads(possess_pawn("Hero", player_index=-1))
    assert result["status"] == "error"
    assert "player_index" in result["message"]
