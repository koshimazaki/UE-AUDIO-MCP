"""Shared helpers for tool response formatting."""

from __future__ import annotations

import json


def _ok(data: dict | None = None, warnings: list[str] | None = None) -> str:
    """Return a JSON success response.

    Strips any 'status' key from *data* so WAAPI responses cannot
    silently overwrite the ok/error signal.
    """
    result: dict = {"status": "ok"}
    if data:
        data.pop("status", None)
        result.update(data)
    if warnings:
        result["warnings"] = warnings
    return json.dumps(result)


def _error(message: str, data: dict | None = None) -> str:
    """Return a JSON error response, optionally with extra data fields."""
    result: dict = {"status": "error", "message": message}
    if data:
        data.pop("status", None)
        data.pop("message", None)
        result.update(data)
    return json.dumps(result)


def _check_ue5_result(result: dict) -> str | None:
    """Check a send_command() result dict for errors.

    Returns an error string if result has status=="error", else None.
    """
    if isinstance(result, dict) and result.get("status") == "error":
        return result.get("message", "Unknown plugin error")
    return None


def _validate_asset_path(path: str, param_name: str = "path") -> str | None:
    """Validate a UE asset path. Returns error string or None if valid."""
    if not path.strip():
        return f"{param_name} cannot be empty"
    if ".." in path:
        return f"{param_name} must not contain '..'"
    if not path.startswith("/Game/") and not path.startswith("/Engine/"):
        return f"{param_name} must start with /Game/ or /Engine/"
    return None
