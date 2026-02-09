# UE Audio MCP

**AI-driven game audio pipelines -- from natural language to Wwise + MetaSounds + Blueprints.**

One MCP server. Three audio engines. 52 tools. Complete audio systems from a single prompt.

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
                    |      26K+ knowledge       |
                    +---------------------------+
                            |
              +-------------+-------------------+
              v             v                   v
     +----------------+ +------------+  +------------------+
     |  Wwise Tools   | | MetaSounds |  | Blueprint Tools  |
     |  (WAAPI)       | |  Tools     |  | (TCP + WAAPI)    |
     |  21 tools      | | 22 tools   |  | 6 tools          |
     +-------+--------+ +-----+------+  +--------+---------+
             |               |                   |
             v               v                   v
     +----------------+ +---------------------------+
     | Wwise App      | | UE5 C++ Plugin            |
     | WAAPI :8080    | | TCP:9877 (24 commands)     |
     +----------------+ | MetaSounds Builder API     |
                        | Blueprint Graph Scanner    |
                        | Editor Menu Integration    |
                        +---------------------------+
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
| Blueprint | 6 | Search 22K+ nodes, scan graphs, list assets, call function |
| UE5 Connection | 3 | Connect, status, info |
| Orchestration | 2 | `build_audio_system` + `build_aaa_project` |

### Knowledge Base -- 26K+ Entries

Structured data + semantic search (TF-IDF + cosine similarity) across the full UE5 audio API surface:

| Data | Entries | Source |
|------|---------|--------|
| **Blueprint API nodes** | **22,649** | Epic Blueprint API Reference (Playwright scraper, UE 5.7) |
| **Blueprint categories** | **2,524** | Recursive BFS scrape of Epic SPA |
| Blueprint nodes (curated) | 946 | 11 hand-categorized audio sub-modules |
| MetaSounds nodes | 144 (798 pins, 21 categories) | Epic MetaSounds Reference + Editor screenshots |
| Builder API functions | 68+ | UE 5.7 MetaSounds Builder API |
| WAAPI functions | 66 | Audiokinetic SDK reference |
| Blueprint audio functions | 55 | GameplayStatics, AudioComponent, Quartz |
| Wwise types & properties | 19 | Types, categories, default paths |
| Audio patterns | 6 | Game audio design patterns |
| UE4->UE5 conversion | 14 | Sound Cue -> MetaSounds migration map |
| **Project Blueprints** | **growing** | Scanned from Lyra, Stack-O-Bot, and user projects |

The 22K+ Blueprint leaf nodes include full pin specs (inputs, outputs, types, descriptions) scraped directly from Epic's documentation SPA. The batch scanner (`scripts/scan_project.py`) imports scanned project Blueprints into the knowledge DB and rebuilds the TF-IDF index for semantic search across all sources.

### 61 Templates

| Type | Count | Examples |
|------|-------|---------|
| MetaSounds DSP | 25 | gunshot, footsteps, ambient, wind, weather, vehicle_engine, sfx_generator, sid_chip_tune, sid_bass, sid_lead, preset_morph, macro_sequence, subtractive_synth, mono_synth, snare... |
| Blueprint Logic | 30 | weapon_burst, footfalls, ambient_wind, quartz_beat_sync, spectral_analysis, sfx_generator_widget, spatial_attenuation, submix_recording, physics_audio... |
| Wwise Hierarchy | 6 | gunshot, footsteps, ambient, ui_sound, weather, vehicle_engine |

All MetaSounds templates are validated against the knowledge DB with pin-level accuracy.

---

## Blueprint Scanner + Editor Menu

Deep-inspect UE5 Blueprint graphs from the editor or batch-scan entire projects.

### C++ Graph Scanner

Scans 7 K2Node types that Python can't access: **CallFunction**, **Event**, **CustomEvent**, **VariableGet/Set**, **MacroInstance**, **DynamicCast**. Each node is checked against 21 audio keywords (Sound, Audio, Ak, Wwise, MetaSound, RTPC, PostEvent, etc.) for automatic audio relevance tagging.

### Editor Menu

"Audio MCP" appears in the UE5 main menu bar:

| Action | What It Does |
|--------|-------------|
| **Scan Project Audio** | Scans all Blueprints under /Game/ with progress bar, saves JSON |
| **Scan Selected Blueprint** | Deep-scan with full pin details for selected Content Browser asset |
| **Export Node Positions** | Exports MetaSound node pixel positions (all Sources + Patches) |
| **Open Results Folder** | Opens Saved/AudioMCP/ in file browser |
| **Server Status** | Shows TCP server port and command count |

### Batch Scanner

```bash
python scripts/scan_project.py --audio-only --import-db --rebuild-embeddings
```

Connects to the UE5 plugin, discovers all Blueprint assets via Asset Registry, scans each for audio-relevant nodes, imports results into the knowledge DB, and rebuilds the TF-IDF semantic search index.

### Asset Registry Queries

`list_assets` queries 12 asset classes: Blueprint, WidgetBlueprint, AnimBlueprint, MetaSoundSource, MetaSoundPatch, SoundWave, SoundCue, SoundAttenuation, SoundClass, SoundConcurrency, SoundMix, ReverbEffect.

---

## ReSID SIDKIT Edition -- C64 SID Chip in MetaSounds

5 custom C++ MetaSounds nodes wrapping a cycle-accurate MOS 6581/8580 SID chip emulator. The same reSID core running in the [SIDKIT](https://github.com/koshimazaki/SIDKIT) project, now available as native MetaSounds DSP nodes.

| Node | Type | Description |
|------|------|-------------|
| **SID Oscillator** | Audio | 24-bit accumulator, 8 waveforms (saw/tri/pulse/noise + combined) |
| **SID Envelope** | Float | Non-linear exponential ADSR with authentic SID timing and delay bug |
| **SID Filter** | Audio | Route any audio through the 6581's analog filter -- VICE VCR model |
| **SID Voice** | Audio | Oscillator x Envelope convenience combo |
| **SID Chip** | Audio | Complete 3-voice SID with filter, FM cross-modulation, per-voice outputs |

SIDKIT extensions beyond stock reSID: FM cross-modulation (Cwejman S1 style), resonance boost up to Q=8.0, per-voice volume, audio-rate freq/PW/cutoff control, VICE 2024 filter model.

`SIDMetaSoundNodes` is a separate Runtime module -- ships in games without the MCP TCP server.

---

## UE5 C++ Plugin

Editor-only plugin providing TCP server for MetaSounds Builder API and Blueprint graph access:

- **24 commands**: builder lifecycle, node ops, graph I/O, variables, presets, audition, blueprint scanning, asset queries, live updates
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

# Run tests
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
Python (src/)         12,300 lines   43 files
C++ Plugin             6,200 lines   36 files
ReSID ThirdParty      17,300 lines   37 files
Scripts                4,000 lines   10 files
Templates             61 files       (25 MetaSounds + 30 Blueprint + 6 Wwise)
Tests                  3,400 lines   20 files
                     --------
Total                 43,200 lines   207 files
```

---

## Development Status

```
Phase 1: Wwise MCP Server        Done    20 tools, WAAPI bridge
Phase 2: Knowledge Base           Done    26K+ entries, semantic search, 144 MS nodes
Phase 3: UE5 Plugin + Tools       Done    C++ plugin (24 cmds), 22 tools, TCP protocol
Phase 4: Orchestration            Done    11 patterns, AAA project, 3-mode auto-detection
Phase 5: ReSID SIDKIT Edition     Done    5 custom C++ MetaSounds nodes, 3 templates
Phase 6: Blueprint Scanner        Done    Graph inspection, editor menu, batch scanner
Phase 7: A2HW Protocol Spec      WIP     Defined in SIDKIT, extended here
```

### Coming Next

- **Game project knowledge** -- Scanning Lyra, Stack-O-Bot, and community projects to grow the Blueprint pattern library with real-world audio implementations
- **Error learning** -- SIDKIT-pattern error_signature -> fix mapping (build fails get remembered)
- **Cloudflare D1 + Vectorize** -- Cloud-hosted knowledge base for team sharing
- **AudioLink integration** -- Automated MetaSounds -> Wwise routing via AudioLink bridge
- **More AAA categories** -- Dialogue, music, cinematics, vehicles expanded
- **Live parameter dashboard** -- Real-time RTPC/MetaSounds parameter monitoring
- **A2HW Protocol** -- Formalising the Agent-to-Hardware protocol for AI-controlled audio across platforms (game engines, DAWs, hardware)

---

## Prior Art

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
