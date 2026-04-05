---
name: ue5-metasound-dsp
description: MetaSounds DSP specialist for Unreal Engine 5. Use when designing MetaSounds graphs, choosing DSP nodes, configuring filters/oscillators/envelopes, building signal chains, working with the Builder API, or creating audio templates. Covers 144 nodes across 20 categories.
allowed-tools: Read, Grep, Glob
argument-hint: [dsp-task-or-question]
---

# MetaSounds DSP — Node Graphs & Signal Design

Design MetaSounds audio graphs: choose nodes, wire signal chains, configure DSP parameters, and generate Builder API command sequences.

## Data Types

Audio, Trigger, Float, Int32, Bool, Time, String, WaveAsset, UObject, Enum (+ Array variants)

**Type rules**: Audio-rate cannot connect to Float. Use correct node variant (e.g., `Multiply (Audio)` vs `Multiply (Float)`).

## Asset Types

| Type | Use | Interface |
|------|-----|-----------|
| **Source** | Standalone playable asset | UE.Source.OneShot or MetaSound |
| **Patch** | Reusable subgraph (no play) | Custom |
| **Preset** | Parameter overrides of existing Source/Patch | Inherits parent |

## Interfaces

- `MetaSound` — Standard audio output
- `UE.Source.OneShot` — OnPlay trigger in, OnFinished trigger out
- `UE.Attenuation` — Distance input for volume falloff
- `UE.Spatialization` — Azimuth/Elevation for 3D positioning

## Node Categories (144 nodes, 20 categories)

### Generators
Sine, Saw, Square, Triangle, Noise, LFO, Additive Synth, SuperOscillator, WaveTable, Perlin Noise

### Wave Players
Wave Player (mono), Stereo Wave Player, with loop/pitch shift/concatenation

### Envelopes
AD Envelope (Audio-rate), AD Envelope (Float), ADSR Envelope, Crossfade, WaveTable Envelope

### Filters
Biquad Filter, State Variable Filter, Dynamic Filter, Ladder Filter, One-Pole HPF, One-Pole LPF, Band Splitter, Bitcrusher

### Delays & Time
Delay, Stereo Delay, Pitch Shift, Diffuser, Grain Delay, Flanger

### Dynamics
Compressor, Limiter

### Math (Audio)
Add, Subtract, Multiply, Mix — all have `Primary Operand` + `Operand` pins

### Math (Float)
Add, Subtract, Multiply, Divide, Modulo, Map Range, Clamp, InterpTo, Linear To Log Frequency

### Triggers
Accumulate, Any, Compare, Control, Counter, Delay, Filter, Gate, Once, OnThreshold, OnValueChange, Pipe, Repeat, Route, Sequence

### Spatialization
ITD Panner, Stereo Panner, Mid-Side Encode/Decode, Doppler Pitch Shift

### Music
Frequency↔MIDI, MIDI Quantizer, Scale to Note Array, BPM to Seconds, Metronome, Quartz Clock

### Effects
Plate Reverb, Ring Modulator, WaveShaper, Chorus, Phaser

### Utility
Crossfade, Envelope Follower, Wave Writer, Random Get, Trigger On Threshold

### SIDKIT (Custom)
SID Oscillator, SID Envelope, SID Filter, SID Voice, SID Chip

## Signal Flow Patterns

### Basic: Generator → Envelope → Output
```
Sine → Multiply(Audio) × AD Envelope → Out Mono
```

### Subtractive: Osc → Filter → Amp → Output
```
Saw → Biquad Filter(LP) → Multiply × ADSR → Out Mono
         ↑ Cutoff Frequency
```

### Additive: Multiple Oscs → Mix → Output
```
Sine(f) + Sine(2f) + Sine(3f) → Add → Multiply × Envelope → Out
```

### Triggered: Event → Sample Player → Processing
```
OnPlay → Wave Player → Biquad Filter → Compressor → Out
                         ↑ Pitch Shift for variation
```

### Modulated: LFO → Parameter Control
```
LFO → Map Range(0-1 → 200-2000) → Biquad Filter Cutoff
```

## Key Pin Names (Authoritative)

| Node | Inputs | Outputs |
|------|--------|---------|
| Sine/Saw/Square/Triangle | Frequency, Phase Offset, Glide, Bias | Audio |
| Noise | Seed | Audio |
| AD Envelope | Trigger, Attack Time, Decay Time | Out Envelope |
| ADSR Envelope | Trigger Attack, Trigger Release, Attack Time, Decay Time, Sustain Level, Release Time | Out Envelope |
| Biquad Filter | In, Cutoff Frequency, Bandwidth, Filter Type | Out |
| State Variable Filter | In, Cutoff Frequency, Resonance, Band Stop Gain | HPF, LPF, BPF, BSF |
| Wave Player | Play, Stop, Wave Asset, Start Time, Loop, Pitch Shift | Out Audio, On Finished |
| Multiply/Add (Audio) | Primary Operand, Operand | Out |
| Map Range | Value, In Range A, In Range B, Out Range A, Out Range B, Clamped | Out |
| InterpTo | Target, Current, Speed, Interp Delta Time | Value |
| Clamp | In, Min, Max | Value |
| Compressor | Audio, Ratio, Threshold dB, Attack Time, Release Time, Sidechain, Wet, Knee | Audio |
| ITD Panner | Audio, Angle, Interaural Delay, Head Width | Left, Right |
| Trigger Repeat | Start, Stop, Period | RepeatOut |
| Trigger Sequence | Trigger, Reset | Out 0, Out 1, ... |

Full reference: `scripts/ms_node_specs.json` (93 nodes, 464 pins from Epic docs)

## Builder API Functions (68+)

### Core
CreateSourceBuilder, CreatePatchBuilder, AddNode, FindNodeInputHandle, FindNodeOutputHandle, ConnectNodes, SetNodeInputDefault, Audition, BuildToAsset

### Graph I/O
AddGraphInput, AddGraphOutput, RemoveGraphInput, RemoveGraphOutput, GetGraphInputNames

### Interfaces
AddInterface, RemoveInterface, IsInterfaceDeclared

### Variables (UE 5.7+)
AddGraphVariable, AddVariableGetNode, AddVariableSetNode, AddVariableGetDelayedNode

### Presets
ConvertToPreset, ConvertFromPreset

### Live Updates
SetLiveUpdatesEnabled

## Templates Available (22 JSON)

| Template | Nodes | Pattern |
|----------|-------|---------|
| gunshot | 7 | Random → WavePlayer → Filter → Envelope |
| footsteps | 8 | Surface switch → per-surface chains |
| ambient | 9 | Looped layers + random details + LFO |
| spatial | 6 | ITD Panner + distance processing |
| ui_sound | 5 | Sine + AD Envelope (procedural) |
| weather | 10 | State-driven + crossfade + dynamic filter |
| vehicle_engine | 14 | Trigger Sequence → layered Wave Players |
| sfx_generator | 25 | 7-stage synth (Gen→Spectral→Filter→Amp→FX) |
| preset_morph | 8 | Morph 0-1 → MapRange → filter params |
| macro_sequence | 12 | Graph variables → InterpTo → filter |
| sid_bass/lead/chip_tune | 5-8 | SID nodes for chiptune |
| wind/snare | 6-8 | From Epic tutorial exports |

Templates at: `src/ue_audio_mcp/templates/`

## Graph JSON Spec

```json
{
  "type": "source",
  "interface": "MetaSound",
  "nodes": [
    {"id": "osc1", "class": "Sine", "defaults": {"Frequency": 440.0}},
    {"id": "env1", "class": "AD Envelope", "defaults": {"Attack Time": 0.01, "Decay Time": 0.5}}
  ],
  "connections": [
    {"from": "osc1:Audio", "to": "env1:In"}
  ],
  "inputs": [
    {"name": "Frequency", "type": "Float", "target": "osc1:Frequency"}
  ],
  "outputs": [
    {"name": "Out Mono", "type": "Audio", "source": "env1:Out Envelope"}
  ]
}
```

Validated by 7-stage validator: required fields, asset_type, interfaces, node types, pin existence, type compatibility, required inputs, interface completeness.

## Design Guidelines

1. Choose asset type: Source (playable) or Patch (reusable subgraph)
2. Select interface: MetaSound (general), OneShot (fire-and-forget)
3. Design signal flow: Generator → Processing → Envelope → Mixing → Output
4. Expose parameters Blueprint needs to control as graph inputs
5. Use `SetNodeLocation()` for editor layout visibility
6. Validate with `ms_validate_graph` before sending to Builder API
7. Consider AudioLink if routing to Wwise for mixing

## Gotchas

- AD Envelope (Float) for modulation chains, AD Envelope (Audio) for amplitude
- InterpTo requires `Current` default value
- Float→Audio connections are invalid — use Biquad Filter Bandwidth, not Multiply Audio
- Dynamic Filter needs Audio-rate cutoff input; use Biquad for Float cutoff
- Pin names from Epic docs may use shorthand — always verify against `ms_node_specs.json`
- Node class names: use display names from knowledge DB, or full `Namespace::Name::Variant` for direct lookup

## Source Files

- Node catalogue: `src/ue_audio_mcp/knowledge/metasound_nodes.py` (144 nodes, 798 pins)
- Templates: `src/ue_audio_mcp/templates/` (22 JSON graphs)
- Graph schema: `src/ue_audio_mcp/knowledge/graph_schema.py`
- Builder tools: `src/ue_audio_mcp/tools/metasounds.py`
- Scraped pins: `scripts/ms_node_specs.json`

$ARGUMENTS
