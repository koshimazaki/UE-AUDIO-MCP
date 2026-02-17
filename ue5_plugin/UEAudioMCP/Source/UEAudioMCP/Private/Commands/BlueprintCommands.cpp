// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/BlueprintCommands.h"
#include "AudioMCPBuilderManager.h"
#include "AudioMCPTypes.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/SoftObjectPath.h"
#include "Editor.h"

DEFINE_LOG_CATEGORY_STATIC(LogAudioMCPBlueprint, Log, All);

// Allowlist of safe audio-related functions that can be called via reflection.
// Prevents arbitrary function execution (e.g. QuitGame, DestroyActor).
static const TSet<FString>& GetAllowedFunctions()
{
	static const TSet<FString> AllowedFunctions = {
		// Audio playback
		TEXT("PlaySound2D"),
		TEXT("PlaySoundAtLocation"),
		TEXT("SpawnSoundAtLocation"),
		TEXT("SpawnSound2D"),
		// Sound mix
		TEXT("SetSoundMixClassOverride"),
		TEXT("ClearSoundMixClassOverride"),
		TEXT("PushSoundMixModifier"),
		TEXT("PopSoundMixModifier"),
		// Global audio
		TEXT("SetGlobalPitchModulation"),
		TEXT("SetGlobalListenerFocusParameters"),
		// Dialogue
		TEXT("PlayDialogue2D"),
		TEXT("PlayDialogueAtLocation"),
		TEXT("SpawnDialogue2D"),
		TEXT("SpawnDialogueAtLocation"),
		// Read-only accessors
		TEXT("GetPlayerCameraManager"),
		TEXT("GetPlayerController"),
		TEXT("GetPlayerPawn"),
	};
	return AllowedFunctions;
}

TSharedPtr<FJsonObject> FCallFunctionCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString FunctionName;
	if (!Params->TryGetStringField(TEXT("function"), FunctionName))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'function'"));
	}

	// Security: only allow known safe audio functions
	if (!GetAllowedFunctions().Contains(FunctionName))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Function '%s' is not in the audio allowlist. "
				"Only audio-related functions (PlaySound2D, SpawnSoundAtLocation, etc.) are permitted."),
				*FunctionName));
	}

	// Get the args object (optional, defaults to empty)
	const TSharedPtr<FJsonObject>* ArgsObj = nullptr;
	Params->TryGetObjectField(TEXT("args"), ArgsObj);

	// Get the editor world as the context object
	UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
	if (!World)
	{
		return AudioMCP::MakeErrorResponse(TEXT("No editor world available"));
	}

	// Try to find the function on common targets:
	// 1. UGameplayStatics (most audio functions live here)
	// 2. World's GameInstance
	// 3. First PlayerController

	UObject* TargetObject = nullptr;
	UFunction* Function = nullptr;

	// Search UGameplayStatics first (PlaySound2D, SpawnSoundAtLocation, etc.)
	Function = UGameplayStatics::StaticClass()->FindFunctionByName(FName(*FunctionName));
	if (Function)
	{
		TargetObject = UGameplayStatics::StaticClass()->GetDefaultObject();
	}

	// Search World
	if (!Function)
	{
		Function = World->GetClass()->FindFunctionByName(FName(*FunctionName));
		if (Function)
		{
			TargetObject = World;
		}
	}

	// Search GameInstance
	if (!Function && World->GetGameInstance())
	{
		Function = World->GetGameInstance()->GetClass()->FindFunctionByName(FName(*FunctionName));
		if (Function)
		{
			TargetObject = World->GetGameInstance();
		}
	}

	if (!Function || !TargetObject)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Function '%s' not found on GameplayStatics, World, or GameInstance. "
				"Ensure the function exists and is callable."), *FunctionName));
	}

	// RAII guard for properly initializing and destroying UE property values
	struct FParamBufferGuard
	{
		UFunction* Func;
		uint8* Buffer;

		FParamBufferGuard(UFunction* InFunc) : Func(InFunc), Buffer(nullptr)
		{
			if (Func->ParmsSize > 0)
			{
				Buffer = static_cast<uint8*>(FMemory::Malloc(Func->ParmsSize));
				FMemory::Memzero(Buffer, Func->ParmsSize);
				for (TFieldIterator<FProperty> It(Func); It; ++It)
				{
					It->InitializeValue_InContainer(Buffer);
				}
			}
		}

		~FParamBufferGuard()
		{
			if (Buffer)
			{
				for (TFieldIterator<FProperty> It(Func); It; ++It)
				{
					It->DestroyValue_InContainer(Buffer);
				}
				FMemory::Free(Buffer);
			}
		}
	};

	FParamBufferGuard ParamGuard(Function);
	uint8* ParamBuffer = ParamGuard.Buffer;

	// Auto-fill WorldContextObject for UGameplayStatics static functions.
	// ProcessEvent doesn't resolve meta=(WorldContext) automatically — we must do it.
	if (ParamBuffer)
	{
		for (TFieldIterator<FProperty> It(Function); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			if (It->GetName() == TEXT("WorldContextObject"))
			{
				if (FObjectProperty* ObjProp = CastField<FObjectProperty>(*It))
				{
					ObjProp->SetObjectPropertyValue_InContainer(ParamBuffer, World);
				}
				break;
			}
		}
	}

	// Fill parameters from JSON args
	if (ParamBuffer && ArgsObj && (*ArgsObj).IsValid())
	{
		for (TFieldIterator<FProperty> It(Function); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			FProperty* Prop = *It;
			if (Prop->HasAnyPropertyFlags(CPF_ReturnParm))
			{
				continue; // Skip return value
			}

			FString PropName = Prop->GetName();
			TSharedPtr<FJsonValue> JsonVal = (*ArgsObj)->TryGetField(PropName);
			if (!JsonVal.IsValid())
			{
				continue; // Use default
			}

			// Map JSON types to UE property types
			if (FFloatProperty* FloatProp = CastField<FFloatProperty>(Prop))
			{
				FloatProp->SetPropertyValue_InContainer(ParamBuffer, static_cast<float>(JsonVal->AsNumber()));
			}
			else if (FDoubleProperty* DoubleProp = CastField<FDoubleProperty>(Prop))
			{
				DoubleProp->SetPropertyValue_InContainer(ParamBuffer, JsonVal->AsNumber());
			}
			else if (FIntProperty* IntProp = CastField<FIntProperty>(Prop))
			{
				IntProp->SetPropertyValue_InContainer(ParamBuffer, static_cast<int32>(JsonVal->AsNumber()));
			}
			else if (FBoolProperty* BoolProp = CastField<FBoolProperty>(Prop))
			{
				BoolProp->SetPropertyValue_InContainer(ParamBuffer, JsonVal->AsBool());
			}
			else if (FStrProperty* StrProp = CastField<FStrProperty>(Prop))
			{
				StrProp->SetPropertyValue_InContainer(ParamBuffer, JsonVal->AsString());
			}
			else if (FNameProperty* NameProp = CastField<FNameProperty>(Prop))
			{
				NameProp->SetPropertyValue_InContainer(ParamBuffer, FName(*JsonVal->AsString()));
			}
			else if (FObjectProperty* ObjProp = CastField<FObjectProperty>(Prop))
			{
				// Load UObject asset from string path (e.g. "/Game/Audio/MySound.MySound")
				FString AssetPath = JsonVal->AsString();
				if (!AssetPath.IsEmpty())
				{
					UObject* LoadedObj = StaticLoadObject(ObjProp->PropertyClass, nullptr, *AssetPath);
					if (LoadedObj)
					{
						ObjProp->SetObjectPropertyValue_InContainer(ParamBuffer, LoadedObj);
					}
					else
					{
						return AudioMCP::MakeErrorResponse(
							FString::Printf(TEXT("Could not load asset '%s' for param '%s'"), *AssetPath, *PropName));
					}
				}
			}
			else if (FStructProperty* StructProp = CastField<FStructProperty>(Prop))
			{
				// Handle FVector from JSON object {"X": 0, "Y": 0, "Z": 0}
				if (StructProp->Struct == TBaseStructure<FVector>::Get())
				{
					const TSharedPtr<FJsonObject>* VecObj = nullptr;
					if (JsonVal->TryGetObject(VecObj) && VecObj && (*VecObj).IsValid())
					{
						FVector Vec;
						Vec.X = (*VecObj)->GetNumberField(TEXT("X"));
						Vec.Y = (*VecObj)->GetNumberField(TEXT("Y"));
						Vec.Z = (*VecObj)->GetNumberField(TEXT("Z"));
						*StructProp->ContainerPtrToValuePtr<FVector>(ParamBuffer) = Vec;
					}
				}
				else if (StructProp->Struct == TBaseStructure<FRotator>::Get())
				{
					const TSharedPtr<FJsonObject>* RotObj = nullptr;
					if (JsonVal->TryGetObject(RotObj) && RotObj && (*RotObj).IsValid())
					{
						FRotator Rot;
						Rot.Pitch = (*RotObj)->GetNumberField(TEXT("Pitch"));
						Rot.Yaw = (*RotObj)->GetNumberField(TEXT("Yaw"));
						Rot.Roll = (*RotObj)->GetNumberField(TEXT("Roll"));
						*StructProp->ContainerPtrToValuePtr<FRotator>(ParamBuffer) = Rot;
					}
				}
			}
		}
	}

	// Execute the function
	TargetObject->ProcessEvent(Function, ParamBuffer);

	// Extract return value if present
	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Called %s"), *FunctionName));
	Response->SetStringField(TEXT("function"), FunctionName);

	if (ParamBuffer)
	{
		for (TFieldIterator<FProperty> It(Function); It; ++It)
		{
			FProperty* Prop = *It;
			if (!Prop->HasAnyPropertyFlags(CPF_ReturnParm))
			{
				continue;
			}

			if (FBoolProperty* BoolProp = CastField<FBoolProperty>(Prop))
			{
				Response->SetBoolField(TEXT("return_value"), BoolProp->GetPropertyValue_InContainer(ParamBuffer));
			}
			else if (FFloatProperty* FloatProp = CastField<FFloatProperty>(Prop))
			{
				Response->SetNumberField(TEXT("return_value"), FloatProp->GetPropertyValue_InContainer(ParamBuffer));
			}
			else if (FIntProperty* IntProp = CastField<FIntProperty>(Prop))
			{
				Response->SetNumberField(TEXT("return_value"), IntProp->GetPropertyValue_InContainer(ParamBuffer));
			}
			else if (FStrProperty* StrProp = CastField<FStrProperty>(Prop))
			{
				Response->SetStringField(TEXT("return_value"), StrProp->GetPropertyValue_InContainer(ParamBuffer));
			}
			else if (FObjectProperty* ObjProp = CastField<FObjectProperty>(Prop))
			{
				UObject* RetObj = ObjProp->GetObjectPropertyValue_InContainer(ParamBuffer);
				Response->SetStringField(TEXT("return_value"),
					RetObj ? RetObj->GetPathName() : TEXT("null"));
			}
		}
	}
	// ParamGuard destructor handles DestroyValue + Free

	UE_LOG(LogAudioMCPBlueprint, Log, TEXT("Called function: %s"), *FunctionName);
	return Response;
}
