# Quartz Music System - Research Summary

_Generated: 2026-02-07 | Sources: 25+_

## Quick Reference

<key-points>
- Quartz is UE's Blueprint-exposed, sample-accurate audio scheduling system (since UE 4.26)
- Core course by Richard Stevens: 12+ tutorials covering looping music, playlists, one-shots, layer mixing, arrangement switching, quantized transitions, stingers, and advanced Quartz
- UE 4.27 project on Fab (free); all concepts transfer directly to UE5 (API is stable)
- Key pattern: Create Clock -> Set BPM -> PlayQuantized on Audio Components -> SubscribeToQuantizationEvent for game logic sync
- UE5 adds MetaSounds integration: Quartz clocks drive MetaSound triggers for procedural/interactive music
- Harmonix Plugin (UE 5.4+) complements Quartz with MIDI sequencing, Fusion Sampler, and Music Clock
</key-points>

---

## Overview

<summary>
The "Quartz Music System" is an official Epic Games learning path (course) that teaches dynamic/interactive music implementation in Unreal Engine using the Quartz subsystem. Quartz solves the fundamental timing problem between game logic (variable frame rate, ~16ms ticks) and audio rendering (fixed buffer size, sample-accurate) by providing a scheduling system that can place audio events at exact sample positions within audio buffers.

The course covers progressively complex techniques: from simple looping background music up to quantized layer mixing with arrangement switching and beat-aware stingers. The companion UE 4.27 project is available free on Fab/Marketplace.
</summary>

---

## Course Structure: All Tutorials

<details>

### Instructor
**Richard Stevens** - Senior Lecturer at Leeds Beckett University, leads the Masters in Sound and Music for Interactive Games program. Co-author of "Game Audio Implementation: A Practical Guide Using the Unreal Engine" (with Dave Raybould, Routledge/CRC Press). Website: gameaudioimplementation.com

### Course Landing Page
- **Quartz Music System** (Course): https://dev.epicgames.com/community/learning/courses/XAw/unreal-engine-quartz-music-system
- **Companion Project (Fab/Marketplace)**: https://www.fab.com/listings/2f0d06ac-9f59-40dc-9a4c-b18006a3091c
- **Engine Version**: UE 4.27 (concepts apply to UE5 unchanged)

### Individual Tutorials (in learning order)

| # | Title | URL | Description |
|---|-------|-----|-------------|
| 1 | **Quartz Music System: Introduction** | [Link](https://dev.epicgames.com/community/learning/tutorials/EbdY/unreal-engine-quartz-music-system-introduction) | Overview of the course, prerequisites, project setup, what Quartz is and why it matters for game music |
| 2 | **Looping Background Music** | [Link](https://dev.epicgames.com/community/learning/tutorials/vyJ1/unreal-engine-looping-background-music) | Simple approaches to background music, issues with looping (gap/click artifacts), why accurate timing systems are needed |
| 3 | **Music Playlists** | [Link](https://dev.epicgames.com/community/learning/tutorials/OPLl/unreal-engine-music-playlists) | Creating reusable Blueprint for music playlists with randomization and skip functionality |
| 4 | **One Shots Using Sound Cues** | [Link](https://dev.epicgames.com/community/learning/tutorials/pPY/unreal-engine-one-shots-using-sound-cues) | Musical one-shot sound effects, adding variety to audio ambiances, Sound Cue integration |
| 5 | **Core Quartz System** | (Part of course at /courses/XAw/) | Creating the Quartz clock, configuring BPM and time signature, starting/stopping clocks, the fundamental scheduling pattern |
| 6 | **Layer Mixing Using Direct Transform** | (Part of course at /courses/XAw/) | Controlling volume of synchronized music layers via direct value setting (Set Volume Multiplier) |
| 7 | **Layer Mixing Using Timelines** | [Link](https://dev.epicgames.com/community/learning/courses/XAw/unreal-engine-quartz-music-system/nO2L/unreal-engine-layer-mixing-using-timelines) | Using UE Timeline nodes for smooth volume crossfades between music layers |
| 8 | **Layer Mixing Using Curves** | (Part of course at /courses/XAw/) | Using Float Curves for non-linear volume transitions and complex crossfade shapes |
| 9 | **Arrangement Switching** | (Part of course at /courses/XAw/) | Switching between different musical arrangements (verse/chorus/bridge) |
| 10 | **Quantized Layer Mixing and Arrangement Switching** | [Link](https://dev.epicgames.com/community/learning/tutorials/k80P/unreal-engine-quantized-layer-mixing-and-arrangement-switching) | Using quantization events and gates to achieve arrangement switching at musical junctures (bars, beats) |
| 11 | **Transitional Demonstration and Quantization** | [Link](https://dev.epicgames.com/community/learning/tutorials/xdZX/unreal-engine-transitional-demonstration-and-quantization) | Building a sophisticated transitional music system, the "Demo Transition Blueprint" |
| 12 | **Unquantized and Quantized Stingers** | [Link](https://dev.epicgames.com/community/learning/tutorials/wrvX/unreal-engine-unquantized-and-quantized-stingers) | Implementing short musical phrases (stingers) that play over existing music, both free-running and beat-synced |
| 13 | **Changing Tempo and Time Signatures** | [Link](https://dev.epicgames.com/community/learning/tutorials/MlYY/unreal-engine-changing-tempo-and-time-signatures) | Changing Quartz clock tempo in sync with musical transitions, implementing time signature changes |
| 14 | **Advanced Quartz** | (Part of course at /courses/XAw/) | Advanced techniques for music systems using Quartz |

### Learning Outcomes
- Construct music playlists for background game music and implement musical one-shots
- Control volume of synchronized music layers via direct transformation, timelines, and curves
- Use a variety of quantization settings for musical transitions
- Change musical tempo and time signatures in sync with gameplay
- Implement rhythmically and harmonically aware musical stingers

</details>

---

## Quartz Architecture: Core Concepts

<details>

### The Timing Problem
Game logic runs on the game thread at variable frame rates (~60fps = ~16ms). Audio renders on the audio thread in fixed buffers (typically 2048 samples at 48kHz = ~43ms). Playing a sound "now" from game code actually means "at the start of the next audio buffer" -- introducing up to 43ms of jitter. For music, this is unacceptable.

### How Quartz Solves It
Quartz lets you schedule audio events to specific **sample positions** within audio buffers. When you call `PlayQuantized()`, the command is forwarded to the audio render thread, which calculates the exact sample where the next beat/bar/quantization boundary falls, and triggers the sound at that sample -- even mid-buffer.

### Key Objects

```
UQuartzSubsystem (World Subsystem)
  |
  +-- Creates/Manages Clocks
  |
  +-- UQuartzClockHandle (Game Thread Proxy)
        |
        +-- Controls -> Quartz Clock (Audio Thread)
                          |
                          +-- Quartz Metronome
                                |
                                +-- Tracks beats/bars at configured BPM/time signature
                                +-- Fires quantization events
                                +-- Schedules commands at exact sample positions
```

**Quartz Subsystem** (`UQuartzSubsystem`)
- World subsystem, access via `GetQuartzSubsystem()` Blueprint node
- Creates clocks, verifies clock existence, queries latency information
- General system functionality independent of specific clocks

**Quartz Clock** (Audio Thread)
- Responsible for scheduling and triggering events on the audio rendering thread
- Contains a Quartz Metronome
- Created with BPM and time signature settings

**Quartz Clock Handle** (`UQuartzClockHandle`)
- Game-thread proxy for controlling the Quartz Clock
- Acquired via the Quartz Subsystem
- All gameplay interaction goes through this handle

**Quartz Metronome** (Audio Thread)
- Object on the audio render thread
- Tracks passage of time based on BPM and time signature
- Schedules future commands at quantization boundaries
- Fires delegate events when musical durations occur

**Quartz Quantization Boundary** (`FQuartzQuantizationBoundary`)
- Struct that tells the Audio Mixer exactly when to schedule an event
- Fields: Quantization (time value), Multiplier (how many of that value), CountingReferencePoint (Bar/Transport relative)

### Scheduling Model
Two independent time bases:
- **Absolute time**: Seconds-based values
- **Musical time**: Bars and beats relative to tempo/signature

Sample-accurate rendering occurs **mid-buffer** rather than buffer-aligned, eliminating traditional command latency.

</details>

---

## Blueprint Nodes Reference

<details>

### Quartz Subsystem Nodes

| Node | Description |
|------|-------------|
| `Get QuartzSubsystem` | Gets the world Quartz subsystem reference |
| `Create New Clock` | Creates a new Quartz clock with name and settings (FQuartzClockSettings, FQuartzTimeSignature) |
| `Does Clock Exist` | Checks if a named clock exists |
| `Get Handle For Clock` | Gets a clock handle by name |
| `Stop Clock` | Stops a named clock |
| `Pause Clock` | Pauses a named clock |
| `Get Duration Of Quantization Type In Seconds` | Converts a quantization type to seconds at current BPM |

### Quartz Clock Handle Nodes

| Node | Description |
|------|-------------|
| `Start Clock` | Starts the clock ticking |
| `Stop Clock` | Stops the clock |
| `Pause Clock` | Pauses the clock |
| `Resume Clock` | Resumes a paused clock |
| `Set Beats Per Minute` | Changes the clock BPM |
| `Subscribe To Quantization Event` | Fires delegate on specified quantization boundary (e.g., Beat, Bar) |
| `Subscribe To All Quantization Events` | Fires delegate on every quantization event type |
| `Reset Transport Quantized` | Resets playback position at a quantized boundary |
| `Get Beats Per Minute` | Gets current BPM |
| `Get Current Quantization Boundary` | Gets current position info |

### Audio Component Nodes (Quartz-aware)

| Node | Description |
|------|-------------|
| `Play Quantized` | Plays audio at specified quantization boundary on a clock. Key params: Clock Handle, Quantization Boundary |
| `Set Trigger Parameter` | Sets a trigger parameter on a MetaSound audio component (for layer activation) |

### Quantization Boundary Construction

| Node | Description |
|------|-------------|
| `Make QuartzQuantizationBoundary` | Creates boundary struct: Quantization type, Multiplier, CountingReferencePoint |
| `Make QuartzClockSettings` | Creates clock settings with time signature |
| `Make QuartzTimeSignature` | Creates time signature: numerator, beat type |

### EQuartzCommandQuantization Enum Values
All available quantization granularities:
- `Bar`
- `Beat`
- `WholeNote`
- `HalfNote`
- `DottedHalfNote`
- `QuarterNote`
- `DottedQuarterNote`
- `EighthNote`
- `DottedEighthNote`
- `SixteenthNote`
- `DottedSixteenthNote`
- `ThirtySecondNote`
- `SixteenthNoteTriplet`
- `EighthNoteTriplet`
- `QuarterNoteTriplet`
- `HalfNoteTriplet`
- `Tick`
- `Count`
- `None`

### Delegate Types

| Delegate | Description |
|----------|-------------|
| `FOnQuartzCommandEventBP` | Fires when a Quartz command completes (e.g., play started) |
| `FOnQuartzMetronomeEventBP` | Fires on metronome events (beat, bar, etc.). Params: ClockName, QuantizationType, NumBars, Beat, BeatFraction |

### Switch Node
| Node | Description |
|------|-------------|
| `Switch on EQuartzCommandQuantization` | Routes execution based on which quantization event fired (Bar, Beat, etc.) |

</details>

---

## Music System Patterns

<details>

### Pattern 1: Simple Looping Background Music
**Problem**: Standard Play/Loop creates audible gaps due to buffer boundaries.
**Solution**: Use PlayQuantized with Bar quantization to ensure seamless loops.

```
BeginPlay
  -> Get QuartzSubsystem -> Create New Clock ("MusicClock", BPM=120, 4/4)
  -> Set Beats Per Minute (120)
  -> Audio Component -> Play Quantized (Clock, Bar boundary)
```

### Pattern 2: Music Playlists
**Pattern**: Reusable Blueprint that manages a list of tracks with randomization and skip.
**Key Nodes**: Array of Sound assets, RandomInteger, PlayQuantized for gapless transitions.

### Pattern 3: Layer Mixing (Vertical Remixing)
**Architecture**: Multiple audio layers (drums, bass, melody, pad) play simultaneously, synchronized to one Quartz clock. Volume of each layer is controlled independently.

Three volume control approaches:
1. **Direct Transform**: Instant volume changes via `Set Volume Multiplier`
2. **Timelines**: Smooth crossfades using UE Timeline nodes with float tracks
3. **Curves**: Float Curve assets for complex non-linear crossfade shapes

```
Single MetaSound Source with multiple internal layers
  -> Each layer has a Trigger parameter for activation
  -> All layers share the same Quartz clock
  -> Trigger volumes in the level -> SubscribeToQuantizationEvent -> SetTriggerParameter
```

**Implementation (from Above Noise Studios)**:
```
FQuartzQuantizationBoundary:
  Quantization = Bar
  Multiplier = 1.0
  CountingReferencePoint = BarRelative
  bResetClockOnQueued = true

Three delegates:
  PlayQuantizationDelegate (FOnQuartzCommandEventBP) - fires when audio queues
  ExecuteTriggerDelegate (FOnQuartzMetronomeEventBP) - triggers layer changes
  UpdateClockDelegate (FOnQuartzMetronomeEventBP) - manages loop cycling
```

### Pattern 4: Arrangement Switching (Horizontal Re-Sequencing)
**Problem**: Switch from verse to chorus at musically appropriate moment.
**Solution**: Gate node + quantization event. The gate opens on gameplay event, but actual switch happens at next Bar boundary.

```
Gameplay Event (e.g., enter boss room)
  -> Set Gate Open
  -> SubscribeToQuantizationEvent(Bar)
  -> On next Bar: Stop current arrangement, PlayQuantized next arrangement
  -> Close Gate
```

### Pattern 5: Quantized Stingers
**Types**:
- **Unquantized**: Play immediately (fire-and-forget, no sync)
- **Quantized**: Schedule to play at next musical boundary

```
Stinger (Quantized):
  Game Event -> PlayQuantized(StingerAudioComponent, ClockHandle, Beat boundary)
  Result: Stinger plays on the next beat, harmonically aligned with current music

Stinger (Unquantized):
  Game Event -> Play() immediately
  Result: Stinger plays ASAP, may not align musically
```

### Pattern 6: Tempo and Time Signature Changes
```
At transition point:
  -> SubscribeToQuantizationEvent(Bar)
  -> On next Bar: SetBeatsPerMinute(newBPM)
  -> Optionally: ResetTransportQuantized to restart from bar 1
```

### Pattern 7: Procedural Music (UE5 + MetaSounds)
**Architecture**: MetaSounds provides the DSP graph, Quartz provides the clock.

From Quartz Quick Start guide:
```
1. Create MetaSound Sources (e.g., MSS_BeepA4, MSS_BeepA3)
   - On Play -> AD Envelope -> Multiply -> Sine -> Output
2. Level Blueprint:
   - Get QuartzSubsystem -> Create New Clock ("LevelClock")
   - Set BPM -> Create Sound 2D (for each MetaSound)
   - Start Clock -> Subscribe To All Quantization Events
   - OnQuantizationEvent -> Switch on EQuartzCommandQuantization
     - Bar -> PlayQuantized (high beep)
     - Beat -> PlayQuantized (low beep)
3. Blueprint Actor (BP_QuartzCube):
   - Get Handle For Clock -> Subscribe To Quantization Event (Beat)
   - OnBeat -> Set Actor Scale 3D (visual sync to music)
```

### Pattern 8: 8-Bar Loop with Reset (from Above Noise Studios)
```
UpdateAndResetClock pattern:
  -> Subscribe to EighthNote quantization
  -> Track current bar position
  -> When bar count reaches 8:
     -> ResetTransportQuantized at quantized boundary
     -> Loop back to bar 1
```

</details>

---

## UE4 vs UE5: What Changed

<details>

### Core API: Stable
The fundamental Quartz API is **essentially unchanged** between UE 4.27 and UE5 (through 5.7):
- `UQuartzSubsystem`, `UQuartzClockHandle`, `FQuartzQuantizationBoundary` -- same API
- `PlayQuantized`, `SubscribeToQuantizationEvent`, `CreateNewClock` -- same signatures
- `EQuartzCommandQuantization` enum -- same values
- Blueprint nodes -- same names and pin layouts

### What UE5 Adds

| Feature | Version | Description |
|---------|---------|-------------|
| **MetaSounds** | UE5.0+ | New DSP graph system. Quartz clocks can drive MetaSound triggers for procedural audio |
| **MetaSound Triggers** | UE5.0+ | Sample-accurate trigger execution within MetaSounds graphs, perfect complement to Quartz scheduling |
| **Music Nodes in MetaSounds** | UE5.0+ | Dedicated music category nodes: ScaleToNoteArray, MIDI functions, Transport Player |
| **Wave Player enhancements** | UE5.0+ | Loop points, sample-accurate concatenation, pitch-scale modulation, cue point reading |
| **Harmonix Plugin** | UE5.4+ | Experimental. MIDI sequencing, Fusion Sampler, Music Clock. Complements Quartz for music-driven gameplay |
| **MetaSounds Pages** | UE5.5+ | Platform-specific graph variants, preset support for per-platform audio |
| **Reverb Node** | UE5.5+ | Native reverb in MetaSounds (previously required external plugins) |
| **Builder API** | UE5.4+ | Experimental. Programmatic MetaSounds graph construction (relevant for MCP integration) |

### Migration Notes
- Sound Cues still work in UE5 (backward compatible), but MetaSounds is the future
- The course project (UE 4.27) can be opened in UE5 with minimal changes
- Key difference: In UE5, you can use MetaSounds Sources instead of Sound Cues with PlayQuantized -- same Blueprint pattern, better audio engine
- The `Send and Receive` Blueprint nodes were deprecated in UE5.0 Preview (use MetaSounds parameter system instead)
- Quartz Quick Start guide in UE5.7 docs uses MetaSounds Sources exclusively (not Sound Cues)

### Recommended UE5 Approach
```
UE 4.27 Pattern:
  Sound Cue -> Audio Component -> PlayQuantized(Clock) -> Subscribe events

UE5 Pattern:
  MetaSound Source -> Audio Component -> PlayQuantized(Clock) -> Subscribe events
  + MetaSound internal triggers driven by Quartz clock
  + MetaSound parameter wiring for layer control
  + (Optional) Harmonix Plugin for MIDI sequencing
```

</details>

---

## Related Resources

<details>

### Official Epic Resources

| Resource | URL | Description |
|----------|-----|-------------|
| Quartz Overview (UE5.7) | [Link](https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-quartz-in-unreal-engine) | Official Quartz documentation |
| Quartz Quick Start (UE5.7) | [Link](https://dev.epicgames.com/documentation/en-us/unreal-engine/quartz-quick-start) | Step-by-step metronome tutorial |
| Quartz Overview (UE4.27) | [Link](https://dev.epicgames.com/documentation/en-us/unreal-engine/quartz-overview?application_version=4.27) | Original UE4 documentation |
| Music Systems in UE | [Link](https://dev.epicgames.com/documentation/en-us/unreal-engine/music-systems-in-unreal-engine) | Landing page for Quartz + Harmonix |
| MetaSounds and Quartz (Livestream) | [Link](https://dev.epicgames.com/community/learning/livestreams/7v6/metasounds-and-quartz-inside-unreal) | Inside Unreal livestream demo |
| Procedural Music with Quartz (Tech Blog) | [Link](https://www.unrealengine.com/en-US/tech-blog/procedural-music-generation-with-quartz) | Epic tech blog on procedural music generation |
| Music Nodes in MetaSounds | [Link](https://dev.epicgames.com/community/learning/tutorials/qzE5/unreal-engine-music-nodes-in-metasounds) | ScaleToNoteArray, MIDI functions |
| MetaSound Function Nodes Reference | [Link](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasound-function-nodes-reference-guide-in-unreal-engine) | Complete MetaSounds node reference |
| Harmonix Plugin | [Link](https://dev.epicgames.com/documentation/en-us/unreal-engine/harmonix-plugin-in-unreal-engine) | UE5.4+ music plugin documentation |
| UQuartzClockHandle API | [Link](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/AudioMixer/Quartz/UQuartzClockHandle) | C++ API reference |
| PlayQuantized BP Reference | [Link](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Audio/Components/Audio/PlayQuantized) | Blueprint API reference |
| SubscribeToQuantizationEvent BP | [Link](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/QuartzClock/SubscribetoQuantizationEvent) | Blueprint API reference |
| Crash Course: Procedural Music with MetaSounds | [Link](https://dev.epicgames.com/community/learning/tutorials/m60q/unreal-engine-crash-course-building-a-simple-and-reactive-procedural-music-system-with-metasounds) | Community tutorial on reactive procedural music |

### Community Resources

| Resource | URL | Description |
|----------|-----|-------------|
| Vertical Remixing Part 1 (Above Noise Studios) | [Link](https://abovenoisestudios.com/blogeng/metasquartzverticaleng) | MetaSounds + Quartz layer mixing tutorial (Blueprint + C++) |
| Vertical Remixing Part 2 (Above Noise Studios) | [Link](https://abovenoisestudios.com/blogeng/metasquartzverticalengp2) | Layer triggering, clock management, delegate architecture |
| Vertical Remixing GitHub | [Link](https://github.com/abovenoisestudios/ANE_Blog_UE5_MetasoundQuartz_InteractiveMusic1) | Full UE5 project source |
| Quartz Template Kit (Michael Gary Dean) | [Link](https://michaelgarydean.itch.io/quartz-music-system-template-kit) | Community template kit extending the course concepts |
| UE5 MetaSounds Gist | [Link](https://gist.github.com/mattetti/e89739a006591289e72c5252da1de877) | Quick reference for MetaSounds features |
| Forum: Course Discussion | [Link](https://forums.unrealengine.com/t/course-quartz-music-system/542820) | Community discussion about the course |
| Forum: Variable BPM in Quartz | [Link](https://forums.unrealengine.com/t/ue5-quartz-dealing-with-a-variable-bpm/1229180) | Advanced: dealing with tempo changes |

### Books
- **Game Audio Implementation: A Practical Guide Using the Unreal Engine** - Richard Stevens & Dave Raybould (Routledge, 2015) - The instructor's comprehensive UE audio textbook

</details>

---

## C++ Module Dependencies (for UE5 Plugin Development)

<details>

Required in `.Build.cs` for Quartz functionality:

```csharp
PublicDependencyModuleNames.AddRange(new string[] {
    "AudioMixer",        // UQuartzSubsystem, UQuartzClockHandle
    "Engine",            // EQuartzCommandQuantization, FQuartzQuantizationBoundary
});

// If using MetaSounds with Quartz:
PublicDependencyModuleNames.AddRange(new string[] {
    "MetasoundEngine",   // UMetaSoundSource
});
```

Required headers:
```cpp
#include "Quartz/AudioMixerClockHandle.h"    // UQuartzClockHandle
#include "MetasoundSource.h"                  // UMetaSoundSource (UE5 only)
#include "Components/AudioComponent.h"        // UAudioComponent
```

</details>

---

## Implications for UE Audio MCP

<details>

### What This Means for Our Project

1. **Quartz tools needed**: We should add Quartz clock management tools to the MCP server:
   - `quartz_create_clock(name, bpm, time_signature)`
   - `quartz_set_bpm(clock_name, bpm)`
   - `quartz_subscribe_event(clock_name, quantization_type)`
   - These route through the C++ plugin TCP connection (like MetaSounds Builder tools)

2. **Template expansion**: The 8 music system patterns from the course map directly to orchestrator templates:
   - `looping_music` -- Simple quantized loop
   - `music_playlist` -- Sequential/random track playlist
   - `layer_mixing` -- Vertical remixing (multiple layers, volume control)
   - `arrangement_switching` -- Horizontal re-sequencing (verse/chorus/bridge)
   - `quantized_stingers` -- Beat-synced musical accents
   - `tempo_change` -- Dynamic BPM transitions

3. **C++ plugin commands to add**:
   - `create_quartz_clock` -- FQuartzClockSettings + FQuartzTimeSignature
   - `start_clock` / `stop_clock` / `pause_clock` / `resume_clock`
   - `set_bpm` -- SetBeatsPerMinute on clock handle
   - `play_quantized` -- PlayQuantized on AudioComponent with boundary
   - `subscribe_quantization` -- SubscribeToQuantizationEvent
   - `reset_transport` -- ResetTransportQuantized

4. **Blueprint wiring**: Quartz operations are primarily Blueprint-level, making them ideal for the BP tools layer (WHEN layer in our architecture)

5. **MetaSounds + Quartz synergy**: The MetaSounds graph (WHAT layer) provides the sound, the Quartz clock (managed via Blueprint/WHEN layer) provides the timing. This maps perfectly to our three-layer architecture.

</details>

---

## Metadata

<meta>
research-date: 2026-02-07
confidence: high
version-checked: UE 4.27, UE 5.0-5.7
instructor: Richard Stevens (Leeds Beckett University)
course-tutorials: 14 (12+ confirmed URLs)
companion-project: UE 4.27 (Fab free download)
api-stability: Quartz API stable from UE 4.26 through UE 5.7
</meta>
