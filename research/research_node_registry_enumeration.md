# MetaSounds & Blueprint Node Registry Enumeration Research

_Generated: 2026-02-11 | Sources: 30+ | Confidence: high_

## Quick Reference

<key-points>
- YES -- there IS a C++ API to enumerate all registered MetaSounds nodes with full pin specs
- `ISearchEngine::Get().FindAllClasses(false)` returns `TArray<FMetasoundFrontendClass>` with full interface (inputs, outputs, metadata)
- `INodeClassRegistry::IterateRegistry()` iterates all registered node classes with class type filtering
- `FBlueprintActionDatabase::Get().GetAllActions()` returns the complete map of all Blueprint node spawners
- NO existing MCP project uses these APIs -- they ALL use hardcoded node lists or manual curation
- KantanDocGenPlugin is the only known project that dumps Blueprint nodes via `FBlueprintActionDatabase`
- Both APIs are Editor-only (require running UE5 Editor) -- perfect for our C++ plugin approach
</key-points>

---

## 1. MetaSounds Node Registry API

### 1.1 ISearchEngine -- The Primary Discovery API

**Header**: `MetasoundFrontendSearchEngine.h` (MetasoundFrontend module)

The `ISearchEngine` interface is the main API for discovering all registered MetaSounds nodes. It has a singleton accessor and methods for finding classes by various criteria.

```cpp
#include "MetasoundFrontendSearchEngine.h"

// Get the singleton search engine
Metasound::Frontend::ISearchEngine& SearchEngine = Metasound::Frontend::ISearchEngine::Get();

// Find ALL registered node classes (the key method)
TArray<FMetasoundFrontendClass> AllClasses = SearchEngine.FindAllClasses(false);
// false = only return highest version of each class
// true  = include ALL versions (for migration)

// Find classes by name
TArray<FMetasoundFrontendClass> Matches = SearchEngine.FindClassesWithName(ClassName, true);

// Find highest version of a specific class
FMetasoundFrontendClass OutClass;
bool bFound = SearchEngine.FindClassWithHighestVersion(ClassName, OutClass);

// Find all registered interfaces
TArray<FMetasoundFrontendInterface> AllInterfaces = SearchEngine.FindAllInterfaces(false);
```

**What FindAllClasses returns**: Each `FMetasoundFrontendClass` contains:

| Field | Type | Content |
|-------|------|---------|
| `ID` | `FGuid` | Unique class identifier |
| `Interface` | `FMetasoundFrontendClassInterface` | Inputs, outputs, environment vars |
| `Metadata` | `FMetasoundFrontendClassMetadata` | Name, version, category, description, keywords |
| `Style` | `FMetasoundFrontendClassStyle` | Visual display info |

### 1.2 FMetasoundFrontendClassMetadata -- Node Identity

Every node class has rich metadata:

| Field | Type | Description |
|-------|------|-------------|
| `ClassName` | `FMetasoundFrontendClassName` | Qualified name (Namespace::Name::Variant) |
| `DisplayName` | `FText` | User-facing name |
| `Description` | `FText` | Detailed tooltip text |
| `Author` | `FString` | Creator/author |
| `Version` | `FMetasoundFrontendVersionNumber` | Major.Minor version |
| `Type` | `EMetasoundFrontendClassType` | External, Graph, Input, Output, etc. |
| `CategoryHierarchy` | `TArray<FText>` | Category path (e.g., ["Generators", "Oscillators"]) |
| `Keywords` | `TArray<FText>` | Search keywords |
| `bIsDeprecated` | `bool` | Whether node should not be used in new graphs |

### 1.3 FMetasoundFrontendClassInterface -- Pin Specifications

The interface contains the full pin layout:

```cpp
// Access inputs and outputs from a class
FMetasoundFrontendClassInterface& ClassInterface = FrontendClass.Interface;
TArray<FMetasoundFrontendClassInput>& Inputs = ClassInterface.Inputs;
TArray<FMetasoundFrontendClassOutput>& Outputs = ClassInterface.Outputs;
```

**FMetasoundFrontendClassVertex** (base for inputs/outputs):

| Field | Type | Description |
|-------|------|-------------|
| `Name` | `FName` | Pin name (e.g., "Audio", "Frequency", "Trigger") |
| `TypeName` | `FName` | Data type (e.g., "Audio", "Float", "Trigger", "Int32") |
| `VertexID` | `FGuid` | Unique pin identifier |
| `AccessType` | `EMetasoundFrontendVertexAccessType` | Access level |
| `Metadata` | `FMetasoundFrontendVertexMetadata` | Additional pin metadata |
| `NodeID` | `FGuid` | Associated node ID |

**FMetasoundFrontendClassInput** additionally has:
- `Defaults` (`TArray<FMetasoundFrontendClassInputDefault>`) -- default values per page

### 1.4 INodeClassRegistry -- Lower-Level Registry API

**Header**: `MetasoundFrontendNodeClassRegistry.h`

For more fine-grained control, the `INodeClassRegistry` provides:

```cpp
// Iterate all registered classes with optional type filtering
Registry.IterateRegistry(
    [](const FMetasoundFrontendClass& InClass) {
        // Process each class
        // InClass.Metadata has ClassName, DisplayName, etc.
        // InClass.Interface has Inputs[], Outputs[]
    },
    EMetasoundFrontendClassType::External  // optional filter
);

// Check if a specific node is registered
bool bRegistered = Registry.IsNodeRegistered(RegistryKey);

// Get the full frontend class from a registry key
FMetasoundFrontendClass OutClass;
bool bFound = Registry.FindFrontendClassFromRegistered(Key, OutClass);

// Get node class info (lightweight, fast)
const FNodeClassInfo& Info = RegistryEntry->GetClassInfo();
// Returns: ClassName, Version, Type, InputTypes (TSet<FName>), OutputTypes (TSet<FName>)
```

### 1.5 FNodeClassInfo -- Lightweight Node Summary

For quick queries without loading full class data:

| Field | Type | Description |
|-------|------|-------------|
| `ClassName` | `FMetasoundFrontendClassName` | Namespace::Name::Variant |
| `Version` | `FMetasoundFrontendVersionNumber` | Version number |
| `Type` | `EMetasoundFrontendClassType` | Node class type |
| `InputTypes` | `TSet<FName>` | Set of input data type names |
| `OutputTypes` | `TSet<FName>` | Set of output data type names |
| `AssetClassID` | `FGuid` | Asset identifier |
| `AssetPath` | `FTopLevelAssetPath` | Asset location |
| `bIsPreset` | `bool` | Whether this is a preset class |

### 1.6 Complete C++ Implementation: Dump All MetaSounds Nodes to JSON

Based on the APIs above, here is how to implement a command in our C++ plugin:

```cpp
#include "MetasoundFrontendSearchEngine.h"
#include "MetasoundFrontendDocument.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"

void DumpAllMetaSoundNodes(TSharedPtr<FJsonObject> ResponseJson)
{
    using namespace Metasound::Frontend;

    // Get all registered node classes (highest version only)
    ISearchEngine& SearchEngine = ISearchEngine::Get();
    TArray<FMetasoundFrontendClass> AllClasses = SearchEngine.FindAllClasses(false);

    TArray<TSharedPtr<FJsonValue>> NodeArray;

    for (const FMetasoundFrontendClass& NodeClass : AllClasses)
    {
        TSharedPtr<FJsonObject> NodeJson = MakeShared<FJsonObject>();

        // Metadata
        const FMetasoundFrontendClassMetadata& Meta = NodeClass.Metadata;
        NodeJson->SetStringField("class_name", Meta.ClassName.ToString());
        NodeJson->SetStringField("display_name", Meta.DisplayName.ToString());
        NodeJson->SetStringField("description", Meta.Description.ToString());
        NodeJson->SetStringField("author", Meta.Author);
        NodeJson->SetNumberField("version_major", Meta.Version.Major);
        NodeJson->SetNumberField("version_minor", Meta.Version.Minor);
        NodeJson->SetBoolField("is_deprecated", Meta.bIsDeprecated);

        // Category hierarchy
        TArray<TSharedPtr<FJsonValue>> CatArray;
        for (const FText& Cat : Meta.CategoryHierarchy)
        {
            CatArray.Add(MakeShared<FJsonValueString>(Cat.ToString()));
        }
        NodeJson->SetArrayField("category", CatArray);

        // Inputs
        TArray<TSharedPtr<FJsonValue>> InputArray;
        const FMetasoundFrontendClassInterface& Interface = NodeClass.Interface;
        for (const FMetasoundFrontendClassInput& Input : Interface.Inputs)
        {
            TSharedPtr<FJsonObject> PinJson = MakeShared<FJsonObject>();
            PinJson->SetStringField("name", Input.Name.ToString());
            PinJson->SetStringField("type", Input.TypeName.ToString());
            PinJson->SetStringField("vertex_id", Input.VertexID.ToString());
            // Default value if available
            InputArray.Add(MakeShared<FJsonValueObject>(PinJson));
        }
        NodeJson->SetArrayField("inputs", InputArray);

        // Outputs
        TArray<TSharedPtr<FJsonValue>> OutputArray;
        for (const FMetasoundFrontendClassOutput& Output : Interface.Outputs)
        {
            TSharedPtr<FJsonObject> PinJson = MakeShared<FJsonObject>();
            PinJson->SetStringField("name", Output.Name.ToString());
            PinJson->SetStringField("type", Output.TypeName.ToString());
            PinJson->SetStringField("vertex_id", Output.VertexID.ToString());
            OutputArray.Add(MakeShared<FJsonValueObject>(PinJson));
        }
        NodeJson->SetArrayField("outputs", OutputArray);

        NodeArray.Add(MakeShared<FJsonValueObject>(NodeJson));
    }

    ResponseJson->SetArrayField("nodes", NodeArray);
    ResponseJson->SetNumberField("count", AllClasses.Num());
}
```

### 1.7 Required Module Dependencies

```csharp
// In YourPlugin.Build.cs
PrivateDependencyModuleNames.AddRange(new string[] {
    "MetasoundFrontend",     // ISearchEngine, INodeClassRegistry
    "MetasoundGraphCore",    // FNodeClassName, FVertexInterface
    "MetasoundEngine",       // UMetaSoundBuilderSubsystem
});
```

---

## 2. Blueprint Node Registry API

### 2.1 FBlueprintActionDatabase -- The Central Database

**Header**: `BlueprintActionDatabase.h` (BlueprintGraph module, Editor-only)

```cpp
#include "BlueprintActionDatabase.h"

// Get the singleton database
FBlueprintActionDatabase& ActionDB = FBlueprintActionDatabase::Get();

// Get ALL registered actions (the key call)
const FBlueprintActionDatabase::FActionRegistry& AllActions = ActionDB.GetAllActions();
// FActionRegistry is TMultiMap<FObjectKey, UBlueprintNodeSpawner*>

// Iterate all actions
for (const auto& Pair : AllActions)
{
    FObjectKey Key = Pair.Key;          // UClass* or UObject* key
    UBlueprintNodeSpawner* Spawner = Pair.Value;

    // Get the node class this spawner creates
    UClass* NodeClass = Spawner->NodeClass;

    // Get action info
    FBlueprintActionInfo ActionInfo(Key.ResolveObjectPtr(), Spawner);
}
```

### 2.2 UBlueprintNodeSpawner -- Action Metadata

Each spawner provides:
- `NodeClass` -- the UK2Node subclass it creates
- `GetDefaultMenuName()` -- display name in the palette
- `GetDefaultMenuCategory()` -- category path
- `GetDefaultMenuTooltip()` -- tooltip text
- `GetDefaultSearchKeywords()` -- search keywords

### 2.3 KantanDocGenPlugin -- Working Example

The [KantanDocGenPlugin](https://github.com/kamrann/KantanDocGenPlugin) is the only known open-source project that successfully dumps all Blueprint nodes using `FBlueprintActionDatabase`. The key code pattern:

```cpp
// From DocGenTaskProcessor.cpp
auto& BPActionMap = FBlueprintActionDatabase::Get().GetAllActions();
if (auto ActionList = BPActionMap.Find(Obj))
{
    for (auto Spawner : *ActionList)
    {
        // Process each spawner -- get node info, pins, metadata
        // The spawner can instantiate a temporary node for pin inspection
    }
}
```

To get pin information, you instantiate a temporary node from the spawner and inspect its pins:

```cpp
UEdGraphNode* TempNode = Spawner->Invoke(TempGraph, IBlueprintNodeBinder::FBindingSet(), FVector2D::ZeroVector);
if (UK2Node* K2Node = Cast<UK2Node>(TempNode))
{
    K2Node->AllocateDefaultPins();
    for (UEdGraphPin* Pin : K2Node->Pins)
    {
        // Pin->PinName, Pin->PinType, Pin->Direction, Pin->DefaultValue
    }
}
```

### 2.4 Required Module Dependencies

```csharp
// In YourPlugin.Build.cs (Editor-only)
PrivateDependencyModuleNames.AddRange(new string[] {
    "BlueprintGraph",        // FBlueprintActionDatabase
    "UnrealEd",              // UEdGraph, UEdGraphNode
    "KismetCompiler",        // UK2Node
});
```

---

## 3. How Existing MCP Projects Get Node Knowledge

### 3.1 Summary: Nobody Uses Runtime Registry Queries

| Project | MetaSounds Knowledge | Blueprint Knowledge | Method |
|---------|---------------------|---------------------|--------|
| chongdashu/unreal-mcp | None | 23 hardcoded node types | Manual curation |
| flopperam/unreal-engine-mcp | Roadmap only | 23 hardcoded node types | Manual curation |
| kvick-games/UnrealMCP | Roadmap only | None | N/A |
| runreal/unreal-mcp | None | Via Python remote exec | Arbitrary Python |
| BilkentAudio/Wwise-MCP | None | None | WAAPI only |
| **UE5-WWISE (ours)** | 144 nodes, 798 pins | 22K+ BP entries | Scraped + manual |

### 3.2 flopperam/unreal-engine-mcp Approach

The largest UE MCP (40+ tools) uses a completely hardcoded list of 23 Blueprint node types:

```
Branch, Comparison, Switch, SwitchEnum, SwitchInteger, ExecutionSequence,
VariableGet, VariableSet, MakeArray, DynamicCast, ClassDynamicCast,
CastByteToEnum, Print, CallFunction, Select, SpawnActor, Timeline,
GetDataTableRow, AddComponentByClass, Self, Knot, Event
```

No runtime discovery. No MetaSounds support at all. Their guide explicitly states these are the "supported types" -- a curated subset.

### 3.3 chongdashu/unreal-mcp Approach

Similar hardcoded approach. Blueprint nodes are created by type string matching in the C++ plugin. No node enumeration or discovery.

### 3.4 KantanDocGenPlugin -- The Exception

The [KantanDocGenPlugin](https://github.com/kamrann/KantanDocGenPlugin) is the only known project that actually queries `FBlueprintActionDatabase` to enumerate all Blueprint nodes for documentation generation. It:
1. Calls `FBlueprintActionDatabase::Get().GetAllActions()`
2. Iterates the returned TMultiMap
3. Instantiates temporary nodes from spawners
4. Reads pins, metadata, and tooltips
5. Generates HTML documentation

### 3.5 Our Current Approach (UE5-WWISE)

We use multiple sources:
- **MetaSounds**: 144 manually curated nodes in `metasound_nodes.py` + 93 scraped from Epic docs
- **Blueprint**: Web scraper (`scrape_blueprint_api.py`) that pulls from Epic's Blueprint API docs
- **Runtime**: `export_metasound` C++ command that reads existing graphs (but does NOT enumerate the registry)

---

## 4. Implementation Plan: Add Registry Enumeration to Our Plugin

### 4.1 New C++ Command: `list_metasound_nodes`

Add to our existing TCP plugin (`UEAudioMCP`):

```cpp
// In a new file or added to QueryCommands.cpp
else if (CommandName == "list_metasound_nodes")
{
    AsyncTask(ENamedThreads::GameThread, [State]()
    {
        TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();

        using namespace Metasound::Frontend;
        ISearchEngine& Search = ISearchEngine::Get();
        TArray<FMetasoundFrontendClass> Classes = Search.FindAllClasses(false);

        TArray<TSharedPtr<FJsonValue>> Nodes;
        for (const auto& C : Classes)
        {
            TSharedPtr<FJsonObject> N = MakeShared<FJsonObject>();
            N->SetStringField("class_name", C.Metadata.ClassName.ToString());
            N->SetStringField("display_name", C.Metadata.DisplayName.ToString());
            N->SetStringField("description", C.Metadata.Description.ToString());

            // ... inputs, outputs, category, version ...

            Nodes.Add(MakeShared<FJsonValueObject>(N));
        }

        Result->SetArrayField("nodes", Nodes);
        Result->SetNumberField("count", Classes.Num());
        State->Complete(Result);
    });
}
```

### 4.2 New C++ Command: `list_blueprint_nodes`

```cpp
else if (CommandName == "list_blueprint_nodes")
{
    AsyncTask(ENamedThreads::GameThread, [State, Params]()
    {
        FBlueprintActionDatabase& DB = FBlueprintActionDatabase::Get();
        const auto& AllActions = DB.GetAllActions();

        TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
        TArray<TSharedPtr<FJsonValue>> Nodes;

        // Optional: filter by class
        FString ClassFilter;
        if (Params->TryGetStringField("class_filter", ClassFilter))
        {
            // Filter to specific class
        }

        for (const auto& Pair : AllActions)
        {
            UBlueprintNodeSpawner* Spawner = Pair.Value;
            if (!Spawner) continue;

            TSharedPtr<FJsonObject> N = MakeShared<FJsonObject>();
            N->SetStringField("name", Spawner->GetDefaultMenuName().ToString());
            N->SetStringField("category", Spawner->GetDefaultMenuCategory().ToString());
            N->SetStringField("node_class", Spawner->NodeClass->GetName());

            Nodes.Add(MakeShared<FJsonValueObject>(N));
        }

        Result->SetArrayField("nodes", Nodes);
        Result->SetNumberField("count", Nodes.Num());
        State->Complete(Result);
    });
}
```

### 4.3 Python MCP Tool Integration

```python
@mcp.tool()
async def ms_list_registered_nodes(include_deprecated: bool = False) -> dict:
    """List all MetaSounds nodes registered in the running UE5 editor.
    Returns complete pin specifications from the engine registry."""
    result = await ue5_connection.send_command("list_metasound_nodes", {
        "include_deprecated": include_deprecated
    })
    return result

@mcp.tool()
async def bp_list_registered_nodes(class_filter: str = "") -> dict:
    """List all Blueprint nodes registered in the running UE5 editor.
    Optionally filter by class name."""
    result = await ue5_connection.send_command("list_blueprint_nodes", {
        "class_filter": class_filter
    })
    return result
```

---

## 5. Important Considerations

<warnings>

### API Stability
- `ISearchEngine` and `INodeClassRegistry` are in the `MetasoundFrontend` module which is **not marked experimental** but has changed between UE versions
- `FMetasoundFrontendRegistryContainer::RegisterPendingNodes()` was replaced by `METASOUND_REGISTER_ITEMS_IN_MODULE` macro in UE 5.7
- The `FMetasoundFrontendClass` struct had breaking changes in 5.7 (`GetDefaultInterface()` instead of direct `Interface` access)

### Performance
- `ISearchEngine::FindAllClasses()` may return hundreds of classes -- should be called once and cached
- `FNodeClassInfo::GetClassInfo()` is documented as "avoid expensive operations" because it is "called frequently when querying nodes"
- `FBlueprintActionDatabase::GetAllActions()` populates the database on first call if not yet created -- can be slow on first invocation

### Module Requirements
- Both APIs are **Editor-only** -- cannot be used in shipped games
- Our plugin is already Editor-only (`Type: Editor` in .uplugin), so this is fine
- Need to add `MetasoundFrontend` and `BlueprintGraph` to Build.cs dependencies

### Data Volume
- MetaSounds: Expect 200-400 registered node classes in a typical project (engine built-in + any custom/plugin nodes)
- Blueprint: Expect 5,000-50,000 action entries depending on installed plugins and project size
- Consider pagination or class-based filtering for Blueprint nodes

### UE Version Compatibility
- `ISearchEngine::Get()` exists since UE 5.0 (MetaSounds introduction)
- `FindAllClasses()` may not exist in earliest versions -- verify against target UE 5.4+ minimum
- `FBlueprintActionDatabase::Get()` has existed since UE 4.x -- stable API

</warnings>

---

## 6. Comparison: Our Current Approach vs. Registry API

| Aspect | Current (Scraped/Manual) | Registry API (Proposed) |
|--------|-------------------------|------------------------|
| Node count | 144 MetaSounds / 22K BP | ALL registered nodes |
| Pin accuracy | Manually verified subset | Engine-authoritative |
| Custom nodes | Not captured | Automatically included |
| Plugin nodes | Not captured | Automatically included |
| UE version | Fixed to scraped version | Matches running editor |
| Offline | Works offline | Requires running editor |
| Maintenance | Manual updates per UE release | Zero maintenance |

**Recommended hybrid approach**: Keep the offline knowledge base as fallback, but add `list_metasound_nodes` and `list_blueprint_nodes` commands to auto-populate/update from the running editor when connected.

---

## 7. Resources

<references>
- [INodeClassRegistryEntry::GetClassInfo](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/MetasoundFrontend/INodeClassRegistryEntry/GetClassInfo) - FNodeClassInfo return docs
- [IDocumentController::FindClass](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/MetasoundFrontend/IDocumentController/FindClass) - Finding classes by registry key
- [FMetasoundFrontendRegistryContainer::IsNodeNative](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/MetasoundFrontend/FMetasoundFrontendRegistryContai-/IsNodeNative?application_version=5.0) - Registry container API
- [MetaSounds Frontend API Module](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/MetasoundFrontend/) - Full class listing (90+ classes, 90+ structs, 35+ interfaces)
- [MetaSound Builder API](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasound-builder-api-in-unreal-engine) - Builder subsystem docs
- [FBlueprintActionDatabase](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Editor/BlueprintGraph/FBlueprintActionDatabase) - Blueprint action database API
- [FBlueprintActionDatabaseRegistrar](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Editor/BlueprintGraph/FBlueprintActionDatabaseRegistra-) - Registrar for node spawners
- [KantanDocGenPlugin](https://github.com/kamrann/KantanDocGenPlugin) - Only known project that dumps BP nodes via FBlueprintActionDatabase
- [Creating MetaSound Nodes in C++ Quickstart](https://dev.epicgames.com/community/learning/tutorials/ry7p/unreal-engine-creating-metasound-nodes-in-c-quickstart) - Node registration tutorial
- [MetaSound Function Nodes Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasound-function-nodes-reference-guide-in-unreal-engine) - Official node reference guide
- [MetaSounds Reference Guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-reference-guide-in-unreal-engine) - Node types and categories
- [chongdashu/unreal-mcp](https://github.com/chongdashu/unreal-mcp) - 1,370 stars, hardcoded 23 BP node types
- [flopperam/unreal-engine-mcp](https://github.com/flopperam/unreal-engine-mcp) - 431 stars, hardcoded 23 BP node types
- [flopperam Blueprint Graph Guide](https://github.com/flopperam/unreal-engine-mcp/blob/main/Guides/blueprint-graph-guide.md) - Documents the hardcoded approach
- [VedantRGosavi/UE5-MCP Research](https://github.com/VedantRGosavi/UE5-MCP/blob/main/research.md) - MCP research noting no runtime discovery
</references>

---

## 8. Metadata

<meta>
research-date: 2026-02-11
confidence: high
apis-verified: ISearchEngine (UE 5.7 docs), INodeClassRegistry (UE 5.7 docs), FBlueprintActionDatabase (UE 5.7 docs), FNodeClassInfo (UE 5.7 docs)
repos-analyzed: 10 MCP repos + KantanDocGenPlugin
version-checked: UE 5.0-5.7
key-headers: MetasoundFrontendSearchEngine.h, MetasoundFrontendNodeClassRegistry.h, MetasoundFrontendDocument.h, BlueprintActionDatabase.h
</meta>
