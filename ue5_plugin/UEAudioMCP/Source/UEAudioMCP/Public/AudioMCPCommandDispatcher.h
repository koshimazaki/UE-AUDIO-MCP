// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "HAL/ThreadSafeBool.h"
#include "Dom/JsonObject.h"

class IAudioMCPCommand;
class FAudioMCPBuilderManager;

/**
 * Routes incoming JSON commands to registered handlers.
 * Dispatches execution to the game thread via AsyncTask + FEvent,
 * ensuring all UE API calls happen on the correct thread.
 */
class FAudioMCPCommandDispatcher
{
public:
	FAudioMCPCommandDispatcher(FAudioMCPBuilderManager* InBuilderManager);
	~FAudioMCPCommandDispatcher();

	/** Register a command handler for the given action name. */
	void RegisterCommand(const FString& Action, TSharedPtr<IAudioMCPCommand> Handler);

	/**
	 * Parse and dispatch a JSON command string.
	 * Blocks calling thread until game thread execution completes.
	 * Returns JSON response string.
	 */
	FString Dispatch(const FString& JsonString);

	/**
	 * Signal that the module is shutting down.
	 * Causes Dispatch() to return errors immediately without posting AsyncTasks.
	 */
	void SignalShutdown();

private:
	TMap<FString, TSharedPtr<IAudioMCPCommand>> CommandMap;
	FAudioMCPBuilderManager* BuilderManager;
	FThreadSafeBool bShuttingDown;
};
