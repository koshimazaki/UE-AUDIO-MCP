# Lyra Audio Triggering Patterns — C++ Reference

**Source**: UE 5.3 LyraStarterGame (`Source/LyraGame/`)
**Scope**: Context Effects (surface-aware SFX), Audio Mix (Control Bus), AnimNotify pipeline

---

## Class Hierarchy

```
UDeveloperSettings
├── ULyraContextEffectsSettings     → EPhysicalSurface → GameplayTag mapping
└── ULyraAudioSettings              → Control Bus/Mix soft references, HDR/LDR chains

UWorldSubsystem
├── ULyraContextEffectsSubsystem    → Per-actor library management, SpawnContextEffects()
└── ULyraAudioMixEffectsSubsystem   → Control Bus activation, HDR/LDR switching

UObject
├── ULyraContextEffectsLibrary      → Data asset: EffectTag + Context → Sounds/Niagara
└── ULyraActiveContextEffects       → Runtime cache of loaded effects

UActorComponent
└── ULyraContextEffectComponent     → Implements ILyraContextEffectsInterface, per-character

UAnimNotify
└── UAnimNotify_LyraContextEffects  → Animation-driven trigger, line trace, surface detection

UInterface
└── ILyraContextEffectsInterface    → AnimMotionEffect() contract
```

---

## Flow: AnimNotify to SpawnSound

### Step 1: AnimNotify fires during animation playback

```cpp
// UAnimNotify_LyraContextEffects::Notify()
void UAnimNotify_LyraContextEffects::Notify(
    USkeletalMeshComponent* MeshComp,
    UAnimSequenceBase* Animation,
    const FAnimNotifyEventReference& EventReference)
{
    AActor* OwningActor = MeshComp->GetOwner();

    // Optional line trace for surface detection
    if (bPerformTrace)
    {
        FVector TraceStart = bAttached
            ? MeshComp->GetSocketLocation(SocketName)
            : MeshComp->GetComponentLocation();

        World->LineTraceSingleByChannel(
            HitResult, TraceStart,
            TraceStart + TraceProperties.EndTraceLocationOffset,
            TraceProperties.TraceChannel, QueryParams);
    }

    // Find all objects implementing ILyraContextEffectsInterface
    // (checks both the Actor and its Components)
    TArray<UObject*> LyraContextEffectImplementingObjects;
    if (OwningActor->Implements<ULyraContextEffectsInterface>())
        LyraContextEffectImplementingObjects.Add(OwningActor);
    for (const auto Component : OwningActor->GetComponents())
        if (Component->Implements<ULyraContextEffectsInterface>())
            LyraContextEffectImplementingObjects.Add(Component);

    // Dispatch to each implementor
    for (UObject* Obj : LyraContextEffectImplementingObjects)
    {
        ILyraContextEffectsInterface::Execute_AnimMotionEffect(Obj,
            SocketName, Effect, MeshComp,
            LocationOffset, RotationOffset, Animation,
            bHitSuccess, HitResult, Contexts,
            VFXProperties.Scale,
            AudioProperties.VolumeMultiplier,
            AudioProperties.PitchMultiplier);
    }
}
```

**Key AnimNotify properties** (set per-notify in animation editor):
- `Effect` (FGameplayTag) — e.g. `Context.Footstep`, `Context.Land`
- `bPerformTrace` — enables surface detection
- `bAttached` / `SocketName` — bone attachment
- `TraceProperties.TraceChannel` — default ECC_Visibility
- `TraceProperties.EndTraceLocationOffset` — trace direction/length
- `AudioProperties.VolumeMultiplier`, `AudioProperties.PitchMultiplier`

### Step 2: ContextEffectComponent receives the call

```cpp
// ULyraContextEffectComponent::AnimMotionEffect_Implementation()
void ULyraContextEffectComponent::AnimMotionEffect_Implementation(
    const FName Bone, const FGameplayTag MotionEffect,
    USceneComponent* StaticMeshComponent,
    const FVector LocationOffset, const FRotator RotationOffset,
    const UAnimSequenceBase* AnimationSequence,
    const bool bHitSuccess, const FHitResult HitResult,
    FGameplayTagContainer Contexts,
    FVector VFXScale, float AudioVolume, float AudioPitch)
{
    FGameplayTagContainer TotalContexts;
    TotalContexts.AppendTags(Contexts);
    TotalContexts.AppendTags(CurrentContexts);  // per-component defaults

    // Surface type → GameplayTag conversion
    if (bConvertPhysicalSurfaceToContext)
    {
        UPhysicalMaterial* PhysMat = HitResult.PhysMaterial.Get();
        EPhysicalSurface SurfType = PhysMat->SurfaceType;

        const ULyraContextEffectsSettings* Settings = GetDefault<ULyraContextEffectsSettings>();
        if (const FGameplayTag* Tag = Settings->SurfaceTypeToContextMap.Find(SurfType))
            TotalContexts.AddTag(*Tag);
    }

    // Delegate to world subsystem
    ULyraContextEffectsSubsystem* Sub = World->GetSubsystem<ULyraContextEffectsSubsystem>();
    Sub->SpawnContextEffects(GetOwner(), StaticMeshComponent, Bone,
        LocationOffset, RotationOffset, MotionEffect, TotalContexts,
        AudioComponents, NiagaraComponents, VFXScale, AudioVolume, AudioPitch);
}
```

**Component properties**:
- `bConvertPhysicalSurfaceToContext` — auto surface→tag conversion
- `DefaultEffectContexts` (FGameplayTagContainer) — always-present tags
- `DefaultContextEffectsLibraries` (TSet<TSoftObjectPtr>) — which libraries to use

### Step 3: Subsystem looks up libraries and spawns effects

```cpp
void ULyraContextEffectsSubsystem::SpawnContextEffects(
    const AActor* SpawningActor, USceneComponent* AttachToComponent,
    const FName AttachPoint, const FVector LocationOffset,
    const FRotator RotationOffset, FGameplayTag Effect,
    FGameplayTagContainer Contexts,
    TArray<UAudioComponent*>& AudioOut,
    TArray<UNiagaraComponent*>& NiagaraOut,
    FVector VFXScale, float AudioVolume, float AudioPitch)
{
    // Find actor's registered library set
    ULyraContextEffectsSet* EffectsLibraries = ActiveActorEffectsMap[SpawningActor];

    TArray<USoundBase*> TotalSounds;
    for (ULyraContextEffectsLibrary* Lib : EffectsLibraries->LyraContextEffectsLibraries)
    {
        TArray<USoundBase*> Sounds;
        Lib->GetEffects(Effect, Contexts, Sounds, NiagaraSystems);
        TotalSounds.Append(Sounds);
    }

    // Spawn each matched sound
    for (USoundBase* Sound : TotalSounds)
    {
        UAudioComponent* AC = UGameplayStatics::SpawnSoundAttached(
            Sound, AttachToComponent, AttachPoint,
            LocationOffset, RotationOffset,
            EAttachLocation::KeepRelativeOffset,
            false,            // bStopWhenAttachedToDestroyed
            AudioVolume,
            AudioPitch,
            0.0f,             // StartTime
            nullptr,          // Attenuation
            nullptr,          // Concurrency
            true);            // bAutoDestroy
        AudioOut.Add(AC);
    }
}
```

### Step 4: Library matching logic (tag-based)

```cpp
void ULyraContextEffectsLibrary::GetEffects(
    const FGameplayTag Effect, const FGameplayTagContainer Context,
    TArray<USoundBase*>& Sounds, TArray<UNiagaraSystem*>& NiagaraSystems)
{
    for (const auto& ActiveEffect : ActiveContextEffects)
    {
        // Exact tag match for effect type AND all context tags must match
        if (Effect.MatchesTagExact(ActiveEffect->EffectTag)
            && Context.HasAllExact(ActiveEffect->Context)
            && (ActiveEffect->Context.IsEmpty() == Context.IsEmpty()))
        {
            Sounds.Append(ActiveEffect->Sounds);
            NiagaraSystems.Append(ActiveEffect->NiagaraSystems);
        }
    }
}
```

**Matching rules**:
- Effect tag must be an **exact** match (not hierarchical)
- Context tags use **HasAllExact** — all tags in the library entry must be present
- Empty context in library matches only empty context in query (and vice versa)

---

## Surface Type Mapping System

### Configuration (ULyraContextEffectsSettings — UDeveloperSettings)

```cpp
UCLASS(config = Game, defaultconfig, meta = (DisplayName = "LyraContextEffects"))
class ULyraContextEffectsSettings : public UDeveloperSettings
{
    // Maps engine EPhysicalSurface enum to GameplayTags
    UPROPERTY(config, EditAnywhere)
    TMap<TEnumAsByte<EPhysicalSurface>, FGameplayTag> SurfaceTypeToContextMap;
};
```

**Typical mappings** (configured in Project Settings > LyraContextEffects):
```
SurfaceType_Default  → Context.Surface.Default
SurfaceType1         → Context.Surface.Concrete
SurfaceType2         → Context.Surface.Glass
SurfaceType3         → Context.Surface.Metal
SurfaceType4         → Context.Surface.Wood
SurfaceType5         → Context.Surface.Dirt
SurfaceType6         → Context.Surface.Water
```

### Physical Material setup required:
1. Create Physical Materials with Surface Type set (e.g. PM_Concrete → SurfaceType1)
2. Assign Physical Materials to static mesh collision
3. Configure `SurfaceTypeToContextMap` in Project Settings
4. Library data assets define per-surface sound sets

### Library data asset structure (FLyraContextEffects):

```cpp
USTRUCT(BlueprintType)
struct FLyraContextEffects
{
    FGameplayTag EffectTag;                  // e.g. "Context.Footstep"
    FGameplayTagContainer Context;           // e.g. "Context.Surface.Concrete"
    TArray<FSoftObjectPath> Effects;         // Sounds + Niagara (soft refs)
};
```

Each library asset contains an array of these entries. Example:
```
Library: LIB_PlayerFootsteps
├── EffectTag=Footstep, Context={Concrete} → [footstep_concrete_01..05]
├── EffectTag=Footstep, Context={Glass}    → [footstep_glass_01..05]
├── EffectTag=Footstep, Context={Metal}    → [footstep_metal_01..03]
├── EffectTag=Land,     Context={Concrete} → [land_concrete_01..03]
└── EffectTag=Land,     Context={Glass}    → [land_glass_01..02]
```

---

## Control Bus Mixing System

### ULyraAudioSettings (configured in Project Settings)

```cpp
UCLASS(config = Game, defaultconfig, meta = (DisplayName = "LyraAudioSettings"))
class ULyraAudioSettings : public UDeveloperSettings
{
    // Bus Mixes
    FSoftObjectPath DefaultControlBusMix;        // base mix, always active
    FSoftObjectPath LoadingScreenControlBusMix;   // ducking during load
    FSoftObjectPath UserSettingsControlBusMix;     // player volume prefs

    // Individual Control Buses (linked to user settings)
    FSoftObjectPath OverallVolumeControlBus;
    FSoftObjectPath MusicVolumeControlBus;
    FSoftObjectPath SoundFXVolumeControlBus;
    FSoftObjectPath DialogueVolumeControlBus;
    FSoftObjectPath VoiceChatVolumeControlBus;

    // HDR/LDR submix effect chains
    TArray<FLyraSubmixEffectChainMap> HDRAudioSubmixEffectChain;
    TArray<FLyraSubmixEffectChainMap> LDRAudioSubmixEffectChain;
};
```

### LyraAudioMixEffectsSubsystem — lifecycle

```
Initialize()     → Load all soft references from LyraAudioSettings
PostInitialize() → Load bus mixes, control buses, HDR/LDR chains
                   Register with LoadingScreenManager
OnWorldBeginPlay()→ Activate DefaultBaseMix
                   Activate UserMix with saved volume levels
                   Apply HDR or LDR effect chains
```

### Key API calls for bus mixing

```cpp
// Activate a mix (additive)
UAudioModulationStatics::ActivateBusMix(World, DefaultBaseMix);

// Create a mix stage with specific volume
FSoundControlBusMixStage Stage =
    UAudioModulationStatics::CreateBusMixStage(World, ControlBus, Volume);

// Update a mix with new stages
TArray<FSoundControlBusMixStage> Stages = { Overall, Music, SFX, Dialogue, VoiceChat };
UAudioModulationStatics::UpdateMix(World, UserMix, Stages);

// Deactivate a mix
UAudioModulationStatics::DeactivateBusMix(World, LoadingScreenMix);

// HDR/LDR submix effect chain override
UAudioMixerBlueprintLibrary::SetSubmixEffectChainOverride(
    World, Submix, EffectChain, 0.1f /*FadeTime*/);
UAudioMixerBlueprintLibrary::ClearSubmixEffectChainOverride(
    World, Submix, 0.1f);
```

---

## Replicating for a Custom Creature/Character

### Minimal setup (4 classes + data assets):

**1. Context Effect Component (add to creature Blueprint)**
```cpp
// On the creature Blueprint, add ULyraContextEffectComponent
// Configure:
//   bConvertPhysicalSurfaceToContext = true
//   DefaultEffectContexts = {Context.Creature.TypeA}  // creature-specific tag
//   DefaultContextEffectsLibraries = {LIB_CreatureFootsteps, LIB_CreatureVocals}
```

**2. Animation Notifies (place in animation montages)**
```
Walk animation:   AnimNotify_LyraContextEffects
                    Effect = "Context.Footstep"
                    bPerformTrace = true
                    TraceProperties.EndTraceLocationOffset = (0, 0, -50)
                    SocketName = "foot_l" / "foot_r"
                    bAttached = true

Attack animation: AnimNotify_LyraContextEffects
                    Effect = "Context.Attack"
                    bPerformTrace = false
                    SocketName = "claw_r"
```

**3. Library data assets (one per sound category)**
```
LIB_CreatureFootsteps:
├── EffectTag=Footstep, Context={Surface.Concrete} → [creature_step_concrete_01..05]
├── EffectTag=Footstep, Context={Surface.Dirt}     → [creature_step_dirt_01..05]
└── EffectTag=Footstep, Context={Surface.Metal}    → [creature_step_metal_01..03]

LIB_CreatureVocals:
├── EffectTag=Attack,  Context={}                  → [creature_attack_01..03]
├── EffectTag=Hurt,    Context={}                  → [creature_hurt_01..04]
└── EffectTag=Death,   Context={}                  → [creature_death_01..02]
```

**4. Surface mapping (one-time project setup)**
```
Project Settings > LyraContextEffects:
  SurfaceType1 → Context.Surface.Concrete
  SurfaceType2 → Context.Surface.Dirt
  SurfaceType3 → Context.Surface.Metal
  SurfaceType4 → Context.Surface.Glass
```

### Component lifecycle:

```
BeginPlay()
  └→ ContextEffectsSubsystem->LoadAndAddContextEffectsLibraries(Owner, Libraries)
       └→ For each library: LoadSynchronous() → LoadEffects() → cache in ActiveActorEffectsMap

AnimNotify fires
  └→ Notify() → line trace → get surface → Execute_AnimMotionEffect()
       └→ Component::AnimMotionEffect_Implementation()
            └→ Aggregate contexts (defaults + surface tag)
                 └→ Subsystem::SpawnContextEffects()
                      └→ Library::GetEffects(tag, contexts) → match
                           └→ SpawnSoundAttached() per matched sound

EndPlay()
  └→ ContextEffectsSubsystem->UnloadAndRemoveContextEffectsLibraries(Owner)
```

---

## Key UE5 APIs Used

| API | Purpose |
|-----|---------|
| `UGameplayStatics::SpawnSoundAttached()` | Spawn sound at bone/socket with volume/pitch |
| `UNiagaraFunctionLibrary::SpawnSystemAttached()` | Spawn VFX at bone/socket |
| `World->LineTraceSingleByChannel()` | Surface detection trace |
| `UAudioModulationStatics::ActivateBusMix()` | Activate a Control Bus Mix |
| `UAudioModulationStatics::CreateBusMixStage()` | Create a bus stage with volume |
| `UAudioModulationStatics::UpdateMix()` | Update bus mix stages |
| `UAudioModulationStatics::DeactivateBusMix()` | Remove a bus mix |
| `UAudioMixerBlueprintLibrary::SetSubmixEffectChainOverride()` | Apply submix effect chain |
| `GetDefault<ULyraContextEffectsSettings>()` | Access project settings singleton |
| `FGameplayTag::MatchesTagExact()` | Exact tag comparison for effect lookup |
| `FGameplayTagContainer::HasAllExact()` | All-tags-present check for context matching |
| `TSoftObjectPtr::LoadSynchronous()` | Synchronous asset load from soft reference |

---

## Design Patterns Summary

1. **Tag-based dispatch** — GameplayTags for both effect type and context, no hardcoded enums
2. **Interface decoupling** — AnimNotify does not know about the component; uses `ILyraContextEffectsInterface`
3. **World Subsystem as registry** — actor-to-library mapping lives in `ULyraContextEffectsSubsystem`
4. **Soft references everywhere** — libraries, bus mixes, control buses all use FSoftObjectPath/TSoftObjectPtr
5. **Additive context** — component defaults + per-notify contexts + surface tag all merge
6. **Data-driven** — no code changes needed to add new surfaces, effects, or creatures
7. **Dual output** — same library entry can produce both Sound and Niagara (audio+VFX from one trigger)
8. **HDR/LDR switching** — submix effect chain overrides swap the entire mastering chain at runtime
