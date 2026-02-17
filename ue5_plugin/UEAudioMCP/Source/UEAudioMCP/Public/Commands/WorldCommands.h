// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "Commands/IAudioMCPCommand.h"

/** place_anim_notify: Add an AnimNotify_PlaySound at a specific time on an AnimSequence. */
class FPlaceAnimNotifyCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** spawn_audio_emitter: Spawn a persistent AmbientSound actor at a world location. */
class FSpawnAudioEmitterCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** import_sound_file: Import a .wav/.ogg file from disk into the Content folder. */
class FImportSoundFileCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** set_physical_surface: Set the surface type on a Physical Material asset. */
class FSetPhysicalSurfaceCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** place_audio_volume: Spawn an AudioVolume actor at a location with optional reverb. */
class FPlaceAudioVolumeCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** place_bp_anim_notify: Place a Blueprint-based AnimNotify on an animation (e.g. surface-detecting footsteps). */
class FPlaceBPAnimNotifyCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** spawn_blueprint_actor: Spawn an instance of a Blueprint class into the editor level. */
class FSpawnBlueprintActorCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};
