// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/PingCommand.h"
#include "AudioMCPTypes.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Misc/App.h"
#include "Misc/EngineVersion.h"
#include "Interfaces/IPluginManager.h"

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

	// Detect available features by checking loaded plugins
	TArray<TSharedPtr<FJsonValue>> Features;

	IPluginManager& PluginManager = IPluginManager::Get();

	if (PluginManager.FindEnabledPlugin(TEXT("Metasound")))
	{
		Features.Add(MakeShared<FJsonValueString>(TEXT("MetaSounds")));
	}

	if (PluginManager.FindEnabledPlugin(TEXT("WwiseAudioLink")))
	{
		Features.Add(MakeShared<FJsonValueString>(TEXT("AudioLink")));
	}

	if (PluginManager.FindEnabledPlugin(TEXT("Wwise")))
	{
		Features.Add(MakeShared<FJsonValueString>(TEXT("Wwise")));
	}

	if (PluginManager.FindEnabledPlugin(TEXT("Quartz")))
	{
		Features.Add(MakeShared<FJsonValueString>(TEXT("Quartz")));
	}

	Response->SetArrayField(TEXT("features"), Features);

	return Response;
}
