# UE Audio MCP — Status & Next Steps

## Current Status (2026-02-09)

```
Component           Count    Status
─────────────────   ──────   ──────────────────
MCP Tools           53       All working (Python)
C++ Plugin Cmds     25       Compiled on UE 5.7.2 macOS
Tests               332      All passing
MetaSounds Nodes    144      20 categories, 798 pins
Templates           22       MS + BP + Wwise
Patterns            10       build_audio_system orchestrator
Slash Commands      4        /ue-agent, /wwise-agent, /build-system, /mcp-plugin
```

### Pipeline Layers

```
Layer            Tools    Execution            Status
─────────────    ──────   ──────────────────   ──────────
Wwise (WAAPI)    20       LIVE via WS:8080     COMPLETE
MetaSounds       18       C++ plugin TCP:9877  COMPILED, UNTESTED LIVE
Blueprint        6        Knowledge + scan     COMPLETE (scan/list/export)
Orchestration    3        build_audio_system   COMPLETE (offline mode verified)
Knowledge        6        SQLite + TF-IDF      COMPLETE
```

### Completed Phases
- [x] Phase 1: Wwise MCP Server (20 tools, WAAPI bridge)
- [x] Phase 2: MetaSounds Knowledge Base (144 nodes, semantic search)
- [x] Phase 3: UE5 Plugin + Python connectivity (25 C++ commands, TCP protocol)
- [x] Phase 4: Orchestration Layer (10 patterns, 3-mode auto-detect)
- [x] ReSID MetaSounds Port (5 custom SID chip nodes)
- [x] UE 5.7.2 Compile Fixes (8 fixes, clean build)
- [x] Blueprint Scanner + Editor Menu (scan/list/export from editor)
- [x] MetaSounds Graph Exporter (full graph export with types, defaults, variables)
- [x] Code Review Cleanup (dedup, rename, robustness fixes)

---

## Next Steps

### Step 1: Test Plugin Live
- [ ] Open UE 5.7 project with plugin compiled
- [ ] Test TCP connection (Python `ue5_connect` → plugin `ping`)
- [ ] Test `create_builder` + `add_node` + `connect` + `build_to_asset`
- [ ] Test `audition` — hear generated MetaSounds live
- [ ] Test `export_metasound` — round-trip export from editor
- [ ] Test `scan_blueprint` + `list_assets` from editor menu
- [ ] Fix any runtime issues found

### Step 2: Extract BPs & MetaSounds from Real Projects
- [ ] **UE Intro Project** (demo we have) — 46 BPs, 13 MS graphs (already scanned)
- [ ] **Stack O Bot** — Epic sample project, extract all BPs + MetaSounds
- [ ] **Lyra Starter Game** — Epic's canonical audio reference, 50+ BPs expected
- [ ] Import all scan data to knowledge DB
- [ ] Rebuild TF-IDF embeddings with expanded corpus
- [ ] Validate pin names and node types against real engine data

### Step 3: Test Blueprints & Spawning
- [ ] Test building MetaSounds assets from templates in each project
- [ ] Test spawning audio actors in PIE (Play In Editor)
- [ ] Test Wwise integration (WAAPI → event creation → trigger)
- [ ] Test AudioLink bridge (MetaSounds → Wwise bus)
- [ ] Test parameter wiring (Blueprint → MetaSounds input)
- [ ] Document any gaps or failures

### Step 4: Video Demo (2-3 min)
- [ ] Script demo flow: prompt → system spawns → audio plays
- [ ] Show: "make me weapon audio" → full stack creates
- [ ] Show: "add ambient" → layers on existing
- [ ] Show: knowledge search ("what handles spatialization?")
- [ ] Show: project scanning from editor menu
- [ ] Show: offline mode generating specs
- [ ] Record with OBS, clean audio capture

### Step 5: Extended — Full Game Level Demo
- [ ] Pick or create a game-like level (character + environment)
- [ ] Full sound design: footsteps, weapons, ambient, UI, weather
- [ ] Character with weapon using full 3-layer stack
- [ ] Multiple audio zones with different ambiences
- [ ] Dynamic weather affecting audio (rain → muffled sounds)
- [ ] Record as ultimate portfolio/demo material

### Step 6: Polish & Ship
- [ ] Open source release (see .claude/plans/ for v0.0.2 plan)
- [ ] Clean git history (squash or BFG)
- [ ] LICENSE, CHANGELOG, pyproject.toml updates
- [ ] GitHub release with version tag
- [ ] Social media post with video
- [ ] Link from SIDKIT / portfolio

---

## Known Issues

- MetaSounds Builder API is experimental — may change between UE versions
- Blueprint layer can't create BP graphs programmatically (use template BPs + parameter wiring)
- AudioLink setup not automated — manual configuration in editor
- Plugin TCP drops after ~17 rapid requests — need reconnect logic (scan_project.py has workaround)
- SIDChipNode per-voice outputs silent at runtime (voice_output[] never populated)
