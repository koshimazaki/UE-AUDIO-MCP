// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/BPBuilderCommands.h"
#include "AudioMCPBlueprintManager.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

DEFINE_LOG_CATEGORY_STATIC(LogBPBuilderCmds, Log, All);

namespace
{
	/** Helper: create an error response. */
	TSharedPtr<FJsonObject> BPError(const FString& Message)
	{
		TSharedPtr<FJsonObject> Resp = MakeShared<FJsonObject>();
		Resp->SetStringField(TEXT("status"), TEXT("error"));
		Resp->SetStringField(TEXT("message"), Message);
		return Resp;
	}

	/** Helper: get the BlueprintManager or return error. */
	FAudioMCPBlueprintManager* GetBPManager(TSharedPtr<FJsonObject>& OutError)
	{
		FAudioMCPBlueprintManager* Mgr = FAudioMCPBlueprintManager::Get();
		if (!Mgr)
		{
			OutError = BPError(TEXT("BlueprintManager not initialized"));
		}
		return Mgr;
	}
}

// ==========================================================================
// bp_open_blueprint
// ==========================================================================

TSharedPtr<FJsonObject> FBPOpenBlueprintCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	TSharedPtr<FJsonObject> Err;
	FAudioMCPBlueprintManager* Mgr = GetBPManager(Err);
	if (!Mgr) return Err;

	FString AssetPath = Params->GetStringField(TEXT("asset_path"));
	if (AssetPath.IsEmpty())
	{
		return BPError(TEXT("Missing required param: asset_path"));
	}

	FString Error;
	if (!Mgr->OpenBlueprint(AssetPath, Error))
	{
		return BPError(Error);
	}

	// Collect auto-registered nodes for the response
	TArray<TSharedPtr<FJsonValue>> NodeList;
	Mgr->AutoRegisterNodes(NodeList);

	TSharedPtr<FJsonObject> Resp = MakeShared<FJsonObject>();
	Resp->SetStringField(TEXT("status"), TEXT("ok"));
	Resp->SetStringField(TEXT("blueprint_name"), Mgr->GetActiveBlueprintName());
	Resp->SetNumberField(TEXT("node_count"), NodeList.Num());
	Resp->SetArrayField(TEXT("nodes"), NodeList);
	return Resp;
}

// ==========================================================================
// bp_add_node
// ==========================================================================

TSharedPtr<FJsonObject> FBPAddNodeCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	TSharedPtr<FJsonObject> Err;
	FAudioMCPBlueprintManager* Mgr = GetBPManager(Err);
	if (!Mgr) return Err;

	FString Id = Params->GetStringField(TEXT("id"));
	FString NodeKind = Params->GetStringField(TEXT("node_kind"));

	if (Id.IsEmpty())
		return BPError(TEXT("Missing required param: id"));
	if (NodeKind.IsEmpty())
		return BPError(TEXT("Missing required param: node_kind"));

	// Position (optional, defaults to 0,0)
	int32 PosX = 0, PosY = 0;
	const TArray<TSharedPtr<FJsonValue>>* PosArray;
	if (Params->TryGetArrayField(TEXT("position"), PosArray) && PosArray->Num() >= 2)
	{
		PosX = static_cast<int32>((*PosArray)[0]->AsNumber());
		PosY = static_cast<int32>((*PosArray)[1]->AsNumber());
	}

	FString Error;
	bool bSuccess = false;
	int32 PinCount = 0;

	if (NodeKind == TEXT("CallFunction"))
	{
		FString FunctionName = Params->GetStringField(TEXT("function_name"));
		if (FunctionName.IsEmpty())
			return BPError(TEXT("CallFunction requires 'function_name' param"));

		bSuccess = Mgr->AddCallFunctionNode(Id, FunctionName, PosX, PosY, Error);
	}
	else if (NodeKind == TEXT("CustomEvent"))
	{
		FString EventName = Params->GetStringField(TEXT("event_name"));
		if (EventName.IsEmpty())
			return BPError(TEXT("CustomEvent requires 'event_name' param"));

		bSuccess = Mgr->AddCustomEventNode(Id, EventName, PosX, PosY, Error);
	}
	else if (NodeKind == TEXT("VariableGet"))
	{
		FString VarName = Params->GetStringField(TEXT("variable_name"));
		if (VarName.IsEmpty())
			return BPError(TEXT("VariableGet requires 'variable_name' param"));

		bSuccess = Mgr->AddVariableGetNode(Id, VarName, PosX, PosY, Error);
	}
	else if (NodeKind == TEXT("VariableSet"))
	{
		FString VarName = Params->GetStringField(TEXT("variable_name"));
		if (VarName.IsEmpty())
			return BPError(TEXT("VariableSet requires 'variable_name' param"));

		bSuccess = Mgr->AddVariableSetNode(Id, VarName, PosX, PosY, Error);
	}
	else
	{
		return BPError(FString::Printf(
			TEXT("Unknown node_kind '%s'. Must be: CallFunction, CustomEvent, VariableGet, VariableSet"),
			*NodeKind));
	}

	if (!bSuccess)
	{
		return BPError(Error);
	}

	TSharedPtr<FJsonObject> Resp = MakeShared<FJsonObject>();
	Resp->SetStringField(TEXT("status"), TEXT("ok"));
	Resp->SetStringField(TEXT("id"), Id);
	Resp->SetStringField(TEXT("node_kind"), NodeKind);
	return Resp;
}

// ==========================================================================
// bp_connect_pins
// ==========================================================================

TSharedPtr<FJsonObject> FBPConnectPinsCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	TSharedPtr<FJsonObject> Err;
	FAudioMCPBlueprintManager* Mgr = GetBPManager(Err);
	if (!Mgr) return Err;

	FString FromNode = Params->GetStringField(TEXT("from_node"));
	FString FromPin = Params->GetStringField(TEXT("from_pin"));
	FString ToNode = Params->GetStringField(TEXT("to_node"));
	FString ToPin = Params->GetStringField(TEXT("to_pin"));

	if (FromNode.IsEmpty() || FromPin.IsEmpty() || ToNode.IsEmpty() || ToPin.IsEmpty())
	{
		return BPError(TEXT("Missing required params: from_node, from_pin, to_node, to_pin"));
	}

	FString Error;
	if (!Mgr->ConnectPins(FromNode, FromPin, ToNode, ToPin, Error))
	{
		return BPError(Error);
	}

	TSharedPtr<FJsonObject> Resp = MakeShared<FJsonObject>();
	Resp->SetStringField(TEXT("status"), TEXT("ok"));
	Resp->SetStringField(TEXT("connection"),
		FString::Printf(TEXT("%s.%s -> %s.%s"), *FromNode, *FromPin, *ToNode, *ToPin));
	return Resp;
}

// ==========================================================================
// bp_set_pin_default
// ==========================================================================

TSharedPtr<FJsonObject> FBPSetPinDefaultCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	TSharedPtr<FJsonObject> Err;
	FAudioMCPBlueprintManager* Mgr = GetBPManager(Err);
	if (!Mgr) return Err;

	FString NodeId = Params->GetStringField(TEXT("node_id"));
	FString PinName = Params->GetStringField(TEXT("pin_name"));
	FString Value = Params->GetStringField(TEXT("value"));

	if (NodeId.IsEmpty() || PinName.IsEmpty())
	{
		return BPError(TEXT("Missing required params: node_id, pin_name"));
	}

	FString Error;
	if (!Mgr->SetPinDefault(NodeId, PinName, Value, Error))
	{
		return BPError(Error);
	}

	TSharedPtr<FJsonObject> Resp = MakeShared<FJsonObject>();
	Resp->SetStringField(TEXT("status"), TEXT("ok"));
	Resp->SetStringField(TEXT("node_id"), NodeId);
	Resp->SetStringField(TEXT("pin_name"), PinName);
	Resp->SetStringField(TEXT("value"), Value);
	return Resp;
}

// ==========================================================================
// bp_compile
// ==========================================================================

TSharedPtr<FJsonObject> FBPCompileCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	TSharedPtr<FJsonObject> Err;
	FAudioMCPBlueprintManager* Mgr = GetBPManager(Err);
	if (!Mgr) return Err;

	TArray<FString> Messages;
	FString Error;
	bool bSuccess = Mgr->CompileBlueprint(Messages, Error);

	TSharedPtr<FJsonObject> Resp = MakeShared<FJsonObject>();
	Resp->SetStringField(TEXT("status"), bSuccess ? TEXT("ok") : TEXT("error"));
	Resp->SetStringField(TEXT("compile_result"), bSuccess ? TEXT("success") : TEXT("failed"));

	if (!bSuccess)
	{
		Resp->SetStringField(TEXT("message"), Error);
	}

	TArray<TSharedPtr<FJsonValue>> MsgArray;
	for (const FString& Msg : Messages)
	{
		MsgArray.Add(MakeShared<FJsonValueString>(Msg));
	}
	Resp->SetArrayField(TEXT("messages"), MsgArray);

	return Resp;
}

// ==========================================================================
// bp_register_existing_node
// ==========================================================================

TSharedPtr<FJsonObject> FBPRegisterExistingNodeCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	TSharedPtr<FJsonObject> Err;
	FAudioMCPBlueprintManager* Mgr = GetBPManager(Err);
	if (!Mgr) return Err;

	FString Id = Params->GetStringField(TEXT("id"));
	FString NodeGuid = Params->GetStringField(TEXT("node_guid"));

	if (Id.IsEmpty() || NodeGuid.IsEmpty())
	{
		return BPError(TEXT("Missing required params: id, node_guid"));
	}

	FString NodeClass, NodeTitle, Error;
	if (!Mgr->RegisterExistingNode(Id, NodeGuid, NodeClass, NodeTitle, Error))
	{
		return BPError(Error);
	}

	TSharedPtr<FJsonObject> Resp = MakeShared<FJsonObject>();
	Resp->SetStringField(TEXT("status"), TEXT("ok"));
	Resp->SetStringField(TEXT("id"), Id);
	Resp->SetStringField(TEXT("node_class"), NodeClass);
	Resp->SetStringField(TEXT("title"), NodeTitle);
	return Resp;
}

// ==========================================================================
// bp_list_pins
// ==========================================================================

TSharedPtr<FJsonObject> FBPListPinsCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	TSharedPtr<FJsonObject> Err;
	FAudioMCPBlueprintManager* Mgr = GetBPManager(Err);
	if (!Mgr) return Err;

	FString NodeId = Params->GetStringField(TEXT("node_id"));
	if (NodeId.IsEmpty())
	{
		return BPError(TEXT("Missing required param: node_id"));
	}

	TArray<TSharedPtr<FJsonValue>> Pins;
	FString Error;
	if (!Mgr->ListPins(NodeId, Pins, Error))
	{
		return BPError(Error);
	}

	TSharedPtr<FJsonObject> Resp = MakeShared<FJsonObject>();
	Resp->SetStringField(TEXT("status"), TEXT("ok"));
	Resp->SetStringField(TEXT("node_id"), NodeId);
	Resp->SetNumberField(TEXT("pin_count"), Pins.Num());
	Resp->SetArrayField(TEXT("pins"), Pins);
	return Resp;
}
