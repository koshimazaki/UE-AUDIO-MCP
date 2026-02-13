# StackOBot Audio System Analysis

**Source**: `/Volumes/Koshi_T7 1/UN5.3/StackOBot/` (UE 5.7)
**Exported**: 2026-02-12 via AudioMCP plugin

## Audio Asset Structure

```
Audio/
├── DATA/
│   ├── Attenuations/
│   │   ├── Attenuation_characters          (character close-range)
│   │   ├── Attenuation_characterswalking   (footstep-specific)
│   │   ├── Attenuation_general             (default)
│   │   └── Attenuation_general_large       (ambient/large sounds)
│   ├── ControlBus/
│   │   ├── StackOBot_GameParameter         (game state → audio)
│   │   ├── StackOBot_Music_Stop            (music stop control)
│   │   └── StackOBot_Music_WinLose         (win/lose state)
│   └── SoundClass/
│       ├── MUSIC
│       ├── SFX
│       └── SFX_charaters                   (character-specific SFX bus)
├── MetaSounds (6):
│   ├── MS_MonoArray          (CORE: reusable random-from-array player)
│   ├── MS_character_footsteps (PRESET of MS_MonoArray)
│   ├── MS_crateimpact         (PRESET of MS_MonoArray)
│   ├── MS_Coin               (single wave player + pitch)
│   ├── MS_DevCom             (single wave player + pitch)
│   └── MS_Jetpack            (3x wave player + ADSR + mixer)
├── MUSIC/
│   ├── MUS_Main_MSS          (SOURCE: 3-stem music, 40 nodes!)
│   ├── MUS_EQDelay_MSP       (PATCH: stereo EQ + delay effect)
│   └── Waves/ (6 music stems: perc, piano, strings, win, fail, start)
└── SFX/Waves/ (21 samples):
    ├── CO_Char_Step_Grass_01..10  (10 footstep variations)
    ├── CO_Char_Grab_Crate_01..03  (3 crate grab variations)
    ├── BugHit_01, ImpactGlass_01, ImpactPlaster_01
    ├── JetpackStart, JetpackLoop, JetpackEnd
    ├── SFX_Coin_Collect, SFX_Coin_Spawn
    ├── Chime_01, Objective_01, Plyr_Spawn_01
    ├── JumpPad_Whoosh_01, Whoosh_01
    ├── RingLoop_01, Wind_01
    └── ImpactGlassDebris_01, ImpactPlasterDebris_01
```

## MetaSounds Graph Details

### MS_MonoArray (Core Reusable Pattern)
**Type**: Source | **Interfaces**: Mono, Source, OneShot

The base pattern all one-shot SFX use. Picks random sample from array, applies random pitch.

```
Signal Flow:
  OnPlay ──→ RandomFloat(Min,Max) ──→ PitchShift ──┐
  OnPlay ──→ Random Get(WaveArray) ──→ WaveAsset ──┤
                                                     ├──→ Wave Player ──→ Mono Out
                                                     │                ──→ OnFinished
```

**Inputs**: OnPlay(Trigger), PitchMin(Float,-2.48), PitchMax(Float,1), WaveArray(WaveAsset:Array)
**DSP Nodes**: RandomFloat, Random Get (WaveAsset:Array), Wave Player (Mono)

### MS_character_footsteps (Preset of MS_MonoArray)
**Type**: Source, **Preset**: YES (inherits MS_MonoArray graph)

Overrides: PitchMin=-3, PitchMax=3, WaveArray=CO_Char_Step_Grass_01..10
Same graph as MS_MonoArray but with footstep-specific parameters.

### MS_crateimpact (Preset of MS_MonoArray)
Same pattern, different wave array (impact sounds).

### MS_Coin
**Type**: Source | Simple single-sample player

```
OnPlay → Wave Player (Stereo) → Right channel only → Mono Out
         PitchShift = 0.004
```

### MS_DevCom
Same as MS_Coin but PitchShift = 0.006. Developer commentary player.

### MS_Jetpack (Complex: 3-layer system)
**Type**: Source | 3 wave players + envelope

```
Signal Flow:
  OnPlay ──→ Wave Player 1 (start) ──→ OnFinished ──→ Wave Player 2 (loop, Loop=True)
                                                    ──→ ADSR Envelope (Attack=0.5, Sustain=1)
  JetpackOff ──→ Trigger Accumulate ──→ Wave Player 3 (end)

  ADSR.Envelope × Multiply(2.0) → Wave Player.PitchShift

  All 3 players → Audio Mixer (Mono, 3) → Mono Out
```

**Key**: Start-Loop-End pattern with ADSR modulating pitch during loop.
**Custom Input**: JetpackOff trigger (Blueprint sends this on jetpack deactivate)

### MUS_EQDelay_MSP (Stereo EQ+Delay Patch)
**Type**: Patch | Reusable stereo effect

```
In L/R → HPF → LPF → Band Splitter (2-band) → Mix with processed band
                                                 ↓ high band
                                         Stereo Delay (time, feedback)
                                                 ↓
                                         Final Mix → Out L/R
```

**Inputs**: Left, Right, HighPass(10), LowPass(20000), SplitterCrossover(600),
DelayTime(0.1), Feedback(0.05), DelayGain(1), MainGain(0), CrossoverMix(1)
**DSP**: 2×HPF, 2×LPF, 2×StereoMixer, BandSplitter, Subtract, StereoDelay

### MUS_Main_MSS (Full Music System — 40 nodes!)
**Type**: Source, Stereo | 3-stem interactive music

```
Architecture:
  4× Wave Players (Strings loop, Piano loop, Perc loop, String oneshot)
  3× MUS_EQDelay_MSP instances (per-stem processing)
  8× GetModulatorValue (Control Bus → per-stem volume/EQ)
  3× Trigger On Value Change (detect parameter changes)
  5× Clamp (threshold gates)
  4× Trigger Any (combine trigger sources)
  3× Trigger Delay (timed stem entries)
  4× Multiply (Audio×Float for volume)
  1× Audio Mixer (Stereo, 3) — final stem mix
  1× Audio Mixer (Stereo, 4) — processing mix
  1× ADSR Envelope (fade out, Release=2s)
  1× TriggerOnThreshold

Control Flow:
  StackOBot_GameParameter → GetModulatorValue → stem volumes
  StackOBot_Music_Stop → threshold trigger → ADSR release → fade out
  StackOBot_Music_WinLose → trigger change → play win/fail stems
```

**Key Pattern**: Control Bus modulation drives per-stem volumes and EQ.
Uses GetModulatorValue nodes to read ControlBus parameters at audio rate.

## Blueprint Triggering (BP_Bot)

Based on asset analysis (BP too complex for TCP scan):

### Footsteps
- **Animation**: `ABP_Bot` (Animation Blueprint)
- **Animations with footsteps**: A_Bot_Walk, A_Bot_Run, A_Bot_LandIdle, A_Bot_LandRun
- **Trigger**: AnimNotify in walk/run animations → SpawnSound → MS_character_footsteps
- **Attenuation**: Attenuation_characterswalking
- **SoundClass**: SFX_charaters
- **Samples**: CO_Char_Step_Grass_01..10 (10 variations, grass only — NO surface switching)

### Jetpack
- **Trigger**: BP_Bot gameplay logic → Play MS_Jetpack on jetpack activate
- **Stop**: BP_Bot sends JetpackOff trigger to MS_Jetpack
- **Pattern**: Start→Loop→End (3 wave files)

### Coins
- **Trigger**: Overlap event → SpawnSound → MS_Coin (SFX_Coin_Collect)
- **Spawn**: Level trigger → SFX_Coin_Spawn

### Crate Impact
- **Trigger**: Physics collision → SpawnSound → MS_crateimpact
- **Samples**: CO_Char_Grab_Crate_01..03 + Impact samples

### Music
- **Trigger**: Level load → MS_Main_MSS starts
- **Control**: StackOBot_GameParameter ControlBus drives stem volumes
- **Win/Lose**: StackOBot_Music_WinLose state triggers

## Surface Switching
**NO surface switching** — only grass footstep samples exist. Single surface type.
To add surface switching, you'd need:
1. Physical materials per surface (grass, concrete, metal, etc.)
2. Line trace from foot bone → detect surface material
3. Switch the Wave Array input on MS_character_footsteps per surface

## Key Patterns for Koshi Creature Mapping

1. **MonoArray Pattern**: Reusable random-from-array + pitch randomization. Use as base for any one-shot SFX.
2. **Preset System**: MS_character_footsteps is a PRESET of MS_MonoArray. Same graph, different params. This is the recommended UE5 pattern for variations.
3. **Start-Loop-End**: Jetpack pattern. Useful for any continuous creature sound (breathing, movement, growl).
4. **Control Bus Modulation**: Music system reads game state via GetModulatorValue. Use for creature aggression level, distance-based behavior, etc.
5. **AnimNotify → SpawnSound**: Standard footstep trigger. Place notifies in walk/run animations at foot contact frames.
