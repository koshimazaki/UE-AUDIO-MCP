# UE Audio MCP — Progress & Roadmap

## Pipeline Status

```
Layer            Python Tools    Execution           Status
─────────────    ────────────    ────────────────    ──────
Wwise (WAAPI)    20 tools        LIVE via WS:8080    COMPLETE
MetaSounds       18 tools        C++ plugin written  CODE READY, UNCOMPILED
Blueprint        4 tools         Knowledge/query     SPEC ONLY
AudioLink        Documented      Not implemented     GAP
Sample import    Wwise: done     UE5 Content: no     HALF
Lifecycle        None            None                GAP
```

## What's Built

- [x] Wwise MCP — 20 tools, WAAPI bridge, works live
- [x] Knowledge DB — 116 MetaSounds nodes, 22K+ BP API nodes, 66 WAAPI functions
- [x] Semantic search — TF-IDF + cosine similarity, <1ms queries
- [x] MetaSounds graph schema — JSON format, 7-stage validator, Builder API command generation
- [x] MetaSounds templates — 22 templates (gunshot, footsteps, ambient, wind, weather, vehicle_engine, sfx_generator, etc.)
- [x] Blueprint templates — 30 templates from Epic tutorials + community
- [x] Wwise templates — 6 integration specs
- [x] Orchestration — `build_audio_system` with 10 patterns, 3-mode auto-detection
- [x] C++ plugin source — 18 commands, TCP:9877, thread-safe dispatch
- [x] UE 5.7 Builder API knowledge — 68+ functions, graph variables, presets, live update
- [x] Blueprint API scraper — Playwright, 22K+ nodes from Epic SPA
- [x] UE4→UE5 conversion map — 14 entries (Sound Cue → MetaSounds)
- [x] README — updated with full inventory
- [x] CREDITS — all tutorial authors attributed
- [x] 241 tests passing

## Phase: Get It Running

### 1. UE5.7 + Plugin Compile
- [ ] Install UE5.7 (downloading)
- [ ] Compile C++ plugin in UE5.7 — may need API changes from 5.4
- [ ] Test TCP connection (Python ↔ plugin)
- [ ] Test `ping` command round-trip
- [ ] Test `create_builder` + `add_node` + `build_to_asset`

### 2. Wwise Project Setup
- [ ] Create blank Wwise project with standard bus hierarchy (Master/SFX/Music/Ambient/UI/Vehicles)
- [ ] Set up AudioLink bus
- [ ] Test WAAPI connection from MCP
- [ ] Script/template for one-click Wwise project bootstrap

### 3. Samples
- [ ] Find free .wav samples (Freesound CC0, Epic Starter Content, TechAudioTools on Fab)
- [ ] Import to Wwise via `wwise_import_audio`
- [ ] Import to UE5 Content folder (manual or script)
- [ ] Test Wave Player references in MetaSounds

### 4. First Live Test
- [ ] Build one MetaSounds asset live via MCP → hear audio
- [ ] Build one Wwise event live via MCP → trigger in editor
- [ ] Connect AudioLink (MetaSounds output → Wwise bus)

## Phase: Demo Features

### 5. Lifecycle Management (remove/swap/list)
- [ ] `list_active_systems` — track what's been spawned (Python state)
- [ ] `remove_audio_system` — tear down Wwise objects + delete MS assets
- [ ] `replace_audio_system` — swap one pattern for another in-place
- [ ] Add C++ plugin commands for asset deletion
- [ ] Demo flow: "make gunshot" → "add ambient" → "swap gunshot for SFX" → "clear all"

### 6. Blueprint Integration
- [ ] Pre-make template BP actors in editor (footstep trigger, weapon fire, ambient zone, etc.)
- [ ] Wire parameters at runtime via Remote Control API
- [ ] Test: MCP sets float parameter → MetaSounds responds → audio changes
- [ ] NOTE: Programmatic BP graph creation is unsolved — use template BPs + parameter wiring

### 7. Claude Code Skills
- [ ] `/spawn-audio` — create audio system in current scene
- [ ] `/swap-audio` — replace one system with another
- [ ] `/clear-audio` — remove all spawned audio
- [ ] Update `/build-system` for live execution mode
- [ ] Clean context between operations

## Phase: Demo & Ship

### 8. Demo Scene
- [ ] Pick UE5 tutorial scene or marketplace level
- [ ] Place audio triggers (zones, animation notifies, input actions)
- [ ] Set up camera path for recording

### 9. Record Video (2-3 min)
- [ ] Show: "make me weapon audio" → system spawns
- [ ] Show: "now add ambient" → layers on top
- [ ] Show: "swap weapons for SFX generator" → replaces
- [ ] Show: knowledge search ("what node handles spatialization?")
- [ ] Show: offline mode generating specs

### 10. Polish & Publish
- [ ] Fix 6 bp_node_specs.json parse errors
- [ ] Clean up any UE5.7 API deprecation warnings
- [ ] GitHub release with version tag
- [ ] Social media post with video
- [ ] Link from SIDKIT / portfolio

## Known Issues

- `bp_node_specs.json` has JSON parse errors (6 test failures) — scraped data corruption
- C++ plugin never compiled — may need UE5.7 API adjustments
- Blueprint layer is spec-only — can't create BP graphs programmatically
- AudioLink setup not automated — manual configuration in editor
- `security hook (make_sure.sh)` flags false positives on db.py

## Architecture Notes

### Why Wwise + MetaSounds?
- MetaSounds = DSP engine (makes the sound)
- Wwise = audio middleware (manages the mix, states, spatialization)
- AudioLink bridges them: MetaSounds → Wwise bus
- Blueprint handles game logic triggers and parameter setting

### Why Blueprint creation is hard
No UE5 API exposes programmatic Blueprint graph creation. Options:
1. Python remote exec (fragile, version-dependent)
2. Pre-made template BPs + runtime parameter wiring (our approach)
3. C++ UEdGraph manipulation (complex, undocumented)

### A2HW Protocol
This project is the second implementation of A2HW (Agent-to-Hardware):
- SIDKIT: A2HW v1 → Teensy SID chip (1 renderer)
- UE Audio MCP: A2HW v2 → Wwise + MetaSounds + Blueprint (3 renderers)
- Same pattern: intent → schema → validate → render
- Protocol spec: see SIDKIT docs/architecture/A2HW-PROTOCOL.md
