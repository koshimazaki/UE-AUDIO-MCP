# WAAPI MCP Server Research Summary

_Generated: 2026-02-06 | Sources: 25+ | Scope: Building an MCP server for Wwise project automation_

## Quick Reference

<key-points>
- WAAPI uses WebSocket (WAMP protocol) on ws://127.0.0.1:8080/waapi or HTTP POST on port 8090
- Wwise MUST be running with WAAPI enabled -- no true headless mode exists
- 87+ API functions covering object CRUD, audio import, soundbanks, transport, RTPC, switch containers
- Two Python libraries: `waapi-client` (official, low-level) and `pywwise` (Pythonic wrapper)
- Key MCP tools to build: create_object, import_audio, create_event, set_property, build_hierarchy, generate_soundbank
- AudioLink (UE5.1+) enables one-way MetaSounds-to-Wwise routing; Wwise cannot feed back into MetaSounds
</key-points>

---

## 1. WAAPI Capabilities -- What You Can Do Programmatically

### 1.1 Object Creation and Management

Every Wwise object type can be created via `ak.wwise.core.object.create`:

**Wwise Object Types (WAAPI type strings):**

| Type String | Purpose |
|---|---|
| `Sound` | Basic sound SFX object |
| `RandomSequenceContainer` | Random/sequence playback of children |
| `SwitchContainer` | Switch/state-driven playback |
| `BlendContainer` | Simultaneous playback with RTPC blending |
| `ActorMixer` | Grouping/routing parent |
| `Event` | Game-facing trigger |
| `Action` | What an event does (Play, Stop, etc.) |
| `Bus` | Audio bus for mixing |
| `AuxBus` | Auxiliary bus (reverb sends, etc.) |
| `WorkUnit` | Organizational work unit |
| `Folder` | Organizational folder |
| `Attenuation` | Distance attenuation ShareSet |
| `SoundBank` | Bank for packaging |
| `GameParameter` | RTPC game parameter |
| `Switch` | Switch type |
| `State` | State type |
| `Trigger` | Trigger type |

**Create Object Example (Python):**
```python
from waapi import WaapiClient

with WaapiClient() as client:
    # Create a Random Container under the Default Work Unit
    result = client.call("ak.wwise.core.object.create", {
        "parent": "\\Actor-Mixer Hierarchy\\Default Work Unit",
        "type": "RandomSequenceContainer",
        "name": "Gunshot_Variations",
        "onNameConflict": "merge"
    })
    container_id = result["id"]
    print(f"Created: {container_id}")
```

**Create Nested Hierarchy in One Call:**
```python
# Create parent with children in a single call
result = client.call("ak.wwise.core.object.create", {
    "parent": "\\Actor-Mixer Hierarchy\\Default Work Unit",
    "type": "ActorMixer",
    "name": "Weapons",
    "onNameConflict": "merge",
    "children": [
        {
            "type": "RandomSequenceContainer",
            "name": "Gunshot_Rifle",
            "children": [
                {"type": "Sound", "name": "Rifle_Shot_01"},
                {"type": "Sound", "name": "Rifle_Shot_02"},
                {"type": "Sound", "name": "Rifle_Shot_03"}
            ]
        },
        {
            "type": "RandomSequenceContainer",
            "name": "Gunshot_Pistol",
            "children": [
                {"type": "Sound", "name": "Pistol_Shot_01"},
                {"type": "Sound", "name": "Pistol_Shot_02"}
            ]
        }
    ]
})
```

### 1.2 Property Setting

```python
# Set volume on an object
client.call("ak.wwise.core.object.setProperty", {
    "object": "\\Actor-Mixer Hierarchy\\Default Work Unit\\Weapons",
    "property": "Volume",
    "value": -3.0
})

# Set pitch randomization
client.call("ak.wwise.core.object.setProperty", {
    "object": "\\Actor-Mixer Hierarchy\\Default Work Unit\\Gunshot_Variations",
    "property": "Pitch",
    "value": 0
})

# Set output bus reference
client.call("ak.wwise.core.object.setReference", {
    "object": "\\Actor-Mixer Hierarchy\\Default Work Unit\\Weapons",
    "reference": "OutputBus",
    "value": "\\Master-Mixer Hierarchy\\Default Work Unit\\Master Audio Bus\\SFX"
})
```

**Common Property Names:**
- `Volume` -- dB offset
- `Pitch` -- cents offset
- `Lowpass` -- low-pass filter (0-100)
- `Highpass` -- high-pass filter (0-100)
- `MakeUpGain` -- make-up gain
- `InitialDelay` -- initial delay in seconds
- `Priority` -- voice priority
- `PriorityDistanceOffset` -- priority by distance
- `UserAuxSendVolume0-3` -- auxiliary send levels
- `GameAuxSendVolume` -- game-defined aux send
- `OutputBusVolume` -- output bus volume
- `OutputBusHighpass` / `OutputBusLowpass` -- bus filter values

### 1.3 Audio File Import

```python
import_args = {
    "importOperation": "useExisting",  # or "createNew", "replaceExisting"
    "default": {
        "importLanguage": "SFX"
    },
    "imports": [
        {
            "audioFile": "C:\\Audio\\rifle_shot_01.wav",
            "objectPath": "\\Actor-Mixer Hierarchy\\Default Work Unit\\Weapons\\Gunshot_Rifle\\<Sound>Rifle_Shot_01"
        },
        {
            "audioFile": "C:\\Audio\\rifle_shot_02.wav",
            "objectPath": "\\Actor-Mixer Hierarchy\\Default Work Unit\\Weapons\\Gunshot_Rifle\\<Sound>Rifle_Shot_02"
        },
        {
            "audioFile": "C:\\Audio\\rifle_shot_03.wav",
            "objectPath": "\\Actor-Mixer Hierarchy\\Default Work Unit\\Weapons\\Gunshot_Rifle\\<Sound>Rifle_Shot_03"
        }
    ]
}

result = client.call("ak.wwise.core.audio.import", import_args)
```

**Import Operation Modes:**
- `createNew` -- always creates new objects
- `useExisting` -- reuses existing containers, creates if missing
- `replaceExisting` -- replaces existing source files

**objectPath Format:**
```
\\Hierarchy\\WorkUnit\\Parent\\<Type>ObjectName
```
The `<Type>` tag (e.g., `<Sound>`, `<RandomSequenceContainer>`, `<AudioFileSource>`) tells WAAPI what type to create at that path level.

### 1.4 Event Creation

```python
# Create an event that plays a sound
event_result = client.call("ak.wwise.core.object.create", {
    "parent": "\\Events\\Default Work Unit",
    "type": "Event",
    "name": "Play_Gunshot_Rifle",
    "onNameConflict": "merge",
    "children": [
        {
            "type": "Action",
            "name": "",
            "@ActionType": 1,  # 1 = Play
            "@Target": "\\Actor-Mixer Hierarchy\\Default Work Unit\\Weapons\\Gunshot_Rifle"
        }
    ]
})
```

**Using the helper library (pss_pywaapi / csg_pywaapi):**
```python
# createEventForObject(objectID, EventParent, action='Play', eventName='', conflictmode='merge')
createEventForObject(
    container_id,
    "\\Events\\Default Work Unit",
    action="Play",
    eventName="Play_Gunshot_Rifle"
)
```

### 1.5 Switch Container Assignment

```python
# Assign children to switch values
client.call("ak.wwise.core.switchContainer.addAssignment", {
    "child": child_object_id,      # GUID of the child sound/container
    "stateOrSwitch": switch_value_id  # GUID of the switch value
})

# Get current assignments
assignments = client.call("ak.wwise.core.switchContainer.getAssignments", {
    "id": switch_container_id
})
```

### 1.6 Attenuation Curves

```python
# Set an attenuation curve
client.call("ak.wwise.core.object.setAttenuationCurve", {
    "object": attenuation_id,
    "curveType": "VolumeDryUsage",
    "use": "Custom",
    "points": [
        {"x": 0, "y": 0, "shape": "Linear"},
        {"x": 50, "y": -6, "shape": "Linear"},
        {"x": 100, "y": -200, "shape": "Exp3"}
    ]
})
```

### 1.7 RTPC Curves

```python
# Using pss_pywaapi helper
setCreateRTPCCurveForObject(
    ObjIDOrPath="\\Actor-Mixer Hierarchy\\Default Work Unit\\Ambience\\Wind",
    PropertyName="Volume",
    ControlInputStructOrID=game_parameter_id,
    PointsList=[
        {"x": 0, "y": -96, "shape": "SCurve"},
        {"x": 50, "y": -12, "shape": "SCurve"},
        {"x": 100, "y": 0, "shape": "SCurve"}
    ]
)
```

### 1.8 SoundBank Generation

```python
# Set soundbank inclusions
client.call("ak.wwise.core.soundbank.setInclusions", {
    "soundbank": soundbank_id,
    "operation": "add",
    "inclusions": [
        {"object": event_id, "filter": ["events", "structures", "media"]}
    ]
})

# Generate soundbanks
client.call("ak.wwise.core.soundbank.generate", {
    "soundbanks": [{"name": "Weapons_Bank"}]
})
```

### 1.9 Transport Control (Previewing)

```python
# Create a transport for previewing
transport = client.call("ak.wwise.core.transport.create", {
    "object": "\\Events\\Default Work Unit\\Play_Gunshot_Rifle"
})

# Play it
client.call("ak.wwise.core.transport.executeAction", {
    "transport": transport["transport"],
    "action": "play"
})

# Stop
client.call("ak.wwise.core.transport.executeAction", {
    "transport": transport["transport"],
    "action": "stop"
})
```

### 1.10 Querying Objects (WAQL)

```python
# Search using Wwise Authoring Query Language
result = client.call("ak.wwise.core.object.get", {
    "waql": "$ from type randomsequencecontainer"
}, options={"return": ["id", "name", "path", "type"]})

# Find all events
result = client.call("ak.wwise.core.object.get", {
    "waql": '$ from type event where name : "Play_*"'
}, options={"return": ["id", "name", "path"]})
```

---

## 2. WAAPI Connection Details

### 2.1 Protocol

| Method | URL | Use Case |
|---|---|---|
| **WAMP (WebSocket)** | `ws://127.0.0.1:8080/waapi` | Primary. Supports RPC + subscriptions |
| **HTTP POST** | `http://127.0.0.1:8090/waapi` | Simple one-off calls, no subscriptions |

WAMP (Web Application Messaging Protocol) over WebSocket is the recommended method. It is the only protocol that supports both function calls AND event subscriptions.

### 2.2 Python Libraries

**Option A: waapi-client (Official, Recommended for MCP)**

```bash
pip install waapi-client
```

```python
from waapi import WaapiClient, CannotConnectToWaapiException

try:
    with WaapiClient() as client:
        info = client.call("ak.wwise.core.getInfo")
        print(f"Connected to Wwise {info['version']['displayName']}")

        # Subscribe to object creation events
        handler = client.subscribe(
            "ak.wwise.core.object.created",
            lambda obj: print(f"Object created: {obj}")
        )

        # ... do work ...

        handler.unsubscribe()

except CannotConnectToWaapiException:
    print("Cannot connect -- is Wwise running with WAAPI enabled?")
```

**Option B: PyWwise (Higher-level Pythonic wrapper)**

```bash
pip install pywwise
```

```python
import pywwise

with pywwise.new_waapi_connection() as ak:
    # More Pythonic API
    info = ak.wwise.core.get_info()
    # ... operations ...
```

**Option C: Raw HTTP (curl/requests, no library needed)**

```bash
curl -X POST http://127.0.0.1:8090/waapi \
  -H "Content-Type: application/json" \
  -d '{"uri": "ak.wwise.core.getInfo", "options": {}, "args": {}}'
```

```python
import requests

response = requests.post("http://127.0.0.1:8090/waapi", json={
    "uri": "ak.wwise.core.getInfo",
    "options": {},
    "args": {}
})
print(response.json())
```

### 2.3 Authentication

There is **no authentication**. WAAPI listens on localhost only. Anyone with local access can connect. For an MCP server, this means:
- Wwise and the MCP server must run on the same machine
- No API keys or tokens needed
- The port can be customized in Wwise preferences

### 2.4 Headless Operation

**Wwise must be running with the GUI.** There is no true headless/daemon mode. However:
- You CAN launch Wwise from the command line with a project: `WwiseConsole.exe generate-soundbank <project.wproj>`
- WwiseConsole.exe can do soundbank generation without the full authoring app
- For full WAAPI access (creating objects, setting properties), the Wwise Authoring application must be open
- The WAAPI server is embedded in the authoring tool -- it is not a standalone server

**Practical implication for MCP:** The MCP server should detect whether Wwise is running and report status. It cannot start Wwise on its own (well, it could launch the process, but the user needs a valid license).

### 2.5 Enabling WAAPI in Wwise

`Project > User Preferences > Enable Wwise Authoring API` must be checked. It is off by default. Port defaults to 8080 for WAMP.

---

## 3. Common Game Audio Patterns (MCP Tool Templates)

### 3.1 Gunshot Events (Random Container with Variations)

```python
def create_gunshot_system(client, weapon_name, wav_files, parent_path="\\Actor-Mixer Hierarchy\\Default Work Unit"):
    """Create a complete gunshot event with random variations."""

    # 1. Create Random Container
    container = client.call("ak.wwise.core.object.create", {
        "parent": parent_path,
        "type": "RandomSequenceContainer",
        "name": f"Gunshot_{weapon_name}",
        "onNameConflict": "merge"
    })
    container_id = container["id"]

    # 2. Set random container properties
    client.call("ak.wwise.core.object.setProperty", {
        "object": container_id,
        "property": "RandomOrSequence",  # 0 = Random, 1 = Sequence
        "value": 0
    })
    client.call("ak.wwise.core.object.setProperty", {
        "object": container_id,
        "property": "NormalOrShuffle",  # 0 = Normal, 1 = Shuffle
        "value": 1  # Shuffle avoids repeats
    })

    # 3. Import audio files
    imports = []
    for i, wav in enumerate(wav_files):
        sound_name = f"{weapon_name}_Shot_{i+1:02d}"
        imports.append({
            "audioFile": wav,
            "objectPath": f"{parent_path}\\Gunshot_{weapon_name}\\<Sound>{sound_name}"
        })

    client.call("ak.wwise.core.audio.import", {
        "importOperation": "useExisting",
        "default": {"importLanguage": "SFX"},
        "imports": imports
    })

    # 4. Add pitch randomization to each child
    children = client.call("ak.wwise.core.object.get", {
        "from": {"id": [container_id]},
        "select": ["children"]
    }, options={"return": ["id"]})

    for child in children.get("return", []):
        # Randomize pitch +/- 100 cents
        client.call("ak.wwise.core.object.setProperty", {
            "object": child["id"],
            "property": "Pitch",
            "value": 0
        })
        # Note: setRandomizer would be used for randomization range

    # 5. Create Play event
    event = client.call("ak.wwise.core.object.create", {
        "parent": "\\Events\\Default Work Unit",
        "type": "Event",
        "name": f"Play_Gunshot_{weapon_name}",
        "onNameConflict": "merge"
    })

    return container_id, event["id"]
```

### 3.2 Footstep System (Switch Container by Surface)

```python
def create_footstep_system(client, surfaces=None):
    """Create a switch-based footstep system."""

    if surfaces is None:
        surfaces = ["Concrete", "Wood", "Grass", "Metal", "Gravel", "Water"]

    parent = "\\Actor-Mixer Hierarchy\\Default Work Unit"

    # 1. Create Switch Group (if not exists)
    switch_group = client.call("ak.wwise.core.object.create", {
        "parent": "\\Switches\\Default Work Unit",
        "type": "SwitchGroup",
        "name": "Surface_Type",
        "onNameConflict": "merge"
    })

    # 2. Create switch values for each surface
    switch_ids = {}
    for surface in surfaces:
        sw = client.call("ak.wwise.core.object.create", {
            "parent": switch_group["id"],
            "type": "Switch",
            "name": surface,
            "onNameConflict": "merge"
        })
        switch_ids[surface] = sw["id"]

    # 3. Create Switch Container
    switch_container = client.call("ak.wwise.core.object.create", {
        "parent": parent,
        "type": "SwitchContainer",
        "name": "Footstep_Surface",
        "onNameConflict": "merge"
    })
    sc_id = switch_container["id"]

    # 4. Set the switch group reference
    client.call("ak.wwise.core.object.setReference", {
        "object": sc_id,
        "reference": "SwitchGroupOrStateGroup",
        "value": switch_group["id"]
    })

    # 5. Create Random Containers for each surface
    for surface in surfaces:
        rc = client.call("ak.wwise.core.object.create", {
            "parent": sc_id,
            "type": "RandomSequenceContainer",
            "name": f"Footstep_{surface}",
            "onNameConflict": "merge"
        })

        # 6. Assign to switch value
        client.call("ak.wwise.core.switchContainer.addAssignment", {
            "child": rc["id"],
            "stateOrSwitch": switch_ids[surface]
        })

    # 7. Create play event
    event = client.call("ak.wwise.core.object.create", {
        "parent": "\\Events\\Default Work Unit",
        "type": "Event",
        "name": "Play_Footstep",
        "onNameConflict": "merge"
    })

    return sc_id
```

### 3.3 Ambient System (Blend Container, RTPC-driven)

```python
def create_ambient_system(client, name, layers):
    """
    Create an ambient blend system driven by RTPC.

    layers: list of dicts like [
        {"name": "Wind_Light", "files": [...], "rtpc_range": (0, 40)},
        {"name": "Wind_Medium", "files": [...], "rtpc_range": (30, 70)},
        {"name": "Wind_Heavy", "files": [...], "rtpc_range": (60, 100)},
    ]
    """
    parent = "\\Actor-Mixer Hierarchy\\Default Work Unit"

    # 1. Create Game Parameter
    game_param = client.call("ak.wwise.core.object.create", {
        "parent": "\\Game Parameters\\Default Work Unit",
        "type": "GameParameter",
        "name": f"RTPC_{name}_Intensity",
        "onNameConflict": "merge"
    })

    # 2. Create Blend Container
    blend = client.call("ak.wwise.core.object.create", {
        "parent": parent,
        "type": "BlendContainer",
        "name": f"Ambient_{name}",
        "onNameConflict": "merge"
    })
    blend_id = blend["id"]

    # 3. Create child sounds for each layer
    for layer in layers:
        sound = client.call("ak.wwise.core.object.create", {
            "parent": blend_id,
            "type": "Sound",
            "name": layer["name"],
            "onNameConflict": "merge"
        })

        # 4. Set RTPC curve on volume for each layer
        # (Using the raw WAAPI approach)
        # The RTPC curve maps game parameter value to volume
        low, high = layer["rtpc_range"]
        # Volume curve: silent outside range, full within
        # This would use setCreateRTPCCurveForObject in the helper libs

    # 5. Set looping on all children
    children = client.call("ak.wwise.core.object.get", {
        "from": {"id": [blend_id]},
        "select": ["children"]
    }, options={"return": ["id"]})

    for child in children.get("return", []):
        client.call("ak.wwise.core.object.setProperty", {
            "object": child["id"],
            "property": "IsLoopingEnabled",
            "value": True
        })

    return blend_id, game_param["id"]
```

### 3.4 UI Sound Events

```python
def create_ui_sound(client, name, wav_file, bus="\\Master-Mixer Hierarchy\\Default Work Unit\\Master Audio Bus\\UI"):
    """Create a simple non-spatial UI sound event."""

    parent = "\\Actor-Mixer Hierarchy\\Default Work Unit\\UI"

    # 1. Create UI actor-mixer if needed
    client.call("ak.wwise.core.object.create", {
        "parent": "\\Actor-Mixer Hierarchy\\Default Work Unit",
        "type": "ActorMixer",
        "name": "UI",
        "onNameConflict": "merge"
    })

    # 2. Import the sound
    client.call("ak.wwise.core.audio.import", {
        "importOperation": "useExisting",
        "default": {"importLanguage": "SFX"},
        "imports": [{
            "audioFile": wav_file,
            "objectPath": f"{parent}\\<Sound>UI_{name}"
        }]
    })

    # 3. Route to UI bus
    sound_result = client.call("ak.wwise.core.object.get", {
        "waql": f'$ "{parent}\\UI_{name}"'
    }, options={"return": ["id"]})

    if sound_result.get("return"):
        sound_id = sound_result["return"][0]["id"]
        client.call("ak.wwise.core.object.setReference", {
            "object": sound_id,
            "reference": "OutputBus",
            "value": bus
        })

    # 4. Create event
    event = client.call("ak.wwise.core.object.create", {
        "parent": "\\Events\\Default Work Unit",
        "type": "Event",
        "name": f"Play_UI_{name}",
        "onNameConflict": "merge"
    })

    return event["id"]
```

### 3.5 Weather/State-Driven Switches

```python
def create_weather_system(client):
    """Create a state-driven weather ambient system."""

    # 1. Create State Group
    state_group = client.call("ak.wwise.core.object.create", {
        "parent": "\\States\\Default Work Unit",
        "type": "StateGroup",
        "name": "Weather",
        "onNameConflict": "merge"
    })

    states = ["Clear", "Cloudy", "LightRain", "HeavyRain", "Storm", "Snow"]
    state_ids = {}

    for state_name in states:
        s = client.call("ak.wwise.core.object.create", {
            "parent": state_group["id"],
            "type": "State",
            "name": state_name,
            "onNameConflict": "merge"
        })
        state_ids[state_name] = s["id"]

    # 2. Create Switch Container driven by state group
    sc = client.call("ak.wwise.core.object.create", {
        "parent": "\\Actor-Mixer Hierarchy\\Default Work Unit",
        "type": "SwitchContainer",
        "name": "Ambience_Weather",
        "onNameConflict": "merge"
    })

    # 3. Reference the state group
    client.call("ak.wwise.core.object.setReference", {
        "object": sc["id"],
        "reference": "SwitchGroupOrStateGroup",
        "value": state_group["id"]
    })

    # 4. Create child sounds for each state, assign them
    for state_name in states:
        sound = client.call("ak.wwise.core.object.create", {
            "parent": sc["id"],
            "type": "Sound",
            "name": f"Weather_{state_name}",
            "onNameConflict": "merge"
        })

        client.call("ak.wwise.core.switchContainer.addAssignment", {
            "child": sound["id"],
            "stateOrSwitch": state_ids[state_name]
        })

    # 5. Create play event
    client.call("ak.wwise.core.object.create", {
        "parent": "\\Events\\Default Work Unit",
        "type": "Event",
        "name": "Play_Weather_Ambience",
        "onNameConflict": "merge"
    })

    return sc["id"], state_ids
```

---

## 4. Complete WAAPI Function Reference (87 Functions)

### 4.1 Core Object Operations
| Function | Description |
|---|---|
| `ak.wwise.core.object.create` | Create Wwise objects (any type) |
| `ak.wwise.core.object.delete` | Delete objects |
| `ak.wwise.core.object.get` | Query objects (supports WAQL) |
| `ak.wwise.core.object.move` | Move objects in hierarchy |
| `ak.wwise.core.object.copy` | Copy objects |
| `ak.wwise.core.object.setName` | Rename objects |
| `ak.wwise.core.object.setNotes` | Set object notes |
| `ak.wwise.core.object.setProperty` | Set property values |
| `ak.wwise.core.object.setReference` | Set references (bus, attenuation, etc.) |
| `ak.wwise.core.object.getPropertyInfo` | Get property metadata |
| `ak.wwise.core.object.getPropertyNames` | List available properties |
| `ak.wwise.core.object.isPropertyEnabled` | Check if property is active |
| `ak.wwise.core.object.getTypes` | Get all object types |
| `ak.wwise.core.object.getAttenuationCurve` | Read attenuation curve |
| `ak.wwise.core.object.setAttenuationCurve` | Write attenuation curve |

### 4.2 Audio Import
| Function | Description |
|---|---|
| `ak.wwise.core.audio.import` | Import WAV/audio files |
| `ak.wwise.core.audio.importTabDelimited` | Import from tab-delimited file |

### 4.3 Switch Container
| Function | Description |
|---|---|
| `ak.wwise.core.switchContainer.addAssignment` | Assign child to switch/state |
| `ak.wwise.core.switchContainer.removeAssignment` | Remove assignment |
| `ak.wwise.core.switchContainer.getAssignments` | List assignments |

### 4.4 Sound Engine (Runtime Preview)
| Function | Description |
|---|---|
| `ak.soundengine.postEvent` | Post event to sound engine |
| `ak.soundengine.executeActionOnEvent` | Execute action on event |
| `ak.soundengine.registerGameObj` | Register game object |
| `ak.soundengine.unregisterGameObj` | Unregister game object |
| `ak.soundengine.setSwitch` | Set switch value |
| `ak.soundengine.setRTPCValue` | Set RTPC value |
| `ak.soundengine.resetRTPCValue` | Reset RTPC |
| `ak.soundengine.setPosition` | Set 3D position |
| `ak.soundengine.setMultiplePositions` | Set multi-position |
| `ak.soundengine.setListeners` | Set listeners |
| `ak.soundengine.setDefaultListeners` | Set default listeners |
| `ak.soundengine.setScalingFactor` | Set distance scaling |
| `ak.soundengine.setListenerSpatialization` | Configure listener spatialization |
| `ak.soundengine.setObjectObstructionAndOcclusion` | Set obstruction/occlusion |
| `ak.soundengine.setGameObjectOutputBusVolume` | Set per-object bus volume |
| `ak.soundengine.setGameObjectAuxSendValues` | Set aux send values |
| `ak.soundengine.postTrigger` | Post trigger |
| `ak.soundengine.seekOnEvent` | Seek within playing event |
| `ak.soundengine.stopPlayingID` | Stop by playing ID |
| `ak.soundengine.stopAll` | Stop all sounds |
| `ak.soundengine.postMsgMonitor` | Post monitor message |

### 4.5 Project & SoundBank
| Function | Description |
|---|---|
| `ak.wwise.core.project.save` | Save project |
| `ak.wwise.core.soundbank.getInclusions` | Get bank inclusions |
| `ak.wwise.core.soundbank.setInclusions` | Set bank inclusions |
| `ak.wwise.core.soundbank.generate` | Generate soundbanks |

### 4.6 Transport (Preview)
| Function | Description |
|---|---|
| `ak.wwise.core.transport.create` | Create transport |
| `ak.wwise.core.transport.destroy` | Destroy transport |
| `ak.wwise.core.transport.getState` | Get transport state |
| `ak.wwise.core.transport.getList` | List transports |
| `ak.wwise.core.transport.executeAction` | Play/stop/pause |

### 4.7 UI, Undo, Remote, Debug
| Function | Description |
|---|---|
| `ak.wwise.ui.bringToForeground` | Bring Wwise to front |
| `ak.wwise.ui.project.open` | Open project |
| `ak.wwise.ui.project.close` | Close project |
| `ak.wwise.ui.getSelectedObjects` | Get current selection |
| `ak.wwise.ui.commands.execute` | Execute UI command |
| `ak.wwise.core.undo.beginGroup` | Start undo group |
| `ak.wwise.core.undo.endGroup` | End undo group |
| `ak.wwise.core.undo.cancelGroup` | Cancel undo group |
| `ak.wwise.core.remote.connect` | Connect to remote game |
| `ak.wwise.core.remote.disconnect` | Disconnect from game |
| `ak.wwise.core.remote.getAvailableConsoles` | List available consoles |
| `ak.wwise.core.remote.getConnectionStatus` | Get connection status |
| `ak.wwise.core.plugin.getList` | List plugins |
| `ak.wwise.waapi.getFunctions` | List all WAAPI functions |
| `ak.wwise.waapi.getTopics` | List subscription topics |
| `ak.wwise.waapi.getSchema` | Get JSON schema for a function |

### 4.8 Subscription Topics (Events)
| Topic | Fires When |
|---|---|
| `ak.wwise.core.object.created` | Object created |
| `ak.wwise.core.object.preDeleted` | Before object deletion |
| `ak.wwise.core.object.postDeleted` | After object deletion |
| `ak.wwise.core.object.nameChanged` | Object renamed |
| `ak.wwise.core.object.propertyChanged` | Property modified |
| `ak.wwise.core.object.referenceChanged` | Reference modified |
| `ak.wwise.core.object.childAdded` | Child added |
| `ak.wwise.core.object.childRemoved` | Child removed |
| `ak.wwise.core.object.curveChanged` | Curve modified |
| `ak.wwise.core.object.attenuationCurveChanged` | Attenuation curve changed |
| `ak.wwise.core.switchContainer.assignmentAdded` | Switch assignment added |
| `ak.wwise.core.switchContainer.assignmentRemoved` | Switch assignment removed |
| `ak.wwise.core.project.loaded` | Project loaded |
| `ak.wwise.core.project.preClosed` | Before project close |
| `ak.wwise.core.project.postClosed` | After project close |
| `ak.wwise.core.transport.stateChanged` | Transport state changed |
| `ak.wwise.ui.selectionChanged` | Selection changed in UI |

---

## 5. Existing Tools and Libraries

### 5.1 No Existing Wwise MCP Server

As of February 2026, there is **no existing MCP server for Wwise**. This would be a first-of-its-kind tool.

### 5.2 Python Libraries

| Library | Install | Level | Notes |
|---|---|---|---|
| [waapi-client](https://github.com/audiokinetic/waapi-client-python) | `pip install waapi-client` | Low-level (official) | Direct WAMP calls, best for MCP base |
| [pywwise](https://github.com/matheusvilano/PyWwise) | `pip install pywwise` | High-level wrapper | Pythonic, OOP, Wwise 2021+ |
| [pss_pywaapi](https://pss-pywaapi.readthedocs.io/) | ReadTheDocs | Helper library | Good reference for patterns |
| [csg_pywaapi](https://csg-pywaapi.readthedocs.io/) | ReadTheDocs | Helper library | Similar to pss_pywaapi |

### 5.3 Existing WAAPI Tool Repositories

| Repository | Description |
|---|---|
| [waapi-python-tools](https://github.com/ak-brodrigue/waapi-python-tools) | Audiokinetic's official tool collection (switch assigner, rename tools, parent creator) |
| [anfelab/waapi](https://github.com/anfelab/waapi) | Community scripts (switch assigner, renaming, clipboard tools) |
| [waapi-text-to-speech](https://github.com/ak-brodrigue/waapi-text-to-speech) | Generate TTS WAVs and import via WAAPI |
| [WwiseToolkit](https://github.com/Yuan-ManX/WwiseToolkit) | SDK, Unity Integration, WAAPI, and Unity Component collection |
| [waapi-python-quickstart](https://github.com/decasteljau/waapi-python-quickstart) | Basic connection example |

---

## 6. Wwise + MetaSounds Coexistence in UE5

### 6.1 AudioLink Bridge (UE 5.1+)

AudioLink is the official mechanism for running MetaSounds and Wwise simultaneously in UE5. It was previously "one or the other" -- now it is "both at the same time."

**How it works:**
```
MetaSounds Patch --> AudioLink Protocol --> Wwise Audio Input Event --> Wwise Bus
```

**Direction: One-way only. MetaSounds feeds INTO Wwise. Wwise CANNOT feed back into MetaSounds.**

### 6.2 Configuration Steps

1. **Enable AudioLink:** Project Settings > Wwise Integration Settings > Unreal Audio Routing > "Route through AudioLink [UE5.1]"
2. **Create Wwise Audio Input Event:** In Wwise, create an event using the Audio Input plugin source
3. **Configure MetaSound Attenuation:** In the MetaSound's Attenuation settings, set the AudioLink override to point at the Wwise Audio Input Event
4. **Optional Spatialization:** Check "Attenuation Spatialization" to let Wwise handle 3D positioning

### 6.3 Practical Use Cases

| System | Engine | Reason |
|---|---|---|
| Dialogue | Wwise | Localization, dynamic mixing, real-time voice management |
| Music | Wwise | Interactive music system, transitions, stingers |
| SFX (traditional) | Wwise | Established pipeline, switch/state systems |
| Procedural footsteps | MetaSounds | Real-time synthesis, granular control |
| Vehicle engines | MetaSounds | Procedural RPM-driven synthesis |
| Synthesized UI feedback | MetaSounds | Low-latency procedural audio |
| Environmental procedural | MetaSounds --> Wwise via AudioLink | Synthesized wind/rain processed through Wwise spatial pipeline |

### 6.4 Known Limitations

- **No reverse routing:** Wwise audio cannot be sent to MetaSounds
- **Obstruction/Occlusion:** Cannot create exclusive occlusion systems in Wwise when source is AudioLink -- UE handles it natively by cutting audio at barriers
- **Spatialization ambiguity:** Unclear interaction between UE attenuation and Wwise 3D settings when both are active
- **Audio glitches:** Random loud noise bursts reported; mitigate with low levels, master limiters, and app restarts after creating new AudioLink objects
- **Iteration:** MetaSounds patches cannot be previewed outside the running game -- requires continuous play testing

### 6.5 MCP Server Relevance

For an MCP server, the Wwise side of AudioLink setup is:
1. Create an Audio Input plugin source in Wwise (via WAAPI)
2. Create an event referencing that source
3. The UE5 side (AudioLink config) is done in the Unreal editor, not via WAAPI

---

## 7. Proposed MCP Server Architecture

### 7.1 Core MCP Tools to Implement

```
wwise_connect          -- Connect to Wwise, verify WAAPI is running
wwise_get_info         -- Get Wwise version, project info
wwise_create_object    -- Create any Wwise object type
wwise_import_audio     -- Import WAV files into project
wwise_set_property     -- Set properties on objects
wwise_set_reference    -- Set references (bus, attenuation, switch group)
wwise_create_event     -- Create event with action
wwise_query            -- WAQL query for finding objects
wwise_build_hierarchy  -- Create full object trees from spec
wwise_assign_switch    -- Assign children to switch/state values
wwise_set_attenuation  -- Configure attenuation curves
wwise_set_rtpc         -- Create/modify RTPC curves
wwise_generate_banks   -- Generate soundbanks
wwise_preview          -- Play/stop events via transport
wwise_save             -- Save project
```

### 7.2 Higher-Level Template Tools

```
wwise_template_gunshot         -- Create full gunshot system (random container + variations + event)
wwise_template_footsteps       -- Create footstep system (switch container by surface)
wwise_template_ambient         -- Create ambient blend system with RTPC
wwise_template_ui_sound        -- Create simple UI sound event
wwise_template_weather_states  -- Create weather state system
wwise_template_music_system    -- Create interactive music hierarchy
```

### 7.3 MCP Server Skeleton

```python
# mcp_wwise_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent
from waapi import WaapiClient, CannotConnectToWaapiException

server = Server("wwise-mcp")
client = None

@server.tool("wwise_connect")
async def connect(url: str = "ws://127.0.0.1:8080/waapi"):
    """Connect to a running Wwise instance via WAAPI."""
    global client
    try:
        client = WaapiClient(url=url)
        info = client.call("ak.wwise.core.getInfo")
        return TextContent(text=f"Connected to Wwise {info['version']['displayName']}")
    except CannotConnectToWaapiException:
        return TextContent(text="ERROR: Cannot connect. Is Wwise running with WAAPI enabled?")

@server.tool("wwise_create_object")
async def create_object(
    parent_path: str,
    object_type: str,
    name: str,
    on_conflict: str = "merge",
    children: list = None
):
    """Create a Wwise object (Sound, RandomSequenceContainer, SwitchContainer, etc.)."""
    args = {
        "parent": parent_path,
        "type": object_type,
        "name": name,
        "onNameConflict": on_conflict
    }
    if children:
        args["children"] = children
    result = client.call("ak.wwise.core.object.create", args)
    return TextContent(text=f"Created {object_type} '{name}': {result['id']}")

@server.tool("wwise_import_audio")
async def import_audio(
    files: list,  # [{"wav_path": "...", "object_path": "..."}]
    operation: str = "useExisting",
    language: str = "SFX"
):
    """Import WAV files into the Wwise project."""
    imports = [
        {"audioFile": f["wav_path"], "objectPath": f["object_path"]}
        for f in files
    ]
    result = client.call("ak.wwise.core.audio.import", {
        "importOperation": operation,
        "default": {"importLanguage": language},
        "imports": imports
    })
    return TextContent(text=f"Imported {len(files)} files")

@server.tool("wwise_query")
async def query(waql: str, return_fields: list = None):
    """Query Wwise objects using WAQL."""
    if return_fields is None:
        return_fields = ["id", "name", "type", "path"]
    result = client.call("ak.wwise.core.object.get", {
        "waql": waql
    }, options={"return": return_fields})
    return TextContent(text=str(result))

# ... additional tools ...

if __name__ == "__main__":
    server.run()
```

---

## 8. Important Considerations

<warnings>
- Wwise Authoring Application MUST be running -- no headless/daemon mode for full WAAPI
- No authentication on WAAPI -- anyone on localhost can connect
- WAAPI is single-threaded in Wwise -- rapid parallel calls may cause issues; use undo groups for batch operations
- Object paths use backslashes (\\) not forward slashes -- easy to get wrong in Python strings
- The `onNameConflict` parameter is critical: "merge" (reuse existing), "rename" (auto-suffix), "replace" (overwrite), "fail" (error)
- SoundBank generation via WAAPI requires platform plugins to be installed in Wwise
- Large imports should be batched (100 files per call recommended) to avoid JSON parsing issues
- WAAPI port (8080) may conflict with other services -- configurable in Wwise preferences
- Always wrap batch operations in undo groups (`beginGroup`/`endGroup`) for atomic operations
- Wwise licenses are required -- free non-commercial license available but limited to 200 media assets in banks
</warnings>

---

## 9. Resources

<references>
- [Official WAAPI Documentation](https://www.audiokinetic.com/library/edge/?id=waapi.html) - Audiokinetic reference
- [waapi-client (Official Python)](https://github.com/audiokinetic/waapi-client-python) - Official Python WAMP client
- [PyWwise](https://github.com/matheusvilano/PyWwise) - Pythonic WAAPI wrapper
- [PyWwise Blog Post](https://www.audiokinetic.com/en/blog/pywwise-waapi-made-pythonic/) - Introduction and tutorial
- [WAAPI Python Tools](https://github.com/ak-brodrigue/waapi-python-tools) - Official automation scripts
- [WAAPI Step-by-Step Example](https://www.audiokinetic.com/en/blog/stepbystep-waapi-example/) - Full workflow tutorial
- [WAAPI is for Everyone Part 1](https://www.audiokinetic.com/en/blog/everyone-can-use-waapi-overview/) - Overview
- [WAAPI is for Everyone Part 2](https://www.audiokinetic.com/en/blog/everyone-can-use-waapi-wwise-core/) - wwise.core deep dive
- [pss_pywaapi API Reference](https://pss-pywaapi.readthedocs.io/en/latest/API.html) - Helper library docs
- [csg_pywaapi API Reference](https://csg-pywaapi.readthedocs.io/en/latest/API.html) - Helper library docs
- [anfelab/waapi Scripts](https://github.com/anfelab/waapi) - Community WAAPI scripts
- [WAAPI C# Audio Import Gist](https://gist.github.com/decasteljau/d9c865342aa3b994840d03a024121327) - Import example
- [AudioLink Blog](https://www.audiokinetic.com/en/blog/adventures-with-audiolink/) - Wwise + UE5 AudioLink
- [AudioLink How-To](https://www.audiokinetic.com/en/blog/how-to-use-audiolink/) - Configuration guide
- [AudioLink via Wwise (nightonmars)](https://blog.nightonmars.com/audio-tunnels-ue-audiolink-via-wwise/) - Practical deep dive
- [Introducing WAQL](https://www.audiokinetic.com/en/blog/introducing-waql/) - Query language reference
- [WAQL Tutorial for Beginners](https://medium.com/@poly.izzzy/waql-tutorial-for-beginners-part-1-554171ee2fe4) - WAQL tutorial
</references>

---

## Metadata

<meta>
research-date: 2026-02-06
confidence: high
version-checked: Wwise 2025.1.4, waapi-client latest, pywwise latest
existing-mcp-server: none (greenfield opportunity)
key-dependency: Wwise Authoring App must be running
recommended-base-library: waapi-client (official, low-level, best for MCP wrapping)
</meta>
