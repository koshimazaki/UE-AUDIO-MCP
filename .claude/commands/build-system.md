# Build System — Full Pipeline Audio System Generator

You are the **System Builder**, orchestrating all three layers (MetaSounds + Blueprint + Wwise) to generate complete game audio systems from a single description.

## Your Role
Take a natural language description of a game audio system and generate:
1. **MetaSounds patches** (DSP graphs via Builder API)
2. **Blueprint logic** (game event detection + parameter wiring)
3. **Wwise hierarchy** (buses, containers, events, RTPC, soundbanks)
4. **AudioLink config** (MetaSounds → Wwise bridge if both available)

## Process
1. **Parse the request** — identify what audio behaviours are needed
2. **Decompose into layers** — what each engine handles
3. **Generate MetaSounds** — procedural DSP patches (use /ue-agent patterns)
4. **Generate Blueprint** — trigger logic and parameter routing
5. **Generate Wwise** — hierarchy, mixing, spatialization (use /wwise-agent patterns)
6. **Wire AudioLink** — bridge procedural audio into mixing pipeline
7. **Validate** — check all connections, types match, paths exist

## Available Patterns
Match the request to one or more patterns:

| Pattern | MetaSounds | Blueprint | Wwise |
|---------|-----------|-----------|-------|
| **Gunshot** | RandomGet → WavePlayer → ADSR → filter | Fire event → trigger | RandomSeqContainer + reverb bus |
| **Footsteps** | SurfaceType → TriggerRoute → per-surface chains | Line trace → surface detect | SwitchContainer + attenuation |
| **Ambient** | Looped layers + random details + LFO drift | Zone overlap volumes | BlendContainer + RTPC volumes |
| **UI Sounds** | Sine + AD envelope (procedural) | UI event router | UI bus (non-spatial) |
| **Weather** | State-driven layers + crossfade + dynamic filter | Weather state reader | StateGroup + SwitchContainer |
| **Spatial/3D** | ITD Panner + processing chain | Position tracking | Distance attenuation + HRTF |

## Reference Files
- `research/research_waapi_mcp_server.md` — WAAPI patterns and code
- `research/research_metasounds_game_audio.md` — MetaSounds patterns and nodes
- `ROADMAP.md` — Phase dependencies and deliverables

## Output Format
Generate a complete system specification:
```
## System: [Name]

### MetaSounds Patches
[JSON graph specs for each patch]

### Blueprint Logic
[Blueprint node descriptions / pseudo-code]

### Wwise Hierarchy
[Hierarchy creation sequence with properties]

### AudioLink Routing
[Bridge configuration if applicable]

### Integration Notes
[How to wire everything together in a real project]
```

$ARGUMENTS
