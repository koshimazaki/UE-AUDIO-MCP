"""Shared test fixtures — mock WaapiClient for all tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

import ue_audio_mcp.connection as conn_module


class MockWaapiClient:
    """Mimics waapi-client's WaapiClient for testing."""

    def __init__(self) -> None:
        self._responses: dict[str, Any] = {
            "ak.wwise.core.getInfo": {
                "version": {"displayName": "Wwise 2024.1.0", "year": 2024, "major": 1},
                "isCommandLine": False,
                "platform": "Windows",
            },
        }
        self.calls: list[tuple[str, dict | None, dict | None]] = []

    def set_response(self, uri: str, response: Any) -> None:
        """Pre-program a response for a WAAPI URI."""
        self._responses[uri] = response

    def call(self, uri: str, args: dict | None = None, options: dict | None = None) -> Any:
        """Record the call and return pre-programmed response."""
        self.calls.append((uri, args, options))
        if uri in self._responses:
            return self._responses[uri]
        # Default: return empty dict with an id
        return {"id": "mock-guid-1234", "name": "MockObject"}

    def disconnect(self) -> None:
        pass


@pytest.fixture()
def mock_waapi() -> MockWaapiClient:
    """Provide a fresh MockWaapiClient."""
    return MockWaapiClient()


@pytest.fixture()
def wwise_conn(mock_waapi: MockWaapiClient, monkeypatch: pytest.MonkeyPatch):
    """Provide a WwiseConnection wired to the mock client.

    Resets the global singleton before and after each test.
    """
    # Reset singleton
    conn_module._connection = None

    connection = conn_module.get_wwise_connection()
    # Bypass real connect — inject mock client directly
    connection._client = mock_waapi
    yield connection

    # Cleanup
    connection._client = None
    conn_module._connection = None
