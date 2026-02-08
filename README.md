# UE Audio MCP

**AI-driven game audio pipelines — from natural language to Wwise + MetaSounds + Blueprints.**

One MCP server. Three audio engines. 50 tools. 22,649 Blueprint API nodes. Complete audio systems from a single prompt.

> "Build weather-responsive ambient with rain, wind, and clear states that crossfade based on intensity"
>
> MetaSounds DSP graph generated. Wwise bus hierarchy + RTPC curves created. Blueprint trigger logic wired. AudioLink bridged. You hear rain starting.

---

## Why This Exists

Game audio systems take weeks to build manually. A weather ambient system needs:
- MetaSounds patches for rain, wind, clear (procedural DSP)
- Blueprint logic reading weather state, setting parameters
- Wwise bus hierarchy, RTPC curves, state groups, spatial mixing
- AudioLink routing procedural audio into the mix pipeline
- Everything wired together with consistent naming

Each layer is a different tool, different specialist, different iteration cycle. This MCP server automates the plumbing so sound designers focus on the sound.

---

## Architecture

```
                    Claude / Cursor / Any MCP Client
                                │
                                │ MCP Protocol (stdio)
                                ▼
                    ┌───────────────────────┐
                    │    UE Audio MCP       │
                    │    50 tools           │
                    │    22K+ knowledge     │
                    └───────┬───────────────┘
                            │
              ┌─────────────┼─────────────────┐
              ▼             ▼                 ▼
     ┌──────────────┐ ┌──────────┐  ┌──────────────────┐
     │  Wwise Tools │ │MetaSounds│  │ Blueprint Tools  │
     │  (WAAPI)     │ │ Tools    │  │ (Remote Control) │
     │  20 tools    │ │ 18 tools │  │ 4 tools          │
     └──────┬───────┘ └────┬─────┘  └────────┬─────────┘
            │              │                 │
            ▼              ▼                 ▼
     ┌──────────────┐ ┌──────────┐  ┌──────────────────┐
     │ Wwise App    │ │ UE5 C++  │  │ UE5 Editor       │
     │ WAAPI :8080  │ │ Plugin   │  │ Remote Control   │
     └──────────────┘ │ TCP:9877 │  └──────────────────┘
                      └──────────┘
```

### The Three Layers

| Layer | Engine | Role | Analogy |
|-------|--------|------|---------|
| **Blueprint** | UE5 | WHEN — detects game events, sets parameters | Stage manager |
| **MetaSounds** | UE5 | WHAT — procedural DSP, synthesis | The instrument |
| **Wwise** | Standalone | HOW — mixing, buses, spatialization, delivery | The mixing desk |

### Signal Flow

```
BLUEPRINT (WHEN)              METASOUNDS (WHAT)           WWISE (HOW)
────────────────              ─────────────────           ──────────────
Player shoots           →    Gunshot synthesis      →    SFX bus, reverb
Player steps on grass   →    Soft filtered step     →    Distance attenuation
Weather changes to rain →    Layered rain + drops   →    Ambient bus, RTPC mix
Vehicle accelerates     →    Engine layer blend     →    Vehicle bus, compression
```

---

## What's Included

### 50 MCP Tools

| Category | Tools | What They Do |
|----------|-------|-------------|
| Wwise Core | 5 | Connect, query, save, raw WAAPI |
| Wwise Objects | 4 | Create objects (19 types), set properties, import audio |
| Wwise Events | 4 | Events, RTPC curves, switch assign, attenuation |
| Wwise Preview | 2 | Transport control, SoundBank generation |
| Wwise Templates | 5 | One-call gunshot/footsteps/ambient/UI/weather |
| MetaSounds Knowledge | 4 | Search 144 nodes, categories, semantic TF-IDF |
| MetaSounds Graphs | 3 | Validate, to Builder API commands, from template |
| MetaSounds Builder | 7 | Create source, add node, connect, set defaults, audition |
| MetaSounds Advanced | 4 | Variables, presets, macros |
| Blueprint | 4 | Search 22K nodes, info, categories, call function |
| UE5 Connection | 3 | Connect, status, info |
| Orchestration | 1 | `build_audio_system` — all 3 layers from one pattern |

### 22 MetaSounds Templates

Full DSP graphs with nodes, connections, and defaults — validated against the knowledge DB:

| Template | Nodes | Signal Chain |
|----------|-------|-------------|
| `gunshot` | 5 | Random Get → Wave Player → ADSR → Multiply |
| `footsteps` | 6 | Trigger Route → Random Get → Wave Player → AD Env → LPF |
| `ambient` | 3 | Wave Player (Stereo) → LFO → Stereo Mixer |
| `wind` | 7 | Noise → LPF (LFO + PawnSpeed modulated cutoff) → Stereo |
| `weather` | 5 | Wave Player → InterpTo → Biquad Filter L/R |
| `vehicle_engine` | 14 | Trigger Sequence → 3x Random Get → Wave Player layers → Compressor |
| `sfx_generator` | 25 | Oscillator → Spectral (WaveShaper/BitCrush/RingMod) → SVF → ADSR → Effects |
| `preset_morph` | 8 | Morph param → MapRange → InterpTo → Filter |
| `macro_sequence` | 10 | MacroStep triggers → graph variables → filter sweep |
| + 13 more | | subtractive_synth, mono_synth, snare, sound_pad, weapon_burst, etc. |

### 30 Blueprint Templates

Game logic patterns from Epic tutorials and community:

| Category | Templates |
|----------|-----------|
| Weapons | weapon_burst_control, weapon_source |
| Movement | footfalls_simple, player_oriented_sound |
| Ambient | ambient_height_wind, ambient_stingers, ambient_weighted_trigger, soundscape_ambient |
| Music | quartz_beat_sync, quartz_multi_clock, quartz_music_playlist, quartz_vertical_music, triggered_music_stinger |
| Effects | audio_modulation, spectral_analysis, submix_spectral_fireflies, physics_audio |
| UI | sfx_generator_widget, metasound_preset_widget, audio_visualiser |
| Spatial | spatial_attenuation, volume_proxy |
| System | submix_recording, synesthesia_stems |

### Knowledge Base

| Data | Entries | Source |
|------|---------|--------|
| MetaSounds nodes | 144 (798 pins) | Epic MetaSounds Reference (Playwright scraper) + Editor + screenshots |
| Blueprint API nodes (scraped) | 22,649 | Epic Blueprint API Reference (Playwright scraper) |
| Blueprint categories | 2,524 | Recursive BFS scrape of Epic SPA |
| Blueprint nodes (curated) | 946 | 11 hand-categorized sub-modules |
| WAAPI functions | 66 | Audiokinetic SDK reference |
| Blueprint audio | 55 | GameplayStatics, AudioComponent, Quartz |
| Wwise types | 19 | Types, properties, categories |
| Audio patterns | 6 | Game audio design patterns |
| UE4→UE5 conversion | 14 | Sound Cue → MetaSounds migration map |

### UE5 C++ Plugin

Editor-only plugin providing TCP server for MetaSounds Builder API access:

- **18 commands**: create_builder, add_node, connect, set_default, build_to_asset, audition, graph variables, preset conversion, live updates
- **Wire protocol**: 4-byte length-prefix + UTF-8 JSON on port 9877
- **Node registry**: 65 display-name → class-name mappings + passthrough for `::` names
- **Thread safety**: FRunnable TCP → AsyncTask(GameThread) dispatch

### 10 Orchestration Patterns

`build_audio_system("pattern_name")` generates all 3 layers with cross-layer wiring:

```
gunshot, footsteps, ambient, spatial, ui_sound, weather,
vehicle_engine, sfx_generator, preset_morph, macro_sequence
```

Auto-detects connections: Full (Wwise+UE5), Wwise-only, or Offline dry-run.

---

## Quick Start

```bash
git clone https://github.com/koshimazaki/UE5-WWISE.git
cd UE5-WWISE
pip install -e ".[dev]"

# Run MCP server
ue-audio-mcp

# Run tests (262 passing)
pytest tests/ -v
```

### MCP Client Config

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

Works without Wwise or UE5 running — knowledge base, templates, and offline mode always available.

---

## A2HW Protocol

This project is the second implementation of the **Agent-to-Hardware (A2HW)** protocol — a standard for AI-controlled audio across platforms.

```
                 ┌──────────────────────────────┐
                 │   A2HW Protocol               │
                 │   "describe sound, get sound" │
                 └──────────────┬───────────────┘
                                │
          ┌─────────┬───────────┼──────────┬──────────┐
          ▼         ▼           ▼          ▼          ▼
     ┌─────────┐ ┌───────┐ ┌────────┐ ┌───────┐ ┌───────┐
     │ Teensy  │ │ Wwise │ │  UE5   │ │ iPad  │ │  DAW  │
     │ SysEx   │ │ WAAPI │ │Builder │ │ AUv3  │ │  OSC  │
     │ +Flash  │ │       │ │  API   │ │       │ │ +MIDI │
     └─────────┘ └───────┘ └────────┘ └───────┘ └───────┘
      SIDKIT      ◄── This project ──►   Future targets
```

| | SIDKIT (A2HW v1) | UE Audio MCP (A2HW v2) |
|---|---|---|
| Target | C64 SID chip on Teensy ARM | Wwise + MetaSounds + Blueprint |
| Renderers | 1 (SysEx → hardware) | 3 (WAAPI + Builder API + Remote Control) |
| Complexity | Linear: compile → flash → play | Graph: 3 tools must agree on naming |
| Agent | Rust, 8 tools, error learning | Python, 50 tools, knowledge DB |
| Protocol | SysEx JSON commands | Same pattern, 3 transports |

Same philosophy: **describe intent, system figures out the wiring.**

---

## Development Status

```
Phase 1: Wwise MCP Server       ✅ 20 tools, WAAPI bridge
Phase 2: Knowledge Base          ✅ 144 nodes (798 pins), 22K+ scraped, semantic search
Phase 3: UE5 Plugin + Tools      ✅ C++ plugin, 14 tools, TCP protocol
Phase 4: Orchestration            ✅ 10 patterns, 3-mode auto-detection
Phase 5: A2HW Protocol Spec     ◐ Defined in SIDKIT, extended here
```

**262 tests passing** across 11 test modules.

---

## Prior Art

No MCP server for game audio exists. This is first-of-kind.

| Existing Tool | Audio? |
|---|---|
| [blender-mcp](https://github.com/ahujasid/blender-mcp) (16.9k stars) — Controls Blender | No |
| [unreal-mcp](https://github.com/chongdashu/unreal-mcp) (1,370 stars) — Controls UE5 editor | No |
| [VibeComfy MCP](https://github.com/koshimazaki/VibeComfy) — 8,400+ ComfyUI nodes | No |
| [BilkentAudio/Wwise-MCP](https://github.com/BilkentAudio/wwise-mcp) — Basic Wwise wrapper | Partial |
| **This project** — Complete 3-layer game audio | **Yes** |

---

## Credits

All templates and knowledge curated from public sources: Epic Games documentation, Audiokinetic SDK reference, and community tutorials. This project is a curation and automation layer — the audio knowledge belongs to the community.

See [CREDITS.md](CREDITS.md) for full attribution to tutorial authors and data sources.

Key sources: [Craig Owen](https://www.youtube.com/watch?v=n5z4L43jMi8) (YAGER), [Matt Spendlove](https://dev.epicgames.com/community/learning/recommended-community-tutorial/Kw7l), [Nick Pfisterer](https://dev.epicgames.com/community/learning/recommended-community-tutorial/WzJ), [Eric Buchholz](https://dev.epicgames.com/community/learning/tutorials/qEjr) (TechAudioTools), [Chris Payne](https://dev.epicgames.com/community/learning/tutorials/opvv), Epic Games official documentation.

---

## Author

Built by [Koshi](https://github.com/koshimazaki)

---

## Licence

MIT
