"""Shared helpers for tool response formatting."""

from __future__ import annotations

import json


def _ok(data: dict | None = None) -> str:
    """Return a JSON success response.

    Strips any 'status' key from *data* so WAAPI responses cannot
    silently overwrite the ok/error signal.
    """
    result: dict = {"status": "ok"}
    if data:
        data.pop("status", None)
        result.update(data)
    return json.dumps(result)


def _error(message: str, data: dict | None = None) -> str:
    """Return a JSON error response, optionally with extra data fields."""
    result: dict = {"status": "error", "message": message}
    if data:
        data.pop("status", None)
        data.pop("message", None)
        result.update(data)
    return json.dumps(result)
