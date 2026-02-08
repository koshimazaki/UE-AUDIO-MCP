# UE 5.7 MetaSounds Builder API Research Summary

_Generated: 2026-02-08 | Sources: 15+_

<key-points>
- UMetaSoundBuilderSubsystem inherits from UEngineSubsystem -- access via GEngine->GetEngineSubsystem<UMetaSoundBuilderSubsystem>(), NOT a static Get()
- CreateSourceBuilder returns the builder + OnPlay/OnFinished/AudioOut handles via out-params
- Audition() takes (UObject* Parent, UAudioComponent*, FOnCreateAuditionGeneratorHandleDelegate, bool bLiveUpdatesEnabled)
- AddNodeByClassName takes FMetasoundFrontendClassName + int32 MajorVersion (defaults to 1)
- BuildNewMetaSound(FName NameBase) returns TScriptInterface<IMetaSoundDocumentInterface>
- Header file is MetasoundBuilderSubsystem.h in MetasoundEngine module
- FMetaSoundNodeHandle/FMetaSoundBuilderNodeInputHandle/FMetaSoundBuilderNodeOutputHandle defined in MetasoundBuilderBase.h
- MetasoundFrontendSearchEngine.h existence unconfirmed for 5.7 -- may be internal/removed
</key-points>

---

## 1. UMetaSoundBuilderSubsystem Access

<details>

### Class Hierarchy

```
UObject
  -> USubsystem
    -> UDynamicSubsystem
      -> UEngineSubsystem
        -> UMetaSoundBuilderSubsystem
```

- **Plugin**: Metasound
- **Module**: MetasoundEngine
- **Header**: `MetasoundBuilderSubsystem.h`

### How to Access in C++

Since it is an **Engine Subsystem** (not an Editor or World subsystem), the correct access pattern is:

```cpp
#include "MetasoundBuilderSubsystem.h"

UMetaSoundBuilderSubsystem* BuilderSS = GEngine->GetEngineSubsystem<UMetaSoundBuilderSubsystem>();
```

### IMPORTANT: Our Current Code Uses `UMetaSoundBuilderSubsystem::Get()`

Our plugin at line 49 of `AudioMCPBuilderManager.cpp` currently calls:
```cpp
UMetaSoundBuilderSubsystem* BuilderSubsystem = UMetaSoundBuilderSubsystem::Get();
```

**This may or may not compile** depending on UE version. Some Epic subsystems provide a static `Get()` convenience method, but the standard UE pattern for engine subsystems is `GEngine->GetEngineSubsystem<T>()`. If the code compiles, Epic likely provides a static helper. If not, switch to the GEngine pattern.

### Verification Status

- Python API confirms: `Bases: EngineSubsystem` (from UE 5.7 docs)
- Standard UE5 access: `GEngine->GetEngineSubsystem<UMetaSoundBuilderSubsystem>()`
- Source code header: `MetasoundBuilderSubsystem.h` (confirmed)

</details>

---

## 2. CreateSourceBuilder Signature

<details>

### Python API Signature (UE 5.7)

```python
create_source_builder(
    builder_name: Name,
    output_format: MetaSoundOutputAudioFormat = MONO,
    is_one_shot: bool = True
) -> tuple(
    MetaSoundSourceBuilder,               # The builder
    on_play_node_output: MetaSoundBuilderNodeOutputHandle,
    on_finished_node_input: MetaSoundBuilderNodeInputHandle,
    audio_out_node_inputs: Array[MetaSoundBuilderNodeInputHandle],
    out_result: MetaSoundBuilderResult
)
```

### C++ Signature (inferred from Python + Blueprint API)

```cpp
UMetaSoundSourceBuilder* UMetaSoundBuilderSubsystem::CreateSourceBuilder(
    FName BuilderName,
    FMetaSoundBuilderNodeOutputHandle& OnPlayOutput,
    FMetaSoundBuilderNodeInputHandle& OnFinishedInput,
    TArray<FMetaSoundBuilderNodeInputHandle>& AudioOutInputs,
    EMetaSoundBuilderResult& OutResult,
    EMetaSoundOutputAudioFormat OutputFormat = EMetaSoundOutputAudioFormat::Mono,
    bool bIsOneShot = true
);
```

### EMetaSoundOutputAudioFormat

An enum controlling audio output channel format. Known values:
- `Mono` (default)
- `Stereo`
- Possibly `FiveDotOne`, `SevenDotOne` etc.

### bIsOneShot Behavior

- `true` (default): The OnFinished graph output is connected, allowing the MetaSound to signal playback completion. Suitable for fire-and-forget sounds.
- `false`: For continuous/looping playback. The OnFinished handle may be invalid.

### Our Current Code

Our code at line 66 uses the correct pattern:
```cpp
Builder = BuilderSubsystem->CreateSourceBuilder(
    FName(*Name),
    OnPlayOutput,
    OnFinishedInput,
    AudioOutInputs,
    Result,
    EMetaSoundOutputAudioFormat::Mono,
    false /* bIsOneShot = false for continuous playback */);
```

**Status: LIKELY CORRECT** -- matches the API shape from documentation.

</details>

---

## 3. Audition Signature

<details>

### Python API Signature (UE 5.7)

```python
MetaSoundSourceBuilder.audition(
    parent: Object,
    audio_component: AudioComponent,
    on_create_generator: OnCreateAuditionGeneratorHandleDelegate,
    live_updates_enabled: bool = False
) -> None
```

### C++ Signature (inferred)

```cpp
void UMetaSoundSourceBuilder::Audition(
    UObject* Parent,
    UAudioComponent* AudioComponent,
    FOnCreateAuditionGeneratorHandleDelegate OnCreateGenerator,
    bool bLiveUpdatesEnabled = false
);
```

### FOnCreateAuditionGeneratorHandleDelegate

- **Type**: DECLARE_DYNAMIC_DELEGATE (Blueprint-compatible delegate)
- **Header**: Likely defined in `MetasoundSourceBuilder.h` or `MetasoundBuilderSubsystem.h`
- **Purpose**: Called when the audition generator handle is created, allowing you to interact with the `UMetasoundGeneratorHandle` for real-time parameter updates
- **Can be empty/unbound**: Our code passes an unbound delegate, which is valid

### How Audition Works Internally

Based on documentation and forum analysis:

1. **Audition does NOT simply call SetSound() + Play()** on the AudioComponent
2. Instead, it:
   a. Builds the transient MetaSound from the builder's current state
   b. Registers it as a unique class in the MetaSound Node Registry
   c. Creates a `UMetaSoundSource` object from the built graph
   d. Sets it on the AudioComponent via SetSound()
   e. Calls Play() on the AudioComponent
   f. If `bLiveUpdatesEnabled = true`, establishes a live link so subsequent builder changes (AddNode, Connect, etc.) are hot-patched into the playing audio with buffer crossfade

### AudioComponent Setup Requirements

```cpp
UAudioComponent* AudioComp = NewObject<UAudioComponent>(World->GetWorldSettings());
AudioComp->bIsUISound = true;            // Non-spatial
AudioComp->bAllowSpatialization = false;
AudioComp->bAutoDestroy = true;
AudioComp->SetVolumeMultiplier(1.0f);
AudioComp->RegisterComponent();           // REQUIRED -- must be registered
```

**Key insight**: The AudioComponent MUST be registered (`RegisterComponent()`) before passing to Audition. An unregistered component will silently fail.

### Our Current Code

```cpp
FOnCreateAuditionGeneratorHandleDelegate EmptyDelegate;
SourceBuilder->Audition(World, AudioComp, EmptyDelegate, bLiveUpdatesRequested);
```

**Status: CORRECT pattern**. The delegate is optional (empty is fine).

**Potential issue**: We create the AudioComponent but don't store it in `AuditionAudioComponent` (the TStrongObjectPtr member). If GC collects it during playback, audio stops. We should assign it.

</details>

---

## 4. AddNodeByClassName

<details>

### C++ Signature (from UE 5.7 API docs)

Two overloads:

```cpp
// Overload 1 (primary)
FMetaSoundNodeHandle UMetaSoundBuilderBase::AddNodeByClassName(
    const FMetasoundFrontendClassName& ClassName,
    int32 MajorVersion,
    EMetaSoundBuilderResult& OutResult
);

// Overload 2 (convenience -- MajorVersion after Result)
FMetaSoundNodeHandle UMetaSoundBuilderBase::AddNodeByClassName(
    const FMetasoundFrontendClassName& ClassName,
    EMetaSoundBuilderResult& OutResult,
    int32 MajorVersion = 1
);
```

### FMetasoundFrontendClassName Construction

```cpp
// Three-part class name: Namespace, Name, Variant
FMetasoundFrontendClassName ClassName(
    FName("UE"),           // Namespace
    FName("Sine"),         // Name
    FName("Audio")         // Variant
);

// Two-part (no variant):
FMetasoundFrontendClassName ClassName(FName("UE"), FName("Sine"));

// Constructors:
FMetasoundFrontendClassName();                              // Default
FMetasoundFrontendClassName(FName Namespace, FName Name);   // Two-part
FMetasoundFrontendClassName(FName Namespace, FName Name, FName Variant);  // Three-part
```

### Our Current Code

Our code at line 292 calls:
```cpp
FMetaSoundNodeHandle NodeHandle = ActiveBuilder.Get()->AddNodeByClassName(ParsedClassName, Result);
```

**WARNING**: This passes only 2 parameters (`ClassName, Result`), which matches overload 2 with default `MajorVersion = 1`. This should work but verify the overload exists in UE 5.7 -- the API docs show both overloads.

### How to Discover Node Class Names

Hold **Shift** while hovering over a node's name in the MetaSound Editor to see a debug tooltip with the full class name (e.g., `UE::Sine::Audio`).

</details>

---

## 5. BuildNewMetaSound

<details>

### C++ Signature (from UE 5.7 API docs)

```cpp
TScriptInterface<IMetaSoundDocumentInterface> UMetaSoundBuilderBase::BuildNewMetaSound(
    FName NameBase
) const;
```

### Behavior

- Creates a **transient** (in-memory) MetaSound by copying the underlying MetaSound managed by the builder
- Registers it with the MetaSound Node Registry as a unique class
- If a MetaSound with `NameBase` already exists, auto-generates a unique name using `NameBase` as prefix
- Returns an `IMetaSoundDocumentInterface` -- the asset can be used as a node in other MetaSounds
- The returned object is NOT automatically saved to disk

### Build vs BuildNewMetaSound vs BuildAndOverwriteMetaSound

| Method | Creates New? | Registers? | Persists? |
|--------|-------------|------------|-----------|
| `Build(Parent, Options)` | Soft deprecated | ? | ? |
| `BuildNewMetaSound(NameBase)` | Yes, transient copy | Yes, unique class | No (in-memory) |
| `BuildAndOverwriteMetaSound(Existing, bForce)` | No, overwrites | Optional | If asset was persistent |

### Our Current Code

```cpp
TScriptInterface<IMetaSoundDocumentInterface> BuiltMetaSound = ActiveBuilder.Get()->BuildNewMetaSound(FName(*Name));
```

**Status: CORRECT** -- matches the documented API.

</details>

---

## 6. Required Includes and Module Dependencies

<details>

### Build.cs Module Dependencies

```csharp
PublicDependencyModuleNames.AddRange(new string[]
{
    "Core",
    "CoreUObject",
    "Engine",
    "MetasoundEngine",    // UMetaSoundBuilderSubsystem, UMetaSoundSourceBuilder, UMetaSoundBuilderBase
    "MetasoundFrontend",  // FMetasoundFrontendClassName, FMetasoundFrontendLiteral, IMetaSoundDocumentInterface
    "MetasoundGraphCore", // FMetaSoundNodeHandle, underlying graph types
});
```

**Reference**: The RNBOMetasound plugin (Cycling74) uses:
- Public: `MetasoundFrontend`, `MetasoundGraphCore`, `MetasoundStandardNodes`, `MetasoundEngine`
- Private: `CoreUObject`, `Engine`, `SignalProcessing`

### Header Includes Map

| Class/Type | Header | Module |
|-----------|--------|--------|
| `UMetaSoundBuilderSubsystem` | `MetasoundBuilderSubsystem.h` | MetasoundEngine |
| `UMetaSoundSourceBuilder` | `MetasoundSourceBuilder.h` (likely) | MetasoundEngine |
| `UMetaSoundBuilderBase` | `MetasoundBuilderBase.h` | MetasoundEngine |
| `FMetasoundFrontendClassName` | `MetasoundFrontendDocument.h` | MetasoundFrontend |
| `FMetasoundFrontendLiteral` | `MetasoundFrontendDocument.h` | MetasoundFrontend |
| `IMetaSoundDocumentInterface` | `MetasoundDocumentInterface.h` | MetasoundFrontend |
| `UMetaSoundSource` | `MetasoundSource.h` | MetasoundEngine |
| `EMetaSoundBuilderResult` | `MetasoundBuilderBase.h` | MetasoundEngine |
| `EMetaSoundOutputAudioFormat` | `MetasoundBuilderSubsystem.h` or `MetasoundOutputFormatInterfaces.h` | MetasoundEngine |
| `FMetaSoundNodeHandle` | `MetasoundBuilderBase.h` | MetasoundEngine |
| `FMetaSoundBuilderNodeInputHandle` | `MetasoundBuilderBase.h` | MetasoundEngine |
| `FMetaSoundBuilderNodeOutputHandle` | `MetasoundBuilderBase.h` | MetasoundEngine |
| `FOnCreateAuditionGeneratorHandleDelegate` | `MetasoundSourceBuilder.h` (likely) | MetasoundEngine |
| `UMetasoundGeneratorHandle` | `MetasoundGeneratorHandle.h` | MetasoundEngine |

### Our Current Includes

```cpp
#include "MetasoundBuilderSubsystem.h"
#include "MetasoundSource.h"
#include "MetasoundDocumentInterface.h"
#include "MetasoundFrontendDocument.h"
#include "Interfaces/MetasoundOutputFormatInterfaces.h"  // EMetaSoundOutputAudioFormat
```

And in the header:
```cpp
#include "MetasoundFrontendDocument.h"   // FMetasoundFrontendClassName
#include "MetasoundBuilderBase.h"        // FMetaSoundNodeHandle, handle types
```

**Status: APPEARS CORRECT** -- covers the main types we use.

</details>

---

## 7. MetasoundFrontendSearchEngine.h

<details>

### Status: UNCONFIRMED for UE 5.7

- No public documentation references `MetasoundFrontendSearchEngine.h` or `ISearchEngine::Get()`
- This appears to be an **internal/private** API that may have been:
  - Renamed in UE 5.5+
  - Moved to a different module
  - Deprecated/removed entirely
- The MetaSound Frontend module reorganized significantly between UE 5.3 and 5.5

### Alternative for Node Discovery

Instead of `ISearchEngine::Get()`, use the Builder API's own node resolution:
- `AddNodeByClassName()` -- knows all registered node classes
- The `MetaSoundBuilderSubsystem` itself can check `IsInterfaceRegistered()`
- Node class names discoverable via Shift+hover in MetaSound Editor

### Recommendation

**Do not depend on MetasoundFrontendSearchEngine.h**. Use `AddNodeByClassName` with known class names from our `NodeTypeMap` registry instead. This is what our current code does and is the documented/public API approach.

</details>

---

## 8. Handle Types and Their Headers

<details>

### All Three Handle Types

```cpp
// All defined in MetasoundBuilderBase.h (MetasoundEngine module)

// Opaque handle to a node in the builder graph
struct FMetaSoundNodeHandle { ... };

// Opaque handle to a specific input pin on a node
struct FMetaSoundBuilderNodeInputHandle { ... };

// Opaque handle to a specific output pin on a node
struct FMetaSoundBuilderNodeOutputHandle { ... };
```

### Usage Pattern

```cpp
// Add a node -- get a node handle
FMetaSoundNodeHandle NodeHandle = Builder->AddNodeByClassName(ClassName, Result);

// Find pins by name on that node
FMetaSoundBuilderNodeOutputHandle OutPin = Builder->FindNodeOutputByName(NodeHandle, FName("Audio"), Result);
FMetaSoundBuilderNodeInputHandle InPin = Builder->FindNodeInputByName(NodeHandle, FName("Frequency"), Result);

// Connect pins
Builder->ConnectNodes(OutPin, InPin, Result);

// Set defaults on input pins
Builder->SetNodeInputDefault(InPin, Literal, Result);
```

### Graph I/O Handles

Graph inputs return `FMetaSoundBuilderNodeOutputHandle` (they output into the graph).
Graph outputs return `FMetaSoundBuilderNodeInputHandle` (they receive from the graph).

This is correct in our code and matches the API.

</details>

---

## 9. Common Compilation Errors with MetaSounds Plugins

<details>

### Error 1: Missing Module Dependencies

```
error LNK2019: unresolved external symbol
```

**Fix**: Add `MetasoundEngine`, `MetasoundFrontend`, `MetasoundGraphCore` to Build.cs `PublicDependencyModuleNames`.

### Error 2: Editor-Only API in Runtime Code

```
error C2065: 'UMetaSoundEditorSubsystem': undeclared identifier
```

**Fix**: Some MetaSounds APIs are editor-only. Wrap with `#if WITH_EDITOR` or `#if WITH_EDITORONLY_DATA`.

### Error 3: MetaSound Headers Break Plugin Compilation

Forum reports that referencing MetaSound.h headers in custom plugin .cpp files can fail. The issue is typically missing module dependencies or include order problems.

**Fix**: Ensure Build.cs dependencies are in `PublicDependencyModuleNames` (not Private) if headers are exposed in your public API.

### Error 4: DuplicateObject Breaking Change (UE 5.4 -> 5.5)

```cpp
// Worked in UE 5.4:
UMetaSoundSource* NewSource = DuplicateObject<UMetaSoundSource>(OriginalMetasound);
// Broken in UE 5.5+
```

**Fix**: Use Builder API's `BuildNewMetaSound()` instead of `DuplicateObject`.

### Error 5: Shipping Build Fatal Errors

MetaSounds can crash in shipping builds if:
- Builder API is used at runtime (some parts are editor-only)
- `WITH_EDITORONLY_DATA` guards are missing
- Node registry is not fully initialized in packaged builds

**Fix**: Check all MetaSounds code paths are guarded for non-editor builds.

### Error 6: FMetasoundFrontendClassName Linker Errors

If using `FMetasoundFrontendClassName` without `MetasoundFrontend` module dependency:
```
error LNK2019: unresolved external symbol "class FMetasoundFrontendClassName::..."
```

**Fix**: Add `"MetasoundFrontend"` to Build.cs dependencies.

### Error 7: MetaSoundBuilderSubsystem::Get() Not Found

If UE 5.7 doesn't provide a static `Get()`:
```
error C2039: 'Get': is not a member of 'UMetaSoundBuilderSubsystem'
```

**Fix**: Use `GEngine->GetEngineSubsystem<UMetaSoundBuilderSubsystem>()` instead.

</details>

---

## 10. How Audition Actually Plays Audio

<details>

### Internal Flow

```
SourceBuilder->Audition(World, AudioComp, Delegate, bLiveUpdates)
    |
    v
1. Builds transient UMetaSoundSource from builder's graph state
2. Registers it in the MetaSound Node Registry as unique class
3. Internally calls AudioComp->SetSound(BuiltMetaSoundSource)
4. AudioComp->Play() is triggered
5. If bLiveUpdatesEnabled:
   - Establishes live link to builder
   - Future ConnectNodes/AddNode/SetDefault calls
     hot-patch the running audio with crossfade
6. If OnCreateGenerator delegate is bound:
   - Creates UMetasoundGeneratorHandle
   - Calls delegate with the handle for real-time parameter control
```

### Key Points

- **AudioComponent MUST be registered** (`RegisterComponent()` called) before Audition
- **AudioComponent should NOT already be playing** -- Audition manages playback
- **bAutoDestroy = true** means the component self-destructs when sound finishes (OneShot)
- **bIsUISound = true** is recommended for preview/audition (non-spatial)
- **Live Updates** allow topology changes (add/remove nodes, change connections) to be reflected in real-time with buffer crossfade -- this is the key differentiator from simply building and playing
- **Live Updates require**: `au.MetaSound.LiveUpdatesEnabled 1` cvar to be set globally, AND `bLiveUpdatesEnabled = true` passed to Audition

### GC Safety

If the AudioComponent is garbage collected during playback, audio stops silently. Solutions:
1. Store in `TStrongObjectPtr<UAudioComponent>` (what our header declares but cpp doesn't use)
2. Store as UPROPERTY() on a UObject
3. Add to root set temporarily

### Our Current Issue

Our code creates the AudioComponent but does NOT assign it to `AuditionAudioComponent`:
```cpp
// Creates AudioComp locally -- could be GC'd!
UAudioComponent* AudioComp = NewObject<UAudioComponent>(World->GetWorldSettings());
// Should add: AuditionAudioComponent.Reset(AudioComp);
```

</details>

---

## Complete UMetaSoundBuilderBase API Surface (UE 5.7)

<details>

### Node Management
| Method | Parameters | Returns |
|--------|-----------|---------|
| `AddNodeByClassName` | `FMetasoundFrontendClassName, int32 MajorVersion=1` | `FMetaSoundNodeHandle, EMetaSoundBuilderResult&` |
| `AddNode` | `TScriptInterface<IMetaSoundDocumentInterface>` | `FMetaSoundNodeHandle, EMetaSoundBuilderResult&` |
| `RemoveNode` | `FMetaSoundNodeHandle, bool bRemoveUnusedDeps=true` | `EMetaSoundBuilderResult&` |
| `ContainsNode` | `FMetaSoundNodeHandle` | `bool` |

### Graph I/O
| Method | Parameters | Returns |
|--------|-----------|---------|
| `AddGraphInputNode` | `FName, FName DataType, FMetasoundFrontendLiteral, bool bConstructor=false` | `FMetaSoundBuilderNodeOutputHandle, EMetaSoundBuilderResult&` |
| `AddGraphOutputNode` | `FName, FName DataType, FMetasoundFrontendLiteral, bool bConstructor=false` | `FMetaSoundBuilderNodeInputHandle, EMetaSoundBuilderResult&` |
| `RemoveGraphInput` | `FName` | `EMetaSoundBuilderResult&` |
| `RemoveGraphOutput` | `FName` | `EMetaSoundBuilderResult&` |
| `FindGraphInputNode` | `FName` | `FMetaSoundNodeHandle, FName, FMetaSoundBuilderNodeOutputHandle, EMetaSoundBuilderResult&` |
| `FindGraphOutputNode` | `FName` | `FMetaSoundNodeHandle, FName, FMetaSoundBuilderNodeInputHandle, EMetaSoundBuilderResult&` |
| `GetGraphInputNames` | none | `TArray<FName>, EMetaSoundBuilderResult&` |
| `GetGraphOutputNames` | none | `TArray<FName>, EMetaSoundBuilderResult&` |
| `SetGraphInputDefault` | `FName, FMetasoundFrontendLiteral` | `EMetaSoundBuilderResult&` |
| `GetGraphInputDefault` | `FName` | `FMetasoundFrontendLiteral, EMetaSoundBuilderResult&` |
| `SetGraphInputName` | `FName, FName NewName` | `EMetaSoundBuilderResult&` |
| `SetGraphOutputName` | `FName, FName NewName` | `EMetaSoundBuilderResult&` |
| `SetGraphInputDataType` | `FName, FName DataType` | `EMetaSoundBuilderResult&` |
| `SetGraphOutputDataType` | `FName, FName DataType` | `EMetaSoundBuilderResult&` |
| `SetGraphInputAccessType` | `FName, EMetasoundFrontendVertexAccessType` | `EMetaSoundBuilderResult&` |
| `SetGraphOutputAccessType` | `FName, EMetasoundFrontendVertexAccessType` | `EMetaSoundBuilderResult&` |

### Graph Variables (UE 5.5+)
| Method | Parameters | Returns |
|--------|-----------|---------|
| `AddGraphVariable` | `FName, FName DataType, FMetasoundFrontendLiteral` | `EMetaSoundBuilderResult&` |
| `AddGraphVariableGetNode` | `FName` | `FMetaSoundNodeHandle, EMetaSoundBuilderResult&` |
| `AddGraphVariableSetNode` | `FName` | `FMetaSoundNodeHandle, EMetaSoundBuilderResult&` |
| `AddGraphVariableGetDelayedNode` | `FName` | `FMetaSoundNodeHandle, EMetaSoundBuilderResult&` |
| `RemoveGraphVariable` | `FName` | `EMetaSoundBuilderResult&` |
| `GetGraphVariableDefault` | `FName` | `FMetasoundFrontendLiteral, EMetaSoundBuilderResult&` |

### Connections
| Method | Parameters | Returns |
|--------|-----------|---------|
| `ConnectNodes` | `FMetaSoundBuilderNodeOutputHandle, FMetaSoundBuilderNodeInputHandle` | `EMetaSoundBuilderResult&` |
| `DisconnectNodes` | `FMetaSoundBuilderNodeOutputHandle, FMetaSoundBuilderNodeInputHandle` | `EMetaSoundBuilderResult&` |
| `DisconnectNodeInput` | `FMetaSoundBuilderNodeInputHandle` | `EMetaSoundBuilderResult&` |
| `DisconnectNodeOutput` | `FMetaSoundBuilderNodeOutputHandle` | `EMetaSoundBuilderResult&` |
| `ConnectNodesByInterfaceBindings` | `FMetaSoundNodeHandle, FMetaSoundNodeHandle` | `EMetaSoundBuilderResult&` |
| `ConnectNodeOutputToGraphOutput` | `FName, FMetaSoundBuilderNodeOutputHandle` | `EMetaSoundBuilderResult&` |
| `ConnectNodeInputToGraphInput` | `FName, FMetaSoundBuilderNodeInputHandle` | `EMetaSoundBuilderResult&` |
| `NodesAreConnected` | `FMetaSoundBuilderNodeOutputHandle, FMetaSoundBuilderNodeInputHandle` | `bool` |

### Node Pin Queries
| Method | Parameters | Returns |
|--------|-----------|---------|
| `FindNodeInputByName` | `FMetaSoundNodeHandle, FName` | `FMetaSoundBuilderNodeInputHandle, EMetaSoundBuilderResult&` |
| `FindNodeOutputByName` | `FMetaSoundNodeHandle, FName` | `FMetaSoundBuilderNodeOutputHandle, EMetaSoundBuilderResult&` |
| `FindNodeInputs` | `FMetaSoundNodeHandle` | `TArray<FMetaSoundBuilderNodeInputHandle>, EMetaSoundBuilderResult&` |
| `FindNodeOutputs` | `FMetaSoundNodeHandle` | `TArray<FMetaSoundBuilderNodeOutputHandle>, EMetaSoundBuilderResult&` |
| `SetNodeInputDefault` | `FMetaSoundBuilderNodeInputHandle, FMetasoundFrontendLiteral` | `EMetaSoundBuilderResult&` |
| `GetNodeInputDefault` | `FMetaSoundBuilderNodeInputHandle` | `FMetasoundFrontendLiteral, EMetaSoundBuilderResult&` |
| `RemoveNodeInputDefault` | `FMetaSoundBuilderNodeInputHandle` | `EMetaSoundBuilderResult&` |
| `NodeInputIsConnected` | `FMetaSoundBuilderNodeInputHandle` | `bool` |
| `NodeOutputIsConnected` | `FMetaSoundBuilderNodeOutputHandle` | `bool` |

### Interfaces
| Method | Parameters | Returns |
|--------|-----------|---------|
| `AddInterface` | `FName` | `EMetaSoundBuilderResult&` |
| `RemoveInterface` | `FName` | `EMetaSoundBuilderResult&` |
| `InterfaceIsDeclared` | `FName` | `bool` |
| `FindInterfaceInputNodes` | `FName` | `TArray<FMetaSoundNodeHandle>, EMetaSoundBuilderResult&` |
| `FindInterfaceOutputNodes` | `FName` | `TArray<FMetaSoundNodeHandle>, EMetaSoundBuilderResult&` |

### Build Operations
| Method | Parameters | Returns |
|--------|-----------|---------|
| `BuildNewMetaSound` | `FName NameBase` | `TScriptInterface<IMetaSoundDocumentInterface>` |
| `BuildAndOverwriteMetaSound` | `TScriptInterface<IMetaSoundDocumentInterface>, bool bForceUnique=false` | void |
| `ConvertToPreset` | `TScriptInterface<IMetaSoundDocumentInterface>` | `EMetaSoundBuilderResult&` |
| `ConvertFromPreset` | none | `EMetaSoundBuilderResult&` |
| `IsPreset` | none | `bool` |
| `GetRootGraphClassName` | none | `FMetasoundFrontendClassName` |

</details>

---

## UMetaSoundSourceBuilder API (extends UMetaSoundBuilderBase)

<details>

| Method | Parameters | Returns |
|--------|-----------|---------|
| `Audition` | `UObject* Parent, UAudioComponent*, FOnCreateAuditionGeneratorHandleDelegate, bool bLiveUpdatesEnabled=false` | void |
| `GetLiveUpdatesEnabled` | none | `bool` |
| `SetFormat` | `EMetaSoundOutputAudioFormat` | `EMetaSoundBuilderResult` |
| `SetQuality` | `FName Quality` | void |
| `SetSampleRateOverride` | `int32 SampleRate` | void |
| `SetBlockRateOverride` | `float BlockRate` | void |

</details>

---

## UMetaSoundBuilderSubsystem Complete API (UE 5.7)

<details>

### Builder Creation
| Method | Parameters | Returns |
|--------|-----------|---------|
| `CreateSourceBuilder` | `FName, OutputFormat=Mono, bIsOneShot=true` | `UMetaSoundSourceBuilder* + out-handles + EMetaSoundBuilderResult&` |
| `CreateSourcePresetBuilder` | `FName, TScriptInterface<IMetaSoundDocumentInterface>` | `UMetaSoundSourceBuilder*, EMetaSoundBuilderResult&` |
| `CreatePatchBuilder` | `FName` | `UMetaSoundPatchBuilder*, EMetaSoundBuilderResult&` |
| `CreatePatchPresetBuilder` | `FName, TScriptInterface<IMetaSoundDocumentInterface>` | `UMetaSoundPatchBuilder*, EMetaSoundBuilderResult&` |

### Builder Registry
| Method | Parameters | Returns |
|--------|-----------|---------|
| `RegisterBuilder` | `FName, UMetaSoundBuilderBase*` | void |
| `RegisterSourceBuilder` | `FName, UMetaSoundSourceBuilder*` | void |
| `RegisterPatchBuilder` | `FName, UMetaSoundPatchBuilder*` | void |
| `UnregisterBuilder` | `FName` | `bool` |
| `UnregisterSourceBuilder` | `FName` | `bool` |
| `UnregisterPatchBuilder` | `FName` | `bool` |

### Builder Lookup
| Method | Parameters | Returns |
|--------|-----------|---------|
| `FindBuilder` | `FName` | `UMetaSoundBuilderBase*` |
| `FindSourceBuilder` | `FName` | `UMetaSoundSourceBuilder*` |
| `FindPatchBuilder` | `FName` | `UMetaSoundPatchBuilder*` |
| `FindBuilderOfDocument` | `TScriptInterface<IMetaSoundDocumentInterface>` | `UMetaSoundBuilderBase*` |
| `FindParentBuilderOfPreset` | `TScriptInterface<IMetaSoundDocumentInterface>` | `UMetaSoundBuilderBase*` |

### Literal Creation
| Method | Parameters | Returns |
|--------|-----------|---------|
| `CreateBoolMetaSoundLiteral` | `bool` | `FMetasoundFrontendLiteral, FName DataType` |
| `CreateIntMetaSoundLiteral` | `int32` | `FMetasoundFrontendLiteral, FName DataType` |
| `CreateFloatMetaSoundLiteral` | `float` | `FMetasoundFrontendLiteral, FName DataType` |
| `CreateStringMetaSoundLiteral` | `FString` | `FMetasoundFrontendLiteral, FName DataType` |
| `CreateObjectMetaSoundLiteral` | `UObject*` | `FMetasoundFrontendLiteral` |
| `CreateMetaSoundLiteralFromParam` | `FAudioParameter` | `FMetasoundFrontendLiteral` |
| (Array variants for each type) | | |

### Utility
| Method | Parameters | Returns |
|--------|-----------|---------|
| `IsInterfaceRegistered` | `FName` | `bool` |
| `SetTargetPage` | (unknown params) | void |

</details>

---

## Action Items for Our Plugin

<warnings>
1. **Verify UMetaSoundBuilderSubsystem::Get()** -- If this doesn't compile in UE 5.7, switch to `GEngine->GetEngineSubsystem<UMetaSoundBuilderSubsystem>()`. The standard pattern for Engine Subsystems does NOT include a static Get() method.

2. **Store AudioComponent in AuditionAudioComponent** -- Our code creates the component but doesn't assign to the TStrongObjectPtr member, risking GC during playback.

3. **AddNodeByClassName overload** -- Our code passes 2 params. The documented overloads take 3 (ClassName, MajorVersion, Result) or (ClassName, Result, MajorVersion=1). If the 2-param version doesn't exist, add `1` as MajorVersion.

4. **MetasoundFrontendSearchEngine.h** -- Do not depend on this. It's not in the public API. Our current NodeTypeMap approach is correct.

5. **Live Updates cvar** -- Audition with live updates also requires `au.MetaSound.LiveUpdatesEnabled 1` console variable to be set globally.

6. **Editor-only guards** -- Audition is editor-only. Our `#if WITH_EDITOR` guard is correct. Ensure all Builder API code paths degrade gracefully in shipping builds.

7. **Build.cs is correct** -- Our module dependencies (MetasoundEngine, MetasoundFrontend, MetasoundGraphCore) match what reference implementations use.
</warnings>

---

## Resources

<references>
- [MetaSound Builder API Official Docs (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasound-builder-api-in-unreal-engine)
- [UMetaSoundBuilderBase C++ API Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/MetasoundEngine/UMetaSoundBuilderBase)
- [UMetaSoundSourceBuilder::Audition API Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/MetasoundEngine/UMetaSoundSourceBuilder/Audition)
- [MetaSoundBuilderSubsystem Python API (5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MetaSoundBuilderSubsystem?application_version=5.7)
- [MetaSoundBuilderBase Python API (5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MetaSoundBuilderBase?application_version=5.7)
- [BuildNewMetaSound Blueprint API](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Audio/MetaSound/Builder/BuildNewMetaSound)
- [MetaSound Builder Blueprint API Index](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Audio/MetaSound/Builder)
- [Programming Subsystems in UE5](https://dev.epicgames.com/documentation/en-us/unreal-engine/programming-subsystems-in-unreal-engine)
- [UMetasoundGeneratorHandle API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/MetasoundEngine/UMetasoundGeneratorHandle)
- [RNBOMetasound Build.cs Reference (Cycling74)](https://github.com/Cycling74/RNBOMetasound)
- [MetaSounds Community Wiki](https://unrealcommunity.wiki/metasounds-d660ee)
- [Creating MetaSound Nodes in C++ Quickstart](https://dev.epicgames.com/community/learning/tutorials/ry7p/unreal-engine-creating-metasound-nodes-in-c-quickstart)
- [MetaSounds Builder API Roadmap Item](https://portal.productboard.com/epicgames/1-unreal-engine-public-roadmap/c/1023-metasound-builder-api-experimental)
- [MetaSounds Runtime Duplication Issue (UE 5.5)](https://forums.unrealengine.com/t/unable-to-duplicate-metasounds-in-runtime-for-shipping-builds-using-the-meta-sound-builder-api/2539114)
- [MetaSound Plugin Compilation Issues](https://forums.unrealengine.com/t/metasound-plug-in-compiling/570218)
</references>

---

<meta>
research-date: 2026-02-08
confidence: high (API surface from official docs), medium (exact C++ signatures inferred from Python/BP API)
version-checked: UE 5.7 (primary), UE 5.3-5.6 (cross-referenced)
key-uncertainty: UMetaSoundBuilderSubsystem::Get() static method existence, MetasoundFrontendSearchEngine.h status
</meta>
