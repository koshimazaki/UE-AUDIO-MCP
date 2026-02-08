# MetaSounds Custom Node Display Style & Colors - Research Summary

_Generated: 2026-02-08 | Sources: 12+_

<key-points>
- FNodeDisplayStyle controls visibility (show names, literals, icon) but has NO color field
- Node colors in MetaSounds are determined by the Editor module (MetasoundEditor), not the node registration API
- CategoryHierarchy (TArray of FText) controls menu placement, not node color
- To customize colors you must modify the editor-side code (SGraphNode pattern), not FNodeClassMetadata
- FNodeClassMetadata has 13 fields: the key styling ones are DisplayStyle, CategoryHierarchy, and ImageName
</key-points>

## Overview

<summary>
MetaSounds custom nodes in UE5 are registered via FNodeClassMetadata, which includes a FNodeDisplayStyle struct
for controlling visual layout in the graph editor. However, the styling system is deliberately limited on the
node registration side -- it controls WHAT is shown (names, literals, icons) but NOT colors. Node title and body
colors are handled entirely by the MetasoundEditor module, which maps categories or node types to colors internally.
This means custom plugin nodes cannot directly set their own color scheme through the public node registration API.
</summary>

## FNodeClassMetadata - Complete Struct Reference

**Header**: `Engine/Plugins/Runtime/Metasound/Source/MetasoundGraphCore/Public/MetasoundNodeInterface.h`

```cpp
struct FNodeClassMetadata
{
    FNodeClassName       ClassName;          // {Namespace, Name, Variant} - registration key
    int32                MajorVersion;       // Used for registration and lookup
    int32                MinorVersion;       // Minor version
    FText                DisplayName;        // Shown in editor
    FText                Description;        // Tooltip/description
    FString              Author;             // Author info
    FText                PromptIfMissing;    // Message when plugin not loaded
    FVertexInterface     DefaultInterface;   // Input/output pins
    TArray<FText>        CategoryHierarchy;  // Menu placement hierarchy
    TArray<FText>        Keywords;           // Search keywords
    FNodeDisplayStyle    DisplayStyle;       // Visual layout control
    ENodeClassAccessFlags AccessFlags;       // Access control
    bool                 bDeprecated;        // Deprecation flag

    static const FNodeClassMetadata& GetEmpty();
};
```

## FNodeClassName - Node Identity

**Header**: Same file (`MetasoundNodeInterface.h`)

```cpp
class FNodeClassName
{
    FName Namespace;  // e.g., "UE", "MyPlugin"
    FName Name;       // e.g., "Volume", "Dust (Audio)"
    FName Variant;    // e.g., "Audio" (variant for polymorphism)

    // Nodes with same Namespace+Name but different Variant are interoperable
    FString ToString(); // Returns "Namespace.Name.Variant"
};
```

**Usage pattern**:
```cpp
// Engine convention
Info.ClassName = { TEXT("UE"), TEXT("Volume"), TEXT("Audio") };

// Custom plugin convention
Metadata.ClassName = { TEXT("UE"), TEXT("Dust (Audio)"), TEXT("Audio") };

// Using StandardNodes namespace
FNodeClassName { StandardNodes::Namespace, "FM Generator Node", StandardNodes::AudioVariant }
```

## FNodeDisplayStyle - Visual Layout Control

**Header**: Same file (`MetasoundNodeInterface.h`)

```cpp
struct FNodeDisplayStyle
{
    bool  bShowInputNames;   // Show input pin names in visual layout
    bool  bShowLiterals;     // Show input literal values in visual layout
    bool  bShowName;         // Show node name in visual layout
    bool  bShowOutputNames;  // Show output pin names in visual layout
    FName ImageName;         // Icon name identifier associated with node
};
```

**Critical finding**: There is NO color field. FNodeDisplayStyle controls layout visibility and icon assignment only.

## CategoryHierarchy - Menu Placement

CategoryHierarchy determines where the node appears in the right-click context menu. It does NOT directly control node color in the graph editor.

```cpp
// Single category
Info.CategoryHierarchy = { LOCTEXT("VolumeCategory", "Utils") };

// Custom plugin category
Metadata.CategoryHierarchy = { METASOUND_LOCTEXT("Custom", "Branches") };

// Nested hierarchy
Metadata.CategoryHierarchy = {
    METASOUND_LOCTEXT("Cat1", "DSP"),
    METASOUND_LOCTEXT("Cat2", "Filters")
};

// Empty (no category)
{ }  // or TArray<FText>()
```

## How Node Colors Actually Work

### The Editor Module Handles Colors

Node colors in the MetaSounds graph editor are NOT set via `FNodeClassMetadata` or `FNodeDisplayStyle`. They are determined by the **MetasoundEditor** module, which lives in:

```
Engine/Plugins/Runtime/Metasound/Source/MetasoundEditor/
```

The editor module contains:
- `MetasoundEditorGraphNode.h/cpp` - UEdGraphNode subclass for MetaSounds
- `SMetasoundGraphNode.h/cpp` - Slate widget rendering the node

These classes follow the standard UE5 SGraphNode pattern where colors are determined by:
1. Overriding `GetNodeTitleColor()` (returns FLinearColor)
2. Overriding `GetNodeBodyTintColor()` (returns FLinearColor)
3. Internal category-to-color mapping within the editor module

### Approaches to Custom Colors

**Approach 1: Category-Based (Indirect, Limited)**
The editor may map certain category strings to colors. By using standard category names that match built-in categories, your nodes may inherit their colors:
```cpp
// These standard categories have established colors in the editor:
// "Generators", "Filters", "Envelopes", "Effects", "Mix", "Spatialization", etc.
Metadata.CategoryHierarchy = { METASOUND_LOCTEXT("Cat", "Generators") };
```

**Approach 2: Editor Module Modification (Direct, Engine Source Required)**
Requires modifying engine source or creating an editor plugin that hooks into the MetaSoundEditor module:
```cpp
// Hypothetical - would need to subclass or patch MetasoundEditorGraphNode
FLinearColor UMyMetasoundEditorGraphNode::GetNodeTitleColor() const
{
    // Custom white/yellow scheme
    return FLinearColor(1.0f, 0.95f, 0.8f);  // Warm white
}

FLinearColor UMyMetasoundEditorGraphNode::GetNodeBodyTintColor() const
{
    return FLinearColor(0.15f, 0.15f, 0.15f);  // Dark body
}
```

**Approach 3: ImageName for Icons (Supported)**
The only visual customization directly supported is setting a custom icon:
```cpp
FNodeDisplayStyle Style;
Style.ImageName = FName("MyCustomIcon");  // Must be registered with Slate
Style.bShowName = true;
Style.bShowInputNames = true;
Style.bShowOutputNames = true;
Style.bShowLiterals = false;
```

## Complete Registration Example

```cpp
#include "MetasoundExecutableOperator.h"
#include "MetasoundPrimitives.h"
#include "MetasoundNodeRegistrationMacro.h"
#include "MetasoundFacade.h"
#include "MetasoundParamHelper.h"

#define LOCTEXT_NAMESPACE "MyPlugin_CustomNode"

namespace MyPlugin
{
    using namespace Metasound;

    namespace CustomNodeNames
    {
        METASOUND_PARAM(InputAudio, "In", "Audio input signal.");
        METASOUND_PARAM(InputAmount, "Amount", "Effect amount (0-1).");
        METASOUND_PARAM(OutputAudio, "Out", "Processed audio output.");
    }

    class FCustomOperator : public TExecutableOperator<FCustomOperator>
    {
    public:
        // ... constructor, BindInputs, BindOutputs, Execute ...

        static const FVertexInterface& GetVertexInterface()
        {
            using namespace CustomNodeNames;
            static const FVertexInterface Interface(
                FInputVertexInterface(
                    TInputDataVertex<FAudioBuffer>(METASOUND_GET_PARAM_NAME_AND_METADATA(InputAudio)),
                    TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InputAmount), 0.5f)
                ),
                FOutputVertexInterface(
                    TOutputDataVertex<FAudioBuffer>(METASOUND_GET_PARAM_NAME_AND_METADATA(OutputAudio))
                )
            );
            return Interface;
        }

        static const FNodeClassMetadata& GetNodeInfo()
        {
            auto InitNodeInfo = []() -> FNodeClassMetadata
            {
                FNodeClassMetadata Info;

                // Identity
                Info.ClassName         = { TEXT("UE"), TEXT("My Custom Effect"), TEXT("Audio") };
                Info.MajorVersion      = 1;
                Info.MinorVersion      = 0;

                // Display
                Info.DisplayName       = LOCTEXT("DisplayName", "My Custom Effect");
                Info.Description       = LOCTEXT("Description", "A custom audio effect node.");
                Info.Author            = TEXT("My Studio");
                Info.PromptIfMissing   = PluginNodeMissingPrompt;

                // Interface
                Info.DefaultInterface  = GetVertexInterface();

                // Category (controls menu placement, may influence editor color)
                Info.CategoryHierarchy = { LOCTEXT("Category", "Effects") };

                // Keywords for search
                Info.Keywords = {
                    LOCTEXT("Keyword1", "custom"),
                    LOCTEXT("Keyword2", "effect")
                };

                // Display style (layout control only, no color)
                FNodeDisplayStyle Style;
                Style.bShowName = true;
                Style.bShowInputNames = true;
                Style.bShowOutputNames = true;
                Style.bShowLiterals = true;
                Style.ImageName = NAME_None;  // No custom icon
                Info.DisplayStyle = Style;

                return Info;
            };

            static const FNodeClassMetadata Info = InitNodeInfo();
            return Info;
        }

        static TUniquePtr<IOperator> CreateOperator(
            const FBuildOperatorParams& InParams, FBuildResults& OutResults)
        {
            // ... create operator from input data ...
        }

        void Execute() { /* DSP processing */ }
    };

    class FCustomNode : public FNodeFacade
    {
    public:
        FCustomNode(const FNodeInitData& InitData)
            : FNodeFacade(InitData.InstanceName, InitData.InstanceID,
                         TFacadeOperatorClass<FCustomOperator>())
        {}
    };

    METASOUND_REGISTER_NODE(FCustomNode);
}

#undef LOCTEXT_NAMESPACE
```

## Module Registration (UE 5.7+)

```cpp
// In your module's StartupModule:
#include "MetasoundFrontendModuleRegistrationMacros.h"

void FMyModule::StartupModule()
{
    METASOUND_REGISTER_ITEMS_IN_MODULE;
}

void FMyModule::ShutdownModule()
{
    METASOUND_UNREGISTER_ITEMS_IN_MODULE;
}
```

## Build Dependencies

```csharp
// .Build.cs
PublicDependencyModuleNames.AddRange(new string[] {
    "MetasoundFrontend",
    "MetasoundGraphCore"
});

PrivateDependencyModuleNames.AddRange(new string[] {
    "MetasoundEngine",
    "AudioMixer",
    "SignalProcessing"
});
```

## Important Considerations

<warnings>
- FNodeDisplayStyle has NO color field - only layout visibility and icon name
- CategoryHierarchy controls menu placement, not node color directly
- Node colors are determined by the MetasoundEditor module (engine editor code)
- To set custom colors you must modify engine source or hook into the editor module
- FNodeClassName Variant enables polymorphism - same name+namespace with different variants are interoperable
- bDeprecated flag exists but behavior is undocumented in public API
- ENodeClassAccessFlags enum values are not publicly documented
- The MetaSound editor is a separate plugin module from MetasoundGraphCore
- Standard category names (Generators, Filters, Envelopes, Effects, Mix) MAY inherit built-in category colors
- ImageName must reference a Slate icon registered with FSlateStyleRegistry
- UE 5.7 uses METASOUND_REGISTER_ITEMS_IN_MODULE for module-level registration
</warnings>

## Real-World Examples

### alexirae/unreal-audio-dsp-template-UE5
```cpp
Info.CategoryHierarchy = { LOCTEXT("DSPTemplate_VolumeNodeCategory", "Utils") };
// No DisplayStyle set (uses defaults)
```

### matthewscharles/metasound-branches (Dust node)
```cpp
Metadata.CategoryHierarchy = { METASOUND_LOCTEXT("Custom", "Branches") };
Metadata.Keywords = TArray<FText>(); // Empty keywords
// No DisplayStyle set (uses defaults)
```

### bh247484/UEMetasoundNodes (FM Generator)
```cpp
FNodeClassMetadata Metadata
{
    FNodeClassName { StandardNodes::Namespace, "FM Generator Node", StandardNodes::AudioVariant },
    1, 0,
    METASOUND_LOCTEXT("FMGeneratorNodeDisplayName", "FM Node"),
    METASOUND_LOCTEXT("FMGeneratorNodeDesc", "A test gain node."),
    PluginAuthor,
    PluginNodeMissingPrompt,
    NodeInterface,
    { },                    // Empty CategoryHierarchy
    { },                    // Empty Keywords
    FNodeDisplayStyle{}     // Default display style
};
```

### Tutorial Template (Epic quickstart)
```cpp
FNodeClassMetadata Metadata
{
    FNodeClassName { StandardNodes::Namespace, "Tutorial Node", StandardNodes::AudioVariant },
    1, 0,
    METASOUND_LOCTEXT("TutorialNodeDisplayName", "Tutorial Node"),
    METASOUND_LOCTEXT("TutorialNodeDesc", "Adds two floats together"),
    PluginAuthor,
    PluginNodeMissingPrompt,
    NodeInterface,
    { },                    // Category Hierarchy
    { METASOUND_LOCTEXT("TutorialNodeKeyword", "Tutorial") },
    FNodeDisplayStyle{}
};
```

## Resources

<references>
- [Epic: Creating MetaSound Nodes in C++ Quickstart](https://dev.epicgames.com/community/learning/tutorials/ry7p/unreal-engine-creating-metasound-nodes-in-c-quickstart)
- [Epic: FNodeDisplayStyle API Reference (UE 5.5)](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/MetasoundGraphCore/FNodeDisplayStyle)
- [Epic: FNodeClassMetadata API Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/MetasoundGraphCore/FNodeClassMetadata)
- [Epic: FNodeClassName API Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/MetasoundGraphCore/FNodeClassName)
- [Epic: MetaSounds Reference Guide (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-reference-guide-in-unreal-engine)
- [GitHub: alexirae/unreal-audio-dsp-template-UE5](https://github.com/alexirae/unreal-audio-dsp-template-UE5)
- [GitHub: matthewscharles/metasound-branches](https://github.com/matthewscharles/metasound-branches)
- [GitHub: bh247484/UEMetasoundNodes](https://github.com/bh247484/UEMetasoundNodes)
- [GitHub: Cycling74/RNBOMetasound](https://github.com/Cycling74/RNBOMetasound)
- [Epic Forum: Creating MetaSound Nodes in C++ Quickstart Discussion](https://forums.unrealengine.com/t/tutorial-creating-metasound-nodes-in-c-quickstart/559789)
- [UE5 MetaSounds Gist (mattetti)](https://gist.github.com/mattetti/e89739a006591289e72c5252da1de877)
- [Unreal Community Wiki: MetaSounds](https://unrealcommunity.wiki/metasounds-d660ee)
</references>

<meta>
research-date: 2026-02-08
confidence: high (API struct definitions confirmed from Epic docs, real-world usage confirmed from 4+ open-source plugins)
version-checked: UE 5.5, 5.7
key-finding: No direct color control via node registration API - colors are editor-side only
</meta>
