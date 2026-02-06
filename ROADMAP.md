# Development Roadmap

## Phase 1: Wwise MCP (Standalone)
**Target: 1 weekend | No UE5 needed | Ships alone as portfolio piece**

The Blender MCP pattern applied to Wwise. One Python server, `waapi-client` does the heavy lifting.

### 1.1 Core Server
- [ ] FastMCP server skeleton with `waapi-client` connection
- [ ] `WwiseConnection` singleton with health check + reconnection
- [ ] Auto-detect: is Wwise running? Graceful error if not
- [ ] `wwise_connect` — connect + return project info
- [ ] `wwise_get_info` — version, project name, platform

### 1.2 Object Tools
- [ ] `wwise_create_object` — create any type (Sound, RandomSequenceContainer, SwitchContainer, BlendContainer, ActorMixer, Event, Bus, AuxBus)
- [ ] `wwise_set_property` — volume, pitch, lowpass, highpass, looping
- [ ] `wwise_set_reference` — output bus, attenuation, switch group
- [ ] `wwise_query` — WAQL queries for finding objects
- [ ] `wwise_import_audio` — import WAV files into hierarchy

### 1.3 Event & Mixing Tools
- [ ] `wwise_create_event` — event with play/stop actions
- [ ] `wwise_set_rtpc` — create RTPC, set curves
- [ ] `wwise_assign_switch` — switch container child assignments
- [ ] `wwise_set_attenuation` — attenuation curves (distance, cone)
- [ ] `wwise_generate_banks` — soundbank generation
- [ ] `wwise_preview` — transport play/stop for auditioning
- [ ] `wwise_save` — save project

### 1.4 Escape Hatch
- [ ] `execute_waapi` — generic WAAPI call (uri + args), like Blender MCP's `execute_blender_code`

### 1.5 Templates (Higher-Level)
- [ ] `template_gunshot` — RandomSequenceContainer + variations + pitch rand + event
- [ ] `template_footsteps` — SwitchContainer by surface + RandomSequence per surface
- [ ] `template_ambient` — BlendContainer + RTPC-driven layer volumes
- [ ] `template_ui_sound` — Sound + event + UI bus routing
- [ ] `template_weather_states` — StateGroup-driven SwitchContainer

### Deliverable
Standalone Wwise MCP server. Install via pip/npm, connect to running Wwise, create audio hierarchies from prompts. GitHub release + demo video.

---

## Phase 2: MetaSounds Knowledge Base
**Target: 1-2 days | No UE5 needed at runtime**

Build the node database and graph spec format. This works offline — generates JSON specs that map to Builder API calls.

### 2.1 Node Database
- [ ] Catalogue all 80+ MetaSounds node types with inputs/outputs/types
- [ ] Categorise: Generators, Wave Players, Envelopes, Filters, Delays, Dynamics, Triggers, Arrays, Math, Mix, Spatialization, Music, Random
- [ ] Store as structured JSON (same pattern as VibeComfy's 8,400 nodes)
- [ ] Node search by category, name, capability

### 2.2 Graph Spec Format
- [ ] Define JSON intermediate representation for MetaSounds graphs
- [ ] Nodes, connections, inputs, outputs, defaults
- [ ] Maps 1:1 to Builder API calls
- [ ] Validate spec against node database (type checking)

### 2.3 Pattern Templates
- [ ] Gunshot: RandomGet → WavePlayer → ADSR → filter → reverb tail
- [ ] Footsteps: SurfaceType input → TriggerRoute → per-surface chains
- [ ] Ambient: looped base + TriggerRepeat details + LFO drift
- [ ] Spatial: ITD Panner / Stereo Panner from Spatialization interface
- [ ] UI: Sine + AD Envelope for procedural clicks, TriggerRoute for types
- [ ] Weather states: TriggerRoute → crossfade layers → InterpTo + dynamic filter

### Deliverable
MetaSounds knowledge base + graph spec generator. Given a text description, outputs a JSON spec documenting the exact graph structure. Useful even without UE5 — sound designers can read the spec and build manually.

---

## Phase 3: UE5 Audio Plugin
**Target: 1 week | Requires UE5 running**

The Blender addon equivalent. A C++ plugin running inside UE5 Editor that receives commands and executes Builder API calls.

### 3.1 Plugin Bridge
- [ ] C++ UE5 plugin with TCP server (port 9877)
- [ ] JSON command protocol (same pattern as Blender addon)
- [ ] Main thread scheduling via UE5 game thread task (equivalent of `bpy.app.timers`)
- [ ] Health check endpoint

### 3.2 MetaSounds Builder Tools
- [ ] `ms_create_source` — CreateSourceBuilder with interface selection
- [ ] `ms_create_patch` — CreatePatchBuilder
- [ ] `ms_add_node` — AddNode by class name
- [ ] `ms_connect_nodes` — ConnectNodes (output handle → input handle)
- [ ] `ms_set_default` — SetNodeInputDefault
- [ ] `ms_add_input` / `ms_add_output` — expose parameters
- [ ] `ms_audition` — Audition() on AudioComponent, hear it NOW
- [ ] `ms_live_update` — modify graph while playing (UE 5.5+ LiveUpdate)
- [ ] `ms_save_asset` — BuildToAsset() to Content Browser
- [ ] `ms_list_nodes` — enumerate available node types from engine

### 3.3 Blueprint Audio Tools
- [ ] `bp_create_audio_manager` — generate audio manager Blueprint
- [ ] `bp_create_trigger` — line trace surface detector, overlap volume, anim notify
- [ ] `bp_wire_params` — connect game state variables to MetaSounds/Wwise params

### 3.4 MCP Integration
- [ ] Add UE5 tools to the main MCP server
- [ ] Auto-detect: UE5 plugin running? Expose MetaSounds + Blueprint tools
- [ ] Unified tool namespace alongside Wwise tools

### Deliverable
UE5 plugin + MCP tools. Generate MetaSounds patches from prompts, audition live, save to project. Blueprint trigger logic generation.

---

## Phase 4: Systems Layer
**Target: 1-2 weeks | Requires Wwise + UE5**

The orchestrator. One command generates complete audio systems across all three layers.

### 4.1 System Generators
- [ ] `build_footsteps` — MetaSounds patch + Blueprint surface detector + Wwise bus/attenuation
- [ ] `build_weather` — multiple patches + Blueprint weather reader + Wwise states/RTPC
- [ ] `build_ambient` — zone patches + Blueprint overlap volumes + Wwise spatial mix
- [ ] `build_weapon_audio` — shot + shell + tail + Blueprint fire event + Wwise layers
- [ ] `build_ui_audio` — procedural UI set + Blueprint event router + Wwise UI bus
- [ ] `build_system` — generic: describe any audio behaviour, get all layers

### 4.2 AudioLink Bridge
- [ ] Configure AudioLink routing: MetaSounds → Wwise bus
- [ ] Create Wwise Audio Input events for procedural sources
- [ ] Wire UE5 attenuation to Wwise spatialization

### 4.3 Session Context
- [ ] Track what's been generated in the current session
- [ ] Cross-system awareness (footsteps know about weather)
- [ ] Undo/rollback via Wwise undo groups + UE5 transactions

### 4.4 Error Learning
- [ ] Store build errors (same pattern as SIDKIT on Cloudflare D1)
- [ ] Feed errors back to improve next generation
- [ ] Track which templates/patterns succeed

### Deliverable
Complete game audio systems from single prompts. Weather, footsteps, weapons, ambient, UI — all wired across Blueprint + MetaSounds + Wwise. Demo video showing end-to-end: prompt → running game audio.

---

## Phase 5: A2HW Protocol Spec
**Target: Ongoing, publish with Phase 4**

Formalise the Agent-to-Hardware protocol as a standard that works across targets.

### 5.1 Protocol Definition
- [ ] JSON schema for synthesis descriptions
- [ ] Parameter types: oscillator, filter, envelope, LFO, sequencer, effect
- [ ] Target-agnostic: same description compiles to SysEx, MetaSounds, Wwise
- [ ] Version the protocol

### 5.2 Target Adapters
- [ ] SIDKIT adapter (SysEx → Teensy) — already exists
- [ ] MetaSounds adapter (Builder API → UE5)
- [ ] Wwise adapter (WAAPI → Wwise)
- [ ] Browser adapter (JS → ModuleRunner) — already exists

### 5.3 Documentation
- [ ] Protocol spec document
- [ ] Examples for each target
- [ ] Integration guide for third-party tools

### Deliverable
Published A2HW protocol spec. Any tool can implement it to target any audio platform.

---

## Dependencies

```
Phase 1 (Wwise MCP) ──────────────────────────→ ships alone
Phase 2 (MetaSounds KB) ──────────────────────→ ships alone (knowledge base)
Phase 3 (UE5 Plugin) ── depends on Phase 2 ──→ ships with Phase 1
Phase 4 (Systems) ──── depends on 1 + 3 ─────→ the full product
Phase 5 (A2HW) ───── parallel, ongoing ──────→ the standard
```

Phase 1 and 2 are independent — build in parallel.
Phase 3 needs Phase 2's node database.
Phase 4 needs everything.
Phase 5 is documentation, runs alongside.

---

## Tech Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| MCP framework | FastMCP (Python) | Wwise `waapi-client` is Python, matches |
| Wwise library | `waapi-client` | Official, low-level, best for wrapping |
| UE5 plugin language | C++ | Builder API is C++, performance |
| Plugin bridge | TCP socket (JSON) | Proven by Blender MCP (16.9k stars) |
| Knowledge base | JSON files | Simple, versionable, embeddable |
| Template format | Parameterised JSON | Same pattern as VibeComfy |

---

## Demo Targets

| Demo | Audience | Shows |
|------|----------|-------|
| Wwise hierarchy from prompt | Game audio professionals | WAAPI automation, first Wwise MCP |
| MetaSounds patch generation | UE5 audio designers | Builder API, procedural audio |
| Full weather system | Studios, hiring managers | All three layers, end-to-end |
| A2HW multi-target | SIGGRAPH, research | Same prompt → hardware + browser + game engine |
| SIDKIT → UE5 bridge | Portfolio | SIDKIT architecture at game engine scale |
