# UE Audio MCP Plugin — Build & Sync Workflow

## Quick Start

```bash
# 1. Build plugin and deploy to UE project
./scripts/build_plugin.sh

# 2. Open UE Editor, wait for it to load

# 3. Sync engine data to knowledge DB
python scripts/sync_nodes_from_engine.py --save-json --update-db
python scripts/sync_bp_from_engine.py --audio-only --save-json --update-db
```

## Architecture

```
Git Repo (ue5_plugin/UEAudioMCP/)     UE Project (Plugins/UEAudioMCP/)
├── Source/UEAudioMCP/          ──►    ├── Source/UEAudioMCP/
├── Source/SIDMetaSoundNodes/   ──►    ├── Source/SIDMetaSoundNodes/
├── Source/ThirdParty/ReSID/    ──►    ├── Source/ThirdParty/ReSID/
└── UEAudioMCP.uplugin         ──►    ├── Binaries/Mac/*.dylib  (compiled)
                                       └── Intermediate/         (build cache)
```

**Two modules:**
- `UEAudioMCP` (Editor) — TCP server, 35 commands, Blueprint/MetaSounds builders
- `SIDMetaSoundNodes` (Runtime) — 5 custom ReSID SID chip MetaSounds nodes

## Build Script

`scripts/build_plugin.sh` — syncs source + compiles via UnrealBuildTool.

```bash
./scripts/build_plugin.sh              # sync source + build (default)
./scripts/build_plugin.sh --clean      # sync + clean intermediates + build
./scripts/build_plugin.sh --sync-only  # just copy source, no compile
./scripts/build_plugin.sh --build-only # just compile, no source copy
```

**Paths (hardcoded in script):**
- Engine: `/Volumes/Koshi_T7/UN5.3/UE_5.7/`
- Project: `/Users/radek/Documents/Unreal Projects/UEIntroProject/`
- Plugin source: `/Users/radek/Documents/GIthub/UE5-WWISE/ue5_plugin/UEAudioMCP/`

**Gotchas:**
- UE Editor must be **closed** during build (dylibs are locked)
- Use `--clean` if build fails with "Action graph is invalid" (stale intermediates)
- Build takes ~2 min (full rebuild) or ~30s (incremental)
- 3 deprecation warnings are expected (UE 5.7 API changes, non-blocking)

## Sync Scripts

Both scripts connect to the plugin via TCP (port 9877) and fetch node/function
registries from the running UE engine.

### `scripts/sync_nodes_from_engine.py` — MetaSounds nodes

```bash
python scripts/sync_nodes_from_engine.py                    # diff only
python scripts/sync_nodes_from_engine.py --save-json        # save to exports/
python scripts/sync_nodes_from_engine.py --save-json --update-db  # save + DB
python scripts/sync_nodes_from_engine.py --diff-only        # compare only
```

- Fetches ALL MetaSounds node classes via `list_metasound_nodes` command
- Pagination: page_size=100, up to 5 retries per page with progressive delay
- Deduplicates by class_name
- Diff report: new nodes, updated pins, pin type changes
- DB: writes to `~/.ue-audio-mcp/knowledge.db` via `get_knowledge_db()` singleton
- Export: `exports/all_metasound_nodes.json`

**Expected output:** ~842 nodes from 9 pages in ~2s

### `scripts/sync_bp_from_engine.py` — Blueprint functions

```bash
python scripts/sync_bp_from_engine.py --audio-only --save-json --update-db
python scripts/sync_bp_from_engine.py --all --save-json     # ALL ~26K functions
python scripts/sync_bp_from_engine.py --class-filter AudioComponent --save-json
python scripts/sync_bp_from_engine.py --diff-only
```

- Fetches BlueprintCallable UFunctions via `list_blueprint_functions` command
- `--audio-only`: C++ `IsAudioRelevant()` filter (24 keywords inc. Quartz/Pitch/Volume)
- `--all`: batch-by-class mode — fetches class list, then per-class (handles ~26K functions)
- Reconnect logic with progressive delay
- DB: writes to `blueprint_nodes_scraped` table

**Expected output:** ~979 audio functions from 165 classes in ~2s

## Knowledge Base

### MetaSounds Catalogue (`metasound_nodes.py`)

| Metric | Count |
|--------|-------|
| Node definitions | 170 |
| CLASS_NAME_TO_DISPLAY entries | 124 (all engine-verified) |
| Nodes with class_name | 145/170 |
| Broken forward mappings | 0 |

**25 nodes without class_name (expected):**
- 5 SID plugin nodes, 4 MSP patch nodes (custom — need plugin loaded)
- 3 infrastructure (Get/Set Variable, Send) — sentinel nodes
- 6 removed in UE 5.7, 7 catalogue-only aliases

**Class_name format:** `Namespace::DisplayName::Variant`
- Examples: `UE::Sine::Audio`, `Clamp::Clamp::Float`, `AD Envelope::AD Envelope::Audio`
- Variant is typically `None`, `Audio`, `Float`, `Int32`

### Blueprint Catalogue (`blueprint_audio_catalogue.json`)

| Metric | Count |
|--------|-------|
| Curated functions | 55 |
| Curated events | 10 |
| Allowlist entries | 41 (C++ == JSON, zero drift) |
| Engine audio functions | 979 |

**Allowlist** (in `AudioMCPBlueprintManager.cpp`): security gate — only allowlisted
functions can be called via Blueprint builder MCP tools.

## C++ Plugin Commands (35 total)

| Group | Commands |
|-------|----------|
| Ping | `ping` |
| Builder | `create_source`, `add_node`, `connect_nodes`, `set_pin_default`, etc. |
| Query | `list_node_classes`/`list_metasound_nodes`, `list_blueprint_functions` |
| Blueprint | `scan_blueprint`, `list_assets`, `export_metasound` |
| BP Builder | `bp_add_node`, `bp_connect_pins`, `bp_compile`, `bp_set_pin` etc. |
| Variables | `add_variable`, `set_variable_default` |
| Presets | `create_preset`, `set_preset_value` |

### `list_metasound_nodes` params:
- `include_pins` (bool) — include input/output pin specs
- `include_metadata` (bool) — include author, keywords, deprecated
- `filter` (string) — substring match on class_name
- `limit`/`offset` (int) — pagination

### `list_blueprint_functions` params:
- `audio_only` (bool) — apply IsAudioRelevant filter
- `class_filter` (string) — exact class name
- `include_pins` (bool) — include parameter signatures
- `list_classes_only` (bool) — summary mode (class names + counts)
- `limit`/`offset` (int) — pagination

## Data Flow for Agents

```
Engine Registry (live)
    │
    ├── sync_nodes_from_engine.py ──► exports/all_metasound_nodes.json
    │                                  └──► ~/.ue-audio-mcp/knowledge.db
    │
    ├── sync_bp_from_engine.py ──► exports/blueprint_functions_audio.json
    │                               └──► ~/.ue-audio-mcp/knowledge.db
    │
    └── export_catalogues.py ──► knowledge/metasound_catalogue.json
                                 knowledge/blueprint_audio_catalogue.json
```

**Agent workflow:**
1. MCP server starts → `seed()` populates in-memory DB from catalogues
2. Agent queries nodes via `ms_search_nodes` / `bp_search_functions` tools
3. Agent builds graphs via `ms_build_graph` / `bp_add_node` + `bp_wire_audio_param`
4. Three-layer: Blueprint (WHEN) + MetaSounds (WHAT) + Wwise (HOW)

## Regenerating Catalogues

```bash
python scripts/export_catalogues.py           # both
python scripts/export_catalogues.py --ms-only # MetaSounds only
python scripts/export_catalogues.py --bp-only # Blueprint only
```

Exports in-memory Python data to JSON catalogues. These are the checked-in
source of truth — sync scripts update the DB but not these files.
