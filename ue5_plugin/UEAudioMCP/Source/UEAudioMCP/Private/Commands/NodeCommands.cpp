// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/NodeCommands.h"
#include "AudioMCPBuilderManager.h"
#include "AudioMCPTypes.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

// ---------------------------------------------------------------------------
// add_node
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FAddNodeCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString NodeId;
	if (!Params->TryGetStringField(TEXT("id"), NodeId))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'id'"));
	}

	FString NodeType;
	if (!Params->TryGetStringField(TEXT("node_type"), NodeType))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'node_type'"));
	}

	// Position: JSON array [x, y] or default [0, 0]
	int32 PosX = 0;
	int32 PosY = 0;

	const TArray<TSharedPtr<FJsonValue>>* PositionArray;
	if (Params->TryGetArrayField(TEXT("position"), PositionArray) && PositionArray->Num() >= 2)
	{
		PosX = static_cast<int32>((*PositionArray)[0]->AsNumber());
		PosY = static_cast<int32>((*PositionArray)[1]->AsNumber());
	}

	FString Error;
	if (!BuilderManager.AddNode(NodeId, NodeType, PosX, PosY, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Added node '%s' (%s) at (%d, %d)"), *NodeId, *NodeType, PosX, PosY));
	Response->SetStringField(TEXT("id"), NodeId);
	Response->SetStringField(TEXT("node_type"), NodeType);
	return Response;
}

// ---------------------------------------------------------------------------
// set_default
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FSetDefaultCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString NodeId;
	if (!Params->TryGetStringField(TEXT("node_id"), NodeId))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'node_id'"));
	}

	FString InputName;
	if (!Params->TryGetStringField(TEXT("input"), InputName))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'input'"));
	}

	// Value can be any JSON type (number, string, bool, array)
	TSharedPtr<FJsonValue> Value = Params->TryGetField(TEXT("value"));
	if (!Value.IsValid())
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'value'"));
	}

	FString Error;
	if (!BuilderManager.SetNodeDefault(NodeId, InputName, Value, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Set default %s.%s"), *NodeId, *InputName));
	Response->SetStringField(TEXT("node_id"), NodeId);
	Response->SetStringField(TEXT("input"), InputName);
	return Response;
}

// ---------------------------------------------------------------------------
// connect
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FConnectCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString FromNode;
	if (!Params->TryGetStringField(TEXT("from_node"), FromNode))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'from_node'"));
	}

	FString FromPin;
	if (!Params->TryGetStringField(TEXT("from_pin"), FromPin))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'from_pin'"));
	}

	FString ToNode;
	if (!Params->TryGetStringField(TEXT("to_node"), ToNode))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'to_node'"));
	}

	FString ToPin;
	if (!Params->TryGetStringField(TEXT("to_pin"), ToPin))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'to_pin'"));
	}

	FString Error;
	if (!BuilderManager.ConnectNodes(FromNode, FromPin, ToNode, ToPin, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Connected %s.%s -> %s.%s"), *FromNode, *FromPin, *ToNode, *ToPin));
	Response->SetStringField(TEXT("from_node"), FromNode);
	Response->SetStringField(TEXT("from_pin"), FromPin);
	Response->SetStringField(TEXT("to_node"), ToNode);
	Response->SetStringField(TEXT("to_pin"), ToPin);
	return Response;
}
