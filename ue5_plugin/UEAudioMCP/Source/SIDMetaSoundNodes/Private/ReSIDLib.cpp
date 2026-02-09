// Copyright UE Audio MCP Project. All Rights Reserved.
// ReSID Single Compilation Unit
// All ReSID implementation files compiled here exactly once to avoid duplicate symbols.
// Individual node .cpp files define RESID_HEADER_ONLY to get declarations only.

#include "CoreMinimal.h"

#ifndef VERSION
#define VERSION "SIDKIT-UE5-1.0"
#endif

THIRD_PARTY_INCLUDES_START

// Include the top-level header which pulls in all sub-headers and their _impl files.
// The _impl includes are guarded by #ifndef RESID_HEADER_ONLY — since we do NOT
// define that macro here, all implementations are compiled in this single TU.
#include "siddefs.h"
#include "sid.h"

THIRD_PARTY_INCLUDES_END
