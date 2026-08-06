// Copyright UE Audio MCP Project. All Rights Reserved.

using UnrealBuildTool;
using System.IO;

public class SIDMetaSoundNodes : ModuleRules
{
	public SIDMetaSoundNodes(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		// The node .cpp files define RESID_HEADER_ONLY to get reSID declarations only,
		// while ReSIDLib.cpp deliberately omits it to compile the implementations once.
		// A unity build concatenates them into one TU, so the node files' define (and
		// their header guards) leak into ReSIDLib.cpp and the implementations are never
		// compiled, producing unresolved externals at link. Keep this module non-unity.
		bUseUnity = false;

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
