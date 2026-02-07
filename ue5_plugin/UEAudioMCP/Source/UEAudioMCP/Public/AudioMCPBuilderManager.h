// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "MetasoundFrontendDocument.h"

// Forward declarations — actual includes only in .cpp
class UMetaSoundBuilderBase;
struct FMetaSoundBuilderNodeOutputHandle;
struct FMetaSoundBuilderNodeInputHandle;

/**
 * Manages the active MetaSounds builder session.
 * Holds the current builder, node handle registry, and graph I/O maps.
 * All methods must be called on the game thread.
 */
class FAudioMCPBuilderManager
{
public:
	FAudioMCPBuilderManager();
	~FAudioMCPBuilderManager();

	// -- Builder lifecycle --

	/** Create a new builder, resetting all state. */
	bool CreateBuilder(const FString& AssetType, const FString& Name, FString& OutError);

	/** Add an interface (e.g. "UE.Source.OneShot") to the current builder. */
	bool AddInterface(const FString& InterfaceName, FString& OutError);

	/** Add a graph-level input node. */
	bool AddGraphInput(const FString& Name, const FString& TypeName, const FString& DefaultValue, FString& OutError);

	/** Add a graph-level output node. */
	bool AddGraphOutput(const FString& Name, const FString& TypeName, FString& OutError);

	// -- Node operations --

	/** Add a node to the graph by display name, store handle by ID. */
	bool AddNode(const FString& NodeId, const FString& NodeType, int32 PosX, int32 PosY, FString& OutError);

	/** Set a default value on a node's input pin. */
	bool SetNodeDefault(const FString& NodeId, const FString& InputName, const TSharedPtr<FJsonValue>& Value, FString& OutError);

	/** Connect two pins — handles __graph__ sentinel for graph I/O. */
	bool ConnectNodes(const FString& FromNode, const FString& FromPin,
	                  const FString& ToNode, const FString& ToPin, FString& OutError);

	// -- Build & Audition --

	/** Build the current graph to a .uasset. */
	bool BuildToAsset(const FString& Name, const FString& Path, FString& OutError);

	/** Audition/preview the current graph in the editor. */
	bool Audition(FString& OutError);

	/** Check if a builder is currently active. */
	bool HasActiveBuilder() const { return ActiveBuilder != nullptr; }

private:
	/** Try to resolve a display name to a MetaSound node class. */
	bool ResolveNodeType(const FString& DisplayName, FString& OutClassName, FString& OutError);

	/** Reset all state (called before creating a new builder). */
	void ResetState();

	// Current builder session
	UMetaSoundBuilderBase* ActiveBuilder;
	FString ActiveBuilderName;

	// Node handle registry: Python string ID -> UE node handle
	// FMetaSoundNodeHandle is needed for FindNodeInputByName/FindNodeOutputByName
	TMap<FString, FMetaSoundNodeHandle> NodeHandles;

	// Graph I/O handle maps: pin name -> handle
	// Graph inputs have output handles (they feed INTO the graph)
	TMap<FString, FMetaSoundBuilderNodeOutputHandle> GraphInputOutputHandles;
	// Graph outputs have input handles (they receive FROM the graph)
	TMap<FString, FMetaSoundBuilderNodeInputHandle> GraphOutputInputHandles;

	// Display name -> MetaSound class name lookup
	TMap<FString, FString> NodeTypeMap;
	bool bNodeTypeMapBuilt;

	/** Build the node type lookup map from the MetaSound registry. */
	void BuildNodeTypeMap();
};
