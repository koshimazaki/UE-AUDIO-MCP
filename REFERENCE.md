# Reference

Detailed listing of tools, templates, knowledge base, C++ components, and workflows.

---

## MCP Tools (63)

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

---

## Knowledge Base (643 entries)

All data engine-verified or hand-curated. TF-IDF semantic search for MetaSounds nodes, SQL keyword matching for Blueprint functions.

| Data | Entries | Source |
|------|---------|--------|
| MetaSounds nodes | 178 (23 categories, 128 class_name mappings) | Engine registry sync + Epic docs |
| Cross-system pin mappings | 130 | BP <-> MetaSounds <-> Wwise wiring |
| Builder API functions | 81 | UE 5.7 MetaSounds Builder API |
| WAAPI functions | 66 | Audiokinetic SDK reference |
| Blueprint audio functions | 55 | GameplayStatics, AudioComponent, Quartz |
| Blueprint nodes (curated) | 55 | Engine-synced audio functions catalogue |
| Audio console commands | 20 | UE5 audio debugging |
| Wwise types & properties | 19 | Types, categories, default paths |
| Tutorial workflows | 17 | Step-by-step MetaSounds build guides |
| Attenuation subsystems | 8 | Distance models and parameters |
| Audio patterns | 6 | Game audio design patterns |
| UE game examples | 5 | Lyra reference implementations |
| Spatialization methods | 3 | HRTF, ITD, panning |

Engine sync scripts fetch live data from the running UE5 editor (842 MetaSounds nodes, 979 audio Blueprint functions from 165 classes).

---

## UE5 C++ Plugin (35 commands)

Editor-only plugin providing TCP server for MetaSounds Builder API and Blueprint graph access:

- **Wire protocol**: 4-byte length-prefix + UTF-8 JSON on port 9877
- **Node registry**: 70 display-name -> class-name mappings (65 standard + 5 SID) + passthrough for `::` names
- **Blueprint builder**: `FAudioMCPBlueprintManager` -- add nodes, connect pins, compile, audio function allowlist
- **Thread safety**: FRunnable TCP -> AsyncTask(GameThread) dispatch
- **Security**: localhost only (127.0.0.1), message size validation

### Editor Menu ("Audio MCP" in menu bar)

Scan Project Audio | Scan Selected Blueprint | Export MetaSounds | Open Results Folder | Server Status

---

## Orchestration (11 patterns)

`build_audio_system("pattern_name")` generates all 3 layers with cross-layer wiring:

```
gunshot, footsteps, ambient, spatial, ui_sound, weather,
vehicle_engine, sfx_generator, preset_morph, macro_sequence, sid_synth
```

`build_aaa_project("MyGame")` generates complete game audio infrastructure (6 categories, bus hierarchy, work units, events, MetaSounds sources, Blueprint wiring).

---

## Templates (73)

33 MetaSounds + 34 Blueprint + 6 Wwise.
All 33 MS templates pass 7-stage validation. 12 derived from shipped games (Lyra, StackOBot).

---

## MetaSounds (33)

### Sources (26)

| Template | Nodes | Source |
|----------|-------|--------|
| `ambient` | 3 | -- |
| `ambient_stingers` | 8 | Epic Community |
| `footfalls_simple` | 5 | Nick Pfisterer |
| `footsteps` | 5 | -- |
| `gunshot` | 5 | -- |
| `looped_sound` | 6 | **StackOBot** -- start/loop/end |
| `macro_sequence` | 10 | -- |
| `mono_array_player` | 4 | **StackOBot** -- random one-shot |
| `mono_synth` | 10 | Matt Spendlove |
| `preset_morph` | 6 | -- |
| `random_playback` | 5 | Epic Community |
| `sample_player` | 1 | -- |
| `sfx_generator` | 26 | Eric Buchholz |
| `sid_bass` | 5 | Koshi Mazaki |
| `sid_chip_tune` | 2 | Koshi Mazaki |
| `sid_lead` | 8 | Koshi Mazaki |
| `snare` | 6 | -- |
| `sound_pad` | 10 | Dr Chris Payne |
| `spatial` | 2 | -- |
| `subtractive_synth` | 4 | Matt Spendlove |
| `ui_sound` | 3 | -- |
| `vehicle_engine` | 12 | Chris Payne |
| `weapon_burst` | 8 | Craig Owen (YAGER) |
| `weapon_source` | 5 | Craig Owen (YAGER) |
| `weather` | 5 | -- |
| `wind` | 7 | Epic Games |

### Patches (7)

| Template | Nodes | Source |
|----------|-------|--------|
| `ambient_element` | 5 | **Lyra** -- ambient voice with random timing |
| `crossfade_by_param` | 27 | Craig Owen (YAGER) |
| `random_eq` | 12 | **Lyra** -- 4-band cascaded random EQ |
| `stereo_balance` | 4 | **Lyra** -- L/R panner balance |
| `stereo_eq_delay` | 6 | **StackOBot** -- HPF+LPF+delay chain |
| `stereo_high_shelf` | 2 | **Lyra** -- matched L/R high-shelf |
| `whizby` | 8 | **Lyra** -- Doppler bullet whizby |

---

## Blueprints (34)

### Combat & Events
`anim_notify_audio` (Lyra) | `gameplay_cue_audio` (Lyra) | `weapon_burst_control` | `weapon_fire_spatial` (Lyra) | `bomb_fuse` | `physics_audio`

### Movement & Spatial
`footfalls_simple` | `player_oriented_sound` | `spatial_attenuation` | `volume_proxy`

### Ambient & Environment
`ambient_height_wind` | `ambient_spline_movement` | `ambient_stingers` | `ambient_weighted_trigger` | `soundscape_ambient` | `wind_system`

### Music & Quartz
`quartz_beat_sync` | `quartz_multi_clock` | `quartz_music_playlist` | `quartz_transitional_states` | `quartz_vertical_music` | `triggered_music_stinger`

### Audio Analysis & Visualisation
`audio_visualiser` | `spectral_analysis` | `submix_spectral_fireflies` | `synesthesia_stems`

### UI & Widgets
`audio_modulation` | `metasound_preset_widget` | `sfx_generator_widget` | `ui_button_sound` (Lyra)

### Misc
`audio_input_butterflies` | `set_float_parameter` | `sound_pad_control` | `submix_recording`

---

## Wwise (6)

`ambient` | `footsteps` | `gunshot` | `ui_sound` | `vehicle_engine` | `weather`

---

## C++ Custom Nodes (5)

ReSID SIDKIT Edition -- MOS 6581/8580 SID chip as MetaSounds nodes:
`SID Oscillator` | `SID Envelope` | `SID Filter` | `SID Voice` | `SID Chip`

---

## C++ Audio Patterns (from Lyra)

Reference implementations in `research/lyra_audio_patterns.md`.

### Context Effects Pipeline
Tag-based audio dispatch: AnimNotify -> line trace -> surface tag -> library lookup -> SpawnSoundAttached.
```
AnimNotify fires → ILyraContextEffectsInterface::AnimMotionEffect()
  → ULyraContextEffectComponent aggregates context tags (defaults + surface)
    → ULyraContextEffectsSubsystem::SpawnContextEffects()
      → ULyraContextEffectsLibrary::GetEffects(tag, contexts) → match
        → UGameplayStatics::SpawnSoundAttached() per sound
```

**Key classes**: `UAnimNotify_LyraContextEffects`, `ULyraContextEffectComponent`, `ULyraContextEffectsSubsystem`, `ULyraContextEffectsLibrary`

### Control Bus Mixing
HDR/LDR audio chain switching + per-bus volume control via `UAudioModulationStatics`:
```
BeginPlay → ActivateBusMix(DefaultBaseMix) → ActivateBusMix(UserMix)
         → SetSubmixEffectChainOverride(HDR or LDR chain)
Settings  → CreateBusMixStage(bus, volume) → UpdateMix(UserMix, stages)
Loading   → ActivateBusMix(LoadingScreenMix) → DeactivateBusMix on complete
```

**Key classes**: `ULyraAudioMixEffectsSubsystem`, `ULyraAudioSettings`

### Design Patterns
1. **Tag-based dispatch** -- GameplayTags for effect type + context, no hardcoded enums
2. **Interface decoupling** -- AnimNotify uses `ILyraContextEffectsInterface`, never knows the component
3. **World Subsystem registry** -- actor-to-library mapping in subsystem
4. **Soft references** -- libraries, bus mixes, control buses all `TSoftObjectPtr`
5. **Data-driven** -- new surfaces/effects/creatures = data assets only, no code changes
6. **Dual output** -- same library entry produces Sound + Niagara (audio+VFX from one trigger)

---

## Workflows

### MCP Tool Chain (Python -> TCP -> UE5)
```
ms_from_template("footsteps")     → generates Builder API commands
ms_create_source("MS_Footsteps")  → creates asset in UE5
ms_add_node / ms_connect / ms_set_default → builds the graph
ms_audition()                     → preview in editor
```

### C++ Plugin Direct (TCP:9877)
```json
{"command": "create_metasound", "params": {"name": "MS_Footsteps", "type": "Source"}}
{"command": "add_node", "params": {"node_class": "UE::Wave Player::Mono", "name": "wp"}}
{"command": "connect_nodes", "params": {"from": "wp", "pin": "Out Mono", "to": "__output__"}}
{"command": "compile_metasound"}
```

### Blueprint Builder (TCP:9877)
```json
{"command": "create_blueprint", "params": {"name": "BP_AudioCtrl", "parent": "Actor"}}
{"command": "add_blueprint_node", "params": {"function": "SpawnSoundAtLocation"}}
{"command": "connect_blueprint_pins", "params": {"from": "event", "to": "spawn"}}
{"command": "compile_blueprint"}
```
