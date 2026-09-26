"""Tools on MCP SDK worker threads.

SDK v2 runs sync tool handlers off the event loop, on worker threads, while the
knowledge DB singleton is opened on the main thread by the server lifespan.
"""

from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import anyio
import pytest
from mcp.client import Client

import ue_audio_mcp.server as server_module
import ue_audio_mcp.session_log as session_log_module
from ue_audio_mcp.knowledge.db import KnowledgeDB
from ue_audio_mcp.session_log import SessionLogger
from ue_audio_mcp.tools.utils import logged_tool

OK = '{"status": "ok"}'


class _NullLogger:
    def log_tool_call(self, *args, **kwargs) -> None:
        pass


class _OfflineConnection:
    """Stands in for Wwise/UE5 so the lifespan never touches the network."""

    def connect(self):
        raise ConnectionError("offline")

    def disconnect(self) -> None:
        pass


@pytest.fixture()
def null_logger(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(session_log_module, "_logger", _NullLogger())


def test_knowledge_db_usable_from_another_thread():
    db = KnowledgeDB(":memory:")  # opened here, like the server lifespan does
    db.insert_node({
        "name": "Sine",
        "category": "Generators",
        "description": "Sine wave oscillator",
        "inputs": [],
        "outputs": [{"name": "Audio", "type": "Audio"}],
        "tags": ["oscillator"],
        "complexity": 1,
    })
    with ThreadPoolExecutor(max_workers=1) as pool:
        nodes = pool.submit(db.query_nodes, name="Sine").result()
    assert nodes[0]["name"] == "Sine"
    db.close()


def test_logged_tool_calls_never_overlap(null_logger):
    active = peak = 0
    guard = threading.Lock()

    @logged_tool
    def slow_tool(i: int) -> str:
        nonlocal active, peak
        with guard:
            active += 1
            peak = max(peak, active)
        time.sleep(0.01)
        with guard:
            active -= 1
        return OK

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(slow_tool, range(16)))

    assert results == [OK] * 16
    assert peak == 1


def test_nested_logged_tool_call_does_not_deadlock(null_logger):
    @logged_tool
    def inner() -> str:
        return OK

    @logged_tool
    def outer() -> str:
        return inner()

    results: list[str] = []
    worker = threading.Thread(target=lambda: results.append(outer()), daemon=True)
    worker.start()
    worker.join(timeout=5)
    assert not worker.is_alive(), "nested logged_tool call deadlocked"
    assert results == [OK]


def test_concurrent_tool_calls_through_mcp_client(knowledge_db, tmp_path, monkeypatch):
    monkeypatch.setattr(session_log_module, "_logger", SessionLogger(str(tmp_path)))
    monkeypatch.setattr(server_module, "get_wwise_connection", _OfflineConnection)
    monkeypatch.setattr(server_module, "get_ue5_connection", _OfflineConnection)

    async def run() -> list:
        results = []
        with anyio.fail_after(30):
            async with Client(server_module.mcp) as client:

                async def call(name: str, args: dict) -> None:
                    results.append(await client.call_tool(name, args))

                async with anyio.create_task_group() as tg:
                    for _ in range(4):
                        tg.start_soon(call, "bp_search", {"query": "play sound"})
                        tg.start_soon(call, "audit_session_stats", {})
        return results

    results = anyio.run(run)

    assert len(results) == 8
    for res in results:
        assert not res.is_error, res.content[0].text
        assert json.loads(res.content[0].text)["status"] == "ok"
