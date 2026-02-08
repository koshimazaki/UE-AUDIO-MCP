// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/BuilderCommands.h"
#include "AudioMCPBuilderManager.h"
#include "AudioMCPTypes.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

// ---------------------------------------------------------------------------
// create_builder
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FCreateBuilderCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString AssetType;
	if (!Params->TryGetStringField(TEXT("asset_type"), AssetType))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'asset_type'"));
	}

	FString Name;
	if (!Params->TryGetStringField(TEXT("name"), Name))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'name'"));
	}

	// Validate asset_type (case-insensitive)
	if (!AssetType.Equals(TEXT("Source"), ESearchCase::IgnoreCase)
		&& !AssetType.Equals(TEXT("Patch"), ESearchCase::IgnoreCase)
		&& !AssetType.Equals(TEXT("Preset"), ESearchCase::IgnoreCase))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Invalid asset_type '%s'. Must be Source, Patch, or Preset"), *AssetType));
	}

	FString Error;
	if (!BuilderManager.CreateBuilder(AssetType, Name, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Created %s builder '%s'"), *AssetType, *Name));
	Response->SetStringField(TEXT("asset_type"), AssetType);
	Response->SetStringField(TEXT("name"), Name);
	return Response;
}

// ---------------------------------------------------------------------------
// add_interface
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FAddInterfaceCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString InterfaceName;
	if (!Params->TryGetStringField(TEXT("interface"), InterfaceName))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'interface'"));
	}

	FString Error;
	if (!BuilderManager.AddInterface(InterfaceName, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	return AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Added interface '%s'"), *InterfaceName));
}

// ---------------------------------------------------------------------------
// add_graph_input
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FAddGraphInputCommand::Execute(
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
	if (!BuilderManager.AddGraphInput(Name, Type, DefaultValue, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Added graph input '%s' (%s)"), *Name, *Type));
	Response->SetStringField(TEXT("name"), Name);
	Response->SetStringField(TEXT("type"), Type);
	return Response;
}

// ---------------------------------------------------------------------------
// add_graph_output
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FAddGraphOutputCommand::Execute(
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

	FString Error;
	if (!BuilderManager.AddGraphOutput(Name, Type, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Added graph output '%s' (%s)"), *Name, *Type));
	Response->SetStringField(TEXT("name"), Name);
	Response->SetStringField(TEXT("type"), Type);
	return Response;
}

// ---------------------------------------------------------------------------
// build_to_asset
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FBuildToAssetCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString Name;
	if (!Params->TryGetStringField(TEXT("name"), Name))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'name'"));
	}

	FString Path;
	if (!Params->TryGetStringField(TEXT("path"), Path))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'path'"));
	}

	// Validate path
	if (!Path.StartsWith(TEXT("/Game/")))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Path must start with /Game/ (got '%s')"), *Path));
	}

	if (Path.Contains(TEXT("..")))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Path must not contain '..'"));
	}

	FString Error;
	if (!BuilderManager.BuildToAsset(Name, Path, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Built asset '%s' at '%s'"), *Name, *Path));
	Response->SetStringField(TEXT("name"), Name);
	Response->SetStringField(TEXT("path"), Path);
	return Response;
}

// ---------------------------------------------------------------------------
// audition
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FAuditionCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString Error;
	if (!BuilderManager.Audition(Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	FString Name;
	Params->TryGetStringField(TEXT("name"), Name);

	return AudioMCP::MakeOkResponse(
		Name.IsEmpty() ? TEXT("Auditioning current graph") :
		FString::Printf(TEXT("Auditioning '%s'"), *Name));
}

// ---------------------------------------------------------------------------
// stop_audition
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FStopAuditionCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	BuilderManager.StopAudition();
	return AudioMCP::MakeOkResponse(TEXT("Audition stopped"));
}
