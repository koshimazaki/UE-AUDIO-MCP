// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/VariableCommands.h"
#include "AudioMCPBuilderManager.h"
#include "AudioMCPTypes.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

// ---------------------------------------------------------------------------
// add_graph_variable
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FAddGraphVariableCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString Name;
	if (!Params->TryGetStringField(TEXT("name"), Name))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'name'"));
	}

	FString Type;
	if (!Params->TryGetStringField(TEXT("type"), Type))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'type'"));
	}

	// Optional default value
	FString DefaultValue;
	Params->TryGetStringField(TEXT("default"), DefaultValue);

	FString Error;
	if (!BuilderManager.AddGraphVariable(Name, Type, DefaultValue, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Added graph variable '%s' (%s)"), *Name, *Type));
	Response->SetStringField(TEXT("name"), Name);
	Response->SetStringField(TEXT("type"), Type);
	return Response;
}

// ---------------------------------------------------------------------------
// add_variable_get_node
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FAddVariableGetNodeCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString NodeId;
	if (!Params->TryGetStringField(TEXT("id"), NodeId))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'id'"));
	}

	FString VariableName;
	if (!Params->TryGetStringField(TEXT("variable_name"), VariableName))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'variable_name'"));
	}

	// Optional: "delayed" mode reads previous-frame value
	bool bDelayed = false;
	Params->TryGetBoolField(TEXT("delayed"), bDelayed);

	FString Error;
	if (!BuilderManager.AddVariableGetNode(NodeId, VariableName, bDelayed, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Added %s variable get node '%s' for '%s'"),
			bDelayed ? TEXT("delayed") : TEXT(""), *NodeId, *VariableName));
	Response->SetStringField(TEXT("id"), NodeId);
	Response->SetStringField(TEXT("variable_name"), VariableName);
	Response->SetBoolField(TEXT("delayed"), bDelayed);
	return Response;
}

// ---------------------------------------------------------------------------
// add_variable_set_node
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FAddVariableSetNodeCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString NodeId;
	if (!Params->TryGetStringField(TEXT("id"), NodeId))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'id'"));
	}

	FString VariableName;
	if (!Params->TryGetStringField(TEXT("variable_name"), VariableName))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'variable_name'"));
	}

	FString Error;
	if (!BuilderManager.AddVariableSetNode(NodeId, VariableName, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Added variable set node '%s' for '%s'"), *NodeId, *VariableName));
	Response->SetStringField(TEXT("id"), NodeId);
	Response->SetStringField(TEXT("variable_name"), VariableName);
	return Response;
}
