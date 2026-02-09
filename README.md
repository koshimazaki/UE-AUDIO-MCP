# UE Audio MCP

**AI-driven game audio pipelines -- from natural language to Wwise + MetaSounds + Blueprints.**

One MCP server. Three audio engines. 52 tools. 307 tests. Complete audio systems from a single prompt.

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
                                |
                                | MCP Protocol (stdio)
                                v
                    +---------------------------+
                    |      UE Audio MCP         |
                    |      52 tools             |
                    |      22K+ knowledge       |
                    +---------------------------+
                            |
              +-------------+-------------------+
              v             v                   v
     +----------------+ +------------+  +------------------+
     |  Wwise Tools   | | MetaSounds |  | Blueprint Tools  |
     |  (WAAPI)       | |  Tools     |  | (Remote Control) |
     |  20 tools      | | 22 tools   |  | 4 tools          |
     +-------+--------+ +-----+------+  +--------+---------+
             |               |                   |
             v               v                   v
     +----------------+ +------------+  +------------------+
     | Wwise App      | | UE5 C++    |  | UE5 Editor       |
     | WAAPI :8080    | | Plugin     |  | Remote Control   |
     +----------------+ | TCP:9877   |  +------------------+
                        +------------+
```

### The Three Layers

| Layer | Engine | Role | Analogy |
|-------|--------|------|---------|
| **Blueprint** | UE5 | WHEN -- detects game events, sets parameters | Stage manager |
| **MetaSounds** | UE5 | WHAT -- procedural DSP, synthesis | The instrument |
| **Wwise** | Standalone | HOW -- mixing, buses, spatialization, delivery | The mixing desk |

### Signal Flow

```
BLUEPRINT (WHEN)              METASOUNDS (WHAT)           WWISE (HOW)
----------------              -----------------           ------------
Player shoots           ->    Gunshot synthesis      ->   SFX bus, reverb
Player steps on grass   ->    Soft filtered step     ->   Distance attenuation
Weather changes to rain ->    Layered rain + drops   ->   Ambient bus, RTPC mix
Vehicle accelerates     ->    Engine layer blend     ->   Vehicle bus, compression
C64 chiptune plays      ->    ReSID SID Chip node    ->   Music bus, stereo mix
```

---

## What's Included

### 52 MCP Tools

| Category | Tools | What They Do |
|----------|-------|-------------|
| Wwise Core | 5 | Connect, query, save, raw WAAPI |
| Wwise Objects | 4 | Create objects (19 types), set properties, import audio |
| Wwise Events | 4 | Events, RTPC curves, switch assign, attenuation |
| Wwise Preview | 2 | Transport control, SoundBank generation |
| Wwise Templates | 6 | One-call gunshot/footsteps/ambient/UI/weather + AAA setup |
| MetaSounds Knowledge | 4 | Search 144 nodes, categories, semantic TF-IDF |
| MetaSounds Graphs | 3 | Validate, to Builder API commands, from template |
| MetaSounds Builder | 10 | Create source, add node, connect, set defaults, audition, presets |
| MetaSounds Advanced | 5 | Variables, preset swap/morph, macro trigger |
| Blueprint | 4 | Search 22K nodes, info, categories, call function |
| UE5 Connection | 3 | Connect, status, info |
| Orchestration | 2 | `build_audio_system` + `build_aaa_project` |

### 25 MetaSounds Templates

Full DSP graphs with nodes, connections, and defaults -- validated against the knowledge DB:

| Template | Nodes | Signal Chain |
|----------|-------|-------------|
| `gunshot` | 5 | Random Get -> Wave Player -> ADSR -> Multiply |
| `footsteps` | 6 | Trigger Route -> Random Get -> Wave Player -> AD Env -> LPF |
| `ambient` | 3 | Wave Player (Stereo) -> LFO -> Stereo Mixer |
| `wind` | 7 | Noise -> LPF (LFO + PawnSpeed modulated cutoff) -> Stereo |
| `weather` | 5 | Wave Player -> InterpTo -> Biquad Filter L/R |
| `vehicle_engine` | 14 | Trigger Sequence -> 3x Random Get -> Wave Player layers -> Compressor |
| `sfx_generator` | 25 | Oscillator -> Spectral (WaveShaper/BitCrush/RingMod) -> SVF -> ADSR -> Effects |
| `sid_chip_tune` | 2 | SID Chip (3-voice) -> Output Gain -- full C64 chiptune |
| `sid_bass` | 5 | SID Voice -> SID Filter (LP) with envelope-driven cutoff sweep |
| `sid_lead` | 8 | 2x SID Oscillator (saw+pulse detuned) -> SID Filter (BP, high res) |
| `preset_morph` | 8 | Morph param -> MapRange -> InterpTo -> Filter |
| `macro_sequence` | 10 | MacroStep triggers -> graph variables -> filter sweep |
| + 13 more | | subtractive_synth, mono_synth, snare, weapon_burst, sound_pad, etc. |

### 30 Blueprint Templates

Game logic patterns from Epic tutorials and community:

| Category | Templates |
|----------|-----------|
| Weapons | weapon_burst_control, weapon_source |
| Movement | footfalls_simple, player_oriented_sound |
| Ambient | ambient_height_wind, ambient_stingers, ambient_weighted_trigger, soundscape_ambient |
| Music/Quartz | quartz_beat_sync, quartz_multi_clock, quartz_music_playlist, quartz_vertical_music, triggered_music_stinger |
| Effects/Analysis | audio_modulation, spectral_analysis, submix_spectral_fireflies, physics_audio |
| UI/Control | sfx_generator_widget, metasound_preset_widget, audio_visualiser |
| Spatial | spatial_attenuation, volume_proxy |
| System | submix_recording, synesthesia_stems |

### 6 Wwise Templates

Pre-built WAAPI object hierarchies with undo support:

| Template | Creates |
|----------|---------|
| `gunshot` | RandomSequenceContainer + variations + pitch randomization |
| `footsteps` | SwitchContainer by surface + per-surface RandomSequence |
| `ambient` | BlendContainer + RTPC-driven layer volumes |
| `ui_sound` | Non-spatial sound + event + UI bus routing |
| `weather` | StateGroup + SwitchContainer + crossfade transitions |
| `vehicle_engine` | RPM layers + BlendContainer + RTPC |

### Knowledge Base

| Data | Entries | Source |
|------|---------|--------|
| MetaSounds nodes | 144 (798 pins, 21 categories) | Epic MetaSounds Reference + Editor screenshots |
| Blueprint API nodes (scraped) | 22,649 | Epic Blueprint API Reference (Playwright scraper) |
| Blueprint categories | 2,524 | Recursive BFS scrape of Epic SPA |
| Blueprint nodes (curated) | 946 | 11 hand-categorized sub-modules |
| WAAPI functions | 66 | Audiokinetic SDK reference |
| Blueprint audio | 55 | GameplayStatics, AudioComponent, Quartz |
| Wwise types | 19 | Types, properties, categories |
| Builder API functions | 68+ | UE 5.7 MetaSounds Builder API |
| Audio patterns | 6 | Game audio design patterns |
| UE4->UE5 conversion | 14 | Sound Cue -> MetaSounds migration map |

---

## ReSID SIDKIT Edition -- C64 SID Chip in MetaSounds

5 custom C++ MetaSounds nodes wrapping a cycle-accurate MOS 6581/8580 SID chip emulator. The same reSID core running in the [SIDKIT](https://github.com/koshimazaki/SIDKIT) project, now available as native MetaSounds DSP nodes.

### Nodes

| Node | Type | Description |
|------|------|-------------|
| **SID Oscillator** | Audio | 24-bit accumulator, 8 waveforms (saw/tri/pulse/noise + combined), actual chip sample tables |
| **SID Envelope** | Float | Non-linear exponential ADSR with authentic SID timing and the ADSR delay bug |
| **SID Filter** | Audio | Route ANY audio through the 6581's analog filter -- non-linear VCR model (VICE) |
| **SID Voice** | Audio | Oscillator x Envelope convenience combo |
| **SID Chip** | Audio | Complete 3-voice SID with filter, FM cross-modulation, per-voice outputs |

### SIDKIT Extensions (beyond stock reSID)

- **FM cross-modulation** -- any oscillator modulates any other (Cwejman S1 style)
- **Resonance boost** -- Q up to 8.0, self-oscillating filter at 1.0
- **Per-voice volume** -- 0-282 (256=unity, +10% headroom)
- **Direct modulation API** -- audio-rate freq/PW/cutoff control
- **VICE 2024 filter** -- 50MB lookup tables for the most accurate 6581 analog model

### Architecture

```
ue5_plugin/UEAudioMCP/
+-- Source/SIDMetaSoundNodes/     Runtime module (ships in games)
|   +-- Public/
|   |   +-- SIDNodeEnums.h        ESIDWaveform(8), ESIDFilterMode(7), ESIDChipModel(2)
|   +-- Private/Nodes/
|       +-- SIDOscillatorNode.cpp  TExecutableOperator wrapping WaveformGenerator
|       +-- SIDEnvelopeNode.cpp    TExecutableOperator wrapping EnvelopeGenerator
|       +-- SIDFilterNode.cpp      TExecutableOperator wrapping Filter (VICE model)
|       +-- SIDVoiceNode.cpp       TExecutableOperator wrapping Voice
|       +-- SIDChipNode.cpp        TExecutableOperator wrapping full SID16
+-- Source/ThirdParty/ReSID/       37 files, cycle-accurate C64 SID emulation
```

The SID nodes appear under the **"ReSID SIDKIT Edition"** category in the MetaSounds editor. `SIDMetaSoundNodes` is a separate Runtime module so the DSP nodes work in shipped games without the MCP TCP server.

---

## UE5 C++ Plugin

Editor-only plugin providing TCP server for MetaSounds Builder API access:

- **18 commands**: create_builder, add_node, connect, set_default, build_to_asset, audition, graph variables, preset conversion, live updates
- **Wire protocol**: 4-byte length-prefix + UTF-8 JSON on port 9877
- **Node registry**: 70 display-name -> class-name mappings (65 standard + 5 SID) + passthrough for `::` names
- **Thread safety**: FRunnable TCP -> AsyncTask(GameThread) dispatch
- **Blueprint reflection**: ProcessEvent with proper InitializeValue/DestroyValue lifecycle
- **Security**: localhost only (127.0.0.1), message size validation

---

## Orchestration

### 11 Audio System Patterns

`build_audio_system("pattern_name")` generates all 3 layers with cross-layer wiring:

```
gunshot, footsteps, ambient, spatial, ui_sound, weather,
vehicle_engine, sfx_generator, preset_morph, macro_sequence, sid_synth
```

Auto-detects connections: **Full** (Wwise+UE5), **Wwise-only**, or **Offline** dry-run.

### AAA Project Orchestrator

`build_aaa_project("MyGame")` generates a complete game audio infrastructure:

| Category | Pattern | Bus | Work Unit |
|----------|---------|-----|-----------|
| Player Footsteps | footsteps | SFX/Foley | Player |
| Player Weapons | gunshot | SFX/Weapons | Player |
| NPC Footsteps | footsteps | SFX/NPC | NPC |
| Ambient Wind | ambient | Ambient/Wind | Environment |
| Weather | weather | Ambient/Weather | Environment |
| UI | ui_sound | UI | UI |

Creates bus hierarchy, work units, events, MetaSounds sources, and Blueprint wiring for all 6 categories in a single call.

---

## Quick Start

```bash
git clone https://github.com/koshimazaki/UE5-WWISE.git
cd UE5-WWISE
pip install -e ".[dev]"

# Run MCP server
ue-audio-mcp

# Run tests (307 passing)
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

Works without Wwise or UE5 running -- knowledge base, templates, and offline mode always available.

### UE5 Plugin Installation

1. Copy `ue5_plugin/UEAudioMCP/` to your project's `Plugins/` folder
2. Enable **UEAudioMCP** in the plugin manager (Editor module, TCP server)
3. Enable **SIDMetaSoundNodes** (Runtime module, SID chip nodes)
4. Rebuild the project -- SID nodes appear under "ReSID SIDKIT Edition" category

---

## Project Stats

```
Python (src/)         12,250 lines   29 files
C++ Plugin            5,534 lines    33 files
ReSID ThirdParty      16,995 lines   37 files
Tests                 3,288 lines    18 files
Templates             61 files       (25 MetaSounds + 30 Blueprint + 6 Wwise)
                     --------
Total                 38,067 lines   117+ files
```

---

## A2HW Protocol

This project is the second implementation of the **Agent-to-Hardware (A2HW)** protocol -- a standard for AI-controlled audio across platforms.

```
                 +------------------------------+
                 |   A2HW Protocol               |
                 |   "describe sound, get sound" |
                 +--------------+---------------+
                                |
          +---------+-----------+----------+----------+
          v         v           v          v          v
     +---------+ +-------+ +--------+ +-------+ +-------+
     | Teensy  | | Wwise | |  UE5   | | iPad  | |  DAW  |
     | SysEx   | | WAAPI | |Builder | | AUv3  | |  OSC  |
     | +Flash  | |       | |  API   | |       | | +MIDI |
     +---------+ +-------+ +--------+ +-------+ +-------+
      SIDKIT      <-- This project -->   Future targets
```

| | SIDKIT (A2HW v1) | UE Audio MCP (A2HW v2) |
|---|---|---|
| Target | C64 SID chip on Teensy ARM | Wwise + MetaSounds + Blueprint |
| Renderers | 1 (SysEx -> hardware) | 3 (WAAPI + Builder API + Remote Control) |
| Complexity | Linear: compile -> flash -> play | Graph: 3 tools must agree on naming |
| Agent | Rust, 8 tools, error learning | Python, 52 tools, knowledge DB |
| Protocol | SysEx JSON commands | Same pattern, 3 transports |

Same philosophy: **describe intent, system figures out the wiring.**

---

## Development Status

```
Phase 1: Wwise MCP Server       Done   20 tools, WAAPI bridge
Phase 2: Knowledge Base          Done   144 nodes (798 pins), 22K+ scraped, semantic search
Phase 3: UE5 Plugin + Tools      Done   C++ plugin, 22 tools, TCP protocol
Phase 4: Orchestration           Done   11 patterns, AAA project, 3-mode auto-detection
Phase 5: ReSID SIDKIT Edition    Done   5 custom C++ MetaSounds nodes, 3 templates
Phase 6: A2HW Protocol Spec     WIP    Defined in SIDKIT, extended here
```

**307 tests passing** across 18 test modules.

---

## Prior Art

This work fills a gap in the existing MCP ecosystem.

| Existing Tool | Audio? |
|---|---|
| [blender-mcp](https://github.com/ahujasid/blender-mcp) (16.9k stars) -- Controls Blender | No |
| [unreal-mcp](https://github.com/chongdashu/unreal-mcp) (1,370 stars) -- Controls UE5 editor | No |
| [VibeComfy MCP](https://github.com/koshimazaki/VibeComfy) -- 8,400+ ComfyUI nodes | No |
| [BilkentAudio/Wwise-MCP](https://github.com/BilkentAudio/wwise-mcp) -- Wwise wrapper | Partial |
| **This project** -- Complete 3-layer game audio + SID chip emulation | **Yes** |

---

## Credits

All templates and knowledge curated from public sources: Epic Games documentation, and tutorials, Audiokinetic SDK reference, and community tutorials. ReSID emulation based on [reSID](http://www.zimmers.net/anonftp/pub/cbm/crossplatform/emulators/resid/) by Dag Lem with SIDKIT extensions.

See [CREDITS.md](CREDITS.md) for full attribution to tutorial authors and data sources.

Key sources: [Craig Owen](https://www.youtube.com/watch?v=n5z4L43jMi8) (YAGER), [Matt Spendlove](https://dev.epicgames.com/community/learning/recommended-community-tutorial/Kw7l), [Nick Pfisterer](https://dev.epicgames.com/community/learning/recommended-community-tutorial/WzJ), [Eric Buchholz](https://dev.epicgames.com/community/learning/tutorials/qEjr) (TechAudioTools), [Chris Payne](https://dev.epicgames.com/community/learning/tutorials/opvv), Epic Games official documentation.

---

## Author

Built by [Koshi Mazaki](https://github.com/koshimazaki)

---

## Licence

MIT
