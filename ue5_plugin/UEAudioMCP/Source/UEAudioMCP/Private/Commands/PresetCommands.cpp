// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/PresetCommands.h"
#include "AudioMCPBuilderManager.h"
#include "AudioMCPTypes.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

// ---------------------------------------------------------------------------
// convert_to_preset
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FConvertToPresetCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString ReferencedAsset;
	if (!Params->TryGetStringField(TEXT("referenced_asset"), ReferencedAsset))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'referenced_asset'"));
	}

	FString Error;
	if (!BuilderManager.ConvertToPreset(ReferencedAsset, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Converted to preset of '%s'"), *ReferencedAsset));
	Response->SetStringField(TEXT("referenced_asset"), ReferencedAsset);
	return Response;
}

// ---------------------------------------------------------------------------
// convert_from_preset
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FConvertFromPresetCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString Error;
	if (!BuilderManager.ConvertFromPreset(Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	return AudioMCP::MakeOkResponse(TEXT("Converted from preset to full graph"));
}
