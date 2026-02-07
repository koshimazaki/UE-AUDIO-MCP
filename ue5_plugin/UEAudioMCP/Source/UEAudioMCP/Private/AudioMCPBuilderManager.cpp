// Copyright UE Audio MCP Project. All Rights Reserved.

#include "AudioMCPBuilderManager.h"
#include "AudioMCPNodeRegistry.h"
#include "AudioMCPTypes.h"
#include "MetasoundBuilderSubsystem.h"
#include "MetasoundSource.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/World.h"
#include "Editor.h"

DEFINE_LOG_CATEGORY_STATIC(LogAudioMCPBuilder, Log, All);

FAudioMCPBuilderManager::FAudioMCPBuilderManager()
	: bNodeTypeMapBuilt(false)
{
}

FAudioMCPBuilderManager::~FAudioMCPBuilderManager()
{
	ResetState();
}

void FAudioMCPBuilderManager::ResetState()
{
	ActiveBuilder.Reset();
	ActiveBuilderName.Empty();
	NodeHandles.Empty();
	GraphInputOutputHandles.Empty();
	GraphOutputInputHandles.Empty();
}

// ---------------------------------------------------------------------------
// Builder lifecycle
// ---------------------------------------------------------------------------

bool FAudioMCPBuilderManager::CreateBuilder(const FString& AssetType, const FString& Name, FString& OutError)
{
	ResetState();

	// Get the MetaSound builder subsystem from the editor world
	UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (!World)
	{
		OutError = TEXT("No editor world available");
		return false;
	}

	UMetaSoundBuilderSubsystem* BuilderSubsystem = World->GetSubsystem<UMetaSoundBuilderSubsystem>();
	if (!BuilderSubsystem)
	{
		OutError = TEXT("MetaSoundBuilderSubsystem not available. Is MetaSounds plugin enabled?");
		return false;
	}

	EMetaSoundBuilderResult Result;
	FMetaSoundBuilderOptions Options;
	Options.Name = FName(*Name);

	UMetaSoundBuilderBase* Builder = nullptr;

	if (AssetType.Equals(TEXT("Source"), ESearchCase::IgnoreCase))
	{
		Builder = BuilderSubsystem->CreateSourceBuilder(Options, Result);
	}
	else if (AssetType.Equals(TEXT("Patch"), ESearchCase::IgnoreCase))
	{
		Builder = BuilderSubsystem->CreatePatchBuilder(Options, Result);
	}
	else if (AssetType.Equals(TEXT("Preset"), ESearchCase::IgnoreCase))
	{
		Builder = BuilderSubsystem->CreatePresetBuilder(Options, Result);
	}
	else
	{
		OutError = FString::Printf(TEXT("Invalid asset_type '%s'. Must be Source, Patch, or Preset"), *AssetType);
		return false;
	}

	if (Result != EMetaSoundBuilderResult::Succeeded || !Builder)
	{
		OutError = FString::Printf(TEXT("Failed to create %s builder for '%s'"), *AssetType, *Name);
		return false;
	}

	ActiveBuilder.Reset(Builder);
	ActiveBuilderName = Name;

	// Build node type map on first use
	if (!bNodeTypeMapBuilt)
	{
		BuildNodeTypeMap();
	}

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Created %s builder: %s"), *AssetType, *Name);
	return true;
}

bool FAudioMCPBuilderManager::AddInterface(const FString& InterfaceName, FString& OutError)
{
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	EMetaSoundBuilderResult Result;
	ActiveBuilder.Get()->AddInterface(FName(*InterfaceName), Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Failed to add interface '%s'"), *InterfaceName);
		return false;
	}

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Added interface: %s"), *InterfaceName);
	return true;
}

bool FAudioMCPBuilderManager::AddGraphInput(const FString& Name, const FString& TypeName, const FString& DefaultValue, FString& OutError)
{
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	EMetaSoundBuilderResult Result;
	FMetaSoundBuilderNodeOutputHandle OutputHandle = ActiveBuilder.Get()->AddGraphInputNode(
		FName(*Name), FName(*TypeName), FMetasoundFrontendLiteral(), Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Failed to add graph input '%s' of type '%s'"), *Name, *TypeName);
		return false;
	}

	// Store the output handle (graph inputs have outputs that feed into the graph)
	GraphInputOutputHandles.Add(Name, OutputHandle);

	// Apply default value if provided
	if (!DefaultValue.IsEmpty())
	{
		FMetasoundFrontendLiteral Literal;

		// Try numeric first, then bool, then string
		if (DefaultValue.IsNumeric())
		{
			Literal.Set(FCString::Atof(*DefaultValue));
		}
		else if (DefaultValue.Equals(TEXT("true"), ESearchCase::IgnoreCase))
		{
			Literal.Set(true);
		}
		else if (DefaultValue.Equals(TEXT("false"), ESearchCase::IgnoreCase))
		{
			Literal.Set(false);
		}
		else
		{
			Literal.Set(DefaultValue);
		}

		// Find the input handle for this graph input node to set its default
		FMetaSoundBuilderNodeInputHandle DefaultInputHandle = ActiveBuilder.Get()->FindNodeInputByName(
			FMetaSoundNodeHandle(), FName(*Name), Result);
		if (Result == EMetaSoundBuilderResult::Succeeded)
		{
			ActiveBuilder.Get()->SetNodeInputDefault(DefaultInputHandle, Literal, Result);
		}
		// Non-fatal if default setting fails — the node was still created
		if (Result != EMetaSoundBuilderResult::Succeeded)
		{
			UE_LOG(LogAudioMCPBuilder, Warning, TEXT("Graph input '%s' created but default value '%s' could not be set"),
				*Name, *DefaultValue);
		}
	}

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Added graph input: %s (%s)"), *Name, *TypeName);
	return true;
}

bool FAudioMCPBuilderManager::AddGraphOutput(const FString& Name, const FString& TypeName, FString& OutError)
{
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	EMetaSoundBuilderResult Result;
	FMetaSoundBuilderNodeInputHandle InputHandle = ActiveBuilder.Get()->AddGraphOutputNode(
		FName(*Name), FName(*TypeName), FMetasoundFrontendLiteral(), Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Failed to add graph output '%s' of type '%s'"), *Name, *TypeName);
		return false;
	}

	// Store the input handle (graph outputs have inputs that receive from the graph)
	GraphOutputInputHandles.Add(Name, InputHandle);

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Added graph output: %s (%s)"), *Name, *TypeName);
	return true;
}

// ---------------------------------------------------------------------------
// Node operations
// ---------------------------------------------------------------------------

bool FAudioMCPBuilderManager::AddNode(const FString& NodeId, const FString& NodeType, int32 PosX, int32 PosY, FString& OutError)
{
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	if (NodeId == AudioMCP::GRAPH_BOUNDARY)
	{
		OutError = TEXT("Cannot use reserved ID '__graph__' for a node");
		return false;
	}

	if (NodeHandles.Contains(NodeId))
	{
		OutError = FString::Printf(TEXT("Duplicate node ID: '%s'"), *NodeId);
		return false;
	}

	// Resolve display name to MetaSound class name
	FString ClassName;
	if (!ResolveNodeType(NodeType, ClassName, OutError))
	{
		return false;
	}

	EMetaSoundBuilderResult Result;
	FMetaSoundNodeHandle NodeHandle = ActiveBuilder.Get()->AddNode(FName(*ClassName), Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Failed to add node '%s' of type '%s' (class: %s)"),
			*NodeId, *NodeType, *ClassName);
		return false;
	}

	// Set editor position for visibility
	ActiveBuilder.Get()->SetNodeLocation(NodeHandle, FVector2D(PosX, PosY), Result);

	// Store the actual node handle for pin lookups in SetNodeDefault/ConnectNodes
	NodeHandles.Add(NodeId, NodeHandle);

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Added node: %s (%s) at (%d, %d)"),
		*NodeId, *NodeType, PosX, PosY);
	return true;
}

bool FAudioMCPBuilderManager::SetNodeDefault(const FString& NodeId, const FString& InputName, const TSharedPtr<FJsonValue>& Value, FString& OutError)
{
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	FMetaSoundNodeHandle* NodeHandlePtr = NodeHandles.Find(NodeId);
	if (!NodeHandlePtr)
	{
		OutError = FString::Printf(TEXT("Unknown node ID: '%s'"), *NodeId);
		return false;
	}

	// Find the node's input by name using the actual node handle
	EMetaSoundBuilderResult Result;
	FMetaSoundBuilderNodeInputHandle InputHandle = ActiveBuilder.Get()->FindNodeInputByName(
		*NodeHandlePtr, FName(*InputName), Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Input '%s' not found on node '%s'"), *InputName, *NodeId);
		return false;
	}

	// Convert JSON value to MetaSound literal
	FMetasoundFrontendLiteral Literal;

	if (Value->Type == EJson::Number)
	{
		Literal.Set(static_cast<float>(Value->AsNumber()));
	}
	else if (Value->Type == EJson::Boolean)
	{
		Literal.Set(Value->AsBool());
	}
	else if (Value->Type == EJson::String)
	{
		Literal.Set(Value->AsString());
	}
	else
	{
		OutError = FString::Printf(TEXT("Unsupported value type for input '%s' on node '%s'"),
			*InputName, *NodeId);
		return false;
	}

	ActiveBuilder.Get()->SetNodeInputDefault(InputHandle, Literal, Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Failed to set default for '%s.%s'"), *NodeId, *InputName);
		return false;
	}

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Set default: %s.%s"), *NodeId, *InputName);
	return true;
}

bool FAudioMCPBuilderManager::ConnectNodes(const FString& FromNode, const FString& FromPin,
                                            const FString& ToNode, const FString& ToPin, FString& OutError)
{
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	EMetaSoundBuilderResult Result;

	// Resolve source: either graph input or regular node
	FMetaSoundBuilderNodeOutputHandle OutputHandle;
	if (FromNode == AudioMCP::GRAPH_BOUNDARY)
	{
		FMetaSoundBuilderNodeOutputHandle* HandlePtr = GraphInputOutputHandles.Find(FromPin);
		if (!HandlePtr)
		{
			OutError = FString::Printf(TEXT("Graph input '%s' not found"), *FromPin);
			return false;
		}
		OutputHandle = *HandlePtr;
	}
	else
	{
		FMetaSoundNodeHandle* NodeHandlePtr = NodeHandles.Find(FromNode);
		if (!NodeHandlePtr)
		{
			OutError = FString::Printf(TEXT("Source node '%s' not found"), *FromNode);
			return false;
		}
		// Find the specific output pin by name using the actual node handle
		OutputHandle = ActiveBuilder.Get()->FindNodeOutputByName(
			*NodeHandlePtr, FName(*FromPin), Result);
		if (Result != EMetaSoundBuilderResult::Succeeded)
		{
			OutError = FString::Printf(TEXT("Output pin '%s' not found on node '%s'"), *FromPin, *FromNode);
			return false;
		}
	}

	// Resolve destination: either graph output or regular node
	FMetaSoundBuilderNodeInputHandle InputHandle;
	if (ToNode == AudioMCP::GRAPH_BOUNDARY)
	{
		FMetaSoundBuilderNodeInputHandle* HandlePtr = GraphOutputInputHandles.Find(ToPin);
		if (!HandlePtr)
		{
			OutError = FString::Printf(TEXT("Graph output '%s' not found"), *ToPin);
			return false;
		}
		InputHandle = *HandlePtr;
	}
	else
	{
		FMetaSoundNodeHandle* NodeHandlePtr = NodeHandles.Find(ToNode);
		if (!NodeHandlePtr)
		{
			OutError = FString::Printf(TEXT("Destination node '%s' not found"), *ToNode);
			return false;
		}
		// Find the specific input pin by name using the actual node handle
		InputHandle = ActiveBuilder.Get()->FindNodeInputByName(
			*NodeHandlePtr, FName(*ToPin), Result);
		if (Result != EMetaSoundBuilderResult::Succeeded)
		{
			OutError = FString::Printf(TEXT("Input pin '%s' not found on node '%s'"), *ToPin, *ToNode);
			return false;
		}
	}

	// Make the connection
	ActiveBuilder.Get()->ConnectNodes(OutputHandle, InputHandle, Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Failed to connect %s.%s -> %s.%s"),
			*FromNode, *FromPin, *ToNode, *ToPin);
		return false;
	}

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Connected: %s.%s -> %s.%s"),
		*FromNode, *FromPin, *ToNode, *ToPin);
	return true;
}

// ---------------------------------------------------------------------------
// Build & Audition
// ---------------------------------------------------------------------------

bool FAudioMCPBuilderManager::BuildToAsset(const FString& Name, const FString& Path, FString& OutError)
{
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	if (!Path.StartsWith(TEXT("/Game/")))
	{
		OutError = FString::Printf(TEXT("Path must start with /Game/ (got '%s')"), *Path);
		return false;
	}

	FString FullPath = Path;
	if (!FullPath.EndsWith(TEXT("/")))
	{
		FullPath += TEXT("/");
	}
	FullPath += Name;

	EMetaSoundBuilderResult Result;
	ActiveBuilder.Get()->BuildToAsset(FName(*FullPath), Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Failed to build asset '%s' at '%s'"), *Name, *FullPath);
		return false;
	}

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Built asset: %s"), *FullPath);
	return true;
}

bool FAudioMCPBuilderManager::Audition(FString& OutError)
{
#if WITH_EDITOR
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (!World)
	{
		OutError = TEXT("No editor world available for audition");
		return false;
	}

	EMetaSoundBuilderResult Result;
	ActiveBuilder.Get()->Audition(World, Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = TEXT("Failed to audition. Try build_to_asset first, then play via Blueprint.");
		return false;
	}

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Auditioning: %s"), *ActiveBuilderName);
	return true;
#else
	OutError = TEXT("Audition is only available in editor builds");
	return false;
#endif
}

// ---------------------------------------------------------------------------
// Node type resolution
// ---------------------------------------------------------------------------

void FAudioMCPBuilderManager::BuildNodeTypeMap()
{
	AudioMCPNodeRegistry::InitNodeTypeMap(NodeTypeMap);
	bNodeTypeMapBuilt = true;
	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Built node type map: %d entries"), NodeTypeMap.Num());
}

bool FAudioMCPBuilderManager::ResolveNodeType(const FString& DisplayName, FString& OutClassName, FString& OutError)
{
	// First try direct lookup in our map
	FString* Found = NodeTypeMap.Find(DisplayName);
	if (Found)
	{
		OutClassName = *Found;
		return true;
	}

	// If the display name already looks like a class name (contains ::), use it directly
	if (DisplayName.Contains(TEXT("::")))
	{
		OutClassName = DisplayName;
		return true;
	}

	OutError = FString::Printf(
		TEXT("Unknown node type '%s'. Use a known display name (e.g. 'Sine', 'Biquad Filter') "
		     "or a full class name (e.g. 'UE::MathOps::Sine'). "
		     "Use ms_search_nodes on the Python side to find valid types."),
		*DisplayName);
	return false;
}
