// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/QueryCommands.h"
#include "AudioMCPBuilderManager.h"
#include "AudioMCPTypes.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

// ---------------------------------------------------------------------------
// get_graph_input_names
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FGetGraphInputNamesCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	TArray<FString> Names;
	FString Error;
	if (!BuilderManager.GetGraphInputNames(Names, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TArray<TSharedPtr<FJsonValue>> JsonNames;
	for (const FString& Name : Names)
	{
		JsonNames.Add(MakeShared<FJsonValueString>(Name));
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Found %d graph inputs"), Names.Num()));
	Response->SetArrayField(TEXT("names"), JsonNames);
	Response->SetNumberField(TEXT("count"), Names.Num());
	return Response;
}

// ---------------------------------------------------------------------------
// set_live_updates
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FSetLiveUpdatesCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	bool bEnabled = true;
	if (!Params->TryGetBoolField(TEXT("enabled"), bEnabled))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'enabled'"));
	}

	FString Error;
	if (!BuilderManager.SetLiveUpdates(bEnabled, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Live updates %s"), bEnabled ? TEXT("enabled") : TEXT("disabled")));
	Response->SetBoolField(TEXT("enabled"), bEnabled);
	return Response;
}
