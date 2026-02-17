---
name: add-command
description: Add a new C++ TCP command + Python MCP tool to the UE Audio MCP plugin. Guides you through the 6-file checklist so nothing gets missed.
allowed-tools: Read, Edit, Write, Bash, Grep, Glob
argument-hint: [command_name] [brief description]
---

# Add New Command to UE Audio MCP

Follow this checklist to add a new C++ TCP command and its Python MCP tool wrapper.

## Checklist (6 files, always in this order)

### 1. Header — declare the command class

**File**: `ue5_plugin/UEAudioMCP/Source/UEAudioMCP/Public/Commands/<Group>Commands.h`

Pick the right group file:
- `BuilderCommands.h` — MetaSounds builder operations
- `NodeCommands.h` — MetaSounds node operations
- `QueryCommands.h` — queries, exports, scans, asset operations
- `BPBuilderCommands.h` — Blueprint graph editing
- `WorldCommands.h` — world setup (AnimNotify, emitters, volumes, spawning)

```cpp
/** command_name: Brief description of what this command does. */
class FMyNewCommand : public IAudioMCPCommand
{
public:
    virtual TSharedPtr<FJsonObject> Execute(
        const TSharedPtr<FJsonObject>& Params,
        FAudioMCPBuilderManager& BuilderManager) override;
};
```

### 2. Implementation — write the Execute() method

**File**: `ue5_plugin/UEAudioMCP/Source/UEAudioMCP/Private/Commands/<Group>Commands.cpp`

Pattern:
```cpp
TSharedPtr<FJsonObject> FMyNewCommand::Execute(
    const TSharedPtr<FJsonObject>& Params,
    FAudioMCPBuilderManager& /*BuilderManager*/)
{
    // 1. Extract params
    FString MyParam;
    if (!Params->TryGetStringField(TEXT("my_param"), MyParam))
    {
        return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'my_param'"));
    }

    // 2. Validate (paths must start with /Game/, no "..", etc.)
    if (!MyParam.StartsWith(TEXT("/Game/")))
    {
        return AudioMCP::MakeErrorResponse(TEXT("my_param must start with /Game/"));
    }

    // 3. Do the work (on game thread — this runs via AsyncTask)
    // ... UE5 API calls here ...

    // 4. Return JSON response
    TSharedPtr<FJsonObject> Resp = AudioMCP::MakeOkResponse();
    Resp->SetStringField(TEXT("my_param"), MyParam);
    return Resp;
}
```

**Key helpers** (from `AudioMCPTypes.h`):
- `AudioMCP::MakeOkResponse()` / `AudioMCP::MakeOkResponse("message")`
- `AudioMCP::MakeErrorResponse("error message")`

**UE 5.7 gotchas**:
- `UE_LOG` format strings are strictly validated — avoid `%s` with complex expressions
- `World->SpawnActor` — use `FTransform` overload, not `FVector*/FRotator*` pointers
- Always check `GEditor` is non-null before accessing editor world

### 3. Build.cs — add module dependencies (if needed)

**File**: `ue5_plugin/UEAudioMCP/Source/UEAudioMCP/UEAudioMCP.Build.cs`

Only if your command uses new UE modules not already listed:
```csharp
PrivateDependencyModuleNames.AddRange(new string[]
{
    // ... existing deps ...
    "NewModule",  // Brief comment why
});
```

### 4. Register — wire command name to class

**File**: `ue5_plugin/UEAudioMCP/Source/UEAudioMCP/Private/UEAudioMCPModule.cpp`

Add include at top:
```cpp
#include "Commands/<Group>Commands.h"  // if new group file
```

Add registration in `RegisterCommands()`:
```cpp
// N+1. Brief description
Dispatcher->RegisterCommand(TEXT("my_command_name"),
    MakeShared<FMyNewCommand>());
```

Update the log message count:
```cpp
TEXT("UE Audio MCP ready — listening on port %d (N+1 commands registered)"),
```

### 5. Python MCP tool — wrap the TCP command

**File**: `src/ue_audio_mcp/tools/<category>.py` (or new file)

```python
@mcp.tool()
def my_command_name(
    my_param: str,
    optional_param: int = 0,
) -> str:
    """Brief description for MCP clients.

    More detail about what this does and when to use it.

    Args:
        my_param: What this parameter controls
        optional_param: What this optional param does (default 0)
    """
    if not my_param.strip():
        return _error("my_param cannot be empty")
    if ".." in my_param:
        return _error("my_param must not contain '..'")

    conn = get_ue5_connection()
    try:
        result = conn.send_command({
            "action": "my_command_name",
            "my_param": my_param,
            "optional_param": optional_param,
        })
        if result.get("status") == "error":
            return _error(result.get("message", "my_command_name failed"))
        return _ok(result)
    except Exception as e:
        return _error(str(e))
```

If new file, add import in `src/ue_audio_mcp/server.py`:
```python
import ue_audio_mcp.tools.my_module  # noqa: E402, F401
```

### 6. Tests — validate Python tool

**File**: `tests/test_<category>.py`

```python
def test_my_command_valid(ue5_conn, mock_ue5_plugin):
    mock_ue5_plugin.set_response("my_command_name", {
        "status": "ok", "my_param": "/Game/Test",
    })
    result = json.loads(my_command_name(my_param="/Game/Test"))
    assert result["status"] == "ok"
    cmd = mock_ue5_plugin.commands[-1]
    assert cmd["action"] == "my_command_name"

def test_my_command_empty_param(ue5_conn):
    result = json.loads(my_command_name(my_param=""))
    assert result["status"] == "error"
    assert "empty" in result["message"]
```

## Build & Verify

```bash
# 1. Run Python tests
python -m pytest tests/ -v

# 2. Sync + clean build
./scripts/build_plugin.sh --clean

# 3. Update docs
# - TOOLS_AND_COMMANDS.md — add to tool/command tables
# - README.md — update counts
# - MEMORY.md — update stats
```

## Security Rules

- Asset paths: must start with `/Game/` or `/Engine/`, reject `..`
- Function names: must be in allowlist (BlueprintManager.AllowedFunctions)
- File paths: validate they exist on disk, reject traversal
- TCP: localhost only (127.0.0.1), 16MB max message size
