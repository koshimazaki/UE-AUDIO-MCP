// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonObject.h"

class FAudioMCPBuilderManager;

/**
 * Abstract interface for all MCP commands.
 * Each command receives the JSON params and the shared BuilderManager,
 * and returns a JSON response (executed on the game thread).
 */
class IAudioMCPCommand
{
public:
	virtual ~IAudioMCPCommand() = default;

	/**
	 * Execute the command on the game thread.
	 * @param Params - JSON params from the incoming command (excludes "action")
	 * @param BuilderManager - Shared MetaSounds builder state
	 * @return JSON response object with "status" field
	 */
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) = 0;
};
