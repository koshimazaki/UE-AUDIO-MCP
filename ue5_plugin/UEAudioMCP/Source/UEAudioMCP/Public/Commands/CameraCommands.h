// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "Commands/IAudioMCPCommand.h"

/** find_actor: Find actors in the current editor or PIE world by label/name/path/class. */
class FFindActorCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** set_actor_transform: Move and/or rotate an actor in the current editor or PIE world. */
class FSetActorTransformCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** focus_editor_camera: Move editor viewport camera(s) to frame an actor. */
class FFocusEditorCameraCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** set_view_target: Set the runtime player controller view target to an actor. */
class FSetViewTargetCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** possess_pawn: Possess a Pawn/Character with a player controller. */
class FPossessPawnCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};
