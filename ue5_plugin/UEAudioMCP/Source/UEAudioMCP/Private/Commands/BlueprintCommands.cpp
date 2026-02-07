// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/BlueprintCommands.h"
#include "AudioMCPBuilderManager.h"
#include "AudioMCPTypes.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"
#include "Editor.h"

DEFINE_LOG_CATEGORY_STATIC(LogAudioMCPBlueprint, Log, All);

TSharedPtr<FJsonObject> FCallFunctionCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString FunctionName;
	if (!Params->TryGetStringField(TEXT("function"), FunctionName))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'function'"));
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
		}
	}
	// ParamGuard destructor handles DestroyValue + Free

	UE_LOG(LogAudioMCPBlueprint, Log, TEXT("Called function: %s"), *FunctionName);
	return Response;
}
