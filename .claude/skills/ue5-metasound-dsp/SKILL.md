---
name: ue5-metasound-dsp
description: MetaSounds DSP specialist for Unreal Engine 5. Use when designing MetaSounds graphs, choosing DSP nodes, configuring filters/oscillators/envelopes, building signal chains, working with the Builder API, or creating audio templates.
allowed-tools: Read, Grep, Glob
argument-hint: "[dsp-task-or-question]"
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

## Finding Nodes and Pins

- Look nodes up in the engine-synced catalogue, `src/ue_audio_mcp/knowledge/metasound_catalogue.json`, or with the `ms_search_nodes` and `ms_node_info` tools. They give the class name (e.g. `UE::Biquad Filter::Audio`) and the exact, typed pin names that `connect` expects.
- With the editor running, `list_node_classes` (TCP) lists everything the engine has registered, including plugin nodes.
- The Builder API is experimental: node classes and pins can change between UE versions, so re-sync the catalogue after an engine upgrade (`scripts/update_catalogue_pins.py`).
- `WaveAsset` inputs need a real imported sound in the project's Content folder.

## Node Categories

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

## Key Pin Names

From the engine-synced catalogue. Use `ms_node_info` for any other node.

| Node | Inputs | Outputs |
|------|--------|---------|
| Sine / Saw / Triangle | Enabled, Bi Polar, Frequency, Modulation, Sync, Phase Offset, Glide, Type | Audio |
| Square | Enabled, Bi Polar, Frequency, Modulation, Sync, Phase Offset, Glide, Type, Pulse Width | Audio |
| Noise | Seed, Type | Audio |
| AD Envelope (Audio/Float) | Trigger, Attack Time, Decay Time, Attack Curve, Decay Curve, Looping, Hard Reset | On Trigger, On Done, Out Envelope |
| ADSR Envelope (Audio/Float) | Trigger Attack, Trigger Release, Attack Time, Decay Time, Sustain Level, Release Time, Attack Curve, Decay Curve, Release Curve, Hard Reset | On Attack Triggered, On Decay Triggered, On Sustain Triggered, On Release Triggered, On Done, Out Envelope |
| Biquad Filter | In, Cutoff Frequency, Bandwidth, Gain, Type | Out |
| State Variable Filter | Cutoff Frequency, Resonance, In, Band Stop Control | Band Pass, Low Pass Filter, High Pass Filter, Band Stop |
| Wave Player (Mono) | Play, Stop, Wave Asset, Start Time, Pitch Shift, Loop, Loop Start, Loop Duration, Maintain Audio Sync | On Play, On Finished, On Nearly Finished, On Looped, On Cue Point, Cue Point ID, Cue Point Label, Loop Percent, Playback Location, Playback Time, Out Mono |
| Multiply / Add (Audio) | PrimaryOperand, AdditionalOperands | Out |
| Map Range (Float) | In, In Range A, In Range B, Out Range A, Out Range B, Clamped | Out Value |
| InterpTo | Interp Time, Target | Value |
| Clamp (Float) | In, Min, Max | Value |
| Compressor | Bypass, Audio, Ratio, Threshold dB, Attack Time, Release Time, Lookahead Time, Knee, Sidechain, Envelope Mode, Analog Mode, Upwards Mode, Wet/Dry | Audio, Gain Envelope |
| ITD Panner | In, Angle, Distance Factor, Head Width | Out Left, Out Right |
| Trigger Repeat | Start, Stop, Period, Num Repeats | RepeatOut |
| Trigger Sequence | In, Reset, Loop | Out 0, Out 1 |

## Builder API Functions

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
- Float→Audio connections are invalid. To scale audio by a float, use `Multiply (Audio by Float)`
- Pin names from Epic docs may use shorthand — always verify against the catalogue (`ms_node_info`)
- Node class names: use display names from knowledge DB, or full `Namespace::Name::Variant` for direct lookup

## Source Files

- Node catalogue: `src/ue_audio_mcp/knowledge/metasound_catalogue.json` (engine-synced) and `metasound_nodes.py`
- Templates: `src/ue_audio_mcp/templates/metasounds/`
- Graph schema and validator: `src/ue_audio_mcp/knowledge/graph_schema.py`
- Tools: `src/ue_audio_mcp/tools/metasounds.py` (catalogue search), `ms_graph.py` (templates, validation), `ms_builder.py` (live Builder API)

$ARGUMENTS
