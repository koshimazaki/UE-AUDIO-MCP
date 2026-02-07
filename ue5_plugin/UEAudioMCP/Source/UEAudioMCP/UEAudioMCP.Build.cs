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
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"Sockets",
			"Networking",
			"Json",
			"JsonUtilities",
			"Projects",
			"MetasoundEngine",
			"MetasoundFrontend",
			"MetasoundGraphCore",
			"MetasoundEditor",
			"MetasoundStandardNodes",
			"AudioMixer",
		});
	}
}
