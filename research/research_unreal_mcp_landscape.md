# Unreal Engine MCP Server Landscape Research

_Generated: 2026-02-06 | Sources: 15+ GitHub repos, web documentation_

## Quick Reference

<key-points>
- 6+ active Unreal MCP projects on GitHub; chongdashu/unreal-mcp leads with 1,370 stars
- All major UE MCP repos use the same pattern: Python MCP Server <-> TCP Socket <-> C++ UE Plugin
- BilkentAudio/Wwise-MCP (23 stars) already exists -- Wwise-only, WAAPI-based, Python/FastMCP, no UE integration
- blender-mcp (16,899 stars) established the gold-standard architecture: Addon (socket server) + MCP Server (FastMCP)
- No project combines Wwise + MetaSounds + Blueprint audio in a single MCP server -- this is greenfield
- Recommended path: Build from scratch using proven architecture patterns, not fork/extend
</key-points>

---

## 1. Unreal Engine MCP Repos -- Detailed Comparison

### 1.1 chongdashu/unreal-mcp (LEADER)

| Attribute | Detail |
|-----------|--------|
| Stars | 1,370 |
| Forks | 205 |
| Language | C++ (plugin) + Python (MCP server) |
| UE Version | 5.5+ |
| Last Updated | 2026-02-06 (active) |
| Status | Experimental |

**Architecture:**
```
AI Client (Claude/Cursor/Windsurf)
    |  MCP Protocol (stdio)
    v
Python MCP Server (unreal_mcp_server.py, FastMCP)
    |  TCP Socket (port 55557)
    v
C++ Plugin (UnrealMCP.uplugin) inside UE5 Editor
    |  Native API calls
    v
Unreal Engine subsystems
```

**Tools Exposed (5 modules in `Python/tools/`):**
- `blueprint_tools.py` -- class creation, component config, physics, spawning, input mapping
- `editor_tools.py` -- actor CRUD, transforms, properties, viewport control
- `node_tools.py` -- Blueprint graph: event/function nodes, variables, connections
- `project_tools.py` -- project-level operations
- `umg_tools.py` -- UMG/UI tools

**Extension Pattern:**
- Tools defined via `@mcp.tool()` decorator (FastMCP)
- Communication: `unreal = get_unreal_connection()` then `response = unreal.send_command("command_name", params)`
- New tools: add Python file to `tools/` directory, auto-registered at startup
- C++ side: add command handler in plugin, expose via TCP

**Audio Capabilities:** NONE. No audio tools whatsoever.

**Could we extend it?**
- YES for Blueprint tools (already has Blueprint graph manipulation)
- NO practical path for MetaSounds (would need C++ Builder API additions to plugin)
- NO path for Wwise (completely different communication -- WAAPI vs TCP to UE)
- Extension would require forking BOTH the Python server AND the C++ plugin
- The plugin has no audio subsystem awareness

**Verdict:** Good reference architecture but wrong scope. Extending it means maintaining someone else's C++ plugin code for features we do not need (general editor control), while adding all our audio code on top.

---

### 1.2 flopperam/unreal-engine-mcp

| Attribute | Detail |
|-----------|--------|
| Stars | 431 |
| Forks | 93 |
| Language | C++ + Python |
| UE Version | 5.5, 5.6, 5.7 |
| Last Updated | 2026-02-06 (active) |

**Architecture:** Same pattern as chongdashu -- Python MCP server over TCP to C++ plugin.

**Unique Features:**
- 40+ tools (most of any UE MCP)
- Blueprint analysis and node manipulation (23+ node types across 6 categories)
- 3D generation quality tiers (text/image-to-3D)
- Embedded agent UI in the UE Editor ("The Flop Agent")
- World-building tools: `create_town`, `construct_house`, `create_castle_fortress`, `create_maze`

**Audio Capabilities:** Roadmap mentions Metasound support but nothing implemented.

**Could we extend it?** Similar situation to chongdashu -- large codebase focused on visual/level design, not audio.

---

### 1.3 kvick-games/UnrealMCP

| Attribute | Detail |
|-----------|--------|
| Stars | 493 |
| Forks | 65 |
| Language | C++ + Python |
| UE Version | 5.5 |

**Architecture:** TCP socket on port 13377 with JSON protocol. Explicitly inspired by blender-mcp.

**Tools:** Basic -- scene info, actor CRUD, transforms, materials, Python execution.

**Roadmap includes (not yet built):** Asset tools, Blueprints, Niagara VFX, **MetaSound**, Modeling Tools, PCG.

**Audio Capabilities:** None implemented. MetaSound is on roadmap.

**Extension Model:** Plans for "easy tool extension outside the main plugin" + `execute_python` escape hatch.

---

### 1.4 runreal/unreal-mcp (NO PLUGIN NEEDED)

| Attribute | Detail |
|-----------|--------|
| Stars | 70 |
| Forks | 14 |
| Language | TypeScript/Node.js + Python remote execution |
| UE Version | Any (uses built-in Python remote execution) |

**Architecture -- KEY DIFFERENCE:**
```
AI Client
    |  MCP Protocol
    v
TypeScript MCP Server (Node.js)
    |  Python Remote Execution Protocol (built into UE)
    v
UE5 Editor (no custom plugin needed!)
```

**No plugin installation required.** Uses UE's built-in Python Editor Script Plugin + remote execution. This is the lightest-weight approach.

**Tools (19 total):** Asset management, world editing, Python execution, screenshots, camera control.

**Audio Capabilities:** None, but `editor_run_python` allows executing arbitrary Python in UE.

**Could we extend it?** YES -- for Blueprint/UE operations, this is the most extensible approach since it avoids custom C++ plugins entirely. However, MetaSounds Builder API is C++ only (not exposed to Python), so this approach cannot generate MetaSounds graphs.

---

### 1.5 Other Notable UE MCP Repos

| Repo | Stars | Approach | Notes |
|------|-------|----------|-------|
| ChiR24/Unreal_mcp | ~20 | TS + C++ + Rust (WASM) | Over-engineered |
| ayeletstudioindia/unreal-analyzer-mcp | ~10 | Analysis/code-reading only | Read-only, no editor control |
| runeape-sats/unreal-mcp | ~5 | Early alpha | Minimal |
| appleweed/UnrealMCPBridge | ~5 | UE Plugin as MCP server | Different architecture |
| natfii/ue5-mcp-bridge | ~15 | Bridges to Blueprints + AnimBP | Niche |

---

## 2. BilkentAudio/Wwise-MCP (Existing Wwise MCP)

| Attribute | Detail |
|-----------|--------|
| Stars | 23 |
| Forks | 3 |
| Language | Python |
| Framework | FastMCP |
| Wwise Version | 2024.1+ |
| Created | 2025-12-02 |
| Last Updated | 2026-02-03 |
| Topics | game-audio, mcp-server, waapi, wwise |

**Architecture:**
```
AI Client (Claude/Cursor)
    |  MCP Protocol (stdio)
    v
FastMCP Server (wwise_mcp.py)
    |  WAAPI (WebSocket, typically port 8080)
    v
Wwise Authoring Application
```

**No UE integration.** This is Wwise-standalone only.

**Source Structure:**
```
app/scripts/
    wwise_mcp.py          -- Main MCP server, tool registration
    wwise_python_lib.py   -- WAAPI wrapper library (the bulk of functionality)
    wwise_session.py      -- Session management
    wwise_errors.py       -- Error types
    waapi_errors.py       -- WAAPI-specific errors
```

**Exposed Capabilities via wwise_python_lib.py:**
- Connection: `connect_to_waapi()`, `disconnect_from_wwise_client()`
- Project info: `get_project_info()`, `get_all_languages()`, `get_all_platforms()`
- Object operations: `get_object_at_path()`, `rename_objects()`, `set_property()`, `set_reference()`, `move_object_by_path()`
- Events: `create_event()`, `list_all_event_names()`, `post_event()`, `stop_event()`
- Game syncs: `create_rtpc()`, `set_state()`, `set_switch()`, `set_rtpc()`, `ramp_rtpc()`
- SoundBanks: `get_all_soundbanks()`, `include_in_soundbank()`, `generate_soundbanks()`
- Game objects: `ensure_game_obj()`, `set_game_obj_position()`, `start_position_ramp()`
- Audio import: `import_audio_files()`, `list_audio_files_at_path_file_explorer()`
- Playback: `post_event()`, `stop_all_sounds()`
- UI: `toggle_layout()`, `get_selected_objects()`

**Tool Registration Pattern:**
```python
@mcp.tool()
async def list_wwise_commands() -> list[str]:
    """Return each available command with its signature"""
    return list_commands()

@mcp.tool()
async def execute_plan(plan: list[str]) -> dict[str, any]:
    """Execute a JSON list of call-strings produced by Claude"""
    log = await anyio.to_thread.run_sync(_run_plan_sync, plan)
    return {"status": "ok", "steps_executed": len(log), "log": log}
```

**Unique Architecture Feature -- Plan Execution:**
Instead of exposing each WAAPI call as a separate MCP tool, Wwise-MCP uses a "plan execution" pattern where Claude generates a sequence of command strings, and the server executes them in order with variable passing (`$var` references across steps). This is more LLM-friendly -- Claude plans a multi-step workflow as a single tool call.

**Could we use/extend this?**
- The `wwise_python_lib.py` is a solid WAAPI wrapper -- could be used as-is or as reference
- Architecture is Wwise-only -- no concept of UE5 integration
- Plan execution pattern is interesting but may be limiting for our multi-engine orchestration
- Would need to add MetaSounds tools, Blueprint tools, and the systems layer on top
- Better to reference than to fork -- their scope is fundamentally different (Wwise authoring vs. game audio systems)

---

## 3. blender-mcp Architecture (The Gold Standard)

| Attribute | Detail |
|-----------|--------|
| Stars | 16,899 |
| Forks | 1,613 |
| Language | Python |
| Framework | FastMCP |
| Author | Siddharth Ahuja (ahujasid) |

**Architecture -- Two Components:**

```
Component 1: MCP Server (src/blender_mcp/server.py)
    - FastMCP framework
    - @mcp.tool() decorated functions
    - BlenderConnection singleton (socket client)
    - Sends JSON commands to addon

Component 2: Blender Addon (addon.py)
    - Runs inside Blender as a plugin
    - TCP socket server (localhost:9876)
    - Receives JSON commands
    - Executes bpy.* calls on main thread
    - Returns JSON responses
```

**Communication Protocol:**
```json
// Command (MCP Server -> Addon)
{"type": "command_name", "params": {"key": "value"}}

// Response (Addon -> MCP Server)
{"status": "ok", "result": {...}}
```

**Key Design Decisions:**
1. Socket server runs INSIDE the DCC app (Blender) -- this is the plugin
2. MCP server is a separate Python process -- this is what Claude talks to
3. JSON over TCP -- simple, debuggable, language-agnostic
4. Main thread scheduling via `bpy.app.timers` -- Blender requires main thread for API calls
5. `execute_blender_code` escape hatch for arbitrary Python execution

**Extension Pattern:**
1. Add command handler in `addon.py` (check incoming JSON `type` field)
2. Implement logic using Blender Python API
3. Return JSON response
4. Add corresponding `@mcp.tool()` in `server.py`
5. Tool immediately available to Claude

**Why 16.9k stars?** Simplicity. Two files. Clear separation. Works out of the box. This is the pattern to follow.

---

## 4. SIDKIT / koshimazaki Architecture

koshimazaki's repos do not contain a "SIDKIT" MCP repo on GitHub. Based on the project README, SIDKIT is a hardware synth project where:
- Triple-agent architecture generates C++ firmware for Teensy ARM
- Compilation errors feed back to improve generation (learning loop on Cloudflare D1)
- SysEx protocol for hardware communication
- A2HW (Agent-to-Hardware) protocol bridges agent descriptions to hardware targets

**koshimazaki's relevant repos:**
- `koshimazaki/SIDSynth` (2 stars) -- SID synth in C
- `koshimazaki/LMStudio-MCP-Bridge` (1 star) -- LM Studio MCP bridge for Claude Code
- `koshimazaki/koshi-code` -- Custom Claude Code setup with memory and MCPs
- `koshimazaki/UE5-WWISE` (this project) -- game audio MCP

The SIDKIT pattern is referenced as inspiration: agent-generated audio systems from natural language. The A2HW protocol concept bridges SIDKIT (hardware) with this project (game engines).

---

## 5. Build vs. Fork/Extend Analysis

### Option A: Fork chongdashu/unreal-mcp

**Pros:**
- 1,370 stars, active community, maintained
- C++ plugin already handles TCP, actor management, Blueprint graph
- Tool extension pattern is clean (add Python files to `tools/`)

**Cons:**
- Zero audio awareness in the C++ plugin
- Would need to add MetaSounds Builder API calls to C++ (heavy modification)
- Would need to maintain their general-purpose editor code we do not need
- Wwise communication is completely separate (WAAPI, not TCP to UE plugin)
- Their plugin is for scene editing, not audio systems
- Fork divergence: their updates would conflict with our audio additions
- We would be maintaining 2,000+ lines of C++ we did not write

### Option B: Fork BilkentAudio/Wwise-MCP

**Pros:**
- Already has WAAPI wrapper with comprehensive coverage
- FastMCP, same framework we would use
- 23 stars but solid implementation

**Cons:**
- Wwise-only, no concept of UE5 integration
- Plan execution pattern may not fit multi-engine orchestration
- Would need to bolt on MetaSounds + Blueprint as separate subsystems
- Their architecture assumes single-target (Wwise), ours is multi-target
- Small community, uncertain maintenance

### Option C: Build from Scratch (RECOMMENDED)

**Pros:**
- Purpose-built for game audio (Wwise + MetaSounds + Blueprint)
- Clean architecture from day 1 -- no inherited technical debt
- Can cherry-pick the best patterns from all projects:
  - blender-mcp's two-component architecture (addon + server)
  - chongdashu's modular tool files pattern
  - BilkentAudio's WAAPI wrapper as reference
  - runreal's plugin-free UE Python execution for Blueprint tools
- Single MCP server with three communication channels:
  - WAAPI WebSocket -> Wwise (like BilkentAudio)
  - TCP Socket -> Custom C++ Plugin (like chongdashu, for MetaSounds Builder API)
  - Python Remote Execution -> UE5 (like runreal, for Blueprint tools -- no plugin needed)
- First-of-kind positioning: no existing project combines these
- Full control over API design, tool naming, error handling

**Cons:**
- More initial work
- No inherited community
- Need to build C++ plugin from scratch (for MetaSounds Builder API)

### Why Build from Scratch Wins

The fundamental issue with forking is **scope mismatch**:

| What We Need | chongdashu | BilkentAudio | What We Build |
|-------------|-----------|-------------|---------------|
| Wwise WAAPI | No | Yes | Yes |
| MetaSounds Builder API | No | No | Yes |
| Blueprint audio tools | Partial (generic) | No | Yes (audio-specific) |
| Audio system orchestration | No | No | Yes |
| AudioLink bridge | No | No | Yes |
| Multi-engine coordination | No | No | Yes |

No existing project is even close to our scope. Forking would mean:
1. Removing 80% of inherited code we do not need
2. Adding 100% of audio-specific code ourselves anyway
3. Maintaining compatibility with upstream for zero benefit

The proven patterns (TCP JSON protocol, FastMCP tools, modular tool files) are architectural conventions, not proprietary code. We adopt the patterns, not the codebases.

---

## 6. Recommended Architecture (Synthesis)

Based on this research, the optimal architecture combines the best of each project:

```
                    Claude / Cursor / Any MCP Client
                                |
                                | MCP Protocol (stdio)
                                v
                    +---------------------------+
                    |    UE Audio MCP Server     |
                    |    (Python, FastMCP)       |
                    |                           |
                    |  tools/wwise/             |  <-- Pattern from chongdashu
                    |  tools/metasounds/        |      (modular tool directories)
                    |  tools/blueprints/        |
                    |  tools/systems/           |
                    +---------------------------+
                       |          |          |
            WAAPI      |   TCP    |  Python  |  Remote Exec
            WebSocket  |   Socket |          |
                       v          v          v
                  +---------+ +--------+ +----------+
                  | Wwise   | | C++ UE | | UE5      |
                  | App     | | Plugin | | Editor   |
                  | (:8080) | | (:9877)| | (Remote) |
                  +---------+ +--------+ +----------+
                                |
                                v
                       MetaSounds Builder API
```

**Communication Channels:**
1. **Wwise:** WAAPI WebSocket (port 8080) -- reference BilkentAudio's `wwise_python_lib.py`
2. **MetaSounds:** TCP Socket to custom C++ plugin (port 9877) -- follow blender-mcp/chongdashu pattern
3. **Blueprint:** UE Python Remote Execution -- follow runreal pattern (NO custom plugin needed)

**Key Patterns to Adopt:**
- From blender-mcp: Two-component architecture, JSON over TCP, socket server inside the app
- From chongdashu: Modular tool files auto-registered, `@mcp.tool()` decorator pattern
- From BilkentAudio: WAAPI wrapper library as reference, plan execution concept
- From runreal: Plugin-free Blueprint tools via Python remote execution

---

## 7. References

<references>
- [chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp) -- 1,370 stars, leader in UE MCP space
- [flopperam/unreal-engine-mcp](https://github.com/flopperam/unreal-engine-mcp) -- 431 stars, most tools (40+)
- [kvick-games/UnrealMCP](https://github.com/kvick-games/UnrealMCP) -- 493 stars, blender-mcp inspired
- [runreal/unreal-mcp](https://github.com/runreal/unreal-mcp) -- 70 stars, no-plugin approach
- [ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp) -- 16,899 stars, gold-standard architecture
- [BilkentAudio/Wwise-MCP](https://github.com/BilkentAudio/Wwise-MCP) -- 23 stars, existing Wwise MCP
- [audiokinetic/waapi-client-python](https://github.com/audiokinetic/waapi-client-python) -- Official WAAPI Python client
- [WAAPI Documentation](https://www.audiokinetic.com/library/wwise_launcher/?id=integrating_wwise_into_an_unreal_project) -- Wwise integration docs
- [blender-mcp server.py](https://github.com/ahujasid/blender-mcp/blob/main/src/blender_mcp/server.py) -- MCP server reference implementation
- [blender-mcp addon.py](https://github.com/ahujasid/blender-mcp/blob/main/addon.py) -- Plugin bridge reference
- [chongdashu/unreal-mcp tools](https://github.com/chongdashu/unreal-mcp/tree/main/Python/tools) -- Modular tool pattern
- [koshimazaki GitHub](https://github.com/koshimazaki) -- SIDKIT creator, 41 repos
</references>

## 8. Metadata

<meta>
research-date: 2026-02-06
confidence: high
repos-analyzed: 10
star-counts-verified: 2026-02-06
version-checked: UE 5.5-5.7, Wwise 2024.1+, FastMCP latest
recommendation: build-from-scratch
</meta>
