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
	, bShuttingDown(false)
	, bAlive(MakeShared<FThreadSafeBool>(true))
{
}

FAudioMCPCommandDispatcher::~FAudioMCPCommandDispatcher()
{
}

void FAudioMCPCommandDispatcher::SignalShutdown()
{
	bShuttingDown = true;
	// Mark alive flag as false so any in-flight AsyncTask lambdas
	// will skip execution instead of dereferencing freed BuilderManager
	*bAlive = false;
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

	// 4. Check for shutdown — return error without posting AsyncTask to avoid deadlock
	if (bShuttingDown)
	{
		return AudioMCP::JsonToString(
			AudioMCP::MakeErrorResponse(TEXT("Server is shutting down")));
	}

	// 5. Execute on game thread with sync event.
	// All captured state is heap-allocated via TSharedPtr so the lambda
	// remains valid even if the caller times out and returns first.
	struct FDispatchState
	{
		TSharedPtr<FJsonObject> Result;
		FEvent* CompletionEvent;
		TSharedPtr<IAudioMCPCommand> Handler;
		TSharedPtr<FJsonObject> Params;
		FAudioMCPBuilderManager* BuilderMgr;
		TSharedPtr<FThreadSafeBool> Alive;  // Shared flag to detect shutdown

		FDispatchState(FEvent* InEvent, TSharedPtr<IAudioMCPCommand> InHandler,
		               TSharedPtr<FJsonObject> InParams, FAudioMCPBuilderManager* InMgr,
		               TSharedPtr<FThreadSafeBool> InAlive)
			: CompletionEvent(InEvent), Handler(InHandler), Params(InParams),
			  BuilderMgr(InMgr), Alive(InAlive) {}

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
		*HandlerPtr, JsonObj, BuilderManager, bAlive);

	AsyncTask(ENamedThreads::GameThread, [State]()
	{
		// Guard against use-after-free: if shutdown destroyed BuilderManager,
		// skip execution and just trigger the event so the TCP thread unblocks.
		if (*State->Alive)
		{
			State->Result = State->Handler->Execute(State->Params, *State->BuilderMgr);
		}
		State->CompletionEvent->Trigger();
	});

	// Poll in 500ms intervals instead of a single 25s wait.
	// This lets the TCP thread exit promptly when bShuttingDown is set,
	// preventing a 25-second editor freeze during shutdown.
	constexpr uint32 PollIntervalMs = 500;
	uint32 ElapsedMs = 0;
	bool bCompleted = false;
	while (ElapsedMs < static_cast<uint32>(AudioMCP::GAME_THREAD_TIMEOUT_MS))
	{
		if (State->CompletionEvent->Wait(PollIntervalMs))
		{
			bCompleted = true;
			break;
		}
		ElapsedMs += PollIntervalMs;
		if (bShuttingDown)
		{
			break;  // Exit quickly on shutdown instead of waiting full timeout
		}
	}

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
