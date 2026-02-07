// Copyright UE Audio MCP Project. All Rights Reserved.

#include "AudioMCPBuilderManager.h"
#include "AudioMCPTypes.h"
#include "MetasoundBuilderSubsystem.h"
#include "MetasoundSource.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/World.h"
#include "Editor.h"

DEFINE_LOG_CATEGORY_STATIC(LogAudioMCPBuilder, Log, All);

FAudioMCPBuilderManager::FAudioMCPBuilderManager()
	: ActiveBuilder(nullptr)
	, bNodeTypeMapBuilt(false)
{
}

FAudioMCPBuilderManager::~FAudioMCPBuilderManager()
{
	ResetState();
}

void FAudioMCPBuilderManager::ResetState()
{
	ActiveBuilder = nullptr;
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

	if (AssetType == TEXT("Source") || AssetType == TEXT("source"))
	{
		ActiveBuilder = BuilderSubsystem->CreateSourceBuilder(Options, Result);
	}
	else if (AssetType == TEXT("Patch") || AssetType == TEXT("patch"))
	{
		ActiveBuilder = BuilderSubsystem->CreatePatchBuilder(Options, Result);
	}
	else if (AssetType == TEXT("Preset") || AssetType == TEXT("preset"))
	{
		ActiveBuilder = BuilderSubsystem->CreatePresetBuilder(Options, Result);
	}
	else
	{
		OutError = FString::Printf(TEXT("Invalid asset_type '%s'. Must be Source, Patch, or Preset"), *AssetType);
		return false;
	}

	if (Result != EMetaSoundBuilderResult::Succeeded || !ActiveBuilder)
	{
		OutError = FString::Printf(TEXT("Failed to create %s builder for '%s'"), *AssetType, *Name);
		ActiveBuilder = nullptr;
		return false;
	}

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
	if (!ActiveBuilder)
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	EMetaSoundBuilderResult Result;
	ActiveBuilder->AddInterface(FName(*InterfaceName), Result);

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
	if (!ActiveBuilder)
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	EMetaSoundBuilderResult Result;
	FMetaSoundBuilderNodeOutputHandle OutputHandle = ActiveBuilder->AddGraphInputNode(
		FName(*Name), FName(*TypeName), FMetasoundFrontendLiteral(), Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Failed to add graph input '%s' of type '%s'"), *Name, *TypeName);
		return false;
	}

	// Store the output handle (graph inputs have outputs that feed into the graph)
	GraphInputOutputHandles.Add(Name, OutputHandle);

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Added graph input: %s (%s)"), *Name, *TypeName);
	return true;
}

bool FAudioMCPBuilderManager::AddGraphOutput(const FString& Name, const FString& TypeName, FString& OutError)
{
	if (!ActiveBuilder)
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	EMetaSoundBuilderResult Result;
	FMetaSoundBuilderNodeInputHandle InputHandle = ActiveBuilder->AddGraphOutputNode(
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
	if (!ActiveBuilder)
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
	FMetaSoundNodeHandle NodeHandle = ActiveBuilder->AddNode(FName(*ClassName), Result);

	if (Result != EMetaSoundBuilderResult::Succeeded)
	{
		OutError = FString::Printf(TEXT("Failed to add node '%s' of type '%s' (class: %s)"),
			*NodeId, *NodeType, *ClassName);
		return false;
	}

	// Set editor position for visibility
	ActiveBuilder->SetNodeLocation(NodeHandle, FVector2D(PosX, PosY), Result);

	// Store the actual node handle for pin lookups in SetNodeDefault/ConnectNodes
	NodeHandles.Add(NodeId, NodeHandle);

	UE_LOG(LogAudioMCPBuilder, Log, TEXT("Added node: %s (%s) at (%d, %d)"),
		*NodeId, *NodeType, PosX, PosY);
	return true;
}

bool FAudioMCPBuilderManager::SetNodeDefault(const FString& NodeId, const FString& InputName, const TSharedPtr<FJsonValue>& Value, FString& OutError)
{
	if (!ActiveBuilder)
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
	FMetaSoundBuilderNodeInputHandle InputHandle = ActiveBuilder->FindNodeInputByName(
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

	ActiveBuilder->SetNodeInputDefault(InputHandle, Literal, Result);

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
	if (!ActiveBuilder)
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	EMetaSoundBuilderResult Result;

	// Resolve source: either graph input or regular node
	FMetaSoundBuilderNodeOutputHandle OutputHandle;
	if (FromNode == AudioMCP::GRAPH_BOUNDARY)
	{
		int32* IdxPtr = GraphInputOutputIndices.Find(FromPin);
		if (!IdxPtr)
		{
			OutError = FString::Printf(TEXT("Graph input '%s' not found"), *FromPin);
			return false;
		}
		OutputHandle = NodeOutputHandles[*IdxPtr];
	}
	else
	{
		int32* IdxPtr = NodeHandleIndices.Find(FromNode);
		if (!IdxPtr)
		{
			OutError = FString::Printf(TEXT("Source node '%s' not found"), *FromNode);
			return false;
		}
		// Find the specific output pin by name
		OutputHandle = ActiveBuilder->FindNodeOutputByName(
			FMetaSoundNodeHandle(), FName(*FromPin), Result);
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
		int32* IdxPtr = GraphOutputInputIndices.Find(ToPin);
		if (!IdxPtr)
		{
			OutError = FString::Printf(TEXT("Graph output '%s' not found"), *ToPin);
			return false;
		}
		InputHandle = NodeInputHandles[*IdxPtr];
	}
	else
	{
		int32* IdxPtr = NodeHandleIndices.Find(ToNode);
		if (!IdxPtr)
		{
			OutError = FString::Printf(TEXT("Destination node '%s' not found"), *ToNode);
			return false;
		}
		InputHandle = ActiveBuilder->FindNodeInputByName(
			FMetaSoundNodeHandle(), FName(*ToPin), Result);
		if (Result != EMetaSoundBuilderResult::Succeeded)
		{
			OutError = FString::Printf(TEXT("Input pin '%s' not found on node '%s'"), *ToPin, *ToNode);
			return false;
		}
	}

	// Make the connection
	ActiveBuilder->ConnectNodes(OutputHandle, InputHandle, Result);

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
	if (!ActiveBuilder)
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
	ActiveBuilder->BuildToAsset(FName(*FullPath), Result);

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
	if (!ActiveBuilder)
	{
		OutError = TEXT("No active builder. Call create_builder first.");
		return false;
	}

	EMetaSoundBuilderResult Result;
	ActiveBuilder->Audition(nullptr, Result);

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
	// Hardcoded map of common display names to MetaSound class names.
	// This covers the ~100 most common nodes used in game audio.
	// A dynamic registry scan can supplement this at runtime.
	NodeTypeMap.Add(TEXT("Sine"), TEXT("UE::MathOps::Sine"));
	NodeTypeMap.Add(TEXT("Noise"), TEXT("UE::Generators::Noise"));
	NodeTypeMap.Add(TEXT("White Noise"), TEXT("UE::Generators::WhiteNoise"));
	NodeTypeMap.Add(TEXT("Wave Player (Mono)"), TEXT("UE::WavePlayer::Mono"));
	NodeTypeMap.Add(TEXT("Wave Player (Stereo)"), TEXT("UE::WavePlayer::Stereo"));
	NodeTypeMap.Add(TEXT("AD Envelope"), TEXT("UE::Generators::ADEnvelope"));
	NodeTypeMap.Add(TEXT("ADSR Envelope"), TEXT("UE::Generators::ADSREnvelope"));
	NodeTypeMap.Add(TEXT("Biquad Filter"), TEXT("UE::Filters::BiquadFilter"));
	NodeTypeMap.Add(TEXT("State Variable Filter"), TEXT("UE::State Variable Filter::Audio"));
	NodeTypeMap.Add(TEXT("Lowpass Filter"), TEXT("UE::Filters::LowpassFilter"));
	NodeTypeMap.Add(TEXT("Highpass Filter"), TEXT("UE::Filters::HighpassFilter"));
	NodeTypeMap.Add(TEXT("Bandpass Filter"), TEXT("UE::Filters::BandpassFilter"));
	NodeTypeMap.Add(TEXT("Ladder Filter"), TEXT("UE::Filters::LadderFilter"));
	NodeTypeMap.Add(TEXT("One-Pole Lowpass"), TEXT("UE::Filters::OnePoleLowpass"));
	NodeTypeMap.Add(TEXT("One-Pole Highpass"), TEXT("UE::Filters::OnePoleHighpass"));
	NodeTypeMap.Add(TEXT("Gain"), TEXT("UE::MathOps::Gain"));
	NodeTypeMap.Add(TEXT("Multiply"), TEXT("UE::MathOps::Multiply"));
	NodeTypeMap.Add(TEXT("Multiply (Audio)"), TEXT("UE::MathOps::Multiply::Audio"));
	NodeTypeMap.Add(TEXT("Add"), TEXT("UE::MathOps::Add"));
	NodeTypeMap.Add(TEXT("Add (Audio)"), TEXT("UE::MathOps::Add::Audio"));
	NodeTypeMap.Add(TEXT("Subtract"), TEXT("UE::MathOps::Subtract"));
	NodeTypeMap.Add(TEXT("Divide"), TEXT("UE::MathOps::Divide"));
	NodeTypeMap.Add(TEXT("Clamp"), TEXT("UE::MathOps::Clamp"));
	NodeTypeMap.Add(TEXT("Map Range"), TEXT("UE::MathOps::MapRange"));
	NodeTypeMap.Add(TEXT("Random (Float)"), TEXT("UE::Random::Float"));
	NodeTypeMap.Add(TEXT("Random Get (Float)"), TEXT("UE::Random::GetFloat"));
	NodeTypeMap.Add(TEXT("Stereo Mixer"), TEXT("UE::Mixing::StereoMixer"));
	NodeTypeMap.Add(TEXT("Mono Mixer"), TEXT("UE::Mixing::MonoMixer"));
	NodeTypeMap.Add(TEXT("Mix"), TEXT("UE::Mixing::Mix"));
	NodeTypeMap.Add(TEXT("LFO"), TEXT("UE::Generators::LFO"));
	NodeTypeMap.Add(TEXT("Oscillator"), TEXT("UE::Generators::Oscillator"));
	NodeTypeMap.Add(TEXT("Saw"), TEXT("UE::Generators::Saw"));
	NodeTypeMap.Add(TEXT("Square"), TEXT("UE::Generators::Square"));
	NodeTypeMap.Add(TEXT("Triangle"), TEXT("UE::Generators::Triangle"));
	NodeTypeMap.Add(TEXT("Pulse"), TEXT("UE::Generators::Pulse"));
	NodeTypeMap.Add(TEXT("Delay"), TEXT("UE::Effects::Delay"));
	NodeTypeMap.Add(TEXT("Stereo Delay"), TEXT("UE::Effects::StereoDelay"));
	NodeTypeMap.Add(TEXT("Reverb"), TEXT("UE::Effects::Reverb"));
	NodeTypeMap.Add(TEXT("Chorus"), TEXT("UE::Effects::Chorus"));
	NodeTypeMap.Add(TEXT("Phaser"), TEXT("UE::Effects::Phaser"));
	NodeTypeMap.Add(TEXT("Flanger"), TEXT("UE::Effects::Flanger"));
	NodeTypeMap.Add(TEXT("Compressor"), TEXT("UE::Dynamics::Compressor"));
	NodeTypeMap.Add(TEXT("Limiter"), TEXT("UE::Dynamics::Limiter"));
	NodeTypeMap.Add(TEXT("Gate"), TEXT("UE::Dynamics::Gate"));
	NodeTypeMap.Add(TEXT("Trigger Repeat"), TEXT("UE::Triggers::TriggerRepeat"));
	NodeTypeMap.Add(TEXT("Trigger Counter"), TEXT("UE::Triggers::TriggerCounter"));
	NodeTypeMap.Add(TEXT("Trigger Control"), TEXT("UE::Triggers::TriggerControl"));
	NodeTypeMap.Add(TEXT("Trigger On Threshold"), TEXT("UE::Triggers::TriggerOnThreshold"));
	NodeTypeMap.Add(TEXT("BPM To Seconds"), TEXT("UE::Timing::BPMToSeconds"));
	NodeTypeMap.Add(TEXT("Freq To MIDI"), TEXT("UE::Conversions::FreqToMIDI"));
	NodeTypeMap.Add(TEXT("MIDI To Freq"), TEXT("UE::Conversions::MIDIToFreq"));
	NodeTypeMap.Add(TEXT("Semitones To Freq Multiplier"), TEXT("UE::Conversions::SemitonesToFreqMultiplier"));
	NodeTypeMap.Add(TEXT("dB To Linear"), TEXT("UE::Conversions::dBToLinear"));
	NodeTypeMap.Add(TEXT("Linear To dB"), TEXT("UE::Conversions::LineardB"));
	NodeTypeMap.Add(TEXT("Mono To Stereo"), TEXT("UE::Routing::MonoToStereo"));
	NodeTypeMap.Add(TEXT("Stereo To Mono"), TEXT("UE::Routing::StereoToMono"));
	NodeTypeMap.Add(TEXT("ITD Panner"), TEXT("UE::Spatialization::ITDPanner"));
	NodeTypeMap.Add(TEXT("Stereo Panner"), TEXT("UE::Spatialization::StereoPanner"));
	NodeTypeMap.Add(TEXT("Send"), TEXT("UE::Routing::Send"));
	NodeTypeMap.Add(TEXT("Receive"), TEXT("UE::Routing::Receive"));
	NodeTypeMap.Add(TEXT("Float To Audio"), TEXT("UE::Conversions::FloatToAudio"));
	NodeTypeMap.Add(TEXT("Audio To Float"), TEXT("UE::Conversions::AudioToFloat"));
	NodeTypeMap.Add(TEXT("Get"), TEXT("UE::Variables::Get"));
	NodeTypeMap.Add(TEXT("Set"), TEXT("UE::Variables::Set"));
	NodeTypeMap.Add(TEXT("Interpolate"), TEXT("UE::MathOps::Interpolate"));
	NodeTypeMap.Add(TEXT("Trigger Delay"), TEXT("UE::Triggers::TriggerDelay"));
	NodeTypeMap.Add(TEXT("Trigger Route"), TEXT("UE::Triggers::TriggerRoute"));
	NodeTypeMap.Add(TEXT("WaveTable"), TEXT("UE::Generators::WaveTable"));
	NodeTypeMap.Add(TEXT("Granulator"), TEXT("UE::Generators::Granulator"));
	NodeTypeMap.Add(TEXT("Sample And Hold"), TEXT("UE::MathOps::SampleAndHold"));

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
