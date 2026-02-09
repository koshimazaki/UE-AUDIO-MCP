# Changelog

## v0.0.2 (2026-02-09)

### Added
- **53 MCP tools** across 5 categories (Wwise, MetaSounds, Blueprint, UE5, Orchestration)
- **C++ UE5 plugin** with 25 TCP commands (MetaSounds Builder API, Blueprint scanner, asset queries)
- **ReSID SID chip nodes** — 5 custom MetaSounds nodes (Oscillator, Envelope, Filter, Voice, Chip)
- **Blueprint Scanner** — deep-inspects 7 K2Node types with audio relevance detection
- **Editor Menu** — "Audio MCP" in main menu bar (Scan Project, Export MetaSounds, Status)
- **MetaSounds Graph Exporter** — full graph export with types, defaults, variables, interfaces
- **AAA Project Orchestrator** — `build_aaa_project` generates 6-category audio infrastructure
- **Knowledge Base** — 144 MetaSounds nodes (798 pins), 22K+ Blueprint API nodes, 66 WAAPI functions
- **Semantic Search** — TF-IDF + cosine similarity across all knowledge sources
- **61 templates** — 22 MetaSounds + 30 Blueprint + 6 Wwise + 3 SID
- **332 tests** all passing
- **4 agent skills** — /mcp-plugin, /metasound-dsp, /unreal-bp, /build-system
- **Batch scanner** — `scripts/scan_project.py` with DB import and embedding rebuild

### Fixed
- UE 5.7.2 compile fixes (8 issues: TNodeFacade, ReSID duplicate symbols, deprecated APIs)
- Pin name migration from Epic docs (230 pins corrected, 48 marked optional)
- Code review cleanup (dedup, rename, robustness fixes)

## v0.0.1 (2026-02-06)

### Added
- Initial Wwise MCP server (20 tools, WAAPI bridge)
- MetaSounds knowledge base (SQLite, 8 tables)
- Graph spec format with 7-stage validator
- 6 MetaSounds templates (gunshot, footsteps, ambient, spatial, ui_sound, weather)
- 52 tests passing
