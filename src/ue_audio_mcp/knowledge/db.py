"""SQLite knowledge database — structured queries over nodes, WAAPI, patterns.

Same 8-table schema designed for future Cloudflare D1 migration.
Default location: ~/.ue-audio-mcp/knowledge.db (persistent, auto-seeded on first run).
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DEFAULT_DB_DIR = os.path.expanduser("~/.ue-audio-mcp")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "knowledge.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS metasound_nodes (
    name        TEXT PRIMARY KEY,
    category    TEXT NOT NULL,
    description TEXT NOT NULL,
    inputs      TEXT NOT NULL,
    outputs     TEXT NOT NULL,
    tags        TEXT NOT NULL,
    complexity  INTEGER NOT NULL DEFAULT 2
);

CREATE TABLE IF NOT EXISTS waapi_functions (
    uri         TEXT PRIMARY KEY,
    namespace   TEXT NOT NULL,
    operation   TEXT NOT NULL,
    description TEXT NOT NULL,
    params      TEXT NOT NULL DEFAULT '{}',
    returns     TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS wwise_types (
    type_name   TEXT PRIMARY KEY,
    category    TEXT NOT NULL,
    description TEXT NOT NULL,
    properties  TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS audio_patterns (
    name        TEXT PRIMARY KEY,
    pattern_type TEXT NOT NULL,
    description TEXT NOT NULL,
    graph_spec  TEXT NOT NULL DEFAULT '{}',
    complexity  INTEGER NOT NULL DEFAULT 3,
    key_nodes   TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS error_patterns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    error_signature TEXT NOT NULL,
    template        TEXT,
    fix             TEXT NOT NULL,
    params          TEXT NOT NULL DEFAULT '{}',
    success_count   INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_error_sig ON error_patterns(error_signature);

CREATE TABLE IF NOT EXISTS ue_game_examples (
    name        TEXT PRIMARY KEY,
    game        TEXT NOT NULL,
    system_type TEXT NOT NULL,
    description TEXT NOT NULL,
    details     TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS blueprint_audio (
    name        TEXT PRIMARY KEY,
    class_name  TEXT NOT NULL,
    category    TEXT NOT NULL,
    description TEXT NOT NULL,
    params      TEXT NOT NULL DEFAULT '[]',
    returns     TEXT NOT NULL DEFAULT '{}',
    tags        TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS blueprint_core (
    name        TEXT PRIMARY KEY,
    class_name  TEXT NOT NULL,
    category    TEXT NOT NULL,
    description TEXT NOT NULL,
    params      TEXT NOT NULL DEFAULT '[]',
    returns     TEXT NOT NULL DEFAULT '{}',
    tags        TEXT NOT NULL DEFAULT '[]'
);
"""


def _like_param(value: str) -> str:
    """Build a SQL LIKE parameter for substring matching."""
    return "%{}%".format(value)


def _tag_param(tag: str) -> str:
    """Build a LIKE parameter matching a JSON-encoded tag string."""
    return '%"{}"%'.format(tag)


class KnowledgeDB:
    """SQLite-backed knowledge database with structured query helpers.

    All queries use parameterised statements (? placeholders).
    No user input is ever interpolated into SQL strings.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)

    def _parse_json_fields(self, d: dict) -> dict:
        for key, val in d.items():
            if isinstance(val, str) and val and val[0] in ("{", "["):
                try:
                    d[key] = json.loads(val)
                except (json.JSONDecodeError, ValueError):
                    pass
        return d

    def _rows_to_dicts(self, rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
        return [self._parse_json_fields(dict(row)) for row in rows]

    def _fetch(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        cur = self._conn.execute(sql, params)
        return self._rows_to_dicts(cur.fetchall())

    # -- MetaSound nodes ---------------------------------------------------

    def insert_node(self, node: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO metasound_nodes "
            "(name, category, description, inputs, outputs, tags, complexity) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                node["name"],
                node["category"],
                node["description"],
                json.dumps(node["inputs"]),
                json.dumps(node["outputs"]),
                json.dumps(node["tags"]),
                node.get("complexity", 2),
            ),
        )
        self._conn.commit()

    def query_nodes(
        self,
        category: str | None = None,
        tag: str | None = None,
        name: str | None = None,
    ) -> list[dict]:
        if name:
            return self._fetch(
                "SELECT * FROM metasound_nodes WHERE name = ? ORDER BY name",
                (name,),
            )
        if category and tag:
            return self._fetch(
                "SELECT * FROM metasound_nodes "
                "WHERE category = ? AND tags LIKE ? ORDER BY name",
                (category, _tag_param(tag)),
            )
        if category:
            return self._fetch(
                "SELECT * FROM metasound_nodes "
                "WHERE category = ? ORDER BY name",
                (category,),
            )
        if tag:
            return self._fetch(
                "SELECT * FROM metasound_nodes "
                "WHERE tags LIKE ? ORDER BY name",
                (_tag_param(tag),),
            )
        return self._fetch(
            "SELECT * FROM metasound_nodes ORDER BY name"
        )

    def count_nodes_by_category(self) -> dict[str, int]:
        rows = self._conn.execute(
            "SELECT category, COUNT(*) as cnt FROM metasound_nodes "
            "GROUP BY category ORDER BY category"
        ).fetchall()
        return {row["category"]: row["cnt"] for row in rows}

    # -- WAAPI functions ---------------------------------------------------

    def insert_waapi(self, func: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO waapi_functions "
            "(uri, namespace, operation, description, params, returns) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                func["uri"],
                func["namespace"],
                func["operation"],
                func["description"],
                json.dumps(func.get("params", {})),
                json.dumps(func.get("returns", {})),
            ),
        )
        self._conn.commit()

    def query_waapi(
        self,
        namespace: str | None = None,
        operation: str | None = None,
    ) -> list[dict]:
        if namespace and operation:
            return self._fetch(
                "SELECT * FROM waapi_functions "
                "WHERE namespace = ? AND operation LIKE ? ORDER BY uri",
                (namespace, _like_param(operation)),
            )
        if namespace:
            return self._fetch(
                "SELECT * FROM waapi_functions "
                "WHERE namespace = ? ORDER BY uri",
                (namespace,),
            )
        if operation:
            return self._fetch(
                "SELECT * FROM waapi_functions "
                "WHERE operation LIKE ? ORDER BY uri",
                (_like_param(operation),),
            )
        return self._fetch(
            "SELECT * FROM waapi_functions ORDER BY uri"
        )

    # -- Wwise types -------------------------------------------------------

    def insert_wwise_type(self, wtype: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO wwise_types "
            "(type_name, category, description, properties) "
            "VALUES (?, ?, ?, ?)",
            (
                wtype["type_name"],
                wtype["category"],
                wtype["description"],
                json.dumps(wtype.get("properties", [])),
            ),
        )
        self._conn.commit()

    # -- Audio patterns ----------------------------------------------------

    def insert_pattern(self, pattern: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO audio_patterns "
            "(name, pattern_type, description, graph_spec, complexity, key_nodes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                pattern["name"],
                pattern["pattern_type"],
                pattern["description"],
                json.dumps(pattern.get("graph_spec", {})),
                pattern.get("complexity", 3),
                json.dumps(pattern.get("key_nodes", [])),
            ),
        )
        self._conn.commit()

    def query_patterns(self, pattern_type: str | None = None) -> list[dict]:
        if pattern_type:
            return self._fetch(
                "SELECT * FROM audio_patterns "
                "WHERE pattern_type = ? ORDER BY name",
                (pattern_type,),
            )
        return self._fetch(
            "SELECT * FROM audio_patterns ORDER BY name"
        )

    # -- Error patterns (grows at runtime) ---------------------------------

    def store_error(
        self,
        signature: str,
        fix: str,
        template: str | None = None,
        params: dict | None = None,
    ) -> None:
        existing = self._fetch(
            "SELECT id, success_count FROM error_patterns "
            "WHERE error_signature = ? AND fix = ?",
            (signature, fix),
        )
        if existing:
            self._conn.execute(
                "UPDATE error_patterns "
                "SET success_count = success_count + 1, "
                "updated_at = datetime('now') WHERE id = ?",
                (existing[0]["id"],),
            )
        else:
            self._conn.execute(
                "INSERT INTO error_patterns "
                "(error_signature, template, fix, params) "
                "VALUES (?, ?, ?, ?)",
                (signature, template, fix, json.dumps(params or {})),
            )
        self._conn.commit()

    def query_errors(self, signature: str) -> list[dict]:
        return self._fetch(
            "SELECT * FROM error_patterns "
            "WHERE error_signature = ? "
            "ORDER BY success_count DESC",
            (signature,),
        )

    # -- Game examples -----------------------------------------------------

    def insert_example(self, example: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO ue_game_examples "
            "(name, game, system_type, description, details) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                example["name"],
                example["game"],
                example["system_type"],
                example["description"],
                json.dumps(example.get("details", {})),
            ),
        )
        self._conn.commit()

    # -- Blueprint audio ---------------------------------------------------

    def insert_blueprint_audio(self, bp: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO blueprint_audio "
            "(name, class_name, category, description, params, returns, tags) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                bp["name"],
                bp["class_name"],
                bp["category"],
                bp["description"],
                json.dumps(bp.get("params", [])),
                json.dumps(bp.get("returns", {})),
                json.dumps(bp.get("tags", [])),
            ),
        )
        self._conn.commit()

    # -- Blueprint core ----------------------------------------------------

    def insert_blueprint_core(self, bp: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO blueprint_core "
            "(name, class_name, category, description, params, returns, tags) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                bp["name"],
                bp["class_name"],
                bp["category"],
                bp["description"],
                json.dumps(bp.get("params", [])),
                json.dumps(bp.get("returns", {})),
                json.dumps(bp.get("tags", [])),
            ),
        )
        self._conn.commit()

    # -- Utility -----------------------------------------------------------

    def table_counts(self) -> dict[str, int]:
        """Return row count for each table."""
        return {
            "metasound_nodes": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM metasound_nodes"
            ).fetchone()["cnt"],
            "waapi_functions": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM waapi_functions"
            ).fetchone()["cnt"],
            "wwise_types": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM wwise_types"
            ).fetchone()["cnt"],
            "audio_patterns": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM audio_patterns"
            ).fetchone()["cnt"],
            "error_patterns": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM error_patterns"
            ).fetchone()["cnt"],
            "ue_game_examples": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM ue_game_examples"
            ).fetchone()["cnt"],
            "blueprint_audio": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM blueprint_audio"
            ).fetchone()["cnt"],
            "blueprint_core": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM blueprint_core"
            ).fetchone()["cnt"],
        }

    def is_seeded(self) -> bool:
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM metasound_nodes"
        ).fetchone()
        return row["cnt"] > 0

    def close(self) -> None:
        self._conn.close()


_db: KnowledgeDB | None = None


def get_knowledge_db(db_path: str | None = None) -> KnowledgeDB:
    """Return the global KnowledgeDB singleton."""
    global _db
    if _db is None:
        path = db_path or DEFAULT_DB_PATH
        _db = KnowledgeDB(path)
        log.info("Knowledge DB opened at %s", path)
    return _db
