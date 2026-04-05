"""Audit tools — query session logs and usage statistics."""

from __future__ import annotations

import json
import logging

from ue_audio_mcp.knowledge.db import get_knowledge_db
from ue_audio_mcp.server import mcp
from ue_audio_mcp.tools.utils import _error, _ok, logged_tool

log = logging.getLogger(__name__)


@mcp.tool()
@logged_tool
def audit_history(
    session_id: str = "",
    event_type: str = "",
    tool_name: str = "",
    since: str = "",
    status_filter: str = "",
    limit: int = 50,
    summary_only: bool = False,
) -> str:
    """Query past session log events with optional filters.

    Args:
        session_id: Filter by session ID
        event_type: Filter by type (tool_call, waapi_call, tcp_command, session_start, session_end)
        tool_name: Filter by tool name
        since: ISO date string — only events after this timestamp
        status_filter: Filter by result status (ok, error)
        limit: Max rows to return (default 50, max 500)
        summary_only: If true, return per-session aggregates instead of raw events
    """
    db = get_knowledge_db()
    limit = min(max(limit, 1), 500)

    if summary_only:
        sql = (
            "SELECT session_id, "
            "MIN(timestamp) as started, MAX(timestamp) as ended, "
            "COUNT(*) as event_count, "
            "SUM(CASE WHEN result_status = 'error' THEN 1 ELSE 0 END) as errors, "
            "ROUND(SUM(duration_ms), 1) as total_ms, "
            "project_context "
            "FROM session_logs WHERE 1=1"
        )
        params: list = []
        if session_id:
            sql += " AND session_id = ?"
            params.append(session_id)
        if event_type:
            sql += " AND event_type = ?"
            params.append(event_type)
        if since:
            sql += " AND timestamp >= ?"
            params.append(since)
        sql += " GROUP BY session_id ORDER BY started DESC LIMIT ?"
        params.append(limit)
        try:
            rows = db._fetch(sql, tuple(params))
            return _ok({"count": len(rows), "sessions": rows})
        except Exception as e:
            return _error(str(e))

    # Raw event query
    sql = "SELECT * FROM session_logs WHERE 1=1"
    params = []
    if session_id:
        sql += " AND session_id = ?"
        params.append(session_id)
    if event_type:
        sql += " AND event_type = ?"
        params.append(event_type)
    if tool_name:
        sql += " AND tool_name = ?"
        params.append(tool_name)
    if since:
        sql += " AND timestamp >= ?"
        params.append(since)
    if status_filter:
        sql += " AND result_status = ?"
        params.append(status_filter)
    sql += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    try:
        rows = db._fetch(sql, tuple(params))
        return _ok({"count": len(rows), "events": rows})
    except Exception as e:
        return _error(str(e))


@mcp.tool()
@logged_tool
def audit_session_stats() -> str:
    """Get overall session logging statistics.

    Returns total sessions, event counts by type, error rate,
    and top 10 most-used tools.
    """
    db = get_knowledge_db()
    try:
        total_events = db._conn.execute(
            "SELECT COUNT(*) as cnt FROM session_logs"
        ).fetchone()["cnt"]

        total_sessions = db._conn.execute(
            "SELECT COUNT(DISTINCT session_id) as cnt FROM session_logs"
        ).fetchone()["cnt"]

        by_type = db._fetch(
            "SELECT event_type, COUNT(*) as cnt FROM session_logs "
            "GROUP BY event_type ORDER BY cnt DESC"
        )

        error_count = db._conn.execute(
            "SELECT COUNT(*) as cnt FROM session_logs WHERE result_status = 'error'"
        ).fetchone()["cnt"]

        top_tools = db._fetch(
            "SELECT tool_name, COUNT(*) as cnt, "
            "ROUND(AVG(duration_ms), 1) as avg_ms, "
            "SUM(CASE WHEN result_status = 'error' THEN 1 ELSE 0 END) as errors "
            "FROM session_logs WHERE event_type = 'tool_call' AND tool_name != '' "
            "GROUP BY tool_name ORDER BY cnt DESC LIMIT 10"
        )

        error_rate = round(error_count / total_events * 100, 1) if total_events else 0.0

        return _ok({
            "total_events": total_events,
            "total_sessions": total_sessions,
            "error_rate_pct": error_rate,
            "events_by_type": {r["event_type"]: r["cnt"] for r in by_type},
            "top_tools": top_tools,
        })
    except Exception as e:
        return _error(str(e))
