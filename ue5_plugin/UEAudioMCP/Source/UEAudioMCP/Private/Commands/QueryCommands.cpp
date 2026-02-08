// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/QueryCommands.h"
#include "AudioMCPBuilderManager.h"
#include "AudioMCPTypes.h"
#include "MetasoundFrontendSearchEngine.h"
#include "MetasoundFrontendDocument.h"
#include "MetasoundDocumentInterface.h"
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

// ---------------------------------------------------------------------------
// get_node_locations — read node positions from a saved MetaSound asset
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FGetNodeLocationsCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString AssetPath;
	if (!Params->TryGetStringField(TEXT("asset_path"), AssetPath))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'asset_path'"));
	}

	// Validate asset path
	if (!AssetPath.StartsWith(TEXT("/Game/")) && !AssetPath.StartsWith(TEXT("/Engine/")))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Asset path must start with /Game/ or /Engine/ (got '%s')"), *AssetPath));
	}
	if (AssetPath.Contains(TEXT("..")))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Asset path must not contain '..'"));
	}

	// Load the MetaSound asset
	UObject* Asset = StaticLoadObject(UObject::StaticClass(), nullptr, *AssetPath);
	if (!Asset)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Could not load asset '%s'"), *AssetPath));
	}

	// Get the MetaSound document interface
	TScriptInterface<IMetaSoundDocumentInterface> DocInterface(Asset);
	if (!DocInterface.GetInterface())
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Asset '%s' is not a MetaSound"), *AssetPath));
	}

	// Access the frontend document (read-only)
	const FMetasoundFrontendDocument& Document = DocInterface->GetConstDocument();
	const FMetasoundFrontendGraph& Graph = Document.RootGraph;

	TArray<TSharedPtr<FJsonValue>> NodeArray;
	TArray<TSharedPtr<FJsonValue>> EdgeArray;

	// Build vertex ID → pin name lookup for edge resolution
	// VertexIDs are globally unique within a MetaSound document
	TMap<FGuid, FString> VertexIdToPinName;
	for (const FMetasoundFrontendNode& Node : Graph.Nodes)
	{
		for (const FMetasoundFrontendVertex& Input : Node.Interface.Inputs)
		{
			VertexIdToPinName.Add(Input.VertexID, Input.Name.ToString());
		}
		for (const FMetasoundFrontendVertex& Output : Node.Interface.Outputs)
		{
			VertexIdToPinName.Add(Output.VertexID, Output.Name.ToString());
		}
	}

	for (const FMetasoundFrontendNode& Node : Graph.Nodes)
	{
		TSharedPtr<FJsonObject> NodeObj = MakeShared<FJsonObject>();

		// Node identity
		NodeObj->SetStringField(TEXT("node_id"), Node.GetID().ToString());

		// Class name: Namespace::Name::Variant
		const FMetasoundFrontendClassName& ClassName = Node.ClassMetadata.GetClassName();
		FString Namespace = ClassName.Namespace.ToString();
		FString Name = ClassName.Name.ToString();
		FString Variant = ClassName.Variant.ToString();

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
		NodeObj->SetStringField(TEXT("class_name"), FullName);
		NodeObj->SetStringField(TEXT("name"), Node.Name.ToString());

		// Position from Style.Display.Locations map
		// Key is a GUID (editor instance), value is FVector2D
		double PosX = 0.0;
		double PosY = 0.0;
		bool bHasPosition = false;

		const TMap<FGuid, FVector2D>& Locations = Node.Style.Display.Locations;
		if (Locations.Num() > 0)
		{
			// Take the first location entry (typically only one per node)
			for (const auto& Pair : Locations)
			{
				PosX = Pair.Value.X;
				PosY = Pair.Value.Y;
				bHasPosition = true;
				break;
			}
		}

		NodeObj->SetNumberField(TEXT("x"), PosX);
		NodeObj->SetNumberField(TEXT("y"), PosY);
		NodeObj->SetBoolField(TEXT("has_position"), bHasPosition);

		// List input pin names
		TArray<TSharedPtr<FJsonValue>> InputPins;
		for (const FMetasoundFrontendVertex& Input : Node.Interface.Inputs)
		{
			InputPins.Add(MakeShared<FJsonValueString>(Input.Name.ToString()));
		}
		NodeObj->SetArrayField(TEXT("inputs"), InputPins);

		// List output pin names
		TArray<TSharedPtr<FJsonValue>> OutputPins;
		for (const FMetasoundFrontendVertex& Output : Node.Interface.Outputs)
		{
			OutputPins.Add(MakeShared<FJsonValueString>(Output.Name.ToString()));
		}
		NodeObj->SetArrayField(TEXT("outputs"), OutputPins);

		NodeArray.Add(MakeShared<FJsonValueObject>(NodeObj));
	}

	// Read edges (connections) — resolve vertex GUIDs to pin names
	for (const FMetasoundFrontendEdge& Edge : Graph.Edges)
	{
		TSharedPtr<FJsonObject> EdgeObj = MakeShared<FJsonObject>();
		EdgeObj->SetStringField(TEXT("from_node"), Edge.FromNodeID.ToString());
		EdgeObj->SetStringField(TEXT("to_node"), Edge.ToNodeID.ToString());

		// Resolve vertex IDs to human-readable pin names
		FString* FromPinName = VertexIdToPinName.Find(Edge.FromVertexID);
		EdgeObj->SetStringField(TEXT("from_pin"),
			FromPinName ? *FromPinName : Edge.FromVertexID.ToString());

		FString* ToPinName = VertexIdToPinName.Find(Edge.ToVertexID);
		EdgeObj->SetStringField(TEXT("to_pin"),
			ToPinName ? *ToPinName : Edge.ToVertexID.ToString());

		EdgeArray.Add(MakeShared<FJsonValueObject>(EdgeObj));
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Read %d nodes, %d edges from '%s'"),
			NodeArray.Num(), EdgeArray.Num(), *AssetPath));
	Response->SetArrayField(TEXT("nodes"), NodeArray);
	Response->SetArrayField(TEXT("edges"), EdgeArray);
	Response->SetStringField(TEXT("asset_path"), AssetPath);
	return Response;
}
