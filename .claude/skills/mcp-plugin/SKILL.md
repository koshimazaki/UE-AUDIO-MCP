---
name: mcp-plugin
description: UE5 Audio MCP plugin TCP control. Use when sending commands to the Unreal Editor plugin, building MetaSounds graphs via TCP, scanning blueprints, listing assets, or debugging the plugin connection on port 9877.
allowed-tools: Bash, Read, Grep, Glob
argument-hint: [command-or-task]
---

# UE Audio MCP Plugin — TCP Control

Drive the C++ TCP server inside Unreal Editor. All commands use 4-byte big-endian length prefix + UTF-8 JSON on `127.0.0.1:9877`.

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

## All 24 Commands

### System
| Command | Params | Returns |
|---------|--------|---------|
| `ping` | — | engine, version, project, features[] |

### Builder Lifecycle
| Command | Params | Returns |
|---------|--------|---------|
| `create_builder` | asset_type (Source/Patch/Preset), name | asset_type, name |
| `add_interface` | interface | — |
| `build_to_asset` | name, path (/Game/...) | name, path |

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
| `connect` | from_node, from_pin, to_node, to_pin | all four |

`__graph__` = sentinel node ID for graph boundary connections.

### Audition
| Command | Params | Returns |
|---------|--------|---------|
| `audition` | name? | — |
| `stop_audition` | — | — |
| `open_in_editor` | — | — |

### Variables (UE 5.7+)
| Command | Params | Returns |
|---------|--------|---------|
| `add_graph_variable` | name, type, default? | name, type |
| `add_variable_get_node` | id, variable_name, delayed? | id, variable_name |
| `add_variable_set_node` | id, variable_name | id, variable_name |

### Presets
| Command | Params | Returns |
|---------|--------|---------|
| `convert_to_preset` | referenced_asset (/Game/...) | referenced_asset |
| `convert_from_preset` | — | — |

### Query
| Command | Params | Returns |
|---------|--------|---------|
| `list_node_classes` | filter?, limit? (200) | nodes[], total, shown |
| `get_node_locations` | asset_path | nodes[], edges[] |
| `get_graph_input_names` | — | names[], count |
| `set_live_updates` | enabled (bool) | enabled |

### Blueprint & Assets
| Command | Params | Returns |
|---------|--------|---------|
| `call_function` | function, args? | function, return_value? |
| `list_assets` | class_filter?, path?, limit? | assets[], total, shown |
| `scan_blueprint` | asset_path, audio_only?, include_pins? | graphs[], audio_summary |

Allowlisted functions: PlaySound2D, PlaySoundAtLocation, SpawnSoundAtLocation, SpawnSound2D, SetSoundMixClassOverride, ClearSoundMixClassOverride, PushSoundMixModifier, PopSoundMixModifier, SetGlobalPitchModulation, SetGlobalListenerFocusParameters, PlayDialogue2D, PlayDialogueAtLocation, SpawnDialogue2D, SpawnDialogueAtLocation, GetPlayerCameraManager, GetPlayerController, GetPlayerPawn.

class_filter values: Blueprint, WidgetBlueprint, AnimBlueprint, MetaSoundSource, MetaSoundPatch, SoundWave, SoundCue, SoundAttenuation, SoundClass, SoundConcurrency, SoundMix, ReverbEffect.

## Key Pin Names

- **Sine/Saw/Square/Triangle**: IN: Frequency, Phase Offset, Glide, Bias; OUT: Audio
- **AD Envelope**: IN: Trigger, Attack Time, Decay Time; OUT: Out Envelope
- **ADSR Envelope**: IN: Trigger Attack, Trigger Release, Attack Time, Decay Time, Sustain Level, Release Time; OUT: Out Envelope
- **Biquad Filter**: IN: In, Cutoff Frequency, Bandwidth, Filter Type; OUT: Out
- **Wave Player**: IN: Play, Stop, Wave Asset, Start Time, Loop, Pitch Shift; OUT: Out Audio, On Finished
- **Multiply/Add (Audio)**: IN: Primary Operand, Operand; OUT: Out
- **Map Range**: IN: Value, In Range A, In Range B, Out Range A, Out Range B, Clamped; OUT: Out

Full pin reference: `scripts/ms_node_specs.json` (93 nodes, 464 pins)

## Example Workflows

### Simple Sine → Output
```json
{"action":"create_builder", "asset_type":"Source", "name":"MySine"}
{"action":"add_interface", "interface":"MetaSound"}
{"action":"add_graph_output", "name":"Out Mono", "type":"Audio"}
{"action":"add_node", "id":"osc", "node_type":"UE::Sine::Audio"}
{"action":"set_default", "node_id":"osc", "input":"Frequency", "value":440}
{"action":"connect", "from_node":"osc", "from_pin":"Audio", "to_node":"__graph__", "to_pin":"Out Mono"}
{"action":"build_to_asset", "name":"MySine", "path":"/Game/Audio/MCP"}
```

### Filtered Synth with Envelope
```json
{"action":"create_builder", "asset_type":"Source", "name":"FilteredSynth"}
{"action":"add_interface", "interface":"MetaSound"}
{"action":"add_graph_output", "name":"Out Mono", "type":"Audio"}
{"action":"add_graph_input", "name":"Cutoff", "type":"Float", "default":"2000.0"}
{"action":"add_node", "id":"osc", "node_type":"UE::Saw::Audio"}
{"action":"add_node", "id":"filt", "node_type":"UE::Biquad Filter::Audio"}
{"action":"add_node", "id":"env", "node_type":"AD Envelope"}
{"action":"add_node", "id":"mul", "node_type":"UE::Multiply::Audio"}
{"action":"connect", "from_node":"osc", "from_pin":"Audio", "to_node":"filt", "to_pin":"In"}
{"action":"connect", "from_node":"__graph__", "from_pin":"Cutoff", "to_node":"filt", "to_pin":"Cutoff Frequency"}
{"action":"connect", "from_node":"filt", "from_pin":"Out", "to_node":"mul", "to_pin":"Primary Operand"}
{"action":"connect", "from_node":"env", "from_pin":"Out Envelope", "to_node":"mul", "to_pin":"Operand"}
{"action":"connect", "from_node":"mul", "from_pin":"Out", "to_node":"__graph__", "to_pin":"Out Mono"}
{"action":"build_to_asset", "name":"FilteredSynth", "path":"/Game/Audio/MCP"}
```

### Project Scan
```json
{"action":"list_assets", "class_filter":"Blueprint"}
{"action":"scan_blueprint", "asset_path":"/Game/BP_Player", "audio_only":true}
{"action":"list_assets", "class_filter":"MetaSoundSource"}
{"action":"get_node_locations", "asset_path":"/Game/Audio/MS_Gunshot"}
```

Or batch: `python scripts/scan_project.py --full-export --import-db --rebuild-embeddings`

## Gotchas

- Must call `create_builder` before any node/connection ops
- `__graph__` is NOT a real node — it's the boundary sentinel
- Path must start with `/Game/` or `/Engine/`, no `..`
- Audio vs Float: cannot cross-connect — use correct node variant
- TCP drops after ~17 rapid commands — use reconnect with progressive delay
- Builder state is global — only one active builder at a time
- `list_node_classes` discovers real class names — the 65-name registry may miss some

## Source Files

- C++ commands: `ue5_plugin/UEAudioMCP/Source/UEAudioMCP/Private/Commands/`
- TCP server: `ue5_plugin/UEAudioMCP/Source/UEAudioMCP/Private/AudioMCPTCPServer.cpp`
- Python tools: `src/ue_audio_mcp/tools/`
- Node registry: `src/ue_audio_mcp/knowledge/metasound_nodes.py` (144 nodes, 798 pins)

$ARGUMENTS
