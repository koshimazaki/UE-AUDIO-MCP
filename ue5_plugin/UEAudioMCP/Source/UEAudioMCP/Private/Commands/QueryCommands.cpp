// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/QueryCommands.h"
#include "AudioMCPBuilderManager.h"
#include "AudioMCPTypes.h"
#include "MetasoundFrontendSearchEngine.h"
#include "MetasoundFrontendDocument.h"
#include "MetasoundDocumentInterface.h"
#include "MetasoundSource.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

// Blueprint graph inspection
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "K2Node_CallFunction.h"
#include "K2Node_Event.h"
#include "K2Node_CustomEvent.h"
#include "K2Node_VariableGet.h"
#include "K2Node_VariableSet.h"
#include "K2Node_MacroInstance.h"
#include "K2Node_DynamicCast.h"

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
	// UE 5.7: RootGraph is FMetasoundFrontendGraphClass, use GetConstDefaultGraph()
	const FMetasoundFrontendGraph& Graph = Document.RootGraph.GetConstDefaultGraph();

	TArray<TSharedPtr<FJsonValue>> NodeArray;
	TArray<TSharedPtr<FJsonValue>> EdgeArray;

	// --- Document-level metadata: asset type + interfaces ---
	FString AssetType = TEXT("Unknown");
	if (Asset->IsA(UMetaSoundSource::StaticClass()))
	{
		AssetType = TEXT("Source");
	}
	else if (Asset->GetClass()->GetName().Contains(TEXT("Patch")))
	{
		AssetType = TEXT("Patch");
	}

	TArray<TSharedPtr<FJsonValue>> InterfaceArray;
	for (const FMetasoundFrontendVersion& Interface : Document.Interfaces)
	{
		FString InterfaceName = FString::Printf(TEXT("%s %d.%d"),
			*Interface.Name.ToString(), Interface.Number.Major, Interface.Number.Minor);
		InterfaceArray.Add(MakeShared<FJsonValueString>(InterfaceName));
	}

	// Build ClassID → ClassName lookup from document dependencies
	TMap<FGuid, FMetasoundFrontendClassName> ClassIdToName;
	for (const FMetasoundFrontendClass& Dep : Document.Dependencies)
	{
		ClassIdToName.Add(Dep.ID, Dep.Metadata.GetClassName());
	}

	// Build vertex ID → pin name lookup for edge resolution
	// Also build NodeID → node name lookup for human-readable edges
	TMap<FGuid, FString> VertexIdToPinName;
	TMap<FGuid, FString> NodeIdToName;
	for (const FMetasoundFrontendNode& Node : Graph.Nodes)
	{
		// Build display name for this node
		FString NodeDisplayName = Node.Name.ToString();
		if (const FMetasoundFrontendClassName* FoundName = ClassIdToName.Find(Node.ClassID))
		{
			NodeDisplayName = FoundName->Name.ToString();
		}
		NodeIdToName.Add(Node.GetID(), NodeDisplayName);

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

		// Class name: look up via ClassID in document dependencies
		FString Namespace;
		FString Name = Node.Name.ToString();
		FString Variant;

		if (const FMetasoundFrontendClassName* FoundName = ClassIdToName.Find(Node.ClassID))
		{
			Namespace = FoundName->Namespace.ToString();
			Name = FoundName->Name.ToString();
			Variant = FoundName->Variant.ToString();
		}

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

		// List input pins with data types and defaults
		TArray<TSharedPtr<FJsonValue>> InputPins;
		for (const FMetasoundFrontendVertex& Input : Node.Interface.Inputs)
		{
			TSharedPtr<FJsonObject> PinObj = MakeShared<FJsonObject>();
			PinObj->SetStringField(TEXT("name"), Input.Name.ToString());
			PinObj->SetStringField(TEXT("type"), Input.TypeName.ToString());

			// Extract default value from node input literals
			for (const FMetasoundFrontendVertexLiteral& Literal : Node.InputLiterals)
			{
				if (Literal.VertexID == Input.VertexID)
				{
					const FMetasoundFrontendLiteral& Lit = Literal.Value;
					FString DefaultStr;

					float FloatVal;
					int32 IntVal;
					bool BoolVal;
					FString StringVal;

					if (Lit.TryGet(FloatVal))
					{
						DefaultStr = FString::SanitizeFloat(FloatVal);
					}
					else if (Lit.TryGet(IntVal))
					{
						DefaultStr = FString::FromInt(IntVal);
					}
					else if (Lit.TryGet(BoolVal))
					{
						DefaultStr = BoolVal ? TEXT("true") : TEXT("false");
					}
					else if (Lit.TryGet(StringVal))
					{
						DefaultStr = StringVal;
					}

					if (!DefaultStr.IsEmpty())
					{
						PinObj->SetStringField(TEXT("default"), DefaultStr);
					}
					break;
				}
			}

			InputPins.Add(MakeShared<FJsonValueObject>(PinObj));
		}
		NodeObj->SetArrayField(TEXT("inputs"), InputPins);

		// List output pins with data types
		TArray<TSharedPtr<FJsonValue>> OutputPins;
		for (const FMetasoundFrontendVertex& Output : Node.Interface.Outputs)
		{
			TSharedPtr<FJsonObject> PinObj = MakeShared<FJsonObject>();
			PinObj->SetStringField(TEXT("name"), Output.Name.ToString());
			PinObj->SetStringField(TEXT("type"), Output.TypeName.ToString());
			OutputPins.Add(MakeShared<FJsonValueObject>(PinObj));
		}
		NodeObj->SetArrayField(TEXT("outputs"), OutputPins);

		NodeArray.Add(MakeShared<FJsonValueObject>(NodeObj));
	}

	// Read edges (connections) — resolve vertex GUIDs to pin names + node names
	for (const FMetasoundFrontendEdge& Edge : Graph.Edges)
	{
		TSharedPtr<FJsonObject> EdgeObj = MakeShared<FJsonObject>();
		EdgeObj->SetStringField(TEXT("from_node"), Edge.FromNodeID.ToString());
		EdgeObj->SetStringField(TEXT("to_node"), Edge.ToNodeID.ToString());

		// Add human-readable node names
		if (FString* FromName = NodeIdToName.Find(Edge.FromNodeID))
		{
			EdgeObj->SetStringField(TEXT("from_node_name"), *FromName);
		}
		if (FString* ToName = NodeIdToName.Find(Edge.ToNodeID))
		{
			EdgeObj->SetStringField(TEXT("to_node_name"), *ToName);
		}

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
	Response->SetStringField(TEXT("asset_type"), AssetType);
	Response->SetArrayField(TEXT("interfaces"), InterfaceArray);
	Response->SetArrayField(TEXT("nodes"), NodeArray);
	Response->SetArrayField(TEXT("edges"), EdgeArray);
	Response->SetStringField(TEXT("asset_path"), AssetPath);
	return Response;
}

// ---------------------------------------------------------------------------
// export_metasound — full graph export with types, defaults, variables, I/O
// ---------------------------------------------------------------------------

TSharedPtr<FJsonObject> FExportMetaSoundCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	FString AssetPath;
	if (!Params->TryGetStringField(TEXT("asset_path"), AssetPath))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'asset_path'"));
	}

	if (!AssetPath.StartsWith(TEXT("/Game/")) && !AssetPath.StartsWith(TEXT("/Engine/")))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Asset path must start with /Game/ or /Engine/ (got '%s')"), *AssetPath));
	}
	if (AssetPath.Contains(TEXT("..")))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Asset path must not contain '..'"));
	}

	UObject* Asset = StaticLoadObject(UObject::StaticClass(), nullptr, *AssetPath);
	if (!Asset)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Could not load asset '%s'"), *AssetPath));
	}

	TScriptInterface<IMetaSoundDocumentInterface> DocInterface(Asset);
	if (!DocInterface.GetInterface())
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Asset '%s' is not a MetaSound"), *AssetPath));
	}

	const FMetasoundFrontendDocument& Document = DocInterface->GetConstDocument();
	const FMetasoundFrontendGraph& Graph = Document.RootGraph.GetConstDefaultGraph();

	// --- Asset type ---
	FString AssetType = TEXT("Unknown");
	if (Asset->IsA(UMetaSoundSource::StaticClass()))
	{
		AssetType = TEXT("Source");
	}
	else if (Asset->GetClass()->GetName().Contains(TEXT("Patch")))
	{
		AssetType = TEXT("Patch");
	}

	// --- Is preset ---
	bool bIsPreset = Document.RootGraph.PresetOptions.bIsPreset;

	// --- Interfaces ---
	TArray<TSharedPtr<FJsonValue>> InterfaceArray;
	for (const FMetasoundFrontendVersion& Interface : Document.Interfaces)
	{
		InterfaceArray.Add(MakeShared<FJsonValueString>(Interface.Name.ToString()));
	}

	// --- Graph-level I/O from RootGraph interface ---
	TArray<TSharedPtr<FJsonValue>> GraphInputsArray;
	for (const FMetasoundFrontendClassInput& ClassInput : Document.RootGraph.Interface.Inputs)
	{
		TSharedPtr<FJsonObject> InputObj = MakeShared<FJsonObject>();
		InputObj->SetStringField(TEXT("name"), ClassInput.Name.ToString());
		InputObj->SetStringField(TEXT("type"), ClassInput.TypeName.ToString());

		// Extract default literal
		const FMetasoundFrontendLiteral& Lit = ClassInput.Default;
		float FloatVal; int32 IntVal; bool BoolVal; FString StringVal;
		if (Lit.TryGet(FloatVal))
		{
			InputObj->SetNumberField(TEXT("default"), FloatVal);
		}
		else if (Lit.TryGet(IntVal))
		{
			InputObj->SetNumberField(TEXT("default"), IntVal);
		}
		else if (Lit.TryGet(BoolVal))
		{
			InputObj->SetBoolField(TEXT("default"), BoolVal);
		}
		else if (Lit.TryGet(StringVal) && !StringVal.IsEmpty())
		{
			InputObj->SetStringField(TEXT("default"), StringVal);
		}

		GraphInputsArray.Add(MakeShared<FJsonValueObject>(InputObj));
	}

	TArray<TSharedPtr<FJsonValue>> GraphOutputsArray;
	for (const FMetasoundFrontendClassOutput& ClassOutput : Document.RootGraph.Interface.Outputs)
	{
		TSharedPtr<FJsonObject> OutputObj = MakeShared<FJsonObject>();
		OutputObj->SetStringField(TEXT("name"), ClassOutput.Name.ToString());
		OutputObj->SetStringField(TEXT("type"), ClassOutput.TypeName.ToString());
		GraphOutputsArray.Add(MakeShared<FJsonValueObject>(OutputObj));
	}

	// --- Graph variables ---
	TArray<TSharedPtr<FJsonValue>> VariablesArray;
	for (const FMetasoundFrontendVariable& Var : Graph.Variables)
	{
		TSharedPtr<FJsonObject> VarObj = MakeShared<FJsonObject>();
		VarObj->SetStringField(TEXT("name"), Var.Name.ToString());
		VarObj->SetStringField(TEXT("type"), Var.TypeName.ToString());
		VarObj->SetStringField(TEXT("id"), Var.ID.ToString());

		// Variable default literal
		const FMetasoundFrontendLiteral& VLit = Var.Literal;
		float VFloat; int32 VInt; bool VBool; FString VString;
		if (VLit.TryGet(VFloat))
		{
			VarObj->SetNumberField(TEXT("default"), VFloat);
		}
		else if (VLit.TryGet(VInt))
		{
			VarObj->SetNumberField(TEXT("default"), VInt);
		}
		else if (VLit.TryGet(VBool))
		{
			VarObj->SetBoolField(TEXT("default"), VBool);
		}
		else if (VLit.TryGet(VString) && !VString.IsEmpty())
		{
			VarObj->SetStringField(TEXT("default"), VString);
		}

		VariablesArray.Add(MakeShared<FJsonValueObject>(VarObj));
	}

	// --- Build ClassID → ClassName + ClassType lookups ---
	TMap<FGuid, FMetasoundFrontendClassName> ClassIdToName;
	TMap<FGuid, FString> ClassIdToType;
	for (const FMetasoundFrontendClass& Dep : Document.Dependencies)
	{
		ClassIdToName.Add(Dep.ID, Dep.Metadata.GetClassName());

		EMetasoundFrontendClassType ClassType = Dep.Metadata.GetType();
		FString TypeStr;
		switch (ClassType)
		{
		case EMetasoundFrontendClassType::External:  TypeStr = TEXT("External"); break;
		case EMetasoundFrontendClassType::Input:     TypeStr = TEXT("Input"); break;
		case EMetasoundFrontendClassType::Output:    TypeStr = TEXT("Output"); break;
		case EMetasoundFrontendClassType::Variable:  TypeStr = TEXT("Variable"); break;
		case EMetasoundFrontendClassType::VariableDeferredAccessor: TypeStr = TEXT("VariableDeferred"); break;
		case EMetasoundFrontendClassType::VariableAccessor: TypeStr = TEXT("VariableAccessor"); break;
		case EMetasoundFrontendClassType::VariableMutator:  TypeStr = TEXT("VariableMutator"); break;
		default: TypeStr = TEXT("Unknown"); break;
		}
		ClassIdToType.Add(Dep.ID, TypeStr);
	}

	// --- Build vertex ID → pin name lookup for edges ---
	TMap<FGuid, FString> VertexIdToPinName;
	TMap<FGuid, FString> NodeIdToName;

	for (const FMetasoundFrontendNode& Node : Graph.Nodes)
	{
		FString NodeDisplayName = Node.Name.ToString();
		if (const FMetasoundFrontendClassName* FoundName = ClassIdToName.Find(Node.ClassID))
		{
			NodeDisplayName = FoundName->Name.ToString();
		}
		NodeIdToName.Add(Node.GetID(), NodeDisplayName);

		for (const FMetasoundFrontendVertex& Input : Node.Interface.Inputs)
		{
			VertexIdToPinName.Add(Input.VertexID, Input.Name.ToString());
		}
		for (const FMetasoundFrontendVertex& Output : Node.Interface.Outputs)
		{
			VertexIdToPinName.Add(Output.VertexID, Output.Name.ToString());
		}
	}

	// --- Nodes ---
	TArray<TSharedPtr<FJsonValue>> NodeArray;
	for (const FMetasoundFrontendNode& Node : Graph.Nodes)
	{
		TSharedPtr<FJsonObject> NodeObj = MakeShared<FJsonObject>();
		NodeObj->SetStringField(TEXT("node_id"), Node.GetID().ToString());

		// Class name
		FString Namespace, Name = Node.Name.ToString(), Variant;
		if (const FMetasoundFrontendClassName* FoundName = ClassIdToName.Find(Node.ClassID))
		{
			Namespace = FoundName->Namespace.ToString();
			Name = FoundName->Name.ToString();
			Variant = FoundName->Variant.ToString();
		}

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

		// Class type
		if (FString* TypeStr = ClassIdToType.Find(Node.ClassID))
		{
			NodeObj->SetStringField(TEXT("class_type"), *TypeStr);
		}

		// Position
		const TMap<FGuid, FVector2D>& Locations = Node.Style.Display.Locations;
		if (Locations.Num() > 0)
		{
			for (const auto& Pair : Locations)
			{
				NodeObj->SetNumberField(TEXT("x"), Pair.Value.X);
				NodeObj->SetNumberField(TEXT("y"), Pair.Value.Y);
				break;
			}
		}

		// Comment
		if (!Node.Style.Display.Comment.IsEmpty())
		{
			NodeObj->SetStringField(TEXT("comment"), Node.Style.Display.Comment);
		}

		// Input pins with types and defaults
		TArray<TSharedPtr<FJsonValue>> InputPins;
		for (const FMetasoundFrontendVertex& Input : Node.Interface.Inputs)
		{
			TSharedPtr<FJsonObject> PinObj = MakeShared<FJsonObject>();
			PinObj->SetStringField(TEXT("name"), Input.Name.ToString());
			PinObj->SetStringField(TEXT("type"), Input.TypeName.ToString());

			for (const FMetasoundFrontendVertexLiteral& Literal : Node.InputLiterals)
			{
				if (Literal.VertexID == Input.VertexID)
				{
					const FMetasoundFrontendLiteral& Lit = Literal.Value;
					float FVal; int32 IVal; bool BVal; FString SVal;
					if (Lit.TryGet(FVal))
					{
						PinObj->SetNumberField(TEXT("default"), FVal);
					}
					else if (Lit.TryGet(IVal))
					{
						PinObj->SetNumberField(TEXT("default"), IVal);
					}
					else if (Lit.TryGet(BVal))
					{
						PinObj->SetBoolField(TEXT("default"), BVal);
					}
					else if (Lit.TryGet(SVal) && !SVal.IsEmpty())
					{
						PinObj->SetStringField(TEXT("default"), SVal);
					}
					break;
				}
			}

			InputPins.Add(MakeShared<FJsonValueObject>(PinObj));
		}
		NodeObj->SetArrayField(TEXT("inputs"), InputPins);

		// Output pins with types
		TArray<TSharedPtr<FJsonValue>> OutputPins;
		for (const FMetasoundFrontendVertex& Output : Node.Interface.Outputs)
		{
			TSharedPtr<FJsonObject> PinObj = MakeShared<FJsonObject>();
			PinObj->SetStringField(TEXT("name"), Output.Name.ToString());
			PinObj->SetStringField(TEXT("type"), Output.TypeName.ToString());
			OutputPins.Add(MakeShared<FJsonValueObject>(PinObj));
		}
		NodeObj->SetArrayField(TEXT("outputs"), OutputPins);

		NodeArray.Add(MakeShared<FJsonValueObject>(NodeObj));
	}

	// --- Edges ---
	TArray<TSharedPtr<FJsonValue>> EdgeArray;
	for (const FMetasoundFrontendEdge& Edge : Graph.Edges)
	{
		TSharedPtr<FJsonObject> EdgeObj = MakeShared<FJsonObject>();
		EdgeObj->SetStringField(TEXT("from_node"), Edge.FromNodeID.ToString());
		EdgeObj->SetStringField(TEXT("to_node"), Edge.ToNodeID.ToString());

		if (FString* FromName = NodeIdToName.Find(Edge.FromNodeID))
		{
			EdgeObj->SetStringField(TEXT("from_node_name"), *FromName);
		}
		if (FString* ToName = NodeIdToName.Find(Edge.ToNodeID))
		{
			EdgeObj->SetStringField(TEXT("to_node_name"), *ToName);
		}

		FString* FromPinName = VertexIdToPinName.Find(Edge.FromVertexID);
		EdgeObj->SetStringField(TEXT("from_pin"),
			FromPinName ? *FromPinName : Edge.FromVertexID.ToString());

		FString* ToPinName = VertexIdToPinName.Find(Edge.ToVertexID);
		EdgeObj->SetStringField(TEXT("to_pin"),
			ToPinName ? *ToPinName : Edge.ToVertexID.ToString());

		EdgeArray.Add(MakeShared<FJsonValueObject>(EdgeObj));
	}

	// --- Response ---
	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Exported '%s': %d nodes, %d edges, %d vars, %d interfaces"),
			*AssetPath, NodeArray.Num(), EdgeArray.Num(),
			VariablesArray.Num(), InterfaceArray.Num()));
	Response->SetStringField(TEXT("asset_path"), AssetPath);
	Response->SetStringField(TEXT("asset_type"), AssetType);
	Response->SetBoolField(TEXT("is_preset"), bIsPreset);
	Response->SetArrayField(TEXT("interfaces"), InterfaceArray);
	Response->SetArrayField(TEXT("graph_inputs"), GraphInputsArray);
	Response->SetArrayField(TEXT("graph_outputs"), GraphOutputsArray);
	Response->SetArrayField(TEXT("variables"), VariablesArray);
	Response->SetArrayField(TEXT("nodes"), NodeArray);
	Response->SetArrayField(TEXT("edges"), EdgeArray);
	return Response;
}

// ---------------------------------------------------------------------------
// scan_blueprint — deep-scan Blueprint graph nodes for function calls & audio
// ---------------------------------------------------------------------------

// Audio relevance check now lives in AudioMCPTypes.h → AudioMCP::IsAudioRelevant()

TSharedPtr<FJsonObject> FScanBlueprintCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	// --- 1. Extract params ---
	FString AssetPath;
	if (!Params->TryGetStringField(TEXT("asset_path"), AssetPath))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Missing required param 'asset_path'"));
	}

	bool bAudioOnly = false;
	Params->TryGetBoolField(TEXT("audio_only"), bAudioOnly);

	bool bIncludePins = false;
	Params->TryGetBoolField(TEXT("include_pins"), bIncludePins);

	// --- 2. Validate path ---
	if (!AssetPath.StartsWith(TEXT("/Game/")) && !AssetPath.StartsWith(TEXT("/Engine/")))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Asset path must start with /Game/ or /Engine/ (got '%s')"), *AssetPath));
	}
	if (AssetPath.Contains(TEXT("..")))
	{
		return AudioMCP::MakeErrorResponse(TEXT("Asset path must not contain '..'"));
	}

	// --- 3. Load Blueprint ---
	UObject* Asset = StaticLoadObject(UObject::StaticClass(), nullptr, *AssetPath);
	if (!Asset)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Could not load asset '%s'"), *AssetPath));
	}

	UBlueprint* BP = Cast<UBlueprint>(Asset);
	if (!BP)
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Asset '%s' is not a Blueprint (class: %s)"),
				*AssetPath, *Asset->GetClass()->GetName()));
	}

	// --- 4. Blueprint metadata ---
	FString BPName = BP->GetName();
	FString ParentClass = BP->ParentClass ? BP->ParentClass->GetName() : TEXT("None");
	FString BlueprintType = BP->GetClass()->GetName();

	// --- 5. Collect graphs ---
	struct FGraphEntry
	{
		FString Type;
		UEdGraph* Graph;
	};
	TArray<FGraphEntry> AllGraphs;

	for (UEdGraph* Graph : BP->UbergraphPages)
	{
		if (Graph) AllGraphs.Add({TEXT("ubergraph"), Graph});
	}
	for (UEdGraph* Graph : BP->FunctionGraphs)
	{
		if (Graph) AllGraphs.Add({TEXT("function"), Graph});
	}
	for (UEdGraph* Graph : BP->MacroGraphs)
	{
		if (Graph) AllGraphs.Add({TEXT("macro"), Graph});
	}

	// --- 6. Iterate graphs and nodes ---
	TArray<TSharedPtr<FJsonValue>> GraphsArray;
	TArray<FString> AudioFunctions;
	int32 TotalNodes = 0;
	int32 AudioNodeCount = 0;

	for (const FGraphEntry& Entry : AllGraphs)
	{
		UEdGraph* Graph = Entry.Graph;
		TArray<TSharedPtr<FJsonValue>> NodesArray;

		for (UEdGraphNode* Node : Graph->Nodes)
		{
			if (!Node) continue;
			TotalNodes++;

			// Classify node
			FString NodeType;
			FString FuncName;
			FString FuncClass;
			FString EventName;
			FString VarName;
			FString MacroName;
			FString CastTarget;
			bool bNodeAudioRelevant = false;

			if (UK2Node_CallFunction* CallNode = Cast<UK2Node_CallFunction>(Node))
			{
				NodeType = TEXT("CallFunction");
				FuncName = CallNode->FunctionReference.GetMemberName().ToString();

				UFunction* TargetFunc = CallNode->GetTargetFunction();
				if (TargetFunc && TargetFunc->GetOwnerClass())
				{
					FuncClass = TargetFunc->GetOwnerClass()->GetName();
				}

				bNodeAudioRelevant = AudioMCP::IsAudioRelevant(FuncName) || AudioMCP::IsAudioRelevant(FuncClass);
				if (bNodeAudioRelevant && !AudioFunctions.Contains(FuncName))
				{
					AudioFunctions.Add(FuncName);
				}
			}
			else if (UK2Node_CustomEvent* CustomEvent = Cast<UK2Node_CustomEvent>(Node))
			{
				NodeType = TEXT("CustomEvent");
				EventName = CustomEvent->CustomFunctionName.ToString();
				bNodeAudioRelevant = AudioMCP::IsAudioRelevant(EventName);
			}
			else if (UK2Node_Event* EventNode = Cast<UK2Node_Event>(Node))
			{
				NodeType = TEXT("Event");
				EventName = EventNode->EventReference.GetMemberName().ToString();
				bNodeAudioRelevant = AudioMCP::IsAudioRelevant(EventName);
			}
			else if (UK2Node_VariableGet* VarGet = Cast<UK2Node_VariableGet>(Node))
			{
				NodeType = TEXT("VariableGet");
				VarName = VarGet->GetVarName().ToString();
				bNodeAudioRelevant = AudioMCP::IsAudioRelevant(VarName);
			}
			else if (UK2Node_VariableSet* VarSet = Cast<UK2Node_VariableSet>(Node))
			{
				NodeType = TEXT("VariableSet");
				VarName = VarSet->GetVarName().ToString();
				bNodeAudioRelevant = AudioMCP::IsAudioRelevant(VarName);
			}
			else if (UK2Node_MacroInstance* Macro = Cast<UK2Node_MacroInstance>(Node))
			{
				NodeType = TEXT("MacroInstance");
				UEdGraph* MacroGraph = Macro->GetMacroGraph();
				MacroName = MacroGraph ? MacroGraph->GetName() : TEXT("Unknown");
				bNodeAudioRelevant = AudioMCP::IsAudioRelevant(MacroName);
			}
			else if (UK2Node_DynamicCast* CastNode = Cast<UK2Node_DynamicCast>(Node))
			{
				NodeType = TEXT("Cast");
				CastTarget = CastNode->TargetType ? CastNode->TargetType->GetName() : TEXT("Unknown");
				bNodeAudioRelevant = AudioMCP::IsAudioRelevant(CastTarget);
			}
			else
			{
				NodeType = Node->GetClass()->GetName();
			}

			if (bNodeAudioRelevant) AudioNodeCount++;

			// Skip non-audio nodes when audio_only filter is active
			if (bAudioOnly && !bNodeAudioRelevant) continue;

			// Build node JSON
			TSharedPtr<FJsonObject> NodeObj = MakeShared<FJsonObject>();
			NodeObj->SetStringField(TEXT("type"), NodeType);
			NodeObj->SetStringField(TEXT("title"),
				Node->GetNodeTitle(ENodeTitleType::ListView).ToString());

			if (!FuncName.IsEmpty())
			{
				NodeObj->SetStringField(TEXT("function_name"), FuncName);
				if (!FuncClass.IsEmpty())
				{
					NodeObj->SetStringField(TEXT("function_class"), FuncClass);
				}
			}
			if (!EventName.IsEmpty())
			{
				NodeObj->SetStringField(TEXT("event_name"), EventName);
			}
			if (!VarName.IsEmpty())
			{
				NodeObj->SetStringField(TEXT("variable_name"), VarName);
			}
			if (!MacroName.IsEmpty())
			{
				NodeObj->SetStringField(TEXT("macro_name"), MacroName);
			}
			if (!CastTarget.IsEmpty())
			{
				NodeObj->SetStringField(TEXT("cast_target"), CastTarget);
			}

			NodeObj->SetBoolField(TEXT("audio_relevant"), bNodeAudioRelevant);
			NodeObj->SetNumberField(TEXT("x"), Node->NodePosX);
			NodeObj->SetNumberField(TEXT("y"), Node->NodePosY);

			if (!Node->NodeComment.IsEmpty())
			{
				NodeObj->SetStringField(TEXT("comment"), Node->NodeComment);
			}

			// Optional pin details
			if (bIncludePins)
			{
				TArray<TSharedPtr<FJsonValue>> PinsArray;
				for (const UEdGraphPin* Pin : Node->Pins)
				{
					if (!Pin) continue;

					TSharedPtr<FJsonObject> PinObj = MakeShared<FJsonObject>();
					PinObj->SetStringField(TEXT("name"), Pin->PinName.ToString());
					PinObj->SetStringField(TEXT("direction"),
						Pin->Direction == EEdGraphPinDirection::EGPD_Input
							? TEXT("input") : TEXT("output"));
					PinObj->SetStringField(TEXT("type"),
						Pin->PinType.PinCategory.ToString());

					if (Pin->PinType.PinSubCategoryObject.IsValid())
					{
						PinObj->SetStringField(TEXT("sub_type"),
							Pin->PinType.PinSubCategoryObject->GetName());
					}

					if (!Pin->DefaultValue.IsEmpty())
					{
						PinObj->SetStringField(TEXT("default"), Pin->DefaultValue);
					}

					PinObj->SetBoolField(TEXT("connected"), Pin->LinkedTo.Num() > 0);
					PinObj->SetNumberField(TEXT("link_count"), Pin->LinkedTo.Num());

					PinsArray.Add(MakeShared<FJsonValueObject>(PinObj));
				}
				NodeObj->SetArrayField(TEXT("pins"), PinsArray);
			}

			NodesArray.Add(MakeShared<FJsonValueObject>(NodeObj));
		}

		// Build graph JSON
		TSharedPtr<FJsonObject> GraphObj = MakeShared<FJsonObject>();
		GraphObj->SetStringField(TEXT("name"), Graph->GetName());
		GraphObj->SetStringField(TEXT("type"), Entry.Type);
		GraphObj->SetNumberField(TEXT("total_nodes"), Graph->Nodes.Num());
		GraphObj->SetNumberField(TEXT("shown_nodes"), NodesArray.Num());
		GraphObj->SetArrayField(TEXT("nodes"), NodesArray);

		GraphsArray.Add(MakeShared<FJsonValueObject>(GraphObj));
	}

	// --- 7. Audio summary ---
	TSharedPtr<FJsonObject> AudioSummary = MakeShared<FJsonObject>();
	AudioSummary->SetBoolField(TEXT("has_audio"), AudioNodeCount > 0);
	AudioSummary->SetNumberField(TEXT("audio_node_count"), AudioNodeCount);

	TArray<TSharedPtr<FJsonValue>> FuncArray;
	for (const FString& Func : AudioFunctions)
	{
		FuncArray.Add(MakeShared<FJsonValueString>(Func));
	}
	AudioSummary->SetArrayField(TEXT("audio_functions"), FuncArray);

	// --- 8. Response ---
	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Scanned '%s': %d graphs, %d nodes (%d audio-relevant)"),
			*BPName, GraphsArray.Num(), TotalNodes, AudioNodeCount));
	Response->SetStringField(TEXT("asset_path"), AssetPath);
	Response->SetStringField(TEXT("blueprint_name"), BPName);
	Response->SetStringField(TEXT("parent_class"), ParentClass);
	Response->SetStringField(TEXT("blueprint_type"), BlueprintType);
	Response->SetNumberField(TEXT("total_nodes"), TotalNodes);
	Response->SetArrayField(TEXT("graphs"), GraphsArray);
	Response->SetObjectField(TEXT("audio_summary"), AudioSummary);
	return Response;
}

// ---------------------------------------------------------------------------
// list_assets — query Asset Registry for assets by class and path
// ---------------------------------------------------------------------------

#include "AssetRegistry/AssetRegistryModule.h"

namespace
{
	/** Map short class names to full FTopLevelAssetPath. */
	bool ResolveClassPath(const FString& ShortName, FTopLevelAssetPath& OutPath)
	{
		struct FClassEntry { const TCHAR* Name; const TCHAR* Package; const TCHAR* Asset; };
		static const FClassEntry Map[] = {
			{ TEXT("Blueprint"),          TEXT("/Script/Engine"),           TEXT("Blueprint") },
			{ TEXT("WidgetBlueprint"),    TEXT("/Script/UMGEditor"),       TEXT("WidgetBlueprint") },
			{ TEXT("AnimBlueprint"),      TEXT("/Script/Engine"),           TEXT("AnimBlueprint") },
			{ TEXT("MetaSoundSource"),    TEXT("/Script/MetasoundEngine"), TEXT("MetaSoundSource") },
			{ TEXT("MetaSoundPatch"),     TEXT("/Script/MetasoundEngine"), TEXT("MetaSoundPatch") },
			{ TEXT("SoundWave"),          TEXT("/Script/Engine"),           TEXT("SoundWave") },
			{ TEXT("SoundCue"),           TEXT("/Script/Engine"),           TEXT("SoundCue") },
			{ TEXT("SoundAttenuation"),   TEXT("/Script/Engine"),           TEXT("SoundAttenuation") },
			{ TEXT("SoundClass"),         TEXT("/Script/Engine"),           TEXT("SoundClass") },
			{ TEXT("SoundConcurrency"),   TEXT("/Script/Engine"),           TEXT("SoundConcurrency") },
			{ TEXT("SoundMix"),           TEXT("/Script/Engine"),           TEXT("SoundMix") },
			{ TEXT("ReverbEffect"),       TEXT("/Script/Engine"),           TEXT("ReverbEffect") },
		};

		for (const FClassEntry& Entry : Map)
		{
			if (ShortName.Equals(Entry.Name, ESearchCase::IgnoreCase))
			{
				OutPath = FTopLevelAssetPath(Entry.Package, Entry.Asset);
				return true;
			}
		}
		return false;
	}
}

TSharedPtr<FJsonObject> FListAssetsCommand::Execute(
	const TSharedPtr<FJsonObject>& Params,
	FAudioMCPBuilderManager& BuilderManager)
{
	// --- Params ---
	FString ClassFilter;
	Params->TryGetStringField(TEXT("class_filter"), ClassFilter);

	FString Path = TEXT("/Game/");
	Params->TryGetStringField(TEXT("path"), Path);

	bool bRecursiveClasses = true;
	Params->TryGetBoolField(TEXT("recursive_classes"), bRecursiveClasses);

	int32 Limit = 5000;
	double LimitVal;
	if (Params->TryGetNumberField(TEXT("limit"), LimitVal))
	{
		Limit = FMath::Clamp(static_cast<int32>(LimitVal), 1, 50000);
	}

	// --- Validate path ---
	if (!Path.StartsWith(TEXT("/Game/")) && !Path.StartsWith(TEXT("/Engine/")))
	{
		return AudioMCP::MakeErrorResponse(
			FString::Printf(TEXT("Path must start with /Game/ or /Engine/ (got '%s')"), *Path));
	}

	// --- Build filter ---
	IAssetRegistry& Registry =
		FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry").Get();

	FARFilter Filter;
	Filter.PackagePaths.Add(FName(*Path));
	Filter.bRecursivePaths = true;
	Filter.bRecursiveClasses = bRecursiveClasses;

	if (!ClassFilter.IsEmpty())
	{
		FTopLevelAssetPath ClassPath;
		if (ResolveClassPath(ClassFilter, ClassPath))
		{
			Filter.ClassPaths.Add(ClassPath);
		}
		else
		{
			return AudioMCP::MakeErrorResponse(
				FString::Printf(TEXT("Unknown class_filter '%s'. Supported: Blueprint, WidgetBlueprint, "
					"AnimBlueprint, MetaSoundSource, MetaSoundPatch, SoundWave, SoundCue, "
					"SoundAttenuation, SoundClass, SoundConcurrency, SoundMix, ReverbEffect"),
					*ClassFilter));
		}
	}

	// --- Query ---
	TArray<FAssetData> Assets;
	Registry.GetAssets(Filter, Assets);

	// --- Build response ---
	TArray<TSharedPtr<FJsonValue>> AssetArray;
	int32 Shown = 0;

	for (const FAssetData& Asset : Assets)
	{
		if (Shown >= Limit) break;

		TSharedPtr<FJsonObject> AssetObj = MakeShared<FJsonObject>();
		AssetObj->SetStringField(TEXT("path"), Asset.GetObjectPathString());
		AssetObj->SetStringField(TEXT("name"), Asset.AssetName.ToString());
		AssetObj->SetStringField(TEXT("class"),
			Asset.AssetClassPath.GetAssetName().ToString());
		AssetObj->SetStringField(TEXT("package_path"), Asset.PackagePath.ToString());

		AssetArray.Add(MakeShared<FJsonValueObject>(AssetObj));
		Shown++;
	}

	TSharedPtr<FJsonObject> Response = AudioMCP::MakeOkResponse(
		FString::Printf(TEXT("Found %d %s assets under '%s' (%d shown)"),
			Assets.Num(),
			ClassFilter.IsEmpty() ? TEXT("") : *ClassFilter,
			*Path, Shown));
	Response->SetArrayField(TEXT("assets"), AssetArray);
	Response->SetNumberField(TEXT("total"), Assets.Num());
	Response->SetNumberField(TEXT("shown"), Shown);
	Response->SetStringField(TEXT("path"), Path);
	if (!ClassFilter.IsEmpty())
	{
		Response->SetStringField(TEXT("class_filter"), ClassFilter);
	}
	return Response;
}
