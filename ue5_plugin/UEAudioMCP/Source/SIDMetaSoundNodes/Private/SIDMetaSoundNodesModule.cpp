// Copyright UE Audio MCP Project. All Rights Reserved.

#include "SIDMetaSoundNodesModule.h"
#include "Modules/ModuleManager.h"
#include "MetasoundFrontendModuleRegistrationMacros.h"

// Declares this module's private registration list. The METASOUND_REGISTER_NODE
// calls in the node .cpp files append to it during static initialisation.
METASOUND_IMPLEMENT_MODULE_REGISTRATION_LIST

void FSIDMetaSoundNodesModule::StartupModule()
{
	// Each module must flush its own registration list. The engine only flushes its
	// global list during MetasoundEngine startup, which runs at PreDefault — before
	// this module loads at Default — so registering here is what makes the SID nodes
	// visible to the MetaSounds node registry.
	METASOUND_REGISTER_ITEMS_IN_MODULE
}

void FSIDMetaSoundNodesModule::ShutdownModule()
{
	METASOUND_UNREGISTER_ITEMS_IN_MODULE
}

IMPLEMENT_MODULE(FSIDMetaSoundNodesModule, SIDMetaSoundNodes)
