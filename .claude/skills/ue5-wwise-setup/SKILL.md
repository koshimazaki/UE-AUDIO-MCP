---
name: ue5-wwise-setup
description: Wwise project setup via WAAPI HTTP API. Use when creating bus hierarchies, RTPCs, switches, states, events, SoundBanks, AudioLink containers, or any Wwise authoring automation. Covers the full WAAPI HTTP workflow on port 8090.
allowed-tools: Read, Grep, Glob, Bash
argument-hint: [wwise-setup-task]
---

# Wwise Setup — WAAPI HTTP Automation

Set up complete Wwise projects programmatically: bus hierarchies, RTPCs, switches, events, SoundBanks, and AudioLink routing.

Common object types: Sound, RandomSequenceContainer, SwitchContainer, BlendContainer, ActorMixer, Event, Bus, AuxBus, GameParameter, Switch, State.

## WAAPI HTTP API (Port 8090)

All calls use `curl -s -X POST http://127.0.0.1:8090/waapi` with JSON body:

```json
{
  "uri": "ak.wwise.core.object.create",
  "args": { ... },
  "options": {}
}
```

**Key format rules:**
- `args` contains the call parameters
- `options` is top-level (NOT inside args), used for `return` fields
- `return` goes in `options`, NOT in `args`
- Always include `"options": {}` even if empty
- Object paths use **backslashes**: `\\Busses\\Default Work Unit\\Main Audio Bus`

### Return Fields

```json
{
  "uri": "ak.wwise.core.object.get",
  "args": { "from": {"id": ["{GUID}"]} },
  "options": { "return": ["id", "name", "type", "path"] }
}
```

## Core WAAPI Operations

### Create Object
```bash
curl -s -X POST http://127.0.0.1:8090/waapi -H "Content-Type: application/json" -d '{
  "uri": "ak.wwise.core.object.create",
  "args": {
    "parent": "\\Busses\\Default Work Unit\\Main Audio Bus",
    "type": "Bus",
    "name": "SFX",
    "onNameConflict": "merge"
  },
  "options": {}
}'
```

### Set Property
```bash
curl -s -X POST http://127.0.0.1:8090/waapi -d '{
  "uri": "ak.wwise.core.object.setProperty",
  "args": {"object": "{GUID}", "property": "Volume", "value": -6.0},
  "options": {}
}'
```

### Set Reference (e.g. OutputBus)
```bash
curl -s -X POST http://127.0.0.1:8090/waapi -d '{
  "uri": "ak.wwise.core.object.setReference",
  "args": {"object": "{GUID}", "reference": "OutputBus", "value": "{BUS_GUID}"},
  "options": {}
}'
```

### Delete Object
```bash
curl -s -X POST http://127.0.0.1:8090/waapi -d '{
  "uri": "ak.wwise.core.object.delete",
  "args": {"object": "{GUID}"},
  "options": {}
}'
```

### Search / Query
```bash
# By ID
"from": {"id": ["{GUID}"]}

# By type
"from": {"ofType": ["Event"]}

# Text search
"from": {"search": ["AudioLink"]}

# By path
"from": {"path": ["\\Events\\Default Work Unit"]}

# Children of object
"transform": [{"select": ["children"]}]
```

### Save Project
```bash
curl -s -X POST http://127.0.0.1:8090/waapi -d '{
  "uri": "ak.wwise.core.project.save", "args": {}, "options": {}
}'
```

## Transport / Playback Testing

```bash
# Play in Wwise transport (NOT ak.soundengine.postEvent)
curl -s -X POST http://127.0.0.1:8090/waapi -d '{
  "uri": "ak.wwise.ui.commands.execute",
  "args": {"command": "TransportPlayDirectly", "objects": ["{EVENT_GUID}"]},
  "options": {}
}'
```

## Reload / Recovery

```bash
# Force reload project from disk
"command": "ForceReloadProject"

# Save project
"uri": "ak.wwise.core.project.save"
```

## Critical Gotchas

1. **WAAPI cannot create SourcePlugin** — Audio Input must be set manually in Wwise UI
2. **Never edit .wwu XML files** — not with Python ET, not with string replacement. Use WAAPI only
3. **Delete macOS `._*.wwu` files** on external drives — Wwise tries to parse them as work units
4. **`clearAudioFileCache: true`** required when SoundBanks are empty/stale
5. **`onNameConflict: "merge"`** prevents duplicate creation errors (the other values are `rename`, `replace` and `fail`)
6. **Paths use backslashes** even on macOS: `\\Busses\\Default Work Unit\\...`
7. **`options: {}`** required in every WAAPI HTTP call (even empty)
8. **SoundBank "Init" is auto-generated** — don't include in generate call
9. **`return` goes in `options`** at top level, NOT in `args`
10. **ForceReloadProject** may show dialog — user must click through
11. **SoundBank stale GUIDs** — if events were deleted+recreated, old GUIDs persist in SoundBank inclusions. Fix: delete entire SoundBank, recreate, re-add inclusions fresh
12. **WAAPI `setInclusions` with "replace"** does NOT always update on-disk .wwu file — Wwise caches its own version
13. **Audio Input source name doesn't matter** — just select "Wwise Audio Input" plugin, naming is irrelevant
14. **Wrap multi-step changes in an undo group** — `ak.wwise.core.undo.beginGroup` … `endGroup`, so one undo reverts the batch
15. **Batch at most 100 items per call** — Wwise authoring is single-threaded
16. **Wwise must be running** — WAAPI is localhost-only with no authentication, and there is no headless authoring mode

## Reference Files

Read these when the task needs them:

- [recipes.md](recipes.md) — bus hierarchy, RTPCs, switches and states, events, SoundBanks, containers, and the full 8-phase build recipe
- [ue5-integration.md](ue5-integration.md) — AudioLink routing, enabling Wwise in a UE5 project, and UE-side gotchas
- [lyra-reference.md](lyra-reference.md) — bus and AudioLink IDs from the Lyra demo project

## Source Files

- Wwise tools: `src/ue_audio_mcp/tools/core.py`, `objects.py`, `events.py`, `preview.py`, `templates.py`
- Wwise types: `src/ue_audio_mcp/knowledge/wwise_types.py`
- Wwise templates: `src/ue_audio_mcp/templates/wwise/`
- WAAPI research: `research/research_waapi_mcp_server.md`

$ARGUMENTS
