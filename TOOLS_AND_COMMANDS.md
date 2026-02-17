# Tools & Commands Reference

69 MCP tools + 41 C++ TCP commands for game audio pipeline automation.

---

## MCP Tools (69)

### Wwise (20 tools)

| Tool | What It Does |
|------|-------------|
| `wwise_connect` | Connect to Wwise Authoring App (WAAPI ws://127.0.0.1:8080) |
| `wwise_query` | Query Wwise objects by path or ID |
| `wwise_save` | Save Wwise project |
| `wwise_raw` | Send raw WAAPI call |
| `wwise_info` | Get Wwise version and project info |
| `wwise_create_object` | Create object (19 types: Sound, Event, Bus, etc.) |
| `wwise_set_property` | Set property on any Wwise object |
| `wwise_import_audio` | Import audio files into Wwise hierarchy |
| `wwise_move_object` | Move/reparent objects in hierarchy |
| `wwise_create_event` | Create Event with play action |
| `wwise_create_rtpc` | Create Game Parameter with curve binding |
| `wwise_assign_switch` | Assign Switch/State to container |
| `wwise_set_attenuation` | Configure distance attenuation |
| `wwise_transport` | Play/stop/pause preview transport |
| `wwise_generate_soundbanks` | Generate SoundBanks |
| `wwise_from_template` | One-call gunshot/footsteps/ambient/UI/weather |
| `wwise_bulk_setup` | Batch hierarchy creation |
| `wwise_bus_hierarchy` | Create bus routing structure |
| `wwise_state_system` | Create state groups + states |
| `build_aaa_project` | Full AAA game audio infrastructure |

### MetaSounds (23 tools)

| Tool | What It Does |
|------|-------------|
| `ms_search_nodes` | TF-IDF semantic search across 195 nodes |
| `ms_list_categories` | List all 23 node categories |
| `ms_node_info` | Get pins, types, defaults for a node |
| `ms_list_nodes` | List all nodes in a category |
| `ms_validate_graph` | 7-stage graph validation |
| `ms_to_builder_commands` | Convert graph spec to Builder API calls |
| `ms_from_template` | Generate graph from 33 parameterised templates |
| `ms_create_source` | Create MetaSound Source asset in UE5 |
| `ms_add_node` | Add node to active builder graph |
| `ms_connect` | Connect two pins |
| `ms_set_default` | Set default value on input pin |
| `ms_add_graph_input` | Add graph-level input |
| `ms_add_graph_output` | Add graph-level output |
| `ms_add_interface` | Add MetaSound interface |
| `ms_build_to_asset` | Save builder graph as .uasset |
| `ms_audition` | Preview graph in editor |
| `ms_stop_audition` | Stop preview playback |
| `ms_add_variable` | Add graph variable (get/set/delayed) |
| `ms_convert_to_preset` | Convert Source to Preset |
| `ms_convert_from_preset` | Convert Preset back to Source |
| `ms_preset_morph` | Crossfade between preset parameter sets |
| `ms_macro_trigger` | Trigger sequence of parameter changes |
| `ms_sync_from_engine` | Sync 842 engine nodes to knowledge DB |

### Blueprint (15 tools)

| Tool | What It Does |
|------|-------------|
| `bp_search` | Search Blueprint audio function catalogue |
| `bp_list_categories` | List Blueprint function categories |
| `bp_node_info` | Get function signature, pins, params |
| `bp_scan_blueprint` | Deep-scan a BP for audio-relevant nodes |
| `bp_list_assets` | Query Asset Registry by class/path |
| `bp_call_function` | Execute allowlisted audio function |
| `bp_open_blueprint` | Open BP for editing (auto-registers all nodes) |
| `bp_add_bp_node` | Add node (CallFunction/CustomEvent/VariableGet/Set) |
| `bp_connect_bp_pins` | Connect two BP node pins |
| `bp_set_bp_pin` | Set default value on BP input pin |
| `bp_compile_blueprint` | Compile active Blueprint |
| `bp_register_existing` | Register existing node by GUID for wiring |
| `bp_list_node_pins` | List all pins on a registered node |
| `bp_wire_audio_param` | High-level: wire audio parameter end-to-end |
| `bp_sync_from_engine` | Sync 979 engine functions to knowledge DB |

### World Setup (6 tools) -- NEW

| Tool | What It Does |
|------|-------------|
| `place_anim_notify` | Place AnimNotify_PlaySound on animation at exact frame time |
| `spawn_audio_emitter` | Spawn AmbientSound actor at world location (spatial audio) |
| `import_sound_file` | Import .wav/.ogg from disk into Content/ |
| `set_physical_surface` | Set surface type on Physical Material (creates if needed) |
| `place_audio_volume` | Place AudioVolume with reverb settings |
| `spawn_blueprint_actor` | Spawn BP actor into level (see it while you wire it) |

### Connection & Orchestration (5 tools)

| Tool | What It Does |
|------|-------------|
| `ue5_connect` | Connect to UE5 plugin (TCP:9877) |
| `ue5_status` | Check plugin connection status |
| `ue5_info` | Get plugin version and command list |
| `build_audio_system` | Generate complete 3-layer audio system from pattern name |
| `build_aaa_project` | Generate full AAA game audio infrastructure |

---

## C++ TCP Commands (41)

Wire protocol: 4-byte length-prefix + UTF-8 JSON on port 9877. All commands execute on the game thread.

### MetaSounds Builder (18 commands)

| # | Command | Params |
|---|---------|--------|
| 1 | `ping` | -- |
| 2 | `create_builder` | name, type(Source/Patch) |
| 3 | `add_interface` | interface_name |
| 4 | `add_graph_input` | name, type, default |
| 5 | `add_graph_output` | name, type |
| 6 | `add_node` | node_class, name |
| 7 | `set_default` | node, pin, value |
| 8 | `connect` | from_node, from_pin, to_node, to_pin |
| 9 | `build_to_asset` | asset_path |
| 10 | `audition` | -- |
| 11 | `stop_audition` | -- |
| 12 | `open_in_editor` | asset_path |
| 13 | `add_graph_variable` | name, type, default |
| 14 | `add_variable_get_node` | variable_name |
| 15 | `add_variable_set_node` | variable_name |
| 16 | `convert_to_preset` | source_path |
| 17 | `convert_from_preset` | preset_path |
| 18 | `set_live_updates` | enabled(bool) |

### Query & Export (10 commands)

| # | Command | Params |
|---|---------|--------|
| 19 | `get_graph_input_names` | -- |
| 20 | `list_node_classes` | include_pins, include_metadata, limit, page |
| 21 | `list_metasound_nodes` | (alias for list_node_classes) |
| 22 | `get_node_locations` | asset_path |
| 23 | `scan_blueprint` | asset_path |
| 24 | `list_assets` | class_name, path, recursive |
| 25 | `export_metasound` | asset_path |
| 26 | `export_audio_blueprint` | asset_path |
| 27 | `list_blueprint_functions` | filter, class_filter, audio_only, limit, include_pins |
| 28 | `call_function` | function, args |

### Blueprint Builder (7 commands)

| # | Command | Params |
|---|---------|--------|
| 29 | `bp_open_blueprint` | asset_path (auto-registers all nodes) |
| 30 | `bp_add_node` | id, node_kind, function_name/event_name/variable_name, position |
| 31 | `bp_connect_pins` | from_node, from_pin, to_node, to_pin |
| 32 | `bp_set_pin_default` | node_id, pin_name, value |
| 33 | `bp_compile` | -- |
| 34 | `bp_register_existing_node` | id, node_guid |
| 35 | `bp_list_pins` | node_id |

### World Setup (6 commands) -- NEW

| # | Command | Params |
|---|---------|--------|
| 36 | `duplicate_asset` | source_path, dest_path |
| 37 | `place_anim_notify` | animation_path, time, sound, notify_name |
| 38 | `spawn_audio_emitter` | sound, location[x,y,z], name, auto_play |
| 39 | `import_sound_file` | file_path, dest_folder |
| 40 | `set_physical_surface` | material_path, surface_type |
| 41 | `place_audio_volume` | location[x,y,z], extent[x,y,z], name, reverb_effect, priority |
| -- | `spawn_blueprint_actor` | blueprint_path, location[x,y,z], rotation[p,y,r], label |

Note: `spawn_blueprint_actor` shares slot with the world commands (registered as #41 alongside `place_audio_volume`).

---

## Sound Designer Workflow

The MCP lets sound designers focus on creative work without learning engine plumbing.

### Quick Start: Wire Sound to Character

```
1. spawn_blueprint_actor("/Game/creature/BP_Creature", location=[0,0,100])
   → creature appears in viewport

2. bp_open_blueprint("/Game/creature/BP_Creature")
   → see all existing nodes (auto-registered)

3. bp_add_bp_node("play_step", "CallFunction", function_name="PlaySound2D")
   → PlaySound2D node appears in graph

4. bp_connect_bp_pins("event_beginplay", "then", "play_step", "execute")
   → wire visible in editor

5. bp_compile_blueprint()
   → hit Play, hear the sound
```

### Animation-Synced Footsteps

```
1. place_anim_notify("/Game/Anims/MM_Walk_Fwd", time=0.25, sound="/Game/Audio/Foley/Step_L")
2. place_anim_notify("/Game/Anims/MM_Walk_Fwd", time=0.65, sound="/Game/Audio/Foley/Step_R")
   → footstep sounds fire at exact foot-contact frames
```

### Material-Dependent Sounds

```
1. set_physical_surface("/Game/Materials/PM_Grass", surface_type="Grass")
2. set_physical_surface("/Game/Materials/PM_Metal", surface_type="Metal")
   → floor tagged as Grass, box tagged as Metal
   → raycast detects surface → triggers appropriate sound
```

### Spatial Audio: Ambient Sound at Location

```
1. spawn_audio_emitter("/Game/Audio/Ambient/Campfire", location=[500, 200, 0], name="CampfireSound")
   → persistent sound source, gets louder as player approaches
```

### Audio Zones with Reverb

```
1. place_audio_volume(location=[1000, 2000, 0], extent=[500, 500, 300],
                      name="CaveZone", reverb_effect="/Game/Audio/Reverb/Cave", priority=1.0)
   → enter the volume, reverb activates
```

### Import Sounds from Disk

```
1. import_sound_file("/path/to/explosion.wav", dest_folder="/Game/Audio/SFX")
   → asset appears in Content Browser, ready to use
```

---

## Templates (73)

33 MetaSounds + 34 Blueprint + 6 Wwise. All validated.

### MetaSounds Sources (26)

ambient, ambient_stingers, footfalls_simple, footsteps, gunshot, looped_sound, macro_sequence, mono_array_player, mono_synth, preset_morph, random_playback, sample_player, sfx_generator, sid_bass, sid_chip_tune, sid_lead, snare, sound_pad, spatial, subtractive_synth, ui_sound, vehicle_engine, weapon_burst, weapon_source, weather, wind

### MetaSounds Patches (7)

ambient_element (Lyra), crossfade_by_param, random_eq (Lyra), stereo_balance (Lyra), stereo_eq_delay (StackOBot), stereo_high_shelf (Lyra), whizby (Lyra)

### Blueprints (34)

Combat: anim_notify_audio, gameplay_cue_audio, weapon_burst_control, weapon_fire_spatial, bomb_fuse, physics_audio
Movement: footfalls_simple, player_oriented_sound, spatial_attenuation, volume_proxy
Ambient: ambient_height_wind, ambient_spline_movement, ambient_stingers, ambient_weighted_trigger, soundscape_ambient, wind_system
Music: quartz_beat_sync, quartz_multi_clock, quartz_music_playlist, quartz_transitional_states, quartz_vertical_music, triggered_music_stinger
Analysis: audio_visualiser, spectral_analysis, submix_spectral_fireflies, synesthesia_stems
UI: audio_modulation, metasound_preset_widget, sfx_generator_widget, ui_button_sound
Misc: audio_input_butterflies, set_float_parameter, sound_pad_control, submix_recording

### Wwise (6)

ambient, footsteps, gunshot, ui_sound, vehicle_engine, weather

---

## Knowledge Base (20 tables, 1053 rows)

| Table | Rows | Content |
|-------|------|---------|
| metasound_nodes | 195 | Node definitions with pins, types, class_names |
| node_aliases | 347 | Display/class/short name → canonical lookup |
| graph_node_usage | -- | Per-graph node usage (populated on project scan) |
| bp_audio_triggers | -- | Audio trigger functions from BP scans |
| blueprint_nodes_scraped | 55 | Curated audio Blueprint functions |
| project_audio_assets | -- | Scanned project assets with source field |
| project_blueprints | -- | Scanned project Blueprint metadata |
| ... | ... | 20 tables total (see db.py for full schema) |

Engine sync: 842 MetaSounds nodes, 979 audio Blueprint functions from 165 classes.

---

## C++ Custom Nodes (5)

ReSID SIDKIT Edition -- MOS 6581/8580 SID chip as MetaSounds nodes:

`SID Oscillator` | `SID Envelope` | `SID Filter` | `SID Voice` | `SID Chip`

---

## Orchestration Patterns (11)

`build_audio_system("pattern_name")` generates all 3 layers:

gunshot, footsteps, ambient, spatial, ui_sound, weather, vehicle_engine, sfx_generator, preset_morph, macro_sequence, sid_synth

`build_aaa_project("MyGame")` generates complete infrastructure (6 categories, bus hierarchy, work units, events, MetaSounds sources, Blueprint wiring).

---

## File Structure

```
src/ue_audio_mcp/
  server.py                    FastMCP entry + lifespan
  connection.py                WaapiConnection singleton
  ue5_connection.py            UE5PluginConnection singleton
  tools/
    wwise_*.py                 20 Wwise tools
    ms_*.py                    23 MetaSounds tools
    bp_*.py                    15 Blueprint tools
    world_setup.py             6 World Setup tools
    systems.py                 2 Orchestration tools
    utils.py                   _ok() / _error() helpers
  knowledge/
    db.py                      SQLite DB (20 tables, v2 schema)
    metasound_nodes.py         195 nodes, 145 class_name mappings
    node_schema.py             MSPin/MSNode TypedDicts
    embeddings.py              TF-IDF search
  templates/
    metasounds/                33 MS templates (JSON)
    blueprints/                34 BP templates (JSON)
    wwise/                     6 Wwise templates (JSON)

ue5_plugin/UEAudioMCP/
  Source/UEAudioMCP/
    Public/
      AudioMCPTypes.h          Wire protocol, helpers
      AudioMCPBuilderManager.h MetaSounds builder state
      AudioMCPBlueprintManager.h Blueprint builder state
      AudioMCPNodeRegistry.h   70 display→class name mappings
      Commands/
        IAudioMCPCommand.h     Command interface
        BuilderCommands.h      MS builder commands
        NodeCommands.h         MS node commands
        QueryCommands.h        Query/export/sync commands
        BPBuilderCommands.h    Blueprint builder commands
        WorldCommands.h        World setup commands (NEW)
    Private/
      UEAudioMCPModule.cpp     Plugin startup, command registration
      AudioMCPTcpServer.cpp    TCP server (FRunnable)
      AudioMCPCommandDispatcher.cpp Command routing
      Commands/*.cpp           All command implementations

tests/                         461 tests across 21 files
scripts/                       Build, sync, verify, export scripts
```
