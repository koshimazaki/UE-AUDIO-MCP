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

CREATE TABLE IF NOT EXISTS blueprint_nodes_scraped (
    name        TEXT PRIMARY KEY,
    target      TEXT NOT NULL DEFAULT '',
    category    TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    inputs      TEXT NOT NULL DEFAULT '[]',
    outputs     TEXT NOT NULL DEFAULT '[]',
    slug        TEXT NOT NULL DEFAULT '',
    ue_version  TEXT NOT NULL DEFAULT '',
    path        TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS builder_api_functions (
    name        TEXT PRIMARY KEY,
    category    TEXT NOT NULL,
    description TEXT NOT NULL,
    params      TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS tutorial_workflows (
    name        TEXT PRIMARY KEY,
    tutorial    TEXT NOT NULL,
    url         TEXT NOT NULL DEFAULT '',
    layers      TEXT NOT NULL DEFAULT '[]',
    description TEXT NOT NULL DEFAULT '',
    tags        TEXT NOT NULL DEFAULT '[]',
    bp_template TEXT NOT NULL DEFAULT '',
    ms_template TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS audio_console_commands (
    cmd         TEXT PRIMARY KEY,
    category    TEXT NOT NULL,
    type        TEXT NOT NULL DEFAULT 'bool',
    default_val TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS spatialization_methods (
    name        TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    details     TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS attenuation_subsystems (
    name        TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    params      TEXT NOT NULL DEFAULT '[]',
    details     TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS project_audio_assets (
    name        TEXT NOT NULL,
    project     TEXT NOT NULL,
    asset_type  TEXT NOT NULL,
    path        TEXT NOT NULL DEFAULT '',
    refs        TEXT NOT NULL DEFAULT '[]',
    properties  TEXT NOT NULL DEFAULT '[]',
    details     TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (name, project)
);
CREATE INDEX IF NOT EXISTS idx_paa_type ON project_audio_assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_paa_project ON project_audio_assets(project);

CREATE TABLE IF NOT EXISTS project_blueprints (
    name        TEXT NOT NULL,
    project     TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    functions   TEXT NOT NULL DEFAULT '[]',
    variables   TEXT NOT NULL DEFAULT '[]',
    components  TEXT NOT NULL DEFAULT '[]',
    events      TEXT NOT NULL DEFAULT '[]',
    refs        TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (name, project)
);

CREATE TABLE IF NOT EXISTS pin_mappings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    bp_function TEXT NOT NULL,
    bp_pin      TEXT NOT NULL,
    ms_node     TEXT NOT NULL DEFAULT '',
    ms_pin      TEXT NOT NULL DEFAULT '',
    data_type   TEXT NOT NULL,
    direction   TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_pm_direction ON pin_mappings(direction);
CREATE INDEX IF NOT EXISTS idx_pm_data_type ON pin_mappings(data_type);
"""


def _escape_like(value: str) -> str:
    """Escape LIKE wildcard characters (%, _) in user input."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _like_param(value: str) -> str:
    """Build a SQL LIKE parameter for substring matching."""
    return "%{}%".format(_escape_like(value))


def _tag_param(tag: str) -> str:
    """Build a LIKE parameter matching a JSON-encoded tag string."""
    return '%"{}"%'.format(_escape_like(tag))


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
                "WHERE category = ? AND tags LIKE ? ESCAPE '\\' ORDER BY name",
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
                "WHERE tags LIKE ? ESCAPE '\\' ORDER BY name",
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
                "WHERE namespace = ? AND operation LIKE ? ESCAPE '\\' ORDER BY uri",
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
                "WHERE operation LIKE ? ESCAPE '\\' ORDER BY uri",
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

    # -- Blueprint curated (audio + core) -----------------------------------

    def search_blueprint_curated(
        self, query: str, category: str | None = None
    ) -> list[dict]:
        """Search curated blueprint tables (audio + core) by name/description."""
        like = _like_param(query)
        results: list[dict] = []
        for table in ("blueprint_audio", "blueprint_core"):
            sql = (
                "SELECT name, category, description, '{}' as _table "
                "FROM {} WHERE (name LIKE ? ESCAPE '\\' "
                "OR description LIKE ? ESCAPE '\\')".format(table, table)
            )
            params: list[str] = [like, like]
            if category:
                sql += " AND category LIKE ? ESCAPE '\\'"
                params.append(_like_param(category))
            sql += " ORDER BY name"
            results.extend(self._fetch(sql, tuple(params)))
        return results

    def query_blueprint_curated_by_name(self, name: str) -> list[dict]:
        """Look up a curated blueprint node by exact name."""
        for table in ("blueprint_audio", "blueprint_core"):
            rows = self._fetch(
                "SELECT * FROM {} WHERE name = ?".format(table), (name,)
            )
            if rows:
                return rows
        return []

    def list_blueprint_curated_categories(self) -> list[dict]:
        """Get category counts from curated blueprint tables."""
        results: list[dict] = []
        for table in ("blueprint_audio", "blueprint_core"):
            rows = self._fetch(
                "SELECT category, COUNT(*) as cnt FROM {} "
                "GROUP BY category ORDER BY category".format(table)
            )
            results.extend(rows)
        return results

    # -- Blueprint scraped --------------------------------------------------

    def insert_blueprint_scraped(self, bp: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO blueprint_nodes_scraped "
            "(name, target, category, description, inputs, outputs, slug, ue_version, path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            self._blueprint_scraped_params(bp),
        )
        self._conn.commit()

    def insert_blueprint_scraped_batch(self, nodes: list[dict]) -> None:
        """Insert many scraped nodes in a single transaction (fast for 1K+ rows)."""
        self._conn.executemany(
            "INSERT OR REPLACE INTO blueprint_nodes_scraped "
            "(name, target, category, description, inputs, outputs, slug, ue_version, path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [self._blueprint_scraped_params(bp) for bp in nodes],
        )
        self._conn.commit()

    @staticmethod
    def _blueprint_scraped_params(bp: dict) -> tuple:
        return (
            bp["name"],
            bp.get("target", ""),
            bp.get("category", ""),
            bp.get("description", ""),
            json.dumps(bp.get("inputs", [])),
            json.dumps(bp.get("outputs", [])),
            bp.get("slug", ""),
            bp.get("ue_version", ""),
            bp.get("path", ""),
        )

    def query_blueprint_scraped(
        self,
        category: str | None = None,
        target: str | None = None,
        name: str | None = None,
    ) -> list[dict]:
        if name:
            return self._fetch(
                "SELECT * FROM blueprint_nodes_scraped WHERE name = ?", (name,)
            )
        if category and target:
            return self._fetch(
                "SELECT * FROM blueprint_nodes_scraped "
                "WHERE category = ? AND target = ? ORDER BY name",
                (category, target),
            )
        if category:
            return self._fetch(
                "SELECT * FROM blueprint_nodes_scraped "
                "WHERE category = ? ORDER BY name",
                (category,),
            )
        if target:
            return self._fetch(
                "SELECT * FROM blueprint_nodes_scraped "
                "WHERE target = ? ORDER BY name",
                (target,),
            )
        return self._fetch(
            "SELECT * FROM blueprint_nodes_scraped ORDER BY name"
        )

    def search_blueprint_scraped(self, query: str) -> list[dict]:
        param = _like_param(query)
        return self._fetch(
            "SELECT * FROM blueprint_nodes_scraped "
            "WHERE name LIKE ? ESCAPE '\\' "
            "OR description LIKE ? ESCAPE '\\' "
            "ORDER BY name",
            (param, param),
        )

    # -- Builder API -------------------------------------------------------

    def insert_builder_api(self, func: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO builder_api_functions "
            "(name, category, description, params) VALUES (?, ?, ?, ?)",
            (
                func["name"],
                func["category"],
                func["description"],
                json.dumps(func.get("params", [])),
            ),
        )
        self._conn.commit()

    def query_builder_api(self, category: str | None = None) -> list[dict]:
        if category:
            return self._fetch(
                "SELECT * FROM builder_api_functions "
                "WHERE category = ? ORDER BY name",
                (category,),
            )
        return self._fetch(
            "SELECT * FROM builder_api_functions ORDER BY name"
        )

    # -- Tutorial workflows ------------------------------------------------

    def insert_tutorial_workflow(self, wf: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO tutorial_workflows "
            "(name, tutorial, url, layers, description, tags, bp_template, ms_template) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                wf["name"],
                wf["tutorial"],
                wf.get("url", ""),
                json.dumps(wf.get("layers", [])),
                wf.get("description", ""),
                json.dumps(wf.get("tags", [])),
                wf.get("blueprint_template", ""),
                wf.get("metasound_template", ""),
            ),
        )
        self._conn.commit()

    def query_tutorial_workflows(self, tag: str | None = None) -> list[dict]:
        if tag:
            return self._fetch(
                "SELECT * FROM tutorial_workflows "
                "WHERE tags LIKE ? ESCAPE '\\' ORDER BY name",
                (_tag_param(tag),),
            )
        return self._fetch(
            "SELECT * FROM tutorial_workflows ORDER BY name"
        )

    # -- Console commands --------------------------------------------------

    def insert_console_command(self, cmd: dict) -> None:
        default = cmd.get("default")
        self._conn.execute(
            "INSERT OR REPLACE INTO audio_console_commands "
            "(cmd, category, type, default_val, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                cmd["cmd"],
                cmd["category"],
                cmd.get("type", "bool"),
                json.dumps(default) if default is not None else "",
                cmd.get("description", ""),
            ),
        )
        self._conn.commit()

    # -- Spatialization ----------------------------------------------------

    def insert_spatialization(self, method: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO spatialization_methods "
            "(name, description, details) VALUES (?, ?, ?)",
            (
                method["name"],
                method["description"],
                json.dumps(method.get("details", {})),
            ),
        )
        self._conn.commit()

    # -- Attenuation -------------------------------------------------------

    def insert_attenuation(self, sub: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO attenuation_subsystems "
            "(name, description, params, details) VALUES (?, ?, ?, ?)",
            (
                sub["name"],
                sub["description"],
                json.dumps(sub.get("params", [])),
                json.dumps(sub.get("details", {})),
            ),
        )
        self._conn.commit()

    # -- Project audio assets (from uasset extraction) ----------------------

    def insert_project_asset(self, asset: dict, project: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO project_audio_assets "
            "(name, project, asset_type, path, refs, properties, details) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                asset["name"],
                project,
                asset["category"],
                asset.get("path", ""),
                json.dumps(asset.get("references", [])),
                json.dumps(asset.get("properties", [])),
                json.dumps({
                    k: v for k, v in asset.items()
                    if k not in ("name", "category", "path", "references",
                                 "properties", "source")
                }),
            ),
        )

    def insert_project_blueprint(self, bp: dict, project: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO project_blueprints "
            "(name, project, description, functions, variables, "
            "components, events, refs) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                bp["name"],
                project,
                bp.get("description", ""),
                json.dumps(bp.get("functions", [])),
                json.dumps(bp.get("variables", [])),
                json.dumps(bp.get("components", [])),
                json.dumps(bp.get("events", [])),
                json.dumps(bp.get("references", [])),
            ),
        )

    def import_uasset_entries(self, entries: list[dict], project: str) -> int:
        """Bulk-import entries from uasset extraction. Returns count."""
        count = 0
        for entry in entries:
            if entry["category"] == "blueprint_audio_pattern":
                self.insert_project_blueprint(entry, project)
            else:
                self.insert_project_asset(entry, project)
            count += 1
        self._conn.commit()
        return count

    def query_project_assets(
        self,
        project: str | None = None,
        asset_type: str | None = None,
        name: str | None = None,
    ) -> list[dict]:
        if name:
            return self._fetch(
                "SELECT * FROM project_audio_assets WHERE name = ?",
                (name,),
            )
        if project and asset_type:
            return self._fetch(
                "SELECT * FROM project_audio_assets "
                "WHERE project = ? AND asset_type = ? ORDER BY name",
                (project, asset_type),
            )
        if project:
            return self._fetch(
                "SELECT * FROM project_audio_assets "
                "WHERE project = ? ORDER BY asset_type, name",
                (project,),
            )
        if asset_type:
            return self._fetch(
                "SELECT * FROM project_audio_assets "
                "WHERE asset_type = ? ORDER BY name",
                (asset_type,),
            )
        return self._fetch(
            "SELECT * FROM project_audio_assets ORDER BY project, asset_type, name"
        )

    def query_project_blueprints(
        self, project: str | None = None, name: str | None = None
    ) -> list[dict]:
        if name:
            return self._fetch(
                "SELECT * FROM project_blueprints WHERE name = ?", (name,)
            )
        if project:
            return self._fetch(
                "SELECT * FROM project_blueprints WHERE project = ? ORDER BY name",
                (project,),
            )
        return self._fetch("SELECT * FROM project_blueprints ORDER BY project, name")

    # -- Pin mappings (cross-system wiring) --------------------------------

    def insert_pin_mapping(self, m: dict) -> None:
        self._conn.execute(
            "INSERT INTO pin_mappings "
            "(bp_function, bp_pin, ms_node, ms_pin, data_type, direction, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                m["bp_function"],
                m["bp_pin"],
                m.get("ms_node", ""),
                m.get("ms_pin", ""),
                m["data_type"],
                m["direction"],
                m.get("description", ""),
            ),
        )
        self._conn.commit()

    def insert_pin_mappings_batch(self, mappings: list[dict]) -> int:
        """Bulk-insert pin mappings. Returns count inserted."""
        self._conn.executemany(
            "INSERT INTO pin_mappings "
            "(bp_function, bp_pin, ms_node, ms_pin, data_type, direction, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    m["bp_function"], m["bp_pin"],
                    m.get("ms_node", ""), m.get("ms_pin", ""),
                    m["data_type"], m["direction"],
                    m.get("description", ""),
                )
                for m in mappings
            ],
        )
        self._conn.commit()
        return len(mappings)

    def query_pin_mappings(
        self,
        direction: str | None = None,
        data_type: str | None = None,
        query: str | None = None,
    ) -> list[dict]:
        """Search pin mappings by direction, data type, or free text."""
        if query:
            param = _like_param(query)
            return self._fetch(
                "SELECT * FROM pin_mappings "
                "WHERE bp_function LIKE ? ESCAPE '\\' "
                "OR ms_pin LIKE ? ESCAPE '\\' "
                "OR description LIKE ? ESCAPE '\\' "
                "ORDER BY direction, bp_function",
                (param, param, param),
            )
        if direction and data_type:
            return self._fetch(
                "SELECT * FROM pin_mappings "
                "WHERE direction = ? AND data_type = ? "
                "ORDER BY bp_function",
                (direction, data_type),
            )
        if direction:
            return self._fetch(
                "SELECT * FROM pin_mappings WHERE direction = ? ORDER BY bp_function",
                (direction,),
            )
        if data_type:
            return self._fetch(
                "SELECT * FROM pin_mappings WHERE data_type = ? ORDER BY bp_function",
                (data_type,),
            )
        return self._fetch("SELECT * FROM pin_mappings ORDER BY direction, bp_function")

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
            "blueprint_nodes_scraped": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM blueprint_nodes_scraped"
            ).fetchone()["cnt"],
            "builder_api_functions": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM builder_api_functions"
            ).fetchone()["cnt"],
            "tutorial_workflows": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM tutorial_workflows"
            ).fetchone()["cnt"],
            "audio_console_commands": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM audio_console_commands"
            ).fetchone()["cnt"],
            "spatialization_methods": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM spatialization_methods"
            ).fetchone()["cnt"],
            "attenuation_subsystems": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM attenuation_subsystems"
            ).fetchone()["cnt"],
            "project_audio_assets": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM project_audio_assets"
            ).fetchone()["cnt"],
            "project_blueprints": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM project_blueprints"
            ).fetchone()["cnt"],
            "pin_mappings": self._conn.execute(
                "SELECT COUNT(*) as cnt FROM pin_mappings"
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
