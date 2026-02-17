// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

class UBlueprint;
class UEdGraphNode;
class UEdGraph;

/**
 * Manages the active Blueprint editing session for MCP commands.
 * Holds the current Blueprint, node handle registry, and audio function allowlist.
 * All methods must be called on the game thread.
 *
 * Singleton pattern: Module creates/destroys, BP commands access via Get().
 */
class FAudioMCPBlueprintManager
{
public:
	FAudioMCPBlueprintManager();
	~FAudioMCPBlueprintManager();

	// -- Singleton access (does NOT change IAudioMCPCommand interface) --
	static FAudioMCPBlueprintManager* Get() { return Instance; }
	static void SetInstance(FAudioMCPBlueprintManager* Inst) { Instance = Inst; }

	// -- Blueprint lifecycle --

	/** Open a Blueprint asset for editing. Resets node handle state. */
	bool OpenBlueprint(const FString& AssetPath, FString& OutError);

	/** Check if a Blueprint is currently open for editing. */
	bool HasActiveBlueprint() const;

	/** Get the name of the active Blueprint. */
	FString GetActiveBlueprintName() const;

	// -- Node operations --

	/** Add a CallFunction node (allowlisted audio functions only). */
	bool AddCallFunctionNode(const FString& Id, const FString& FunctionName,
		int32 PosX, int32 PosY, FString& OutError);

	/** Add a CustomEvent node. */
	bool AddCustomEventNode(const FString& Id, const FString& EventName,
		int32 PosX, int32 PosY, FString& OutError);

	/** Add a VariableGet node (variable must pre-exist on the Blueprint). */
	bool AddVariableGetNode(const FString& Id, const FString& VarName,
		int32 PosX, int32 PosY, FString& OutError);

	/** Add a VariableSet node (variable must pre-exist on the Blueprint). */
	bool AddVariableSetNode(const FString& Id, const FString& VarName,
		int32 PosX, int32 PosY, FString& OutError);

	// -- Pin operations --

	/** Connect two pins between registered nodes. */
	bool ConnectPins(const FString& FromId, const FString& FromPin,
		const FString& ToId, const FString& ToPin, FString& OutError);

	/** Set a default value on a node's input pin. */
	bool SetPinDefault(const FString& NodeId, const FString& PinName,
		const FString& Value, FString& OutError);

	// -- Compile --

	/** Compile the active Blueprint, return status and messages. */
	bool CompileBlueprint(TArray<FString>& OutMessages, FString& OutError);

	// -- Introspection --

	/** Register an existing node by its FGuid string, so we can wire to it. */
	bool RegisterExistingNode(const FString& Id, const FString& NodeGuid,
		FString& OutNodeClass, FString& OutNodeTitle, FString& OutError);

	/** List all pins on a registered node. */
	bool ListPins(const FString& NodeId, TArray<TSharedPtr<FJsonValue>>& OutPins,
		FString& OutError);

	/** Auto-register all existing EventGraph nodes by title. Returns node info. */
	int32 AutoRegisterNodes(TArray<TSharedPtr<FJsonValue>>& OutNodes);

private:
	/** The single global instance — set by Module startup/shutdown. */
	static FAudioMCPBlueprintManager* Instance;

	/** Get the EventGraph (first UbergraphPage) from the active Blueprint. */
	UEdGraph* GetEventGraph(FString& OutError) const;

	/** Check if a function name is in the audio allowlist. */
	bool IsAllowedFunction(const FString& FunctionName) const;

	/** Find a UFunction by name across audio-relevant classes. */
	UFunction* FindAudioFunction(const FString& FunctionName) const;

	/** Reset node handles (called when opening a new Blueprint). */
	void ResetHandles();

	// Active Blueprint being edited
	TWeakObjectPtr<UBlueprint> ActiveBlueprint;

	// MCP ID -> graph node pointer
	TMap<FString, TWeakObjectPtr<UEdGraphNode>> NodeHandles;

	// Audio function allowlist
	TSet<FString> AllowedFunctions;

	/** Build the allowlist on first use. */
	void BuildAllowlist();
	bool bAllowlistBuilt = false;
};
