# UE Audio MCP

**Build complete game audio systems from natural language.**

One MCP server. Three audio engines. Wwise + MetaSounds + Blueprint — wired together, running in your game.

> "Build weather-responsive ambient with rain, wind, and clear states that crossfade based on intensity"
>
> → 3 MetaSounds patches generated → Blueprint trigger logic wired → Wwise bus hierarchy + RTPC curves created → AudioLink bridged → Running in game. You hear rain starting.

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
                    │    UE Audio MCP        │
                    │    (one server)        │
                    └───────┬───────────────┘
                            │
              ┌─────────────┼─────────────────┐
              v             v                  v
     ┌──────────────┐ ┌──────────┐  ┌──────────────────┐
     │  Wwise Tools │ │ MetaSound│  │ Blueprint Tools   │
     │  (WAAPI)     │ │ Tools    │  │ (Remote Control)  │
     └──────┬───────┘ └────┬─────┘  └────────┬─────────┘
            │              │                  │
            v              v                  v
     ┌──────────────┐ ┌──────────┐  ┌──────────────────┐
     │ Wwise App    │ │ UE5      │  │ UE5 Editor       │
     │ (WAAPI :8080)│ │ Plugin   │  │ (Remote Control)  │
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

## Tool Groups

### Wwise Tools (works standalone — just Wwise running)
```
wwise_connect              Connect to running Wwise instance
wwise_get_info             Project info, version
wwise_create_object        Create any Wwise object type
wwise_import_audio         Import WAV files
wwise_set_property         Set volume, pitch, filters
wwise_set_reference        Assign buses, attenuation
wwise_create_event         Create events with actions
wwise_query                WAQL queries
wwise_set_rtpc             Create/modify RTPC curves
wwise_assign_switch        Switch container assignments
wwise_set_attenuation      Attenuation curves
wwise_generate_banks       Build soundbanks
wwise_preview              Play/stop via transport
wwise_save                 Save project
execute_waapi              Generic escape hatch — any WAAPI call
```

### MetaSounds Tools (works with UE5 running)
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
ms_list_nodes              Browse available node types
```

### Blueprint Tools (works with UE5 running)
```
bp_create_audio_manager    Generate audio manager Blueprint
bp_create_trigger          Surface detector, zone volume, animation notify
bp_wire_params             Connect game state → MetaSounds/Wwise params
bp_create_zone             Ambient zone with overlap + fade
```

### Systems Tools (the differentiator — orchestrates all three)
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
| Wwise only | All Wwise tools |
| UE5 only | MetaSounds + Blueprint tools |
| Wwise + UE5 | Everything, including AudioLink bridge and full Systems tools |

No manual configuration. Install once, use what you have.

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

- **MCP Server:** Python (FastMCP)
- **Wwise Bridge:** `waapi-client` (official Audiokinetic Python library)
- **UE5 Bridge:** Custom C++ plugin with TCP server (Builder API + Remote Control)
- **Knowledge Base:** Node databases for MetaSounds (80+ nodes) and Wwise object types
- **Templates:** Parameterised patterns for common game audio systems

---

## Status

**Early development.** Building in public.

- [ ] Wwise MCP — standalone tools via WAAPI
- [ ] MetaSounds knowledge base — node database + graph spec templates
- [ ] UE5 audio plugin — Builder API bridge
- [ ] Blueprint tools — trigger logic generation
- [ ] Systems layer — multi-layer orchestration
- [ ] A2HW protocol spec — published standard
- [ ] AudioLink bridge — MetaSounds → Wwise routing

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
