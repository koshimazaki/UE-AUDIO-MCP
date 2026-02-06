"""System, utilities, debug, data table, and subsystem Blueprint nodes.

Sources:
- UKismetSystemLibrary (Debug Drawing, System Info, Console, Object/Class,
  File/Path, Primary Asset ID, Soft References, GC, Undo)
- UDataTableFunctionLibrary (Data Table queries)
- USubsystemBlueprintLibrary (Subsystem access)
"""
from __future__ import annotations
from ue_audio_mcp.knowledge.blueprint_nodes import _n

# ── Debug Drawing (UKismetSystemLibrary) ──────────────────────────
_n("DrawDebugLine", "UKismetSystemLibrary", "debug_draw",
   "Draws a debug line in world space", ["debug", "draw", "line"])
_n("DrawDebugCircle", "UKismetSystemLibrary", "debug_draw",
   "Draws a debug circle", ["debug", "draw", "circle"])
_n("DrawDebugArrow", "UKismetSystemLibrary", "debug_draw",
   "Draws a debug arrow", ["debug", "draw", "arrow"])
_n("DrawDebugBox", "UKismetSystemLibrary", "debug_draw",
   "Draws a debug box", ["debug", "draw", "box"])
_n("DrawDebugSphere", "UKismetSystemLibrary", "debug_draw",
   "Draws a debug sphere", ["debug", "draw", "sphere"])
_n("DrawDebugCapsule", "UKismetSystemLibrary", "debug_draw",
   "Draws a debug capsule", ["debug", "draw", "capsule"])
_n("DrawDebugCylinder", "UKismetSystemLibrary", "debug_draw",
   "Draws a debug cylinder", ["debug", "draw", "cylinder"])
_n("DrawDebugCone", "UKismetSystemLibrary", "debug_draw",
   "Draws a debug cone (radians)", ["debug", "draw", "cone"])
_n("DrawDebugConeInDegrees", "UKismetSystemLibrary", "debug_draw",
   "Draws a debug cone (degrees)", ["debug", "draw", "cone"])
_n("DrawDebugPoint", "UKismetSystemLibrary", "debug_draw",
   "Draws a debug point", ["debug", "draw", "point"])
_n("DrawDebugString", "UKismetSystemLibrary", "debug_draw",
   "Draws debug text at 3D location", ["debug", "draw", "string", "text"])
_n("DrawDebugPlane", "UKismetSystemLibrary", "debug_draw",
   "Draws a debug plane", ["debug", "draw", "plane"])
_n("DrawDebugCamera", "UKismetSystemLibrary", "debug_draw",
   "Draws a debug camera shape", ["debug", "draw", "camera"])
_n("DrawDebugFrustum", "UKismetSystemLibrary", "debug_draw",
   "Draws a debug camera frustum", ["debug", "draw", "frustum"])
_n("DrawDebugCoordinateSystem", "UKismetSystemLibrary", "debug_draw",
   "Draws XYZ coordinate axes", ["debug", "draw", "coordinate", "axes"])
_n("DrawDebugFloatHistoryLocation", "UKismetSystemLibrary", "debug_draw",
   "Draws 2D histogram at world location", ["debug", "draw", "histogram"])
_n("DrawDebugFloatHistoryTransform", "UKismetSystemLibrary", "debug_draw",
   "Draws 2D histogram with transform", ["debug", "draw", "histogram"])
_n("FlushDebugStrings", "UKismetSystemLibrary", "debug_draw",
   "Removes all active debug strings", ["debug", "flush", "clear"])
_n("FlushPersistentDebugLines", "UKismetSystemLibrary", "debug_draw",
   "Clears all persistent debug lines/shapes", ["debug", "flush", "clear"])

# ── Print/Log (UKismetSystemLibrary) ─────────────────────────────
_n("PrintString", "UKismetSystemLibrary", "debug_log",
   "Prints string to log and/or screen", ["print", "log", "debug"])
_n("PrintText", "UKismetSystemLibrary", "debug_log",
   "Prints FText to log and/or screen", ["print", "log", "text"])
_n("PrintWarning", "UKismetSystemLibrary", "debug_log",
   "Prints warning to log", ["print", "log", "warning"])

# ── System Info (UKismetSystemLibrary) ────────────────────────────
_n("GetPlatformName", "UKismetSystemLibrary", "system_info",
   "Returns platform name (Windows, Mac, etc.)", ["platform", "system"])
_n("GetEngineVersion", "UKismetSystemLibrary", "system_info",
   "Returns engine version string", ["version", "engine"])
_n("GetGameBundleId", "UKismetSystemLibrary", "system_info",
   "Returns application bundle identifier", ["bundle", "app"])
_n("GetProjectDirectory", "UKismetSystemLibrary", "system_info",
   "Returns project root directory", ["directory", "project", "path"])
_n("GetProjectContentDirectory", "UKismetSystemLibrary", "system_info",
   "Returns Content folder path", ["directory", "content", "path"])
_n("GetProjectSavedDirectory", "UKismetSystemLibrary", "system_info",
   "Returns Saved folder path", ["directory", "saved", "path"])
_n("GetDeviceId", "UKismetSystemLibrary", "system_info",
   "Returns platform-specific device ID", ["device", "id"])
_n("GetUniqueDeviceId", "UKismetSystemLibrary", "system_info",
   "Returns globally unique device ID", ["device", "id", "unique"])
_n("GetCommandLine", "UKismetSystemLibrary", "system_info",
   "Returns process command line", ["command", "line", "args"])
_n("HasLaunchOption", "UKismetSystemLibrary", "system_info",
   "Checks if launch option was specified", ["launch", "option", "args"])
_n("GetDefaultLanguage", "UKismetSystemLibrary", "system_info",
   "Returns default language", ["language", "locale"])
_n("GetDefaultLocale", "UKismetSystemLibrary", "system_info",
   "Returns default locale", ["locale", "language"])
_n("IsStandalone", "UKismetSystemLibrary", "system_info",
   "Returns true if running standalone", ["standalone", "mode"])
_n("IsDedicatedServer", "UKismetSystemLibrary", "system_info",
   "Returns true if dedicated server", ["server", "dedicated"])
_n("IsServer", "UKismetSystemLibrary", "system_info",
   "Returns true if server (listen or dedicated)", ["server", "mode"])
_n("IsPackagedForDistribution", "UKismetSystemLibrary", "system_info",
   "True if packaged build", ["package", "distribution", "shipping"])

# ── Console Variables (UKismetSystemLibrary) ──────────────────────
_n("GetConsoleVariableBoolValue", "UKismetSystemLibrary", "console",
   "Gets bool console variable value", ["console", "cvar", "bool"])
_n("GetConsoleVariableIntValue", "UKismetSystemLibrary", "console",
   "Gets int console variable value", ["console", "cvar", "int"])
_n("GetConsoleVariableFloatValue", "UKismetSystemLibrary", "console",
   "Gets float console variable value", ["console", "cvar", "float"])
_n("SetConsoleVariableBool", "UKismetSystemLibrary", "console",
   "Sets bool console variable", ["console", "cvar", "bool", "set"])
_n("SetConsoleVariableInt", "UKismetSystemLibrary", "console",
   "Sets int console variable", ["console", "cvar", "int", "set"])
_n("SetConsoleVariableFloat", "UKismetSystemLibrary", "console",
   "Sets float console variable", ["console", "cvar", "float", "set"])
_n("ExecuteConsoleCommand", "UKismetSystemLibrary", "console",
   "Executes console command string", ["console", "command", "exec"])

# ── Object/Class Utilities (UKismetSystemLibrary) ────────────────
_n("IsValid", "UKismetSystemLibrary", "object_utils",
   "Returns true if object reference is valid", ["object", "valid", "check"])
_n("IsValidClass", "UKismetSystemLibrary", "object_utils",
   "Returns true if class reference is valid", ["class", "valid", "check"])
_n("GetObjectName", "UKismetSystemLibrary", "object_utils",
   "Returns object name", ["object", "name"])
_n("GetDisplayName", "UKismetSystemLibrary", "object_utils",
   "Returns display name", ["object", "name", "display"])
_n("GetClassDisplayName", "UKismetSystemLibrary", "object_utils",
   "Returns class display name", ["class", "name", "display"])
_n("GetPathName", "UKismetSystemLibrary", "object_utils",
   "Returns full path name", ["object", "path", "name"])
_n("GetObjectClass", "UKismetSystemLibrary", "object_utils",
   "Returns class of object", ["object", "class"])
_n("DoesImplementInterface", "UKismetSystemLibrary", "object_utils",
   "Checks if object implements interface", ["object", "interface", "check"])
_n("GetOuterObject", "UKismetSystemLibrary", "object_utils",
   "Returns outer object", ["object", "outer", "parent"])

# ── File/Path Utilities (UKismetSystemLibrary) ───────────────────
_n("ConvertToAbsolutePath", "UKismetSystemLibrary", "file_utils",
   "Converts to absolute file path", ["file", "path", "absolute"])
_n("ConvertToRelativePath", "UKismetSystemLibrary", "file_utils",
   "Converts to relative file path", ["file", "path", "relative"])
_n("NormalizeFilename", "UKismetSystemLibrary", "file_utils",
   "Normalizes file path", ["file", "path", "normalize"])
_n("CanLaunchURL", "UKismetSystemLibrary", "file_utils",
   "Checks if URL can be opened", ["url", "launch", "check"])
_n("LaunchURL", "UKismetSystemLibrary", "file_utils",
   "Opens URL in default browser", ["url", "launch", "browser"])

# ── Primary Asset ID (UKismetSystemLibrary) ──────────────────────
_n("MakePrimaryAssetIdFromString", "UKismetSystemLibrary", "asset",
   "Creates PrimaryAssetId from string", ["asset", "id", "create"])
_n("Conv_PrimaryAssetIdToString", "UKismetSystemLibrary", "asset",
   "PrimaryAssetId to string", ["asset", "id", "convert", "string"])
_n("Conv_PrimaryAssetTypeToString", "UKismetSystemLibrary", "asset",
   "PrimaryAssetType to string", ["asset", "type", "convert", "string"])
_n("GetPrimaryAssetIdFromObject", "UKismetSystemLibrary", "asset",
   "Gets PrimaryAssetId from object", ["asset", "id", "object"])
_n("GetClassFromPrimaryAssetId", "UKismetSystemLibrary", "asset",
   "Gets class from asset ID", ["asset", "id", "class"])
_n("GetSoftClassReferenceFromPrimaryAssetId", "UKismetSystemLibrary", "asset",
   "Gets soft class ref from ID", ["asset", "id", "soft", "class"])
_n("GetSoftObjectReferenceFromPrimaryAssetId", "UKismetSystemLibrary", "asset",
   "Gets soft object ref from ID", ["asset", "id", "soft", "object"])
_n("EqualEqual_PrimaryAssetId", "UKismetSystemLibrary", "asset",
   "Compares asset IDs", ["asset", "id", "compare", "equal"])
_n("EqualEqual_PrimaryAssetType", "UKismetSystemLibrary", "asset",
   "Compares asset types", ["asset", "type", "compare", "equal"])
_n("IsValidPrimaryAssetId", "UKismetSystemLibrary", "asset",
   "Validates asset ID", ["asset", "id", "valid"])
_n("IsValidPrimaryAssetType", "UKismetSystemLibrary", "asset",
   "Validates asset type", ["asset", "type", "valid"])

# ── Soft References (UKismetSystemLibrary) ───────────────────────
_n("Conv_SoftObjectReferenceToString", "UKismetSystemLibrary", "asset",
   "Soft reference to string path", ["soft", "reference", "string"])
_n("Conv_SoftObjectReferenceToObject", "UKismetSystemLibrary", "asset",
   "Resolves soft reference to object", ["soft", "reference", "resolve"])
_n("Conv_SoftClassReferenceToString", "UKismetSystemLibrary", "asset",
   "Soft class ref to string", ["soft", "class", "string"])
_n("Conv_SoftClassReferenceToClass", "UKismetSystemLibrary", "asset",
   "Resolves soft class reference", ["soft", "class", "resolve"])
_n("Conv_ObjectToSoftObjectReference", "UKismetSystemLibrary", "asset",
   "Object to soft reference", ["soft", "reference", "convert"])
_n("Conv_ClassToSoftClassReference", "UKismetSystemLibrary", "asset",
   "Class to soft class reference", ["soft", "class", "convert"])
_n("EqualEqual_SoftObjectReference", "UKismetSystemLibrary", "asset",
   "Soft reference equality", ["soft", "reference", "equal"])
_n("EqualEqual_SoftClassReference", "UKismetSystemLibrary", "asset",
   "Soft class reference equality", ["soft", "class", "equal"])
_n("IsValidSoftObjectReference", "UKismetSystemLibrary", "asset",
   "Validates soft reference", ["soft", "reference", "valid"])
_n("IsValidSoftClassReference", "UKismetSystemLibrary", "asset",
   "Validates soft class reference", ["soft", "class", "valid"])
_n("LoadAsset", "UKismetSystemLibrary", "asset",
   "Latent async load of soft object ref", ["asset", "load", "async"])
_n("LoadClassAsset", "UKismetSystemLibrary", "asset",
   "Latent async load of soft class ref", ["asset", "load", "async", "class"])

# ── Garbage Collection (UKismetSystemLibrary) ────────────────────
_n("CollectGarbage", "UKismetSystemLibrary", "system_info",
   "Forces garbage collection", ["gc", "garbage", "memory"])

# ── Undo/Transactions (UKismetSystemLibrary) ─────────────────────
_n("BeginTransaction", "UKismetSystemLibrary", "editor",
   "Begins undo transaction", ["undo", "transaction", "begin"])
_n("EndTransaction", "UKismetSystemLibrary", "editor",
   "Ends undo transaction", ["undo", "transaction", "end"])
_n("CancelTransaction", "UKismetSystemLibrary", "editor",
   "Cancels undo transaction", ["undo", "transaction", "cancel"])
_n("TransactObject", "UKismetSystemLibrary", "editor",
   "Records object for undo", ["undo", "transaction", "record"])
_n("CreateCopyForUndoBuffer", "UKismetSystemLibrary", "editor",
   "Copies to undo buffer", ["undo", "buffer", "copy"])

# ── Rendering (UKismetSystemLibrary) ─────────────────────────────
_n("GetConvenientWindowedResolutions", "UKismetSystemLibrary", "rendering",
   "Returns available windowed resolutions", ["rendering", "resolution", "window"])
_n("GetSupportedFullscreenResolutions", "UKismetSystemLibrary", "rendering",
   "Returns supported fullscreen resolutions", ["rendering", "resolution", "fullscreen"])
_n("SetEnableWorldRendering", "UKismetSystemLibrary", "rendering",
   "Enables/disables world rendering", ["rendering", "world", "toggle"])
_n("GetEnableWorldRendering", "UKismetSystemLibrary", "rendering",
   "Returns world rendering state", ["rendering", "world", "state"])

# ── Data Table (UDataTableFunctionLibrary) ───────────────────────
_n("GetDataTableRow", "UDataTableFunctionLibrary", "data_table",
   "Attempts to retrieve a row by RowName", ["data", "table", "row", "get"])
_n("GetDataTableRowNames", "UDataTableFunctionLibrary", "data_table",
   "Returns all row names in the table", ["data", "table", "row", "names"])
_n("GetDataTableRowStruct", "UDataTableFunctionLibrary", "data_table",
   "Returns the UScriptStruct used by the DataTable", ["data", "table", "struct"])
_n("DoesDataTableRowExist", "UDataTableFunctionLibrary", "data_table",
   "Returns bool if row with given name exists", ["data", "table", "row", "exists"])
_n("GetDataTableColumnAsString", "UDataTableFunctionLibrary", "data_table",
   "Returns all values in a column as string array", ["data", "table", "column"])
_n("GetDataTableColumnNames", "UDataTableFunctionLibrary", "data_table",
   "Returns all column names", ["data", "table", "column", "names"])
_n("EvaluateCurveTableRow", "UDataTableFunctionLibrary", "data_table",
   "Evaluates a CurveTable row at a given X value", ["curve", "table", "evaluate"])

# ── Subsystems (USubsystemBlueprintLibrary) ──────────────────────
_n("GetEngineSubsystem", "USubsystemBlueprintLibrary", "subsystem",
   "Gets engine subsystem by class (engine lifetime)", ["subsystem", "engine"])
_n("GetGameInstanceSubsystem", "USubsystemBlueprintLibrary", "subsystem",
   "Gets game instance subsystem by class", ["subsystem", "game", "instance"])
_n("GetWorldSubsystem", "USubsystemBlueprintLibrary", "subsystem",
   "Gets world subsystem by class (world lifetime)", ["subsystem", "world"])
_n("GetLocalPlayerSubsystem", "USubsystemBlueprintLibrary", "subsystem",
   "Gets local player subsystem by class", ["subsystem", "player", "local"])
