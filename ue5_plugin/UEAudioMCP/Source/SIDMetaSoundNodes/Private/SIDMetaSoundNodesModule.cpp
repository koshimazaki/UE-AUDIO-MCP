// Copyright UE Audio MCP Project. All Rights Reserved.

#include "SIDMetaSoundNodesModule.h"
#include "Modules/ModuleManager.h"

void FSIDMetaSoundNodesModule::StartupModule()
{
	// SID MetaSounds nodes are auto-registered via METASOUND_REGISTER_NODE macros
}

void FSIDMetaSoundNodesModule::ShutdownModule()
{
}

IMPLEMENT_MODULE(FSIDMetaSoundNodesModule, SIDMetaSoundNodes)
