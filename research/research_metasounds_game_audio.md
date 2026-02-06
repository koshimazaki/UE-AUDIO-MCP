# MetaSounds Game Audio Patterns -- Research Summary

_Generated: 2026-02-06 | Sources: 40+ | Target: MCP Server Scoping for MetaSounds Patch Generation_

## Quick Reference

<key-points>
- MetaSounds is UE5's node-based DSP audio system replacing Sound Cues -- flow graph, not execution graph
- Three asset types: Source (playable), Patch (reusable subgraph), Preset (parameter overrides on parent)
- Builder API (experimental, UE 5.4+) enables runtime graph creation via C++ and Blueprint -- the critical API for an MCP server
- MetaSoundFrontendDocument struct holds all graph data (nodes, edges, style metadata) inside UAsset files
- No existing MCP server handles MetaSounds -- gap confirmed across all UE5 MCP projects
- RNBO (Cycling '74) can export Max/MSP patches as MetaSound nodes -- proves external toolchain viability
- Lyra starter game is the canonical reference implementation for all 6 audio patterns below
</key-points>

---

## 1. Architecture: How MetaSounds Work

### Asset Types

| Type | Purpose | Playable? | Key Use |
|------|---------|-----------|---------|
| **MetaSound Source** | Self-contained audio generator | Yes | Final playable sound |
| **MetaSound Patch** | Reusable node subgraph | No (needs Source host) | Shared logic (e.g., random pitch, array player) |
| **MetaSound Preset** | Read-only graph from parent + input overrides | Depends on parent | Variants (same gun, different settings) |

### Graph Model

- **Flow graph** (not execution graph like Blueprints)
- Signal flows from inputs through processing nodes to audio output
- Data between nodes passed **by reference** (not copied) -- auto-optimized to static C++
- **Sample-accurate timing** at audio-buffer level
- Supports audio-rate parametric modulation (node params modulated by audio buffers)

### Data Types (Pin Types)

| Type | Description |
|------|-------------|
| Audio | Signal buffers for DSP manipulation |
| Trigger | Sample-accurate execution signals (modular synthesis style) |
| Float | Block-rate numeric values |
| Int32 | Integer values |
| Bool | Boolean flags |
| Time | Duration values |
| String | Labels/debugging |
| UObject | Asset references (USoundWave, etc.) |
| Enum | Enumerated variables |
| WaveAsset | Sound file references |
| Array variants | Arrays of any of the above |

### Interfaces (Built-in)

| Interface | Provides | Inputs/Outputs |
|-----------|----------|----------------|
| UE.Source.OneShot | One-shot playback | OnPlay (trigger in), OnFinished (trigger out) |
| UE.Attenuation | Distance-based volume | Distance (float in) |
| UE.Spatialization | 3D positioning | Azimuth, Elevation (float in) |

---

## 2. Complete Node Reference

### Generators
- Additive Synth, Saw, Sine, Square, Triangle
- SuperOscillator, WaveTable Oscillator, WaveTable Player
- Low Frequency Noise, Low-Frequency Oscillator (LFO)
- Noise (pink/white), Perlin Noise

### Wave Players
- Wave Player (Mono, Stereo, Quad, 5.1, 7.1)
- Properties: Loop, LoopStart, LoopDuration, StartTime, PitchShift
- Sample-accurate concatenation for seamless looping

### Envelopes
- AD Envelope (Attack-Decay)
- ADSR Envelope (Attack-Decay-Sustain-Release)
- Crossfade
- WaveTable Envelope
- Evaluate WaveTable
- Each has Audio-rate and Float-rate versions

### Filters
- Biquad Filter, Dynamic Filter, Ladder Filter
- State Variable Filter
- One-Pole High Pass / Low Pass Filter
- Sample And Hold
- Bitcrusher
- Mono/Stereo Band Splitter

### Delays
- Delay, Stereo Delay
- Delay Pitch Shift
- Diffuser
- Grain Delay

### Dynamics
- Compressor, Limiter
- Decibels to Linear Gain / Linear Gain to Decibels

### Triggers
- Trigger Accumulate, Trigger Any
- Trigger Compare, Trigger Control
- Trigger Counter, Trigger Delay
- Trigger Filter, Trigger Once
- Trigger On Threshold, Trigger On Value Change
- Trigger Pipe, Trigger Repeat
- Trigger Route

### Arrays
- Get, Set, Num (count)
- Random Get (with optional weight array)
- Shuffle (no-repeat randomization)
- Concatenate, Subset

### Math
- Add, Subtract, Multiply, Divide
- Abs, Clamp, Log, Power, Modulo
- Map Range, Min, Max
- Filter Q To Bandwidth
- Linear To Log Frequency

### Mix
- Mono Mixer (N inputs to 1)
- Stereo Mixer (N stereo inputs to 1)

### Spatialization
- ITD Panner (Interaural Time Difference)
- Stereo Panner
- Mid-Side Encode / Decode

### Music
- Frequency To MIDI / MIDI To Frequency
- MIDI Note Quantizer
- Scale to Note Array
- BPM To Seconds

### Random
- Random Bool, Random Float, Random Int, Random Time

### Debug
- Get Wave Info, Print Log

### External IO
- Audio Bus Reader
- Wave Writer

### General / Utility
- Envelope Follower
- Flanger, RingMod, WaveShaper
- InterpTo (interpolation)
- Get WaveTable From Bank

---

## 3. Six Game Audio Patterns

### Pattern 1: Gunshots (One-Shot Weapon Fire)

**Goal:** Non-repetitive weapon fire with layered components and environmental response.

**Typical Graph Structure:**
```
[OnPlay Trigger] --> [Trigger Route] --> [Random Get (WaveAsset Array)]
                                              |
                                              v
                                     [Wave Player (Mono)]
                                              |
                                     [Random Float] --> pitch input
                                              |
                                              v
                                     [ADSR Envelope] (short attack, fast decay)
                                              |
                                     [Multiply] (wave * envelope)
                                              |
                                     [Stereo Mixer] <-- [Wave Player: tail/reverb layer]
                                              |
                                     [Output]
```

**Key Nodes Used:**
- **Random Get** on WaveAsset array (3-8 gunshot samples) -- avoids "machine gun" repetition
- **Wave Player Mono** with pitch shift input from Random Float (range: -0.05 to +0.05)
- **ADSR Envelope** with very short attack (~1ms), short decay, no sustain, short release
- **Stereo Mixer** to layer: close shot + mechanical layer + reverb tail
- **Trigger Route** for single-shot vs burst logic

**Lyra Implementation Details:**
- lib_Whizby patch: bullet flyby with incoming/receding sound phases
- lib_DovetailClip patch: blends previous audio with new results using stereo balance
- Raycast-based reflection system: "shoots out raycasts + bounce rays, determines space from ray travel distance and energy absorption"
- 8-tap delay for early reflections, frequency clamped 300Hz-10kHz
- Convolution reverb using IR assets for room response

**Blueprint Integration:**
- Set Float Parameter for pitch/intensity
- Execute Trigger Parameter for fire event
- Concurrency settings limit simultaneous instances for rapid-fire weapons

---

### Pattern 2: Footsteps / Walking

**Goal:** Surface-aware, randomized, animation-synced footstep audio.

**Typical Graph Structure:**
```
[OnPlay Trigger] --> [Input: SurfaceType (Int32)]
                           |
                    [Trigger Route] --> branch per surface
                           |
            +--------------+--------------+
            |              |              |
    [Array: Concrete] [Array: Dirt] [Array: Grass]
            |              |              |
    [Random Get]    [Random Get]   [Random Get]
            |              |              |
            +------[Wave Player]----------+
                        |
                [Random Float] --> pitch variation
                        |
                [AD Envelope] (sharp attack, quick decay)
                        |
                [One-Pole Low Pass] (optional surface EQ)
                        |
                [Output]
```

**Key Nodes Used:**
- **Input parameter: SurfaceType** (Int32 or Enum) set from Blueprint via line trace
- **Trigger Route** to select correct array based on surface
- **Random Get / Shuffle** on per-surface WaveAsset arrays (5-10 samples each)
- **Random Float** for subtle pitch variation (range: -0.03 to +0.03)
- **AD Envelope** for percussive transient shaping
- **One-Pole Low Pass Filter** -- softer for grass/dirt, brighter for concrete/metal

**Surface Detection (Blueprint Side):**
- Line trace from foot bone downward
- Physical Material lookup on hit result
- Map Physical Material to surface type integer
- Pass to MetaSound via Set Int32 Parameter on Audio Component

**Community Implementations:**
- Nemisindo Adaptive Footsteps: 4 shoe types, 7 surface types, firmness control, randomness parameter (0-1.0, default 0.5)
- Epic tutorial: First-person footfalls with terrain presets using MetaSounds

---

### Pattern 3: Ambient Sounds

**Goal:** Looping, layered environmental audio with natural variation and distance falloff.

**Typical Graph Structure:**
```
[OnPlay Trigger]
      |
      +--> [Wave Player 1: base layer] (Loop=true)
      |           |
      |    [Stereo Panner] --> [Mono Mixer]
      |                              |
      +--> [Wave Player 2: detail layer] (Loop=true)
      |           |
      |    [Random Float] --> pitch (subtle drift)
      |           |
      |    [Stereo Panner] --> [Mono Mixer]
      |                              |
      +--> [Trigger Repeat] --> [Random Get (oneshot details)]
                  |
           [Wave Player 3: random detail stings]
                  |
           [AD Envelope]
                  |
           [Stereo Panner] --> [Mono Mixer]
                                     |
                              [Stereo Mixer: all layers]
                                     |
                              [Output]
```

**Key Nodes Used:**
- **Wave Player** with Loop=true, LoopStart, LoopDuration for base layers
- **Trigger Repeat** with random time intervals for sporadic detail sounds (birds, drips, creaks)
- **Random Get** on detail sound arrays
- **AD/ADSR Envelope** for natural fade of detail elements
- **Stereo Panner** for width variation across layers
- **LFO** modulating filter cutoff for subtle movement in base layer
- **Perlin Noise** or **Low Frequency Noise** for organic parameter drift

**Distance Attenuation:**
- Handled via Attenuation Settings asset on the Audio Component (not inside MetaSound graph)
- UE.Attenuation interface provides Distance input for internal distance-based mixing
- Individual layer attenuation: use Distance input with Map Range to fade detail layers at different distances

**Lyra Implementation:**
- mx_PlayAmbientElement patch: spawns randomized ambient sounds with initial delays
- Wind system: raycast-driven, adjusts volume based on player velocity + environment shape

---

### Pattern 4: Panning / Spatial Placement

**Goal:** 3D positioned audio with binaural rendering and object-based spatialization.

**Typical Graph Structure:**
```
[UE.Spatialization Interface]
      |
      +--> Azimuth (float) --> [ITD Panner]
      +--> Elevation (float) --> [ITD Panner]
      |
[Wave Player] --> [Processing chain] --> [ITD Panner] --> [Output Stereo]
```

**Key Nodes Used:**
- **ITD Panner** (Interaural Time Difference) -- primary 3D panner for headphone HRTF rendering
- **Stereo Panner** -- simpler left/right positioning for speaker output
- **Mid-Side Encode/Decode** -- stereo width manipulation
- **UE.Spatialization** interface provides Azimuth and Elevation from world position

**Spatialization Methods:**
| Method | Best For | Notes |
|--------|----------|-------|
| ITD Panner | Headphones/HRTF | Binaural, data-derived filters from angle |
| Stereo Panner | Speakers | Traditional L/R balance, breaks down with HRTF |
| Attenuation Settings | General | Volume falloff, air absorption, occlusion |

**HRTF Notes:**
- Head-Related Transfer Function renders binaural spatialization
- Built from impulse recordings as function of angle relative to listener geometry
- Only works well with headphones -- degrades on stereo speakers
- UE5 provides built-in HRTF or supports third-party (atmoky trueSpatial)

**Lyra Attenuation Presets:**
- Volume falloff over distance
- ITD-based 3D spatialization
- Air absorption (frequency-dependent filtering)
- Occlusion effects from environmental obstacles

---

### Pattern 5: UI Sounds

**Goal:** Non-spatial interface feedback (clicks, hovers, notifications).

**Typical Graph Structure:**
```
[OnPlay Trigger] --> [Input: UIEventType (Int32)]
                           |
                    [Trigger Route]
                           |
            +---------+----+----+---------+
            |         |         |         |
      [Click]   [Hover]   [Back]   [Confirm]
            |         |         |         |
      [Sine Gen] [Wave Player] [Sine] [Wave Player]
            |         |         |         |
      [AD Env]  [AD Env]  [AD Env] [ADSR Env]
            |         |         |         |
            +----[Mono Mixer]----+---------+
                       |
                [One-Pole LPF] (optional warmth)
                       |
                [Output]
```

**Key Nodes Used:**
- **Sine / Triangle generators** for procedural click/blip synthesis
- **AD Envelope** with very short attack and decay (1-50ms) for percussive clicks
- **Wave Player** for sample-based UI sounds
- **Trigger Route** to select sound variant based on UI event type
- **Map Range** to scale input parameters to useful ranges
- **Frequency To MIDI / MIDI To Frequency** for musical UI tones

**Playback Method:**
- `UGameplayStatics::PlaySound2D()` -- no world position, heard regardless of camera
- Called from UI widget button click/hover functions
- Or: Spawn Audio Component with no attenuation

**Design Notes:**
- UI sounds are typically 2D (no spatialization)
- Keep MetaSound graphs simple for UI -- minimize DSP overhead
- Procedural synthesis (sine + envelope) is excellent for UI: tiny footprint, infinite variation
- For musical UI themes, use MIDI To Frequency with Scale to Note Array

---

### Pattern 6: Object/Weather Sound Switches

**Goal:** Game state drives audio transitions between different sound profiles.

**Typical Graph Structure:**
```
[OnPlay Trigger]
      |
[Input: WeatherState (Int32)] --> [Trigger Route]
      |                                   |
      |                    +-------+------+-------+
      |                    |       |              |
      |               [Clear]  [Rain]        [Storm]
      |                    |       |              |
      |              [WP: wind] [WP: rain]  [WP: thunder]
      |              [Loop]    [Loop]       [Trigger Repeat + Random]
      |                    |       |              |
      |                    +--[Stereo Mixer]------+
      |                              |
[Input: Intensity (Float)] --> [Crossfade] between layers
                                     |
                              [Dynamic Filter] (intensity-driven cutoff)
                                     |
                              [Output]
```

**Key Nodes Used:**
- **Input parameters** (Int32 for state, Float for intensity) set from Blueprint
- **Trigger Route** to switch between active sound sets
- **Crossfade** node for smooth transitions between states
- **InterpTo** for gradual parameter changes (prevents clicks)
- **Wave Player** with Loop=true for continuous backgrounds
- **Trigger Repeat** with Random time for sporadic events (thunder)
- **Dynamic Filter** for intensity-driven tonal changes
- **ADSR Envelope** for layer fade-in/fade-out on state change

**Blueprint Integration Pattern:**
```
1. Weather Manager detects state change
2. Calls Set Int32 Parameter ("WeatherState", newState) on Audio Component
3. Calls Set Float Parameter ("Intensity", value) for gradual changes
4. MetaSound internally routes/crossfades based on parameter values
5. For triggers: Execute Trigger Parameter ("ThunderStrike")
```

**Lyra Music System Pattern (applicable to weather):**
- Music Manager tracks combat intensity (increases in firefights, decays in exploration)
- mx_Stingers patch: combines 5 sound types (bass, percussion-deep, percussion-light, pad, lead)
- Vertical re-mixing with Quartz clock sync
- ADSR envelopes for layer fade-in per intensity threshold

---

## 4. Builder API -- The Key to Programmatic Generation

### Overview

The MetaSound Builder API (experimental, UE 5.4+) is the primary mechanism for creating MetaSounds programmatically. This is the critical API for an MCP server approach.

### Key Classes

| Class | Module | Purpose |
|-------|--------|---------|
| MetaSound Builder Subsystem | MetaSoundEngine | Entry point -- create/access builders |
| MetaSound Editor Subsystem | Editor Only | Edit-time asset manipulation and export |
| MetaSound Source Builder | Editor/Runtime | Mutate/query MetaSound Source UObjects |
| MetaSound Patch Builder | Editor/Runtime | Mutate/query MetaSound Patch UObjects |

### Handle Types

| Handle | Purpose |
|--------|---------|
| MetaSound Node Handle | Reference to a node in the graph |
| MetaSound Node Output Handle | Reference to a specific output pin |
| MetaSound Node Input Handle | Reference to a specific input pin |

### Core Operations

**1. Create a graph:**
```
BuilderSubsystem -> CreateSourceBuilder() -> returns Builder + Graph I/O handles
```

**2. Add nodes:**
- Native nodes by class name (hold Shift + hover node names in Editor for full class names)
- Document-based nodes by referencing MetaSound Patch/Source UObjects

**3. Access pins:**
- FindNodeInput() / FindNodeOutput() -- get handle to specific pin
- FindGraphInput() / FindGraphOutput() -- get handle to graph-level I/O

**4. Connect nodes:**
- ConnectNodes(OutputHandle, InputHandle) -- equivalent to dragging wires in Editor

**5. Remove elements:**
- DisconnectNode(), RemoveNode(), RemoveGraphInput/Output(), RemoveInterface()

**6. Audition:**
- Audition() plays the graph on an AudioComponent
- LiveUpdateEnabled (Beta 5.5) provides real-time topology changes with crossfade

**7. Export:**
- BuildToAsset() serializes to a .uasset with specified name/path
- SetNodeLocation() positions nodes for Editor readability

### Current Limitations
- No variable support
- No paged input/graph support via Blueprint
- No template node support (reroutes) in Blueprint API
- Handle IDs must not be serialized (change between versions)

---

## 5. File Format and Serialization

### Internal Structure

MetaSound assets are stored as standard UE .uasset files. The core data structure is:

**MetaSoundFrontendDocument** (struct inside UMetaSoundSource / UMetaSoundPatch UObjects):
- Graph execution data (nodes, connections/edges between them)
- Style/display metadata (node positions, display names, widget info)
- Input/output definitions with types and defaults

### Paths to Programmatic Generation

| Approach | Viability | Notes |
|----------|-----------|-------|
| **Builder API (C++/Blueprint)** | Best | Official API, runtime + editor, can export to asset |
| **UAssetAPI (JSON round-trip)** | Possible but fragile | .NET tool for uasset <-> JSON, MetaSounds not explicitly supported |
| **JsonAsAsset plugin** | Partial | Imports JSON from FModel, supports audio (SoundWave), MetaSounds not listed |
| **Custom C++ plugin** | Full control | Access MetaSoundFrontendDocument directly, create graphs in code |
| **RNBO (Max/MSP export)** | Nodes only | Exports custom MetaSound nodes, not full graphs |

### Source Code References
- Plugin source: `Engine/Plugins/Runtime/Metasound/`
- StandardNodes folder: contains all built-in node implementations
- New nodes are single C++ files added to the project
- MetaSoundFrontendDocumentBuilder manipulates the document struct

---

## 6. Wwise vs MetaSounds

### Comparison

| Feature | MetaSounds | Wwise |
|---------|-----------|-------|
| Cost | Free (built-in) | Licensed (free under 1000 media assets) |
| Graph Type | DSP flow graph | Event-based + RTPC system |
| Procedural Audio | Native strength | Limited |
| Sound Designer Workflow | In-editor only | Standalone authoring tool |
| Advanced Mixing | Basic submix | Professional-grade |
| Spatial Audio | Built-in ITD/HRTF | Advanced rooms/portals |
| Blueprint Integration | Native parameters + triggers | Wwise-specific Blueprint nodes |
| Runtime Graph Modification | Yes (Builder API) | No (authored in Wwise) |

### Coexistence via AudioLink

- Available since UE 5.1
- Allows UE Audio Engine (MetaSounds) alongside Wwise simultaneously
- Use case: Wwise for dialogue/music/traditional SFX, MetaSounds for procedural elements
- AudioLink bridges the two systems at the submix level

### When to Use Which

| Scenario | Recommendation |
|----------|---------------|
| Solo/small team | MetaSounds |
| Dedicated sound designers | Wwise |
| Procedural audio (engines, weapons, weather) | MetaSounds |
| 100+ hours audio content | Wwise |
| Budget-constrained | MetaSounds |
| Console memory optimization | Wwise |
| Runtime audio graph generation (MCP server) | MetaSounds only |

---

## 7. Existing Tools and MCP Servers

### UE5 MCP Servers (None support audio)

| Project | Audio Support | Features |
|---------|--------------|----------|
| [unreal-mcp](https://github.com/chongdashu/unreal-mcp) | None | Actor management, Blueprint, Editor control |
| [UnrealMCP](https://github.com/kvick-games/UnrealMCP) | None | AI agent control of Unreal |
| [UnrealGenAISupport](https://github.com/prajwalshettydev/UnrealGenAISupport) | Planned (audio TTS) | LLM integration, scene generation |
| [runreal UE MCP](https://www.pulsemcp.com/servers/runreal-unreal-engine) | None | General Unreal Engine control |

### Related Audio Tools

| Tool | Purpose | MetaSounds? |
|------|---------|-------------|
| [RNBO MetaSound](https://github.com/Cycling74/RNBOMetasound) | Export Max/MSP patches as MetaSound nodes | Nodes only, not graphs |
| [metasound-branches](https://github.com/matthewscharles/metasound-branches) | Custom MetaSound nodes (Branches) | Custom nodes |
| [MetaSoundsSynthRepo](https://github.com/msp/MetaSoundsSynthRepo) | UE5 MetaSound synth examples | Example graphs |
| [MetaSound Transistor](https://www.fab.com/listings/29dfd80e-4689-4723-ba72-6dbed673af37) | Procedural SFX design system (Fab marketplace) | Full plugin |
| [MetaVolts Music Maker](https://unityunreal.com/unreal-engine-assets-free-download-2/ue-sound-music/773-metavolts-music-maker-generator-tool-for-easy-in-game-soundtracks-with-metasound.html) | In-game soundtrack generation | Music focused |
| [Nemisindo Footsteps](https://nemisindo.com/documentation/unreal-footsteps-metasounds) | Adaptive footstep system | Footsteps only |

---

## 8. MCP Server Scoping -- Technical Feasibility

### Viable Architecture

```
User Text Description
        |
        v
[MCP Server (Python/TypeScript)]
        |
   Parses description into graph spec
        |
        v
[Graph Spec JSON] -- intermediate representation
   {
     "type": "source",
     "interface": "UE.Source.OneShot",
     "nodes": [
       {"id": "wp1", "type": "WavePlayer_Mono", "params": {"Loop": false}},
       {"id": "rg1", "type": "RandomGet_WaveAsset", "params": {}},
       {"id": "env1", "type": "ADSREnvelope_Audio", "params": {"Attack": 0.001}},
       {"id": "mul1", "type": "Multiply_Audio", "params": {}},
       ...
     ],
     "connections": [
       {"from": "rg1.out", "to": "wp1.WaveAsset"},
       {"from": "wp1.OutAudio", "to": "mul1.InA"},
       {"from": "env1.OutEnvelope", "to": "mul1.InB"},
       ...
     ],
     "inputs": [
       {"name": "OnPlay", "type": "Trigger"},
       {"name": "Shots", "type": "WaveAsset[]"}
     ],
     "outputs": [
       {"name": "OutAudio", "type": "Audio"},
       {"name": "OnFinished", "type": "Trigger"}
     ]
   }
        |
        v
[UE5 Plugin (C++ or Blueprint)]
   Uses Builder API to:
   1. CreateSourceBuilder()
   2. Add nodes by class name
   3. Connect nodes
   4. SetNodeLocation() for readability
   5. BuildToAsset() to save
```

### Two Possible Approaches

**Approach A: MCP Server + UE5 Plugin (Recommended)**
- MCP server generates graph specification JSON
- UE5 plugin receives JSON via TCP/HTTP
- Plugin uses Builder API to construct and save MetaSound asset
- Advantage: Uses official API, editor-visible, auditionable
- Complexity: Medium (need both MCP server and UE plugin)

**Approach B: MCP Server + Direct Asset Generation**
- MCP server generates .uasset files directly using UAssetAPI
- No UE5 plugin needed
- Disadvantage: Fragile, format undocumented for MetaSounds, version-dependent
- Complexity: High (reverse-engineering required)

### Template Library Strategy

Pre-build the 6 game audio patterns as parameterized templates:

| Template | Required Inputs | Configurable |
|----------|----------------|--------------|
| Gunshot | WaveAsset array | Pitch range, layers, envelope times, reverb tail |
| Footsteps | WaveAsset arrays per surface | Surface count, pitch range, filter per surface |
| Ambient | Base loop + detail array | Layer count, detail frequency, LFO depth |
| Spatial | Source audio | Panner type (ITD/Stereo), HRTF enable |
| UI Sound | Event type mapping | Synth vs sample, envelope shape, frequency |
| State Switch | State count + audio per state | Crossfade time, intensity mapping, filter curves |

### Node Class Names (for Builder API)

To use the Builder API, you need the full C++ class names. Discover them by:
1. Hold Shift + hover over node names in MetaSound Editor
2. Check `Engine/Plugins/Runtime/Metasound/Source/MetasoundStandardNodes/`
3. Common pattern: `Metasound::FNodeClassName` registered via macros

### Key Risks

1. **Builder API is experimental** -- API may change between UE versions
2. **Node class names are not publicly documented** -- must be discovered from source
3. **No JSON-to-MetaSound path exists** -- must be built
4. **WaveAsset references** require actual .uasset sound files to exist in the project
5. **Editor visibility** -- graphs created via Builder API may not display perfectly in the Editor without SetNodeLocation() calls

---

## 9. Lyra Audio Reference Architecture

The Lyra Starter Game (Epic's canonical UE5 sample) implements a production-quality audio system worth studying.

### Lyra MetaSound Patches

| Patch Name | Purpose |
|------------|---------|
| lib_Whizby | Bullet flyby (incoming + receding phases) |
| lib_DovetailClip | Blend previous audio with new playing audio |
| lib_TriggerEvery | Periodic triggers with modulo-based reset |
| MS_Graph_RandomPitch_Stereo | Random pitch shift on stereo signals |
| mx_PlayAmbientElement | Randomized ambient sounds with initial delays |
| mx_Stingers | 5-layer music transitions (bass, perc-deep, perc-light, pad, lead) |

### Lyra Submix Architecture

```
Master
  |-- UISubmix
  |-- SFXSubmix
  |-- MusicSubmix
  |-- VoiceSubmix
  |-- ReverbSubmix
  |-- EarlyReflectionSubmix
  |-- SendEffectSubmix
```

### Lyra Signal Chain
```
Sound Source --> Mixing (Sound Classes + Submixes) --> Modulation (Control Bus) --> Output
```

### Lyra Audio Settings (DefaultGame.ini)
- DefaultControlBusMix, LoadingScreenControlBusMix
- UserSettingsControlBusMix with buses: Overall, Music, SoundFX, Dialogue, VoiceChat
- HDR/LDR submix effect chains (compressor/limiter)

---

## Resources

<references>

### Official Documentation
- [MetaSounds Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-in-unreal-engine) - Main landing page
- [MetaSounds Reference Guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-reference-guide-in-unreal-engine) - Asset types, interfaces, data types
- [Function Nodes Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasound-function-nodes-reference-guide-in-unreal-engine) - Complete node list
- [MetaSounds Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-quick-start) - Getting started tutorial
- [Builder API Documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasound-builder-api-in-unreal-engine) - Programmatic graph creation
- [Spatialization Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/spatialization-overview-in-unreal-engine) - 3D audio / HRTF
- [MetaSounds Next-Gen Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-the-next-generation-sound-sources-in-unreal-engine) - Architecture deep dive

### Tutorials
- [Creating MetaSound Nodes in C++ Quickstart](https://dev.epicgames.com/community/learning/tutorials/ry7p/unreal-engine-creating-metasound-nodes-in-c-quickstart) - Custom node development
- [Using Generator Nodes](https://dev.epicgames.com/community/learning/tutorials/DYWL/unreal-engine-using-generator-nodes-in-metasounds) - Synthesis nodes
- [How to Use MetaSound Presets](https://dev.epicgames.com/community/learning/tutorials/mXOv/unreal-engine-how-to-use-metasound-presets) - Preset system
- [Footsteps with MetaSounds](https://dev.epicgames.com/community/learning/tutorials/9GYn/how-to-make-footsteps-with-metasounds-in-unreal-engine-5) - Surface-based footsteps
- [First Person Footfalls with Terrain Presets](https://dev.epicgames.com/community/learning/tutorials/vyzR/creating-first-person-footfalls-with-metasounds-presets-for-different-terrain) - Terrain detection
- [Music and Environmental Audio for Lyra](https://dev.epicgames.com/community/learning/tutorials/ry1l/unreal-engine-music-and-environmental-audio-for-project-lyra-using-metasounds) - Full environmental system
- [Introduction to MetaSounds](https://dev.epicgames.com/community/learning/tutorials/BKPD/unreal-engine-introduction-to-metasounds) - Community intro
- [MetaSounds: From Miniguns to Music](https://dev.epicgames.com/community/learning/talks-and-demos/lMK/metasounds-in-ue5-from-miniguns-to-music) - Epic talks/demos
- [Wave Player Node Usage](https://forums.unrealengine.com/t/tutorial-metasound-wave-player-node-usage/631409) - Detailed Wave Player guide

### Community & Analysis
- [Lyra Game Core Audio Breakdown](https://www.jaydengames.com/posts/ue5-black-magic-game-core-audio/) - Detailed Lyra audio architecture
- [Lyra Music/Environmental Audio (Disasterpeace)](https://disasterpeace.com/blog/epic-games.lyra.html) - SweejTech/Sweet Justice implementation
- [Diving into UE5 MetaSounds](https://www.jesseleehumphry.com/post/diving-into-ue5-metasounds) - Practical deep dive
- [Abstracting the UE5 MetaSound](https://www.jesseleehumphry.com/post/abstracting-the-ue5-metasound) - Reusable patterns
- [MetaSounds Community Wiki](https://unrealcommunity.wiki/metasounds-d660ee) - Community reference
- [UE5 MetaSounds Gist (mattetti)](https://gist.github.com/mattetti/e89739a006591289e72c5252da1de877) - C++ node examples
- [Building an FM Synth](https://www.cenatus.org/blog/27-building-an-fm-synth-with-metasounds) - Synthesis patterns
- [Vertical Re-Mixing with Quartz](https://abovenoisestudios.com/blogeng/metasquartzverticaleng) - Music layer system
- [MetaSounds vs Wwise (Aircada)](https://aircada.com/blog/metasounds-vs-wwise) - Comparison analysis
- [Wwise UE Integration Tutorial](https://generalistprogrammer.com/tutorials/wwise-unreal-engine-integration-complete-audio-tutorial) - Wwise setup
- [Wwise AudioLink](https://www.audiokinetic.com/en/blog/adventures-with-audiolink/) - Coexistence mechanism
- [UE5 SFX Complete Guide (Outscal)](https://outscal.com/blog/sound-effects-ue5-complete-guide) - General audio guide
- [Audio in UE Quick Guide (SFXEngine)](https://sfxengine.com/blog/how-to-add-audio-in-unreal-engine) - Practical setup

### Tools & Plugins
- [RNBO MetaSound (Cycling '74)](https://github.com/Cycling74/RNBOMetasound) - Max/MSP to MetaSound nodes
- [metasound-branches](https://github.com/matthewscharles/metasound-branches) - Custom MetaSound nodes
- [MetaSoundsSynthRepo](https://github.com/msp/MetaSoundsSynthRepo) - Synth examples
- [UAssetAPI](https://atenfyr.github.io/UAssetAPI/) - .uasset JSON serialization
- [JsonAsAsset](https://github.com/JsonAsAsset/JsonAsAsset) - JSON to UE asset importer
- [Nemisindo Adaptive Footsteps](https://nemisindo.com/documentation/unreal-footsteps-metasounds) - Footstep system

### MCP Servers (UE5)
- [unreal-mcp](https://github.com/chongdashu/unreal-mcp) - AI controls Unreal via MCP
- [UnrealMCP](https://github.com/kvick-games/UnrealMCP) - AI agent Unreal control
- [UnrealGenAISupport](https://github.com/prajwalshettydev/UnrealGenAISupport) - GenAI + MCP for UE5

</references>

---

## Metadata

<meta>
research-date: 2026-02-06
confidence: high
version-checked: UE 5.4, 5.5, 5.7
builder-api-status: experimental (since 5.4)
gap-confirmed: no MCP server for MetaSounds exists
recommended-approach: MCP Server + UE5 Builder API Plugin
lyra-version: UE 5.0+ (latest with MetaSounds)
</meta>
