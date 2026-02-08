// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/QueryCommands.h"
#include "AudioMCPBuilderManager.h"
#include "AudioMCPTypes.h"
#include "MetasoundFrontendSearchEngine.h"
#include "MetasoundFrontendDocument.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

// ---------------------------------------------------------------------------
// get_graph_input_names
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FGetGraphInputNamesCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	TArray<FString> Names;
	FString Error;
	if (!BuilderManager.GetGraphInputNames(Names, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TArray<TSharedPtr<FJsonValue>> JsonNames;
	for (const FString& Name : Names)
	{
		JsonNames.Add(MakeShared<FJsonValueString>(Name));
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Found %d graph inputs"), Names.Num()));
	Response->SetArrayField(TEXT("names"), JsonNames);
	Response->SetNumberField(TEXT("count"), Names.Num());
	return Response;
}

// ---------------------------------------------------------------------------
// set_live_updates
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FSetLiveUpdatesCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	bool bEnabled = true;
	if (!Params->TryGetBoolField(TEXT("enabled"), bEnabled))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'enabled'"));
	}

	FString Error;
	if (!BuilderManager.SetLiveUpdates(bEnabled, Error))
	{
		return AudioMCP::MakeErrorResponse(Error);
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Live updates %s"), bEnabled ? TEXT("enabled") : TEXT("disabled")));
	Response->SetBoolField(TEXT("enabled"), bEnabled);
	return Response;
}

// ---------------------------------------------------------------------------
// list_node_classes
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FListNodeClassesCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	// Optional filter: only return nodes whose name contains this substring
	FString Filter;
	Params->TryGetStringField(TEXT("filter"), Filter);

	// Optional limit (default 200 to avoid huge responses)
	int32 Limit = 200;
	double LimitVal;
	if (Params->TryGetNumberField(TEXT("limit"), LimitVal))
	{
		Limit = FMath::Clamp(static_cast<int32>(LimitVal), 1, 5000);
	}

	Metasound::Frontend::ISearchEngine& SearchEngine = Metasound::Frontend::ISearchEngine::Get();
	SearchEngine.Prime();

	TArray<FMetasoundFrontendClass> AllClasses = SearchEngine.FindAllClasses(false /* bInIncludeAllVersions */);

	TArray<TSharedPtr<FJsonValue>> NodeArray;
	int32 TotalMatched = 0;

	for (const FMetasoundFrontendClass& FrontendClass : AllClasses)
	{
		const FMetasoundFrontendClassMetadata& Metadata = FrontendClass.Metadata;

		// Build the full class name string: "Namespace::Name::Variant"
		FString Namespace = Metadata.GetClassName().Namespace.ToString();
		FString Name = Metadata.GetClassName().Name.ToString();
		FString Variant = Metadata.GetClassName().Variant.ToString();

		FString FullName;
		if (Namespace.IsEmpty())
		{
			FullName = Variant.IsEmpty() ? Name : FString::Printf(TEXT("%s::%s"), *Name, *Variant);
		}
		else
		{
			FullName = Variant.IsEmpty()
				? FString::Printf(TEXT("%s::%s"), *Namespace, *Name)
				: FString::Printf(TEXT("%s::%s::%s"), *Namespace, *Name, *Variant);
		}

		// Apply filter if specified
		if (!Filter.IsEmpty() && !FullName.Contains(Filter, ESearchCase::IgnoreCase))
		{
			continue;
		}

		TotalMatched++;

		if (NodeArray.Num() < Limit)
		{
			TSharedPtr<FJsonObject> NodeObj = MakeShared<FJsonObject>();
			NodeObj->SetStringField(TEXT("class_name"), FullName);
			NodeObj->SetStringField(TEXT("namespace"), Namespace);
			NodeObj->SetStringField(TEXT("name"), Name);
			NodeObj->SetStringField(TEXT("variant"), Variant);
			NodeArray.Add(MakeShared<FJsonValueObject>(NodeObj));
		}
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Found %d node classes (%d shown)"), TotalMatched, NodeArray.Num()));
	Response->SetArrayField(TEXT("nodes"), NodeArray);
	Response->SetNumberField(TEXT("total"), TotalMatched);
	Response->SetNumberField(TEXT("shown"), NodeArray.Num());
	return Response;
}
