# UE Audio MCP - Project Instructions

## Project Overview
Building the **first MCP server for game audio** — generating complete Wwise + MetaSounds + Blueprint audio systems from natural language.

**Architecture**: Three-layer system
- **Blueprint (WHEN)** — Game event detection, parameter setting via Remote Control API
- **MetaSounds (WHAT)** — Procedural DSP synthesis via Builder API (UE 5.4+)
- **Wwise (HOW)** — Mixing, buses, spatialization, RTPC via WAAPI (ws://127.0.0.1:8080/waapi)

**Inspired by SIDKIT** — Same agent-generated audio philosophy, different target (game engines vs hardware).

---

## Tech Stack
| Component | Technology | Notes |
|-----------|-----------|-------|
| MCP Server | Python (FastMCP) | Main server |
| Wwise Bridge | `waapi-client` | Official Audiokinetic Python lib |
| UE5 Bridge | C++ plugin + TCP (port 9877) | JSON command protocol |
| Knowledge Base | JSON files | 80+ MetaSounds nodes, 16 Wwise types |
| Templates | Parameterised JSON | 6 game audio patterns |

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
src/tools/wwise/       → WAAPI tool implementations
src/tools/metasounds/  → MetaSounds Builder tools
src/tools/blueprints/  → Blueprint generation tools
src/knowledge/         → Node databases, type definitions
src/protocol/          → A2HW protocol implementation
src/systems/           → High-level system generators
templates/             → Parameterised audio pattern templates
research/              → API research docs (WAAPI, MetaSounds)
tests/                 → Integration & unit tests
```

---

## Research Available
- `research/research_waapi_mcp_server.md` — Complete WAAPI reference (87 functions, all object types, 5 game audio patterns with code, AudioLink setup)
- `research/research_metasounds_game_audio.md` — MetaSounds nodes (80+), Builder API, 6 game audio patterns, Lyra reference architecture

## Reference Implementations
- **SIDKIT** — Agent-generated hardware synths (SysEx protocol)
- **VibeComfy MCP** — 8,400+ ComfyUI nodes via MCP (node database pattern)
- **Blender MCP** — Controls Blender via TCP+JSON plugin bridge (16.9k stars)
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
