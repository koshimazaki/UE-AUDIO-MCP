// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class FAudioMCPTcpServer;
class FAudioMCPCommandDispatcher;
class FAudioMCPBuilderManager;
class FAudioMCPBlueprintManager;

/**
 * Editor module that starts the Audio MCP TCP server on load.
 * Creates the builder manager, registers all 33 commands,
 * and starts listening on port 9877.
 */
class FUEAudioMCPModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

	static FUEAudioMCPModule& Get()
	{
		return FModuleManager::LoadModuleChecked<FUEAudioMCPModule>("UEAudioMCP");
	}

private:
	/** Register all command handlers with the dispatcher. */
	void RegisterCommands();

	TUniquePtr<FAudioMCPBuilderManager> BuilderManager;
	TUniquePtr<FAudioMCPBlueprintManager> BlueprintManager;
	TUniquePtr<FAudioMCPCommandDispatcher> Dispatcher;
	TUniquePtr<FAudioMCPTcpServer> TcpServer;
};
