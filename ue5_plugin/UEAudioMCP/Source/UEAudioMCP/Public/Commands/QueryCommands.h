// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "Commands/IAudioMCPCommand.h"

/** get_graph_input_names: List all graph-level input names for introspection. */
class FGetGraphInputNamesCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** set_live_updates: Enable or disable real-time topology changes while auditioning. */
class FSetLiveUpdatesCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};
