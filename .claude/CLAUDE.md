# UE Audio MCP

An MCP server (Python) and an Unreal Editor plugin (C++) that build game audio from natural language. Three layers: Blueprints decide *when* (game events), MetaSounds *what* (procedural DSP), Wwise *how* (mixing, buses, spatialisation). The server drives Wwise through WAAPI, and MetaSounds and Blueprints through the plugin's TCP commands.

- Python 3.10+, MCP Python SDK 2.x (`MCPServer`), stdio transport
- Unreal Engine 5.7.2+ for the plugin; Wwise 2025.1.4+ with WAAPI enabled for the Wwise tools
- Knowledge, template and validation tools work offline; Wwise and UE5 tools need those apps running

## Layout

- `src/ue_audio_mcp/server.py`: the `MCPServer` instance and lifespan; imports every tool module
- `src/ue_audio_mcp/tools/`: MCP tools, one module per area (Wwise, MetaSounds, Blueprints, world setup, camera, audit, orchestration)
- `src/ue_audio_mcp/connection.py`, `ue5_connection.py`: WAAPI (WebSocket :8080) and UE5 TCP (:9877) singletons
- `src/ue_audio_mcp/knowledge/`: SQLite knowledge DB, TF-IDF search, node catalogues, graph validator (`graph_schema.py`)
- `src/ue_audio_mcp/templates/`: MetaSounds, Blueprint and Wwise JSON templates
- `ue5_plugin/`: the C++ plugin. Its own `CLAUDE.md` has the build notes and the UE breaking-changes checklist
- `scripts/`: engine sync, catalogue pipeline, verification and plugin build. See `scripts/CLAUDE.md`
- `tests/`: pytest suite with mock WAAPI and UE5 fixtures in `tests/conftest.py`
- `research/`: background research (WAAPI, MetaSounds, AudioLink, Lyra patterns, the MCP landscape)
- `TOOLS_AND_COMMANDS.md`: every MCP tool and TCP command

Domain guides live in `.claude/skills/`: MetaSounds DSP, Blueprint audio, Wwise setup, driving the plugin, adding plugin commands, and full-system builds.

## Commands

```bash
pip install -e ".[dev]"
pytest                               # tests never touch ~/.ue-audio-mcp
python scripts/verify_templates.py   # after changing templates or node catalogues
ue-audio-mcp                         # run the server over stdio (python -m ue_audio_mcp.server also works)
```

## Conventions

- Tools are sync functions decorated `@mcp.tool()` then `@logged_tool`, returning `_ok(...)` or `_error(...)` JSON strings from `tools/utils.py`. `logged_tool` records each call in the audit log and holds a lock: the SDK runs sync tools on worker threads, and all tools share one SQLite connection, UE5 socket and WAAPI client.
- Open text files with `encoding="utf-8"`; Windows defaults to cp1252.
- No secrets in code. SQL uses parameterised queries only. Validate UE asset paths with `_validate_asset_path` (`/Game/` or `/Engine/`, no `..`).
- Every tool gets a test built on the mock fixtures in `tests/conftest.py`.
- MetaSound class and pin names come from the engine-synced catalogue, `knowledge/metasound_catalogue.json`. Node entries follow the `MSNode`/`MSPin` TypedDicts in `knowledge/node_schema.py`. Check graphs with `validate_graph()`.
- Don't hard-code counts in docs; they drift. Tools are the `@mcp.tool()` functions in `tools/`; TCP commands are the `RegisterCommand` calls in the plugin.

## Runtime data

The server keeps its knowledge DB and session logs in `~/.ue-audio-mcp/`. The DB is a cache built from the catalogues in `src/` plus audit and project-scan data; missing catalogue rows are re-seeded when it opens.
