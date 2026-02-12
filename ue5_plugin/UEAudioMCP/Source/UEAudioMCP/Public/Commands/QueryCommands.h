// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "Commands/IAudioMCPCommand.h"

/** get_graph_input_names: List all graph-level input names for introspection. */
class FGetGraphInputNamesCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** set_live_updates: Enable or disable real-time topology changes while auditioning. */
class FSetLiveUpdatesCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** list_node_classes: Enumerate all registered MetaSound node classes from the engine registry. */
class FListNodeClassesCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** get_node_locations: Read node positions and connections from a saved MetaSound asset. */
class FGetNodeLocationsCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** export_metasound: Full export of a MetaSound asset — nodes, pins, types, defaults, variables, interfaces, graph I/O. */
class FExportMetaSoundCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** scan_blueprint: Deep-scan a Blueprint asset to extract graph nodes, function calls, and audio relevance. */
class FScanBlueprintCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** list_assets: Query the Asset Registry for assets by class and path. */
class FListAssetsCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** export_audio_blueprint: Focused export of audio-relevant BP nodes + 1-hop neighbours with full edge wiring. */
class FExportAudioBlueprintCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};

/** list_blueprint_functions: Enumerate BlueprintCallable UFunctions across all loaded classes. */
class FListBlueprintFunctionsCommand : public IAudioMCPCommand
{
public:
	virtual TSharedPtr<FJsonObject> Execute(
		const TSharedPtr<FJsonObject>& Params,
		FAudioMCPBuilderManager& BuilderManager) override;
};
