// Copyright UE Audio MCP Project. All Rights Reserved.

#include "AudioMCPCommandDispatcher.h"
#include "AudioMCPBuilderManager.h"
#include "AudioMCPTypes.h"
#include "Commands/IAudioMCPCommand.h"
#include "Async/Async.h"
#include "Dom/JsonObject.h"
#include "HAL/Event.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

DEFINE_LOG_CATEGORY_STATIC(LogAudioMCPDispatcher, Log, All);

FAudioMCPCommandDispatcher::FAudioMCPCommandDispatcher(FAudioMCPBuilderManager* InBuilderManager)
	: BuilderManager(InBuilderManager)
{
}

FAudioMCPCommandDispatcher::~FAudioMCPCommandDispatcher()
{
}

void FAudioMCPCommandDispatcher::RegisterCommand(const FString& Action, TSharedPtr<IAudioMCPCommand> Handler)
{
	CommandMap.Add(Action, Handler);
	UE_LOG(LogAudioMCPDispatcher, Log, TEXT("Registered command: %s"), *Action);
}

FString FAudioMCPCommandDispatcher::Dispatch(const FString& JsonString)
{
	// 1. Parse JSON
	TSharedPtr<FJsonObject> JsonObj;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonString);
	if (!FJsonSerializer::Deserialize(Reader, JsonObj) || !JsonObj.IsValid())
	{
		return AudioMCP::JsonToString(AudioMCP::MakeErrorResponse(TEXT("Invalid JSON")));
	}

	// 2. Extract action
	FString Action;
	if (!JsonObj->TryGetStringField(TEXT("action"), Action))
	{
		return AudioMCP::JsonToString(AudioMCP::MakeErrorResponse(TEXT("Missing 'action' field")));
	}

	// 3. Find handler
	TSharedPtr<IAudioMCPCommand>* HandlerPtr = CommandMap.Find(Action);
	if (!HandlerPtr || !HandlerPtr->IsValid())
	{
		return AudioMCP::JsonToString(
			AudioMCP::MakeErrorResponse(FString::Printf(TEXT("Unknown action: '%s'"), *Action)));
	}

	UE_LOG(LogAudioMCPDispatcher, Log, TEXT("Dispatching: %s"), *Action);

	// 4. Execute on game thread with sync event.
	// All captured state is heap-allocated via TSharedPtr so the lambda
	// remains valid even if the caller times out and returns first.
	struct FDispatchState
	{
		TSharedPtr<FJsonObject> Result;
		FEvent* CompletionEvent;
		TSharedPtr<IAudioMCPCommand> Handler;
		TSharedPtr<FJsonObject> Params;
		FAudioMCPBuilderManager* BuilderMgr;

		FDispatchState(FEvent* InEvent, TSharedPtr<IAudioMCPCommand> InHandler,
		               TSharedPtr<FJsonObject> InParams, FAudioMCPBuilderManager* InMgr)
			: CompletionEvent(InEvent), Handler(InHandler), Params(InParams), BuilderMgr(InMgr) {}

		~FDispatchState()
		{
			if (CompletionEvent)
			{
				FPlatformProcess::ReturnSynchEventToPool(CompletionEvent);
			}
		}
	};

	TSharedPtr<FDispatchState> State = MakeShared<FDispatchState>(
		FPlatformProcess::GetSynchEventFromPool(false),
		*HandlerPtr, JsonObj, BuilderManager);

	AsyncTask(ENamedThreads::GameThread, [State]()
	{
		State->Result = State->Handler->Execute(State->Params, *State->BuilderMgr);
		State->CompletionEvent->Trigger();
	});

	// Wait for game thread execution (25s timeout, under Python's 30s)
	bool bCompleted = State->CompletionEvent->Wait(AudioMCP::GAME_THREAD_TIMEOUT_MS);

	if (!bCompleted)
	{
		UE_LOG(LogAudioMCPDispatcher, Error, TEXT("Command '%s' timed out on game thread"), *Action);
		return AudioMCP::JsonToString(
			AudioMCP::MakeErrorResponse(
				FString::Printf(TEXT("Command '%s' timed out after %dms"),
					*Action, AudioMCP::GAME_THREAD_TIMEOUT_MS)));
	}

	TSharedPtr<FJsonObject> Result = State->Result;
	if (!Result.IsValid())
	{
		return AudioMCP::JsonToString(AudioMCP::MakeErrorResponse(TEXT("Command returned null result")));
	}

	// Ensure action is echoed back in the response
	Result->SetStringField(TEXT("action"), Action);

	return AudioMCP::JsonToString(Result);
}
