# UE 5.7 Python ARFilter & Asset Query Research

_Generated: 2026-02-09 | Sources: 12+_

## Quick Reference

<key-points>
- ARFilter properties (class_paths, class_names, etc.) CANNOT be set on instances after construction in UE 5.7
- FIX: Pass all filter params as constructor kwargs: `unreal.ARFilter(class_paths=[...], recursive_classes=True)`
- ALTERNATIVE: Use `get_assets_by_class(TopLevelAssetPath, search_sub_classes)` which bypasses ARFilter entirely
- TopLevelAssetPath constructor: `unreal.TopLevelAssetPath(package_name="/Script/Engine", asset_name="SoundWave")`
- ALTERNATIVE: `EditorAssetLibrary.list_assets()` + manual class filtering (no ARFilter needed)
</key-points>

## The Problem

In UE 5.7, the following code that worked in earlier versions now fails:

```python
# BROKEN in UE 5.7
ar_filter = unreal.ARFilter()
ar_filter.class_paths = [unreal.TopLevelAssetPath("/Script/Engine", "SoundWave")]
# ERROR: ARFilter: Property 'ClassPaths' for attribute 'class_paths' on 'ARFilter' cannot be edited on instances
```

This is because Epic changed the UPROPERTY specifiers on ARFilter's struct members, making them read-only after construction. The Python binding enforces this restriction: you can no longer assign to `ar_filter.class_paths`, `ar_filter.class_names`, `ar_filter.recursive_classes`, or any other ARFilter property on an existing instance.

## Solution 1: Constructor Kwargs (RECOMMENDED)

The ARFilter constructor accepts ALL properties as keyword arguments. Pass everything at construction time:

```python
import unreal

registry = unreal.AssetRegistryHelpers.get_asset_registry()

# Single class query
ar_filter = unreal.ARFilter(
    class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "SoundWave")],
    recursive_classes=False
)
assets = registry.get_assets(ar_filter)

# Multiple classes in one filter
ar_filter = unreal.ARFilter(
    class_paths=[
        unreal.TopLevelAssetPath("/Script/Engine", "SoundWave"),
        unreal.TopLevelAssetPath("/Script/MetasoundEngine", "MetaSoundSource"),
        unreal.TopLevelAssetPath("/Script/MetasoundEngine", "MetaSoundPatch"),
    ],
    recursive_classes=True
)
assets = registry.get_assets(ar_filter)

# With package path restriction
ar_filter = unreal.ARFilter(
    class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "SoundWave")],
    package_paths=["/Game/Audio"],
    recursive_paths=True,
    recursive_classes=False
)
assets = registry.get_assets(ar_filter)
```

### Full Constructor Signature (UE 5.3-5.7)

```python
unreal.ARFilter(
    package_names: list[unreal.Name] = [],           # Filter by package names
    package_paths: list[unreal.Name] = [],           # Filter by package paths
    soft_object_paths: list[unreal.SoftObjectPath] = [],  # Filter by specific asset paths
    class_paths: list[unreal.TopLevelAssetPath] = [],     # Filter by class (NOT subclasses by default)
    recursive_class_paths_exclusion_set: list[unreal.TopLevelAssetPath] = [],  # Exclude classes when recursive
    class_names: list[unreal.Name] = [],             # DEPRECATED - use class_paths
    recursive_classes_exclusion_set: list[unreal.Name] = [],  # DEPRECATED
    recursive_paths: bool = False,                    # Recurse into subfolders
    recursive_classes: bool = False,                  # Include subclasses
    include_only_on_disk_assets: bool = False         # Exclude in-memory-only assets
)
```

### TopLevelAssetPath Constructor

```python
unreal.TopLevelAssetPath(
    package_name: str = '',   # e.g. "/Script/Engine"
    asset_name: str = ''      # e.g. "SoundWave"
)
```

## Solution 2: get_assets_by_class (SIMPLEST)

Bypasses ARFilter entirely. Available in UE 5.1+:

```python
import unreal

registry = unreal.AssetRegistryHelpers.get_asset_registry()

# Find all SoundWave assets
path = unreal.TopLevelAssetPath("/Script/Engine", "SoundWave")
assets = registry.get_assets_by_class(path, search_sub_classes=False)

# Find all MetaSoundSource assets (including subclasses)
path = unreal.TopLevelAssetPath("/Script/MetasoundEngine", "MetaSoundSource")
assets = registry.get_assets_by_class(path, search_sub_classes=True)
```

### Method Signature

```python
AssetRegistry.get_assets_by_class(
    class_path_name: unreal.TopLevelAssetPath,  # Class to search for
    search_sub_classes: bool = False              # Include derived classes
) -> list[unreal.AssetData] | None
```

### Common Class Paths for Audio

| Class | TopLevelAssetPath |
|-------|------------------|
| SoundWave | `("/Script/Engine", "SoundWave")` |
| SoundCue | `("/Script/Engine", "SoundCue")` |
| MetaSoundSource | `("/Script/MetasoundEngine", "MetaSoundSource")` |
| MetaSoundPatch | `("/Script/MetasoundEngine", "MetaSoundPatch")` |
| SoundAttenuation | `("/Script/Engine", "SoundAttenuation")` |
| SoundClass | `("/Script/Engine", "SoundClass")` |
| SoundConcurrency | `("/Script/Engine", "SoundConcurrency")` |
| SoundMix | `("/Script/Engine", "SoundMix")` |
| ReverbEffect | `("/Script/Engine", "ReverbEffect")` |
| SoundControlBus | `("/Script/AudioModulation", "SoundControlBus")` |
| SoundControlBusMix | `("/Script/AudioModulation", "SoundControlBusMix")` |
| Blueprint | `("/Script/Engine", "Blueprint")` |
| WidgetBlueprint | `("/Script/UMGEditor", "WidgetBlueprint")` |
| AnimBlueprint | `("/Script/Engine", "AnimBlueprint")` |
| AnimSequence | `("/Script/Engine", "AnimSequence")` |
| AnimMontage | `("/Script/Engine", "AnimMontage")` |

## Solution 3: EditorAssetLibrary (No Filter Object Needed)

When you just need asset paths and can filter manually:

```python
import unreal

# List all assets under a path
all_assets = unreal.EditorAssetLibrary.list_assets("/Game/Audio", recursive=True)

# Load and check class manually
for asset_path in all_assets:
    asset_data = unreal.EditorAssetLibrary.find_asset_data(asset_path)
    if asset_data.asset_class_path.asset_name == "SoundWave":
        # Process the SoundWave
        pass
```

This is slower than ARFilter-based queries for large projects but avoids the immutable-struct issue entirely.

## Solution 4: Tag-Based Filtering

```python
import unreal

# Find assets by metadata tag
assets = unreal.EditorAssetLibrary.list_asset_by_tag_value("AssetClass", "SoundWave")
```

Limited usefulness -- not all assets have the tags you need.

## Fixed Script: find_assets_by_class

The broken code in `scripts/dump_blueprints_ue5.py` (lines 73-96) should be replaced:

```python
# BEFORE (BROKEN in UE 5.7):
def find_assets_by_class(class_names):
    registry = get_asset_registry()
    results = []
    for class_name in class_names:
        ar_filter = unreal.ARFilter()
        ar_filter.class_paths = [unreal.TopLevelAssetPath("/Script/Engine", class_name)]
        assets = registry.get_assets(ar_filter)
        ...

# AFTER (WORKS in UE 5.7) - Option A: Constructor kwargs
def find_assets_by_class(class_names):
    registry = get_asset_registry()
    results = []
    for class_name in class_names:
        ar_filter = unreal.ARFilter(
            class_paths=[unreal.TopLevelAssetPath("/Script/Engine", class_name)]
        )
        assets = registry.get_assets(ar_filter)
        if not assets:
            for module in ["CoreUObject", "UMG", "MetasoundEngine", "AudioModulation", "AudioMixer"]:
                ar_filter = unreal.ARFilter(
                    class_paths=[unreal.TopLevelAssetPath("/Script/" + module, class_name)]
                )
                assets = registry.get_assets(ar_filter)
                if assets:
                    break
        if assets:
            for asset in assets:
                results.append({
                    "package_name": str(asset.package_name),
                    "asset_name": str(asset.asset_name),
                    "asset_class": str(asset.asset_class_path.asset_name),
                    "package_path": str(asset.package_path),
                })
    return results

# AFTER (WORKS in UE 5.7) - Option B: get_assets_by_class (no ARFilter)
CLASS_MODULE_MAP = {
    "SoundWave": "Engine", "SoundCue": "Engine", "SoundAttenuation": "Engine",
    "SoundClass": "Engine", "SoundConcurrency": "Engine", "SoundMix": "Engine",
    "ReverbEffect": "Engine", "Blueprint": "Engine", "AnimBlueprint": "Engine",
    "AnimSequence": "Engine", "AnimMontage": "Engine",
    "MetaSoundSource": "MetasoundEngine", "MetaSoundPatch": "MetasoundEngine",
    "SoundControlBus": "AudioModulation", "SoundControlBusMix": "AudioModulation",
    "WidgetBlueprint": "UMGEditor",
}

def find_assets_by_class(class_names):
    registry = get_asset_registry()
    results = []
    for class_name in class_names:
        module = CLASS_MODULE_MAP.get(class_name, "Engine")
        path = unreal.TopLevelAssetPath("/Script/" + module, class_name)
        assets = registry.get_assets_by_class(path, search_sub_classes=False)
        if not assets and module == "Engine":
            # Fallback: try other modules
            for alt_module in ["CoreUObject", "UMG", "MetasoundEngine", "AudioModulation", "AudioMixer"]:
                path = unreal.TopLevelAssetPath("/Script/" + alt_module, class_name)
                assets = registry.get_assets_by_class(path)
                if assets:
                    break
        if assets:
            for asset in assets:
                results.append({
                    "package_name": str(asset.package_name),
                    "asset_name": str(asset.asset_name),
                    "asset_class": str(asset.asset_class_path.asset_name),
                    "package_path": str(asset.package_path),
                })
    return results
```

## Other Useful AssetRegistry Methods (UE 5.6-5.7)

```python
registry = unreal.AssetRegistryHelpers.get_asset_registry()

# Get ALL assets (slow, use sparingly)
all_assets = registry.get_all_assets(include_only_on_disk_assets=False)

# Get assets in a folder
folder_assets = registry.get_assets_by_path("/Game/Audio", recursive=True)

# Get assets in multiple folders
multi_folder = registry.get_assets_by_paths(
    ["/Game/Audio", "/Game/SFX"],
    recursive=True
)

# Get specific asset by path
asset = registry.get_asset_by_object_path("/Game/Audio/MySoundWave")  # deprecated
asset = registry.k2_get_asset_by_object_path("/Game/Audio/MySoundWave")  # modern

# Post-filter an existing asset list
filtered = registry.run_assets_through_filter(asset_list, ar_filter)
```

## Important Considerations

<warnings>
- ARFilter instance properties are READ-ONLY in UE 5.7 -- must use constructor kwargs
- class_names is DEPRECATED since UE 5.1 -- use class_paths with TopLevelAssetPath
- get_all_assets() can be extremely slow on large projects -- always prefer filtered queries
- TopLevelAssetPath requires the correct module name ("/Script/Engine" vs "/Script/MetasoundEngine")
- get_assets_by_class returns None (not empty list) when no matches found -- always check for None
- The UE Python API is marked "Experimental" and may change between versions
- EditorAssetLibrary requires the "Editor Scripting Utilities" plugin to be enabled
</warnings>

## Resources

<references>
- [ARFilter Python API (UE 5.3)](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/ARFilter?application_version=5.3) - Constructor signature, all properties
- [AssetRegistry Python API (UE 5.6)](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AssetRegistry?application_version=5.6) - All query methods
- [AssetRegistry Python API (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AssetRegistry?application_version=5.7) - Latest version
- [TopLevelAssetPath (UE 5.3)](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TopLevelAssetPath?application_version=5.3) - Constructor and properties
- [Asset Registry Overview (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/asset-registry-in-unreal-engine) - Concepts and C++ patterns
- [EditorAssetLibrary (UE 5.3)](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorAssetLibrary?application_version=5.3) - List/load helpers
- [Python Scripting (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python) - Official guide
- [Get Assets by Class Blueprint (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/BlueprintAPI/AssetRegistry/GetAssetsbyClass) - Blueprint equivalent
</references>

## Metadata

<meta>
research-date: 2026-02-09
confidence: high
version-checked: UE 5.1, 5.2, 5.3, 5.4, 5.6, 5.7
affected-file: scripts/dump_blueprints_ue5.py (lines 73-96)
root-cause: ARFilter UPROPERTY specifiers changed to disallow instance-level property assignment
</meta>
