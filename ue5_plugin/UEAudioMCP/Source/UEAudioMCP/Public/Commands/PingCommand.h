// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "Commands/IAudioMCPCommand.h"

/**
 * Responds to "ping" with engine info.
 * Returns: engine, version, project name, detected features.
 * Must match MockUE5Plugin ping response in conftest.py.
 */
class FPingCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};
