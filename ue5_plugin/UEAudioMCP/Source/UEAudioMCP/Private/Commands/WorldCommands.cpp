// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/WorldCommands.h"
#include "AudioMCPTypes.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Editor.h"
#include "Engine/World.h"

// AnimNotify
#include "Animation/AnimSequenceBase.h"
#include "Animation/AnimNotifies/AnimNotify.h"
#include "Animation/AnimNotifies/AnimNotify_PlaySound.h"
#include "Sound/SoundBase.h"

// Audio emitter
#include "Sound/AmbientSound.h"
#include "Components/AudioComponent.h"
#include "Kismet/GameplayStatics.h"

// Import
#include "AssetToolsModule.h"
#include "IAssetTools.h"
#include "AutomatedAssetImportData.h"

// Physical materials
#include "PhysicalMaterials/PhysicalMaterial.h"

// Audio volumes
#include "Sound/AudioVolume.h"
#include "Sound/ReverbEffect.h"
#include "Builders/CubeBuilder.h"

// Asset loading & registry
#include "UObject/SoftObjectPath.h"
#include "EditorAssetLibrary.h"
#include "AssetRegistry/AssetRegistryModule.h"

// Blueprint spawning
#include "Engine/Blueprint.h"

DEFINE_LOG_CATEGORY_STATIC(LogWorldCmds, Log, All);

// ==========================================================================
// place_anim_notify
// ==========================================================================

TSharedPtr<FJsonObject> FPlaceAnimNotifyCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	FString AnimPath;
	if (!Params->TryGetStringField(TEXT("animation_path"), AnimPath))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'animation_path'"));
	}

	double Time = 0.0;
	if (!Params->TryGetNumberField(TEXT("time"), Time))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'time'"));
	}

	FString SoundPath;
	Params->TryGetStringField(TEXT("sound"), SoundPath);

	FString NotifyName;
	if (!Params->TryGetStringField(TEXT("notify_name"), NotifyName))
	{
		NotifyName = TEXT("Footstep");
	}

	// Validate paths
	if (!AnimPath.StartsWith(TEXT("/Game/")) && !AnimPath.StartsWith(TEXT("/Engine/")))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("animation_path must start with /Game/ or /Engine/ (got '%s')"), *AnimPath));
	}
	if (AnimPath.Contains(TEXT("..")))
	{
		return AudioMCP::MakeErrorResponse(TEXT("animation_path must not contain '..'"));
	}
	if (!SoundPath.IsEmpty() && SoundPath.Contains(TEXT("..")))
	{
		return AudioMCP::MakeErrorResponse(TEXT("sound path must not contain '..'"));
	}

	// Load the animation asset
	UAnimSequenceBase* AnimSeq = LoadObject<UAnimSequenceBase>(
		nullptr, *AnimPath);
	if (!AnimSeq)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Could not load AnimSequence at '%s'"), *AnimPath));
	}

	// Validate time is within animation length
	float AnimLength = AnimSeq->GetPlayLength();
	if (Time < 0.0 || Time > AnimLength)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Time %.3f is out of range [0, %.3f] for '%s'"),
				Time, AnimLength, *AnimPath));
	}

	// Load the sound asset if specified
	USoundBase* Sound = nullptr;
	if (!SoundPath.IsEmpty())
	{
		Sound = LoadObject<USoundBase>(nullptr, *SoundPath);
		if (!Sound)
		{
			return AudioMCP::MakeErrorResponse(
				FString::Printf(TEXT("Could not load SoundBase at '%s'"), *SoundPath));
		}
	}

	// Create the AnimNotify
	UAnimNotify_PlaySound* Notify = NewObject<UAnimNotify_PlaySound>(
		AnimSeq, UAnimNotify_PlaySound::StaticClass());
	if (!Notify)
	{
		return AudioMCP::MakeErrorResponse(TEXT("Failed to create AnimNotify_PlaySound"));
	}

	// Set the sound on the notify
	if (Sound)
	{
		Notify->Sound = Sound;
	}

	// Add the notify event to the animation
	FAnimNotifyEvent& NewEvent = AnimSeq->Notifies.AddDefaulted_GetRef();
	NewEvent.NotifyName = FName(*NotifyName);
	NewEvent.Notify = Notify;
	NewEvent.SetTime(static_cast<float>(Time));
	NewEvent.TriggerTimeOffset = GetTriggerTimeOffsetForType(EAnimEventTriggerOffsets::OffsetBefore);

	// Link the notify to the animation
	NewEvent.Link(AnimSeq, static_cast<float>(Time));

	// Mark the animation as modified
	AnimSeq->Modify();
	AnimSeq->PostEditChange();
	AnimSeq->RefreshCacheData();

	UE_LOG(LogWorldCmds, Log, TEXT("Placed AnimNotify '%s' at %.3fs on '%s'"),
		*NotifyName, Time, *AnimPath);

	TSharedPtr<FJsonObject> Resp = AudioMCP::MakeOkResponse();
	Resp->SetStringField(TEXT("animation"), AnimPath);
	Resp->SetStringField(TEXT("notify_name"), NotifyName);
	Resp->SetNumberField(TEXT("time"), Time);
	Resp->SetNumberField(TEXT("animation_length"), AnimLength);
	if (Sound)
	{
		Resp->SetStringField(TEXT("sound"), SoundPath);
	}
	return Resp;
}

// ==========================================================================
// place_bp_anim_notify
// ==========================================================================

TSharedPtr<FJsonObject> FPlaceBPAnimNotifyCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	FString AnimPath;
	if (!Params->TryGetStringField(TEXT("animation_path"), AnimPath))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'animation_path'"));
	}

	double Time = 0.0;
	if (!Params->TryGetNumberField(TEXT("time"), Time))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'time'"));
	}

	FString NotifyBPPath;
	if (!Params->TryGetStringField(TEXT("notify_blueprint_path"), NotifyBPPath))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'notify_blueprint_path'"));
	}

	FString NotifyName;
	if (!Params->TryGetStringField(TEXT("notify_name"), NotifyName))
	{
		NotifyName = TEXT("BPNotify");
	}

	// Validate animation path
	if (!AnimPath.StartsWith(TEXT("/Game/")) && !AnimPath.StartsWith(TEXT("/Engine/")))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("animation_path must start with /Game/ or /Engine/ (got '%s')"), *AnimPath));
	}
	if (AnimPath.Contains(TEXT("..")))
	{
		return AudioMCP::MakeErrorResponse(TEXT("animation_path must not contain '..'"));
	}

	// Validate notify blueprint path
	if (!NotifyBPPath.StartsWith(TEXT("/Game/")) && !NotifyBPPath.StartsWith(TEXT("/Engine/")))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("notify_blueprint_path must start with /Game/ or /Engine/ (got '%s')"), *NotifyBPPath));
	}
	if (NotifyBPPath.Contains(TEXT("..")))
	{
		return AudioMCP::MakeErrorResponse(TEXT("notify_blueprint_path must not contain '..'"));
	}

	// Load the animation asset
	UAnimSequenceBase* AnimSeq = LoadObject<UAnimSequenceBase>(nullptr, *AnimPath);
	if (!AnimSeq)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Could not load AnimSequence at '%s'"), *AnimPath));
	}

	// Validate time is within animation length
	float AnimLength = AnimSeq->GetPlayLength();
	if (Time < 0.0 || Time > AnimLength)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Time %.3f is out of range [0, %.3f] for '%s'"),
				Time, AnimLength, *AnimPath));
	}

	// Load the Blueprint asset
	UBlueprint* Blueprint = LoadObject<UBlueprint>(nullptr, *NotifyBPPath);
	if (!Blueprint)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Could not load Blueprint at '%s'"), *NotifyBPPath));
	}

	// Validate the Blueprint is an AnimNotify subclass
	UClass* NotifyClass = Blueprint->GeneratedClass;
	if (!NotifyClass)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Blueprint '%s' has no GeneratedClass — is it compiled?"), *NotifyBPPath));
	}
	if (!NotifyClass->IsChildOf(UAnimNotify::StaticClass()))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Blueprint '%s' is not an AnimNotify subclass (class: %s)"),
				*NotifyBPPath, *NotifyClass->GetName()));
	}

	// Create the notify instance
	UAnimNotify* Notify = NewObject<UAnimNotify>(AnimSeq, NotifyClass);
	if (!Notify)
	{
		return AudioMCP::MakeErrorResponse(TEXT("Failed to create AnimNotify instance"));
	}

	// Add the notify event to the animation
	FAnimNotifyEvent& NewEvent = AnimSeq->Notifies.AddDefaulted_GetRef();
	NewEvent.NotifyName = FName(*NotifyName);
	NewEvent.Notify = Notify;
	NewEvent.SetTime(static_cast<float>(Time));
	NewEvent.TriggerTimeOffset = GetTriggerTimeOffsetForType(EAnimEventTriggerOffsets::OffsetBefore);

	// Link the notify to the animation
	NewEvent.Link(AnimSeq, static_cast<float>(Time));

	// Mark the animation as modified
	AnimSeq->Modify();
	AnimSeq->PostEditChange();
	AnimSeq->RefreshCacheData();

	UE_LOG(LogWorldCmds, Log, TEXT("Placed BP AnimNotify '%s' (%s) at %.3fs on '%s'"),
		*NotifyName, *NotifyClass->GetName(), Time, *AnimPath);

	TSharedPtr<FJsonObject> Resp = AudioMCP::MakeOkResponse();
	Resp->SetStringField(TEXT("animation"), AnimPath);
	Resp->SetStringField(TEXT("notify_name"), NotifyName);
	Resp->SetStringField(TEXT("notify_blueprint"), NotifyBPPath);
	Resp->SetStringField(TEXT("notify_class"), NotifyClass->GetName());
	Resp->SetNumberField(TEXT("time"), Time);
	Resp->SetNumberField(TEXT("animation_length"), AnimLength);
	return Resp;
}

// ==========================================================================
// spawn_audio_emitter
// ==========================================================================

TSharedPtr<FJsonObject> FSpawnAudioEmitterCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	// Sound asset path
	FString SoundPath;
	if (!Params->TryGetStringField(TEXT("sound"), SoundPath))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'sound'"));
	}

	// Location [x, y, z]
	const TArray<TSharedPtr<FJsonValue>>* LocArray = nullptr;
	if (!Params->TryGetArrayField(TEXT("location"), LocArray) || LocArray->Num() < 3)
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'location' (array of [x, y, z])"));
	}
	FVector Location(
		(*LocArray)[0]->AsNumber(),
		(*LocArray)[1]->AsNumber(),
		(*LocArray)[2]->AsNumber()
	);

	// Optional params
	bool bAutoPlay = true;
	Params->TryGetBoolField(TEXT("auto_play"), bAutoPlay);

	FString EmitterName;
	if (!Params->TryGetStringField(TEXT("name"), EmitterName))
	{
		EmitterName = TEXT("MCP_AudioEmitter");
	}

	// Validate sound path
	if (!SoundPath.StartsWith(TEXT("/Game/")) && !SoundPath.StartsWith(TEXT("/Engine/")))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("sound path must start with /Game/ or /Engine/ (got '%s')"), *SoundPath));
	}
	if (SoundPath.Contains(TEXT("..")))
	{
		return AudioMCP::MakeErrorResponse(TEXT("sound path must not contain '..'"));
	}

	// Load the sound asset
	USoundBase* Sound = LoadObject<USoundBase>(nullptr, *SoundPath);
	if (!Sound)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Could not load SoundBase at '%s'"), *SoundPath));
	}

	// Get the editor world
	UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (!World)
	{
		return AudioMCP::MakeErrorResponse(TEXT("No editor world available"));
	}

	// Spawn an AmbientSound actor
	FActorSpawnParameters SpawnParams;
	SpawnParams.Name = FName(*EmitterName);
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	AAmbientSound* Emitter = World->SpawnActor<AAmbientSound>(
		AAmbientSound::StaticClass(),
		Location,
		FRotator::ZeroRotator,
		SpawnParams);

	if (!Emitter)
	{
		return AudioMCP::MakeErrorResponse(TEXT("Failed to spawn AmbientSound actor"));
	}

	// Set the sound on the audio component
	UAudioComponent* AudioComp = Emitter->GetAudioComponent();
	if (!AudioComp)
	{
		return AudioMCP::MakeErrorResponse(TEXT("AmbientSound spawned but AudioComponent is null"));
	}
	AudioComp->SetSound(Sound);
	if (bAutoPlay)
	{
		AudioComp->bAutoActivate = true;
		AudioComp->Play();
	}

	// Set a label
	Emitter->SetActorLabel(*EmitterName);

	UE_LOG(LogWorldCmds, Log, TEXT("Spawned audio emitter '%s' at (%.0f, %.0f, %.0f) with '%s'"),
		*EmitterName, Location.X, Location.Y, Location.Z, *SoundPath);

	TSharedPtr<FJsonObject> Resp = AudioMCP::MakeOkResponse();
	Resp->SetStringField(TEXT("name"), Emitter->GetActorLabel());
	Resp->SetStringField(TEXT("sound"), SoundPath);

	TArray<TSharedPtr<FJsonValue>> LocOut;
	LocOut.Add(MakeShared<FJsonValueNumber>(Location.X));
	LocOut.Add(MakeShared<FJsonValueNumber>(Location.Y));
	LocOut.Add(MakeShared<FJsonValueNumber>(Location.Z));
	Resp->SetArrayField(TEXT("location"), LocOut);
	Resp->SetBoolField(TEXT("auto_play"), bAutoPlay);
	return Resp;
}

// ==========================================================================
// import_sound_file
// ==========================================================================

TSharedPtr<FJsonObject> FImportSoundFileCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	FString FilePath;
	if (!Params->TryGetStringField(TEXT("file_path"), FilePath))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'file_path'"));
	}

	FString DestFolder;
	if (!Params->TryGetStringField(TEXT("dest_folder"), DestFolder))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'dest_folder'"));
	}

	// Validate paths — reject traversal
	if (FilePath.Contains(TEXT("..")))
	{
		return AudioMCP::MakeErrorResponse(TEXT("file_path must not contain '..'"));
	}

	// Validate file extension
	FString Extension = FPaths::GetExtension(FilePath).ToLower();
	if (Extension != TEXT("wav") && Extension != TEXT("ogg"))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Unsupported audio format '.%s'. Only .wav and .ogg are supported."), *Extension));
	}

	// Validate file exists on disk
	if (!FPaths::FileExists(FilePath))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("File not found: '%s'"), *FilePath));
	}

	// Validate destination
	if (!DestFolder.StartsWith(TEXT("/Game/")))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("dest_folder must start with /Game/ (got '%s')"), *DestFolder));
	}
	if (DestFolder.Contains(TEXT("..")))
	{
		return AudioMCP::MakeErrorResponse(TEXT("dest_folder must not contain '..'"));
	}

	// Use automated import (no modal dialog — headless for MCP)
	UAutomatedAssetImportData* ImportData = NewObject<UAutomatedAssetImportData>();
	ImportData->bReplaceExisting = true;
	ImportData->DestinationPath = DestFolder;
	ImportData->Filenames.Add(FilePath);

	IAssetTools& AssetTools = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();
	TArray<UObject*> ImportedAssets = AssetTools.ImportAssetsAutomated(ImportData);

	if (ImportedAssets.Num() == 0)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Import failed for '%s' to '%s'"), *FilePath, *DestFolder));
	}

	UObject* ImportedAsset = ImportedAssets[0];
	FString AssetPath = ImportedAsset->GetPathName();
	FString AssetName = ImportedAsset->GetName();

	UE_LOG(LogWorldCmds, Log, TEXT("Imported '%s' -> '%s'"), *FilePath, *AssetPath);

	TSharedPtr<FJsonObject> Resp = AudioMCP::MakeOkResponse();
	Resp->SetStringField(TEXT("asset_path"), AssetPath);
	Resp->SetStringField(TEXT("asset_name"), AssetName);
	Resp->SetStringField(TEXT("source_file"), FilePath);
	Resp->SetStringField(TEXT("format"), Extension);
	return Resp;
}

// ==========================================================================
// set_physical_surface
// ==========================================================================

TSharedPtr<FJsonObject> FSetPhysicalSurfaceCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	FString MaterialPath;
	if (!Params->TryGetStringField(TEXT("material_path"), MaterialPath))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'material_path'"));
	}

	FString SurfaceType;
	if (!Params->TryGetStringField(TEXT("surface_type"), SurfaceType))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'surface_type'"));
	}

	// Validate path
	if (MaterialPath.Contains(TEXT("..")))
	{
		return AudioMCP::MakeErrorResponse(TEXT("material_path must not contain '..'"));
	}
	if (!MaterialPath.StartsWith(TEXT("/Game/")) && !MaterialPath.StartsWith(TEXT("/Engine/")))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("material_path must start with /Game/ or /Engine/ (got '%s')"), *MaterialPath));
	}

	// Load or create the Physical Material
	UPhysicalMaterial* PhysMat = LoadObject<UPhysicalMaterial>(nullptr, *MaterialPath);

	bool bCreated = false;
	if (!PhysMat)
	{
		// Try to create a new Physical Material at the specified path
		FString PackagePath = FPaths::GetPath(MaterialPath);
		FString AssetName = FPaths::GetBaseFilename(MaterialPath);

		UPackage* Package = CreatePackage(*MaterialPath);
		if (!Package)
		{
			return AudioMCP::MakeErrorResponse(
				FString::Printf(TEXT("Could not create package at '%s'"), *MaterialPath));
		}

		PhysMat = NewObject<UPhysicalMaterial>(Package, *AssetName,
			RF_Public | RF_Standalone);
		if (!PhysMat)
		{
			return AudioMCP::MakeErrorResponse(TEXT("Failed to create PhysicalMaterial"));
		}
		bCreated = true;
	}

	// Map surface type string to EPhysicalSurface enum
	// UE5 defines SurfaceType1..SurfaceType62 as custom surface types
	EPhysicalSurface Surface = SurfaceType_Default;
	bool bFound = SurfaceType.Equals(TEXT("Default"), ESearchCase::IgnoreCase)
	           || SurfaceType.Equals(TEXT("SurfaceType_Default"), ESearchCase::IgnoreCase);

	// Check project surface type names from the project settings
	UEnum* SurfaceEnum = StaticEnum<EPhysicalSurface>();
	if (SurfaceEnum && !bFound)
	{
		for (int32 i = 0; i < SurfaceEnum->NumEnums() - 1; ++i)
		{
			// Try display name first (project-configured names like "Grass")
			FString EnumName = SurfaceEnum->GetDisplayNameTextByIndex(i).ToString();
			if (EnumName.Equals(SurfaceType, ESearchCase::IgnoreCase))
			{
				Surface = static_cast<EPhysicalSurface>(SurfaceEnum->GetValueByIndex(i));
				bFound = true;
				break;
			}
			// Also check the raw enum name (e.g., "SurfaceType1")
			FString RawName = SurfaceEnum->GetNameStringByIndex(i);
			if (RawName.Equals(SurfaceType, ESearchCase::IgnoreCase))
			{
				Surface = static_cast<EPhysicalSurface>(SurfaceEnum->GetValueByIndex(i));
				bFound = true;
				break;
			}
		}
	}

	if (!bFound)
	{
		// Build list of available surface types for the error message
		FString Available;
		if (SurfaceEnum)
		{
			for (int32 i = 0; i < SurfaceEnum->NumEnums() - 1; ++i)
			{
				FString Name = SurfaceEnum->GetDisplayNameTextByIndex(i).ToString();
				if (!Name.IsEmpty() && Name != TEXT("SurfaceType_Default"))
				{
					if (!Available.IsEmpty()) Available += TEXT(", ");
					Available += Name;
				}
			}
		}
		FString Msg = FString::Printf(
			TEXT("Unknown surface type '%s'."), *SurfaceType);
		if (!Available.IsEmpty())
		{
			Msg += FString::Printf(TEXT(" Available: %s"), *Available);
		}
		else
		{
			Msg += TEXT(" Configure surface types in Project Settings > Physics > Physical Surface.");
		}
		return AudioMCP::MakeErrorResponse(Msg);
	}

	PhysMat->SurfaceType = Surface;
	PhysMat->Modify();
	PhysMat->PostEditChange();

	// Save the asset if newly created
	if (bCreated)
	{
		FAssetRegistryModule::AssetCreated(PhysMat);
		PhysMat->MarkPackageDirty();
	}

	FString SurfaceName = SurfaceEnum
		? SurfaceEnum->GetDisplayNameTextByValue(static_cast<int64>(Surface)).ToString()
		: TEXT("Default");

	UE_LOG(LogWorldCmds, Log, TEXT("Set surface type '%s' (%s) on '%s'"),
		*SurfaceType, *SurfaceName, *MaterialPath);

	TSharedPtr<FJsonObject> Resp = AudioMCP::MakeOkResponse();
	Resp->SetStringField(TEXT("material_path"), MaterialPath);
	Resp->SetStringField(TEXT("surface_type"), SurfaceType);
	Resp->SetStringField(TEXT("surface_enum"), SurfaceName);
	Resp->SetNumberField(TEXT("surface_index"), static_cast<int32>(Surface));
	Resp->SetBoolField(TEXT("created"), bCreated);
	return Resp;
}

// ==========================================================================
// place_audio_volume
// ==========================================================================

TSharedPtr<FJsonObject> FPlaceAudioVolumeCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	// Location [x, y, z]
	const TArray<TSharedPtr<FJsonValue>>* LocArray = nullptr;
	if (!Params->TryGetArrayField(TEXT("location"), LocArray) || LocArray->Num() < 3)
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'location' (array of [x, y, z])"));
	}
	FVector Location(
		(*LocArray)[0]->AsNumber(),
		(*LocArray)[1]->AsNumber(),
		(*LocArray)[2]->AsNumber()
	);

	// Extent [x, y, z] — half-size of the volume box
	const TArray<TSharedPtr<FJsonValue>>* ExtArray = nullptr;
	FVector Extent(500.0, 500.0, 500.0); // Default 10m cube
	if (Params->TryGetArrayField(TEXT("extent"), ExtArray) && ExtArray->Num() >= 3)
	{
		Extent = FVector(
			(*ExtArray)[0]->AsNumber(),
			(*ExtArray)[1]->AsNumber(),
			(*ExtArray)[2]->AsNumber()
		);
	}

	// Optional reverb effect path
	FString ReverbPath;
	Params->TryGetStringField(TEXT("reverb_effect"), ReverbPath);
	if (!ReverbPath.IsEmpty() && ReverbPath.Contains(TEXT("..")))
	{
		return AudioMCP::MakeErrorResponse(TEXT("reverb_effect path must not contain '..'"));
	}

	// Optional name
	FString VolumeName;
	if (!Params->TryGetStringField(TEXT("name"), VolumeName))
	{
		VolumeName = TEXT("MCP_AudioVolume");
	}

	// Optional priority
	double Priority = 0.0;
	Params->TryGetNumberField(TEXT("priority"), Priority);

	// Get the editor world
	UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (!World)
	{
		return AudioMCP::MakeErrorResponse(TEXT("No editor world available"));
	}

	// Spawn the AudioVolume
	FActorSpawnParameters SpawnParams;
	SpawnParams.Name = FName(*VolumeName);
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	AAudioVolume* Volume = World->SpawnActor<AAudioVolume>(
		AAudioVolume::StaticClass(),
		Location,
		FRotator::ZeroRotator,
		SpawnParams);

	if (!Volume)
	{
		return AudioMCP::MakeErrorResponse(TEXT("Failed to spawn AudioVolume actor"));
	}

	// Build brush geometry so the volume defines an actual zone
	UCubeBuilder* CubeBuilder = NewObject<UCubeBuilder>(Volume);
	CubeBuilder->X = Extent.X * 2.0f;
	CubeBuilder->Y = Extent.Y * 2.0f;
	CubeBuilder->Z = Extent.Z * 2.0f;
	CubeBuilder->Build(World, Volume);

	Volume->SetActorLabel(*VolumeName);
	Volume->SetPriority(static_cast<float>(Priority));

	// Set reverb if specified
	if (!ReverbPath.IsEmpty())
	{
		UReverbEffect* Reverb = LoadObject<UReverbEffect>(nullptr, *ReverbPath);
		if (Reverb)
		{
			FReverbSettings ReverbSettings;
			ReverbSettings.bApplyReverb = true;
			ReverbSettings.ReverbEffect = Reverb;
			ReverbSettings.Volume = 1.0f;
			ReverbSettings.FadeTime = 0.5f;
			Volume->SetReverbSettings(ReverbSettings);
		}
		else
		{
			Volume->Destroy();
			return AudioMCP::MakeErrorResponse(
				FString::Printf(TEXT("Could not load ReverbEffect at '%s'"), *ReverbPath));
		}
	}

	UE_LOG(LogWorldCmds, Log, TEXT("Placed AudioVolume '%s' at (%.0f, %.0f, %.0f) extent (%.0f, %.0f, %.0f)"),
		*VolumeName, Location.X, Location.Y, Location.Z,
		Extent.X, Extent.Y, Extent.Z);

	TSharedPtr<FJsonObject> Resp = AudioMCP::MakeOkResponse();
	Resp->SetStringField(TEXT("name"), VolumeName);

	TArray<TSharedPtr<FJsonValue>> LocOut;
	LocOut.Add(MakeShared<FJsonValueNumber>(Location.X));
	LocOut.Add(MakeShared<FJsonValueNumber>(Location.Y));
	LocOut.Add(MakeShared<FJsonValueNumber>(Location.Z));
	Resp->SetArrayField(TEXT("location"), LocOut);

	TArray<TSharedPtr<FJsonValue>> ExtOut;
	ExtOut.Add(MakeShared<FJsonValueNumber>(Extent.X));
	ExtOut.Add(MakeShared<FJsonValueNumber>(Extent.Y));
	ExtOut.Add(MakeShared<FJsonValueNumber>(Extent.Z));
	Resp->SetArrayField(TEXT("extent"), ExtOut);

	Resp->SetNumberField(TEXT("priority"), Priority);
	if (!ReverbPath.IsEmpty())
	{
		Resp->SetStringField(TEXT("reverb_effect"), ReverbPath);
	}
	return Resp;
}

// ==========================================================================
// spawn_blueprint_actor
// ==========================================================================

TSharedPtr<FJsonObject> FSpawnBlueprintActorCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	FString BlueprintPath;
	if (!Params->TryGetStringField(TEXT("blueprint_path"), BlueprintPath))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'blueprint_path'"));
	}

	// Validate path
	if (!BlueprintPath.StartsWith(TEXT("/Game/")) && !BlueprintPath.StartsWith(TEXT("/Engine/")))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("blueprint_path must start with /Game/ or /Engine/ (got '%s')"), *BlueprintPath));
	}
	if (BlueprintPath.Contains(TEXT("..")))
	{
		return AudioMCP::MakeErrorResponse(TEXT("blueprint_path must not contain '..'"));
	}

	// Location (optional, defaults to origin)
	FVector Location = FVector::ZeroVector;
	const TArray<TSharedPtr<FJsonValue>>* LocArray = nullptr;
	if (Params->TryGetArrayField(TEXT("location"), LocArray) && LocArray->Num() >= 3)
	{
		Location = FVector(
			(*LocArray)[0]->AsNumber(),
			(*LocArray)[1]->AsNumber(),
			(*LocArray)[2]->AsNumber()
		);
	}

	// Rotation (optional, defaults to zero)
	FRotator Rotation = FRotator::ZeroRotator;
	const TArray<TSharedPtr<FJsonValue>>* RotArray = nullptr;
	if (Params->TryGetArrayField(TEXT("rotation"), RotArray) && RotArray->Num() >= 3)
	{
		Rotation = FRotator(
			(*RotArray)[0]->AsNumber(),  // Pitch
			(*RotArray)[1]->AsNumber(),  // Yaw
			(*RotArray)[2]->AsNumber()   // Roll
		);
	}

	// Optional label
	FString ActorLabel;
	Params->TryGetStringField(TEXT("label"), ActorLabel);

	// Load the Blueprint asset
	UBlueprint* Blueprint = LoadObject<UBlueprint>(nullptr, *BlueprintPath);
	if (!Blueprint)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Could not load Blueprint at '%s'"), *BlueprintPath));
	}

	// Get the generated class (the spawnable class)
	UClass* SpawnClass = Blueprint->GeneratedClass;
	if (!SpawnClass)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Blueprint '%s' has no GeneratedClass — is it compiled?"), *BlueprintPath));
	}

	// Must be an Actor subclass
	if (!SpawnClass->IsChildOf(AActor::StaticClass()))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Blueprint '%s' is not an Actor subclass (class: %s)"),
				*BlueprintPath, *SpawnClass->GetName()));
	}

	// Get the editor world
	UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (!World)
	{
		return AudioMCP::MakeErrorResponse(TEXT("No editor world available"));
	}

	// Spawn the actor
	FTransform SpawnTransform(Rotation, Location);
	FActorSpawnParameters SpawnParams;
	SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	AActor* SpawnedActor = World->SpawnActor(SpawnClass, &SpawnTransform, SpawnParams);

	if (!SpawnedActor)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Failed to spawn actor from '%s'"), *BlueprintPath));
	}

	// Set label if provided
	if (!ActorLabel.IsEmpty())
	{
		SpawnedActor->SetActorLabel(*ActorLabel);
	}

	FString FinalLabel = SpawnedActor->GetActorLabel();
	FString ClassName = SpawnClass->GetName();

	UE_LOG(LogWorldCmds, Log, TEXT("Spawned actor at (%.0f, %.0f, %.0f) from blueprint"),
		Location.X, Location.Y, Location.Z);

	TSharedPtr<FJsonObject> Resp = AudioMCP::MakeOkResponse();
	Resp->SetStringField(TEXT("actor_label"), FinalLabel);
	Resp->SetStringField(TEXT("actor_class"), ClassName);
	Resp->SetStringField(TEXT("blueprint"), BlueprintPath);

	TArray<TSharedPtr<FJsonValue>> LocOut;
	LocOut.Add(MakeShared<FJsonValueNumber>(Location.X));
	LocOut.Add(MakeShared<FJsonValueNumber>(Location.Y));
	LocOut.Add(MakeShared<FJsonValueNumber>(Location.Z));
	Resp->SetArrayField(TEXT("location"), LocOut);

	TArray<TSharedPtr<FJsonValue>> RotOut;
	RotOut.Add(MakeShared<FJsonValueNumber>(Rotation.Pitch));
	RotOut.Add(MakeShared<FJsonValueNumber>(Rotation.Yaw));
	RotOut.Add(MakeShared<FJsonValueNumber>(Rotation.Roll));
	Resp->SetArrayField(TEXT("rotation"), RotOut);

	return Resp;
}
