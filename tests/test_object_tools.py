"""Tests for object CRUD tools."""

from __future__ import annotations

import json

from ue_audio_mcp.tools.objects import (
    wwise_create_object,
    wwise_import_audio,
    wwise_set_property,
    wwise_set_reference,
)


def _parse(result: str) -> dict:
    return json.loads(result)


def test_create_object(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.object.create", {"id": "guid-1", "name": "MySound"})
    result = _parse(wwise_create_object(
        "\\Actor-Mixer Hierarchy\\Default Work Unit",
        "Sound",
        "MySound",
    ))
    assert result["status"] == "ok"
    assert result["id"] == "guid-1"
    # Verify the call was made with onNameConflict
    call_args = mock_waapi.calls[-1][1]
    assert call_args["onNameConflict"] == "merge"


def test_create_object_invalid_type(wwise_conn):
    result = _parse(wwise_create_object(
        "\\Actor-Mixer Hierarchy\\Default Work Unit",
        "InvalidType",
        "Foo",
    ))
    assert result["status"] == "error"
    assert "Invalid object_type" in result["message"]


def test_create_object_invalid_conflict(wwise_conn):
    result = _parse(wwise_create_object(
        "\\Actor-Mixer Hierarchy\\Default Work Unit",
        "Sound",
        "Foo",
        on_conflict="invalid",
    ))
    assert result["status"] == "error"
    assert "Invalid on_conflict" in result["message"]


def test_set_property(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.object.setProperty", None)
    result = _parse(wwise_set_property(
        "\\Actor-Mixer Hierarchy\\Default Work Unit\\MySound",
        "Volume",
        "-3.0",
    ))
    assert result["status"] == "ok"
    assert result["value"] == -3.0


def test_set_property_bool(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.object.setProperty", None)
    result = _parse(wwise_set_property(
        "\\Actor-Mixer Hierarchy\\Default Work Unit\\MySound",
        "IsLoopingEnabled",
        "true",
    ))
    assert result["status"] == "ok"
    assert result["value"] is True


def test_set_reference(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.object.setReference", None)
    result = _parse(wwise_set_reference(
        "\\Actor-Mixer Hierarchy\\Default Work Unit\\MySound",
        "OutputBus",
        "\\Master-Mixer Hierarchy\\Default Work Unit\\Master Audio Bus\\SFX",
    ))
    assert result["status"] == "ok"
    assert result["reference"] == "OutputBus"


def test_import_audio(wwise_conn, mock_waapi):
    mock_waapi.set_response("ak.wwise.core.audio.import", {"objects": []})
    files = json.dumps([{
        "audioFile": "/path/to/shot.wav",
        "objectPath": "\\Actor-Mixer Hierarchy\\Default Work Unit\\<Sound>Shot_01",
    }])
    result = _parse(wwise_import_audio(files))
    assert result["status"] == "ok"
    assert result["imported"] == 1


def test_import_audio_invalid_json(wwise_conn):
    result = _parse(wwise_import_audio("not-json"))
    assert result["status"] == "error"
    assert "Invalid audio_files JSON" in result["message"]


def test_import_audio_batch_limit(wwise_conn):
    files = json.dumps([{"audioFile": f"/f{i}.wav", "objectPath": f"\\p\\<Sound>S{i}"} for i in range(101)])
    result = _parse(wwise_import_audio(files))
    assert result["status"] == "error"
    assert "Batch limit exceeded" in result["message"]


def test_import_audio_invalid_operation(wwise_conn):
    result = _parse(wwise_import_audio("[]", import_operation="badMode"))
    assert result["status"] == "error"
    assert "Invalid import_operation" in result["message"]
