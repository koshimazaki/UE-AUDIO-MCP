# UE Audio MCP

**Build Complete game audio systems from natural language.**

One MCP server. Three audio engines. Wwise + MetaSounds + Blueprint — wired together, running in your game.

> "Build weather-responsive ambient with rain, wind, and clear states that crossfade based on intensity"
>
> → 3 MetaSounds patches generated → Blueprint trigger logic wired → Wwise bus hierarchy + RTPC curves created → AudioLink bridged → Running in game. You hear rain starting.

---

## Quick Start (Phase 1 — Wwise MCP)

Phase 1 ships standalone — only Wwise required, no UE5 needed.

### Install

```bash
git clone https://github.com/koshimazaki/UE5-WWISE.git
cd UE5-WWISE
pip install -e ".[dev]"
```

### Run

```bash
# Start the MCP server (auto-connects to Wwise on ws://127.0.0.1:8080/waapi)
ue-audio-mcp
```

Wwise Authoring must be running with WAAPI enabled (`Project > User Preferences > Enable Wwise Authoring API`). If Wwise isn't running, the server starts anyway — connect later with `wwise_connect`.

### MCP Client Configuration

Add to your MCP client config (Claude Desktop, Cursor, etc.):

```json
{
  "mcpServers": {
    "ue-audio-mcp": {
      "command": "ue-audio-mcp",
      "transport": "stdio"
    }
  }
}
```

### Test

```bash
pytest tests/ -v    # 107 tests, all passing
```

---

## The Problem

Game audio systems take weeks to build. A weather ambient system needs:
- MetaSounds patches for rain, wind, clear (procedural DSP)
- Blueprint logic reading weather state, setting parameters
- Wwise bus hierarchy, RTPC curves, state groups, spatial mixing
- AudioLink routing procedural audio into the mix pipeline
- Everything wired together and tested

Each layer is a different tool, different specialist, different iteration cycle. Sound designers wait for programmers. Programmers wait for design specs. Everyone iterates manually.

## The Solution

Describe what you want. Get a complete audio system.

```
You: "generative footsteps that change by surface with weight variation"

MCP generates and deploys:

  MetaSounds:  MS_Footstep_Proc
    ├── SurfaceType input (Int32) → Trigger Route
    ├── Per-surface: Grass (soft filter), Concrete (bright), Metal (resonant), Wood (creaky)
    ├── RandomGet per surface array, AD envelope per step
    └── Speed + Weight inputs modulate pitch, volume, filter

  Blueprint:   BP_FootstepSystem
    ├── Animation notify → fire step event
    ├── Line trace → Physical Material → SurfaceType
    ├── Character velocity → Speed, mass → Weight
    └── All params wired to MetaSounds inputs

  Wwise:       Footstep bus + attenuation
    ├── SFX bus routing with distance LP filter
    ├── RTPC: Speed → volume + pitch range
    └── AudioLink receives procedural audio from MetaSounds

  → Applied to character. Walking sounds change as you cross surfaces.
```

Not replacing sound designers — giving them a first draft in seconds instead of days. They refine from there.

---

## Architecture

```
                    Claude / Cursor / Any MCP Client
                                │
                                │ MCP Protocol (stdio)
                                v
                    ┌───────────────────────┐
                    │    UE Audio MCP       │
                    │    (one server)       │
                    └───────┬───────────────┘
                            │
              ┌─────────────┼─────────────────┐
              v             v                 v
     ┌──────────────┐ ┌──────────┐  ┌──────────────────┐
     │  Wwise Tools │ │ MetaSound│  │ Blueprint Tools  │
     │  (WAAPI)     │ │ Tools    │  │ (Remote Control) │
     └──────┬───────┘ └────┬─────┘  └────────┬─────────┘
            │              │                 │
            v              v                 v
     ┌──────────────┐ ┌──────────┐  ┌──────────────────┐
     │ Wwise App    │ │ UE5      │  │ UE5 Editor       │
     │ (WAAPI :8080)│ │ Plugin   │  │ (Remote Control) │
     └──────────────┘ │ (Builder │  └──────────────────┘
                      │  API)    │
                      └──────────┘
```

### The Three Layers

| Layer | Engine | Role | API | Analogy |
|-------|--------|------|-----|---------|
| **Blueprint** | UE5 | WHEN — detects game events, sets parameters | Remote Control API | Stage manager |
| **MetaSounds** | UE5 | WHAT — procedural DSP, synthesis, generates the actual sound | Builder API (via plugin) | The instrument |
| **Wwise** | Standalone | HOW — mixing, buses, spatialization, RTPC, delivery | WAAPI (WebSocket :8080) | The mixing desk |

### Signal Flow

```
BLUEPRINT (WHEN)                 METASOUNDS (WHAT)              WWISE (HOW)
────────────────                 ─────────────────              ──────────────
Player shoots             →     Gunshot synthesis        →     SFX bus, reverb
Player steps on grass     →     Soft filtered footstep   →     Distance attenuation
Weather changes to rain   →     Layered rain + droplets  →     Ambient bus, RTPC mix
UI button clicked         →     Procedural click         →     UI bus (2D, no spatial)
Enter forest zone         →     Dense ambient layers     →     Zone crossfade
```

**AudioLink (UE 5.1+)** bridges MetaSounds → Wwise. One-way: procedural audio flows into Wwise's mixing pipeline.

---

## Wwise Tools (Phase 1 — Shipped)

20 tools across 5 modules. All return JSON `{"status": "ok/error", ...}` for consistent LLM parsing.

### Core (5 tools)

| Tool | Description | WAAPI |
|------|-------------|-------|
| `wwise_connect` | Connect to Wwise (default `ws://127.0.0.1:8080/waapi`) | `ak.wwise.core.getInfo` |
| `wwise_get_info` | Get Wwise version, platform, project info | `ak.wwise.core.getInfo` |
| `wwise_query` | Query objects using WAQL with custom return fields | `ak.wwise.core.object.get` |
| `wwise_save` | Save the current Wwise project | `ak.wwise.core.project.save` |
| `execute_waapi` | Raw WAAPI escape hatch — call any of 87 WAAPI functions | Any URI |

### Objects (4 tools)

| Tool | Description | WAAPI |
|------|-------------|-------|
| `wwise_create_object` | Create any Wwise object (19 types, validated) | `ak.wwise.core.object.create` |
| `wwise_set_property` | Set Volume, Pitch, Lowpass, IsLoopingEnabled, etc. (24 known properties) | `ak.wwise.core.object.setProperty` |
| `wwise_set_reference` | Assign OutputBus, Attenuation, SwitchGroup, Effects | `ak.wwise.core.object.setReference` |
| `wwise_import_audio` | Import WAV files (batch up to 100, 3 import modes) | `ak.wwise.core.audio.import` |

### Events & Mixing (4 tools)

| Tool | Description | WAAPI |
|------|-------------|-------|
| `wwise_create_event` | Create Event + Action (18 action types: Play, Stop, Pause, etc.) | `ak.wwise.core.object.create` |
| `wwise_set_rtpc` | Create GameParameter for RTPC binding with curve points | `ak.wwise.core.object.create` |
| `wwise_assign_switch` | Assign children to switch/state values in SwitchContainers | `ak.wwise.core.switchContainer.addAssignment` |
| `wwise_set_attenuation` | Create Attenuation ShareSet with distance curves (7 curve types) | `ak.wwise.core.object.setAttenuationCurve` |

### Preview (2 tools)

| Tool | Description | WAAPI |
|------|-------------|-------|
| `wwise_preview` | Play/stop/pause via transport control | `ak.wwise.core.transport.*` |
| `wwise_generate_banks` | Generate SoundBanks by name | `ak.wwise.core.soundbank.generate` |

### Templates (5 tools)

One-call generators for complete game audio patterns. All wrapped in **undo groups** for atomic rollback.

| Tool | What It Creates |
|------|----------------|
| `template_gunshot` | RandomSequenceContainer + N variation Sounds + pitch randomization + Play Event |
| `template_footsteps` | SwitchGroup + SwitchContainer + per-surface RandomSequenceContainers + Play Event |
| `template_ambient` | GameParameter (RTPC) + BlendContainer + looped layer Sounds + Play Event |
| `template_ui_sound` | ActorMixer(UI) + Sound + OutputBus routing + Play Event |
| `template_weather_states` | StateGroup + SwitchContainer + per-state looped Sounds + assignments + Play Event |

### Knowledge Base (Phase 2 — Shipped)

1,209 entries across 8 SQLite tables. Semantic search via TF-IDF embeddings (<1ms queries, no ML deps).

7 MCP tools: `ms_list_nodes`, `ms_node_info`, `ms_search_nodes`, `ms_list_categories`, `ms_validate_graph`, `ms_graph_to_commands`, `ms_graph_from_template`.

#### Data Sources & Counts

| Table | Entries | Source | What It Contains |
|-------|---------|--------|-----------------|
| `metasound_nodes` | 112 | [MetaSounds docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-reference-guide-in-unreal-engine) + Editor node browser | 16 categories, full pin specs (name/type/default), complexity ratings |
| `blueprint_core` | 946 | [Epic Blueprint API Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI) | 61 categories, 45 UE5 C++ classes, 11 sub-modules |
| `waapi_functions` | 66 | [Audiokinetic WAAPI Reference](https://www.audiokinetic.com/en/library/edge/?source=SDK&id=waapi__reference.html) | 11 namespaces, params/returns per function |
| `blueprint_audio` | 55 | Epic Blueprint API + Audiokinetic Wwise UE5 Integration | 4 classes: GameplayStatics, AudioComponent, Quartz, AudioVolume |
| `wwise_types` | 19 | WAAPI docs + Wwise Authoring reference | Real descriptions, property lists, category mapping |
| `audio_patterns` | 6 | Hand-authored from game audio patterns | gunshot, footsteps, ambient, spatial, ui_sound, weather |
| `ue_game_examples` | 5 | Lyra Starter Game source analysis | Whizby, dovetail, ambient, music, submix architectures |
| `error_patterns` | 0 (grows at runtime) | SIDKIT-pattern error learning | error_signature → fix mapping with success_count |

#### Blueprint Node Modules (946 nodes)

| Module | Nodes | UE5 C++ Source |
|--------|-------|---------------|
| `math_spatial.py` | 231 | `UKismetMathLibrary` (vector/rotator/quat/transform) |
| `math_core.py` | 143 | `UKismetMathLibrary` (bool/byte/int/float/trig) |
| `math_utility.py` | 114 | `UKismetMathLibrary` (interp/random/noise/color/datetime) |
| `gameplay.py` | 100 | `UGameplayStatics` (damage/player/actor/level/time) |
| `string_array.py` | 92 | `UKismetStringLibrary`, `UKismetArrayLibrary` |
| `system.py` | 80 | `UKismetSystemLibrary` (debug/system/console/asset) |
| `audio.py` | 60 | `UGameplayStatics`, `UAkGameplayStatics` (Wwise) |
| `flow_control.py` | 59 | `UK2Node_*`, `UKismetSystemLibrary` |
| `collision_physics.py` | 32 | `UKismetSystemLibrary` (traces/overlaps) |
| `rendering.py` | 20 | `UMaterialInstanceDynamic` |
| `input_nodes.py` | 15 | `UEnhancedInputComponent` |

#### MetaSounds Graph Templates (6 patterns)

| Template | Nodes | Key DSP Chain |
|----------|-------|--------------|
| `gunshot` | 5 | Array Random Get → Wave Player → ADSR → Multiply |
| `footsteps` | 6 | Trigger Route → Random Get → Wave Player → AD Envelope → LPF |
| `ambient` | 3 | Wave Player (Stereo) → LFO modulation → Stereo Mixer |
| `spatial` | 2 | Wave Player (Mono) → ITD Panner (binaural) |
| `ui_sound` | 3 | Sine → AD Envelope → Multiply (procedural click) |
| `weather` | 5 | Wave Player → InterpTo → Map Range → Biquad Filter L/R |

#### Wwise Static Knowledge (Phase 1)

| Data | Count | Used By |
|------|-------|---------|
| Object types | 19 | `wwise_create_object` validation |
| Properties | 24 | `wwise_set_property` documentation |
| References | 8 | `wwise_set_reference` documentation |
| Default paths | 9 | All template tools |
| Event actions | 18 | `wwise_create_event` validation |
| Curve types | 7 | `wwise_set_attenuation` validation |
| Curve shapes | 9 | RTPC + attenuation point validation |

---

## MetaSounds Tools (Phase 3 — Planned)

Requires UE5 5.4+ with custom C++ plugin running on TCP port 9877.

```
ms_create_source           New MetaSounds Source via Builder API
ms_create_patch            New MetaSounds Patch
ms_add_node                Add node by class name
ms_connect_nodes           Wire output → input
ms_set_default             Set input default value
ms_add_input               Expose parameter to Blueprint
ms_add_output              Expose output
ms_audition                Play the graph NOW
ms_live_update             Modify while playing (UE 5.5+)
ms_save_asset              Export to .uasset
```

## Blueprint Tools (Phase 3 — Planned)

```
bp_create_audio_manager    Generate audio manager Blueprint
bp_create_trigger          Surface detector, zone volume, animation notify
bp_wire_params             Connect game state → MetaSounds/Wwise params
bp_create_zone             Ambient zone with overlap + fade
```

## Systems Tools (Phase 4 — Planned)

The differentiator — orchestrates all three layers from a single prompt.

```
build_system               "weather ambient" → generates all layers
build_footsteps            Complete surface-reactive footstep system
build_weapon_audio         Gunshot + shell + tail + distance
build_ambient              Zone-based ambient with layers
build_ui_audio             Procedural UI sound set
build_weather              State-driven weather audio system
```

---

## Auto-Detection

The server detects what's available on startup:

| Running | Available Tools |
|---------|----------------|
| Nothing | Knowledge base, template preview, A2HW protocol |
| Wwise only | All Wwise tools (20 tools — Phase 1) |
| UE5 only | MetaSounds + Blueprint tools |
| Wwise + UE5 | Everything, including AudioLink bridge and full Systems tools |

No manual configuration. Install once, use what you have.

---

## Project Structure

```
pyproject.toml                              → Package config, pip install -e ".[dev]"
src/ue_audio_mcp/
├── server.py                               → FastMCP entry point + lifespan + tool wiring
├── connection.py                           → WwiseConnection singleton (WAAPI WebSocket)
├── tools/
│   ├── utils.py                            → Shared _ok/_error JSON helpers
│   ├── core.py                             → 5 tools: connect, info, query, save, execute
│   ├── objects.py                          → 4 tools: create, set property/reference, import
│   ├── events.py                           → 4 tools: events, RTPC, switch assign, attenuation
│   ├── preview.py                          → 2 tools: transport preview, soundbank generation
│   ├── templates.py                        → 5 tools: gunshot, footsteps, ambient, UI, weather
│   ├── metasounds.py                       → 4 tools: list/info/search/categories (TF-IDF cached)
│   └── ms_graph.py                         → 3 tools: validate, to_commands, from_template
├── knowledge/
│   ├── db.py                               → SQLite KnowledgeDB (8 tables, LIKE-escaped queries)
│   ├── seed.py                             → Seeds all tables from static catalogues
│   ├── embeddings.py                       → TF-IDF + cosine similarity, save/load .npz
│   ├── graph_schema.py                     → GraphSpec validator (7 stages) + Builder API commands
│   ├── wwise_types.py                      → 19 types, 24 props, 18 actions, 9 paths, curves
│   ├── waapi_functions.py                  → 87 WAAPI functions, 11 namespaces
│   ├── metasound_nodes.py                  → 112 nodes, 16 categories, full pin specs
│   ├── metasound_data_types.py             → Pin types, asset types, interfaces, compatibility
│   ├── blueprint_audio.py                  → 55 UE5 audio Blueprint functions
│   └── blueprint_nodes/                    → 946 UE5 Blueprint nodes (11 sub-modules)
│       ├── __init__.py                     → Registry + query helpers
│       ├── flow_control.py                 → 59 nodes (UK2Node_*, timers, comparison, conversion)
│       ├── math_core.py                    → 143 nodes (bool/byte/int/float/trig)
│       ├── math_spatial.py                 → 231 nodes (vector/rotator/quat/transform)
│       ├── math_utility.py                 → 114 nodes (interp/random/noise/color/datetime)
│       ├── string_array.py                 → 92 nodes (string ops, array ops)
│       ├── audio.py                        → 60 nodes (UE audio + Wwise integration)
│       ├── gameplay.py                     → 100 nodes (damage/player/actor/level/time)
│       ├── collision_physics.py            → 32 nodes (traces/overlaps)
│       ├── input_nodes.py                  → 15 nodes (Enhanced Input)
│       ├── rendering.py                    → 20 nodes (materials/meshes)
│       └── system.py                       → 80 nodes (debug/console/asset/platform)
├── templates/
│   ├── wwise/                              → 5 Wwise declarative pattern specs
│   └── metasounds/                         → 6 MetaSounds graph templates (JSON)
tests/                                      → 107 tests, all passing
├── conftest.py                             → MockWaapiClient + seeded KnowledgeDB fixtures
├── test_connection.py                      → 6 tests
├── test_core_tools.py                      → 8 tests
├── test_object_tools.py                    → 10 tests
├── test_event_tools.py                     → 8 tests
├── test_preview_tools.py                   → 7 tests
├── test_templates.py                       → 10 tests
├── test_db.py                              → 14 tests (LIKE escaping, seeding, embeddings)
├── test_graph_schema.py                    → 13 tests (validation, builder commands)
├── test_metasound_knowledge.py             → 11 tests (search caching, category+tag)
└── test_ms_graph_tools.py                  → 17 tests (6 parametrized templates, round-trip)
research/
├── research_waapi_mcp_server.md            → 69KB — 87 WAAPI functions, all patterns
├── research_metasounds_game_audio.md       → 11KB — 80+ nodes, Builder API
└── research_unreal_mcp_landscape.md        → 10 repos analysed, build-vs-fork decision
```

---

## Development Phases

```
Phase 1: Wwise MCP (standalone, WAAPI)     ✅ SHIPPED — 20 tools, 52 tests
Phase 2: MetaSounds + Blueprint Knowledge   ✅ SHIPPED — 7 tools, 1209 entries, 107 total tests
Phase 3: UE5 Audio Plugin (Builder API)     → needs Phase 2
Phase 4: Systems Layer (orchestration)      → needs Phase 1+3
Phase 5: A2HW Protocol Spec                → parallel
```

---

## Inspired by SIDKIT

This project applies the same philosophy as [SIDKIT](https://github.com/koshimazaki) — agent-generated audio systems from natural language — to game engines instead of hardware.

| SIDKIT | UE Audio MCP |
|--------|-------------|
| "make a Pacman sequencer" → generates C++ firmware | "make weather ambient" → generates patches + blueprints |
| Triple agent builds for Teensy ARM | Agent builds for UE5 + Wwise |
| Learns from compilation errors on Cloudflare D1 | Learns from build errors in UE5 |
| Hardware becomes different instrument via prompt | Game gets different audio system via prompt |
| 8 encoders, 30 buttons as performance controls | Blueprint params, RTPC as runtime controls |
| SysEx protocol | A2HW protocol |

**Same architecture. Same agent philosophy. Different target.**

---

## A2HW Protocol

The **Agent-to-Hardware** protocol is the shared language between SIDKIT and UE Audio MCP. A synthesis description in A2HW maps to multiple targets:

```
A2HW Description
    │
    ├──→ SIDKIT:      SysEx → Teensy ARM (hardware synth)
    ├──→ Browser:     JS → ModuleRunner (web preview)
    ├──→ MetaSounds:  Builder API → UE5 (game engine)
    └──→ Wwise:       WAAPI → mixing pipeline (middleware)
```

One prompt. Multiple render targets. The protocol is the standard — implementations vary per platform.

---

## Tech Stack

| Component | Technology | Status |
|-----------|-----------|--------|
| MCP Server | Python (FastMCP) | Shipped |
| Wwise Bridge | `waapi-client` (official Audiokinetic lib) | Shipped |
| UE5 Bridge | Custom C++ plugin + TCP (port 9877) | Planned |
| Knowledge (structured) | SQLite (8 tables, 1,209 entries) | Shipped — local-first, no latency |
| Knowledge (semantic) | TF-IDF + numpy cosine similarity | Shipped — <1ms queries, no ML deps |
| Templates | Parameterised JSON + Python generators | Shipped (5 Wwise + 6 MetaSounds patterns) |

**Requirements:** Python 3.10+, Wwise 2024/2025 with WAAPI enabled

---

## Prior Art

No MCP server exists for game audio. This is first-of-kind.

| Existing Tool | What It Does | Audio? |
|---------------|-------------|--------|
| [blender-mcp](https://github.com/ahujasid/blender-mcp) (16.9k stars) | Controls Blender via MCP | No |
| [unreal-mcp](https://github.com/chongdashu/unreal-mcp) | Controls UE5 editor via MCP | No |
| [RNBO MetaSound](https://github.com/Cycling74/RNBOMetasound) | Max/MSP → MetaSound nodes | Nodes only |
| [VibeComfy MCP](https://github.com/koshimazaki/VibeComfy) | 8,400+ ComfyUI nodes via MCP | No |
| **This project** | Complete game audio systems via MCP | **Yes — first** |

---

## Author

Built by [Koshi](https://github.com/koshimazaki) — creator of SIDKIT, VibeComfy MCP, and shipped audio products for Elektron, Waldorf, Qu-bit Electronix, and Industrial Music Electronics.

20 years designing audio workflows. From hardware synthesisers to game engines.

---

## Licence

TBD
