# Ambient and Procedural Sound Design - Research Summary

_Generated: 2026-02-07 | Sources: 18+ | Authors: Richard Stevens & Dave Raybould_

## Quick Reference

<key-points>
- Official Epic Dev Community learning path: 14+ individual tutorials, ~2h16m total runtime
- UE 4.23-4.24 project with complete game world (populated + blank levels for practice)
- Covers: area loops, source loops, one-shots, randomization, occlusion (3 methods), procedural layering/modulation, Blueprint audio systems
- Core UE4 patterns: Sound Cue node graphs, Ambient Sound actors, Audio Volumes, Sound Attenuation assets, Blueprint AudioComponent spawning
- Same authors offer UE5 follow-up: "MetaSounds & More" (Foundation + Control & Communication), 7+ hours, 286 pages
- UE5 migration: Sound Cues still work but MetaSounds replace them for procedural audio; Ambient Sound actors, Audio Volumes, and Blueprint patterns transfer directly
</key-points>

---

## Overview

<summary>
"Ambient and Procedural Sound Design" is an official Epic Games learning path created by Richard Stevens and Dave Raybould, two of the foremost educators in game audio implementation. The course teaches how to add audio ambiance to game scenes, progressing from basic looping and one-shot techniques through advanced procedural and component-based sound production using Blueprints. It ships with a complete UE 4.23-4.24 project containing a fully populated game world and an empty version for hands-on practice. The course is part of a larger set of 6 audio courses (18 hours total) that Stevens & Raybould created for Epic's online learning portal.
</summary>

---

## Course Structure

### Main Course Page
**URL**: https://dev.epicgames.com/community/learning/courses/qR/unreal-engine-ambient-and-procedural-sound-design

### Individual Tutorials (In Order)

| # | Tutorial Title | URL | Key Topics |
|---|---------------|-----|------------|
| 1 | **Introduction to the Course** | [Link](https://dev.epicgames.com/community/learning/tutorials/2bv/unreal-engine-introduction-to-the-course) | Course overview, project setup, two map versions (completed + blank) |
| 2 | **Importing and Organizing Audio Assets** | [Link](https://dev.epicgames.com/community/learning/tutorials/zX0/unreal-engine-importing-and-organizing-audio-assets) | Audio file formats (WAV, AIFF, FLAC, OGG), import methods, Content Browser organization |
| 3 | **Area Loops** | [Link](https://dev.epicgames.com/community/learning/tutorials/Vd2/unreal-engine-area-loops) | Ambient Sound actor for background ambiance, stereo room tones, attenuation spheres (inner radius = full volume, outer = falloff) |
| 4 | **Source Loops and Virtual Voices** | [Link](https://dev.epicgames.com/community/learning/tutorials/e9Z/unreal-engine-source-loops-and-virtual-voices) | Mono source positioning, spatialization (Panning vs Binaural), Non-Spatialized Radius, virtual voice system |
| 5 | **Attenuation Functions and Custom Curves** | [Link](https://dev.epicgames.com/community/learning/tutorials/5Xd/unreal-engine-attenuation-functions-and-custom-curves) | Attenuation function types, custom curves, reusable Sound Attenuation assets, distance modeling |
| 6 | **One Shots Using Sound Cues** | [Link](https://dev.epicgames.com/community/learning/tutorials/pPY/unreal-engine-one-shots-using-sound-cues) | Sound Cue creation, Random node, Delay node, Looping node for randomly timed one-shots (e.g., bird calls) |
| 7 | **Switching Sounds for Fake Occlusion** | [Link](https://dev.epicgames.com/community/learning/tutorials/JXl/unreal-engine-switching-sounds-for-fake-occlusion) | Simple occlusion method: switch between outdoor/indoor sound variants based on player location |
| 8 | **Ambient Zones for Occlusion** | [Link](https://dev.epicgames.com/community/learning/tutorials/1bB/unreal-engine-ambient-zones-for-occlusion) | Audio Volumes with Ambient Zone settings, mimicking wall/surface occlusion, interior/exterior transitions |
| 9 | **Dynamic Occlusion with Ambient Zones** | [Link](https://dev.epicgames.com/community/learning/tutorials/DB8/unreal-engine-dynamic-occlusion-with-ambient-zones) | Dynamic ambient zone adjustment for changing spaces, Blueprint-driven zone control |
| 10 | **Occlusion with Simple Raycasting** | [Link](https://dev.epicgames.com/community/learning/tutorials/qBY/unreal-engine-occlusion-with-simple-raycasting) | Built-in dynamic occlusion using game geometry, Line Trace, occlusion trace settings |
| 11 | **Procedural Sound Design: Randomization** | [Link](https://dev.epicgames.com/community/learning/tutorials/Z8w/unreal-engine-procedural-sound-design-randomization) | Random node options, weighting specific inputs, avoiding repetition |
| 12 | **Procedural Sound Design: Modulation Approaches** | [Link](https://dev.epicgames.com/community/learning/tutorials/b8d/unreal-engine-procedural-sound-design-modulation-approaches) | Pitch modulation, volume modulation, Sound Cue Modulator nodes for variation |
| 13 | **Procedural Sound Design: Layered Approaches** | [Link](https://dev.epicgames.com/community/learning/tutorials/avW/unreal-engine-procedural-sound-design-layered-approaches) | Component-based sound decomposition, combinatorial layering (4 categories x 3 variants = 81 combos), switch nodes for material-based selection |
| 14 | **Player Oriented Sound Blueprint 01** | [Link](https://dev.epicgames.com/community/learning/tutorials/Yz6/unreal-engine-player-oriented-sound-blueprint-01) | Blueprint AudioComponent spawning, playing sounds at player-relative locations, reusable Blueprint audio systems |
| 15 | **Blueprint-based Sound Movement Using Splines** | [Link](https://dev.epicgames.com/community/learning/tutorials/Ekj/unreal-engine-blueprint-based-sound-movement-using-splines) | Moving_Sounds Blueprint, animating sounds along Spline components, spatial movement |

**Additional project content**: Interactive elements including environmental triggers, physics-based audio events (barrels/objects falling), fully populated ambient environment.

### Project Structure
```
AmbientAndProceduralSound/
  Content/
    Maps/
      EPIC_AUDIO_Courses_V001        -- Completed example (all audio implemented)
      EPIC_AUDIO_Courses_V001_Blank  -- Empty level for practice
    Audio/
      Ambience/                      -- Pre-organized audio assets by category
      ...
```

---

## Key Technical Patterns

### 1. Area Loops (Background Ambiance)

**Purpose**: Establish spatial context with stereo background "room tone" beds.

**Pattern**:
- Place **Ambient Sound** actor in level
- Assign **stereo** Sound Wave or Sound Cue
- Configure **Sound Attenuation** asset:
  - Inner Radius = room/area dimensions (full volume zone)
  - Outer Radius = falloff distance to neighboring areas
  - Attenuation function: Linear, Logarithmic, NaturalSound, or Custom Curve
- Keep loops "relatively simple" to avoid noticeable repetition artifacts
- Stack multiple Ambient Sound actors at different distances for layered detail

**Actors/Components**: `AmbientSound`, `SoundAttenuation`, `SoundWave`

### 2. Source Loops (Object-Specific Sounds)

**Purpose**: Position mono sounds at specific world locations (waterfalls, machinery, fires).

**Pattern**:
- Place **Ambient Sound** actor at sound source location
- Use **mono** Sound Wave for proper spatialization
- Configure spatialization method:
  - **Panning**: Speaker-based (for speaker playback)
  - **Binaural**: HRTF-based (for headphone playback)
- Set **Non-Spatialized Radius**: Reduces panning artifacts when player is very close
- **Virtual Voices**: Engine automatically virtualizes distant/quiet sounds (saves CPU)

**Key Settings**: Spatialization Method, Non-Spatialized Radius, Focus/Non-Focus Azimuth

### 3. One-Shots via Sound Cues

**Purpose**: Add life to environments with randomly timed, varied sound effects.

**Sound Cue Node Graph Pattern** (bird call example):
```
[Random] --> [Delay] --> [Looping] --> [Output]
   |
   +-- SoundWave_Bird_01
   +-- SoundWave_Bird_02
   +-- SoundWave_Bird_03
```

**Key Sound Cue Nodes**:
- `Random`: Selects randomly from multiple inputs (with optional weighting)
- `Delay`: Adds variable timing between plays
- `Looping`: Enables continuous playback
- `Modulator`: Applies pitch/volume randomization
- `Concatenator`: Chains sounds sequentially
- `Switch`: Selects based on game state (material type, etc.)
- `Mixer`: Combines multiple simultaneous layers
- `Attenuation`: Per-node distance falloff

### 4. Occlusion Systems (3 Methods, Increasing Complexity)

**Method A -- Fake Occlusion (Sound Switching)**:
- Maintain outdoor + indoor variants of each ambient sound
- Switch between them based on player entering/exiting Audio Volume triggers
- Simplest approach, widely used in production

**Method B -- Ambient Zones**:
- Place **Audio Volume** actors to define indoor/outdoor regions
- Configure **Ambient Zone Settings** on each volume:
  - Interior Volume, Interior LPF (low-pass filter frequency)
  - Exterior Volume, Exterior LPF
- Engine automatically interpolates when crossing boundaries
- Can be adjusted dynamically via Blueprint for changing spaces

**Method C -- Raycast Occlusion**:
- Enable built-in **dynamic occlusion** in Sound Attenuation settings
- Engine traces rays from listener to sound source
- Geometry between listener and source triggers occlusion filtering
- Most physically accurate but most expensive (CPU)

**Blueprint Nodes for Occlusion**:
- `LineTraceByChannel` (for custom raycast implementations)
- `Set Audio Volume Enabled`
- `Set Interior Settings` (dynamic ambient zone control)

### 5. Procedural Sound Design: Randomization

**Purpose**: Avoid repetition by randomly selecting from multiple sound variants.

**Sound Cue Pattern**:
- **Random Node**: Core randomization with weight per input
  - Weight = 0: Never selected
  - Higher weight = more frequent selection
  - "No Repeat" option prevents immediate repetition
- Combined with **Delay** (random range) for timing variation
- Combined with **Modulator** for pitch/volume variation on each play

### 6. Procedural Sound Design: Modulation

**Purpose**: Vary audio through pitch and volume modulation without needing many assets.

**Techniques**:
- **Pitch Modulation**: Random range on pitch (e.g., 0.95-1.05 for subtle, 0.7-1.3 for dramatic)
- **Volume Modulation**: Random range on volume per play
- **Sound Cue Modulator Node**: Applies pitch/volume ranges to any input
- Minimal asset count, maximum perceived variety

### 7. Procedural Sound Design: Layered/Component-Based

**Purpose**: Decompose complex sounds into components that recombine at runtime for massive variety.

**Explosion Example**:
```
Category A (Body):     3 variants  \
Category B (Tail):     3 variants   |  3 x 3 x 3 x 3 = 81 combinations
Category C (Debris):   3 variants   |  Add 1 "Crack" variant = 108 total
Category D (Sub-bass): 3 variants  /
```

**Pattern**:
1. Record/design components separately (body, tail, debris, sub-bass, crack)
2. Import as individual mono/stereo assets
3. Build Sound Cue with **Random** nodes per category feeding into **Mixer**
4. Use **Switch** nodes for material-conditional layers (concrete debris vs glass debris)
5. Add slight **randomized delays** between layers for natural offset
6. Distribute components across surround channels via Blueprint

**Math**: `N` categories with `V` variants each = `V^N` total combinations. Adding one more variant to any category multiplies total by ~33%.

### 8. Blueprint Audio Systems (Reusable/Flexible)

**Purpose**: Build reusable, game-responsive audio systems beyond what Sound Cues alone can do.

**Player-Oriented Sound Blueprint**:
- Spawn `AudioComponent` at player-relative locations
- Play one-shots at arbitrary world positions (not just actor locations)
- Control playback parameters from Blueprint (volume, pitch, play/stop)

**Sound Movement via Splines**:
- `Moving_Sounds` Blueprint class
- Attach AudioComponent to actor
- Drive actor position along **Spline** component over time
- Creates spatial movement of sound sources (flyovers, vehicles, conveyor belts)

**Key Blueprint Functions**:
- `SpawnSoundAtLocation` / `SpawnSound2D`
- `PlaySoundAtLocation`
- `SetFloatParameter` / `SetBoolParameter` (on AudioComponent)
- `Audio Component: Play`, `Stop`, `FadeIn`, `FadeOut`
- `Set Sound` (change Sound Cue/Wave at runtime)
- `Get Audio Component` (from Ambient Sound actor)
- `LineTraceByChannel` (for custom occlusion)

---

## Authors: Richard Stevens & Dave Raybould

### Richard Stevens
- **Role**: Senior Lecturer and Programme Leader, Masters in Sound and Music for Interactive Games
- **Institution**: Leeds Beckett University
- **Expertise**: 20+ years teaching game audio, sound design, interactive audio
- **Publications**: "Game Audio Implementation: A Practical Guide Using the Unreal Engine" (Routledge, ISBN 9781138777248), "The Game Audio Tutorial" (Focal Press)
- **Website**: https://gameaudioimplementation.com/

### Dave Raybould
- **Role**: Senior Lecturer
- **Institution**: Leeds Beckett University
- **Expertise**: Games audio, sound design, synthesis
- **Publications**: Co-author of "Game Audio Implementation" with Stevens
- **Notable**: Authored the "Getting Started with Game Audio in Unreal Engine" primer for A Sound Effect

### Joint Work for Epic Games
- **6 courses** developed for Epic's Online Learning portal (18 hours total video content)
- Courses span: Ambient/Procedural Sound, Dynamic Audio, Sound & Space, and more
- Also created independent **"MetaSounds & More"** course series (UE5-focused, 7+ hours)

### Related Courses by Same Authors (Epic Dev Community)
| Course | URL | Focus |
|--------|-----|-------|
| **Dynamic Audio** | [Link](https://dev.epicgames.com/community/learning/courses/Eq/unreal-engine-dynamic-audio) | Audio responding to game events and conditions |
| **Sound and Space** | [Link](https://dev.epicgames.com/community/learning/courses/kN/unreal-engine-sound-and-space) | Spatial audio, ambient zones, occlusion, spline movement |

### Independent Courses (gameaudioimplementation.com)
| Course | Price | Content |
|--------|-------|---------|
| **MetaSounds & More: Foundation** | $230 (50% student discount) | 144-page guide, 25 videos (~4 hrs), UE5 project. No prior UE experience needed. Covers: setup, ambient sounds, attenuation, spatialization, MetaSound editing, randomization, layering, modulation, sequencing, Blueprint interaction, debugging, patches & presets. |
| **MetaSounds & More: Control & Communication** | $230 (50% student discount) | 142-page guide, 20 videos (~3h20m), UE5 project. Builds on Foundation. Covers: MetaSound inputs (Bool, Float, Time, Trigger), Blueprint classes, custom events, direct Blueprint communication, Event Dispatchers, MetaSound outputs for spawning & control. |
| **Bundle (both)** | $447 | 286 pages, 45 videos, 7+ hours total |

---

## UE5 / MetaSounds Equivalents

### What Transfers Directly (No Changes Needed)

| UE4 Concept | UE5 Status | Notes |
|-------------|-----------|-------|
| **Ambient Sound Actor** | Fully supported | Works identically in UE5, supports both Sound Cue and MetaSound sources |
| **Audio Volume** | Replaced by **Audio Gameplay Volume** (UE 5.1+) | More flexible, supports submixes, reverb, attenuation overrides |
| **Sound Attenuation Assets** | Fully supported | Reusable attenuation settings work identically |
| **Blueprint AudioComponent** | Fully supported | SpawnSoundAtLocation, PlaySoundAtLocation, parameter control all work |
| **Spatialization (Panning/Binaural)** | Enhanced | UE5 adds Soundfield rendering, improved HRTF |
| **Blueprint Spawn/Play functions** | Fully supported | Same API, works with both Sound Cues and MetaSounds |

### What MetaSounds Replaces

| UE4 (Sound Cue) | UE5 (MetaSounds) | Why Better |
|-----------------|-------------------|------------|
| **Random Node** | `Random Get (Float/Int)` + `Wave Player` array | Sample-accurate timing, true random distribution |
| **Modulator Node** (pitch/volume) | `Random Get (Float)` feeding `Pitch Shift` / `Gain` | Per-sample control, no audio artifacts at boundaries |
| **Delay Node** | `Trigger Delay` / `Delay` with precise timing | Sample-accurate scheduling |
| **Looping Node** | `Trigger Repeat` / `Wave Player` loop mode | Seamless looping with crossfade options |
| **Switch Node** (material-based) | `Int Switch` / `Enum Router` | More flexible routing, any data type |
| **Concatenator** | `Trigger Sequence` + multiple `Wave Player` | Precise sequencing with gap control |
| **Mixer** (layering) | Multiple `Wave Player` -> `Stereo Mixer` / `Add (Audio)` | Full DSP processing per layer |
| **Sound Cue graph** (overall) | **MetaSound Source** / **MetaSound Patch** | Full DSP graph, extensible API, presets, better performance |

### New Capabilities in UE5 MetaSounds (Not Possible in UE4 Sound Cues)

| Capability | Description |
|-----------|-------------|
| **True Procedural Synthesis** | Oscillators, noise generators, filters -- create sounds from scratch |
| **Sample-Accurate Timing** | Buffer-level control impossible in Sound Cues |
| **Custom DSP Graphs** | Arbitrary signal processing (reverb, distortion, granular, etc.) |
| **MetaSound Presets** | Override parameters without duplicating entire graphs |
| **MetaSound Patches** | Reusable subgraphs (true modular audio) |
| **Float/Int/Bool Inputs from Blueprint** | Direct parameter control via AudioComponent::SetFloatParameter |
| **Trigger System** | Event-driven graph execution (not just continuous) |
| **Graph Variables** | Internal state management within a MetaSound |
| **Soundscape Plugin** (UE 5.1+) | Procedural ambient generation, replaces manual Ambient Sound placement |

### Migration Strategy for Course Patterns

| Course Pattern | UE5 Approach |
|---------------|-------------|
| **Area Loops** (Ambient Sound + attenuation) | Same approach works. Optionally use **Soundscape** plugin for fully procedural ambient. |
| **Source Loops** (positioned mono) | Same Ambient Sound actor. Use MetaSound Source for procedural variation. |
| **One-Shots** (Sound Cue Random+Delay+Loop) | Build as MetaSound Source: `TriggerRepeat` -> `TriggerDelay(random)` -> `Random Get` -> `WavePlayer` |
| **Fake Occlusion** (sound switching) | Same Blueprint approach. MetaSounds can crossfade between variants smoothly. |
| **Ambient Zones** | Use **Audio Gameplay Volumes** (UE 5.1+) for enhanced zone control. |
| **Raycast Occlusion** | Same built-in system. UE5 adds improved geometry-aware occlusion. |
| **Randomization** (weighted random) | MetaSound `Random Get (Int)` with weight arrays. More precise than Sound Cue Random. |
| **Modulation** (pitch/volume) | MetaSound `Random Get (Float)` -> `Pitch Shift` / `Gain`. Per-sample accuracy. |
| **Layered Components** | Multiple `WavePlayer` nodes with `Random Get` selection per layer -> `Stereo Mixer`. Can add real-time DSP per layer. |
| **Blueprint Audio** (spawn/control) | Same Blueprint API. MetaSound parameters exposed via `SetFloatParameter` / `SetTriggerParameter`. |
| **Spline Movement** | Same Blueprint pattern. MetaSounds add Doppler processing for moving sources. |

---

## Blueprint Nodes & Actors Reference (From Course)

### Actors
| Actor | Purpose |
|-------|---------|
| `AmbientSound` | Places sound source in level (wraps AudioComponent) |
| `AudioVolume` | Defines region with ambient zone settings, reverb, occlusion properties |
| `TriggerVolume` | Overlap detection for sound switching |

### Assets
| Asset | Purpose |
|-------|---------|
| `SoundWave` | Imported audio file |
| `SoundCue` | Node-based audio processing graph |
| `SoundAttenuation` | Reusable distance falloff configuration |
| `SoundConcurrency` | Controls max simultaneous instances |

### Sound Cue Nodes (Used in Course)
| Node | Purpose |
|------|---------|
| `Random` | Select randomly from inputs (with weighting) |
| `Delay` | Add variable timing |
| `Looping` | Continuous playback |
| `Modulator` | Pitch/volume randomization ranges |
| `Switch` | Game-state-conditional routing |
| `Concatenator` | Sequential chaining |
| `Mixer` | Simultaneous layering |
| `Attenuation` | Per-node distance falloff |
| `Crossfade by Param` | Parameter-driven blending |

### Blueprint Functions (Used in Course)
| Function | Purpose |
|----------|---------|
| `Play Sound at Location` | One-shot playback at world position |
| `Spawn Sound at Location` | Creates AudioComponent at position (controllable) |
| `Spawn Sound 2D` | Non-spatialized sound playback |
| `Audio Component: Play` | Start playback |
| `Audio Component: Stop` | Stop playback |
| `Audio Component: Fade In/Out` | Smooth volume transitions |
| `Audio Component: Set Float Parameter` | Runtime parameter control |
| `Audio Component: Set Bool Parameter` | Runtime parameter control |
| `Audio Component: Set Sound` | Change source at runtime |
| `Line Trace By Channel` | Raycast for custom occlusion |
| `Get Audio Component` | Extract component from Ambient Sound actor |
| `Set Audio Volume Enabled` | Toggle Audio Volume at runtime |
| `Set Interior Settings` | Dynamic ambient zone control |

---

## Important Considerations

<warnings>
- **UE Version**: Course built for UE 4.23-4.24. Most patterns work in UE5 but Audio Volumes replaced by Audio Gameplay Volumes in 5.1+
- **Sound Cues vs MetaSounds**: Sound Cues still work in UE5 but are no longer the recommended path for new procedural audio. MetaSounds provide sample-accurate control, better performance, and extensibility
- **Project Download**: Available on UE Marketplace (free with course) -- may need version upgrade for UE5
- **No Wwise/FMOD Coverage**: Course uses only native UE audio. Middleware integration requires separate study
- **MetaSounds Builder API**: Experimental since UE 5.4 -- the programmatic equivalent of Sound Cue graph construction
- **Soundscape Plugin**: UE 5.1+ replacement for manual ambient sound placement. Procedurally generates ambient sounds as player moves through world
- **Virtual Voices**: Course covers this UE4 feature; still relevant in UE5 for performance optimization
</warnings>

---

## Resources

<references>
- [Course: Ambient and Procedural Sound Design](https://dev.epicgames.com/community/learning/courses/qR/unreal-engine-ambient-and-procedural-sound-design) - Main course page (Epic Dev Community)
- [Course Forum Discussion](https://forums.unrealengine.com/t/course-ambient-and-procedural-sound-design/610312) - Community discussion thread
- [UE Marketplace: Course Project](https://www.unrealengine.com/marketplace/en-US/product/604-ambient-and-procedural-sound-design) - Downloadable project files
- [Dave Raybould: UE Audio Primer](https://www.asoundeffect.com/unreal-engine-audio-primer/) - Quick start guide (A Sound Effect)
- [Procedural Game Sound Design](https://www.asoundeffect.com/procedural-game-sound-design/) - Layering/component article (A Sound Effect)
- [Game Audio Implementation (Book)](https://www.routledge.com/Game-Audio-Implementation-A-Practical-Guide-Using-the-Unreal-Engine/Stevens-Raybould/p/book/9781138777248) - Comprehensive textbook by same authors
- [gameaudioimplementation.com](https://gameaudioimplementation.com/) - Authors' website with MetaSounds courses
- [MetaSounds & More Courses](https://gameaudioimplementation.com/courses) - UE5 follow-up courses ($230 each, 50% student discount)
- [Course: Dynamic Audio](https://dev.epicgames.com/community/learning/courses/Eq/unreal-engine-dynamic-audio) - Related Stevens/Raybould course
- [Course: Sound and Space](https://dev.epicgames.com/community/learning/courses/kN/unreal-engine-sound-and-space) - Related Stevens/Raybould course
- [MetaSounds Documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-the-next-generation-sound-sources-in-unreal-engine) - Official UE5 MetaSounds docs
- [Audio in UE5](https://dev.epicgames.com/documentation/en-us/unreal-engine/audio-in-unreal-engine-5) - UE5 audio overview
- [Sound Attenuation Docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/sound-attenuation-in-unreal-engine) - Attenuation reference
- [Sound Cue Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/sound-cue-reference-for-unreal-engine) - All Sound Cue nodes
- [Ambient Sound Actor Guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/ambient-sound-actor-user-guide?application_version=4.27) - UE4.27 actor reference
- [Lyra MetaSounds Tutorial](https://dev.epicgames.com/community/learning/tutorials/ry1l/unreal-engine-music-and-environmental-audio-for-project-lyra-using-metasounds) - UE5 MetaSounds in practice
- [Soundscape Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/soundscape-quick-start) - UE5 procedural ambient system
- [Online Audio Learning Resources](https://forums.unrealengine.com/t/online-learning-resources-and-livestreams-for-unreal-audio/151920) - Comprehensive audio resource list
</references>

---

## Metadata

<meta>
research-date: 2026-02-07
confidence: high
engine-version: UE 4.23-4.24 (course), UE 5.x (migration notes)
course-duration: 2 hours 16 minutes
tutorial-count: 15 individual tutorials identified
authors: Richard Stevens, Dave Raybould (Leeds Beckett University)
related-courses: Dynamic Audio, Sound and Space, MetaSounds & More (Foundation + Control & Communication)
project-name: AmbientAndProceduralSound
marketplace-product-id: 604
course-code: qR
</meta>
