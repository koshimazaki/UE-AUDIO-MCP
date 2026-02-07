// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "Commands/IAudioMCPCommand.h"

/** convert_to_preset: Convert the current builder graph to a preset of a referenced asset. */
class FConvertToPresetCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** convert_from_preset: Revert a preset back to a full editable graph. */
class FConvertFromPresetCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};
