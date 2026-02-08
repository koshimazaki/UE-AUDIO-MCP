# Blueprint Audio Interaction Patterns — Lyra + Stack-O-Bot

## Overview
Analysis of two Epic reference projects to identify audio interaction patterns for the UE5-WWISE MCP scanner.
- **Lyra**: C++ + GAS + GameplayTags (AAA pattern)
- **Stack-O-Bot**: Blueprint-only + MetaSounds (indie pattern)

## Architecture Comparison

| Aspect | Lyra (AAA) | Stack-O-Bot (Indie) |
|--------|------------|---------------------|
| Source | C++ + Blueprints | Blueprint-only |
| Audio routing | GameplayTags → Context Effects Library | Direct MetaSounds patches |
| Footsteps | AnimNotify → line trace → PhysMat → tag → audio | MS_character_footsteps → wave randomization |
| Weapons | GAS ability → AnimNotify → hit trace → surface tag | N/A |
| Mix control | 5 SoundControlBuses + Audio Modulation | 3 Sound Classes + Control Bus |
| Interaction | IInteractableTarget + GAS abilities | BPC_InteractionHandler central router |
| Impact | PhysMat → GameplayTag → Context Effects | MS_crateimpact → velocity modulation |
| Music | Bus-based stems | MetaSounds stems + state crossfade |
| Spawning | PlaySoundAtLocation (direct) | One-shot at spawn point |
| UI | Common UI framework audio | PlaySound2D on widget events |

## Pattern 1: Footsteps

### Lyra Implementation
- **Class**: `UAnimNotify_LyraContextEffects` (C++)
- **File**: `Source/LyraGame/Feedback/ContextEffects/AnimNotify_LyraContextEffects.h/cpp`
- **Flow**: AnimNotify → optional line trace → PhysicalMaterial → GameplayTag → ContextEffectsLibrary.GetEffects() → SpawnSoundAttached
- **Audio params**: VolumeMultiplier, PitchMultiplier per notify
- **Surface detection**: Line trace to ground, physical material check

### Stack-O-Bot Implementation
- **Asset**: `MS_character_footsteps` (MetaSounds Patch)
- **Waves**: `CO_Char_Step_Grass_01` through `_10` (randomized selection)
- **Attenuation**: `Attenuation_characterswalking`
- **Sound Class**: `SFX_charaters`

### Scanner Detection
- Look for: AnimNotify subclasses, PlaySound/SpawnSound near movement logic
- Look for: MetaSounds patches with "footstep" or "step" in name
- Look for: PhysicalMaterial references near audio calls

## Pattern 2: Weapon Fire

### Lyra Implementation
- **Class**: `ULyraGameplayAbility_RangedWeapon`
- **File**: `Source/LyraGame/Weapons/LyraGameplayAbility_RangedWeapon.h/cpp`
- **Flow**: ActivateAbility → fire animation → AnimNotify at muzzle frame → WeaponTrace → FHitResult.PhysMat → context tag → muzzle sound + impact sound
- **Fire blocking**: `TAG_WeaponFireBlocked` GameplayTag
- **Impact**: bReturnPhysicalMaterial=true on traces

### Scanner Detection
- Look for: GAS abilities with weapon/fire/shoot in name
- Look for: AnimNotify on fire/attack montages
- Look for: Line/sweep traces with bReturnPhysicalMaterial
- Look for: InputAction with fire/shoot/attack naming

## Pattern 3: Reverb / Room Audio

### Lyra Implementation
- **Class**: `ULyraAudioMixEffectsSubsystem` (WorldSubsystem)
- **File**: `Source/LyraGame/Audio/LyraAudioMixEffectsSubsystem.h/cpp`
- **Buses**: Overall, Music, SoundFX, Dialogue, VoiceChat
- **Features**: HDR/LDR submix effect chain switching, loading screen mix
- **Settings**: `ULyraAudioSettings` with default ControlBusMix path

### Stack-O-Bot Implementation
- **Attenuation profiles**: 4 (characters, characterswalking, general, general_large)
- **Sound classes**: 3 (MUSIC, SFX, SFX_charaters)
- **Control bus**: StackOBot_GameParameter, Music_Stop, Music_WinLose

### Scanner Detection
- Look for: AudioVolume actors in levels
- Look for: ReverbEffect/SoundAttenuation assets
- Look for: SoundControlBus/SoundControlBusMix references
- Look for: OnComponentBeginOverlap on trigger volumes

## Pattern 4: Interaction

### Lyra Implementation
- **Interface**: `IInteractableTarget`
- **Ability**: `ULyraGameplayAbility_Interact`
- **Detection**: Line trace from player → find interactable → GAS ability activation
- **Audio**: Via GameplayMessage broadcasts

### Stack-O-Bot Implementation
- **Central handler**: `BPC_InteractionHandler` component
- **Types**: Coin pickup (OnOverlap), pressure plate (OnHit), portal (OnOverlap)
- **Audio**: MS_Coin, grab crate waves, chime

### Scanner Detection
- Look for: IInteractableTarget or Interact interfaces
- Look for: OnBeginOverlap on pickup/collectible actors
- Look for: InteractionComponent or InteractionHandler patterns

## Pattern 5: Impact / Collision

### Lyra Implementation
- **Source**: Weapon traces with PhysicalMaterial
- **Flow**: FHitResult → EPhysicalSurface → GameplayTag → Context Effects → audio
- **Variety**: Material-dependent (metal, wood, flesh, glass, etc.)

### Stack-O-Bot Implementation
- **Asset**: `MS_crateimpact` (MetaSounds Patch)
- **Waves**: Impact_01, ImpactGlass_01, ImpactPlaster_01 + debris variants
- **Trigger**: OnComponentHit → velocity-based volume/pitch
- **BPs**: BP_Crate, BP_DestructiblePlatform, BP_Balance

### Scanner Detection
- Look for: OnComponentHit/OnHit delegates
- Look for: GetVelocity near audio calls (velocity-based modulation)
- Look for: PhysicalMaterial checks near impact handling

## Pattern 6: Spawning

### Lyra Implementation
- **Class**: `ALyraWeaponSpawner`
- **Events**: PlayPickupEffects(), PlayRespawnEffects() (BlueprintNativeEvent)
- **Audio**: `UGameplayStatics::PlaySoundAtLocation(PickupSound/RespawnSound)`
- **Trigger**: OnOverlapBegin → weapon pickup, cooldown timer → respawn

### Stack-O-Bot Implementation
- **BP**: BP_SpawnPad
- **Wave**: Plyr_Spawn_01
- **Trigger**: Spawn event → one-shot at location

### Scanner Detection
- Look for: SpawnActor calls near PlaySound
- Look for: Respawn/Spawn events with audio references
- Look for: OnRep_ replication callbacks with effects

## Pattern 7: UI Audio

### Lyra Implementation
- **Class**: `ULyraActivatableWidget` (extends CommonUI)
- **Framework**: Common UI plugin provides audio dispatch
- **Trigger**: OnClicked delegates, widget activation/deactivation

### Stack-O-Bot Implementation
- **Waves**: Chime_01, Objective_01, RingLoop_01
- **Trigger**: HUD widget OnClicked events
- **Delivery**: PlaySound2D (non-spatial)

### Scanner Detection
- Look for: UUserWidget subclasses with audio references
- Look for: OnClicked/OnHovered delegates near PlaySound2D
- Look for: CommonUI plugin usage

## Pattern 8: Music / State Transitions

### Lyra Implementation
- **System**: SoundControlBusMix for volume, submix chains for effects
- **HDR/LDR**: Dynamic range adaptation via submix preset switching

### Stack-O-Bot Implementation
- **Assets**: MUS_Main_MSS (MetaSounds), MUS_EQDelay_MSP (preset)
- **Stems**: Piano, Strings, Perc (separate wave files)
- **Control**: Music_Stop, Music_WinLose control bus params
- **Trigger**: Game state changes (playing/win/lose) → crossfade

### Scanner Detection
- Look for: SoundControlBusMix references
- Look for: Game state enums near audio transitions
- Look for: MetaSounds patches with MUS_ prefix

## Context Effects System (Lyra-specific, AAA pattern)

The key architectural insight from Lyra:

```
AnimNotify fires
  → Line trace (optional)
  → Physical surface detected
  → GameplayTag built: "Effect.Footstep" + "Context.Surface.Metal"
  → ContextEffectsLibrary.GetEffects(Effect, Context)
  → Returns: TArray<USoundBase*> + TArray<UNiagaraSystem*>
  → SpawnSoundAttached(Sound, MeshComp, Socket, Location, Volume, Pitch)
```

**Key classes**:
- `ULyraContextEffectsSubsystem` — manages per-actor effect libraries
- `ULyraContextEffectComponent` — component that implements the interface
- `ULyraContextEffectsLibrary` — data asset mapping tags → effects
- `ILyraContextEffectsInterface` — interface for effect execution

This is the AAA pattern our scanner should recognize and our builder should replicate.

## Node Type Detection Summary

| UE5 Node/Class | Indicates | Audio System |
|----------------|-----------|-------------|
| `AnimNotify` subclass | Animation-driven audio | Footsteps, weapon fire |
| `OnComponentBeginOverlap` | Zone entry | Reverb, ambience |
| `OnComponentHit` | Physics collision | Impact sounds |
| `InputAction` (Enhanced Input) | Player action | Weapon fire, abilities |
| `GameplayAbility` activation | GAS ability | Weapons, interaction |
| `PlaySoundAtLocation` | Direct audio playback | Any one-shot |
| `SpawnSoundAttached` | Attached audio | Movement, character |
| `PlaySound2D` | Non-spatial audio | UI sounds |
| `SoundControlBus` reference | Mix control | Volume settings |
| `MetaSounds` patch reference | Procedural audio | Any complex sound |
| `PhysicalMaterial` check | Surface detection | Footsteps, impacts |
| `GameplayTag` + ContextEffects | Tag-driven routing | AAA pattern (any) |
| `OnRep_` replication | Networked events | Spawning, state changes |

## Blueprint Assets Inventory

### Stack-O-Bot MetaSounds (6)
- MS_character_footsteps, MS_Coin, MS_Jetpack, MS_crateimpact, MS_DevCom, MS_MonoArray

### Stack-O-Bot SFX Waves (32)
- Footsteps: 10, Grab: 3, Impact: 7, Jetpack: 3, Coin: 2, UI: 4, Movement: 3

### Stack-O-Bot Attenuation (4)
- characters, characterswalking, general, general_large

### Stack-O-Bot Sound Classes (3)
- MUSIC, SFX, SFX_charaters

### Stack-O-Bot Control Bus (3)
- GameParameter, Music_Stop, Music_WinLose

### Lyra Audio Files (C++)
- Audio subsystem: 4 files
- Context effects: 10 files
- Weapons: 14 files
- Character: 16 files
- Interaction: 17 files
- Settings: 3 files
