# MetaSounds Builder API: External Implementations Research

_Generated: 2026-02-08 | Sources: 25+ | Scope: GitHub repos, UE forums, Epic docs, engine source_

## Quick Reference

<key-points>
- NO other MCP project ships MetaSounds Builder API tools in production. ChiR24/Unreal_mcp has handlers but uses FrontendDocumentBuilder (not BuilderSubsystem). kvick-games/UnrealMCP lists MetaSound support but has NOT implemented it. chongdashu/unreal-mcp has zero audio support.
- The only project doing runtime Builder API graph construction is Amir-BK/unDAW (DAW plugin). It stores UMetaSoundSourceBuilder* and calls ConnectNodes/Audition with live delegate updates.
- Epic's engine source reveals UMetaSoundBuilderSubsystem is an ENGINE subsystem (GEngine->GetEngineSubsystem), NOT a world subsystem. Builders are transient objects in GetTransientPackage() with RF_Public|RF_Transient flags.
- Critical pitfall: Builder API requires WITH_EDITORONLY_DATA for some paths -- DuplicateObject broke in UE 5.5, and shipping builds cannot use the full builder. Our editor-only approach is correct.
- FMetasoundFrontendClassName uses dot notation internally (Namespace.Name.Variant) but our C++ plugin parses "::" -- both work because AddNodeByClassName accepts the struct, not a string.
</key-points>

---

## 1. Projects Surveyed

### 1.1 ChiR24/Unreal_mcp -- The Only MCP With Audio Authoring

**Repo**: https://github.com/ChiR24/Unreal_mcp
**Architecture**: TypeScript MCP server + C++ McpAutomationBridge plugin + optional Rust/WASM layer
**Audio file**: `McpAutomationBridge_AudioAuthoringHandlers.cpp`

This is the closest comparable project to ours. Key differences:

| Aspect | ChiR24/Unreal_mcp | Our UEAudioMCP |
|--------|-------------------|----------------|
| Builder approach | `FMetaSoundFrontendDocumentBuilder` (direct document manipulation) | `UMetaSoundBuilderSubsystem::CreateSourceBuilder()` (high-level API) |
| Node class names | Mapped strings: `"oscillator"` -> `"Metasound.Sine"` | 65-entry NodeTypeMap + `::` passthrough |
| Connection method | `FNamedEdge` + `Builder.AddNamedEdges()` (GUID-based) | `Builder->ConnectNodes(OutputHandle, InputHandle)` (handle-based) |
| MetaSound creation | `UMetaSoundSourceFactory` or `NewObject<UMetaSoundSource>()` | `BuilderSubsystem->CreateSourceBuilder()` |
| Finalization | `Builder.FinishBuilding()` on UE 5.4+ | `BuildNewMetaSound()` |
| Conditional compilation | `#if __has_include("MetasoundSource.h")` | Direct includes, editor-only guards |
| Audition | Not implemented | Full AudioComponent + `SourceBuilder->Audition()` |
| Transport | HTTP/WebSocket MCP | TCP socket (port 9877) |

**What they do that we don't:**
- Conditional feature detection with `__has_include()` for graceful degradation across UE versions
- Sound Class, Sound Mix (4-band EQ), Attenuation, Dialogue, Reverb/Source Effect chain tools
- Path normalization helper (`/Content` -> `/Game`, backslash -> forward slash)
- `McpSafeAssetSave()` to avoid modal dialogs during headless operation

**What we do that they don't:**
- Full Audition support with AudioComponent lifecycle management
- Graph variable support (Get/Set/GetDelayed nodes)
- Preset conversion (ConvertToPreset/ConvertFromPreset)
- Live updates via Audition parameter
- `__graph__` sentinel for graph boundary connections
- Display-name-to-class-name registry (65 hardcoded entries)
- TStrongObjectPtr for GC-safe builder storage

### 1.2 Amir-BK/unDAW -- Most Advanced Runtime Builder Usage

**Repo**: https://github.com/Amir-BK/unDAW
**Purpose**: Digital Audio Workstation in UE5 (MIDI playback with assignable MetaSounds patches)
**Engine**: UE 5.4+ required

This is the most sophisticated Builder API consumer found anywhere on GitHub.

**Key patterns from their code** (`M2SoundGraphData.h`):

```cpp
// Member storage
UMetaSoundSourceBuilder* BuilderContext;
UMetaSoundBuilderSubsystem* MSBuilderSystem;
UAudioComponent* AuditionComponent;  // Transient, BlueprintReadOnly

// Connection pattern
BuilderContext->ConnectNodes(OutputHandle, InputHandle, Result);
BuilderContext->DisconnectNodes(OutputHandle, InputHandle, Result);

// Audition with generator handle callback
void AuditionBuilder(UAudioComponent* InAudioComponent);
void OnMetaSoundGeneratorHandleCreated(UMetasoundGeneratorHandle* Handle);
```

**Critical design patterns:**
- Separate delegates for topology changes vs connection changes (`OnVertexNeedsBuilderUpdates`, `OnVertexNeedsBuilderConnectionUpdates`)
- Generator handle binding for MIDI output receivers and clock signals
- Loop settings with bar duration configuration
- Struct parameter packs for MIDI data (`StructParametersPack`)
- Transient vertices tracked separately from persistent ones

**What this tells us:**
- Our `TStrongObjectPtr<UMetaSoundBuilderBase>` pattern is validated -- they also store builder pointers as class members
- They use `UMetasoundGeneratorHandle` for bidirectional communication (we don't yet)
- Their delegate pattern for vertex updates could enable our live update feature more robustly

### 1.3 chongdashu/unreal-mcp -- No Audio At All

**Repo**: https://github.com/chongdashu/unreal-mcp (1,370 stars)
**Status**: EXPERIMENTAL, no audio/MetaSounds tools
**Tools**: Actor management, Blueprint creation, component configuration, editor viewport control
**Relevance**: Architecture reference only (C++ plugin + Python MCP, modular tool files)

### 1.4 kvick-games/UnrealMCP -- MetaSound Listed, Not Implemented

**Repo**: https://github.com/kvick-games/UnrealMCP
**Status**: "VERY WIP REPO", MetaSound on roadmap but not started
**Port**: TCP 13377

### 1.5 WillGordon9999/UE-Angelscript -- API Surface Reference

**Repo**: https://github.com/WillGordon9999/UE-Angelscript
**File**: `Bind_MetaSoundBuilderSubsystem.cpp`

Angelscript bindings expose the full BuilderSubsystem API surface (27 methods):

**Literal creation** (10 methods): Bool, Int, Float, String (scalar + array variants), Object, ObjectArray
**Builder creation** (5 methods): CreatePatchBuilder, CreateSourceBuilder, CreatePatchPresetBuilder, CreateSourcePresetBuilder, CreateMetaSoundLiteralFromParam
**Builder lookup** (4 methods): FindBuilder, FindPatchBuilder, FindSourceBuilder, FindBuilderOfDocument
**Builder registration** (6 methods): Register/Unregister for Builder, PatchBuilder, SourceBuilder
**Utility** (2 methods): IsInterfaceRegistered

Key insight: `AddNodeByClassName`, `ConnectNodes`, `Audition` are on the **builder classes** (UMetaSoundBuilderBase / UMetaSoundSourceBuilder), NOT the subsystem. The subsystem only creates/finds/registers builders.

---

## 2. Epic Engine Source Analysis

Source: `MetasoundBuilderSubsystem.cpp` from UE 5.4 engine source (mirror: chenyong2github/UnrealEngine)

### 2.1 Subsystem Access Pattern

```cpp
// Epic's internal access (engine subsystem, NOT world subsystem)
UMetaSoundBuilderSubsystem& UMetaSoundBuilderSubsystem::GetChecked()
{
    checkf(GEngine, TEXT("Cannot access without engine loaded"));
    UMetaSoundBuilderSubsystem* BuilderSubsystem =
        GEngine->GetEngineSubsystem<UMetaSoundBuilderSubsystem>();
    checkf(BuilderSubsystem, TEXT("Failed to find initialized subsystem"));
    return *BuilderSubsystem;
}
```

**Our code uses**: `UMetaSoundBuilderSubsystem::Get()` -- this is correct for UE 5.7 where it was changed to a static getter.

### 2.2 CreateSourceBuilder Implementation

```cpp
UMetaSoundSourceBuilder* UMetaSoundBuilderSubsystem::CreateSourceBuilder(
    FName BuilderName,
    FMetaSoundBuilderNodeOutputHandle& OnPlayNodeOutput,
    FMetaSoundBuilderNodeInputHandle& OnFinishedNodeInput,
    TArray<FMetaSoundBuilderNodeInputHandle>& AudioOutNodeInputs,
    EMetaSoundBuilderResult& OutResult,
    EMetaSoundOutputAudioFormat OutputFormat,
    bool bIsOneShot)
```

Internal steps:
1. Creates transient builder via `CreateTransientBuilder<UMetaSoundSourceBuilder>(BuilderName)`
2. Sets output format if not Mono via `SetFormat()`
3. Finds audio output nodes matching format interface
4. Populates `AudioOutNodeInputs` by finding node inputs
5. Retrieves OnPlay interface node output handle
6. If one-shot, retrieves OnFinished interface node input handle

### 2.3 Transient Builder Creation

```cpp
template <typename BuilderClass>
BuilderClass& CreateTransientBuilder(FName BuilderName = {})
{
    const EObjectFlags NewObjectFlags = RF_Public | RF_Transient;
    UPackage* TransientPackage = GetTransientPackage();
    const FName ObjectName = MakeUniqueObjectName(
        TransientPackage, BuilderClass::StaticClass(), BuilderName);
    TObjectPtr<BuilderClass> NewBuilder = NewObject<BuilderClass>(
        TransientPackage, ObjectName, NewObjectFlags);
    check(NewBuilder);
    NewBuilder->InitFrontendBuilder();
    return *NewBuilder.Get();
}
```

Key: Builders are **transient objects** -- they live in `GetTransientPackage()`, not saved to disk. This is why our `TStrongObjectPtr` approach is essential (prevents GC collection of the transient object).

### 2.4 Source Builder vs Base Builder Initialization

```cpp
// Base class (Patch)
void UMetaSoundBuilderBase::InitFrontendBuilder()
{
    UMetaSoundBuilderDocument* DocObject = CreateTransientDocumentObject();
    Builder = FMetaSoundFrontendDocumentBuilder(DocObject);
    Builder.InitDocument();
}

// Source-specific (adds modify delegates for live audition)
void UMetaSoundSourceBuilder::InitFrontendBuilder()
{
    TSharedRef<FDocumentModifyDelegates> DocumentDelegates =
        MakeShared<FDocumentModifyDelegates>();
    InitDelegates(*DocumentDelegates);

    UMetaSoundBuilderDocument* DocObject = CreateTransientDocumentObject();
    Builder = FMetaSoundFrontendDocumentBuilder(DocObject, DocumentDelegates);
    Builder.InitDocument();
}
```

The source builder wires up `FDocumentModifyDelegates` for live audition topology updates. This is why our `bLiveUpdatesRequested` flag works -- it enables the delegate pathway that was set up at builder creation.

### 2.5 Include Files (from engine source)

```cpp
#include "MetasoundBuilderSubsystem.h"
#include "Components/AudioComponent.h"
#include "Engine/Engine.h"
#include "Interfaces/MetasoundOutputFormatInterfaces.h"
#include "Interfaces/MetasoundFrontendSourceInterface.h"
#include "Metasound.h"
#include "MetasoundAssetSubsystem.h"
#include "MetasoundDataReference.h"
#include "MetasoundDynamicOperatorTransactor.h"
#include "MetasoundFrontendDataTypeRegistry.h"
#include "MetasoundFrontendDocument.h"
#include "MetasoundFrontendRegistries.h"
#include "MetasoundFrontendSearchEngine.h"
#include "MetasoundFrontendTransform.h"
#include "MetasoundGeneratorHandle.h"
#include "MetasoundLog.h"
#include "MetasoundParameterTransmitter.h"
#include "MetasoundSource.h"
#include "MetasoundTrace.h"
#include "MetasoundUObjectRegistry.h"
#include "MetasoundVertex.h"
```

**Our includes** (AudioMCPBuilderManager.cpp):
```cpp
#include "MetasoundBuilderSubsystem.h"
#include "MetasoundSource.h"
#include "MetasoundDocumentInterface.h"
#include "MetasoundFrontendDocument.h"
#include "Interfaces/MetasoundOutputFormatInterfaces.h"
#include "Components/AudioComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Editor.h"
```

We are missing some includes that could be useful: `MetasoundGeneratorHandle.h` (for Audition callbacks), `MetasoundFrontendRegistries.h` (for node discovery), `MetasoundLog.h` (for native log category).

---

## 3. UMetaSoundBuilderBase Full API Reference

Source: UE 5.7 C++ API docs + Python API bindings

### 3.1 Node Operations

| Method | Parameters | Returns | Notes |
|--------|-----------|---------|-------|
| `AddNodeByClassName` | `FMetasoundFrontendClassName, int32 MajorVersion=1` | `FMetaSoundNodeHandle, EMetaSoundBuilderResult` | Adds highest version of named class |
| `AddNode` | `TScriptInterface<IMetaSoundDocumentInterface>` | `FMetaSoundNodeHandle, EMetaSoundBuilderResult` | For custom MetaSound references |
| `RemoveNode` | `FMetaSoundNodeHandle, bool bRemoveUnusedDependencies` | `EMetaSoundBuilderResult` | Can cascade-remove deps |
| `ContainsNode` | `FMetaSoundNodeHandle` | `bool` | |
| `FindNodeInputs` | `FMetaSoundNodeHandle` | `TArray<FMetaSoundBuilderNodeInputHandle>` | All inputs |
| `FindNodeOutputs` | `FMetaSoundNodeHandle` | `TArray<FMetaSoundBuilderNodeOutputHandle>` | All outputs |
| `FindNodeInputByName` | `FMetaSoundNodeHandle, FName` | `FMetaSoundBuilderNodeInputHandle` | |
| `FindNodeOutputByName` | `FMetaSoundNodeHandle, FName` | `FMetaSoundBuilderNodeOutputHandle` | |
| `SetNodeLocation` | `FMetaSoundNodeHandle, FVector2D` | `EMetaSoundBuilderResult` | Editor only |

### 3.2 Connection Operations

| Method | Parameters | Returns | Notes |
|--------|-----------|---------|-------|
| `ConnectNodes` | `OutputHandle, InputHandle` | `EMetaSoundBuilderResult` | No loop detection (perf) |
| `ConnectNodeToGraphOutput` | `SourceNode, NodeOutputName, GraphOutputName` | `EMetaSoundBuilderResult` | Shorthand |
| `DisconnectNodes` | `OutputHandle, InputHandle` | `EMetaSoundBuilderResult` | |
| `NodesAreConnected` | `OutputHandle, InputHandle` | `bool` | |
| `NodeInputIsConnected` | `InputHandle` | `bool` | |

### 3.3 Graph I/O and Variables

| Method | Parameters | Returns | Notes |
|--------|-----------|---------|-------|
| `AddGraphInputNode` | `Name, DataType, DefaultValue, bIsConstructorInput` | `OutputHandle` | Graph inputs produce outputs |
| `AddGraphOutputNode` | `Name, DataType, DefaultValue, bIsConstructorOutput` | `InputHandle` | Graph outputs consume inputs |
| `SetGraphInputDefault` | `InputName, Literal` | `EMetaSoundBuilderResult` | |
| `AddGraphVariable` | `Name, DataType, DefaultValue` | `EMetaSoundBuilderResult` | UE 5.5+ |
| `AddGraphVariableGetNode` | `Name` | `FMetaSoundNodeHandle` | |
| `AddGraphVariableSetNode` | `Name` | `FMetaSoundNodeHandle` | |
| `AddGraphVariableGetDelayedNode` | `Name` | `FMetaSoundNodeHandle` | Previous-frame value |

### 3.4 Interface and Build

| Method | Parameters | Returns | Notes |
|--------|-----------|---------|-------|
| `AddInterface` | `FName InterfaceName` | `EMetaSoundBuilderResult` | e.g. "UE.Source.OneShot" |
| `RemoveInterface` | `FName InterfaceName` | `EMetaSoundBuilderResult` | |
| `InterfaceIsDeclared` | `FName InterfaceName` | `bool` | |
| `Build` | `UObject* Parent, FMetaSoundBuilderOptions` | `IMetaSoundDocumentInterface` | |
| `BuildNewMetaSound` | `FName NameBase` | `IMetaSoundDocumentInterface` | Transient, registered with node registry |
| `BuildAndOverwriteMetaSound` | `ExistingMetaSound, bForceUniqueClassName` | void | |
| `ConvertToPreset` | `TScriptInterface<IMetaSoundDocumentInterface>` | `EMetaSoundBuilderResult` | |
| `ConvertFromPreset` | | `EMetaSoundBuilderResult` | |

### 3.5 Audition (UMetaSoundSourceBuilder only)

```cpp
void UMetaSoundSourceBuilder::Audition(
    UObject* WorldContextObject,
    UAudioComponent* AudioComponent,
    FOnCreateAuditionGeneratorHandleDelegate OnCreateGenerator,
    bool bLiveUpdatesEnabled);
```

- Only available on `UMetaSoundSourceBuilder`, NOT `UMetaSoundBuilderBase`
- `OnCreateGenerator` delegate fires when the `UMetasoundGeneratorHandle` is ready
- `bLiveUpdatesEnabled` enables real-time topology changes with buffer crossfade
- AudioComponent must be registered and valid
- In UE 5.7, `SetLiveUpdatesEnabled` was removed from the base class -- now only a param to Audition

---

## 4. FMetasoundFrontendClassName Format

Internal format: `Namespace.Name` optionally with `.Variant`

```cpp
FMetasoundFrontendClassName(FName Namespace, FName Name, FName Variant = NAME_None);

// Examples:
// "UE.Sine.Audio"      -> Namespace="UE", Name="Sine", Variant="Audio"
// "UE.AD Envelope"     -> Namespace="UE", Name="AD Envelope", Variant=""
// "UE.Biquad Filter"   -> Namespace="UE", Name="Biquad Filter", Variant=""
```

**How our plugin handles this:**
We parse `"::"` as separator: `"UE::Sine::Audio"` -> `FMetasoundFrontendClassName(FName("UE"), FName("Sine"), FName("Audio"))`

This works correctly because the `FMetasoundFrontendClassName` struct constructor takes three `FName` parameters regardless of the separator used in the string representation. The internal `ToString()` method outputs dot notation, but construction accepts any FName values.

---

## 5. Common Pitfalls and Known Issues

### 5.1 Print Log Nodes Crash Shipping Builds

**Source**: [Epic Forums - Fatal error in shipping builds](https://forums.unrealengine.com/t/metasounds-cause-a-fatal-error-in-shipping-builds/877128)

Print Log nodes in a MetaSound graph cause fatal crashes in shipping builds. They don't require activation or connection -- their mere presence is enough. Must remove all debug nodes before packaging.

### 5.2 Concurrent Builder Conflicts

**Error**: `"LogMetaSound: Error: OnBeginActiveBuilder() call while prior builder is still active"`

Occurs when using MetaSounds as audio sources in UI animation sequences. Two builder modifications run simultaneously. Workaround: Replace MetaSound reference with `PlaySound2D` on a timer delay.

**Relevance to us**: Our plugin is single-threaded (one TCP connection, one builder at a time), so we avoid this. But if we ever support multiple concurrent builders, this will bite.

### 5.3 DuplicateObject Broke in UE 5.5

**Source**: [Epic Forums - Unable to duplicate MetaSounds at runtime](https://forums.unrealengine.com/t/unable-to-duplicate-metasounds-in-runtime-for-shipping-builds-using-the-meta-sound-builder-api/2539114)

`DuplicateObject<UMetaSoundSource>()` worked in UE 5.4 but is "no longer allowed" in 5.5. The Builder API is the replacement, but it requires `WITH_EDITORONLY_DATA` -- so no shipping build support for runtime graph duplication. No official workaround exists (post remains unanswered).

### 5.4 Node Registry Conflicts

**Source**: [Epic Forums - Registration failed for MetaSound node](https://forums.unrealengine.com/t/registration-failed-for-metasound-node/2035105)

Duplicate Animation Notifies or assets with identical names trigger: `"Node with registry key already registered. The previously registered node will be overwritten."`

Fixed in two engine commits (8c0baa29, ade688fd) as of September 2024. The error log may not affect functionality but is alarming.

### 5.5 MetaSounds Namespace Migration

**Source**: [Epic Forums - Creating MetaSound Nodes in C++ Quickstart](https://forums.unrealengine.com/t/tutorial-creating-metasound-nodes-in-c-quickstart/559789/6)

Types moved into `Metasound::` namespace between UE 5.0 and 5.1+. Code written for 5.0 tutorials may fail to compile on newer versions.

### 5.6 SpawnSound2D vs PlaySound2D Stuck Audio

**Source**: [Epic Forums - MetaSound stop working at all or stuck](https://forums.unrealengine.com/t/metasound-stop-working-at-all-or-stuck-when-too-many/2321014)

When many concurrent MetaSounds play, `SpawnSound2D` components can get stuck at random parameter positions. The `auto-destroy` boolean on spawned components interacts badly with stop commands. Default audio channel limit is 32 concurrent sounds.

**Relevance to us**: Our Audition uses `bAutoDestroy = true` -- if the user rapidly auditions while a previous audition is playing, we could hit this. Consider setting `bAutoDestroy = false` and manually managing the AudioComponent lifecycle.

### 5.7 MetaSound Start+Stop on Same Frame

**Source**: [Epic Forums - MetaSound starting and stopping instantly](https://forums.unrealengine.com/t/metasound-starting-and-stopping-instantly/2607112)

When start and stop triggers fire on the same frame, no audio plays. This is by design (input-driven architecture), but unexpected for procedurally-triggered sounds.

### 5.8 Builder API Status: Still Beta in UE 5.7

The official docs mark the Builder API as **Beta** with the warning: "use caution when shipping with it." Variables support was added in UE 5.5. Graph Pages were added in UE 5.6. Live Updates remains a beta feature.

---

## 6. Comparison: Our Implementation vs The Field

### What We Do Better Than Everyone

1. **Full Audition pipeline**: We are the only MCP project with working AudioComponent creation + `SourceBuilder->Audition()` + live updates flag. ChiR24 doesn't audition at all.

2. **Graph variable support**: AddGraphVariable, AddVariableGetNode, AddVariableSetNode, AddGraphVariableGetDelayedNode. No other MCP project has this.

3. **Preset conversion**: ConvertToPreset/ConvertFromPreset. Unique to our implementation.

4. **`__graph__` sentinel pattern**: Clean abstraction for graph boundary connections. ChiR24 uses GUID-based edges instead.

5. **65-entry node type registry**: Display name to class name mapping. ChiR24 has ~5 hardcoded mappings.

6. **TStrongObjectPtr for builder storage**: Prevents garbage collection. Validated by Epic's own transient object pattern.

7. **UE 5.7 API alignment**: We use `CreateSourceBuilder` with the 5.7 signature (returns OnPlay/OnFinished/AudioOut handles). ChiR24 uses the older FrontendDocumentBuilder approach.

### What Others Do That We Should Consider

1. **ChiR24: `__has_include()` guards**
   ```cpp
   #if __has_include("MetasoundSource.h")
   #define MCP_HAS_METASOUND 1
   #endif
   ```
   Graceful degradation when MetaSounds plugin is not enabled. We hard-fail.

2. **ChiR24: Path normalization**
   Converting `/Content/` to `/Game/` and backslashes to forward slashes. We only check for `/Game/` prefix.

3. **ChiR24: Safe asset save**
   `McpSafeAssetSave()` avoids modal dialogs during headless operation. Our `BuildToAsset` uses `BuildNewMetaSound` (transient, no dialog), but future asset-save operations should consider this.

4. **unDAW: Generator handle callback**
   ```cpp
   void OnMetaSoundGeneratorHandleCreated(UMetasoundGeneratorHandle* Handle);
   ```
   We pass an empty delegate to Audition. If we want bidirectional communication (parameter feedback, MIDI output), we need this.

5. **unDAW: Separate topology vs connection delegates**
   `OnVertexNeedsBuilderUpdates` vs `OnVertexNeedsBuilderConnectionUpdates`. More granular than our boolean flag.

6. **Engine source: `MetasoundGeneratorHandle.h` include**
   We don't include this yet. Needed for Audition callback support and real-time parameter monitoring.

### Potential Issues in Our Code

1. **AuditionAudioComponent member declared but unused**: We create a local `AudioComp` in `Audition()` but have `TStrongObjectPtr<UAudioComponent> AuditionAudioComponent` as a member that is never populated. The local component may be GC'd after the function returns if `bAutoDestroy` doesn't fire quickly enough.

2. **bAutoDestroy = true risk**: Combined with live updates, auto-destroying the AudioComponent while the builder still has a reference could cause issues. unDAW stores AuditionComponent as a class member (Transient, BlueprintReadOnly).

3. **No generator handle delegate**: We pass `FOnCreateAuditionGeneratorHandleDelegate EmptyDelegate` -- we can't detect when audition actually starts playing or get parameter feedback.

4. **Single builder limitation**: One `ActiveBuilder` at a time. The engine supports multiple registered builders (Register/Unregister pattern). For complex systems (e.g., layered sounds), we might need multiple simultaneous builders.

---

## 7. Recommendations

### Immediate (Low Effort, High Impact)

1. **Store AudioComponent in member**: Assign `AuditionAudioComponent` in `Audition()` instead of using a local. Set `bAutoDestroy = false` and manage lifecycle manually in `ResetState()`.

2. **Add generator handle delegate**: Wire up `FOnCreateAuditionGeneratorHandleDelegate` to log when audition actually begins playing. Future: expose generator handle for parameter feedback.

3. **Add `__has_include` guards**: Graceful compilation when MetaSounds plugin is disabled.

### Medium Term

4. **Include `MetasoundGeneratorHandle.h`**: Enable real-time parameter monitoring and bidirectional communication during audition.

5. **Add `MetasoundFrontendRegistries.h`**: Enable runtime node class discovery instead of relying solely on our 65-entry hardcoded map.

6. **Path normalization**: Add `/Content/` to `/Game/` conversion for asset paths.

### Long Term

7. **Multi-builder support**: Allow named builders to coexist (matching Epic's Register/UnregisterBuilder pattern).

8. **Generator handle parameter feedback**: Report real-time audio analysis back through TCP.

---

## 8. Resources

<references>
- [Epic: MetaSound Builder API Docs (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasound-builder-api-in-unreal-engine)
- [Epic: UMetaSoundBuilderBase API Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/MetasoundEngine/UMetaSoundBuilderBase)
- [Epic: MetaSound Python API (5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MetaSoundBuilderBase?application_version=5.7)
- [Epic: Builder Blueprint API](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Audio/MetaSound/Builder)
- [ChiR24/Unreal_mcp Audio Handlers](https://github.com/ChiR24/Unreal_mcp/blob/29d1315c443ad58f9f78aded3c9dde6b15c8ba9c/plugins/McpAutomationBridge/Source/McpAutomationBridge/Private/McpAutomationBridge_AudioAuthoringHandlers.cpp)
- [Amir-BK/unDAW Graph Data](https://github.com/Amir-BK/unDAW/blob/00d6870d761ed32be860a8b8ea71cd2c6cb7f931/Source/BKMusicCore/Public/M2SoundGraphData.h)
- [chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp)
- [kvick-games/UnrealMCP](https://github.com/kvick-games/UnrealMCP)
- [UE-Angelscript Builder Bindings](https://github.com/WillGordon9999/UE-Angelscript/blob/77af4ac942e317950cc7cb96b38232b1191e4bb1/Plugins/Angelscript/Source/ASRuntimeBind_70/Private/Bind_MetaSoundBuilderSubsystem.cpp)
- [Epic: MetaSounds Reference Guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-reference-guide-in-unreal-engine)
- [Epic: Creating MetaSound Nodes in C++ Quickstart](https://dev.epicgames.com/community/learning/tutorials/ry7p/unreal-engine-creating-metasound-nodes-in-c-quickstart)
- [Epic Forums: Fatal error in shipping builds](https://forums.unrealengine.com/t/metasounds-cause-a-fatal-error-in-shipping-builds/877128)
- [Epic Forums: MetaSound registration error](https://forums.unrealengine.com/t/metasound-error/1211669)
- [Epic Forums: MetaSound start/stop instantly](https://forums.unrealengine.com/t/metasound-starting-and-stopping-instantly/2607112)
- [Epic Forums: Builder API runtime duplication issue](https://forums.unrealengine.com/t/unable-to-duplicate-metasounds-in-runtime-for-shipping-builds-using-the-meta-sound-builder-api/2539114)
- [Epic Forums: Registration failed for MetaSound node](https://forums.unrealengine.com/t/registration-failed-for-metasound-node/2035105)
- [Epic Forums: MetaSounds stuck with many concurrent](https://forums.unrealengine.com/t/metasound-stop-working-at-all-or-stuck-when-too-many/2321014)
- [Epic Forums: Create/Edit MetaSound at runtime](https://forums.unrealengine.com/t/create-edit-metasound-during-runtime/753198)
- [Epic Roadmap: Builder API (Experimental)](https://portal.productboard.com/epicgames/1-unreal-engine-public-roadmap/c/1023-metasound-builder-api-experimental)
- [Epic Bug: UE-149182 Editor crash with MetaSound C++ reference](https://issues.unrealengine.com/issue/UE-149182)
- [mattetti MetaSounds Gist](https://gist.github.com/mattetti/e89739a006591289e72c5252da1de877)
- [Abstracting the UE5 MetaSound (Jesse Lee Humphry)](https://www.jesseleehumphry.com/post/abstracting-the-ue5-metasound)
- [Engine Source: MetasoundBuilderSubsystem.cpp](https://github.com/chenyong2github/UnrealEngine/blob/c865e168d0935b8e5f4bd865ddcc1c733c8ce7cf/Engine/Plugins/Runtime/Metasound/Source/MetasoundEngine/Private/MetasoundBuilderSubsystem.cpp)
</references>

## Metadata

<meta>
research-date: 2026-02-08
confidence: high
version-checked: UE 5.4, 5.5, 5.6, 5.7
repos-analyzed: 8 (ChiR24, Amir-BK, chongdashu, kvick-games, WillGordon9999, realAYAYA, chenyong2github, Cycling74)
forum-threads: 8
api-docs-pages: 6
</meta>
