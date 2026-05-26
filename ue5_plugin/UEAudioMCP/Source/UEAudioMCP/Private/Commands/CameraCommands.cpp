// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/CameraCommands.h"
#include "AudioMCPTypes.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Editor.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

DEFINE_LOG_CATEGORY_STATIC(LogCameraCmds, Log, All);

namespace
{
	UWorld* GetEditorWorld()
	{
		return GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	}

	UWorld* GetPIEWorld()
	{
		if (!GEditor)
		{
			return nullptr;
		}

		for (const FWorldContext& Context : GEditor->GetWorldContexts())
		{
			if (Context.WorldType == EWorldType::PIE && Context.World())
			{
				return Context.World();
			}
		}

		return nullptr;
	}

	UWorld* GetActiveWorld()
	{
		if (UWorld* PIEWorld = GetPIEWorld())
		{
			return PIEWorld;
		}
		return GetEditorWorld();
	}

	bool ReadNumberElement(const TArray<TSharedPtr<FJsonValue>>& Values, int32 Index, const TCHAR* FieldName, double& OutValue, FString& OutError)
	{
		if (!Values.IsValidIndex(Index) || !Values[Index].IsValid() || Values[Index]->Type != EJson::Number)
		{
			OutError = FString::Printf(TEXT("%s values must be finite numbers"), FieldName);
			return false;
		}

		OutValue = Values[Index]->AsNumber();
		if (!FMath::IsFinite(OutValue))
		{
			OutError = FString::Printf(TEXT("%s values must be finite numbers"), FieldName);
			return false;
		}

		return true;
	}

	bool ReadVectorArray(const TSharedPtr<FJsonObject>& Params, const TCHAR* FieldName, FVector& OutVector, FString& OutError)
	{
		const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
		if (!Params->TryGetArrayField(FieldName, Values))
		{
			return false;
		}
		if (!Values || Values->Num() < 3)
		{
			OutError = FString::Printf(TEXT("%s must be [x, y, z]"), FieldName);
			return false;
		}

		double X = 0.0;
		double Y = 0.0;
		double Z = 0.0;
		if (!ReadNumberElement(*Values, 0, FieldName, X, OutError)
			|| !ReadNumberElement(*Values, 1, FieldName, Y, OutError)
			|| !ReadNumberElement(*Values, 2, FieldName, Z, OutError))
		{
			return false;
		}

		OutVector = FVector(
			X,
			Y,
			Z);
		return true;
	}

	bool ReadRotatorArray(const TSharedPtr<FJsonObject>& Params, const TCHAR* FieldName, FRotator& OutRotator, FString& OutError)
	{
		const TArray<TSharedPtr<FJsonValue>>* Values = nullptr;
		if (!Params->TryGetArrayField(FieldName, Values))
		{
			return false;
		}
		if (!Values || Values->Num() < 3)
		{
			OutError = FString::Printf(TEXT("%s must be [pitch, yaw, roll]"), FieldName);
			return false;
		}

		double Pitch = 0.0;
		double Yaw = 0.0;
		double Roll = 0.0;
		if (!ReadNumberElement(*Values, 0, FieldName, Pitch, OutError)
			|| !ReadNumberElement(*Values, 1, FieldName, Yaw, OutError)
			|| !ReadNumberElement(*Values, 2, FieldName, Roll, OutError))
		{
			return false;
		}

		OutRotator = FRotator(
			Pitch,
			Yaw,
			Roll);
		return true;
	}

	TArray<TSharedPtr<FJsonValue>> VectorToJson(const FVector& Vector)
	{
		TArray<TSharedPtr<FJsonValue>> Values;
		Values.Add(MakeShared<FJsonValueNumber>(Vector.X));
		Values.Add(MakeShared<FJsonValueNumber>(Vector.Y));
		Values.Add(MakeShared<FJsonValueNumber>(Vector.Z));
		return Values;
	}

	TArray<TSharedPtr<FJsonValue>> RotatorToJson(const FRotator& Rotator)
	{
		TArray<TSharedPtr<FJsonValue>> Values;
		Values.Add(MakeShared<FJsonValueNumber>(Rotator.Pitch));
		Values.Add(MakeShared<FJsonValueNumber>(Rotator.Yaw));
		Values.Add(MakeShared<FJsonValueNumber>(Rotator.Roll));
		return Values;
	}

	TSharedPtr<FJsonObject> ActorToJson(AActor* Actor)
	{
		TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
		if (!Actor)
		{
			return Obj;
		}

		Obj->SetStringField(TEXT("label"), Actor->GetActorLabel());
		Obj->SetStringField(TEXT("name"), Actor->GetName());
		Obj->SetStringField(TEXT("path"), Actor->GetPathName());
		Obj->SetStringField(TEXT("class"), Actor->GetClass() ? Actor->GetClass()->GetName() : TEXT(""));
		Obj->SetArrayField(TEXT("location"), VectorToJson(Actor->GetActorLocation()));
		Obj->SetArrayField(TEXT("rotation"), RotatorToJson(Actor->GetActorRotation()));
		Obj->SetBoolField(TEXT("is_pawn"), Actor->IsA<APawn>());
		return Obj;
	}

	bool ActorMatches(AActor* Actor, const FString& Query, const FString& ClassFilter)
	{
		if (!Actor)
		{
			return false;
		}

		if (!ClassFilter.IsEmpty())
		{
			const FString ClassName = Actor->GetClass() ? Actor->GetClass()->GetName() : TEXT("");
			if (!ClassName.Contains(ClassFilter, ESearchCase::IgnoreCase))
			{
				return false;
			}
		}

		if (Query.IsEmpty())
		{
			return true;
		}

		return Actor->GetActorLabel().Contains(Query, ESearchCase::IgnoreCase)
			|| Actor->GetName().Contains(Query, ESearchCase::IgnoreCase)
			|| Actor->GetPathName().Contains(Query, ESearchCase::IgnoreCase);
	}

	AActor* FindActor(UWorld* World, const FString& ActorRef)
	{
		if (!World || ActorRef.IsEmpty())
		{
			return nullptr;
		}

		for (TActorIterator<AActor> It(World); It; ++It)
		{
			AActor* Actor = *It;
			if (!Actor)
			{
				continue;
			}

			if (Actor->GetActorLabel().Equals(ActorRef, ESearchCase::IgnoreCase)
				|| Actor->GetName().Equals(ActorRef, ESearchCase::IgnoreCase)
				|| Actor->GetPathName().Equals(ActorRef, ESearchCase::IgnoreCase))
			{
				return Actor;
			}
		}

		return nullptr;
	}

	FString RequireActorRef(const TSharedPtr<FJsonObject>& Params)
	{
		FString ActorRef;
		Params->TryGetStringField(TEXT("actor"), ActorRef);
		return ActorRef;
	}
}

TSharedPtr<FJsonObject> FFindActorCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	UWorld* World = GetActiveWorld();
	if (!World)
	{
		return AudioMCP::MakeErrorResponse(TEXT("No editor or PIE world available"));
	}

	FString Query;
	Params->TryGetStringField(TEXT("query"), Query);

	FString ClassFilter;
	Params->TryGetStringField(TEXT("class_filter"), ClassFilter);

	double LimitValue = 50.0;
	Params->TryGetNumberField(TEXT("limit"), LimitValue);
	const int32 Limit = FMath::Clamp(static_cast<int32>(LimitValue), 1, 500);

	TArray<TSharedPtr<FJsonValue>> Actors;
	int32 TotalMatches = 0;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		AActor* Actor = *It;
		if (!ActorMatches(Actor, Query, ClassFilter))
		{
			continue;
		}

		TotalMatches++;
		if (Actors.Num() < Limit)
		{
			Actors.Add(MakeShared<FJsonValueObject>(ActorToJson(Actor)));
		}
	}

	TSharedPtr<FJsonObject> Resp = AudioMCP::MakeOkResponse();
	Resp->SetStringField(TEXT("query"), Query);
	Resp->SetStringField(TEXT("class_filter"), ClassFilter);
	Resp->SetNumberField(TEXT("total"), TotalMatches);
	Resp->SetNumberField(TEXT("shown"), Actors.Num());
	Resp->SetArrayField(TEXT("actors"), Actors);
	return Resp;
}

TSharedPtr<FJsonObject> FSetActorTransformCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	UWorld* World = GetEditorWorld();
	if (!World)
	{
		return AudioMCP::MakeErrorResponse(TEXT("No editor world available"));
	}

	const FString ActorRef = RequireActorRef(Params);
	if (ActorRef.IsEmpty())
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'actor'"));
	}

	AActor* Actor = FindActor(World, ActorRef);
	if (!Actor)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Actor '%s' not found"), *ActorRef));
	}

	FString Error;
	FVector Location = Actor->GetActorLocation();
	FRotator Rotation = Actor->GetActorRotation();
	const bool bHasLocation = ReadVectorArray(Params, TEXT("location"), Location, Error);
	if (!Error.IsEmpty())
	{
		return AudioMCP::MakeErrorResponse(Error);
	}
	const bool bHasRotation = ReadRotatorArray(Params, TEXT("rotation"), Rotation, Error);
	if (!Error.IsEmpty())
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	if (!bHasLocation && !bHasRotation)
	{
		return AudioMCP::MakeErrorResponse(TEXT("Provide at least one of 'location' or 'rotation'"));
	}

	Actor->Modify();
	if (bHasLocation)
	{
		Actor->SetActorLocation(Location, false, nullptr, ETeleportType::TeleportPhysics);
	}
	if (bHasRotation)
	{
		Actor->SetActorRotation(Rotation, ETeleportType::TeleportPhysics);
	}
#if WITH_EDITOR
	Actor->PostEditMove(true);
#endif
	Actor->MarkPackageDirty();

	TSharedPtr<FJsonObject> Resp = AudioMCP::MakeOkResponse();
	Resp->SetObjectField(TEXT("actor"), ActorToJson(Actor));
	return Resp;
}

TSharedPtr<FJsonObject> FFocusEditorCameraCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	UWorld* World = GetEditorWorld();
	if (!World)
	{
		return AudioMCP::MakeErrorResponse(TEXT("No editor world available"));
	}
	if (!GEditor)
	{
		return AudioMCP::MakeErrorResponse(TEXT("GEditor unavailable"));
	}

	const FString ActorRef = RequireActorRef(Params);
	if (ActorRef.IsEmpty())
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'actor'"));
	}

	AActor* Actor = FindActor(World, ActorRef);
	if (!Actor)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Actor '%s' not found"), *ActorRef));
	}

	bool bActiveViewportOnly = true;
	Params->TryGetBoolField(TEXT("active_viewport_only"), bActiveViewportOnly);

	GEditor->MoveViewportCamerasToActor(*Actor, bActiveViewportOnly);

	TSharedPtr<FJsonObject> Resp = AudioMCP::MakeOkResponse();
	Resp->SetObjectField(TEXT("actor"), ActorToJson(Actor));
	Resp->SetBoolField(TEXT("active_viewport_only"), bActiveViewportOnly);
	return Resp;
}

TSharedPtr<FJsonObject> FSetViewTargetCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	UWorld* World = GetPIEWorld();
	if (!World)
	{
		return AudioMCP::MakeErrorResponse(TEXT("No PIE/simulation world available"));
	}

	const FString ActorRef = RequireActorRef(Params);
	if (ActorRef.IsEmpty())
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'actor'"));
	}

	AActor* Target = FindActor(World, ActorRef);
	if (!Target)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Actor '%s' not found"), *ActorRef));
	}

	double PlayerIndexValue = 0.0;
	Params->TryGetNumberField(TEXT("player_index"), PlayerIndexValue);
	const int32 PlayerIndex = FMath::Max(0, static_cast<int32>(PlayerIndexValue));

	double BlendTime = 0.0;
	Params->TryGetNumberField(TEXT("blend_time"), BlendTime);

	APlayerController* PC = UGameplayStatics::GetPlayerController(World, PlayerIndex);
	if (!PC)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("No PlayerController found for player_index %d. This command requires PIE/simulation."), PlayerIndex));
	}

	PC->SetViewTargetWithBlend(Target, static_cast<float>(FMath::Max(0.0, BlendTime)));

	TSharedPtr<FJsonObject> Resp = AudioMCP::MakeOkResponse();
	Resp->SetObjectField(TEXT("actor"), ActorToJson(Target));
	Resp->SetNumberField(TEXT("player_index"), PlayerIndex);
	Resp->SetNumberField(TEXT("blend_time"), BlendTime);
	return Resp;
}

TSharedPtr<FJsonObject> FPossessPawnCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& /*BuilderManager*/)
{
	UWorld* World = GetPIEWorld();
	if (!World)
	{
		return AudioMCP::MakeErrorResponse(TEXT("No PIE/simulation world available"));
	}

	const FString ActorRef = RequireActorRef(Params);
	if (ActorRef.IsEmpty())
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'actor'"));
	}

	AActor* Actor = FindActor(World, ActorRef);
	if (!Actor)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Actor '%s' not found"), *ActorRef));
	}

	APawn* Pawn = Cast<APawn>(Actor);
	if (!Pawn)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Actor '%s' is not a Pawn/Character"), *ActorRef));
	}

	double PlayerIndexValue = 0.0;
	Params->TryGetNumberField(TEXT("player_index"), PlayerIndexValue);
	const int32 PlayerIndex = FMath::Max(0, static_cast<int32>(PlayerIndexValue));

	APlayerController* PC = UGameplayStatics::GetPlayerController(World, PlayerIndex);
	if (!PC)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("No PlayerController found for player_index %d. Possession requires PIE/simulation."), PlayerIndex));
	}

	PC->Possess(Pawn);

	bool bSetViewTarget = true;
	Params->TryGetBoolField(TEXT("set_view_target"), bSetViewTarget);
	if (bSetViewTarget)
	{
		PC->SetViewTarget(Pawn);
	}

	TSharedPtr<FJsonObject> Resp = AudioMCP::MakeOkResponse();
	Resp->SetObjectField(TEXT("actor"), ActorToJson(Pawn));
	Resp->SetNumberField(TEXT("player_index"), PlayerIndex);
	Resp->SetBoolField(TEXT("set_view_target"), bSetViewTarget);
	return Resp;
}
