"""Session logging — dual JSONL + SQLite audit trail for every MCP call.

Every tool invocation, WAAPI call, and TCP command is recorded with timing,
status, and sanitised parameters.  JSONL files live in ~/.ue-audio-mcp/logs/
(one per day, append mode).  SQLite rows go into the ``session_logs`` table
of the knowledge DB.

Usage::

    logger = get_session_logger()
    logger.start_session("MyProject")
    logger.log_tool_call("ms_search_nodes", {"query": "sine"}, "ok", 12.3)
    logger.end_session()
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

_LOG_DIR = os.path.expanduser("~/.ue-audio-mcp/logs")
_MAX_FIELD_SIZE = 4096  # truncate any single field beyond 4 KB
_BINARY_KEYS = {"binary", "audio_data", "waveform", "thumbnail", "raw_bytes"}
_ROTATION_DAYS = 30

_logger: SessionLogger | None = None


class SessionLogger:
    """Dual-output session logger (JSONL file + SQLite)."""

    def __init__(self, log_dir: str = _LOG_DIR) -> None:
        self._log_dir = log_dir
        self._session_id: str = ""
        self._project_context: str = ""
        self._start_time: float = 0.0
        self._db: Any = None  # lazy — avoids circular import

    # -- lifecycle ----------------------------------------------------------

    def start_session(self, project_context: str = "") -> str:
        """Begin a new session.  Returns the session id."""
        self._session_id = uuid.uuid4().hex[:12]
        self._project_context = project_context
        self._start_time = time.monotonic()
        self._write_event("session_start", tool_name="", action="start")
        return self._session_id

    def end_session(self) -> None:
        """Close the current session."""
        if not self._session_id:
            return
        elapsed = (time.monotonic() - self._start_time) * 1000
        self._write_event(
            "session_end", tool_name="", action="end", duration_ms=elapsed
        )
        self._session_id = ""

    @property
    def session_id(self) -> str:
        return self._session_id

    # -- public log methods ------------------------------------------------

    def log_tool_call(
        self,
        tool_name: str,
        params: dict | None = None,
        result_status: str = "",
        duration_ms: float = 0.0,
        error_message: str = "",
    ) -> None:
        self._write_event(
            "tool_call",
            tool_name=tool_name,
            params=params,
            result_status=result_status,
            duration_ms=duration_ms,
            error_message=error_message,
        )

    def log_waapi_call(
        self,
        uri: str,
        args: dict | None = None,
        result_status: str = "",
        duration_ms: float = 0.0,
        error_message: str = "",
    ) -> None:
        self._write_event(
            "waapi_call",
            uri=uri,
            params=args,
            result_status=result_status,
            duration_ms=duration_ms,
            error_message=error_message,
        )

    def log_tcp_command(
        self,
        action: str,
        params: dict | None = None,
        result_status: str = "",
        duration_ms: float = 0.0,
        error_message: str = "",
    ) -> None:
        self._write_event(
            "tcp_command",
            action=action,
            params=params,
            result_status=result_status,
            duration_ms=duration_ms,
            error_message=error_message,
        )

    # -- rotation ----------------------------------------------------------

    def rotate_logs(self, max_age_days: int = _ROTATION_DAYS) -> int:
        """Delete JSONL files and DB rows older than *max_age_days*.
        Returns number of files deleted."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        deleted = 0

        # JSONL files
        log_path = Path(self._log_dir)
        if log_path.is_dir():
            for f in log_path.glob("session_*.jsonl"):
                # filename: session_YYYY-MM-DD.jsonl
                date_part = f.stem.replace("session_", "")
                if date_part < cutoff_str:
                    try:
                        f.unlink()
                        deleted += 1
                    except OSError:
                        pass

        # SQLite rows
        try:
            db = self._get_db()
            if db is not None:
                try:
                    db._conn.execute(
                        "DELETE FROM session_logs WHERE timestamp < ?",
                        (cutoff_str,),
                    )
                    db._conn.commit()
                except Exception:
                    try:
                        db._conn.rollback()
                    except Exception:
                        pass
                    raise
        except Exception as exc:
            log.debug("SQLite log rotation failed: %s", exc)

        return deleted

    # -- internal ----------------------------------------------------------

    def _write_event(
        self,
        event_type: str,
        *,
        tool_name: str = "",
        action: str = "",
        uri: str = "",
        params: dict | None = None,
        result_status: str = "",
        duration_ms: float = 0.0,
        error_message: str = "",
    ) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        sanitised = self._sanitize_payload(params) if params else {}
        params_json = json.dumps(sanitised)

        # -- JSONL --
        try:
            Path(self._log_dir).mkdir(parents=True, exist_ok=True)
            day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            filepath = os.path.join(self._log_dir, f"session_{day}.jsonl")
            record = {
                "ts": ts,
                "sid": self._session_id,
                "type": event_type,
                "tool": tool_name,
                "action": action,
                "uri": uri,
                "params": sanitised,
                "status": result_status,
                "ms": round(duration_ms, 2),
                "error": error_message,
                "project": self._project_context,
            }
            with open(filepath, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, separators=(",", ":")) + "\n")
        except Exception as exc:
            log.debug("JSONL write failed: %s", exc)

        # -- SQLite --
        try:
            db = self._get_db()
            if db is not None:
                try:
                    db._conn.execute(
                        "INSERT INTO session_logs "
                        "(timestamp, session_id, event_type, tool_name, action, "
                        "uri, params, result_status, duration_ms, error_message, "
                        "project_context) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            ts, self._session_id, event_type, tool_name, action,
                            uri, params_json, result_status, duration_ms,
                            error_message, self._project_context,
                        ),
                    )
                    db._conn.commit()
                except Exception:
                    try:
                        db._conn.rollback()
                    except Exception:
                        pass
                    raise
        except Exception as exc:
            log.debug("SQLite log write failed: %s", exc)

    def _get_db(self) -> Any:
        """Lazy-load the knowledge DB to avoid circular imports."""
        if self._db is None:
            try:
                from ue_audio_mcp.knowledge.db import get_knowledge_db
                self._db = get_knowledge_db()
            except Exception:
                return None
        return self._db

    @staticmethod
    def _sanitize_payload(payload: dict | None) -> dict:
        """Truncate large fields and strip binary keys."""
        if not payload:
            return {}
        clean: dict[str, Any] = {}
        for key, val in payload.items():
            if key in _BINARY_KEYS:
                clean[key] = "<binary>"
                continue
            if isinstance(val, str) and len(val) > _MAX_FIELD_SIZE:
                clean[key] = val[:_MAX_FIELD_SIZE] + "...<truncated>"
            elif isinstance(val, (dict, list)):
                dumped = json.dumps(val, default=str)
                if len(dumped) > _MAX_FIELD_SIZE:
                    clean[key] = dumped[:_MAX_FIELD_SIZE] + "...<truncated>"
                else:
                    clean[key] = val
            else:
                clean[key] = val
        return clean


def get_session_logger(log_dir: str | None = None) -> SessionLogger:
    """Return the global SessionLogger singleton."""
    global _logger
    if _logger is None:
        _logger = SessionLogger(log_dir or _LOG_DIR)
    return _logger
