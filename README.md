```
██╗   ██╗███████╗     █████╗ ██╗   ██╗██████╗ ██╗ ██████╗     ███╗   ███╗ ██████╗██████╗
██║   ██║██╔════╝    ██╔══██╗██║   ██║██╔══██╗██║██╔═══██╗    ████╗ ████║██╔════╝██╔══██╗
██║   ██║█████╗      ███████║██║   ██║██║  ██║██║██║   ██║    ██╔████╔██║██║     ██████╔╝
██║   ██║██╔══╝      ██╔══██║██║   ██║██║  ██║██║██║   ██║    ██║╚██╔╝██║██║     ██╔═══╝
╚██████╔╝███████╗    ██║  ██║╚██████╔╝██████╔╝██║╚██████╔╝    ██║ ╚═╝ ██║╚██████╗██║
 ╚═════╝ ╚══════╝    ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝ ╚═════╝     ╚═╝     ╚═╝ ╚═════╝╚═╝
░░░░░░░░░░░░░░░░░░ AI Game Audio — Wwise + MetaSounds + Blueprints ░░░░░░░░░░░░░░░░░░░
```

# UE Audio MCP

**AI-driven game audio pipelines -- from natural language to Wwise + MetaSounds + Blueprints.**

One MCP server. Three audio engines. 63 tools. 178 engine-verified MetaSounds nodes. Optimised for **Unreal Engine 5.7** and **Wwise 2024**.

> "Create a footsteps sound setup for my character -- use MetaSounds noise and filter in the patch, Blueprint trigger on anim notify"
>
> MCP generates the MetaSounds DSP graph (noise -> filter -> AD envelope) and outputs Blueprint wiring for the animation trigger.

### Install

```bash
git clone https://github.com/koshimazaki/UE-AUDIO-MCP.git
cd UE-AUDIO-MCP
pip install -e ".[dev]"

# Run MCP server
ue-audio-mcp
```

Works without Wwise or UE5 running -- knowledge base, templates, and offline mode always available.

---

## Architecture

```
                    Claude / Cursor / Any MCP Client
                                |
                                | MCP Protocol (stdio)
                                v
                    +---------------------------+
                    |      UE Audio MCP         |
                    |      63 tools             |
                    |      643 knowledge entries|
                    +---------------------------+
                            |
              +-------------+-------------------+
              v             v                   v
     +----------------+ +------------+  +------------------+
     |  Wwise Tools   | | MetaSounds |  | Blueprint Tools  |
     |  (WAAPI)       | |  Tools     |  | (TCP + Knowledge)|
     |  20 tools      | | 18 tools   |  | 14 tools         |
     +-------+--------+ +-----+------+  +--------+---------+
             |               |                   |
             v               v                   v
     +----------------+ +---------------------------+
     | Wwise App      | | UE5 C++ Plugin             |
     | WAAPI :8080    | | TCP:9877 (35 commands)     |
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

### 63 MCP Tools

| Category | Tools | What They Do |
|----------|-------|-------------|
| Wwise Core | 5 | Connect, query, save, raw WAAPI |
| Wwise Objects | 4 | Create objects (19 types), set properties, import audio |
| Wwise Events | 4 | Events, RTPC curves, switch assign, attenuation |
| Wwise Preview | 2 | Transport control, SoundBank generation |
| Wwise Templates | 5 | One-call gunshot/footsteps/ambient/UI/weather + AAA setup |
| MetaSounds Knowledge | 4 | Search 178 nodes, categories, TF-IDF semantic search |
| MetaSounds Graphs | 3 | Validate, to Builder API commands, from template |
| MetaSounds Builder | 10 | Create source, add node, connect, set defaults, audition, presets |
| MetaSounds Advanced | 5 | Variables, preset swap/morph, macro trigger |
| MetaSounds Sync | 1 | Sync engine node registry to knowledge DB |
| Blueprint Knowledge | 6 | Search nodes, scan graphs, list assets, call function |
| Blueprint Builder | 8 | Add nodes, connect pins, compile, set defaults, wire audio params |
| Blueprint Sync | 1 | Sync engine function registry to knowledge DB |
| UE5 Connection | 3 | Connect, status, info |
| Orchestration | 2 | `build_audio_system` + `build_aaa_project` |

### Knowledge Base -- 643 Verified Entries

All data engine-verified or hand-curated. TF-IDF semantic search for MetaSounds nodes, WAAPI, and patterns. SQL keyword matching for Blueprint functions.

| Data | Entries | Source |
|------|---------|--------|
| MetaSounds nodes | **178** (23 categories, 128 class_name mappings) | Engine registry sync + Epic docs |
| Cross-system pin mappings | 130 | BP ↔ MetaSounds ↔ Wwise wiring table |
| Builder API functions | 81 | UE 5.7 MetaSounds Builder API |
| WAAPI functions | 66 | Audiokinetic SDK reference |
| Blueprint audio functions | 55 | GameplayStatics, AudioComponent, Quartz |
| Blueprint nodes (curated) | 55 | Engine-synced audio functions catalogue |
| Audio console commands | 20 | UE5 audio debugging commands |
| Wwise types & properties | 19 | Types, categories, default paths |
| Tutorial workflows | 17 | Step-by-step MetaSounds build guides |
| Attenuation subsystems | 8 | Distance models and parameters |
| Audio patterns | 6 | Game audio design patterns (gunshot, footsteps, ambient, etc.) |
| UE game examples | 5 | Lyra reference implementations |
| Spatialization methods | 3 | HRTF, ITD, panning |

Engine sync scripts fetch live data from the running UE5 editor (842 MetaSounds nodes, 979 audio Blueprint functions from 165 classes). The batch scanner (`scripts/scan_project.py`) imports scanned project Blueprints into the knowledge DB.

### 73 Templates (33/33 MS validated)

| Type | Count | Highlights |
|------|-------|-----------|
| MetaSounds DSP | 33 | 26 Sources + 7 Patches. Includes 12 from shipped games (Lyra, StackOBot) |
| Blueprint Logic | 34 | Combat, Quartz music, physics, ambient, UI, animation-driven audio |
| Wwise Hierarchy | 6 | gunshot, footsteps, ambient, ui_sound, weather, vehicle_engine |

All 33 MetaSounds templates pass 7-stage validation against the engine-verified catalogue. 12 templates derived from production games: **Lyra** (random_eq, whizby, stereo_high_shelf, stereo_balance, ambient_element, gameplay_cue_audio, weapon_fire_spatial, ui_button_sound, anim_notify_audio) and **StackOBot** (mono_array_player, looped_sound, stereo_eq_delay).

See **[TEMPLATES.md](TEMPLATES.md)** for the full catalogue with C++ audio patterns from Lyra (Context Effects pipeline, Control Bus mixing).

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
| **Export MetaSounds** | Full graph export with types, defaults, variables, interfaces (all Sources + Patches) |
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

- **35 commands**: builder lifecycle, node ops, graph I/O, variables, presets, audition, blueprint scanning/building, asset queries, engine registry sync, live updates
- **Wire protocol**: 4-byte length-prefix + UTF-8 JSON on port 9877
- **Node registry**: 70 display-name -> class-name mappings (65 standard + 5 SID) + passthrough for `::` names
- **Blueprint builder**: `FAudioMCPBlueprintManager` -- add nodes, connect pins, compile, audio function allowlist
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

## Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Unreal Engine | **5.7.2+** | MetaSounds Builder API (experimental since 5.4) |
| Wwise | **2025.1.4+** | WAAPI enabled (Project Settings > Wwise > Enable WAAPI) |
| Python | 3.10+ | MCP server runtime |
| Wwise Authoring | Running | WAAPI WebSocket on localhost:8080 (66 functions) |

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

### UE5 Plugin Installation

1. Copy `ue5_plugin/UEAudioMCP/` to your project's `Plugins/` folder
2. Enable **UEAudioMCP** in the plugin manager (Editor module, TCP server)
3. Enable **SIDMetaSoundNodes** (Runtime module, SID chip nodes)
4. Rebuild -- SID nodes appear under "ReSID SIDKIT Edition" category in MetaSounds editor

---

## Development Status

```
Phase 1: Wwise MCP Server        Done    20 tools, WAAPI bridge
Phase 2: Knowledge Base           Done    643 entries, TF-IDF search (178 MS nodes), keyword search (55 BP)
Phase 3: UE5 Plugin + Tools       Done    C++ plugin (35 cmds), 63 tools, TCP protocol
Phase 4: Orchestration            Done    11 patterns, AAA project, 3-mode auto-detection
Phase 5: ReSID SIDKIT Edition     Done    5 custom C++ MetaSounds nodes, 3 templates
Phase 6: Blueprint Scanner        Done    Graph inspection, editor menu, batch scanner
Phase 7: Blueprint Builder        Done    8 MCP tools, audio function allowlist, compile
Phase 8: Engine Registry Sync     Done    842 MS nodes + 979 BP funcs synced from live engine
Phase 9: Data Integrity           Done    25/25 templates verified, 128 class_name mappings
Phase 10: Production Templates    Done    +12 from Lyra/StackOBot, 33/33 MS + 34 BP validated
```

### Coming Next

- **End-to-end testing** -- Build MetaSounds + wire Blueprints + hear audio in PIE
- **AudioLink integration** -- Automated MetaSounds -> Wwise routing via AudioLink bridge
- **Video demo** -- Prompt-to-audio pipeline walkthrough
- **A2HW Protocol** -- Agent-to-Hardware protocol for AI-controlled audio across platforms

---

## Agent Skills

Install UE Audio agent skills for Claude Code, Cursor, Windsurf, and [35+ other agents](https://skills.sh):

```bash
npx skills add koshimazaki/ue-audio-skills
```

| Skill | What it does |
|-------|-------------|
| `/mcp-plugin` | TCP plugin control -- 35 commands for building MetaSounds graphs, scanning blueprints, listing assets |
| `/metasound-dsp` | MetaSounds DSP specialist -- 178 nodes, Builder API, signal flow patterns, graph templates |
| `/unreal-bp` | Blueprint audio logic -- game event detection, parameter wiring, asset scanning |
| `/build-system` | Full pipeline orchestrator -- generates complete 3-layer audio systems from a single description |

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
