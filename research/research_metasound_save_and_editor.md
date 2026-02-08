# MetaSounds: Save to Disk & Open in Editor -- Research Summary

_Generated: 2026-02-08 | Sources: 12+ | Engine Version: UE 5.7_

## Quick Reference

<key-points>
- `UMetaSoundEditorSubsystem::BuildToAsset()` is the ONLY method that saves a builder's graph as a real .uasset file
- `BuildNewMetaSound()` on UMetaSoundBuilderBase creates TRANSIENT objects only (memory, not disk)
- `UAssetEditorSubsystem::OpenEditorForAsset()` opens any asset in its native editor (MetaSounds graph editor for MetaSounds)
- `SetNodeLocation()` lives on `UMetaSoundEditorSubsystem` (NOT on the builder base class)
- `FindOrBeginBuilding()` lets you get a builder for an existing saved MetaSound asset
- Our current C++ plugin uses `BuildNewMetaSound()` which does NOT save to disk -- needs to be replaced
</key-points>

---

## Overview

<summary>
The MetaSounds Builder API has three subsystems that serve different roles:

1. **UMetaSoundBuilderSubsystem** (Engine Subsystem) -- Creates builders, manages transient MetaSounds at runtime
2. **UMetaSoundEditorSubsystem** (Editor Subsystem) -- Saves to assets, node positioning, editor-time operations
3. **UMetaSoundAssetSubsystem** -- Asset loading/unloading

The critical distinction: `UMetaSoundBuilderBase` methods (`BuildNewMetaSound`, `BuildAndOverwriteMetaSound`) only create transient in-memory objects. To create a real `.uasset` file on disk that persists and is visible in the Content Browser, you MUST use `UMetaSoundEditorSubsystem::BuildToAsset()`.
</summary>

---

## The Three Build Methods on UMetaSoundBuilderBase

### 1. BuildNewMetaSound (Transient Only)

```cpp
// C++ Signature (from UE 5.7 API)
TScriptInterface<IMetaSoundDocumentInterface> BuildNewMetaSound(FName NameBase);
```

```python
# Python API
build_new_meta_sound(name_base: Name) -> MetaSoundDocumentInterface
```

- Creates a **transient** MetaSound in memory
- Registers it with the MetaSound Node Registry as a unique class
- If a MetaSound with `NameBase` already exists, generates a unique name using `NameBase` as prefix
- **Does NOT save to disk** -- exists only in memory during the session
- Good for: audition/preview, runtime playback, temporary graphs

### 2. BuildAndOverwriteMetaSound (Transient Only)

```cpp
// C++ Signature
void BuildAndOverwriteMetaSound(
    TScriptInterface<IMetaSoundDocumentInterface> ExistingMetaSound,
    bool bForceUniqueClassName = false
);
```

```python
# Python API
build_and_overwrite_meta_sound(existing_meta_sound, force_unique_class_name=False) -> None
```

- Overwrites an **existing transient** MetaSound with the builder's current state
- **CANNOT overwrite saved assets** -- documentation explicitly states: _"Not permissible to overwrite MetaSound asset, only transient MetaSound"_
- Use case: updating a previously-built transient MetaSound without creating a new one

### 3. Build (SOFT DEPRECATED in UE 5.7)

```cpp
// C++ Signature (deprecated)
TScriptInterface<IMetaSoundDocumentInterface> Build(
    UObject* Parent,
    const FMetaSoundBuilderOptions& Options
);
```

- **Soft deprecated** in UE 5.7: _"Parent no longer supported and field is ignored."_
- Do not use for new code

---

## Saving to Disk: UMetaSoundEditorSubsystem::BuildToAsset

This is the critical API for creating persistent `.uasset` files.

### C++ Signature

```cpp
TScriptInterface<IMetaSoundDocumentInterface> BuildToAsset(
    UMetaSoundBuilderBase* InBuilder,
    const FString& Author,
    const FString& AssetName,
    const FString& PackagePath,
    EMetaSoundBuilderResult& OutResult,
    const USoundWave* TemplateSoundWave = nullptr  // optional: copy SoundWave settings from template
);
```

### Python Signature

```python
build_to_asset(
    builder: MetaSoundBuilderBase,
    author: str,
    asset_name: str,
    package_path: str,
    template_sound_wave: SoundWave = None
) -> (MetaSoundDocumentInterface, MetaSoundBuilderResult)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| InBuilder | UMetaSoundBuilderBase* | The builder whose graph to export |
| Author | FString | Author metadata string (e.g., "UEAudioMCP") |
| AssetName | FString | Name of the asset (e.g., "MySineTone") |
| PackagePath | FString | Content folder path (e.g., "/Game/Audio/MetaSounds") |
| OutResult | EMetaSoundBuilderResult& | Success/failure result |
| TemplateSoundWave | const USoundWave* | Optional: copy audio settings (sample rate, channels, etc.) from an existing SoundWave |

### Return Value

Returns a `TScriptInterface<IMetaSoundDocumentInterface>` -- the saved MetaSound asset. This can be cast to `UObject*` via `GetObject()` for use with `UAssetEditorSubsystem::OpenEditorForAsset()`.

### What It Does

1. Creates a new UPackage at the specified path
2. Creates a UMetaSoundSource (or UMetaSoundPatch) inside the package
3. Copies the builder's graph document into the new asset
4. Saves the package to disk as a `.uasset` file
5. Registers the asset with the Asset Registry (appears in Content Browser)
6. Returns the created asset interface

### How to Access the Subsystem

```cpp
#if WITH_EDITOR
#include "MetaSoundEditorSubsystem.h"

UMetaSoundEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UMetaSoundEditorSubsystem>();
if (EditorSubsystem)
{
    EMetaSoundBuilderResult Result;
    TScriptInterface<IMetaSoundDocumentInterface> SavedAsset = EditorSubsystem->BuildToAsset(
        Builder,          // UMetaSoundBuilderBase*
        TEXT("UEAudioMCP"), // Author
        TEXT("MySineTone"), // AssetName
        TEXT("/Game/Audio/MetaSounds"), // PackagePath
        Result,
        nullptr           // TemplateSoundWave (optional)
    );

    if (Result == EMetaSoundBuilderResult::Succeeded && SavedAsset.GetObject())
    {
        UE_LOG(LogTemp, Log, TEXT("Saved MetaSound asset: %s"), *SavedAsset.GetObject()->GetPathName());
    }
}
#endif
```

### Module Dependency

The `UMetaSoundEditorSubsystem` lives in the **MetasoundEditor** module. Your plugin's `.Build.cs` must include:

```csharp
if (Target.bBuildEditor)
{
    PrivateDependencyModuleNames.Add("MetasoundEditor");
}
```

---

## Editing an Existing Asset: FindOrBeginBuilding

To load an existing saved MetaSound and modify it:

### C++ Signature

```cpp
UMetaSoundBuilderBase* FindOrBeginBuilding(
    TScriptInterface<IMetaSoundDocumentInterface> MetaSound,
    EMetaSoundBuilderResult& OutResult
) const;
```

### Python Signature

```python
find_or_begin_building(meta_sound: MetaSoundDocumentInterface)
    -> (MetaSoundBuilderBase, MetaSoundBuilderResult)
```

### Usage

```cpp
// Load an existing MetaSound asset
UObject* Asset = StaticLoadObject(UObject::StaticClass(), nullptr, TEXT("/Game/Audio/MySineTone.MySineTone"));
TScriptInterface<IMetaSoundDocumentInterface> DocInterface(Asset);

UMetaSoundEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UMetaSoundEditorSubsystem>();
EMetaSoundBuilderResult Result;
UMetaSoundBuilderBase* Builder = EditorSubsystem->FindOrBeginBuilding(DocInterface, Result);

if (Result == EMetaSoundBuilderResult::Succeeded && Builder)
{
    // Now you can modify the builder: AddNode, ConnectNodes, etc.
    // When done, call BuildToAsset again to save changes
}
```

**Important**: Returns null for transient MetaSounds. Use `UMetaSoundBuilderSubsystem::FindBuilder()` for transients instead.

---

## Opening in the MetaSounds Editor

### UAssetEditorSubsystem::OpenEditorForAsset

```cpp
#if WITH_EDITOR
#include "Subsystems/AssetEditorSubsystem.h"

UAssetEditorSubsystem* AssetEditorSubsystem = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
if (AssetEditorSubsystem)
{
    UObject* MetaSoundAsset = SavedAsset.GetObject(); // from BuildToAsset result
    bool bOpened = AssetEditorSubsystem->OpenEditorForAsset(MetaSoundAsset);
    // If already open, brings the existing editor to front (does NOT create a duplicate)
}
#endif
```

### Behavior

- If the MetaSound asset is NOT currently open: opens a new MetaSounds graph editor tab
- If the MetaSound asset IS already open: brings the existing editor window to the front
- The MetaSounds editor displays the node graph visually with all nodes, connections, and positions
- Node positions are determined by `SetNodeLocation()` calls made during building

### Required Headers and Modules

```cpp
#include "Subsystems/AssetEditorSubsystem.h"
// Module: UnrealEd (already available in editor-only plugins)
```

---

## Node Positioning: SetNodeLocation

**Critical**: In UE 5.7, `SetNodeLocation` is on `UMetaSoundEditorSubsystem`, NOT on `UMetaSoundBuilderBase`.

### C++ Signature

```cpp
void SetNodeLocation(
    UMetaSoundBuilderBase* InBuilder,
    const FMetaSoundNodeHandle& InNode,
    const FVector2D& InLocation,
    EMetaSoundBuilderResult& OutResult
);
```

### Python Signature

```python
set_node_location(
    builder: MetaSoundBuilderBase,
    node: MetaSoundNodeHandle,
    location: Vector2D
) -> MetaSoundBuilderResult
```

### Usage

```cpp
UMetaSoundEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UMetaSoundEditorSubsystem>();
EMetaSoundBuilderResult Result;

// After adding a node:
FMetaSoundNodeHandle NodeHandle = Builder->AddNodeByClassName(ClassName, Result);

// Set its visual position in the graph editor:
EditorSubsystem->SetNodeLocation(Builder, NodeHandle, FVector2D(200.0, 100.0), Result);
```

**Note**: Our current C++ plugin uses `Builder->SetNodeLocation()` which may or may not compile depending on UE version. The canonical UE 5.7 path is through the EditorSubsystem. Both may work if the base class still exposes it as a convenience wrapper.

---

## Editor Refresh Behavior

<details>

### Does the MetaSounds editor auto-refresh?

The MetaSounds editor observes the underlying `FMetasoundFrontendDocument`. When the document changes:

1. **BuildToAsset to the same path as an open editor**: The editor should detect the package modification and refresh the graph display. However, this depends on whether the asset was fully re-saved or just modified in-place.

2. **Recommended approach for live updates**:
   - Use `FindOrBeginBuilding()` to get a builder for an already-open asset
   - Modify the builder (add/remove nodes, connections)
   - The editor may update live if the document interface triggers change delegates
   - Call `RegisterGraphWithFrontend()` to force synchronization

3. **Force refresh**: After saving, you can close and reopen the editor:
   ```cpp
   AssetEditorSubsystem->CloseAllEditorsForAsset(MetaSoundAsset);
   AssetEditorSubsystem->OpenEditorForAsset(MetaSoundAsset);
   ```

### RegisterGraphWithFrontend

```cpp
void RegisterGraphWithFrontend(UObject& InMetaSound, bool bInForceViewSynchronization) const;
```

Call with `bInForceViewSynchronization = true` to force the editor graph to re-sync with the document model.

### AddBuilderDelegateListener

```cpp
UMetaSoundEditorBuilderListener* AddBuilderDelegateListener(
    UMetaSoundBuilderBase* InBuilder,
    EMetaSoundBuilderResult& OutResult
);
```

Returns a listener object that receives notifications when the builder's document changes. The MetaSounds editor uses this internally.

</details>

---

## Complete Pipeline: Build, Save, Open

Here is the exact sequence of API calls needed:

```cpp
#if WITH_EDITOR
// 1. Get subsystems
UMetaSoundBuilderSubsystem* BuilderSS = UMetaSoundBuilderSubsystem::Get();
UMetaSoundEditorSubsystem* EditorSS = GEditor->GetEditorSubsystem<UMetaSoundEditorSubsystem>();
UAssetEditorSubsystem* AssetEditorSS = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();

// 2. Create a builder (Source example)
EMetaSoundBuilderResult Result;
FMetaSoundBuilderNodeOutputHandle OnPlayOutput;
FMetaSoundBuilderNodeInputHandle OnFinishedInput;
TArray<FMetaSoundBuilderNodeInputHandle> AudioOutInputs;

UMetaSoundBuilderBase* Builder = BuilderSS->CreateSourceBuilder(
    FName("MySineTone"),
    OnPlayOutput, OnFinishedInput, AudioOutInputs,
    Result, EMetaSoundOutputAudioFormat::Mono, true /*bIsOneShot*/
);

// 3. Add nodes
FMetasoundFrontendClassName SineClass(FName("UE"), FName("Sine"), FName("Audio"));
FMetaSoundNodeHandle SineNode = Builder->AddNodeByClassName(SineClass, Result);

// 4. Set node positions (via EditorSubsystem)
EditorSS->SetNodeLocation(Builder, SineNode, FVector2D(300, 200), Result);

// 5. Connect nodes
FMetaSoundBuilderNodeOutputHandle SineOut = Builder->FindNodeOutputByName(SineNode, FName("Audio"), Result);
Builder->ConnectNodes(SineOut, AudioOutInputs[0], Result);

// 6. SAVE TO DISK as .uasset
TScriptInterface<IMetaSoundDocumentInterface> SavedAsset = EditorSS->BuildToAsset(
    Builder,
    TEXT("UEAudioMCP"),           // Author
    TEXT("MySineTone"),           // AssetName
    TEXT("/Game/Audio/Generated"), // PackagePath
    Result,
    nullptr                      // TemplateSoundWave
);

if (Result == EMetaSoundBuilderResult::Succeeded && SavedAsset.GetObject())
{
    // 7. OPEN IN METASOUNDS EDITOR
    AssetEditorSS->OpenEditorForAsset(SavedAsset.GetObject());

    UE_LOG(LogTemp, Log, TEXT("Created and opened: %s"),
        *SavedAsset.GetObject()->GetPathName());
}
#endif
```

### The resulting asset:
- Saved at: `Content/Audio/Generated/MySineTone.uasset`
- Visible in Content Browser under `/Game/Audio/Generated/`
- Double-clicking opens the MetaSounds graph editor with all nodes visible
- Node positions match the `SetNodeLocation()` calls
- Can be referenced by AudioComponents, Sound Cues, Blueprints

---

## What Our C++ Plugin Needs to Change

<warnings>

### Current Problem

Our `FAudioMCPBuilderManager::BuildToAsset()` currently calls:

```cpp
TScriptInterface<IMetaSoundDocumentInterface> BuiltMetaSound =
    ActiveBuilder.Get()->BuildNewMetaSound(FName(*Name));
```

This creates a **transient** MetaSound that is NOT saved to disk. The `Path` parameter is accepted but ignored.

### Required Fix

Replace with `UMetaSoundEditorSubsystem::BuildToAsset()`:

```cpp
bool FAudioMCPBuilderManager::BuildToAsset(const FString& Name, const FString& Path, FString& OutError)
{
    // ... validation ...

    UMetaSoundEditorSubsystem* EditorSubsystem = GEditor->GetEditorSubsystem<UMetaSoundEditorSubsystem>();
    if (!EditorSubsystem)
    {
        OutError = TEXT("MetaSoundEditorSubsystem not available (editor-only)");
        return false;
    }

    EMetaSoundBuilderResult Result;
    TScriptInterface<IMetaSoundDocumentInterface> SavedAsset = EditorSubsystem->BuildToAsset(
        ActiveBuilder.Get(),
        TEXT("UEAudioMCP"),  // Author
        *Name,               // AssetName
        *Path,               // PackagePath (e.g. "/Game/Audio")
        Result,
        nullptr              // TemplateSoundWave
    );

    if (Result != EMetaSoundBuilderResult::Succeeded || !SavedAsset.GetObject())
    {
        OutError = FString::Printf(TEXT("Failed to save MetaSound '%s' to '%s'"), *Name, *Path);
        return false;
    }

    // Store reference for OpenInEditor command
    LastBuiltAsset = SavedAsset.GetObject();

    UE_LOG(LogAudioMCPBuilder, Log, TEXT("Saved MetaSound asset: %s at %s"),
        *Name, *SavedAsset.GetObject()->GetPathName());
    return true;
}
```

### Additional Changes Needed

1. **Add MetasoundEditor module dependency** in `.Build.cs`
2. **Add `#include "MetaSoundEditorSubsystem.h"`** to BuilderManager.cpp
3. **Add new command: `open_in_editor`** that calls `UAssetEditorSubsystem::OpenEditorForAsset()`
4. **Consider moving SetNodeLocation** calls to use EditorSubsystem instead of Builder directly
5. **Store `LastBuiltAsset`** as a `TWeakObjectPtr<UObject>` member for the open_in_editor command

### SetNodeLocation Migration

Current code in AddNode():
```cpp
#if WITH_EDITOR
    ActiveBuilder.Get()->SetNodeLocation(NodeHandle, FVector2D(PosX, PosY), Result);
#endif
```

Should become:
```cpp
#if WITH_EDITOR
    UMetaSoundEditorSubsystem* EditorSS = GEditor->GetEditorSubsystem<UMetaSoundEditorSubsystem>();
    if (EditorSS)
    {
        EditorSS->SetNodeLocation(ActiveBuilder.Get(), NodeHandle, FVector2D(PosX, PosY), Result);
    }
#endif
```

</warnings>

---

## Alternative Approach: Manual SavePackage

If `UMetaSoundEditorSubsystem::BuildToAsset()` is unavailable or has issues, the manual approach:

```cpp
// 1. Build transient first
TScriptInterface<IMetaSoundDocumentInterface> TransientMS = Builder->BuildNewMetaSound(FName(*Name));
UObject* MSObject = TransientMS.GetObject();

// 2. Create a package
FString PackageName = Path / Name; // e.g. "/Game/Audio/MySineTone"
UPackage* Package = CreatePackage(*PackageName);

// 3. Duplicate the transient into the persistent package
UObject* SavedObject = StaticDuplicateObject(MSObject, Package, FName(*Name));
SavedObject->SetFlags(RF_Public | RF_Standalone);
SavedObject->MarkPackageDirty();

// 4. Notify asset registry
FAssetRegistryModule::AssetCreated(SavedObject);

// 5. Save to disk
FString PackageFileName = FPackageName::LongPackageNameToFilename(
    PackageName, FPackageName::GetAssetPackageExtension());

FSavePackageArgs SaveArgs;
SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
SaveArgs.SaveFlags = SAVE_NoError;

bool bSaved = UPackage::SavePackage(Package, SavedObject, *PackageFileName, SaveArgs);
```

**Warning**: This manual approach may not properly set up MetaSound-specific internal state (document registration, node class registry, etc.). `BuildToAsset()` is strongly preferred.

---

## Resources

<references>
- [UMetaSoundBuilderBase API (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/MetasoundEngine/UMetaSoundBuilderBase) -- Full C++ API reference
- [MetaSound Builder API Guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasound-builder-api-in-unreal-engine) -- Official overview with examples
- [UMetaSoundEditorSubsystem API (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/MetasoundEditor/UMetaSoundEditorSubsystem) -- Editor subsystem with BuildToAsset
- [Python API: MetaSoundBuilderBase](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MetaSoundBuilderBase?application_version=5.7) -- Python bindings (cleaner signatures)
- [Python API: MetaSoundEditorSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MetaSoundEditorSubsystem?application_version=5.7) -- Python editor subsystem
- [BuildNewMetaSound Blueprint API](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Audio/MetaSound/Builder/BuildNewMetaSound) -- Blueprint reference
- [Builder Blueprint Functions](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Audio/MetaSound/Builder) -- All builder Blueprint functions
- [SetNodeLocation Blueprint API](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/Audio/MetaSound/Builder/Editor/SetNodeLocation) -- Node positioning
- [UAssetEditorSubsystem::OpenEditorForAsset](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Editor/UnrealEd/Subsystems/UAssetEditorSubsystem/OpenEditorForAsset/2) -- Open asset in editor
- [SavePackage Pattern](https://georgy.dev/posts/save-uobject-to-package/) -- Generic UObject save pattern
- [UPackage::SavePackage API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/CoreUObject/UPackage/SavePackage) -- Low-level package save
- [FAssetEditorManager Migration](https://forums.unrealengine.com/t/fasseteditormanager-missing-in-ue5/524878) -- UE4->UE5 migration notes
</references>

---

## Metadata

<meta>
research-date: 2026-02-08
confidence: high
version-checked: UE 5.7
key-apis: UMetaSoundEditorSubsystem::BuildToAsset, UAssetEditorSubsystem::OpenEditorForAsset, UMetaSoundBuilderBase::BuildNewMetaSound
modules-required: MetasoundEngine, MetasoundEditor, UnrealEd
editor-only: BuildToAsset, SetNodeLocation (EditorSubsystem), OpenEditorForAsset
runtime-safe: BuildNewMetaSound, BuildAndOverwriteMetaSound, Audition
</meta>
