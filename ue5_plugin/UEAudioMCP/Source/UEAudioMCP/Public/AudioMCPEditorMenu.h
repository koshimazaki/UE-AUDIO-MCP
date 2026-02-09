// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

/**
 * Registers the "Audio MCP" menu in the editor main menu bar.
 * Provides: Scan Project, Scan Selected, Export Positions, Open Results, Status.
 */
class FAudioMCPEditorMenu
{
public:
	/** Register all menu entries. Call from StartupModule. */
	static void Register();

	/** Remove menu entries. Call from ShutdownModule. */
	static void Unregister();

private:
	/** Called once ToolMenus system is ready. */
	static void RegisterImpl();

	/** Populate the Audio MCP submenu. */
	static void PopulateMenu(class UToolMenu* Menu);

	// --- Menu action handlers ---
	static void OnScanProject();
	static void OnScanSelected();
	static void OnExportNodePositions();
	static void OnOpenResultsFolder();
	static void OnShowStatus();

	/** Shared: save JSON object to Saved/AudioMCP/{Filename}. Returns full path. */
	static FString SaveResultJson(const FString& Filename, const TSharedPtr<FJsonObject>& Json);
};
