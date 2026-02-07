// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "Commands/IAudioMCPCommand.h"

/**
 * call_function: Execute a Blueprint/UObject function via reflection.
 * Finds the function by name, fills parameters from JSON, calls ProcessEvent.
 */
class FCallFunctionCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};
