// Copyright UE Audio MCP Project. All Rights Reserved.

#include "AudioMCPBlueprintManager.h"

#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_CallFunction.h"
#include "K2Node_CustomEvent.h"
#include "K2Node_VariableGet.h"
#include "K2Node_VariableSet.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

#define LOCTEXT_NAMESPACE "AudioMCPBlueprintManager"

DEFINE_LOG_CATEGORY_STATIC(LogAudioMCPBP, Log, All);

// Static singleton
FAudioMCPBlueprintManager* FAudioMCPBlueprintManager::Instance = nullptr;

FAudioMCPBlueprintManager::FAudioMCPBlueprintManager()
{
}

FAudioMCPBlueprintManager::~FAudioMCPBlueprintManager()
{
	if (Instance == this)
	{
		Instance = nullptr;
	}
}

// ==========================================================================
// Blueprint lifecycle
// ==========================================================================

bool FAudioMCPBlueprintManager::OpenBlueprint(const FString& AssetPath, FString& OutError)
{
	// Validate path
	if (AssetPath.IsEmpty())
	{
		OutError = TEXT("asset_path is empty");
		return false;
	}
	if (AssetPath.Contains(TEXT("..")))
	{
		OutError = TEXT("asset_path must not contain '..'");
		return false;
	}

	// Load the Blueprint asset
	UObject* Loaded = StaticLoadObject(UBlueprint::StaticClass(), nullptr, *AssetPath);
	if (!Loaded)
	{
		OutError = FString::Printf(TEXT("Could not load Blueprint at '%s'"), *AssetPath);
		return false;
	}

	UBlueprint* BP = Cast<UBlueprint>(Loaded);
	if (!BP)
	{
		OutError = FString::Printf(TEXT("'%s' is not a Blueprint"), *AssetPath);
		return false;
	}

	ResetHandles();
	ActiveBlueprint = BP;

	UE_LOG(LogAudioMCPBP, Log, TEXT("Opened Blueprint: %s"), *BP->GetName());
	return true;
}

bool FAudioMCPBlueprintManager::HasActiveBlueprint() const
{
	return ActiveBlueprint.IsValid();
}

FString FAudioMCPBlueprintManager::GetActiveBlueprintName() const
{
	if (ActiveBlueprint.IsValid())
	{
		return ActiveBlueprint->GetName();
	}
	return TEXT("");
}

// ==========================================================================
// Node operations
// ==========================================================================

bool FAudioMCPBlueprintManager::AddCallFunctionNode(
	const FString& Id, const FString& FunctionName,
	int32 PosX, int32 PosY, FString& OutError)
{
	if (!HasActiveBlueprint())
	{
		OutError = TEXT("No active Blueprint — call bp_open_blueprint first");
		return false;
	}

	BuildAllowlist();
	if (!IsAllowedFunction(FunctionName))
	{
		OutError = FString::Printf(TEXT("Function '%s' is not in the audio allowlist"), *FunctionName);
		return false;
	}

	UFunction* Func = FindAudioFunction(FunctionName);
	if (!Func)
	{
		OutError = FString::Printf(TEXT("Could not find UFunction '%s'"), *FunctionName);
		return false;
	}

	UEdGraph* Graph = GetEventGraph(OutError);
	if (!Graph) return false;

	// Modify for undo support
	Graph->Modify();

	UK2Node_CallFunction* Node = NewObject<UK2Node_CallFunction>(Graph);
	Node->SetFromFunction(Func);
	Node->AllocateDefaultPins();
	Node->NodePosX = PosX;
	Node->NodePosY = PosY;

	Graph->AddNode(Node, /*bFromUI=*/false, /*bSelectNewNode=*/false);

	NodeHandles.Add(Id, Node);

	UE_LOG(LogAudioMCPBP, Log, TEXT("Added CallFunction node '%s' (%s) at (%d,%d)"),
		*Id, *FunctionName, PosX, PosY);
	return true;
}

bool FAudioMCPBlueprintManager::AddCustomEventNode(
	const FString& Id, const FString& EventName,
	int32 PosX, int32 PosY, FString& OutError)
{
	if (!HasActiveBlueprint())
	{
		OutError = TEXT("No active Blueprint — call bp_open_blueprint first");
		return false;
	}

	UEdGraph* Graph = GetEventGraph(OutError);
	if (!Graph) return false;

	Graph->Modify();

	UK2Node_CustomEvent* Node = NewObject<UK2Node_CustomEvent>(Graph);
	Node->CustomFunctionName = FName(*EventName);
	Node->AllocateDefaultPins();
	Node->NodePosX = PosX;
	Node->NodePosY = PosY;

	Graph->AddNode(Node, /*bFromUI=*/false, /*bSelectNewNode=*/false);

	NodeHandles.Add(Id, Node);

	UE_LOG(LogAudioMCPBP, Log, TEXT("Added CustomEvent node '%s' (%s) at (%d,%d)"),
		*Id, *EventName, PosX, PosY);
	return true;
}

bool FAudioMCPBlueprintManager::AddVariableGetNode(
	const FString& Id, const FString& VarName,
	int32 PosX, int32 PosY, FString& OutError)
{
	if (!HasActiveBlueprint())
	{
		OutError = TEXT("No active Blueprint — call bp_open_blueprint first");
		return false;
	}

	// Verify variable exists on the Blueprint
	UBlueprint* BP = ActiveBlueprint.Get();
	FName VarFName(*VarName);
	FProperty* Prop = FindFProperty<FProperty>(BP->SkeletonGeneratedClass, VarFName);
	if (!Prop)
	{
		OutError = FString::Printf(TEXT("Variable '%s' not found on Blueprint '%s'"),
			*VarName, *BP->GetName());
		return false;
	}

	UEdGraph* Graph = GetEventGraph(OutError);
	if (!Graph) return false;

	Graph->Modify();

	UK2Node_VariableGet* Node = NewObject<UK2Node_VariableGet>(Graph);
	Node->VariableReference.SetSelfMember(VarFName);
	Node->AllocateDefaultPins();
	Node->NodePosX = PosX;
	Node->NodePosY = PosY;

	Graph->AddNode(Node, /*bFromUI=*/false, /*bSelectNewNode=*/false);

	NodeHandles.Add(Id, Node);

	UE_LOG(LogAudioMCPBP, Log, TEXT("Added VariableGet node '%s' (%s) at (%d,%d)"),
		*Id, *VarName, PosX, PosY);
	return true;
}

bool FAudioMCPBlueprintManager::AddVariableSetNode(
	const FString& Id, const FString& VarName,
	int32 PosX, int32 PosY, FString& OutError)
{
	if (!HasActiveBlueprint())
	{
		OutError = TEXT("No active Blueprint — call bp_open_blueprint first");
		return false;
	}

	UBlueprint* BP = ActiveBlueprint.Get();
	FName VarFName(*VarName);
	FProperty* Prop = FindFProperty<FProperty>(BP->SkeletonGeneratedClass, VarFName);
	if (!Prop)
	{
		OutError = FString::Printf(TEXT("Variable '%s' not found on Blueprint '%s'"),
			*VarName, *BP->GetName());
		return false;
	}

	UEdGraph* Graph = GetEventGraph(OutError);
	if (!Graph) return false;

	Graph->Modify();

	UK2Node_VariableSet* Node = NewObject<UK2Node_VariableSet>(Graph);
	Node->VariableReference.SetSelfMember(VarFName);
	Node->AllocateDefaultPins();
	Node->NodePosX = PosX;
	Node->NodePosY = PosY;

	Graph->AddNode(Node, /*bFromUI=*/false, /*bSelectNewNode=*/false);

	NodeHandles.Add(Id, Node);

	UE_LOG(LogAudioMCPBP, Log, TEXT("Added VariableSet node '%s' (%s) at (%d,%d)"),
		*Id, *VarName, PosX, PosY);
	return true;
}

// ==========================================================================
// Pin operations
// ==========================================================================

bool FAudioMCPBlueprintManager::ConnectPins(
	const FString& FromId, const FString& FromPin,
	const FString& ToId, const FString& ToPin, FString& OutError)
{
	if (!HasActiveBlueprint())
	{
		OutError = TEXT("No active Blueprint");
		return false;
	}

	TWeakObjectPtr<UEdGraphNode>* FromPtr = NodeHandles.Find(FromId);
	if (!FromPtr || !FromPtr->IsValid())
	{
		OutError = FString::Printf(TEXT("Unknown node '%s' — register it first"), *FromId);
		return false;
	}
	TWeakObjectPtr<UEdGraphNode>* ToPtr = NodeHandles.Find(ToId);
	if (!ToPtr || !ToPtr->IsValid())
	{
		OutError = FString::Printf(TEXT("Unknown node '%s' — register it first"), *ToId);
		return false;
	}

	UEdGraphNode* FromNode = FromPtr->Get();
	UEdGraphNode* ToNode = ToPtr->Get();

	// Find output pin on source node
	UEdGraphPin* OutPin = nullptr;
	for (UEdGraphPin* Pin : FromNode->Pins)
	{
		if (Pin->Direction == EGPD_Output && Pin->PinName.ToString() == FromPin)
		{
			OutPin = Pin;
			break;
		}
	}
	if (!OutPin)
	{
		OutError = FString::Printf(TEXT("Output pin '%s' not found on node '%s'"), *FromPin, *FromId);
		return false;
	}

	// Find input pin on target node
	UEdGraphPin* InPin = nullptr;
	for (UEdGraphPin* Pin : ToNode->Pins)
	{
		if (Pin->Direction == EGPD_Input && Pin->PinName.ToString() == ToPin)
		{
			InPin = Pin;
			break;
		}
	}
	if (!InPin)
	{
		OutError = FString::Printf(TEXT("Input pin '%s' not found on node '%s'"), *ToPin, *ToId);
		return false;
	}

	// Try creating the connection
	const UEdGraphSchema_K2* Schema = GetDefault<UEdGraphSchema_K2>();
	bool bConnected = Schema->TryCreateConnection(OutPin, InPin);
	if (!bConnected)
	{
		OutError = FString::Printf(TEXT("Cannot connect %s.%s -> %s.%s (type mismatch or incompatible)"),
			*FromId, *FromPin, *ToId, *ToPin);
		return false;
	}

	UE_LOG(LogAudioMCPBP, Log, TEXT("Connected %s.%s -> %s.%s"), *FromId, *FromPin, *ToId, *ToPin);
	return true;
}

bool FAudioMCPBlueprintManager::SetPinDefault(
	const FString& NodeId, const FString& PinName,
	const FString& Value, FString& OutError)
{
	if (!HasActiveBlueprint())
	{
		OutError = TEXT("No active Blueprint");
		return false;
	}

	TWeakObjectPtr<UEdGraphNode>* NodePtr = NodeHandles.Find(NodeId);
	if (!NodePtr || !NodePtr->IsValid())
	{
		OutError = FString::Printf(TEXT("Unknown node '%s'"), *NodeId);
		return false;
	}

	UEdGraphNode* Node = NodePtr->Get();

	// Find the pin by name (input direction)
	UEdGraphPin* Pin = nullptr;
	for (UEdGraphPin* P : Node->Pins)
	{
		if (P->PinName.ToString() == PinName && P->Direction == EGPD_Input)
		{
			Pin = P;
			break;
		}
	}
	if (!Pin)
	{
		OutError = FString::Printf(TEXT("Input pin '%s' not found on node '%s'"), *PinName, *NodeId);
		return false;
	}

	const UEdGraphSchema_K2* Schema = GetDefault<UEdGraphSchema_K2>();
	if (!Schema->TrySetDefaultValue(*Pin, Value))
	{
		OutError = FString::Printf(TEXT("Failed to set default value '%s' on pin '%s' of node '%s'"), *Value, *PinName, *NodeId);
		return false;
	}

	UE_LOG(LogAudioMCPBP, Log, TEXT("Set %s.%s = %s"), *NodeId, *PinName, *Value);
	return true;
}

// ==========================================================================
// Compile
// ==========================================================================

bool FAudioMCPBlueprintManager::CompileBlueprint(
	TArray<FString>& OutMessages, FString& OutError)
{
	if (!HasActiveBlueprint())
	{
		OutError = TEXT("No active Blueprint — call bp_open_blueprint first");
		return false;
	}

	UBlueprint* BP = ActiveBlueprint.Get();
	FKismetEditorUtilities::CompileBlueprint(BP, EBlueprintCompileOptions::None);

	// Gather compiler results (CurrentMessageLog may be null after clean compile)
	if (BP->CurrentMessageLog)
	{
		for (const FCompilerResultsLog::TCompilerResultsLogItem& Entry : BP->CurrentMessageLog->Messages)
		{
			if (Entry.IsValid())
			{
				OutMessages.Add(Entry->ToText().ToString());
			}
		}
	}

	bool bSuccess = (BP->Status != BS_Error);
	if (!bSuccess)
	{
		OutError = TEXT("Compilation failed — see messages for details");
	}

	UE_LOG(LogAudioMCPBP, Log, TEXT("Compiled '%s': %s (%d messages)"),
		*BP->GetName(), bSuccess ? TEXT("OK") : TEXT("ERRORS"), OutMessages.Num());
	return bSuccess;
}

// ==========================================================================
// Introspection
// ==========================================================================

bool FAudioMCPBlueprintManager::RegisterExistingNode(
	const FString& Id, const FString& NodeGuid,
	FString& OutNodeClass, FString& OutNodeTitle, FString& OutError)
{
	if (!HasActiveBlueprint())
	{
		OutError = TEXT("No active Blueprint");
		return false;
	}

	FGuid Guid;
	if (!FGuid::Parse(NodeGuid, Guid))
	{
		OutError = FString::Printf(TEXT("Invalid GUID format: '%s'"), *NodeGuid);
		return false;
	}

	UBlueprint* BP = ActiveBlueprint.Get();

	// Search all graphs for the node with this GUID
	for (UEdGraph* Graph : BP->UbergraphPages)
	{
		for (UEdGraphNode* Node : Graph->Nodes)
		{
			if (Node->NodeGuid == Guid)
			{
				NodeHandles.Add(Id, Node);
				OutNodeClass = Node->GetClass()->GetName();
				OutNodeTitle = Node->GetNodeTitle(ENodeTitleType::ListView).ToString();

				UE_LOG(LogAudioMCPBP, Log, TEXT("Registered existing node '%s' -> %s (%s)"),
					*Id, *OutNodeClass, *OutNodeTitle);
				return true;
			}
		}
	}

	// Also check function graphs
	for (UEdGraph* Graph : BP->FunctionGraphs)
	{
		for (UEdGraphNode* Node : Graph->Nodes)
		{
			if (Node->NodeGuid == Guid)
			{
				NodeHandles.Add(Id, Node);
				OutNodeClass = Node->GetClass()->GetName();
				OutNodeTitle = Node->GetNodeTitle(ENodeTitleType::ListView).ToString();
				return true;
			}
		}
	}

	OutError = FString::Printf(TEXT("No node with GUID '%s' found in Blueprint"), *NodeGuid);
	return false;
}

bool FAudioMCPBlueprintManager::ListPins(
	const FString& NodeId, TArray<TSharedPtr<FJsonValue>>& OutPins, FString& OutError)
{
	TWeakObjectPtr<UEdGraphNode>* NodePtr = NodeHandles.Find(NodeId);
	if (!NodePtr || !NodePtr->IsValid())
	{
		OutError = FString::Printf(TEXT("Unknown node '%s'"), *NodeId);
		return false;
	}

	UEdGraphNode* Node = NodePtr->Get();

	for (UEdGraphPin* Pin : Node->Pins)
	{
		if (Pin->bHidden) continue;

		TSharedPtr<FJsonObject> PinObj = MakeShared<FJsonObject>();
		PinObj->SetStringField(TEXT("name"), Pin->PinName.ToString());
		PinObj->SetStringField(TEXT("direction"),
			Pin->Direction == EGPD_Input ? TEXT("input") : TEXT("output"));
		PinObj->SetStringField(TEXT("type"), Pin->PinType.PinCategory.ToString());
		PinObj->SetStringField(TEXT("default"), Pin->DefaultValue);
		PinObj->SetBoolField(TEXT("connected"), Pin->LinkedTo.Num() > 0);

		// Include sub-category (e.g., the class name for object pins)
		if (!Pin->PinType.PinSubCategoryObject.IsNull())
		{
			PinObj->SetStringField(TEXT("sub_type"),
				Pin->PinType.PinSubCategoryObject->GetName());
		}

		OutPins.Add(MakeShared<FJsonValueObject>(PinObj));
	}

	return true;
}

// ==========================================================================
// Private helpers
// ==========================================================================

UEdGraph* FAudioMCPBlueprintManager::GetEventGraph(FString& OutError) const
{
	if (!ActiveBlueprint.IsValid())
	{
		OutError = TEXT("No active Blueprint");
		return nullptr;
	}

	UBlueprint* BP = ActiveBlueprint.Get();
	if (BP->UbergraphPages.Num() == 0)
	{
		OutError = TEXT("Blueprint has no event graph (UbergraphPages)");
		return nullptr;
	}

	return BP->UbergraphPages[0];
}

bool FAudioMCPBlueprintManager::IsAllowedFunction(const FString& FunctionName) const
{
	return AllowedFunctions.Contains(FunctionName);
}

UFunction* FAudioMCPBlueprintManager::FindAudioFunction(const FString& FunctionName) const
{
	// Search across audio-relevant classes
	static const TArray<UClass*> SearchClasses = []()
	{
		TArray<UClass*> Classes;
		// UAudioComponent
		if (UClass* C = FindObject<UClass>(nullptr, TEXT("/Script/Engine.AudioComponent")))
			Classes.Add(C);
		// UGameplayStatics
		if (UClass* C = FindObject<UClass>(nullptr, TEXT("/Script/Engine.GameplayStatics")))
			Classes.Add(C);
		// AActor
		if (UClass* C = FindObject<UClass>(nullptr, TEXT("/Script/Engine.Actor")))
			Classes.Add(C);
		// UKismetMathLibrary
		if (UClass* C = FindObject<UClass>(nullptr, TEXT("/Script/Engine.KismetMathLibrary")))
			Classes.Add(C);
		// UKismetSystemLibrary (Print String)
		if (UClass* C = FindObject<UClass>(nullptr, TEXT("/Script/Engine.KismetSystemLibrary")))
			Classes.Add(C);
		// AkComponent (Wwise)
		if (UClass* C = FindObject<UClass>(nullptr, TEXT("/Script/AkAudio.AkComponent")))
			Classes.Add(C);
		// AkGameplayStatics (Wwise)
		if (UClass* C = FindObject<UClass>(nullptr, TEXT("/Script/AkAudio.AkGameplayStatics")))
			Classes.Add(C);
		return Classes;
	}();

	FName FuncFName(*FunctionName);
	for (UClass* Class : SearchClasses)
	{
		if (!Class) continue;
		if (UFunction* Func = Class->FindFunctionByName(FuncFName))
		{
			return Func;
		}
	}

	return nullptr;
}

void FAudioMCPBlueprintManager::BuildAllowlist()
{
	if (bAllowlistBuilt) return;
	bAllowlistBuilt = true;

	// AudioComponent parameter setting
	AllowedFunctions.Add(TEXT("SetFloatParameter"));
	AllowedFunctions.Add(TEXT("SetIntParameter"));
	AllowedFunctions.Add(TEXT("SetBoolParameter"));
	AllowedFunctions.Add(TEXT("SetStringParameter"));
	AllowedFunctions.Add(TEXT("SetWaveParameter"));
	AllowedFunctions.Add(TEXT("ExecuteTriggerParameter"));

	// Playback
	AllowedFunctions.Add(TEXT("PlaySound2D"));
	AllowedFunctions.Add(TEXT("PlaySoundAtLocation"));
	AllowedFunctions.Add(TEXT("SpawnSoundAtLocation"));
	AllowedFunctions.Add(TEXT("SpawnSound2D"));
	AllowedFunctions.Add(TEXT("Play"));
	AllowedFunctions.Add(TEXT("Stop"));
	AllowedFunctions.Add(TEXT("SetPaused"));
	AllowedFunctions.Add(TEXT("IsPlaying"));
	AllowedFunctions.Add(TEXT("FadeIn"));
	AllowedFunctions.Add(TEXT("FadeOut"));
	AllowedFunctions.Add(TEXT("AdjustVolume"));

	// Properties
	AllowedFunctions.Add(TEXT("SetVolumeMultiplier"));
	AllowedFunctions.Add(TEXT("SetPitchMultiplier"));
	AllowedFunctions.Add(TEXT("SetSound"));

	// Spatial
	AllowedFunctions.Add(TEXT("SetWorldLocation"));
	AllowedFunctions.Add(TEXT("SetWorldRotation"));
	AllowedFunctions.Add(TEXT("GetDistanceTo"));
	AllowedFunctions.Add(TEXT("GetActorLocation"));

	// Sound mix
	AllowedFunctions.Add(TEXT("SetSoundMixClassOverride"));
	AllowedFunctions.Add(TEXT("PushSoundMixModifier"));
	AllowedFunctions.Add(TEXT("PopSoundMixModifier"));

	// Wwise (AkComponent)
	AllowedFunctions.Add(TEXT("PostEvent"));
	AllowedFunctions.Add(TEXT("PostAkEvent"));
	AllowedFunctions.Add(TEXT("SetRTPCValue"));
	AllowedFunctions.Add(TEXT("SetSwitch"));
	AllowedFunctions.Add(TEXT("SetState"));
	AllowedFunctions.Add(TEXT("PostTrigger"));

	// Math helpers
	AllowedFunctions.Add(TEXT("Multiply_FloatFloat"));
	AllowedFunctions.Add(TEXT("Add_FloatFloat"));
	AllowedFunctions.Add(TEXT("Subtract_FloatFloat"));
	AllowedFunctions.Add(TEXT("Divide_FloatFloat"));
	AllowedFunctions.Add(TEXT("MapRangeClamped"));
	AllowedFunctions.Add(TEXT("Lerp"));
	AllowedFunctions.Add(TEXT("FClamp"));

	// Debug
	AllowedFunctions.Add(TEXT("PrintString"));

	UE_LOG(LogAudioMCPBP, Log, TEXT("Built audio function allowlist: %d entries"),
		AllowedFunctions.Num());
}

void FAudioMCPBlueprintManager::ResetHandles()
{
	NodeHandles.Empty();
}

#undef LOCTEXT_NAMESPACE
