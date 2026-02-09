// Copyright UE Audio MCP Project. All Rights Reserved.

using UnrealBuildTool;

public class UEAudioMCP : ModuleRules
{
	public UEAudioMCP(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"MetasoundEngine",    // UMetaSoundBuilderSubsystem, UMetaSoundSourceBuilder
			"MetasoundFrontend",  // FMetasoundFrontendClassName, FMetasoundFrontendLiteral, IMetaSoundDocumentInterface
			"MetasoundGraphCore", // Underlying graph logic for Builder API
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"Sockets",
			"Networking",
			"Json",
			"JsonUtilities",
			"Projects",
			"UnrealEd",
			"AudioMixer",
			"MetasoundEditor",   // UMetaSoundEditorSubsystem: BuildToAsset, SetNodeLocation
			"BlueprintGraph",    // UK2Node_CallFunction, UK2Node_Event — Blueprint graph inspection
			"ToolMenus",         // UToolMenus — editor menu bar integration
			"ContentBrowser",    // IContentBrowserSingleton — selected asset queries
		});
	}
}
