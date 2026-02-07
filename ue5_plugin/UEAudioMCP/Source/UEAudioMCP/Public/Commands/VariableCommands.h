// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "Commands/IAudioMCPCommand.h"

/** add_graph_variable: Create a named variable in the MetaSounds graph. */
class FAddGraphVariableCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** add_variable_get_node: Add a Get Variable node to read a graph variable. */
class FAddVariableGetNodeCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** add_variable_set_node: Add a Set Variable node to write a graph variable. */
class FAddVariableSetNodeCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};
