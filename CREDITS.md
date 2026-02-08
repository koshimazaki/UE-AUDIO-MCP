# Credits & Attribution

This project's templates and knowledge base draw from the work of these audio professionals and their tutorials. Thank you for sharing your expertise with the community.

## Tutorial Authors

### Craig Owen — YAGER Development, Berlin
**Lead Sound Designer** | Advanced MetaSounds weapon audio series

Originally created as internal training for YAGER's sound design team, then published publicly.

- [MetaSounds Advanced Tutorial - Dynamic Gunshots Over Distance](https://www.youtube.com/watch?v=n5z4L43jMi8)
- Series covers: project setup, folder standardisation, creating variations, layering, Blueprint control, distance crossfades, room reverb switching

**Templates based on this work:**
- `metasounds/weapon_source.json` — Room reverb switch + distance tail crossfade
- `metasounds/weapon_burst.json` — Burst fire with round-robin layers
- `metasounds/crossfade_by_param.json` — 3-layer distance crossfade patch
- `blueprints/weapon_burst_control.json` — Timeline-driven burst fire Blueprint

---

### Matt Spendlove (`msp`)
**Recommended MetaSounds tutorial series** on Epic Dev Community

- [Introduction to MetaSounds](https://dev.epicgames.com/community/learning/recommended-community-tutorial/Kw7l/unreal-engine-metasounds)
- [GitHub: 6070 Intro to MetaSounds](https://github.com/msp/6070-intro-to-metasounds)
- Series covers: MetaSounds Editor, patches/sources/presets hierarchy, procedural vs sample-based, subtractive synthesis, interactive audio

**Templates based on this work:**
- `metasounds/subtractive_synth.json` — Noise + LFO + Filter
- `metasounds/mono_synth.json` — Minimoog-style mono synthesizer
- `blueprints/set_float_parameter.json` — Real-time parameter control pattern

---

### Nick Pfisterer (`pfist`)
**First-person footfalls tutorials** on Epic Dev Community

- [Creating First Person Footfalls with MetaSounds](https://dev.epicgames.com/community/learning/recommended-community-tutorial/WzJ/creating-first-person-footfalls-with-metasounds)
- [Footfalls with MetaSounds Presets for Different Terrain](https://dev.epicgames.com/community/learning/tutorials/vyzR/creating-first-person-footfalls-with-metasounds-presets-for-different-terrain)

**Templates based on this work:**
- `metasounds/footfalls_simple.json` — Random sample + timed repeat footfalls
- `blueprints/footfalls_simple.json` — Blueprint character footfall control

---

### Rich Vreeland (Disasterpeace)
**Lyra music & environmental audio** — canonical UE5 game audio reference

- [Music and Environmental Audio for Project Lyra using MetaSounds](https://dev.epicgames.com/community/learning/tutorials/ry1l/unreal-engine-music-and-environmental-audio-for-project-lyra-using-metasounds)
- [Blog: Epic Games / Lyra](https://disasterpeace.com/blog/epic-games.lyra)
- Covers: 4 reusable systems, music state machine, stingers, vertical layering, crossfading, probability-driven transitions

**Knowledge informed by this work:**
- Ambient/stinger architecture patterns
- State-driven music transition concepts

---

### GorkaGames (`GorkaChampion`)
**Footsteps & dynamic audio tutorials** on Epic Dev Community

- [How to Make Footsteps with MetaSounds in UE5](https://dev.epicgames.com/community/learning/tutorials/9GYn/how-to-make-footsteps-with-metasounds-in-unreal-engine-5)
- [How to Make Dynamic Audio with MetaSounds in UE5](https://dev.epicgames.com/community/learning/tutorials/oE3a/how-to-make-dynamic-audio-with-metasounds-in-unreal-engine-5)

---

### Epic Games — Official Documentation
Templates derived from official UE5 audio tutorials and documentation:

| Template | Source |
|---|---|
| `metasounds/wind.json` | [MetaSounds Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-quick-start) |
| `blueprints/wind_system.json` | [MetaSounds Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-quick-start) |
| `blueprints/bomb_fuse.json` | [MetaSounds Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-quick-start) |
| `blueprints/audio_modulation.json` | [Audio Modulation Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/audio-modulation-quick-start-in-unreal-engine) |
| `blueprints/submix_recording.json` | [Submixes Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-submixes-in-unreal-engine) |
| `blueprints/spectral_analysis.json` | [Submixes Overview](https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-submixes-in-unreal-engine) |
| `blueprints/quartz_beat_sync.json` | [Quartz Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/quartz-quick-start-in-unreal-engine) |
| `blueprints/volume_proxy.json` | [Volume Proxies Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/volume-proxies-quick-start) |
| `blueprints/spatial_attenuation.json` | [Sound Attenuation](https://dev.epicgames.com/documentation/en-us/unreal-engine/sound-attenuation-in-unreal-engine) |
| `blueprints/soundscape_ambient.json` | [Soundscape Quick Start](https://dev.epicgames.com/documentation/en-us/unreal-engine/soundscape-quick-start) |
| `blueprints/metasound_preset_widget.json` | [Creating MetaSound Preset Widgets](https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-metasound-preset-widgets) |

---

### Eric Buchholz (`TechAudioTools`, Epic Games)
**Technical Audio Designer** | TechAudioTools Content — MetaSounds production tools, SFX Generator, Preset Widgets

- [TechAudioTools Content Documentation](https://dev.epicgames.com/community/learning/tutorials/ZMpq/unreal-engine-tech-audio-tools-content-documentation)
- [TechAudioTools Content on Fab](https://www.fab.com/listings/d44cbd49-7691-4f82-abdb-6428c78508f6)
- Covers: SFX Generator synth architecture (Generator→Spectral→Filter→Amp→Effects), Preset Widget system with hierarchical randomization, MetaSound Builder initialization, Output Watch delegates, Audio Bus analysis, Wave Writer recording, custom Editor User Widgets (Float Knob, Integer Slider, Boolean Toggle, Randomizer with lock/scope)
- Also: MetaSound Input Migrator, MetaSound Metadata Editor
- UE 5.6+ compatible, requires TechAudioTools + UMG Viewmodel engine plugins

**Templates based on this work:**
- `metasounds/sfx_generator.json` — Full synth topology: switchable generator → spectral effects → SVF filter → ADSR amplifier → parallel send effects
- `blueprints/sfx_generator_widget.json` — Preset Widget controller with Builder init, ViewModel binding, Output Watch, randomization
- `blueprints/metasound_preset_widget.json` — Preset Widget creation pattern

---

### Chris Payne (`ChrisPayne123`)
**Senior Game Audio Leader** | MetaSounds Sound Pads — Blueprint ↔ MetaSounds communication with visual feedback

- [Metasound Sound Pads](https://dev.epicgames.com/community/learning/tutorials/opvv/unreal-engine-metasound-sound-pads)
- Covers: Dynamic sound pad system, audio file playback + synthesis, Blueprint-driven visual feedback (dynamic materials), musical scale structures in MetaSounds, pitch control
- UE 5.6 compatible

**Templates based on this work:**
- `metasounds/sound_pad.json` — Dual-source synth + sample player with scale array lookup
- `blueprints/sound_pad_control.json` — Hit-driven sound pad with enum switching, cooldown, material feedback

**Knowledge informed by this work:**
- Blueprint ↔ MetaSounds parameter communication patterns
- Audio-reactive material feedback
- Musical scale implementation in MetaSounds

---

### Richard Stevens & Dave Raybould (Leeds Beckett University)
**Co-authors of "Game Audio Implementation" (Routledge)** | 3 Epic Learning Paths, 41+ tutorials, 18+ hours of content

- [Ambient and Procedural Sound Design](https://dev.epicgames.com/community/learning/courses/qR/unreal-engine-ambient-and-procedural-sound-design) (UE 4.23, 15 tutorials, 2h16m)
- [Quartz Music System](https://dev.epicgames.com/community/learning/courses/XAw/unreal-engine-quartz-music-system) (UE 4.27, 14 tutorials) — Richard Stevens
- [Audio-Driven Gameplay](https://dev.epicgames.com/community/learning/paths/60/unreal-engine-audio-driven-gameplay) (UE 4.26, 12+ tutorials) — Richard Stevens
- Companion projects free on Fab: [Quartz](https://www.fab.com/listings/2f0d06ac-9f59-40dc-9a4c-b18006a3091c), [Audio-Driven Gameplay](https://www.unrealengine.com/marketplace/en-US/product/audio-driven-gameplay)
- Also: [MetaSounds & More](https://gameaudioimplementation.com/courses) — UE5 courses (7+ hours, 286 pages)

**Templates based on this work:**
- `blueprints/ambient_spline_movement.json` — Sound movement along Spline path with Timeline
- `blueprints/ambient_height_wind.json` — Height-based wind volume with creak threshold
- `blueprints/ambient_weighted_trigger.json` — Probability-gated ambient one-shots
- `blueprints/player_oriented_sound.json` — Player-relative directional sound spawning
- `blueprints/audio_visualiser.json` — Attenuation debug visualiser (LPF/HPF/occlusion)
- `blueprints/submix_spectral_fireflies.json` — Submix FFT → particle color/size feedback
- `blueprints/audio_input_butterflies.json` — Microphone input → creature spawning
- `blueprints/physics_audio.json` — Physics rolling/impact/scraping → audio
- `blueprints/quartz_vertical_music.json` — Quartz-synchronised vertical music layers
- `blueprints/triggered_music_stinger.json` — One-shot overlap-triggered stinger
- `blueprints/quartz_music_playlist.json` — Shuffle-based music playlist with OnAudioFinished chaining
- `blueprints/quartz_multi_clock.json` — Dual Quartz clocks with different time signatures (4/4 + 5/4)
- `blueprints/quartz_transitional_states.json` — Full bidirectional music state machine (Amb/Low/Mid/High) with harmonic stingers
- `blueprints/synesthesia_stems.json` — Synesthesia NRT per-stem analysis + particle visualisation

**Knowledge informed by this work:**
- Sound Class hierarchy (Master → Area_Loops + Source_Loops + One_Shots + Footsteps + Foley + Night_Day + Dialogue)
- 3 occlusion methods: fake switching, Ambient Zones, raycasting
- Component-based sound decomposition (4 categories × 3 variants = 81 combinations)
- Audio analysis patterns: Envelope Following, Spectral Analysis, Audio Capture (microphone), Synesthesia NRT
- Quartz music system: vertical layering, bar-quantized transitions, metronome callbacks, multi-clock coordination
- Physics audio: angular velocity → rolling, NormalImpulse → impacts, linear velocity → scraping
- Multi-clock patterns: separate clocks for different time signatures, StartOtherClock for sync, beat-level queueing
- Transitional music: bidirectional state machine with cover triggers, harmonic stinger selection by bar position
- Synesthesia NRT: ConstantQ (spectral), Onset (transients), Loudness (envelope) — zero runtime cost pre-computed analysis

---

### Mariia Sakun — Sound Designer
**Technical Sound Design** | Darkflow (UE5 + MetaSounds), Mortal Void (UE5 + Wwise)

- [Portfolio & Projects](https://www.mariia-sakun-sound.com/projects)
- Darkflow: Hoverboard system (speed/height/terrain-reactive engine layers + turbo), modular weapon systems (randomized layers + dynamic attenuation)
- Mortal Void: Weapon design + environmental sound (UE5 + Wwise)

**Templates informed by this work:**
- `metasounds/vehicle_engine.json` — Multi-layer engine with Trigger Sequence → Random Get → Wave Player + Compressor (based on Darkflow hoverboard architecture)
- `blueprints/weapon_burst_control.json` — Modular weapon fire patterns

---

### Other Notable References

- **Dan Reynolds** (Epic Games, Senior Technical Audio Designer) — Rivian motor simulation, MetaSounds architecture guidance
- **Samuel Bass** (Epic Games Evangelist) — [Composing MetaSounds](https://dev.epicgames.com/community/learning/tutorials/PWM7/unreal-engine-composing-metasounds) for Brick Breakers
- **Nazzal Naseer** — [Understanding MetaSounds](https://dev.epicgames.com/community/learning/tutorials/9Jja/unreal-engine-understanding-metasounds)
- **Nemisindo** — [Adaptive Footsteps Plugin](https://nemisindo.com/documentation/unreal-footsteps-metasounds) (procedural, 7 surfaces, 5 shoe types)
- **The Audio Programmer** — [FM Synthesizer Tutorial](https://www.theaudioprogrammer.com/content/unreal-engine-metasounds-tutorial-01-creating-your-first-metasound-fm-synthesizer)

## Original Templates

These templates were designed by this project based on common game audio patterns, not derived from specific tutorials:

`gunshot`, `footsteps`, `ambient`, `spatial`, `ui_sound`, `weather`, `snare`, `macro_sequence`, `preset_morph`, `sample_player`, `random_playback`, `ambient_stingers`
