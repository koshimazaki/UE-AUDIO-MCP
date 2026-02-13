// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

// Must match Python ue5_connection.py constants exactly
namespace AudioMCP
{
	constexpr int32 DEFAULT_PORT = 9877;
	constexpr int32 HEADER_SIZE = 4;
	constexpr int32 MAX_MESSAGE_SIZE = 16 * 1024 * 1024; // 16 MB
	constexpr int32 GAME_THREAD_TIMEOUT_MS = 25000;       // Under Python's 30s

	// Sentinel node ID for graph-level input/output wiring
	inline const TCHAR GRAPH_BOUNDARY[] = TEXT("__graph__");

	/** Serialize a JSON object to a compact UTF-8 string. */
	inline FString JsonToString(const TSharedPtr<FJsonObject>& JsonObj)
	{
		FString Output;
		TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>> Writer =
			TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Output);
		FJsonSerializer::Serialize(JsonObj.ToSharedRef(), Writer);
		return Output;
	}

	/** Create a success response: {"status":"ok", ...extra fields} */
	inline TSharedPtr<FJsonObject> MakeOkResponse()
	{
		TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
		Obj->SetStringField(TEXT("status"), TEXT("ok"));
		return Obj;
	}

	/** Create a success response with a message field. */
	inline TSharedPtr<FJsonObject> MakeOkResponse(const FString& Message)
	{
		TSharedPtr<FJsonObject> Obj = MakeOkResponse();
		Obj->SetStringField(TEXT("message"), Message);
		return Obj;
	}

	/** Create an error response: {"status":"error","message":"..."} */
	inline TSharedPtr<FJsonObject> MakeErrorResponse(const FString& Message)
	{
		TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
		Obj->SetStringField(TEXT("status"), TEXT("error"));
		Obj->SetStringField(TEXT("message"), Message);
		return Obj;
	}

	/** Shared list of audio-relevant keywords for Blueprint scanning.
	 *  Used by QueryCommands.cpp and AudioMCPEditorMenu.cpp — single source of truth.
	 */
	inline bool IsAudioRelevant(const FString& Name)
	{
		static const TCHAR* Keywords[] = {
			TEXT("Sound"), TEXT("Audio"), TEXT("Ak"), TEXT("Wwise"),
			TEXT("MetaSound"), TEXT("Reverb"), TEXT("SoundMix"),
			TEXT("Dialogue"), TEXT("RTPC"), TEXT("Occlusion"),
			TEXT("Attenuation"), TEXT("PostEvent"), TEXT("SetSwitch"),
			TEXT("SetState"), TEXT("Submix"), TEXT("Modulation"),
			TEXT("SoundClass"), TEXT("SoundCue"), TEXT("Listener"),
			TEXT("Spatialization"), TEXT("AudioVolume"),
			TEXT("Quartz"), TEXT("Pitch"), TEXT("Volume"),
		};
		for (const TCHAR* Keyword : Keywords)
		{
			if (Name.Contains(Keyword, ESearchCase::IgnoreCase))
			{
				return true;
			}
		}
		return false;
	}
}
