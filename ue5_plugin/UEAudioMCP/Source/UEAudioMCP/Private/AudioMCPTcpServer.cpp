// Copyright UE Audio MCP Project. All Rights Reserved.

#include "AudioMCPTcpServer.h"
#include "AudioMCPCommandDispatcher.h"
#include "AudioMCPTypes.h"
#include "Common/TcpSocketBuilder.h"
#include "Sockets.h"
#include "SocketSubsystem.h"

DEFINE_LOG_CATEGORY_STATIC(LogAudioMCPServer, Log, All);

FAudioMCPTcpServer::FAudioMCPTcpServer(FAudioMCPCommandDispatcher* InDispatcher)
	: Dispatcher(InDispatcher)
	, ListenSocket(nullptr)
	, Thread(nullptr)
	, bStopping(false)
{
}

FAudioMCPTcpServer::~FAudioMCPTcpServer()
{
	StopListening();
}

bool FAudioMCPTcpServer::StartListening(int32 Port)
{
	if (ListenSocket)
	{
		UE_LOG(LogAudioMCPServer, Warning, TEXT("Already listening"));
		return false;
	}

	ISocketSubsystem* SocketSubsystem = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
	if (!SocketSubsystem)
	{
		UE_LOG(LogAudioMCPServer, Error, TEXT("Failed to get socket subsystem"));
		return false;
	}

	ListenSocket = FTcpSocketBuilder(TEXT("AudioMCPListener"))
		.AsReusable()
		.BoundToAddress(FIPv4Address(127, 0, 0, 1))
		.BoundToPort(Port)
		.Listening(1)
		.Build();

	if (!ListenSocket)
	{
		UE_LOG(LogAudioMCPServer, Error, TEXT("Failed to create listen socket on port %d"), Port);
		return false;
	}

	bStopping = false;
	Thread = FRunnableThread::Create(this, TEXT("AudioMCPTcpServer"), 0, TPri_Normal);

	if (!Thread)
	{
		UE_LOG(LogAudioMCPServer, Error, TEXT("Failed to create server thread"));
		ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(ListenSocket);
		ListenSocket = nullptr;
		return false;
	}

	UE_LOG(LogAudioMCPServer, Log, TEXT("Audio MCP TCP server listening on port %d"), Port);
	return true;
}

void FAudioMCPTcpServer::StopListening()
{
	bStopping = true;

	if (ListenSocket)
	{
		ListenSocket->Close();
	}

	// Close the active client socket to unblock any RecvExact() call on the TCP thread.
	// Without this, a blocked Recv() would hang WaitForCompletion() indefinitely.
	{
		FScopeLock Lock(&ClientSocketMutex);
		if (ActiveClientSocket)
		{
			ActiveClientSocket->Close();
		}
	}

	if (Thread)
	{
		Thread->WaitForCompletion();
		delete Thread;
		Thread = nullptr;
	}

	if (ListenSocket)
	{
		ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(ListenSocket);
		ListenSocket = nullptr;
	}

	UE_LOG(LogAudioMCPServer, Log, TEXT("Audio MCP TCP server stopped"));
}

bool FAudioMCPTcpServer::Init()
{
	return true;
}

uint32 FAudioMCPTcpServer::Run()
{
	while (!bStopping)
	{
		// Wait for a connection with a timeout so we can check bStopping
		bool bHasPendingConnection = false;
		ListenSocket->WaitForPendingConnection(bHasPendingConnection, FTimespan::FromSeconds(1.0));

		if (bStopping)
		{
			break;
		}

		if (bHasPendingConnection)
		{
			TSharedRef<FInternetAddr> RemoteAddr = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->CreateInternetAddr();
			FSocket* ClientSocket = ListenSocket->Accept(*RemoteAddr, TEXT("AudioMCPClient"));

			if (ClientSocket)
			{
				UE_LOG(LogAudioMCPServer, Log, TEXT("Client connected from %s"), *RemoteAddr->ToString(true));
				HandleClient(ClientSocket);
				UE_LOG(LogAudioMCPServer, Log, TEXT("Client disconnected"));

				ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(ClientSocket);
			}
		}
	}

	return 0;
}

void FAudioMCPTcpServer::Stop()
{
	bStopping = true;
}

void FAudioMCPTcpServer::Exit()
{
}

void FAudioMCPTcpServer::HandleClient(FSocket* Client)
{
	// Register client socket so StopListening() can close it to unblock RecvExact()
	{
		FScopeLock Lock(&ClientSocketMutex);
		ActiveClientSocket = Client;
	}

	// Set socket buffer sizes for predictable behavior
	int32 ActualSize = 0;
	Client->SetSendBufferSize(65536, ActualSize);
	Client->SetReceiveBufferSize(65536, ActualSize);

	constexpr float ClientIdleTimeoutSeconds = 60.0f;

	while (!bStopping)
	{
		// Wait for data with idle timeout to prevent zombie connections
		if (!WaitForData(Client, ClientIdleTimeoutSeconds))
		{
			UE_LOG(LogAudioMCPServer, Log, TEXT("Client idle timeout (%.0fs), disconnecting"), ClientIdleTimeoutSeconds);
			break;
		}

		// 1. Read 4-byte big-endian length header
		uint8 HeaderBuf[AudioMCP::HEADER_SIZE];
		if (!RecvExact(Client, HeaderBuf, AudioMCP::HEADER_SIZE))
		{
			break; // Client disconnected or error
		}

		// Decode big-endian uint32 (network byte order)
		uint32 PayloadLength = (static_cast<uint32>(HeaderBuf[0]) << 24)
		                     | (static_cast<uint32>(HeaderBuf[1]) << 16)
		                     | (static_cast<uint32>(HeaderBuf[2]) << 8)
		                     | (static_cast<uint32>(HeaderBuf[3]));

		if (PayloadLength == 0 || PayloadLength > static_cast<uint32>(AudioMCP::MAX_MESSAGE_SIZE))
		{
			UE_LOG(LogAudioMCPServer, Error,
				TEXT("Invalid message size: %u bytes (max %d)"),
				PayloadLength, AudioMCP::MAX_MESSAGE_SIZE);

			FString ErrorJson = AudioMCP::JsonToString(
				AudioMCP::MakeErrorResponse(
					FString::Printf(TEXT("Message size %u exceeds maximum %d"),
						PayloadLength, AudioMCP::MAX_MESSAGE_SIZE)));
			SendResponse(Client, ErrorJson);
			break;
		}

		// 2. Read payload (reuse buffer across messages to reduce allocations)
		static thread_local TArray<uint8> PayloadBuf;
		if (PayloadBuf.Num() < static_cast<int32>(PayloadLength))
		{
			PayloadBuf.SetNumUninitialized(PayloadLength);
		}
		if (!RecvExact(Client, PayloadBuf.GetData(), PayloadLength))
		{
			break;
		}

		// 3. Decode UTF-8 payload
		FString JsonString;
		{
			FUTF8ToTCHAR Converter(reinterpret_cast<const ANSICHAR*>(PayloadBuf.GetData()), PayloadLength);
			JsonString = FString(Converter.Length(), Converter.Get());
		}

		UE_LOG(LogAudioMCPServer, Verbose, TEXT("Received: %s"), *JsonString);

		// 4. Dispatch command and get response
		FString ResponseJson = Dispatcher->Dispatch(JsonString);

		UE_LOG(LogAudioMCPServer, Verbose, TEXT("Sending: %s"), *ResponseJson);

		// 5. Send response
		if (!SendResponse(Client, ResponseJson))
		{
			break;
		}

		// 6. Shrink payload buffer if it grew too large (W5: prevent monotonic growth)
		if (PayloadBuf.Max() > 65536)
		{
			PayloadBuf.Empty();
		}
	}

	// Clear client socket registration so StopListening() won't close a stale pointer
	{
		FScopeLock Lock(&ClientSocketMutex);
		ActiveClientSocket = nullptr;
	}
}

bool FAudioMCPTcpServer::RecvExact(FSocket* Socket, uint8* Buffer, int32 Size)
{
	int32 BytesRead = 0;
	while (BytesRead < Size && !bStopping)
	{
		int32 Read = 0;
		if (!Socket->Recv(Buffer + BytesRead, Size - BytesRead, Read))
		{
			return false;
		}
		if (Read == 0)
		{
			return false; // Connection closed
		}
		BytesRead += Read;
	}
	return BytesRead == Size;
}

bool FAudioMCPTcpServer::SendExact(FSocket* Socket, const uint8* Data, int32 Size)
{
	int32 TotalSent = 0;
	while (TotalSent < Size && !bStopping)
	{
		int32 Sent = 0;
		if (!Socket->Send(Data + TotalSent, Size - TotalSent, Sent))
		{
			return false;
		}
		if (Sent == 0)
		{
			return false;
		}
		TotalSent += Sent;
	}
	return TotalSent == Size;
}

bool FAudioMCPTcpServer::SendResponse(FSocket* Socket, const FString& JsonString)
{
	// Convert to UTF-8
	FTCHARToUTF8 Converter(*JsonString);
	int32 PayloadSize = Converter.Length();

	// Response size guard
	if (PayloadSize > AudioMCP::MAX_MESSAGE_SIZE)
	{
		UE_LOG(LogAudioMCPServer, Error,
			TEXT("Response too large: %d bytes (max %d)"), PayloadSize, AudioMCP::MAX_MESSAGE_SIZE);

		// Send a truncated error response instead
		FString ErrorJson = AudioMCP::JsonToString(
			AudioMCP::MakeErrorResponse(
				FString::Printf(TEXT("Response size %d exceeds maximum %d"),
					PayloadSize, AudioMCP::MAX_MESSAGE_SIZE)));
		FTCHARToUTF8 ErrorConverter(*ErrorJson);
		PayloadSize = ErrorConverter.Length();

		uint8 Header[AudioMCP::HEADER_SIZE];
		Header[0] = static_cast<uint8>((PayloadSize >> 24) & 0xFF);
		Header[1] = static_cast<uint8>((PayloadSize >> 16) & 0xFF);
		Header[2] = static_cast<uint8>((PayloadSize >> 8) & 0xFF);
		Header[3] = static_cast<uint8>(PayloadSize & 0xFF);

		if (!SendExact(Socket, Header, AudioMCP::HEADER_SIZE))
		{
			return false;
		}
		return SendExact(Socket, reinterpret_cast<const uint8*>(ErrorConverter.Get()), PayloadSize);
	}

	// Build 4-byte big-endian header
	uint8 Header[AudioMCP::HEADER_SIZE];
	Header[0] = static_cast<uint8>((PayloadSize >> 24) & 0xFF);
	Header[1] = static_cast<uint8>((PayloadSize >> 16) & 0xFF);
	Header[2] = static_cast<uint8>((PayloadSize >> 8) & 0xFF);
	Header[3] = static_cast<uint8>(PayloadSize & 0xFF);

	// Send header using SendExact (handles partial sends)
	if (!SendExact(Socket, Header, AudioMCP::HEADER_SIZE))
	{
		UE_LOG(LogAudioMCPServer, Error, TEXT("Failed to send response header"));
		return false;
	}

	// Send payload using SendExact
	if (!SendExact(Socket, reinterpret_cast<const uint8*>(Converter.Get()), PayloadSize))
	{
		UE_LOG(LogAudioMCPServer, Error, TEXT("Failed to send response payload"));
		return false;
	}

	return true;
}

bool FAudioMCPTcpServer::WaitForData(FSocket* Socket, float TimeoutSeconds)
{
	// Use native socket Wait() for minimal latency — no polling loop.
	// Check bStopping in 1-second windows to stay responsive to shutdown.
	double Deadline = FPlatformTime::Seconds() + TimeoutSeconds;
	while (!bStopping)
	{
		double Remaining = Deadline - FPlatformTime::Seconds();
		if (Remaining <= 0.0)
		{
			return false;
		}

		// Wait up to 1s at a time so we can check bStopping between waits
		float WaitTime = FMath::Min(static_cast<float>(Remaining), 1.0f);
		if (Socket->Wait(ESocketWaitConditions::WaitForRead, FTimespan::FromSeconds(WaitTime)))
		{
			return true;
		}
	}
	return false;
}
