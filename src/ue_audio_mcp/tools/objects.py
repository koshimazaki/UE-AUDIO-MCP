"""Object CRUD tools — create, set property, set reference, import audio."""

from __future__ import annotations

import json
import logging

from ue_audio_mcp.connection import get_wwise_connection
from ue_audio_mcp.knowledge.wwise_types import (
    COMMON_PROPERTIES,
    COMMON_REFERENCES,
    IMPORT_OPERATIONS,
    NAME_CONFLICT_MODES,
    OBJECT_TYPES,
)
from ue_audio_mcp.server import mcp

log = logging.getLogger(__name__)

BATCH_LIMIT = 100


def _ok(data: dict | None = None) -> str:
    result = {"status": "ok"}
    if data:
        result.update(data)
    return json.dumps(result)


def _error(message: str) -> str:
    return json.dumps({"status": "error", "message": message})


@mcp.tool()
def wwise_create_object(
    parent_path: str,
    object_type: str,
    name: str,
    on_conflict: str = "merge",
) -> str:
    """Create a Wwise object in the hierarchy.

    Args:
        parent_path: Parent object path (backslash-separated, e.g. \\Actor-Mixer Hierarchy\\Default Work Unit)
        object_type: Wwise type (Sound, RandomSequenceContainer, Event, etc.)
        name: Object name
        on_conflict: Name conflict mode: merge, rename, replace, fail
    """
    if object_type not in OBJECT_TYPES:
        return _error(
            f"Invalid object_type '{object_type}'. "
            f"Valid types: {sorted(OBJECT_TYPES)}"
        )
    if on_conflict not in NAME_CONFLICT_MODES:
        return _error(
            f"Invalid on_conflict '{on_conflict}'. "
            f"Valid modes: {sorted(NAME_CONFLICT_MODES)}"
        )

    conn = get_wwise_connection()
    try:
        result = conn.call("ak.wwise.core.object.create", {
            "parent": parent_path,
            "type": object_type,
            "name": name,
            "onNameConflict": on_conflict,
        })
        return _ok({"id": result.get("id"), "name": result.get("name")})
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def wwise_set_property(object_path: str, property_name: str, value: str) -> str:
    """Set a property on a Wwise object.

    Args:
        object_path: Object path or GUID
        property_name: Property name (Volume, Pitch, Lowpass, IsLoopingEnabled, etc.)
        value: JSON-encoded value (number, bool, or string)
    """
    if property_name not in COMMON_PROPERTIES:
        log.warning("Property '%s' not in known list — passing through", property_name)

    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value

    conn = get_wwise_connection()
    try:
        conn.call("ak.wwise.core.object.setProperty", {
            "object": object_path,
            "property": property_name,
            "value": parsed_value,
        })
        return _ok({"object": object_path, "property": property_name, "value": parsed_value})
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def wwise_set_reference(object_path: str, reference: str, value: str) -> str:
    """Set a reference on a Wwise object (e.g. OutputBus, Attenuation).

    Args:
        object_path: Object path or GUID
        reference: Reference name (OutputBus, Attenuation, SwitchGroupOrStateGroup, etc.)
        value: Target object path or GUID
    """
    if reference not in COMMON_REFERENCES:
        log.warning("Reference '%s' not in known list — passing through", reference)

    conn = get_wwise_connection()
    try:
        conn.call("ak.wwise.core.object.setReference", {
            "object": object_path,
            "reference": reference,
            "value": value,
        })
        return _ok({"object": object_path, "reference": reference, "value": value})
    except Exception as e:
        return _error(str(e))


@mcp.tool()
def wwise_import_audio(
    audio_files: str,
    import_operation: str = "useExisting",
    language: str = "SFX",
) -> str:
    """Import audio files into Wwise.

    Args:
        audio_files: JSON array of objects with 'audioFile' and 'objectPath' keys.
            Example: [{"audioFile": "/path/to/shot.wav", "objectPath": "\\\\Actor-Mixer Hierarchy\\\\Default Work Unit\\\\<Sound>Shot_01"}]
        import_operation: createNew, useExisting, or replaceExisting
        language: Import language (default SFX)
    """
    if import_operation not in IMPORT_OPERATIONS:
        return _error(
            f"Invalid import_operation '{import_operation}'. "
            f"Valid: {sorted(IMPORT_OPERATIONS)}"
        )

    try:
        files = json.loads(audio_files)
    except json.JSONDecodeError:
        return _error(f"Invalid audio_files JSON: {audio_files}")

    if not isinstance(files, list):
        return _error("audio_files must be a JSON array")
    if len(files) > BATCH_LIMIT:
        return _error(f"Batch limit exceeded: {len(files)} > {BATCH_LIMIT}")

    conn = get_wwise_connection()
    try:
        result = conn.call("ak.wwise.core.audio.import", {
            "importOperation": import_operation,
            "default": {"importLanguage": language},
            "imports": files,
        })
        return _ok({"imported": len(files), "result": result})
    except Exception as e:
        return _error(str(e))
