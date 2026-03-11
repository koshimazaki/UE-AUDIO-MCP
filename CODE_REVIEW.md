# Code Review — UE Audio MCP

**Date**: 2026-03-11
**Branch**: `claude/code-review-improvements-M1nPB`
**Scope**: Full repo review — structural integrity, naming, code quality, documentation accuracy

---

## Summary

The repo is well-structured with solid architecture. Five parallel review agents examined naming consistency, structural integrity, code quality, C++ plugin code, and templates/knowledge. Below are findings grouped by severity.

**Verified counts (actual):**
| Item | Actual | Was (CLAUDE.md) | Was (README) |
|------|--------|-----------------|--------------|
| MCP tools | 74 | — | 69 |
| C++ commands | 43 | 35 | 41 |
| MS templates | 33 | 25 | 33 |
| BP templates | 34 | 30 | 34 |
| Wwise templates | 6 | 6 | 6 |
| Test functions | 456 | 432 | — |
| Research docs | 6 | 3 | — |
| Audio patterns | 11 | — | 11 |

---

## Issues Fixed in This PR

### 1. Documentation Count Drift (FIXED)

All three docs (CLAUDE.md, README.md, ue5_plugin/README.md) had stale numbers after recent world_setup and blueprint-spawning features were added.

**Files changed:**
- `.claude/CLAUDE.md` — Updated tool counts (74), command counts (43), template counts (33/34/6), test count (456), research doc count (6), fixed `verify_pins.py` reference (doesn't exist) to `verify_blueprint_nodes.py`
- `README.md` — Updated tool counts (74 total, 21/24/16/7/4/2 breakdown), command count (43)
- `ue5_plugin/README.md` — Updated command count (43)
- `TOOLS_AND_COMMANDS.md` — Updated all section counts (74 tools, 43 commands, per-category breakdowns), fixed `spawn_blueprint_actor` numbering gap, added `ue5_duplicate_asset` to tool listing

### 2. CLAUDE.md File Tree Inaccuracies (FIXED)

- `connection.py` was listed as containing both `WaapiConnection + UE5PluginConnection` — but `UE5PluginConnection` is in `ue5_connection.py`
- `graph_schema.py` was listed under `src/ue_audio_mcp/` root but is actually in `knowledge/`
- Tools directory used glob patterns (`wwise_*.py`, `ms_*.py`, `bp_*.py`) that don't match actual filenames (`core.py`, `objects.py`, etc.)
- Missing `ue5_core.py` and `world_setup.py` from file tree

### 3. Error Handling Inconsistency (FIXED)

`world_setup.py` and `ue5_core.py` used inline `result.get("status") == "error"` checks while other tools used the shared `_check_ue5_result()` helper. Migrated both files to use the helper for consistency.

---

## Findings Not Changed (Recommendations)

### 4. Naming Conventions — Generally Consistent

**Python modules**: All snake_case, consistent prefixes (`ms_*` for MetaSounds, `bp_*` for Blueprint). Minor note: Wwise tools don't use a `wwise_*` prefix (they use `core.py`, `objects.py`, `events.py`, `preview.py`, `templates.py`). This is acceptable since they were the original tools.

**Functions**: All tool functions are snake_case, consistent. Internal helpers use `_` prefix.

**JSON templates**: Use snake_case keys throughout. Consistent.

**C++ plugin**: Follows UE5 naming (PascalCase for classes/functions, `F` prefix for structs).

### 5. Structural Integrity — Sound

- All `__init__.py` files present in Python packages
- No circular imports detected
- All scripts mentioned in CLAUDE.md exist
- `pyproject.toml` is well-configured with proper entry points
- Templates directory structure matches documented layout

### 6. Test Coverage — Good but Gaps

**24 test files, 456 test functions.** Coverage is strong for:
- All tool modules have corresponding test files
- Connection classes (both Wwise and UE5)
- Graph schema validation
- Knowledge DB operations
- Template validation

**Gaps identified:**
- `knowledge/seed.py` — No dedicated test file (seeding logic)
- `knowledge/embeddings.py` — Search accuracy tests could be expanded
- `knowledge/blueprint_scraped.py` — No dedicated tests
- Integration tests between layers (e.g., systems.py calling real templates)

### 7. Code Quality Observations

**Strengths:**
- Consistent `_ok()`/`_error()` response pattern across all 74 tools
- Path traversal protection (`..` checks) on all asset path inputs
- `_validate_asset_path()` shared helper used broadly
- Connection singletons with clean lifecycle management
- Graceful degradation (offline/wwise-only/full modes)

**Minor observations:**
- `connection.py` `is_connected()` makes a real WAAPI call (`getInfo`) — this is intentional (verifies liveness) but could be slow under load
- `ms_builder.py` `_normalize_pin_type()` returns `"Audio"` for empty strings — sensible default but worth a comment
- `templates.py` imports `waapi` at top level, meaning it fails to import if `waapi` package isn't installed even when only using MetaSounds tools. The lifespan already handles this gracefully.

### 8. C++ Plugin Observations

**Strengths:**
- Clean command dispatch pattern via `FAudioMCPCommandDispatcher`
- Each command group in separate files (`WorldCommands.cpp`, `BPBuilderCommands.cpp`, etc.)
- Path validation with `..` traversal checks
- JSON parsing with error responses

**Observations:**
- `WorldCommands.cpp` is 885 lines — largest single command file. Consider splitting if more world commands are added.
- `AudioMCPNodeRegistry.h` changed to use templates (`TNodeFacade<Op>`) for UE 5.7 compat — well handled
- `UEAudioMCP.Build.cs` has appropriate module dependencies

### 9. Template/Knowledge Integrity

- All 33 MS templates are valid JSON
- All 34 BP templates are valid JSON
- `metasound_nodes.py` has 195 nodes with 145 class_name mappings — matches claims
- 20 DB tables as documented
- `graph_schema.py` 7-stage validator is thorough
- `CLASS_NAME_TO_DISPLAY` reverse mapping kept in sync via `ms_sync_from_engine`

---

## Improvement Suggestions (Future Work)

1. **Automated count tracking**: Add a CI script that verifies documented counts match reality (prevents drift)
2. **Type stubs for C++ commands**: A shared enum/constant for command action strings used in both Python tools and C++ registration
3. **BP tool naming alignment**: Consider renaming `blueprints.py` → `bp_knowledge.py` for consistency with `ms_builder.py` / `bp_builder.py` pattern
4. **Connection health check**: Add a lightweight ping-based `is_connected()` for Wwise (vs current `getInfo` call)
5. **ue5_plugin/README.md command table**: Update the command table (currently shows 35-era grouping, missing world/BP-notify commands)
6. **Seed tests**: Add test coverage for `knowledge/seed.py` DB seeding
