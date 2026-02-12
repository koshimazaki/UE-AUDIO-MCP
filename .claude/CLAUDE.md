# UE Audio MCP - Project Instructions

## Project Overview
MCP server for game audio — generating complete Wwise + MetaSounds + Blueprint audio systems from natural language.

**Architecture**: Three-layer system
- **Blueprint (WHEN)** — Game event detection, parameter setting via Remote Control API
- **MetaSounds (WHAT)** — Procedural DSP synthesis via Builder API (UE 5.4+)
- **Wwise (HOW)** — Mixing, buses, spatialization, RTPC via WAAPI (ws://127.0.0.1:8080/waapi)

---

## Tech Stack
| Component | Technology | Notes |
|-----------|-----------|-------|
| MCP Server | Python (FastMCP) | Main server, stdio transport |
| Wwise Bridge | `waapi-client` | Official Audiokinetic Python lib, WebSocket :8080 |
| UE5 Bridge | C++ plugin + TCP (port 9877) | JSON command protocol, 35 commands |
| Knowledge | Local SQLite + TF-IDF | 178 nodes, 643 verified entries, semantic search |
| Templates | Parameterised JSON | 25 MetaSounds + 30 Blueprint + 6 Wwise |

## Key APIs
- **WAAPI**: 87 functions, WAMP/WebSocket on :8080, HTTP on :8090. Wwise MUST be running.
- **MetaSounds Builder API**: Experimental (UE 5.4+). CreateSourceBuilder, AddNode, ConnectNodes, Audition, BuildToAsset.
- **UE5 Remote Control**: Blueprint parameter wiring, game state connections.
- **AudioLink (UE 5.1+)**: One-way MetaSounds → Wwise routing.

---

## Agent Specialisations

### /ue-agent — Unreal Engine 5 Specialist
Handles: MetaSounds patches, Builder API, Blueprint audio logic, DSP node graphs, UE5 plugin C++ code, Remote Control API.

### /wwise-agent — Wwise & WAAPI Specialist
Handles: WAAPI calls, Wwise object hierarchy, RTPC curves, switch containers, bus routing, SoundBank generation, AudioLink bridge, sound synthesis concepts.

---

## Critical Rules

### Wwise/WAAPI
- Object paths use **backslashes** `\Actor-Mixer Hierarchy\Default Work Unit\MySound`
- Always use `onNameConflict` param: "merge", "rename", "replace", or "fail"
- Wrap batch operations in **undo groups** (`ak.wwise.core.undo.beginGroup/endGroup`)
- Wwise is single-threaded — batch max 100 items per call
- No authentication (localhost only) — no headless mode
- Key object types: Sound, RandomSequenceContainer, SwitchContainer, BlendContainer, ActorMixer, Event, Bus, AuxBus, GameParameter, Switch, State

### MetaSounds
- Builder API is **experimental** — API may change between UE versions
- Node class names are NOT publicly documented — discover via Shift+hover in Editor
- Data types: Audio, Trigger, Float, Int32, Bool, Time, String, WaveAsset, UObject, Enum
- Asset types: Source (playable), Patch (reusable subgraph), Preset (parameter overrides)
- WaveAsset references require actual .wav files in project Content folder
- Use `SetNodeLocation()` for editor visibility

### UE 5.7 Breaking Changes (C++ Plugin)
These break every major UE update — check first when compile fails:
- **`Document.RootGraph.Interface`** → `Document.RootGraph.GetDefaultInterface()` (inputs/outputs access)
- **`ClassInput.Default`** (removed) → `ClassInput.FindConstDefault(FGuid())` returns `FMetasoundFrontendLiteral*` (null if no default). `FGuid()` = default page.
- **`FNodeFacade`** → `TNodeFacade<Op>` (templated in 5.7)
- **`GetOrConstructDataReadReference`** → `GetOrCreateDefaultDataReadReference` (deprecated 5.6)
- **`bEnableUndefinedIdentifierWarnings`** → `UndefinedIdentifierWarningLevel = WarningLevel.Off` (deprecated 5.5)
- **`__attribute__((optimize))`** — Clang doesn't support it, wrap with `#if !defined(__clang__)`

### Code Standards
- Python: FastMCP patterns, async where needed for WebSocket
- C++: UE5 coding standards for plugin code (UCLASS, UPROPERTY, etc.)
- JSON: All knowledge base entries validated against schema
- Tests: Every tool gets integration test with mock WAAPI/Builder responses
- Security: No secrets in code, validate all inputs, parameterised queries only

### File Locations
```
src/ue_audio_mcp/
├── server.py              → FastMCP entry point + lifespan
├── connection.py          → WaapiConnection + UE5PluginConnection singletons
├── tools/
│   ├── wwise_*.py         → WAAPI tool implementations (20 tools)
│   ├── ms_*.py            → MetaSounds tools (knowledge + builder + sync, 19 tools)
│   ├── bp_*.py            → Blueprint tools (builder + knowledge + sync, 15 tools)
│   └── systems.py         → Orchestrator (build_audio_system, build_aaa_project)
├── knowledge/
│   ├── db.py              → SQLite knowledge DB (9 tables, singleton)
│   ├── embeddings.py      → TF-IDF + cosine similarity search
│   ├── wwise_types.py     → Object types, properties, defaults
│   ├── metasound_nodes.py → 178 nodes, 23 categories, 128 class_name mappings
│   └── tutorials.py       → Builder API catalogue, patterns, conversions
├── templates/
│   ├── metasounds/        → 25 MS graph templates (JSON, 25/25 validated)
│   ├── blueprints/        → 30 BP templates (JSON)
│   └── wwise/             → 6 Wwise hierarchy templates (JSON)
└── graph_schema.py        → Graph spec format + 7-stage validator
ue5_plugin/UEAudioMCP/     → C++ plugin (35 commands, TCP:9877)
ue5_plugin/SIDMetaSoundNodes/ → ReSID SID chip nodes (5 custom nodes)
scripts/build_plugin.sh    → Sync source + compile via UBT
scripts/sync_nodes_from_engine.py  → Sync 842 MS nodes from engine
scripts/sync_bp_from_engine.py     → Sync 979 BP funcs from engine
scripts/verify_templates.py        → 4-check template verification
research/                  → 3 core reference docs (WAAPI, MetaSounds, MCP landscape)
tests/                     → 432 tests across 20 files
```

## Build & Deploy
```bash
# Sync source + compile (UE Editor must be closed)
./scripts/build_plugin.sh

# Sync only (no compile — UE recompiles on open)
./scripts/build_plugin.sh --sync-only

# Clean build (stale intermediates)
./scripts/build_plugin.sh --clean

# Paths:
#   Engine:  /Volumes/Koshi_T7/UN5.3/UE_5.7/
#   Project: ~/Documents/Unreal Projects/UEIntroProject/
#   Source:  ue5_plugin/UEAudioMCP/
```

## Common Patterns (6 Game Audio Systems)
1. **Gunshot** — RandomSequenceContainer + variations + pitch randomisation + ADSR
2. **Footsteps** — SwitchContainer by surface + per-surface RandomSequence + AD envelope
3. **Ambient** — BlendContainer + RTPC-driven layer volumes + zone triggers
4. **UI Sounds** — Procedural sine+envelope or sample, non-spatial, UI bus
5. **Weather/States** — StateGroup-driven SwitchContainer + crossfade transitions
6. **Spatial/3D** — ITD Panner + distance attenuation + HRTF

---

## Quick Commands
- `/ue-agent` — Launch UE5 specialist for MetaSounds/Blueprint/DSP tasks
- `/wwise-agent` — Launch Wwise specialist for WAAPI/mixing/routing tasks
- `/build-system` — Full pipeline audio system generator
- `/mcp-plugin` — UE5 plugin TCP control (35 commands)
