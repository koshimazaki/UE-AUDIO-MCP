# UE Audio MCP — C++ Plugin

Editor-only UE5 plugin. TCP server on **port 9877** receives JSON commands from the Python MCP server and executes them via MetaSounds Builder API and Blueprint reflection.

## Runtime Flow

```
 Python MCP Server (stdio)
        │
        │  TCP :9877  (4-byte BE length + UTF-8 JSON)
        ▼
 ┌─────────────────────────────┐
 │  FAudioMCPTcpServer         │  FRunnable background thread
 │  accept → recv → parse      │  Bound to 127.0.0.1 only
 └─────────────┬───────────────┘
               │
               ▼
 ┌─────────────────────────────┐
 │  FAudioMCPCommandDispatcher │  Routes "action" → handler
 │  AsyncTask(GameThread)      │  FEvent sync (25s timeout)
 └─────────────┬───────────────┘
               │  Game Thread
       ┌───────┼───────────────┐
       ▼       ▼               ▼
    Ping   BuilderManager   Blueprint
  (info)   (MetaSounds)    (reflection)
```

## 11 Commands

| Action | What it does |
|--------|-------------|
| `ping` | Returns engine version, project name, features |
| `create_builder` | New MetaSounds Source/Patch/Preset builder |
| `add_interface` | Add interface (e.g. `UE.Source.OneShot`) |
| `add_graph_input` | Graph-level input node |
| `add_graph_output` | Graph-level output node |
| `add_node` | Add DSP node by display name or class |
| `set_default` | Set input pin default value |
| `connect` | Wire pins (`__graph__` = graph boundary) |
| `build_to_asset` | Save to `/Game/...` .uasset |
| `audition` | Preview in editor |
| `call_function` | Execute UFunction via ProcessEvent |

## Setup

1. Copy `UEAudioMCP/` into your project's `Plugins/` folder
2. Rebuild. Plugin starts automatically on editor launch
3. Check Output Log for `Audio MCP TCP server listening on port 9877`
4. From Python: `ue5_connect()` → sends `ping` → ready
