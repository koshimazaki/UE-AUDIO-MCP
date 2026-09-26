---
name: ue5-audio-mcp
description: UE5 Audio MCP plugin TCP control. Use when sending commands to the Unreal Editor plugin on port 9877 — building MetaSounds graphs, editing Blueprint graphs, placing audio emitters, volumes and anim notifies, staging actors and cameras, scanning Blueprints, listing or exporting assets, or debugging the plugin connection.
allowed-tools: Bash, Read, Grep, Glob
argument-hint: "[command-or-task]"
---

# UE Audio MCP Plugin — TCP Control

Drive the C++ TCP server inside Unreal Editor. Each command is flat JSON (`action` plus its params at the top level), framed with a 4-byte big-endian length prefix, on `127.0.0.1:9877`. Commands run on the game thread.

## Connection

```python
# Python SDK
from ue_audio_mcp.ue5_connection import get_ue5_connection
conn = get_ue5_connection()
resp = conn.send_command({"action": "ping"})

# Raw TCP
python3 -c "
import socket, struct, json
s = socket.socket(); s.settimeout(5); s.connect(('127.0.0.1', 9877))
p = json.dumps({'action':'ping'}).encode()
s.sendall(struct.pack('>I', len(p)) + p)
r = s.recv(4); l = struct.unpack('>I', r)[0]; print(json.loads(s.recv(l)))
"
```

## Commands

The plugin registers 48 commands. Params marked `?` are optional, with defaults in parentheses; every response also carries `status` (and `message` on errors). The source of truth is the `RegisterCommand` calls in `ue5_plugin/UEAudioMCP/Source/UEAudioMCP/Private/UEAudioMCPModule.cpp`; each command reads its params in `Private/Commands/*.cpp`.

### System
| Command | Params | Returns |
|---------|--------|---------|
| `ping` | — | engine, version, project, features |

### Builder lifecycle
| Command | Params | Returns |
|---------|--------|---------|
| `create_builder` | asset_type (Source/Patch/Preset), name | asset_type, name |
| `add_interface` | interface | — |

### Graph I/O
| Command | Params | Returns |
|---------|--------|---------|
| `add_graph_input` | name, type, default? | name, type |
| `add_graph_output` | name, type | name, type |

### Nodes
| Command | Params | Returns |
|---------|--------|---------|
| `add_node` | id, node_type, position? [x,y] | id, node_type |
| `set_default` | node_id, input, value | node_id, input |
| `connect` | from_node, from_pin, to_node, to_pin | from_node, from_pin, to_node, to_pin |

### Build, audition & editor
| Command | Params | Returns |
|---------|--------|---------|
| `build_to_asset` | name, path | name, path |
| `audition` | name? | — |
| `stop_audition` | — | — |
| `open_in_editor` | — | — |

### Variables (UE 5.7+)
| Command | Params | Returns |
|---------|--------|---------|
| `add_graph_variable` | name, type, default? | name, type |
| `add_variable_get_node` | id, variable_name, delayed? | id, variable_name, delayed |
| `add_variable_set_node` | id, variable_name | id, variable_name |

### Presets
| Command | Params | Returns |
|---------|--------|---------|
| `convert_to_preset` | referenced_asset | referenced_asset |
| `convert_from_preset` | — | — |

### Query & export
| Command | Params | Returns |
|---------|--------|---------|
| `get_graph_input_names` | — | names, count |
| `set_live_updates` | enabled | enabled |
| `list_node_classes` | filter?, limit? (200), offset?, include_pins?, include_metadata? | nodes, total, shown, offset |
| `list_metasound_nodes` | same as list_node_classes | nodes, total, shown, offset |
| `get_node_locations` | asset_path | asset_type, interfaces, nodes, edges, asset_path |
| `export_metasound` | asset_path | asset_path, asset_type, is_preset, interfaces, graph_inputs, graph_outputs, variables, nodes, edges |

### Blueprint & assets
| Command | Params | Returns |
|---------|--------|---------|
| `call_function` | function, args? | function, return_value |
| `scan_blueprint` | asset_path, audio_only?, include_pins?, graph_name?, list_graphs_only? | asset_path, blueprint_name, parent_class, blueprint_type, total_nodes, graphs, audio_summary |
| `list_assets` | class_filter?, path?, recursive_classes?, limit? | assets, total, shown, path, class_filter |
| `export_audio_blueprint` | asset_path | asset_path, blueprint_name, audio_nodes, total_nodes, nodes, edges |
| `list_blueprint_functions` | filter?, class_filter?, audio_only?, list_classes_only?, include_pins?, limit?, offset? | classes, total_classes, total_functions, shown, functions, total, offset |
| `duplicate_asset` | source_path, dest_path | source_path, dest_path, asset_name, asset_class |
| `import_sound_file` | file_path, dest_folder | asset_path, asset_name, source_file, format |

### Blueprint builder
| Command | Params | Returns |
|---------|--------|---------|
| `bp_open_blueprint` | asset_path (auto-registers the Blueprint's existing nodes) | blueprint_name, node_count, nodes |
| `bp_add_node` | id, node_kind (CallFunction/CustomEvent/VariableGet/VariableSet), function_name / event_name / variable_name (per kind), position? [x,y] | id, node_kind |
| `bp_connect_pins` | from_node, from_pin, to_node, to_pin | connection |
| `bp_set_pin_default` | node_id, pin_name, value | node_id, pin_name, value |
| `bp_compile` | — | compile_result, messages |
| `bp_register_existing_node` | id, node_guid | id, node_class, title |
| `bp_list_pins` | node_id | node_id, pin_count, pins |

### World setup
| Command | Params | Returns |
|---------|--------|---------|
| `spawn_audio_emitter` | sound, location [x,y,z], auto_play?, name? (MCP_AudioEmitter) | name, sound, location, auto_play |
| `place_audio_volume` | location [x,y,z], extent? [x,y,z], reverb_effect?, name? (MCP_AudioVolume), priority? | name, location, extent, priority, reverb_effect |
| `set_physical_surface` | material_path, surface_type | material_path, surface_type, surface_enum, surface_index, created |
| `place_anim_notify` | animation_path, time, sound?, notify_name? (Footstep) | animation, notify_name, time, animation_length, sound |
| `place_bp_anim_notify` | animation_path, time, notify_blueprint_path, notify_name? (BPNotify) | animation, notify_name, notify_blueprint, notify_class, time, animation_length |
| `spawn_blueprint_actor` | blueprint_path, location? [x,y,z], rotation? [pitch,yaw,roll], label? | actor_label, actor_class, blueprint, location, rotation |

### Actor & camera
| Command | Params | Returns |
|---------|--------|---------|
| `find_actor` | query?, class_filter?, limit? | query, class_filter, total, shown, actors |
| `set_actor_transform` | actor, location? [x,y,z], rotation? [pitch,yaw,roll] (at least one) | actor |
| `focus_editor_camera` | actor, active_viewport_only? | actor, active_viewport_only |
| `set_view_target` | actor, player_index?, blend_time? | actor, player_index, blend_time |
| `possess_pawn` | actor, player_index?, set_view_target? | actor, player_index, set_view_target |

Allowlisted functions: PlaySound2D, PlaySoundAtLocation, SpawnSoundAtLocation, SpawnSound2D, SetSoundMixClassOverride, ClearSoundMixClassOverride, PushSoundMixModifier, PopSoundMixModifier, SetGlobalPitchModulation, SetGlobalListenerFocusParameters, PlayDialogue2D, PlayDialogueAtLocation, SpawnDialogue2D, SpawnDialogueAtLocation, GetPlayerCameraManager, GetPlayerController, GetPlayerPawn.

class_filter values: Blueprint, WidgetBlueprint, AnimBlueprint, MetaSoundSource, MetaSoundPatch, SoundWave, SoundCue, SoundAttenuation, SoundClass, SoundConcurrency, SoundMix, ReverbEffect.

## Source Builder Graph Pins

`create_builder` with `Source` gives `__graph__` three built-in pins: `OnPlay` (trigger in), `OnFinished` (trigger out) and `Audio:0` (mono audio out). Wire the sound into `Audio:0`: `add_graph_output` adds an extra, custom output, not the one you hear. `__graph__` is the boundary sentinel, not a real node.

## Node Types and Pin Names

`add_node` accepts a display name from the plugin's small built-in map (e.g. `Sine`, `Biquad Filter`) or any full class name containing `::`. Take class names and exact, typed pin names from the engine-synced catalogue — `src/ue_audio_mcp/knowledge/metasound_catalogue.json`, or the `ms_node_info` and `ms_search_nodes` tools — and use `list_node_classes` against the live editor for anything missing.

Common nodes (from the catalogue):

- **Sine / Saw / Triangle** (`UE::Sine::Audio, UE::Saw::Audio, UE::Triangle::Audio`): in Enabled, Bi Polar, Frequency, Modulation, Sync, Phase Offset, Glide, Type; out Audio
- **Square** (`UE::Square::Audio`): in Enabled, Bi Polar, Frequency, Modulation, Sync, Phase Offset, Glide, Type, Pulse Width; out Audio
- **AD Envelope (Audio)** (`AD Envelope::AD Envelope::Audio`): in Trigger, Attack Time, Decay Time, Attack Curve, Decay Curve, Looping, Hard Reset; out On Trigger, On Done, Out Envelope
- **ADSR Envelope (Float)** (`ADSR Envelope::ADSR Envelope::Float`): in Trigger Attack, Trigger Release, Attack Time, Decay Time, Sustain Level, Release Time, Attack Curve, Decay Curve, Release Curve, Hard Reset; out On Attack Triggered, On Decay Triggered, On Sustain Triggered, On Release Triggered, On Done, Out Envelope
- **Biquad Filter** (`UE::Biquad Filter::Audio`): in In, Cutoff Frequency, Bandwidth, Gain, Type; out Out
- **Wave Player (Mono)** (`UE::Wave Player::Mono`): in Play, Stop, Wave Asset, Start Time, Pitch Shift, Loop, Loop Start, Loop Duration, Maintain Audio Sync; out On Play, On Finished, On Nearly Finished, On Looped, On Cue Point, Cue Point ID, Cue Point Label, Loop Percent, Playback Location, Playback Time, Out Mono
- **Multiply (Audio)** (`UE::Multiply::Audio`): in PrimaryOperand, AdditionalOperands; out Out
- **Multiply (Audio by Float)** (`UE::Multiply::Audio by Float`): in PrimaryOperand, AdditionalOperands; out Out
- **Map Range (Float)** (`MapRange::MapRange::Float`): in In, In Range A, In Range B, Out Range A, Out Range B, Clamped; out Out Value

## Example Workflows

### Simple Sine → Output
```json
{"action":"create_builder", "asset_type":"Source", "name":"MySine"}
{"action":"add_node", "id":"osc", "node_type":"UE::Sine::Audio"}
{"action":"set_default", "node_id":"osc", "input":"Frequency", "value":440}
{"action":"connect", "from_node":"osc", "from_pin":"Audio", "to_node":"__graph__", "to_pin":"Audio:0"}
{"action":"build_to_asset", "name":"MySine", "path":"/Game/Audio/MCP"}
```

### Filtered Synth with Envelope
```json
{"action":"create_builder", "asset_type":"Source", "name":"FilteredSynth"}
{"action":"add_graph_input", "name":"Cutoff", "type":"Float", "default":"2000.0"}
{"action":"add_node", "id":"osc", "node_type":"UE::Saw::Audio"}
{"action":"add_node", "id":"filt", "node_type":"UE::Biquad Filter::Audio"}
{"action":"add_node", "id":"env", "node_type":"AD Envelope::AD Envelope::Audio"}
{"action":"add_node", "id":"amp", "node_type":"UE::Multiply::Audio"}
{"action":"connect", "from_node":"osc", "from_pin":"Audio", "to_node":"filt", "to_pin":"In"}
{"action":"connect", "from_node":"__graph__", "from_pin":"Cutoff", "to_node":"filt", "to_pin":"Cutoff Frequency"}
{"action":"connect", "from_node":"__graph__", "from_pin":"OnPlay", "to_node":"env", "to_pin":"Trigger"}
{"action":"connect", "from_node":"filt", "from_pin":"Out", "to_node":"amp", "to_pin":"PrimaryOperand"}
{"action":"connect", "from_node":"env", "from_pin":"Out Envelope", "to_node":"amp", "to_pin":"AdditionalOperands"}
{"action":"connect", "from_node":"amp", "from_pin":"Out", "to_node":"__graph__", "to_pin":"Audio:0"}
{"action":"connect", "from_node":"env", "from_pin":"On Done", "to_node":"__graph__", "to_pin":"OnFinished"}
{"action":"build_to_asset", "name":"FilteredSynth", "path":"/Game/Audio/MCP"}
```

### Project Scan & Export
```json
{"action":"list_assets", "class_filter":"Blueprint"}
{"action":"scan_blueprint", "asset_path":"/Game/BP_Player", "audio_only":true}
{"action":"list_assets", "class_filter":"MetaSoundSource"}
{"action":"export_metasound", "asset_path":"/Game/Audio/MS_Gunshot"}
```

Or batch: `python scripts/scan_project.py --full-export --import-db --rebuild-embeddings`

## Gotchas

- Call `create_builder` before any node or connection command. Builder state is global: one active builder at a time.
- Asset paths must start with `/Game/` or `/Engine/` and must not contain `..`.
- Audio and Float pins don't cross-connect. Pick the matching node variant, e.g. `Multiply (Audio by Float)` to scale audio by a float.
- TCP drops after ~17 rapid commands — reconnect with a progressive delay.

## Source Files

- Command registration: `ue5_plugin/UEAudioMCP/Source/UEAudioMCP/Private/UEAudioMCPModule.cpp`
- Command handlers: `ue5_plugin/UEAudioMCP/Source/UEAudioMCP/Private/Commands/`
- Builder state, `__graph__` pins, node-type resolution: `ue5_plugin/UEAudioMCP/Source/UEAudioMCP/Private/AudioMCPBuilderManager.cpp`
- TCP server: `ue5_plugin/UEAudioMCP/Source/UEAudioMCP/Private/AudioMCPTcpServer.cpp`
- Python tools: `src/ue_audio_mcp/tools/`
- Node catalogue: `src/ue_audio_mcp/knowledge/metasound_catalogue.json` (engine-synced) and `metasound_nodes.py`

$ARGUMENTS
