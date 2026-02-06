"""WAAPI function catalogue — all 87 functions + 17 subscription topics.

Complete reference for every callable WAAPI endpoint, organised by namespace.
Used by:
  - The MCP tool layer (execute_waapi validation + hints)
  - The knowledge DB seeder (bulk upload to SQLite/D1)
  - The semantic search tool (description + tag matching)

All data sourced from research/research_waapi_mcp_server.md Section 4
and Audiokinetic's official WAAPI documentation.
"""

from __future__ import annotations


# ===================================================================
# Helper types
# ===================================================================

FunctionDef = dict   # Full function definition
TopicDef = dict      # Subscription topic definition


def _func(
    uri: str,
    namespace: str,
    description: str,
    params: list[str] | None = None,
    returns: str | None = None,
    tags: list[str] | None = None,
    critical: bool = False,
) -> FunctionDef:
    """Build a WAAPI function definition."""
    return {
        "uri": uri,
        "namespace": namespace,
        "description": description,
        "params": params or [],
        "returns": returns,
        "tags": tags or [],
        "critical": critical,
    }


def _topic(
    uri: str,
    description: str,
    category: str,
    tags: list[str] | None = None,
) -> TopicDef:
    """Build a subscription topic definition."""
    return {
        "uri": uri,
        "description": description,
        "category": category,
        "tags": tags or [],
    }


# ===================================================================
# WAAPI_FUNCTIONS — keyed by URI, 87 entries
# ===================================================================

WAAPI_FUNCTIONS: dict[str, FunctionDef] = {}


def _reg(func: FunctionDef) -> None:
    WAAPI_FUNCTIONS[func["uri"]] = func


# -------------------------------------------------------------------
# ak.wwise.core.object (15 functions)
# -------------------------------------------------------------------

_reg(_func(
    "ak.wwise.core.object.create", "object",
    "Create any Wwise object type in the hierarchy.",
    ["parent", "type", "name", "onNameConflict", "children"],
    "id, name, type, path",
    ["create", "object", "hierarchy", "CRUD"],
    critical=True,
))

_reg(_func(
    "ak.wwise.core.object.delete", "object",
    "Delete objects from the hierarchy.",
    ["object"],
    None,
    ["delete", "remove", "object", "CRUD"],
))

_reg(_func(
    "ak.wwise.core.object.get", "object",
    "Query objects using WAQL or property filters.",
    ["waql", "from", "select"],
    "return (array of objects)",
    ["query", "search", "WAQL", "find", "object"],
    critical=True,
))

_reg(_func(
    "ak.wwise.core.object.move", "object",
    "Move objects to a new parent in the hierarchy.",
    ["object", "parent"],
    None,
    ["move", "hierarchy", "reorganise"],
))

_reg(_func(
    "ak.wwise.core.object.copy", "object",
    "Copy objects to a new parent.",
    ["object", "parent", "newName"],
    "id, name",
    ["copy", "duplicate", "clone"],
))

_reg(_func(
    "ak.wwise.core.object.setName", "object",
    "Rename an existing object.",
    ["object", "name"],
    None,
    ["rename", "name"],
))

_reg(_func(
    "ak.wwise.core.object.setNotes", "object",
    "Add notes/metadata to an object.",
    ["object", "notes"],
    None,
    ["notes", "metadata", "annotation"],
))

_reg(_func(
    "ak.wwise.core.object.setProperty", "object",
    "Set a property value on an object (Volume, Pitch, etc.).",
    ["object", "property", "value"],
    None,
    ["property", "set", "volume", "pitch", "parameter"],
    critical=True,
))

_reg(_func(
    "ak.wwise.core.object.setReference", "object",
    "Set a reference on an object (OutputBus, Attenuation, etc.).",
    ["object", "reference", "value"],
    None,
    ["reference", "bus", "attenuation", "routing"],
    critical=True,
))

_reg(_func(
    "ak.wwise.core.object.getPropertyInfo", "object",
    "Get metadata/constraints for a property.",
    ["object", "property"],
    "propertyInfo",
    ["property", "info", "metadata"],
))

_reg(_func(
    "ak.wwise.core.object.getPropertyNames", "object",
    "List all available properties for an object type.",
    ["object"],
    "propertyNames (array)",
    ["property", "list", "discovery"],
))

_reg(_func(
    "ak.wwise.core.object.isPropertyEnabled", "object",
    "Check if a property is active/enabled on an object.",
    ["object", "property"],
    "enabled (bool)",
    ["property", "state", "enabled"],
))

_reg(_func(
    "ak.wwise.core.object.getTypes", "object",
    "Get all available Wwise object types.",
    [],
    "types (array)",
    ["types", "discovery", "schema"],
))

_reg(_func(
    "ak.wwise.core.object.getAttenuationCurve", "object",
    "Read attenuation curve points for an object.",
    ["object", "curveType"],
    "points, curveType",
    ["attenuation", "curve", "distance", "3D"],
))

_reg(_func(
    "ak.wwise.core.object.setAttenuationCurve", "object",
    "Write attenuation curve with specified points.",
    ["object", "curveType", "use", "points"],
    None,
    ["attenuation", "curve", "distance", "3D", "spatialization"],
))

# -------------------------------------------------------------------
# ak.wwise.core.audio (2 functions)
# -------------------------------------------------------------------

_reg(_func(
    "ak.wwise.core.audio.import", "audio",
    "Import WAV/audio files into the Wwise hierarchy.",
    ["importOperation", "default", "imports"],
    "objects (array)",
    ["import", "audio", "WAV", "file", "media"],
    critical=True,
))

_reg(_func(
    "ak.wwise.core.audio.importTabDelimited", "audio",
    "Batch import from tab-delimited file.",
    ["file", "importOperation", "default"],
    "objects (array)",
    ["import", "batch", "tab", "file"],
))

# -------------------------------------------------------------------
# ak.wwise.core.switchContainer (3 functions)
# -------------------------------------------------------------------

_reg(_func(
    "ak.wwise.core.switchContainer.addAssignment", "switchContainer",
    "Assign a child object to a switch/state value.",
    ["child", "stateOrSwitch"],
    None,
    ["switch", "state", "assign", "container"],
    critical=True,
))

_reg(_func(
    "ak.wwise.core.switchContainer.removeAssignment", "switchContainer",
    "Remove a child from a switch/state assignment.",
    ["child", "stateOrSwitch"],
    None,
    ["switch", "state", "unassign", "container"],
))

_reg(_func(
    "ak.wwise.core.switchContainer.getAssignments", "switchContainer",
    "Get all switch/state assignments for a container.",
    ["id"],
    "assignments (array)",
    ["switch", "state", "list", "container"],
))

# -------------------------------------------------------------------
# ak.soundengine (21 functions)
# -------------------------------------------------------------------

_reg(_func(
    "ak.soundengine.postEvent", "soundengine",
    "Post an event to the sound engine for playback.",
    ["eventName", "gameObjectID"],
    "playingID",
    ["event", "play", "runtime", "playback"],
    critical=True,
))

_reg(_func(
    "ak.soundengine.executeActionOnEvent", "soundengine",
    "Execute action on a running event (stop, pause, resume).",
    ["eventID", "action"],
    None,
    ["event", "action", "stop", "pause", "resume"],
))

_reg(_func(
    "ak.soundengine.registerGameObj", "soundengine",
    "Register a game object for 3D spatialization.",
    ["gameObjectID", "name"],
    None,
    ["game object", "register", "3D", "spatial"],
))

_reg(_func(
    "ak.soundengine.unregisterGameObj", "soundengine",
    "Unregister a game object.",
    ["gameObjectID"],
    None,
    ["game object", "unregister"],
))

_reg(_func(
    "ak.soundengine.setSwitch", "soundengine",
    "Set a switch value at runtime for a game object.",
    ["switchGroup", "switchValue", "gameObjectID"],
    None,
    ["switch", "runtime", "state"],
))

_reg(_func(
    "ak.soundengine.setRTPCValue", "soundengine",
    "Set RTPC (Game Parameter) value at runtime.",
    ["rtpcName", "value", "gameObjectID"],
    None,
    ["RTPC", "game parameter", "value", "runtime"],
    critical=True,
))

_reg(_func(
    "ak.soundengine.resetRTPCValue", "soundengine",
    "Reset RTPC to its default value.",
    ["rtpcName", "gameObjectID"],
    None,
    ["RTPC", "reset", "default"],
))

_reg(_func(
    "ak.soundengine.setPosition", "soundengine",
    "Set 3D position for a game object.",
    ["gameObjectID", "position"],
    None,
    ["position", "3D", "spatial", "location"],
))

_reg(_func(
    "ak.soundengine.setMultiplePositions", "soundengine",
    "Set multiple 3D positions for advanced spatialization.",
    ["gameObjectID", "positions"],
    None,
    ["position", "3D", "multi", "emitter"],
))

_reg(_func(
    "ak.soundengine.setListeners", "soundengine",
    "Assign listeners to a game object.",
    ["gameObjectID", "listenerIDs"],
    None,
    ["listener", "3D", "spatial", "assign"],
))

_reg(_func(
    "ak.soundengine.setDefaultListeners", "soundengine",
    "Set the default listener(s) for the sound engine.",
    ["listenerIDs"],
    None,
    ["listener", "default", "3D"],
))

_reg(_func(
    "ak.soundengine.setScalingFactor", "soundengine",
    "Set distance scaling factor for 3D audio.",
    ["scalingFactor"],
    None,
    ["distance", "scaling", "3D", "attenuation"],
))

_reg(_func(
    "ak.soundengine.setListenerSpatialization", "soundengine",
    "Configure listener spatialization (HRTF, height).",
    ["listenerID", "spatializationConfig"],
    None,
    ["listener", "spatialization", "HRTF", "binaural"],
))

_reg(_func(
    "ak.soundengine.setObjectObstructionAndOcclusion", "soundengine",
    "Set obstruction and occlusion values for a game object.",
    ["gameObjectID", "obstruction", "occlusion"],
    None,
    ["obstruction", "occlusion", "3D", "environment"],
))

_reg(_func(
    "ak.soundengine.setGameObjectOutputBusVolume", "soundengine",
    "Set per-object output bus volume.",
    ["gameObjectID", "busID", "volume"],
    None,
    ["volume", "bus", "per-object"],
))

_reg(_func(
    "ak.soundengine.setGameObjectAuxSendValues", "soundengine",
    "Set auxiliary send levels for a game object.",
    ["gameObjectID", "auxBusID", "sendLevel"],
    None,
    ["aux", "send", "reverb", "effect"],
))

_reg(_func(
    "ak.soundengine.postTrigger", "soundengine",
    "Post a trigger (for legacy stinger/transition events).",
    ["triggerName", "gameObjectID"],
    None,
    ["trigger", "stinger", "transition", "legacy"],
))

_reg(_func(
    "ak.soundengine.seekOnEvent", "soundengine",
    "Seek to a position in a playing event.",
    ["eventID", "position"],
    None,
    ["seek", "position", "playback"],
))

_reg(_func(
    "ak.soundengine.stopPlayingID", "soundengine",
    "Stop a sound by its playing ID.",
    ["playingID"],
    None,
    ["stop", "playback"],
))

_reg(_func(
    "ak.soundengine.stopAll", "soundengine",
    "Stop all sounds on a game object.",
    ["gameObjectID"],
    None,
    ["stop", "all", "silence"],
))

_reg(_func(
    "ak.soundengine.postMsgMonitor", "soundengine",
    "Post a message to the Wwise profiler/monitor.",
    ["message"],
    None,
    ["monitor", "debug", "profiler", "message"],
))

# -------------------------------------------------------------------
# ak.wwise.core.project (1 function)
# -------------------------------------------------------------------

_reg(_func(
    "ak.wwise.core.project.save", "project",
    "Save the current Wwise project.",
    [],
    None,
    ["save", "project", "persist"],
    critical=True,
))

# -------------------------------------------------------------------
# ak.wwise.core.soundbank (3 functions)
# -------------------------------------------------------------------

_reg(_func(
    "ak.wwise.core.soundbank.getInclusions", "soundbank",
    "Get the list of objects included in a SoundBank.",
    ["soundbank"],
    "inclusions (array)",
    ["soundbank", "inclusion", "list"],
))

_reg(_func(
    "ak.wwise.core.soundbank.setInclusions", "soundbank",
    "Set which objects/events to include in a SoundBank.",
    ["soundbank", "operation", "inclusions"],
    None,
    ["soundbank", "inclusion", "set", "configure"],
))

_reg(_func(
    "ak.wwise.core.soundbank.generate", "soundbank",
    "Generate SoundBank files for deployment.",
    ["soundbanks", "platforms", "skipLanguages"],
    "logs",
    ["soundbank", "generate", "build", "deploy"],
    critical=True,
))

# -------------------------------------------------------------------
# ak.wwise.core.transport (5 functions)
# -------------------------------------------------------------------

_reg(_func(
    "ak.wwise.core.transport.create", "transport",
    "Create a transport instance for previewing objects/events.",
    ["object"],
    "transport (id)",
    ["transport", "preview", "create"],
))

_reg(_func(
    "ak.wwise.core.transport.destroy", "transport",
    "Destroy a transport instance.",
    ["transport"],
    None,
    ["transport", "destroy", "cleanup"],
))

_reg(_func(
    "ak.wwise.core.transport.getState", "transport",
    "Get the playback state of a transport.",
    ["transport"],
    "state",
    ["transport", "state", "status"],
))

_reg(_func(
    "ak.wwise.core.transport.getList", "transport",
    "List all active transport instances.",
    [],
    "list (array)",
    ["transport", "list", "active"],
))

_reg(_func(
    "ak.wwise.core.transport.executeAction", "transport",
    "Execute play/stop/pause on a transport.",
    ["transport", "action"],
    None,
    ["transport", "play", "stop", "pause", "preview"],
    critical=True,
))

# -------------------------------------------------------------------
# ak.wwise.ui (5 functions)
# -------------------------------------------------------------------

_reg(_func(
    "ak.wwise.ui.bringToForeground", "ui",
    "Bring the Wwise window to the foreground.",
    [],
    None,
    ["UI", "window", "foreground"],
))

_reg(_func(
    "ak.wwise.ui.project.open", "ui",
    "Open a Wwise project file.",
    ["filepath"],
    None,
    ["project", "open", "UI"],
))

_reg(_func(
    "ak.wwise.ui.project.close", "ui",
    "Close the current Wwise project.",
    [],
    None,
    ["project", "close", "UI"],
))

_reg(_func(
    "ak.wwise.ui.getSelectedObjects", "ui",
    "Get the currently selected objects in the Wwise UI.",
    [],
    "objects (array)",
    ["UI", "selection", "selected"],
))

_reg(_func(
    "ak.wwise.ui.commands.execute", "ui",
    "Execute a Wwise UI command by name.",
    ["commandName", "commandArgs"],
    None,
    ["UI", "command", "execute"],
))

# -------------------------------------------------------------------
# ak.wwise.core.undo (3 functions)
# -------------------------------------------------------------------

_reg(_func(
    "ak.wwise.core.undo.beginGroup", "undo",
    "Start an atomic undo group for batch operations.",
    [],
    None,
    ["undo", "transaction", "begin", "batch"],
    critical=True,
))

_reg(_func(
    "ak.wwise.core.undo.endGroup", "undo",
    "End an atomic undo group.",
    ["displayName"],
    None,
    ["undo", "transaction", "end", "batch"],
    critical=True,
))

_reg(_func(
    "ak.wwise.core.undo.cancelGroup", "undo",
    "Cancel an undo group without applying changes.",
    [],
    None,
    ["undo", "cancel", "rollback"],
))

# -------------------------------------------------------------------
# ak.wwise.core.remote (4 functions)
# -------------------------------------------------------------------

_reg(_func(
    "ak.wwise.core.remote.connect", "remote",
    "Connect to a remote game console.",
    ["platformName", "port"],
    None,
    ["remote", "console", "connect", "game"],
))

_reg(_func(
    "ak.wwise.core.remote.disconnect", "remote",
    "Disconnect from remote game.",
    [],
    None,
    ["remote", "disconnect"],
))

_reg(_func(
    "ak.wwise.core.remote.getAvailableConsoles", "remote",
    "List available console connections.",
    [],
    "consoles (array)",
    ["remote", "console", "list", "discovery"],
))

_reg(_func(
    "ak.wwise.core.remote.getConnectionStatus", "remote",
    "Get the current remote connection status.",
    [],
    "status",
    ["remote", "status", "connection"],
))

# -------------------------------------------------------------------
# ak.wwise.core.plugin (1 function)
# -------------------------------------------------------------------

_reg(_func(
    "ak.wwise.core.plugin.getList", "plugin",
    "Get the list of installed Wwise plugins.",
    [],
    "plugins (array)",
    ["plugin", "list", "discovery"],
))

# -------------------------------------------------------------------
# ak.wwise.waapi (3 functions)
# -------------------------------------------------------------------

_reg(_func(
    "ak.wwise.waapi.getFunctions", "waapi",
    "List all available WAAPI functions.",
    [],
    "functions (array)",
    ["WAAPI", "introspection", "discovery"],
))

_reg(_func(
    "ak.wwise.waapi.getTopics", "waapi",
    "List all available subscription topics.",
    [],
    "topics (array)",
    ["WAAPI", "topics", "subscription", "discovery"],
))

_reg(_func(
    "ak.wwise.waapi.getSchema", "waapi",
    "Get JSON schema for a WAAPI function or topic.",
    ["functionURI"],
    "schema (JSON)",
    ["WAAPI", "schema", "introspection"],
))


# ===================================================================
# WAAPI_TOPICS — 17 subscription events
# ===================================================================

WAAPI_TOPICS: dict[str, TopicDef] = {}


def _reg_topic(topic: TopicDef) -> None:
    WAAPI_TOPICS[topic["uri"]] = topic


# Object events (10)
_reg_topic(_topic(
    "ak.wwise.core.object.created",
    "Fires when an object is created.",
    "object",
    ["object", "created", "lifecycle"],
))

_reg_topic(_topic(
    "ak.wwise.core.object.preDeleted",
    "Fires before an object is deleted.",
    "object",
    ["object", "delete", "pre", "lifecycle"],
))

_reg_topic(_topic(
    "ak.wwise.core.object.postDeleted",
    "Fires after an object is deleted.",
    "object",
    ["object", "delete", "post", "lifecycle"],
))

_reg_topic(_topic(
    "ak.wwise.core.object.nameChanged",
    "Fires when an object is renamed.",
    "object",
    ["object", "rename", "name"],
))

_reg_topic(_topic(
    "ak.wwise.core.object.propertyChanged",
    "Fires when a property is modified on an object.",
    "object",
    ["object", "property", "change"],
))

_reg_topic(_topic(
    "ak.wwise.core.object.referenceChanged",
    "Fires when a reference is modified on an object.",
    "object",
    ["object", "reference", "change"],
))

_reg_topic(_topic(
    "ak.wwise.core.object.childAdded",
    "Fires when a child is added to an object.",
    "object",
    ["object", "child", "added", "hierarchy"],
))

_reg_topic(_topic(
    "ak.wwise.core.object.childRemoved",
    "Fires when a child is removed from an object.",
    "object",
    ["object", "child", "removed", "hierarchy"],
))

_reg_topic(_topic(
    "ak.wwise.core.object.curveChanged",
    "Fires when a curve is modified on an object.",
    "object",
    ["object", "curve", "change"],
))

_reg_topic(_topic(
    "ak.wwise.core.object.attenuationCurveChanged",
    "Fires when an attenuation curve is changed.",
    "object",
    ["attenuation", "curve", "change", "3D"],
))

# Container events (2)
_reg_topic(_topic(
    "ak.wwise.core.switchContainer.assignmentAdded",
    "Fires when a switch assignment is added.",
    "container",
    ["switch", "assignment", "added"],
))

_reg_topic(_topic(
    "ak.wwise.core.switchContainer.assignmentRemoved",
    "Fires when a switch assignment is removed.",
    "container",
    ["switch", "assignment", "removed"],
))

# Project events (3)
_reg_topic(_topic(
    "ak.wwise.core.project.loaded",
    "Fires when a project is loaded.",
    "project",
    ["project", "loaded", "lifecycle"],
))

_reg_topic(_topic(
    "ak.wwise.core.project.preClosed",
    "Fires before a project is closed.",
    "project",
    ["project", "close", "pre"],
))

_reg_topic(_topic(
    "ak.wwise.core.project.postClosed",
    "Fires after a project is closed.",
    "project",
    ["project", "close", "post"],
))

# Transport events (1)
_reg_topic(_topic(
    "ak.wwise.core.transport.stateChanged",
    "Fires when a transport's playback state changes.",
    "transport",
    ["transport", "state", "playback"],
))

# UI events (1)
_reg_topic(_topic(
    "ak.wwise.ui.selectionChanged",
    "Fires when the selection changes in the Wwise UI.",
    "ui",
    ["UI", "selection", "change"],
))


# ===================================================================
# Query / search helpers
# ===================================================================

def get_functions_by_namespace(namespace: str) -> list[FunctionDef]:
    """Return all functions in a namespace (case-insensitive)."""
    ns = namespace.lower()
    return [f for f in WAAPI_FUNCTIONS.values() if f["namespace"].lower() == ns]


def get_critical_functions() -> list[FunctionDef]:
    """Return functions marked as critical for MCP tool building."""
    return [f for f in WAAPI_FUNCTIONS.values() if f["critical"]]


def search_functions(query: str) -> list[FunctionDef]:
    """Substring search across URI, description, and tags."""
    q = query.lower()
    uri_hits: list[FunctionDef] = []
    tag_hits: list[FunctionDef] = []
    desc_hits: list[FunctionDef] = []
    seen: set[str] = set()

    for func in WAAPI_FUNCTIONS.values():
        uid = func["uri"]
        if q in func["uri"].lower():
            uri_hits.append(func)
            seen.add(uid)
        elif any(q in t.lower() for t in func["tags"]):
            if uid not in seen:
                tag_hits.append(func)
                seen.add(uid)
        elif q in func["description"].lower():
            if uid not in seen:
                desc_hits.append(func)
    return uri_hits + tag_hits + desc_hits


def get_all_namespaces() -> dict[str, int]:
    """Return a dict of namespace -> number of functions."""
    counts: dict[str, int] = {}
    for func in WAAPI_FUNCTIONS.values():
        ns = func["namespace"]
        counts[ns] = counts.get(ns, 0) + 1
    return dict(sorted(counts.items()))
