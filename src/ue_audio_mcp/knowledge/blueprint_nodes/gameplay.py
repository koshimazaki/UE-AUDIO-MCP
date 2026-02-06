"""Gameplay nodes: actor, player, damage, game state, spawning, level, time, effects, haptics.
Source: UGameplayStatics -- official Epic C++ API.
"""
from __future__ import annotations
from ue_audio_mcp.knowledge.blueprint_nodes import _n

# ===================================================================
# DAMAGE  (4 nodes)
# ===================================================================

_n("ApplyDamage", "UGameplayStatics", "damage",
   "Applies generic damage to actor",
   ["damage", "combat", "health"])
_n("ApplyPointDamage", "UGameplayStatics", "damage",
   "Applies damage with hit direction/location",
   ["damage", "combat", "health"])
_n("ApplyRadialDamage", "UGameplayStatics", "damage",
   "Applies damage to all actors in sphere",
   ["damage", "combat", "health"])
_n("ApplyRadialDamageWithFalloff", "UGameplayStatics", "damage",
   "Radial damage with inner/outer radius falloff",
   ["damage", "combat", "health"])

# ===================================================================
# PLAYER & CONTROLLER  (14 nodes)
# ===================================================================

_n("GetPlayerController", "UGameplayStatics", "player",
   "Returns player controller at index",
   ["player", "controller", "pawn"])
_n("GetPlayerControllerFromID", "UGameplayStatics", "player",
   "Gets controller by physical controller ID",
   ["player", "controller", "pawn"])
_n("GetPlayerControllerID", "UGameplayStatics", "player",
   "Gets physical ID from controller",
   ["player", "controller", "pawn"])
_n("SetPlayerControllerID", "UGameplayStatics", "player",
   "Assigns physical controller ID",
   ["player", "controller", "pawn"])
_n("GetNumPlayerControllers", "UGameplayStatics", "player",
   "Total player controllers",
   ["player", "controller", "pawn"])
_n("GetNumLocalPlayerControllers", "UGameplayStatics", "player",
   "Local player controller count",
   ["player", "controller", "pawn"])
_n("GetPlayerPawn", "UGameplayStatics", "player",
   "Returns player's pawn",
   ["player", "controller", "pawn"])
_n("GetPlayerCharacter", "UGameplayStatics", "player",
   "Returns player's character",
   ["player", "controller", "pawn"])
_n("GetPlayerCameraManager", "UGameplayStatics", "player",
   "Returns camera manager",
   ["player", "controller", "pawn"])
_n("GetPlayerState", "UGameplayStatics", "player",
   "Returns player state by index",
   ["player", "controller", "pawn"])
_n("GetPlayerStateFromUniqueNetId", "UGameplayStatics", "player",
   "Player state by network ID",
   ["player", "controller", "pawn"])
_n("GetNumPlayerStates", "UGameplayStatics", "player",
   "Active player state count",
   ["player", "controller", "pawn"])
_n("CreatePlayer", "UGameplayStatics", "player",
   "Creates new local player",
   ["player", "controller", "pawn"])
_n("RemovePlayer", "UGameplayStatics", "player",
   "Removes local player",
   ["player", "controller", "pawn"])

# ===================================================================
# ACTOR QUERIES  (8 nodes)
# ===================================================================

_n("GetActorOfClass", "UGameplayStatics", "actor",
   "Finds first actor of class (SLOW)",
   ["actor", "query", "find"])
_n("GetAllActorsOfClass", "UGameplayStatics", "actor",
   "Finds all actors of class",
   ["actor", "query", "find"])
_n("GetAllActorsWithTag", "UGameplayStatics", "actor",
   "Finds all actors with tag",
   ["actor", "query", "find"])
_n("GetAllActorsOfClassWithTag", "UGameplayStatics", "actor",
   "Finds actors matching class AND tag",
   ["actor", "query", "find"])
_n("GetAllActorsWithInterface", "UGameplayStatics", "actor",
   "Finds actors implementing interface",
   ["actor", "query", "find"])
_n("FindNearestActor", "UGameplayStatics", "actor",
   "Returns closest actor from array",
   ["actor", "query", "find"])
_n("GetActorArrayAverageLocation", "UGameplayStatics", "actor",
   "Centroid of actor array",
   ["actor", "query", "find"])
_n("GetActorArrayBounds", "UGameplayStatics", "actor",
   "Bounding box of actor collection",
   ["actor", "query", "find"])

# ===================================================================
# PROJECTILE PREDICTION  (5 nodes)
# ===================================================================

_n("BlueprintPredictProjectilePath_Advanced", "UGameplayStatics", "projectile",
   "Full projectile prediction with collision",
   ["projectile", "trajectory", "physics"])
_n("BlueprintPredictProjectilePath_ByObjectType", "UGameplayStatics", "projectile",
   "Prediction by object types",
   ["projectile", "trajectory", "physics"])
_n("BlueprintPredictProjectilePath_ByTraceChannel", "UGameplayStatics", "projectile",
   "Prediction by trace channel",
   ["projectile", "trajectory", "physics"])
_n("Blueprint_PredictProjectilePath_ByTraceChannel", "UGameplayStatics", "projectile",
   "Prediction by trace (newer overload)",
   ["projectile", "trajectory", "physics"])
_n("SuggestProjectileVelocity", "UGameplayStatics", "projectile",
   "Calculates launch velocity to hit target",
   ["projectile", "trajectory", "physics"])

# ===================================================================
# LEVEL & WORLD  (14 nodes)
# ===================================================================

_n("GetCurrentLevelName", "UGameplayStatics", "level_world",
   "Returns name of current level",
   ["level", "world", "streaming"])
_n("OpenLevel", "UGameplayStatics", "level_world",
   "Travels to another level",
   ["level", "world", "streaming"])
_n("OpenLevelBySoftObjectPtr", "UGameplayStatics", "level_world",
   "Level travel via soft reference",
   ["level", "world", "streaming"])
_n("LoadStreamLevel", "UGameplayStatics", "level_world",
   "Async streams in a level",
   ["level", "world", "streaming"])
_n("LoadStreamLevelBySoftObjectPtr", "UGameplayStatics", "level_world",
   "Streams level via soft reference",
   ["level", "world", "streaming"])
_n("UnloadStreamLevel", "UGameplayStatics", "level_world",
   "Unloads streamed level",
   ["level", "world", "streaming"])
_n("UnloadStreamLevelBySoftObjectPtr", "UGameplayStatics", "level_world",
   "Unloads via soft reference",
   ["level", "world", "streaming"])
_n("GetStreamingLevel", "UGameplayStatics", "level_world",
   "Returns streaming level object",
   ["level", "world", "streaming"])
_n("FlushLevelStreaming", "UGameplayStatics", "level_world",
   "Blocks until streaming completes",
   ["level", "world", "streaming"])
_n("CancelAsyncLoading", "UGameplayStatics", "level_world",
   "Cancels queued streaming",
   ["level", "world", "streaming"])
_n("GetWorldOriginLocation", "UGameplayStatics", "level_world",
   "Returns world origin position",
   ["level", "world", "streaming"])
_n("SetWorldOriginLocation", "UGameplayStatics", "level_world",
   "Sets world origin (origin rebasing)",
   ["level", "world", "streaming"])
_n("RebaseZeroOriginOntoLocal", "UGameplayStatics", "level_world",
   "Converts origin-based to local coords",
   ["level", "world", "streaming"])
_n("RebaseLocalOriginOntoZero", "UGameplayStatics", "level_world",
   "Converts local to origin-based coords",
   ["level", "world", "streaming"])

# ===================================================================
# TIME  (8 nodes)
# ===================================================================

_n("GetTimeSeconds", "UGameplayStatics", "time",
   "Game time (affected by pause+dilation)",
   ["time", "delta", "dilation"])
_n("GetUnpausedTimeSeconds", "UGameplayStatics", "time",
   "Time not affected by pause",
   ["time", "delta", "dilation"])
_n("GetRealTimeSeconds", "UGameplayStatics", "time",
   "Real-time (not pause/dilation affected)",
   ["time", "delta", "dilation"])
_n("GetAccurateRealTime", "UGameplayStatics", "time",
   "Precise real time at call moment",
   ["time", "delta", "dilation"])
_n("GetAudioTimeSeconds", "UGameplayStatics", "time",
   "Audio-synced time",
   ["time", "delta", "dilation"])
_n("GetWorldDeltaSeconds", "UGameplayStatics", "time",
   "Frame delta time with dilation",
   ["time", "delta", "dilation"])
_n("GetGlobalTimeDilation", "UGameplayStatics", "time",
   "Current time dilation value",
   ["time", "delta", "dilation"])
_n("SetGlobalTimeDilation", "UGameplayStatics", "time",
   "Sets global time dilation",
   ["time", "delta", "dilation"])

# ===================================================================
# GAME STATE  (6 nodes)
# ===================================================================

_n("GetGameMode", "UGameplayStatics", "game_state",
   "Returns current GameMode",
   ["gamemode", "gamestate", "pause"])
_n("GetGameState", "UGameplayStatics", "game_state",
   "Returns current GameState",
   ["gamemode", "gamestate", "pause"])
_n("GetGameInstance", "UGameplayStatics", "game_state",
   "Returns the GameInstance",
   ["gamemode", "gamestate", "pause"])
_n("SetGamePaused", "UGameplayStatics", "game_state",
   "Pauses/unpauses the game",
   ["gamemode", "gamestate", "pause"])
_n("IsGamePaused", "UGameplayStatics", "game_state",
   "Returns pause state",
   ["gamemode", "gamestate", "pause"])
_n("GetObjectClass", "UGameplayStatics", "game_state",
   "Returns class of object",
   ["gamemode", "gamestate", "pause"])

# ===================================================================
# CAMERA & VIEWPORT  (5 nodes)
# ===================================================================

_n("ProjectWorldToScreen", "UGameplayStatics", "camera",
   "3D world to 2D screen",
   ["camera", "viewport", "screen"])
_n("DeprojectScreenToWorld", "UGameplayStatics", "camera",
   "2D screen to 3D world",
   ["camera", "viewport", "screen"])
_n("GetViewProjectionMatrix", "UGameplayStatics", "camera",
   "Returns view/projection matrices",
   ["camera", "viewport", "screen"])
_n("GetViewportMouseCaptureMode", "UGameplayStatics", "camera",
   "Returns mouse capture mode",
   ["camera", "viewport", "screen"])
_n("PlayWorldCameraShake", "UGameplayStatics", "camera",
   "Plays camera shake for nearby players",
   ["camera", "viewport", "screen"])

# ===================================================================
# SAVE GAME  (7 nodes)
# ===================================================================

_n("CreateSaveGameObject", "UGameplayStatics", "save_game",
   "Creates new SaveGame instance",
   ["save", "load", "persistence"])
_n("SaveGameToSlot", "UGameplayStatics", "save_game",
   "Saves to named slot",
   ["save", "load", "persistence"])
_n("LoadGameFromSlot", "UGameplayStatics", "save_game",
   "Loads from named slot",
   ["save", "load", "persistence"])
_n("DeleteGameInSlot", "UGameplayStatics", "save_game",
   "Deletes save file",
   ["save", "load", "persistence"])
_n("DoesSaveGameExist", "UGameplayStatics", "save_game",
   "Checks if save slot exists",
   ["save", "load", "persistence"])
_n("AsyncSaveGameToSlot", "UGameplayStatics", "save_game",
   "Async save game",
   ["save", "load", "persistence"])
_n("AsyncLoadGameFromSlot", "UGameplayStatics", "save_game",
   "Async load game",
   ["save", "load", "persistence"])

# ===================================================================
# SPAWNING  (5 nodes)
# ===================================================================

_n("BeginDeferredActorSpawnFromClass", "UGameplayStatics", "spawning",
   "Deferred spawn (call FinishSpawning later)",
   ["spawn", "actor", "create"])
_n("FinishSpawningActor", "UGameplayStatics", "spawning",
   "Finishes deferred spawn",
   ["spawn", "actor", "create"])
_n("SpawnObject", "UGameplayStatics", "spawning",
   "Spawns non-actor UObject",
   ["spawn", "actor", "create"])
_n("BeginSpawningActorFromBlueprint", "UGameplayStatics", "spawning",
   "Begins spawning from Blueprint class",
   ["spawn", "actor", "create"])
_n("BeginSpawningActorFromClass", "UGameplayStatics", "spawning",
   "Begins spawning from class",
   ["spawn", "actor", "create"])

# ===================================================================
# PARTICLE EFFECTS  (2 nodes)
# ===================================================================

_n("SpawnEmitterAtLocation", "UGameplayStatics", "effects",
   "Spawns particle effect at location",
   ["effects", "particle", "vfx"])
_n("SpawnEmitterAttached", "UGameplayStatics", "effects",
   "Spawns particle attached to component",
   ["effects", "particle", "vfx"])

# ===================================================================
# DECALS  (2 nodes)
# ===================================================================

_n("SpawnDecalAtLocation", "UGameplayStatics", "effects",
   "Spawns decal at location",
   ["effects", "decal", "rendering"])
_n("SpawnDecalAttached", "UGameplayStatics", "effects",
   "Spawns decal attached to component",
   ["effects", "decal", "rendering"])

# ===================================================================
# FORCE FEEDBACK / HAPTICS  (3 nodes)
# ===================================================================

_n("SpawnForceFeedbackAtLocation", "UGameplayStatics", "haptics",
   "Spawns force feedback at location",
   ["haptics", "feedback", "controller"])
_n("SpawnForceFeedbackAttached", "UGameplayStatics", "haptics",
   "Spawns force feedback on component",
   ["haptics", "feedback", "controller"])
_n("PlayForceFeedback", "UGameplayStatics", "haptics",
   "Plays force feedback effect",
   ["haptics", "feedback", "controller"])

# ===================================================================
# OPTION PARSING  (4 nodes)
# ===================================================================

_n("ParseOption", "UGameplayStatics", "option_parsing",
   "Extracts value from 'key=value' string",
   ["option", "parse", "config"])
_n("HasOption", "UGameplayStatics", "option_parsing",
   "Checks if key exists in option string",
   ["option", "parse", "config"])
_n("GetKeyValue", "UGameplayStatics", "option_parsing",
   "Splits key=value pair",
   ["option", "parse", "config"])
_n("GetIntOption", "UGameplayStatics", "option_parsing",
   "Extracts int from option string",
   ["option", "parse", "config"])

# ===================================================================
# PLATFORM / MISC  (9 nodes)
# ===================================================================

_n("GetPlatformName", "UGameplayStatics", "platform",
   "Returns platform identifier",
   ["platform", "system", "misc"])
_n("EnableLiveStreaming", "UGameplayStatics", "platform",
   "Toggles DVR streaming",
   ["platform", "system", "misc"])
_n("AnnounceAccessibleString", "UGameplayStatics", "platform",
   "Announces text via accessibility system",
   ["platform", "system", "misc"])
_n("SetForceDisableSplitscreen", "UGameplayStatics", "platform",
   "Force disable/enable splitscreen",
   ["platform", "system", "misc"])
_n("IsSplitscreenForceDisabled", "UGameplayStatics", "platform",
   "Checks splitscreen state",
   ["platform", "system", "misc"])
_n("SetEnableWorldRendering", "UGameplayStatics", "platform",
   "Toggles world rendering",
   ["platform", "system", "misc"])
_n("GetEnableWorldRendering", "UGameplayStatics", "platform",
   "Returns world rendering state",
   ["platform", "system", "misc"])
_n("GrassOverlappingSphereCount", "UGameplayStatics", "platform",
   "Counts grass instances in sphere",
   ["platform", "system", "misc"])
_n("FindCollisionUV", "UGameplayStatics", "platform",
   "Gets UV coordinates from hit result",
   ["platform", "system", "misc"])
