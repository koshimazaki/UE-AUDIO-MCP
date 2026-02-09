// Copyright UE Audio MCP Project. All Rights Reserved.

#include "Commands/QueryCommands.h"
#include "AudioMCPBuilderManager.h"
#include "AudioMCPTypes.h"
#include "MetasoundFrontendSearchEngine.h"
#include "MetasoundFrontendDocument.h"
#include "MetasoundDocumentInterface.h"
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

	// Build ClassID → ClassName lookup from document dependencies
	TMap<FGuid, FMetasoundFrontendClassName> ClassIdToName;
	for (const FMetasoundFrontendClass& Dep : Document.Dependencies)
	{
		ClassIdToName.Add(Dep.ID, Dep.Metadata.GetClassName());
	}

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
				EventName = CustomEvent->CustomFunctionName;
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
