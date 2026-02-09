// Copyright UE Audio MCP Project. All Rights Reserved.

#include "AudioMCPEditorMenu.h"
#include "AudioMCPTypes.h"
#include "Commands/QueryCommands.h"
#include "AudioMCPBuilderManager.h"

#include "ToolMenus.h"
#include "Misc/ScopedSlowTask.h"
#include "Misc/FileHelper.h"
#include "HAL/PlatformProcess.h"
#include "HAL/PlatformFileManager.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/Blueprint.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "K2Node_CallFunction.h"
#include "K2Node_Event.h"
#include "K2Node_CustomEvent.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Framework/Notifications/NotificationManager.h"
#include "Widgets/Notifications/SNotificationList.h"
#include "ContentBrowserModule.h"
#include "IContentBrowserSingleton.h"

#define LOCTEXT_NAMESPACE "AudioMCPEditor"

DEFINE_LOG_CATEGORY_STATIC(LogAudioMCPMenu, Log, All);

// Audio keyword check — same list as QueryCommands.cpp
namespace
{
	bool IsAudioRelevantName(const FString& Name)
	{
		static const TCHAR* Keywords[] = {
			TEXT("Sound"), TEXT("Audio"), TEXT("Ak"), TEXT("Wwise"),
			TEXT("MetaSound"), TEXT("Reverb"), TEXT("SoundMix"),
			TEXT("Dialogue"), TEXT("RTPC"), TEXT("Occlusion"),
			TEXT("Attenuation"), TEXT("PostEvent"), TEXT("SetSwitch"),
			TEXT("SetState"), TEXT("Submix"), TEXT("Modulation"),
			TEXT("SoundClass"), TEXT("SoundCue"), TEXT("Listener"),
			TEXT("Spatialization"), TEXT("AudioVolume"),
		};
		for (const TCHAR* Keyword : Keywords)
		{
			if (Name.Contains(Keyword, ESearchCase::IgnoreCase))
				return true;
		}
		return false;
	}

	/** Get the Saved/AudioMCP/ directory, creating it if needed. */
	FString GetOutputDir()
	{
		FString Dir = FPaths::ProjectSavedDir() / TEXT("AudioMCP");
		IPlatformFile& PlatformFile = FPlatformFileManager::Get().GetPlatformFile();
		if (!PlatformFile.DirectoryExists(*Dir))
		{
			PlatformFile.CreateDirectoryTree(*Dir);
		}
		return Dir;
	}

	/** Show an editor notification popup. */
	void ShowNotification(const FText& Message, SNotificationItem::ECompletionState State)
	{
		FNotificationInfo Info(Message);
		Info.ExpireDuration = 5.0f;
		Info.bUseSuccessFailIcons = true;
		if (TSharedPtr<SNotificationItem> Item = FSlateNotificationManager::Get().AddNotification(Info))
		{
			Item->SetCompletionState(State);
		}
	}
}

// ==========================================================================
// Registration
// ==========================================================================

void FAudioMCPEditorMenu::Register()
{
	UToolMenus::RegisterStartupCallback(
		FSimpleMulticastDelegate::FDelegate::CreateStatic(&FAudioMCPEditorMenu::RegisterImpl));
}

// Private static — called once ToolMenus are ready
void FAudioMCPEditorMenu::RegisterImpl()
{
	UToolMenu* MainMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu");
	if (!MainMenu) return;

	// Add "Audio MCP" as a top-level submenu
	FToolMenuSection& Section = MainMenu->FindOrAddSection("AudioMCP");
	Section.AddSubMenu(
		"AudioMCPMenu",
		LOCTEXT("AudioMCP", "Audio MCP"),
		LOCTEXT("AudioMCPTooltip", "Audio MCP scanning, export, and status tools"),
		FNewToolMenuDelegate::CreateStatic(&FAudioMCPEditorMenu::PopulateMenu),
		false, // bInDefault
		FSlateIcon(FAppStyle::GetAppStyleSetName(), "LevelEditor.Tabs.AudioMixer")
	);
}

void FAudioMCPEditorMenu::Unregister()
{
	if (UToolMenus* ToolMenus = UToolMenus::TryGet())
	{
		ToolMenus->RemoveMenu("LevelEditor.MainMenu.AudioMCPMenu");
	}
}

void FAudioMCPEditorMenu::PopulateMenu(UToolMenu* Menu)
{
	// --- Scanning section ---
	{
		FToolMenuSection& Section = Menu->FindOrAddSection("Scanning",
			LOCTEXT("ScanningSection", "Scanning"));

		Section.AddMenuEntry(
			"ScanProject",
			LOCTEXT("ScanProject", "Scan Project Audio"),
			LOCTEXT("ScanProjectTip", "Scan all Blueprints for audio-relevant function calls and events"),
			FSlateIcon(FAppStyle::GetAppStyleSetName(), "Icons.Search"),
			FUIAction(FExecuteAction::CreateStatic(&FAudioMCPEditorMenu::OnScanProject))
		);

		Section.AddMenuEntry(
			"ScanSelected",
			LOCTEXT("ScanSelected", "Scan Selected Blueprint"),
			LOCTEXT("ScanSelectedTip", "Deep-scan the currently selected Blueprint asset"),
			FSlateIcon(FAppStyle::GetAppStyleSetName(), "ClassIcon.Blueprint"),
			FUIAction(FExecuteAction::CreateStatic(&FAudioMCPEditorMenu::OnScanSelected))
		);
	}

	// --- Export section ---
	{
		FToolMenuSection& Section = Menu->FindOrAddSection("Export",
			LOCTEXT("ExportSection", "Export"));

		Section.AddMenuEntry(
			"ExportPositions",
			LOCTEXT("ExportPositions", "Export Node Positions"),
			LOCTEXT("ExportPositionsTip", "Export MetaSound node pixel positions to JSON"),
			FSlateIcon(FAppStyle::GetAppStyleSetName(), "Icons.Save"),
			FUIAction(FExecuteAction::CreateStatic(&FAudioMCPEditorMenu::OnExportNodePositions))
		);

		Section.AddMenuEntry(
			"OpenResults",
			LOCTEXT("OpenResults", "Open Results Folder"),
			LOCTEXT("OpenResultsTip", "Open the Saved/AudioMCP/ output folder"),
			FSlateIcon(FAppStyle::GetAppStyleSetName(), "Icons.FolderOpen"),
			FUIAction(FExecuteAction::CreateStatic(&FAudioMCPEditorMenu::OnOpenResultsFolder))
		);
	}

	// --- Info section ---
	{
		FToolMenuSection& Section = Menu->FindOrAddSection("Info",
			LOCTEXT("InfoSection", "Info"));

		Section.AddMenuEntry(
			"ServerStatus",
			LOCTEXT("ServerStatus", "Server Status"),
			LOCTEXT("ServerStatusTip", "Show Audio MCP TCP server status"),
			FSlateIcon(FAppStyle::GetAppStyleSetName(), "Icons.Info"),
			FUIAction(FExecuteAction::CreateStatic(&FAudioMCPEditorMenu::OnShowStatus))
		);
	}
}

// ==========================================================================
// Menu Actions
// ==========================================================================

void FAudioMCPEditorMenu::OnScanProject()
{
	// 1. Find all Blueprint assets
	IAssetRegistry& Registry =
		FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry").Get();

	FARFilter Filter;
	Filter.PackagePaths.Add(FName(TEXT("/Game")));
	Filter.bRecursivePaths = true;
	Filter.bRecursiveClasses = true;
	Filter.ClassPaths.Add(FTopLevelAssetPath(TEXT("/Script/Engine"), TEXT("Blueprint")));

	TArray<FAssetData> Assets;
	Registry.GetAssets(Filter, Assets);

	if (Assets.Num() == 0)
	{
		ShowNotification(
			LOCTEXT("NoBPs", "No Blueprints found under /Game/"),
			SNotificationItem::CS_Fail);
		return;
	}

	// 2. Scan each Blueprint with progress
	FScopedSlowTask SlowTask(Assets.Num(),
		LOCTEXT("ScanningBPs", "Scanning Blueprints for audio..."));
	SlowTask.MakeDialog(true);

	TArray<TSharedPtr<FJsonValue>> ResultsArray;
	int32 AudioBPs = 0;
	int32 TotalAudioNodes = 0;
	int32 Errors = 0;

	for (const FAssetData& AssetData : Assets)
	{
		SlowTask.EnterProgressFrame(1.0f,
			FText::FromString(AssetData.AssetName.ToString()));
		if (SlowTask.ShouldCancel()) break;

		FString AssetPath = AssetData.GetObjectPathString();
		UObject* Loaded = AssetData.GetAsset();
		UBlueprint* BP = Cast<UBlueprint>(Loaded);
		if (!BP)
		{
			Errors++;
			continue;
		}

		// Quick-scan: count audio nodes across all graphs
		int32 AudioNodeCount = 0;
		TArray<FString> AudioFunctions;
		int32 TotalNodes = 0;

		auto ScanGraphs = [&](const TArray<UEdGraph*>& Graphs)
		{
			for (UEdGraph* Graph : Graphs)
			{
				if (!Graph) continue;
				for (UEdGraphNode* Node : Graph->Nodes)
				{
					if (!Node) continue;
					TotalNodes++;
					if (UK2Node_CallFunction* CallNode = Cast<UK2Node_CallFunction>(Node))
					{
						FString FuncName = CallNode->FunctionReference.GetMemberName().ToString();
						FString FuncClass;
						if (UFunction* Func = CallNode->GetTargetFunction())
						{
							if (Func->GetOwnerClass())
								FuncClass = Func->GetOwnerClass()->GetName();
						}
						if (IsAudioRelevantName(FuncName) || IsAudioRelevantName(FuncClass))
						{
							AudioNodeCount++;
							if (!AudioFunctions.Contains(FuncName))
								AudioFunctions.Add(FuncName);
						}
					}
					else if (UK2Node_CustomEvent* CE = Cast<UK2Node_CustomEvent>(Node))
					{
						if (IsAudioRelevantName(CE->CustomFunctionName))
							AudioNodeCount++;
					}
				}
			}
		};

		ScanGraphs(BP->UbergraphPages);
		ScanGraphs(BP->FunctionGraphs);

		// Build result entry
		TSharedPtr<FJsonObject> Entry = MakeShared<FJsonObject>();
		Entry->SetStringField(TEXT("name"), BP->GetName());
		Entry->SetStringField(TEXT("path"), AssetPath);
		Entry->SetStringField(TEXT("parent_class"),
			BP->ParentClass ? BP->ParentClass->GetName() : TEXT("None"));
		Entry->SetNumberField(TEXT("total_nodes"), TotalNodes);
		Entry->SetNumberField(TEXT("audio_nodes"), AudioNodeCount);
		Entry->SetBoolField(TEXT("has_audio"), AudioNodeCount > 0);

		TArray<TSharedPtr<FJsonValue>> FuncArr;
		for (const FString& F : AudioFunctions)
			FuncArr.Add(MakeShared<FJsonValueString>(F));
		Entry->SetArrayField(TEXT("audio_functions"), FuncArr);

		ResultsArray.Add(MakeShared<FJsonValueObject>(Entry));

		if (AudioNodeCount > 0)
		{
			AudioBPs++;
			TotalAudioNodes += AudioNodeCount;
		}
	}

	// 3. Save results
	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("project"), FApp::GetProjectName());
	Root->SetStringField(TEXT("scan_time"), FDateTime::Now().ToString());
	Root->SetNumberField(TEXT("total_blueprints"), Assets.Num());
	Root->SetNumberField(TEXT("audio_blueprints"), AudioBPs);
	Root->SetNumberField(TEXT("total_audio_nodes"), TotalAudioNodes);
	Root->SetNumberField(TEXT("errors"), Errors);
	Root->SetArrayField(TEXT("blueprints"), ResultsArray);

	FString OutputPath = SaveResultJson(TEXT("project_audio_scan.json"), Root);

	// 4. Log + notify
	UE_LOG(LogAudioMCPMenu, Log,
		TEXT("Audio scan complete: %d BPs, %d audio-relevant (%d audio nodes), saved to %s"),
		Assets.Num(), AudioBPs, TotalAudioNodes, *OutputPath);

	ShowNotification(
		FText::Format(
			LOCTEXT("ScanDone", "Scan complete: {0} BPs, {1} audio-relevant ({2} audio nodes)"),
			Assets.Num(), AudioBPs, TotalAudioNodes),
		SNotificationItem::CS_Success);
}


void FAudioMCPEditorMenu::OnScanSelected()
{
	// Get Content Browser selection
	TArray<FAssetData> SelectedAssets;
	FContentBrowserModule& CBModule =
		FModuleManager::LoadModuleChecked<FContentBrowserModule>("ContentBrowser");
	CBModule.Get().GetSelectedAssets(SelectedAssets);

	// Filter to Blueprints only
	TArray<FAssetData> BPAssets;
	for (const FAssetData& Asset : SelectedAssets)
	{
		if (Asset.AssetClassPath.GetAssetName() == TEXT("Blueprint") ||
			Asset.AssetClassPath.GetAssetName() == TEXT("WidgetBlueprint") ||
			Asset.AssetClassPath.GetAssetName() == TEXT("AnimBlueprint"))
		{
			BPAssets.Add(Asset);
		}
	}

	if (BPAssets.Num() == 0)
	{
		ShowNotification(
			LOCTEXT("NoSelection", "No Blueprint selected in Content Browser"),
			SNotificationItem::CS_Fail);
		return;
	}

	// Use the FScanBlueprintCommand for full detail
	FScanBlueprintCommand ScanCmd;
	FAudioMCPBuilderManager DummyManager;

	TArray<TSharedPtr<FJsonValue>> ResultsArray;

	for (const FAssetData& Asset : BPAssets)
	{
		TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
		Params->SetStringField(TEXT("asset_path"), Asset.GetObjectPathString());
		Params->SetBoolField(TEXT("audio_only"), false);
		Params->SetBoolField(TEXT("include_pins"), true);

		TSharedPtr<FJsonObject> Result = ScanCmd.Execute(Params, DummyManager);
		ResultsArray.Add(MakeShared<FJsonValueObject>(Result));

		FString BPName = Result->GetStringField(TEXT("blueprint_name"));
		int32 Nodes = static_cast<int32>(Result->GetNumberField(TEXT("total_nodes")));
		UE_LOG(LogAudioMCPMenu, Log, TEXT("Scanned %s: %d nodes"), *BPName, Nodes);
	}

	// Save
	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetNumberField(TEXT("count"), ResultsArray.Num());
	Root->SetArrayField(TEXT("results"), ResultsArray);

	FString OutputPath = SaveResultJson(TEXT("selected_scan.json"), Root);

	ShowNotification(
		FText::Format(
			LOCTEXT("SelectedDone", "Scanned {0} Blueprint(s) — saved to Saved/AudioMCP/"),
			BPAssets.Num()),
		SNotificationItem::CS_Success);
}


void FAudioMCPEditorMenu::OnExportNodePositions()
{
	// Find all MetaSoundSource assets and export their node positions
	IAssetRegistry& Registry =
		FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry").Get();

	FARFilter Filter;
	Filter.PackagePaths.Add(FName(TEXT("/Game")));
	Filter.bRecursivePaths = true;
	Filter.ClassPaths.Add(FTopLevelAssetPath(TEXT("/Script/MetasoundEngine"), TEXT("MetaSoundSource")));

	TArray<FAssetData> Assets;
	Registry.GetAssets(Filter, Assets);

	// Also get MetaSoundPatch assets
	FARFilter PatchFilter;
	PatchFilter.PackagePaths.Add(FName(TEXT("/Game")));
	PatchFilter.bRecursivePaths = true;
	PatchFilter.ClassPaths.Add(FTopLevelAssetPath(TEXT("/Script/MetasoundEngine"), TEXT("MetaSoundPatch")));

	TArray<FAssetData> PatchAssets;
	Registry.GetAssets(PatchFilter, PatchAssets);
	Assets.Append(PatchAssets);

	if (Assets.Num() == 0)
	{
		ShowNotification(
			LOCTEXT("NoMS", "No MetaSound assets found under /Game/"),
			SNotificationItem::CS_Fail);
		return;
	}

	// Use FGetNodeLocationsCommand for each asset
	FGetNodeLocationsCommand LocCmd;
	FAudioMCPBuilderManager DummyManager;

	TArray<TSharedPtr<FJsonValue>> ResultsArray;
	int32 Success = 0;

	FScopedSlowTask SlowTask(Assets.Num(),
		LOCTEXT("ExportingPositions", "Exporting MetaSound node positions..."));
	SlowTask.MakeDialog(true);

	for (const FAssetData& Asset : Assets)
	{
		SlowTask.EnterProgressFrame();
		if (SlowTask.ShouldCancel()) break;

		TSharedPtr<FJsonObject> Params = MakeShared<FJsonObject>();
		Params->SetStringField(TEXT("asset_path"), Asset.GetObjectPathString());

		TSharedPtr<FJsonObject> Result = LocCmd.Execute(Params, DummyManager);
		if (Result->GetStringField(TEXT("status")) == TEXT("ok"))
		{
			ResultsArray.Add(MakeShared<FJsonValueObject>(Result));
			Success++;
		}
	}

	TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetNumberField(TEXT("count"), Success);
	Root->SetArrayField(TEXT("metasounds"), ResultsArray);

	FString OutputPath = SaveResultJson(TEXT("node_positions.json"), Root);

	ShowNotification(
		FText::Format(
			LOCTEXT("ExportDone", "Exported positions for {0} MetaSound asset(s)"),
			Success),
		SNotificationItem::CS_Success);
}


void FAudioMCPEditorMenu::OnOpenResultsFolder()
{
	FString Dir = GetOutputDir();
	FPlatformProcess::ExploreFolder(*Dir);
}


void FAudioMCPEditorMenu::OnShowStatus()
{
	FString Message = FString::Printf(
		TEXT("Audio MCP TCP Server\n"
			 "Port: %d\n"
			 "Project: %s\n"
			 "Commands: 24"),
		AudioMCP::DEFAULT_PORT,
		FApp::GetProjectName());

	ShowNotification(FText::FromString(Message), SNotificationItem::CS_None);
	UE_LOG(LogAudioMCPMenu, Log, TEXT("%s"), *Message);
}


// ==========================================================================
// Utilities
// ==========================================================================

FString FAudioMCPEditorMenu::SaveResultJson(
	const FString& Filename,
	const TSharedPtr<FJsonObject>& Json)
{
	FString Dir = GetOutputDir();
	FString FullPath = Dir / Filename;

	FString JsonString;
	TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
	FJsonSerializer::Serialize(Json.ToSharedRef(), Writer);

	FFileHelper::SaveStringToFile(JsonString, *FullPath,
		FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);

	return FullPath;
}

#undef LOCTEXT_NAMESPACE
