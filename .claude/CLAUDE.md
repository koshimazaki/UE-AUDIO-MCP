# UE Audio MCP - Project Instructions

## Project Overview
 The ** MCP server for game audio** — generating complete Wwise + MetaSounds + Blueprint audio systems from natural language.

**Architecture**: Three-layer system
- **Blueprint (WHEN)** — Game event detection, parameter setting via Remote Control API
- **MetaSounds (WHAT)** — Procedural DSP synthesis via Builder API (UE 5.4+)
- **Wwise (HOW)** — Mixing, buses, spatialization, RTPC via WAAPI (ws://127.0.0.1:8080/waapi)

**Inspired by SIDKIT** — Same agent-generated audio philosophy, different target (game engines vs hardware).

---

## Tech Stack
| Component | Technology | Notes |
|-----------|-----------|-------|
| MCP Server | Python (FastMCP) | Main server, stdio transport |
| Wwise Bridge | `waapi-client` | Official Audiokinetic Python lib, WebSocket :8080 |
| UE5 Bridge | C++ plugin + TCP (port 9877) | JSON command protocol, all UE5 tools route through this |
| Knowledge (structured) | Cloudflare D1 | Nodes, WAAPI functions, types, patterns, error fixes |
| Knowledge (semantic) | Cloudflare Vectorize | Embeddings over same D1 data for meaning-based search |
| Error Learning | Cloudflare D1 | SIDKIT pattern: error_signature → fix mapping |
| Templates | Parameterised JSON | 6+ game audio patterns |

## Knowledge Architecture (D1 + Vectorize)

**Two search paths for two different needs:**
- **D1 (structured)** — Source of truth. SQL queries by category, type, name, property.
  - `WHERE category = 'filters'` → exact node list
  - `WHERE type = 'SwitchContainer'` → Wwise object spec
- **Vectorize (semantic)** — Same entries embedded for meaning-based search.
  - "make it sound underwater" → finds Lowpass, Biquad, wet reverb pattern
  - "add spatial movement" → finds ITD Panner, Stereo Panner, Doppler

**D1 Tables:**
| Table | Contents | Example Query |
|---|---|---|
| `metasound_nodes` | 80+ nodes, inputs/outputs/types | category, data_type, name |
| `waapi_functions` | 87 WAAPI calls, params/returns | namespace, operation |
| `wwise_types` | 16 object types, properties | type_name, property |
| `audio_patterns` | Game audio patterns (gunshot, footstep...) | pattern_type, complexity |
| `error_patterns` | error_signature → successful_fix | error_hash, success_rate |
| `ue_game_examples` | Lyra, Fortnite, game audio references | game, system_type |

**Cloudflare Setup (fully independent):**
- Own D1 database: `ue-audio-knowledge` (no runtime link to SIDKIT)
- Own Vectorize index: `ue-audio-index` (own embeddings)
- Own Workers (same Cloudflare account, separate deployments)
- **One-time seed**: Copy universal DSP knowledge from SIDKIT (oscillators, filters, envelopes, LFOs, effects) — then grows independently
- No shared workers, no cross-reference, no A2HW dependency at runtime

## Key APIs
- **WAAPI**: 87 functions, WAMP/WebSocket on :8080, HTTP on :8090. Wwise MUST be running.
- **MetaSounds Builder API**: Experimental (UE 5.4+). CreateSourceBuilder, AddNode, ConnectNodes, Audition, BuildToAsset.
- **UE5 Remote Control**: Blueprint parameter wiring, game state connections.
- **AudioLink (UE 5.1+)**: One-way MetaSounds → Wwise routing.

---

## Development Phases
```
Phase 1: Wwise MCP (standalone, WAAPI)     → ships alone
Phase 2: MetaSounds Knowledge Base          → ships alone
Phase 3: UE5 Audio Plugin (Builder API)     → needs Phase 2
Phase 4: Systems Layer (orchestration)      → needs Phase 1+3
Phase 5: A2HW Protocol Spec                → parallel
```

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
├── connection.py          → WaapiConnection singleton + UE5 plugin connection
├── tools/
│   ├── wwise/             → WAAPI tool implementations
│   ├── metasounds/        → MetaSounds Builder tools (via C++ plugin)
│   ├── blueprints/        → Blueprint tools (via C++ plugin)
│   └── systems/           → High-level system generators (orchestrator)
├── knowledge/
│   ├── d1_client.py       → Cloudflare D1 structured queries
│   ├── vectorize_client.py → Cloudflare Vectorize semantic search
│   ├── wwise_types.py     → Object types, properties, defaults
│   └── metasound_nodes.py → Node catalogue, data types
├── storage/
│   └── error_learning.py  → SIDKIT-pattern error→fix storage (D1)
├── protocol/              → A2HW protocol implementation
└── templates/             → Parameterised audio pattern templates
workers/                   → Cloudflare Workers (D1 + Vectorize API)
research/                  → API research docs (WAAPI, MetaSounds, UE MCP landscape)
tests/                     → Integration & unit tests
```

### SIDKIT-Inspired Patterns
- **Error learning**: When builds fail, store error_signature + fix in D1. Query before generating to avoid known mistakes.
- **Agentic iteration**: Tools can retry with feedback (max 10 iterations, like SIDKIT's compile loop).
- **Knowledge search**: Agent has `search_knowledge` tool — queries D1 by type OR Vectorize by meaning.
- **Template system**: Parameterised patterns (gunshot, footstep, ambient, UI, weather, spatial) — like SIDKIT's game/synth/sequencer templates.

---

## Research Available
- `research/research_waapi_mcp_server.md` — Complete WAAPI reference (87 functions, all object types, 5 game audio patterns with code, AudioLink setup)
- `research/research_metasounds_game_audio.md` — MetaSounds nodes (80+), Builder API, 6 game audio patterns, Lyra reference architecture
- `research/research_unreal_mcp_landscape.md` — 10 repos analysed, build-vs-fork decision, architecture synthesis

## Reference Implementations
- **SIDKIT Agent** (`sidkit-agent/`) — Rust, agentic loop + ToolExecutor, 8 tools, error learning (SQLite), knowledge base (19 categories, semantic search), GCC compile→flash pipeline. **Primary architecture reference.**
- **BilkentAudio/Wwise-MCP** (23 stars) — Existing Wwise MCP, FastMCP + WAAPI wrapper. Reference for WAAPI patterns, NOT forking.
- **blender-mcp** (16.9k stars) — Gold standard: addon (socket server inside app) + MCP server (FastMCP). TCP+JSON pattern.
- **chongdashu/unreal-mcp** (1,370 stars) — UE5 MCP leader. C++ plugin + Python. Modular tool files pattern. No audio.
- **runreal/unreal-mcp** (70 stars) — No-plugin approach via UE Python remote exec. Lightweight but can't do Builder API.
- **VibeComfy MCP** — 8,400+ ComfyUI nodes via MCP (node database pattern)
- **Lyra Starter Game** — Epic's canonical UE5 audio reference

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
