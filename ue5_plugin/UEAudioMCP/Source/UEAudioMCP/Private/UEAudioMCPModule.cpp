// Copyright UE Audio MCP Project. All Rights Reserved.

#include "UEAudioMCPModule.h"
#include "AudioMCPTcpServer.h"
#include "AudioMCPCommandDispatcher.h"
#include "AudioMCPBuilderManager.h"
#include "AudioMCPTypes.h"
#include "Commands/PingCommand.h"
#include "Commands/BuilderCommands.h"
#include "Commands/NodeCommands.h"
#include "Commands/BlueprintCommands.h"
#include "Commands/VariableCommands.h"
#include "Commands/PresetCommands.h"
#include "Commands/QueryCommands.h"
#include "AudioMCPEditorMenu.h"
#include "Modules/ModuleManager.h"

DEFINE_LOG_CATEGORY_STATIC(LogAudioMCPModule, Log, All);

void FUEAudioMCPModule::StartupModule()
{
	UE_LOG(LogAudioMCPModule, Log, TEXT("UE Audio MCP plugin starting up..."));

	// Create subsystems in dependency order
	BuilderManager = MakeUnique<FAudioMCPBuilderManager>();
	Dispatcher = MakeUnique<FAudioMCPCommandDispatcher>(BuilderManager.Get());

	RegisterCommands();

	TcpServer = MakeUnique<FAudioMCPTcpServer>(Dispatcher.Get());
	if (TcpServer->StartListening(AudioMCP::DEFAULT_PORT))
	{
		UE_LOG(LogAudioMCPModule, Log,
			TEXT("UE Audio MCP ready — listening on port %d (25 commands registered)"),
			AudioMCP::DEFAULT_PORT);
	}
	else
	{
		UE_LOG(LogAudioMCPModule, Error,
			TEXT("Failed to start Audio MCP TCP server on port %d"),
			AudioMCP::DEFAULT_PORT);
	}

	// Register editor menu (deferred until ToolMenus is ready)
	FAudioMCPEditorMenu::Register();
}

void FUEAudioMCPModule::ShutdownModule()
{
	UE_LOG(LogAudioMCPModule, Log, TEXT("UE Audio MCP plugin shutting down..."));

	FAudioMCPEditorMenu::Unregister();

	// Signal dispatcher first so in-flight commands return immediately
	// instead of posting AsyncTasks that can never run (deadlock prevention)
	if (Dispatcher)
	{
		Dispatcher->SignalShutdown();
	}

	if (TcpServer)
	{
		TcpServer->StopListening();
		TcpServer.Reset();
	}

	Dispatcher.Reset();
	BuilderManager.Reset();

	UE_LOG(LogAudioMCPModule, Log, TEXT("UE Audio MCP plugin shut down"));
}

void FUEAudioMCPModule::RegisterCommands()
{
	// 1. Ping
	Dispatcher->RegisterCommand(TEXT("ping"),
		MakeShared<FPingCommand>());

	// 2-3. Builder lifecycle
	Dispatcher->RegisterCommand(TEXT("create_builder"),
		MakeShared<FCreateBuilderCommand>());
	Dispatcher->RegisterCommand(TEXT("add_interface"),
		MakeShared<FAddInterfaceCommand>());

	// 4-5. Graph I/O
	Dispatcher->RegisterCommand(TEXT("add_graph_input"),
		MakeShared<FAddGraphInputCommand>());
	Dispatcher->RegisterCommand(TEXT("add_graph_output"),
		MakeShared<FAddGraphOutputCommand>());

	// 6-8. Node operations
	Dispatcher->RegisterCommand(TEXT("add_node"),
		MakeShared<FAddNodeCommand>());
	Dispatcher->RegisterCommand(TEXT("set_default"),
		MakeShared<FSetDefaultCommand>());
	Dispatcher->RegisterCommand(TEXT("connect"),
		MakeShared<FConnectCommand>());

	// 9-12. Build, audition & editor
	Dispatcher->RegisterCommand(TEXT("build_to_asset"),
		MakeShared<FBuildToAssetCommand>());
	Dispatcher->RegisterCommand(TEXT("audition"),
		MakeShared<FAuditionCommand>());
	Dispatcher->RegisterCommand(TEXT("stop_audition"),
		MakeShared<FStopAuditionCommand>());
	Dispatcher->RegisterCommand(TEXT("open_in_editor"),
		MakeShared<FOpenInEditorCommand>());

	// 13. Blueprint reflection
	Dispatcher->RegisterCommand(TEXT("call_function"),
		MakeShared<FCallFunctionCommand>());

	// 14-16. Graph variables (UE 5.7)
	Dispatcher->RegisterCommand(TEXT("add_graph_variable"),
		MakeShared<FAddGraphVariableCommand>());
	Dispatcher->RegisterCommand(TEXT("add_variable_get_node"),
		MakeShared<FAddVariableGetNodeCommand>());
	Dispatcher->RegisterCommand(TEXT("add_variable_set_node"),
		MakeShared<FAddVariableSetNodeCommand>());

	// 17-18. Preset conversion
	Dispatcher->RegisterCommand(TEXT("convert_to_preset"),
		MakeShared<FConvertToPresetCommand>());
	Dispatcher->RegisterCommand(TEXT("convert_from_preset"),
		MakeShared<FConvertFromPresetCommand>());

	// 19-22. Query & live updates
	Dispatcher->RegisterCommand(TEXT("get_graph_input_names"),
		MakeShared<FGetGraphInputNamesCommand>());
	Dispatcher->RegisterCommand(TEXT("set_live_updates"),
		MakeShared<FSetLiveUpdatesCommand>());
	Dispatcher->RegisterCommand(TEXT("list_node_classes"),
		MakeShared<FListNodeClassesCommand>());
	Dispatcher->RegisterCommand(TEXT("get_node_locations"),
		MakeShared<FGetNodeLocationsCommand>());

	// 23-24. Blueprint graph inspection & asset queries
	Dispatcher->RegisterCommand(TEXT("scan_blueprint"),
		MakeShared<FScanBlueprintCommand>());
	Dispatcher->RegisterCommand(TEXT("list_assets"),
		MakeShared<FListAssetsCommand>());

	// 25. Full MetaSound graph export
	Dispatcher->RegisterCommand(TEXT("export_metasound"),
		MakeShared<FExportMetaSoundCommand>());

	// 26. Focused audio Blueprint export with edges
	Dispatcher->RegisterCommand(TEXT("export_audio_blueprint"),
		MakeShared<FExportAudioBlueprintCommand>());
}

IMPLEMENT_MODULE(FUEAudioMCPModule, UEAudioMCP)
