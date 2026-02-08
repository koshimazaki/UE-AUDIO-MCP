// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "HAL/Runnable.h"
#include "HAL/ThreadSafeBool.h"
#include "HAL/CriticalSection.h"
#include "Sockets.h"

class FAudioMCPCommandDispatcher;

/**
 * Background TCP server that accepts one client at a time.
 * Runs on a dedicated FRunnable thread, dispatches commands
 * to the game thread via the CommandDispatcher.
 *
 * Wire protocol: 4-byte big-endian uint32 length + UTF-8 JSON payload.
 * Matches Python ue5_connection.py exactly.
 */
class FAudioMCPTcpServer : public FRunnable
{
public:
	FAudioMCPTcpServer(FAudioMCPCommandDispatcher* InDispatcher);
	virtual ~FAudioMCPTcpServer();

	/** Start listening on the given port. Returns true on success. */
	bool StartListening(int32 Port);

	/** Signal the server to stop and wait for thread exit. */
	void StopListening();

	/** Is the server currently listening? */
	bool IsListening() const { return ListenSocket != nullptr; }

	// FRunnable interface
	virtual bool Init() override;
	virtual uint32 Run() override;
	virtual void Stop() override;
	virtual void Exit() override;

private:
	/** Handle a single connected client until disconnect or error. */
	void HandleClient(FSocket* Client);

	/** Read exactly Size bytes from socket. Returns false on error/disconnect. */
	bool RecvExact(FSocket* Socket, uint8* Buffer, int32 Size);

	/** Send exactly Size bytes to socket, looping on partial sends. */
	bool SendExact(FSocket* Socket, const uint8* Data, int32 Size);

	/** Send a JSON response with length-prefix header. */
	bool SendResponse(FSocket* Socket, const FString& JsonString);

	/** Check if socket has data ready within timeout. Returns false on timeout/error. */
	bool WaitForData(FSocket* Socket, float TimeoutSeconds);

	FAudioMCPCommandDispatcher* Dispatcher;
	FSocket* ListenSocket;
	FRunnableThread* Thread;
	FThreadSafeBool bStopping;

	/** Guards ActiveClientSocket access between TCP thread and StopListening(). */
	FCriticalSection ClientSocketMutex;
	/** Current client socket — stored so StopListening() can close it to unblock RecvExact(). */
	FSocket* ActiveClientSocket = nullptr;
};
