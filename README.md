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

**AI-powered game audio toolkit — MetaSounds graph generation & export, project scanning, and Wwise/Blueprint knowledge base via MCP for Unreal Engine 5.7.**

One MCP server. Three audio engines. 63 tools. 178 engine-verified MetaSounds nodes. Optimised for Unreal Engine 5.7** and **Wwise 2025.

> "Create a footsteps sound setup for my character -- use MetaSounds noise and filter in the patch, Blueprint trigger on anim notify"
>
> MCP generates the MetaSounds DSP graph (noise -> filter -> AD envelope) and outputs Blueprint wiring for the animation trigger.

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

## Setup

```bash
# 1. MCP Server (Python)
git clone https://github.com/koshimazaki/UE-AUDIO-MCP.git
cd UE-AUDIO-MCP && pip install -e ".[dev]"
ue-audio-mcp
```

```json
// 2. MCP Client Config (Claude Code, Cursor, etc.)
{
  "mcpServers": {
    "ue-audio-mcp": { "command": "ue-audio-mcp", "transport": "stdio" }
  }
}
```

```
// 3. UE5 Plugin — copy to project Plugins/ folder, enable in plugin manager
ue5_plugin/UEAudioMCP/        → Editor module (TCP server, 35 commands)
ue5_plugin/SIDMetaSoundNodes/  → Runtime module (SID chip nodes)
```

Works without Wwise or UE5 running -- knowledge base, templates, and offline mode always available.

| Requirement | Version |
|-------------|---------|
| Unreal Engine | **5.7.2+** (MetaSounds Builder API, experimental since 5.4) |
| Wwise | **2025.1.4+** (WAAPI enabled, WebSocket on localhost:8080) |
| Python | 3.10+ |

---

## What's Included

- **63 MCP tools** -- Wwise (20), MetaSounds (23), Blueprint (15), orchestration (5)
- **643 knowledge entries** -- 178 MetaSounds nodes, 66 WAAPI functions, 55 BP audio functions, TF-IDF search
- **73 templates** -- 33 MetaSounds DSP + 34 Blueprint logic + 6 Wwise hierarchy (33/33 MS validated)
- **35 C++ TCP commands** -- MetaSounds Builder API, Blueprint builder, graph scanning, asset queries
- **5 custom C++ nodes** -- ReSID SID chip emulator (oscillator, envelope, filter, voice, full chip)
- **11 audio system patterns** -- gunshot, footsteps, ambient, vehicle, weather, UI, SID synth...
- **Editor menu** -- Scan Project, Export MetaSounds, Server Status from UE5 menu bar
- **Engine sync** -- 842 MS nodes + 979 BP functions synced from live UE5 editor

12 templates from shipped games: **Lyra** (random EQ, whizby, stereo balance, gameplay cues, anim notify audio) and **StackOBot** (array player, looped sound, EQ+delay).

See **[REFERENCE.md](REFERENCE.md)** for full tool listing, template catalogue, knowledge base details, C++ patterns, and workflows.

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

`SIDMetaSoundNodes` is a separate Runtime module -- ships in games without the MCP TCP server.

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
