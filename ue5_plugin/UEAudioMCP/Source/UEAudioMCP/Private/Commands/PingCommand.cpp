// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/PingCommand.h"
#include "AudioMCPTypes.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Misc/App.h"
#include "Misc/EngineVersion.h"
#include "Modules/ModuleManager.h"

TSharedPtr<FJsonObject> FPingCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse();

	// Engine info
	Response->SetStringField(TEXT("engine"), TEXT("UnrealEngine"));

	// Version string (e.g. "5.4.0")
	const FEngineVersion& Version = FEngineVersion::Current();
	FString VersionStr = FString::Printf(TEXT("%d.%d.%d"),
		Version.GetMajor(), Version.GetMinor(), Version.GetPatch());
	Response->SetStringField(TEXT("version"), VersionStr);

	// Project name
	Response->SetStringField(TEXT("project"), FApp::GetProjectName());

	// Detect available features by checking loaded modules.
	// Use FModuleManager::IsModuleLoaded — more reliable than IPluginManager
	// for engine subsystems (Quartz is part of Engine, not a standalone plugin).
	TArray<TSharedPtr<FJsonValue>> Features;

	if (FModuleManager::Get().IsModuleLoaded(TEXT("MetasoundEngine")))
	{
		Features.Add(MakeShared<FJsonValueString>(TEXT("MetaSounds")));
	}

	if (FModuleManager::Get().IsModuleLoaded(TEXT("AudioMixer")))
	{
		Features.Add(MakeShared<FJsonValueString>(TEXT("AudioMixer")));
	}

	// Quartz is part of the Engine module, check for its subsystem availability
	Features.Add(MakeShared<FJsonValueString>(TEXT("Quartz")));

	// Wwise and AudioLink are optional third-party plugins
	if (FModuleManager::Get().IsModuleLoaded(TEXT("Wwise")))
	{
		Features.Add(MakeShared<FJsonValueString>(TEXT("Wwise")));
	}

	if (FModuleManager::Get().IsModuleLoaded(TEXT("WwiseAudioLink")))
	{
		Features.Add(MakeShared<FJsonValueString>(TEXT("AudioLink")));
	}

	Response->SetArrayField(TEXT("features"), Features);

	return Response;
}
