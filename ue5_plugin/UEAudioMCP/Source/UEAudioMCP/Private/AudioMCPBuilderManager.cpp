// Copyright UE Audio MCP Project. All Rights Reserved.

#include "AudioMCPBuilderManager.h"
#include "AudioMCPNodeRegistry.h"
#include "AudioMCPTypes.h"
#include "MetasoundBuilderSubsystem.h"
#include "MetasoundSource.h"
#include "MetasoundDocumentInterface.h"
#include "MetasoundFrontendDocument.h"
#include "Interfaces/MetasoundOutputFormatInterfaces.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Components/AudioComponent.h"
#include "Engine/Engine.h"
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
	StopAudition();
	ActiveBuilder.Reset();
	ActiveBuilderName.Empty();
	NodeHandles.Empty();
	GraphInputOutputHandles.Empty();
	GraphOutputInputHandles.Empty();
	bLiveUpdatesRequested = false;
}

void FAudioMCPBuilderManager::StopAudition()
{
	if (AuditionAudioComponent.IsValid())
	{
		UAudioComponent* Comp = AuditionAudioComponent.Get();
		if (Comp && Comp->IsPlaying())
		{
			Comp->Stop();
			UE_LOG(LogAudioMCPBuilder, Log, TEXT("Stopped previous audition"));
		}
		AuditionAudioComponent.Reset();
	}
}

// ---------------------------------------------------------------------------
// Builder lifecycle
// ---------------------------------------------------------------------------

bool FAudioMCPBuilderManager::CreateBuilder(const FString& AssetType, const FString& Name, FString& OutError)
{
	ResetState();

	// Get the MetaSound builder subsystem (Engine Subsystem in UE 5.7+)
	UMetaSoundBuilderSubsystem* BuilderSubsystem = UMetaSoundBuilderSubsystem::Get();
	if (!BuilderSubsystem)
	{
		OutError = TEXT("MetaSoundBuilderSubsystem not available. Is MetaSounds plugin enabled?");
		return false;
	}

	EMetaSoundBuilderResult Result;
	UMetaSoundBuilderBase* Builder = nullptr;

	if (AssetType.Equals(TEXT("Source"), ESearchCase::IgnoreCase))
	{
		// UE 5.7: CreateSourceBuilder returns output handles for OnPlay/OnFinished/AudioOut
		FMetaSoundBuilderNodeOutputHandle OnPlayOutput;
		FMetaSoundBuilderNodeInputHandle OnFinishedInput;
		TArray<FMetaSoundBuilderNodeInputHandle> AudioOutInputs;

		Builder = BuilderSubsystem->CreateSourceBuilder(
			FName(*Name),
			OnPlayOutput,
			OnFinishedInput,
			AudioOutInputs,
			Result,
			EMetaSoundOutputAudioFormat::Mono,
			false /* bIsOneShot = false for continuous playback */);

		// Store the built-in Source graph handles so __graph__ connections work
		if (Result == EMetaSoundBuilderResult::Succeeded && Builder)
		{
			// Store OnPlay as a graph input (it's an output handle that feeds into the graph)
			GraphInputOutputHandles.Add(TEXT("OnPlay"), OnPlayOutput);

			// Store OnFinished as a graph output (it's an input handle that receives from the graph)
			GraphOutputInputHandles.Add(TEXT("OnFinished"), OnFinishedInput);

			// Store audio output channels: "Audio:0", "Audio:1", etc.
			for (int32 i = 0; i < AudioOutInputs.Num(); ++i)
			{
				FString PinName = FString::Printf(TEXT("Audio:%d"), i);
				GraphOutputInputHandles.Add(PinName, AudioOutInputs[i]);
			}

			UE_LOG(LogAudioMCPBuilder, Log, TEXT("Source builder '%s': %d audio outputs stored"),
				*Name, AudioOutInputs.Num());
		}
	}
	else if (AssetType.Equals(TEXT("Patch"), ESearchCase::IgnoreCase))
	{
		// UE 5.7: CreatePatchBuilder takes just name + result
		Builder = BuilderSubsystem->CreatePatchBuilder(FName(*Name), Result);
	}
	else if (AssetType.Equals(TEXT("Preset"), ESearchCase::IgnoreCase))
	{
		// UE 5.7: Preset requires a referenced MetaSound — cannot create standalone.
		// Use CreateBuilder("Source"/"Patch") first, then ConvertToPreset.
		OutError = TEXT("Cannot create a standalone Preset builder in UE 5.7. "
			"Create a Source or Patch builder first, then use convert_to_preset.");
		return false;
	}
	else
	{
		OutError = FString::Printf(TEXT("Invalid asset_type '%s'. Must be Source or Patch"), *AssetType);
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

	// UE 5.7: Parse "Namespace::Name::Variant" into FMetasoundFrontendClassName
	FMetasoundFrontendClassName ParsedClassName;
	TArray<FString> Parts;
	ClassName.ParseIntoArray(Parts, TEXT("::"), true);

	if (Parts.Num() == 1)
	{
		ParsedClassName = FMetasoundFrontendClassName(FName(), FName(*Parts[0]));
	}
	else if (Parts.Num() == 2)
	{
		ParsedClassName = FMetasoundFrontendClassName(FName(*Parts[0]), FName(*Parts[1]));
	}
	else if (Parts.Num() >= 3)
	{
		ParsedClassName = FMetasoundFrontendClassName(FName(*Parts[0]), FName(*Parts[1]), FName(*Parts[2]));
	}

	EMetaSoundBuilderResult Result;
	FMetaSoundNodeHandle NodeHandle = ActiveBuilder.Get()->AddNodeByClassName(ParsedClassName, Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Failed to add node '%s' of type '%s' (class: %s, parsed: {Namespace='%s', Name='%s', Variant='%s'})"),
			*NodeId, *NodeType, *ClassName,
			*ParsedClassName.Namespace.ToString(),
			*ParsedClassName.Name.ToString(),
			*ParsedClassName.Variant.ToString());
		return false;
	}

	// Set editor position for visibility (editor-only in UE 5.7)
#if WITH_EDITOR
	ActiveBuilder.Get()->SetNodeLocation(NodeHandle, FVector2D(PosX, PosY), Result);
#endif

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
// Graph variables (UE 5.7)
// ---------------------------------------------------------------------------

bool FAudioMCPBuilderManager::AddGraphVariable(const FString& Name, const FString& TypeName, const FString& DefaultValue, FString& OutError)
{
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	EMetaSoundBuilderResult Result;
	FMetasoundFrontendLiteral DefaultLiteral;

	// Parse default value if provided
	if (!DefaultValue.IsEmpty())
	{
		if (DefaultValue.IsNumeric())
		{
			DefaultLiteral.Set(FCString::Atof(*DefaultValue));
		}
		else if (DefaultValue.Equals(TEXT("true"), ESearchCase::IgnoreCase))
		{
			DefaultLiteral.Set(true);
		}
		else if (DefaultValue.Equals(TEXT("false"), ESearchCase::IgnoreCase))
		{
			DefaultLiteral.Set(false);
		}
		else
		{
			DefaultLiteral.Set(DefaultValue);
		}
	}

	ActiveBuilder.Get()->AddGraphVariable(FName(*Name), FName(*TypeName), DefaultLiteral, Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Failed to add graph variable '%s' of type '%s'"), *Name, *TypeName);
		return false;
	}

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Added graph variable: %s (%s)"), *Name, *TypeName);
	return true;
}

bool FAudioMCPBuilderManager::AddVariableGetNode(const FString& NodeId, const FString& VariableName, bool bDelayed, FString& OutError)
{
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	if (NodeHandles.Contains(NodeId))
	{
		OutError = FString::Printf(TEXT("Duplicate node ID: '%s'"), *NodeId);
		return false;
	}

	EMetaSoundBuilderResult Result;
	FMetaSoundNodeHandle NodeHandle;

	if (bDelayed)
	{
		NodeHandle = ActiveBuilder.Get()->AddGraphVariableGetDelayedNode(FName(*VariableName), Result);
	}
	else
	{
		NodeHandle = ActiveBuilder.Get()->AddGraphVariableGetNode(FName(*VariableName), Result);
	}

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Failed to add %svariable get node for '%s'"),
			bDelayed ? TEXT("delayed ") : TEXT(""), *VariableName);
		return false;
	}

	NodeHandles.Add(NodeId, NodeHandle);

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Added %svariable get node: %s -> %s"),
		bDelayed ? TEXT("delayed ") : TEXT(""), *NodeId, *VariableName);
	return true;
}

bool FAudioMCPBuilderManager::AddVariableSetNode(const FString& NodeId, const FString& VariableName, FString& OutError)
{
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	if (NodeHandles.Contains(NodeId))
	{
		OutError = FString::Printf(TEXT("Duplicate node ID: '%s'"), *NodeId);
		return false;
	}

	EMetaSoundBuilderResult Result;
	FMetaSoundNodeHandle NodeHandle = ActiveBuilder.Get()->AddGraphVariableSetNode(FName(*VariableName), Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Failed to add variable set node for '%s'"), *VariableName);
		return false;
	}

	NodeHandles.Add(NodeId, NodeHandle);

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Added variable set node: %s -> %s"), *NodeId, *VariableName);
	return true;
}

// ---------------------------------------------------------------------------
// Preset conversion
// ---------------------------------------------------------------------------

bool FAudioMCPBuilderManager::ConvertToPreset(const FString& ReferencedAsset, FString& OutError)
{
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	// Load the referenced MetaSound asset
	UObject* Asset = StaticLoadObject(UObject::StaticClass(), nullptr, *ReferencedAsset);
	if (!Asset)
	{
		OutError = FString::Printf(TEXT("Could not load referenced asset '%s'"), *ReferencedAsset);
		return false;
	}

	// UE 5.7: ConvertToPreset takes TScriptInterface<IMetaSoundDocumentInterface>
	TScriptInterface<IMetaSoundDocumentInterface> DocInterface(Asset);
	if (!DocInterface.GetInterface())
	{
		OutError = FString::Printf(TEXT("Asset '%s' does not implement IMetaSoundDocumentInterface"), *ReferencedAsset);
		return false;
	}

	EMetaSoundBuilderResult Result;
	ActiveBuilder.Get()->ConvertToPreset(DocInterface, Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Failed to convert to preset of '%s'"), *ReferencedAsset);
		return false;
	}

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Converted to preset of: %s"), *ReferencedAsset);
	return true;
}

bool FAudioMCPBuilderManager::ConvertFromPreset(FString& OutError)
{
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	EMetaSoundBuilderResult Result;
	ActiveBuilder.Get()->ConvertFromPreset(Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = TEXT("Failed to convert from preset to full graph");
		return false;
	}

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Converted from preset to full graph"));
	return true;
}

// ---------------------------------------------------------------------------
// Query / Introspection
// ---------------------------------------------------------------------------

bool FAudioMCPBuilderManager::GetGraphInputNames(TArray<FString>& OutNames, FString& OutError)
{
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	OutNames.Empty();
	for (const auto& Pair : GraphInputOutputHandles)
	{
		OutNames.Add(Pair.Key);
	}

	return true;
}

bool FAudioMCPBuilderManager::SetLiveUpdates(bool bEnabled, FString& OutError)
{
	if (!ActiveBuilder.IsValid())
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	// UE 5.7: SetLiveUpdatesEnabled removed from BuilderBase.
	// Live updates are now controlled via the bLiveUpdatesEnabled param in Audition().
	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Live updates flag set to %s (applied at audition time)"),
		bEnabled ? TEXT("enabled") : TEXT("disabled"));
	bLiveUpdatesRequested = bEnabled;
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

	// UE 5.7: Use BuildNewMetaSound to create a registered transient MetaSound.
	// This is the safest path — avoids the crash-prone Build(FMetaSoundBuilderOptions).
	TScriptInterface<IMetaSoundDocumentInterface> BuiltMetaSound = ActiveBuilder.Get()->BuildNewMetaSound(FName(*Name));
	if (!BuiltMetaSound.GetObject())
	{
		OutError = FString::Printf(TEXT("Failed to build MetaSound '%s'"), *Name);
		return false;
	}

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Built and registered MetaSound: %s"), *Name);
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

	// UE 5.7: Audition is only on UMetaSoundSourceBuilder, not the base class
	UMetaSoundSourceBuilder* SourceBuilder = Cast<UMetaSoundSourceBuilder>(ActiveBuilder.Get());
	if (!SourceBuilder)
	{
		OutError = TEXT("Audition is only available for Source builders (not Patch/Preset)");
		return false;
	}

	UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (!World)
	{
		OutError = TEXT("No editor world available for audition");
		return false;
	}

	// Stop any previous audition before starting a new one
	StopAudition();

	// Create a transient AudioComponent for playback (non-spatial / 2D)
	UAudioComponent* AudioComp = NewObject<UAudioComponent>(World->GetWorldSettings());
	if (!AudioComp)
	{
		OutError = TEXT("Failed to create AudioComponent for audition");
		return false;
	}
	AudioComp->bIsUISound = true;            // Non-spatial, plays on UI bus
	AudioComp->bAllowSpatialization = false;  // No 3D positioning needed
	AudioComp->bAutoDestroy = false;          // We manage lifetime via TStrongObjectPtr
	AudioComp->SetVolumeMultiplier(1.0f);
	AudioComp->RegisterComponent();

	// Store in member to prevent garbage collection during playback
	AuditionAudioComponent.Reset(AudioComp);

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Audition: AudioComponent created — bIsUISound=%d, bAllowSpatialization=%d, Volume=%.2f, Registered=%d"),
		AudioComp->bIsUISound, AudioComp->bAllowSpatialization, AudioComp->VolumeMultiplier, AudioComp->IsRegistered());

	// UE 5.7 signature: Audition(Parent, AudioComponent, OnCreateDelegate, bLiveUpdates)
	FOnCreateAuditionGeneratorHandleDelegate GeneratorDelegate;
	SourceBuilder->Audition(World, AudioComp, GeneratorDelegate, bLiveUpdatesRequested);

	// Check state immediately after Audition call
	bool bPlaying = AudioComp->IsPlaying();
	bool bActive = AudioComp->IsActive();
	USoundBase* Sound = AudioComp->Sound;

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Audition: called SourceBuilder->Audition() for '%s'. IsPlaying=%d, IsActive=%d, Sound=%s"),
		*ActiveBuilderName, bPlaying, bActive, Sound ? *Sound->GetName() : TEXT("null"));

	if (!bPlaying && !bActive)
	{
		UE_LOG(LogAudioMCPBuilder, Warning, TEXT("Audition: AudioComponent not playing after Audition() call. "
			"This may indicate the graph has no audio output connected to __graph__ Audio:0, "
			"or the MetaSound source failed to build internally."));
	}

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
		     "or a full class name (e.g. 'UE::Sine::Audio'). "
		     "Use list_node_classes command to discover available nodes."),
		*DisplayName);
	return false;
}
