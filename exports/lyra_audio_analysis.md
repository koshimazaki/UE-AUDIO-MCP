# Lyra Audio System Analysis

**Source**: `/Volumes/Koshi_T7 1/UN5.3/Lyra2/LyraStarterGame/` (UE 5.3)
**Exported**: 2026-02-12 via AudioMCP plugin
**Total MetaSounds**: 90 (45 Sources, 3 Source presets, 22 Patches, 20 Source presets)

## Audio Asset Structure

```
Audio/
├── MetaSounds/ (65 assets — core library)
│   ├── sfx_Random_nl_meta              (CORE: mono random-from-array player)
│   ├── sfx_RandomStereo_nl_meta        (CORE: stereo random-from-array player)
│   ├── sfx_RandomWLimitedRangeLayer    (random + distance-gated layer)
│   ├── sfx_Character_FS_Base           (CORE: footstep base graph)
│   ├── sfx_Character_FS_Concrete       (wrapper → FS_Base with concrete samples)
│   ├── sfx_Character_FS_Glass          (wrapper → FS_Base with glass samples)
│   ├── sfx_Character_Land_Concrete     (wrapper → FS_Base with landing samples)
│   ├── sfx_Character_Land_Glass        (wrapper → FS_Base with landing samples)
│   ├── sfx_ImpactPlaster               (2-layer impact: main + distance-gated)
│   ├── sfx_ImpactDefault_Preset        (preset of ImpactPlaster)
│   ├── sfx_ImpactGlass_Preset          (preset of ImpactPlaster)
│   ├── sfx_ImpactCharacter_Preset      (preset of Random with distance layer)
│   ├── sfx_Character_DamageGiven       (stereo hit confirm)
│   ├── sfx_Character_DamageTaken       (stereo damage receive)
│   ├── sfx_Character_DamageGivenKill   (kill confirm)
│   ├── sfx_Character_DamageGivenWeakSpot (headshot confirm)
│   ├── sfx_Character_DamageTakenWeakSpot (headshot receive)
│   ├── sfx_Character_RespawnTimer      (procedural countdown, 53 nodes)
│   ├── sfx_WhizBys                     (3× whiz-by layers + stereo pan, 39 nodes)
│   ├── sfx_Weapon_SemiAutomatic        (4-layer gunshot, 56 nodes)
│   ├── sfx_Weapon_FullyAutomatic_lp    (auto-fire system, 131 nodes!)
│   ├── sfx_Weapon_GrenadeExplosion     (4-layer explosion, 42 nodes)
│   ├── sfx_Weapon_GrenadeImpact        (bounce + sub-bass, 40 nodes)
│   ├── sfx_Weapon_MeleeImpact          (simple stereo melee)
│   ├── sfx_CapturePoint_Progress       (procedural objective, 44 nodes)
│   ├── sfx_Amb_Wind_lp                 (procedural wind, 71 nodes!)
│   ├── sfx_Amb_Teleport_lp             (procedural teleport ambient, 52 nodes)
│   ├── sfx_Amb_WeaponPad_lp            (synth weapon pad loop, 49 nodes)
│   ├── sfx_InventoryPad_lp             (random-looping inventory)
│   ├── sfx_Interactable_JumpPad        (2-layer jump pad)
│   ├── mx_System                       (FULL MUSIC SYSTEM, 220 nodes!)
│   │
│   ├── lib_DovetailClip                (CORE PATCH: gapless wave player)
│   ├── lib_DovetailClipFromArray       (CORE PATCH: array version of above)
│   ├── lib_StereoBalance               (PATCH: L/R balance)
│   ├── lib_RandInterpTo                (PATCH: random smooth interpolation)
│   ├── lib_RandPanStereo               (PATCH: random stereo panning)
│   ├── lib_TriggerAfter                (PATCH: trigger after N events)
│   ├── lib_TriggerEvery                (PATCH: trigger every N events)
│   ├── lib_TriggerModulo               (PATCH: trigger on modulo count)
│   ├── lib_TriggerStopAfter            (PATCH: stop after N triggers)
│   ├── lib_WhizBy                      (PATCH: oncoming+receding crossfade)
│   ├── mx_Stingers                     (PATCH: 6-stem stinger mixer)
│   ├── mx_PlayAmbientElement           (PATCH: random ambient element)
│   ├── mx_PlayAmbientChord             (PATCH: 2-element chord player)
│   └── MS_Graph_RandomPitch_Stereo     (PATCH: random + pitch shift stereo)
│
├── Sounds/
│   ├── UI/
│   │   ├── ButtonHover                 (procedural: Square + MIDI, 21 nodes)
│   │   ├── ButtonClick                 (procedural: synth click, 30 nodes)
│   │   ├── sfx_UI_Lobby_Highlight/Select_Preset    (preset of RandomStereo)
│   │   ├── sfx_UI_MainMenu_Highlight/Select_Preset
│   │   └── sfx_UI_SubMenu_Highlight/Select/Back_Preset
│   ├── Weapons/
│   │   ├── MS_GatedWavePlayer          (CORE PATCH: triggered wave player)
│   │   ├── MS_WavePlayerCrossfader     (PATCH: 3-distance crossfade, 55 nodes)
│   │   ├── MS_WaveArrayCrossfader      (PATCH: array-based distance crossfade)
│   │   ├── MS_EqualPowerCrossfade      (PATCH: math utility)
│   │   ├── MS_LowAmmoTone             (PATCH: procedural low-ammo warning)
│   │   ├── MS_RandomEQ                (PATCH: 8-band random EQ, 45 nodes)
│   │   ├── MS_StereoGain              (PATCH: stereo gain utility)
│   │   ├── MS_StereoHighShelf         (PATCH: stereo shelf filter)
│   │   ├── Pistol/MSS_Weapons_Pistol_Fire      (92 nodes)
│   │   ├── Rifle/MSS_Weapons_Rifle_Fire        (117 nodes)
│   │   ├── Rifle2/MSS_Weapons_Rifle2_Fire      (138 nodes)
│   │   ├── Shotgun/MSS_Weapons_Shotgun_Fire    (129 nodes)
│   │   └── Explosions/MSS_Explosions_Grenade   (91 nodes)
│   └── Presets (20 — sfx_*_Preset inheriting base graphs)
```

## Core Reusable MetaSounds Patterns

### 1. Random-From-Array (sfx_Random_nl_meta) — Base for all one-shots

```
Signal Flow:
  OnPlay ──→ RandomFloat(Min,Max) ──→ PitchShift ──┐
  OnPlay ──→ Random Get(WaveArray) ──→ WaveAsset ──┤
                                                     ├──→ Wave Player ──→ Mono Out
  Gain ──→ Multiply ─────────────────────────────────┘    └──→ OnFinished
```

**Inputs**: OnPlay(Trigger), Sounds(WaveAsset:Array), Min(Float,-2), Max(Float,2), Gain(Float,1)
**Used by**: 20+ presets for UI, weapons, impacts, movement

### 2. Footstep Base (sfx_Character_FS_Base_nl_meta) — Surface-aware footsteps

```
Signal Flow:
  OnPlay ──→ RandomFloat ──→ MS_GatedWavePlayer(Footsteps) ──┐
  OnPlay ──→ TriggerDelay ──→ MS_GatedWavePlayer(Foley) ─────┤
                                                               ├──→ Audio Mixer (Mono,2) ──→ Out
  Footstep Gain ──→ GatedPlayer1.Amplitude                    │
  Foley Gain(0.1) ──→ GatedPlayer2.Amplitude ─────────────────┘
```

**Key**: Two layers — primary footstep + delayed foley at 10% volume.
Per-surface wrappers (FS_Concrete, FS_Glass, Land_Concrete, Land_Glass) just feed different WaveAsset:Arrays.

### 3. Multi-Layer Impact (sfx_ImpactPlaster_nl_meta) — Distance-aware impacts

```
Signal Flow:
  OnPlay ──→ TriggerDelay(MainDelayTime) ──→ MS_Graph_RandomPitch(MainSounds) ──┐
  OnPlay ──→ TriggerDelay(LayerDelayTime) ──→ MS_Graph_RandomPitch(LayerSounds) ─┤
  UE.Attenuation.Distance ──→ MapRange(LayerMinRange,LayerMaxRange) ──→ Multiply ┘
                                                                          └──→ Audio Mixer (Mono,2) ──→ Out
```

**Key**: Layer volume scales with distance via `UE.Attenuation.Distance` interface input.
Close = main layer dominant. Far = layer fades in.

### 4. Semi-Auto Weapon (sfx_Weapon_SemiAutomatic_nl_meta) — 4-layer gunshot

```
Architecture (56 nodes):
  Layer 1: MainLayer      → Random Get → Wave Player (immediate)
  Layer 2: ReportLayer    → Random Get → Wave Player (delayed, AD Envelope attack)
  Layer 3: DryClickLayer  → Random Get → Wave Player (short pre-delay)
  Layer 4: SubLayer       → Sine oscillator + ADSR envelope (procedural sub-bass)
           SubBaseFrequency(40Hz) + SubMaxFrequencyMod(440) + SubFrequencyModTime(0.125)

  All 4 layers → Audio Mixer (Stereo,4) → Stereo Out
```

**Key**: Procedural sub-bass layer uses Sine + frequency sweep + ADSR. No sample needed.

### 5. Full-Auto Weapon (sfx_Weapon_FullyAutomatic_lp_meta) — 131 nodes

```
Architecture:
  DryClick → Wave Player (onset only, TriggerSequence gate)
  MainLayer → 2× Wave Player (alternating via TriggerSequence)
  SecondaryLayer → Wave Player (sweetener, random offset)
  AutoClick → Wave Player (mechanical click per shot)
  MainTail → Wave Player (decay tail on stop)
  SubLayer → Procedural sub (same pattern as semi-auto)

  TriggerRepeat(1/ShotsPerSecond) → drives all per-shot triggers
  OnStop → triggers tail + stops repeat
  All → Decibels to Linear Gain (6×) → per-layer levels
  Final mix → Audio Mixer (Stereo,6) → Stereo Out
```

**Key**: `ShotsPerSecond` input drives fire rate. Two alternating main players for gapless looping.

### 6. Weapon Fire — AAA Pattern (MSS_Weapons_Rifle_Fire) — 117 nodes

```
Architecture:
  Punch-Close, Punch-Distant, Punch-Far → MS_WavePlayerCrossfader (distance-based)
  Mech → MS_GatedWavePlayer
  Noise-Interior-Close, Noise-Interior-Distant → MS_WavePlayerCrossfader
  NoiseTail → MS_GatedWavePlayer (on stop)

  Per-shot trigger: Fire → TriggerToggle gate → TriggerRepeat(Period)
  OnStop → stop repeat, trigger tail

  Post-processing per layer:
    MS_RandomEQ (random 8-band per shot)
    One-Pole HPF (distance filtering)
    Compressor (2× parallel)
    MS_HomeMadeShelf
    MS_StereoGain (FinalGain)

  Variables: track fire state, toggle per-shot
  Final: Audio Mixer (Stereo,8) → Stereo Out
```

**Key patterns**:
- **MS_WavePlayerCrossfader**: 3-distance crossfade (close/distant/far) with equal-power curve
- **MS_RandomEQ**: 8-band random EQ variation per shot (avoids repetition)
- **MS_LowAmmoTone**: Procedural triangle-wave warning when MagazineAmmo is low
- **PawnSeed**: Per-pawn random seed so different characters sound different

### 7. Grenade Explosion (MSS_Explosions_Grenade) — 91 nodes

```
Layers (6 distance-crossfaded):
  Punch-Close / Punch-Distant → MS_WaveArrayCrossfader
  Noise-Exterior-Close / Noise-Exterior-Distant → MS_WaveArrayCrossfader
  Noise-Interior-Close / Noise-Interior-Distant (scaled by IndoorFactor)
  SFX layer, Ricochet layer

  Post: MS_HomeMadeShelf + MS_StereoGain
  Final: Audio Mixer (Stereo,8) → Out
```

### 8. Procedural Wind (sfx_Amb_Wind_lp_meta) — 71 nodes

```
Architecture:
  3× Noise generators → One-Pole HPF/LPF (modulated cutoffs)
  Cutoff modulation: Noise → SampleAndHold → InterpTo (7× smooth interps)
  Wind input + PawnSpeed → MapRange → filter cutoffs
  LFO → amplitude modulation
  lib_StereoBalance for L/R panning
```

**Key**: Entirely procedural — no wave files. Wind parameter + PawnSpeed drive filter cutoffs.

### 9. Procedural UI (ButtonHover / ButtonClick) — Pure synthesis

```
ButtonHover (21 nodes):
  NoteBase → MIDI To Frequency → 2× Square oscillators
  AD Envelopes (2×) → amplitude shaping
  Ladder Filter → tonal shaping
  Sound Length → envelope duration

ButtonClick (30 nodes):
  Square + Sine → State Variable Filter → Delay (2×)
  4× AD Envelopes for layered transients
  Noise → WaveShaper → crunch layer
  LFO modulation
```

**Key**: Zero wave assets. All synthesis from oscillators + envelopes + filters.

### 10. Music System (mx_System) — 220 nodes!

```
Architecture:
  14× lib_DovetailClipFromArray (gapless stem players)
  7× lib_DovetailClip (single wave players)
  7× lib_RandPanStereo (random stereo spread)
  5× lib_RandInterpTo (smooth random parameter changes)
  5× lib_TriggerEvery (rhythmic trigger patterns)
  3× lib_TriggerAfter (delayed starts)
  2× mx_PlayAmbientChord (ambient harmony)
  16 graph variables + 19 variable accessors

  Stems: perc-deep, perc-light, plips, bass, long-pad, short-pad, wet-lead
  Menu variants: menu.perc-deep, menu.perc-light, menu.chords, etc.

  Control:
    Intensity input → per-stem gain scaling via Variables
    bIsMenu → switches between combat/menu stem sets
    LookDir → stereo positioning
    Metronome → drives trigger timing
    MasterVolume → final output level
    OnStingerPositive → mx_Stingers (6-stem stinger)

  Final: Audio Mixer (Stereo,7) → Audio Mixer (Stereo,8) → Stereo Out
```

**Key**: DovetailClip pattern provides gapless playback by alternating two Wave Players
with overlapping tails. The music is generative — stems trigger probabilistically,
not a fixed arrangement.

## Patch Library Summary

| Patch | Purpose | Nodes |
|-------|---------|-------|
| MS_GatedWavePlayer | Triggered random wave player | 21 |
| MS_WavePlayerCrossfader | 3-distance crossfade with equal power | 55 |
| MS_WaveArrayCrossfader | Array-based distance crossfade | 29 |
| MS_EqualPowerCrossfade | Math: equal power curve | 7 |
| MS_RandomEQ | Random 8-band EQ per trigger | 45 |
| MS_LowAmmoTone | Procedural warning tone | 16 |
| MS_StereoGain | Simple stereo gain | 10 |
| MS_StereoHighShelf | Stereo high shelf filter | 12 |
| MS_Graph_RandomPitch_Stereo | Random pitch + stereo player | 18 |
| MS_Graph_TriggerDelayPitchShift_Mono | Delayed + pitch shifted mono | 20 |
| lib_DovetailClip | Gapless wave player (2× alternating) | 27 |
| lib_DovetailClipFromArray | Array version of DovetailClip | 16 |
| lib_StereoBalance | L/R balance control | 14 |
| lib_RandInterpTo | Random smooth interpolation | 12 |
| lib_RandPanStereo | Random stereo panning | 9 |
| lib_TriggerAfter | Trigger after N events | 8 |
| lib_TriggerEvery | Trigger every N events | 8 |
| lib_TriggerModulo | Trigger on modulo count | 11 |
| lib_TriggerStopAfter | Stop after N triggers | 8 |
| lib_WhizBy | Oncoming+receding bullet pass | 28 |
| mx_Stingers | 6-stem musical stinger | 34 |
| mx_PlayAmbientElement | Random ambient element player | 18 |
| mx_PlayAmbientChord | 2-element chord player | 20 |

## Blueprint Triggering

Lyra uses a **ContextEffects** system (not direct Blueprint audio calls):

1. **AnimNotify_LyraContextEffects** placed on foot-contact frames in animations
2. AnimNotify performs line trace downward to detect physical surface
3. `ULyraContextEffectComponent` on character converts surface type to GameplayTag
4. `ULyraContextEffectsSubsystem` looks up matching library entries
5. `UGameplayStatics::SpawnSoundAttached()` plays the matched MetaSounds

See `/Users/radek/Documents/GIthub/UE5-WWISE/research/lyra_audio_patterns.md` for full C++ code.

## Comparison: Lyra vs StackOBot

| Aspect | StackOBot | Lyra |
|--------|-----------|------|
| MetaSounds count | 8 | 90 |
| Max graph complexity | 40 nodes (music) | 220 nodes (music) |
| Surface switching | None (grass only) | Full (concrete, glass, per-surface libs) |
| Weapon system | None | 4 weapon types, distance crossfade, per-pawn seed |
| Procedural audio | Minimal (jetpack ADSR) | Extensive (wind, UI, capture point, respawn) |
| Music architecture | 3-stem, ControlBus volumes | Generative, DovetailClip, probabilistic stems |
| Footstep pattern | MS_MonoArray preset | FS_Base (2-layer: step + foley) per surface |
| Reusable patches | 0 | 23 (lib_*, MS_*, mx_*) |
| Triggering | Direct SpawnSound | Tag-based ContextEffects system |
| Mix control | ControlBus (3 buses) | ControlBus (5 buses) + HDR/LDR + LoadingScreen |

## Key Patterns for Implementation

1. **DovetailClip**: Gapless playback via 2 alternating Wave Players with overlapped tails. Essential for music stems.
2. **WavePlayerCrossfader**: 3-distance crossfade (close/distant/far) with equal-power curves. Standard for any spatialized one-shot.
3. **RandomEQ**: 8-band random EQ per trigger eliminates repetition in rapid-fire sounds. Apply to any fast-repeating SFX.
4. **FS_Base 2-layer**: Always pair primary sample with a quieter foley layer (cloth rustle, gear jingle) delayed by ~50ms.
5. **Sub-bass synthesis**: For impacts/gunshots, add a Sine oscillator with frequency sweep + ADSR. No sample needed.
6. **Tag-based dispatch**: Use GameplayTags for all effect lookup. Avoids switch statements, fully data-driven.
7. **Patch library**: Build reusable patches (gain, filter, crossfade, trigger utilities) and compose complex graphs from them.
