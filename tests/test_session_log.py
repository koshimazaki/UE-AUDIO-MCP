"""Tests for session logging — SessionLogger, logged_tool, audit tools."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import ue_audio_mcp.session_log as sl_module
from ue_audio_mcp.session_log import SessionLogger, get_session_logger


@pytest.fixture()
def session_logger(tmp_path, knowledge_db):
    """Provide a fresh SessionLogger writing to tmp_path, reset singleton."""
    sl_module._logger = None
    logger = SessionLogger(log_dir=str(tmp_path / "logs"))
    # Point DB to the test knowledge_db
    logger._db = knowledge_db
    sl_module._logger = logger
    yield logger
    sl_module._logger = None


class TestSessionLifecycle:
    def test_start_session_returns_id(self, session_logger):
        sid = session_logger.start_session("TestProject")
        assert len(sid) == 12
        assert session_logger.session_id == sid

    def test_end_session_clears_id(self, session_logger):
        session_logger.start_session()
        session_logger.end_session()
        assert session_logger.session_id == ""

    def test_end_session_noop_when_not_started(self, session_logger):
        session_logger.end_session()  # should not raise


class TestLogMethods:
    def test_log_tool_call_writes_sqlite(self, session_logger, knowledge_db):
        session_logger.start_session("proj")
        session_logger.log_tool_call("ms_search_nodes", {"query": "sine"}, "ok", 12.5)

        rows = knowledge_db._fetch(
            "SELECT * FROM session_logs WHERE event_type = 'tool_call'"
        )
        assert len(rows) == 1
        assert rows[0]["tool_name"] == "ms_search_nodes"
        assert rows[0]["result_status"] == "ok"
        assert rows[0]["duration_ms"] == pytest.approx(12.5)

    def test_log_waapi_call_writes_sqlite(self, session_logger, knowledge_db):
        session_logger.start_session()
        session_logger.log_waapi_call(
            "ak.wwise.core.getInfo", {"arg": 1}, "ok", 5.0
        )

        rows = knowledge_db._fetch(
            "SELECT * FROM session_logs WHERE event_type = 'waapi_call'"
        )
        assert len(rows) == 1
        assert rows[0]["uri"] == "ak.wwise.core.getInfo"
        assert rows[0]["event_type"] == "waapi_call"

    def test_log_tcp_command_writes_sqlite(self, session_logger, knowledge_db):
        session_logger.start_session()
        session_logger.log_tcp_command("ping", {"action": "ping"}, "ok", 2.0)

        rows = knowledge_db._fetch(
            "SELECT * FROM session_logs WHERE event_type = 'tcp_command'"
        )
        assert len(rows) == 1
        assert rows[0]["action"] == "ping"

    def test_log_with_error(self, session_logger, knowledge_db):
        session_logger.start_session()
        session_logger.log_tool_call(
            "wwise_connect", {}, "error", 100.0, "Connection refused"
        )

        rows = knowledge_db._fetch(
            "SELECT * FROM session_logs WHERE result_status = 'error'"
        )
        assert len(rows) == 1
        assert rows[0]["error_message"] == "Connection refused"


class TestJSONLOutput:
    def test_jsonl_file_created(self, session_logger, tmp_path):
        session_logger.start_session("proj")
        session_logger.log_tool_call("test_tool", {"x": 1}, "ok", 1.0)

        log_dir = tmp_path / "logs"
        files = list(log_dir.glob("session_*.jsonl"))
        assert len(files) == 1

        lines = files[0].read_text(encoding="utf-8").strip().split("\n")
        # session_start + tool_call = 2 lines
        assert len(lines) == 2
        record = json.loads(lines[1])
        assert record["tool"] == "test_tool"
        assert record["status"] == "ok"

    def test_jsonl_appends(self, session_logger, tmp_path):
        session_logger.start_session()
        session_logger.log_tool_call("t1", {}, "ok", 1.0)
        session_logger.log_tool_call("t2", {}, "ok", 2.0)

        files = list((tmp_path / "logs").glob("session_*.jsonl"))
        lines = files[0].read_text(encoding="utf-8").strip().split("\n")
        # session_start + 2 tool calls
        assert len(lines) == 3


class TestSanitization:
    def test_truncate_large_string(self):
        payload = {"big": "x" * 10000}
        clean = SessionLogger._sanitize_payload(payload)
        assert len(clean["big"]) < 5000
        assert "truncated" in clean["big"]

    def test_strip_binary_keys(self):
        payload = {"name": "test", "binary": b"data", "audio_data": "raw"}
        clean = SessionLogger._sanitize_payload(payload)
        assert clean["binary"] == "<binary>"
        assert clean["audio_data"] == "<binary>"
        assert clean["name"] == "test"

    def test_none_payload(self):
        assert SessionLogger._sanitize_payload(None) == {}

    def test_truncate_large_dict(self):
        payload = {"big_list": list(range(2000))}
        clean = SessionLogger._sanitize_payload(payload)
        if isinstance(clean["big_list"], str):
            assert "truncated" in clean["big_list"]


class TestRotation:
    def test_rotate_deletes_old_files(self, session_logger, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        # Create an "old" file
        old_file = log_dir / "session_2020-01-01.jsonl"
        old_file.write_text('{"test": true}\n', encoding="utf-8")
        # Create a "recent" file
        recent_file = log_dir / "session_2099-12-31.jsonl"
        recent_file.write_text('{"test": true}\n', encoding="utf-8")

        deleted = session_logger.rotate_logs(max_age_days=30)
        assert deleted == 1
        assert not old_file.exists()
        assert recent_file.exists()


class TestLoggedToolDecorator:
    def test_decorator_logs_successful_call(self, session_logger, knowledge_db):
        from ue_audio_mcp.tools.utils import logged_tool

        @logged_tool
        def fake_tool(name: str, count: int = 5) -> str:
            return json.dumps({"status": "ok", "name": name})

        session_logger.start_session()
        result = fake_tool("test", count=3)

        parsed = json.loads(result)
        assert parsed["status"] == "ok"

        rows = knowledge_db._fetch(
            "SELECT * FROM session_logs WHERE tool_name = 'fake_tool'"
        )
        assert len(rows) == 1
        assert rows[0]["result_status"] == "ok"
        params = rows[0]["params"]
        if isinstance(params, str):
            params = json.loads(params)
        assert params["name"] == "test"
        assert params["count"] == 3

    def test_decorator_logs_error_status(self, session_logger, knowledge_db):
        from ue_audio_mcp.tools.utils import logged_tool

        @logged_tool
        def fail_tool() -> str:
            return json.dumps({"status": "error", "message": "boom"})

        session_logger.start_session()
        fail_tool()

        rows = knowledge_db._fetch(
            "SELECT * FROM session_logs WHERE tool_name = 'fail_tool'"
        )
        assert len(rows) == 1
        assert rows[0]["result_status"] == "error"
        assert rows[0]["error_message"] == "boom"

    def test_decorator_logs_exception(self, session_logger, knowledge_db):
        from ue_audio_mcp.tools.utils import logged_tool

        @logged_tool
        def crash_tool() -> str:
            raise ValueError("kaboom")

        session_logger.start_session()
        with pytest.raises(ValueError, match="kaboom"):
            crash_tool()

        rows = knowledge_db._fetch(
            "SELECT * FROM session_logs WHERE tool_name = 'crash_tool'"
        )
        assert len(rows) == 1
        assert rows[0]["result_status"] == "error"
        assert "kaboom" in rows[0]["error_message"]


class TestAuditTools:
    def test_audit_history(self, session_logger, knowledge_db):
        session_logger.start_session("proj")
        session_logger.log_tool_call("tool_a", {}, "ok", 10.0)
        session_logger.log_tool_call("tool_b", {}, "error", 20.0, "fail")

        from ue_audio_mcp.tools.audit import audit_history
        result = json.loads(audit_history.__wrapped__(limit=10))
        assert result["status"] == "ok"
        assert result["count"] >= 2

    def test_audit_history_summary(self, session_logger, knowledge_db):
        session_logger.start_session("proj")
        session_logger.log_tool_call("tool_a", {}, "ok", 10.0)

        from ue_audio_mcp.tools.audit import audit_history
        result = json.loads(audit_history.__wrapped__(summary_only=True))
        assert result["status"] == "ok"
        assert len(result["sessions"]) >= 1

    def test_audit_session_stats(self, session_logger, knowledge_db):
        session_logger.start_session()
        session_logger.log_tool_call("t1", {}, "ok", 5.0)
        session_logger.log_tool_call("t2", {}, "error", 3.0, "err")

        from ue_audio_mcp.tools.audit import audit_session_stats
        result = json.loads(audit_session_stats.__wrapped__())
        assert result["status"] == "ok"
        assert result["total_events"] >= 2
        assert result["total_sessions"] >= 1
        assert "top_tools" in result


class TestGetSessionLoggerSingleton:
    def test_singleton(self, tmp_path):
        sl_module._logger = None
        a = get_session_logger(str(tmp_path))
        b = get_session_logger()
        assert a is b
        sl_module._logger = None
