"""Shared test fixtures — mock WaapiClient for all tests."""

from __future__ import annotations

from typing import Any

import pytest

import ue_audio_mcp.connection as conn_module
import ue_audio_mcp.knowledge.db as db_module
import ue_audio_mcp.ue5_connection as ue5_module


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


class MockUE5Plugin:
    """Mimics the UE5 C++ plugin TCP server for testing."""

    def __init__(self) -> None:
        self._responses: dict[str, Any] = {
            "ping": {
                "status": "ok",
                "engine": "UnrealEngine",
                "version": "5.4.0",
                "project": "TestProject",
                "features": ["MetaSounds", "AudioLink"],
            },
        }
        self.commands: list[dict] = []

    def set_response(self, action: str, response: Any) -> None:
        """Pre-program a response for a command action."""
        self._responses[action] = response

    def send_command(self, command: dict) -> dict:
        """Record the command and return pre-programmed response."""
        self.commands.append(command)
        action = command.get("action", "")
        if action in self._responses:
            return self._responses[action]
        return {"status": "ok", "action": action}


@pytest.fixture()
def mock_ue5_plugin() -> MockUE5Plugin:
    """Provide a fresh MockUE5Plugin."""
    return MockUE5Plugin()


@pytest.fixture()
def ue5_conn(mock_ue5_plugin: MockUE5Plugin):
    """Provide a UE5PluginConnection wired to the mock plugin.

    Resets the global singleton before and after each test.
    """
    ue5_module._connection = None
    connection = ue5_module.get_ue5_connection()
    # Bypass real TCP — inject mock's send_command directly
    connection.send_command = mock_ue5_plugin.send_command
    # Mark as "connected" by setting a truthy _sock
    connection._sock = True  # type: ignore[assignment]
    yield connection
    connection._sock = None
    ue5_module._connection = None


@pytest.fixture()
def knowledge_db():
    """Provide a seeded in-memory KnowledgeDB for testing.

    Resets the global singleton before and after each test.
    """
    from ue_audio_mcp.knowledge.db import KnowledgeDB
    from ue_audio_mcp.knowledge.seed import seed_database

    db_module._db = None
    db = KnowledgeDB(":memory:")
    seed_database(db)
    db_module._db = db
    yield db
    db.close()
    db_module._db = None
