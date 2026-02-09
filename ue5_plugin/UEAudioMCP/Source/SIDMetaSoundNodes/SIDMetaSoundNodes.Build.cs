// Copyright UE Audio MCP Project. All Rights Reserved.

using UnrealBuildTool;
using System.IO;

public class SIDMetaSoundNodes : ModuleRules
{
	public SIDMetaSoundNodes(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		// reSID ThirdParty include path
		string ReSIDPath = Path.Combine(ModuleDirectory, "..", "ThirdParty", "ReSID");
		PublicIncludePaths.Add(ReSIDPath);

		// Enable VICE 1.0 non-linear filter model (50MB tables, desktop-only)
		PublicDefinitions.Add("USE_NEW_FILTER=1");

		// Suppress reSID compiler warnings (C-style casts, signed/unsigned, etc.)
		UndefinedIdentifierWarningLevel = WarningLevel.Off;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"MetasoundEngine",
			"MetasoundFrontend",
			"MetasoundGraphCore",
			"MetasoundStandardNodes",
			"AudioExtensions",
			"SignalProcessing",
		});

		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"AudioMixer",
		});
	}
}
