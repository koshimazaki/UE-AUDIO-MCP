# Wwise Build Recipes

Part of the `ue5-wwise-setup` skill. All calls use the WAAPI HTTP format and rules in `SKILL.md`.

## Bus Hierarchy Setup

Standard game audio bus hierarchy (template):

```
Main Audio Bus
├── SFX
│   ├── Player
│   │   ├── Footsteps
│   │   └── Foley
│   ├── Weapons
│   │   ├── Weapons_Rifle
│   │   ├── Weapons_Shotgun
│   │   └── Weapons_Pistol
│   ├── Impacts
│   └── Meta_Footsteps
├── NPC
│   ├── NPC_Footsteps
│   ├── NPC_Vocals
│   └── NPC_Actions
├── Ambient
│   ├── General_SoundBed
│   ├── Location_A
│   └── Location_B
├── Music
├── VO
└── AudioLink
    ├── AudioLink_Footsteps
    ├── AudioLink_Weapons
    └── AudioLink_Ambient
```

**AuxBusses** (reverb sends — 3 room types):
- **Reverb_Small** — tight room, short tail (0.4-0.8s RT60), hut/closet
- **Reverb_Medium** — standard room, mid tail (1.0-1.8s RT60), house/cave
- **Reverb_Large** — hall/cathedral, long tail (2.5-5.0s RT60), temple/warehouse

### Python automation pattern:

```python
import subprocess, json

def waapi(uri, args):
    payload = json.dumps({"uri": uri, "args": args, "options": {}})
    r = subprocess.run(["curl", "-s", "-X", "POST", "http://127.0.0.1:8090/waapi",
                       "-H", "Content-Type: application/json", "-d", payload],
                      capture_output=True, text=True)
    return json.loads(r.stdout)

# Create bus under Main Audio Bus
result = waapi("ak.wwise.core.object.create", {
    "parent": "\\Busses\\Default Work Unit\\Main Audio Bus",
    "type": "Bus", "name": "SFX", "onNameConflict": "merge"
})
bus_id = result["id"]
```

## RTPC (Game Parameters)

### Create Game Parameter
```python
waapi("ak.wwise.core.object.create", {
    "parent": "\\Game Parameters\\Default Work Unit",
    "type": "GameParameter", "name": "Distance",
    "onNameConflict": "merge"
})
```

Key game parameters:
- **Distance** — Player-to-source distance
- **FootstepIntensity** — Movement speed
- **CombatIntensity** — Combat state
- **PlayerHealth** — Health percentage
- **Surface** — Surface type (0-1)
- **WeaponFireRate** — Firing rate
- **MusicVolume** — Music mix level
- **ReverbSend** — Reverb wet amount

## Switches & States

### Switch Group
```python
# Create switch group
waapi("ak.wwise.core.object.create", {
    "parent": "\\Switches\\Default Work Unit",
    "type": "SwitchGroup", "name": "Surface",
    "onNameConflict": "merge"
})
# Create switch values
for surface in ["Concrete", "Glass", "Metal", "Wood", "Dirt"]:
    waapi("ak.wwise.core.object.create", {
        "parent": "\\Switches\\Default Work Unit\\Surface",
        "type": "Switch", "name": surface,
        "onNameConflict": "merge"
    })
```

### State Group
```python
waapi("ak.wwise.core.object.create", {
    "parent": "\\States\\Default Work Unit",
    "type": "StateGroup", "name": "Music_State",
    "onNameConflict": "merge"
})
for state in ["Music_On", "Music_Off"]:
    waapi("ak.wwise.core.object.create", {
        "parent": "\\States\\Default Work Unit\\Music_State",
        "type": "State", "name": state,
        "onNameConflict": "merge"
    })
```

## Events

### Create Event with Play Action
```python
# Create event
event = waapi("ak.wwise.core.object.create", {
    "parent": "\\Events\\Default Work Unit",
    "type": "Event", "name": "Play_Footstep",
    "onNameConflict": "merge"
})
# Add Play action (ActionType 1 = Play)
action = waapi("ak.wwise.core.object.create", {
    "parent": event["id"], "type": "Action",
    "name": "Play", "@ActionType": 1,
    "onNameConflict": "merge"
})
# Set target sound
waapi("ak.wwise.core.object.setReference", {
    "object": action["id"], "reference": "Target",
    "value": "{SOUND_GUID}"
})
```

**ActionType values**: 1=Play, 2=Stop, 3=Pause, 4=Resume, 7=SetSwitch, 8=SetState

## SoundBanks

### Create SoundBank
```python
waapi("ak.wwise.core.object.create", {
    "parent": "\\SoundBanks\\Default Work Unit",
    "type": "SoundBank", "name": "LyraDemo",
    "onNameConflict": "merge"
})
```

### Set Inclusions
```python
waapi("ak.wwise.core.soundbank.setInclusions", {
    "soundbank": "{BANK_GUID}",
    "operation": "add",
    "inclusions": [
        {"object": "{EVENT_GUID}", "filter": ["events", "structures", "media"]}
    ]
})
```

### Generate SoundBanks
```python
waapi("ak.wwise.core.soundbank.generate", {
    "soundbanks": [{"name": "LyraDemo"}],
    "platforms": ["Mac"],
    "languages": ["SFX"],
    "clearAudioFileCache": True,  # IMPORTANT: forces reconversion
    "writeToDisk": True
})
```

**Critical**: Use `clearAudioFileCache: true` when banks are empty/stale.

### Stage Banks for UE5
Copy from GeneratedSoundBanks to Content/WwiseAudio:
```bash
cp GeneratedSoundBanks/Mac/*.bnk Content/WwiseAudio/Mac/
cp GeneratedSoundBanks/Mac/*.json Content/WwiseAudio/Mac/
```

## Containers Setup

### SwitchContainer (Footsteps by surface)
```python
sc = waapi("ak.wwise.core.object.create", {
    "parent": "\\Actor-Mixer Hierarchy\\Default Work Unit\\Player_Audio",
    "type": "SwitchContainer", "name": "Footsteps",
    "onNameConflict": "merge"
})
# Set switch group reference
waapi("ak.wwise.core.object.setReference", {
    "object": sc["id"], "reference": "SwitchGroupOrStateGroup",
    "value": "{SURFACE_SWITCH_GROUP_GUID}"
})
# Add RandomSequenceContainers per surface
for surface in ["Concrete", "Glass", "Metal", "Dirt"]:
    waapi("ak.wwise.core.object.create", {
        "parent": sc["id"], "type": "RandomSequenceContainer",
        "name": f"Footstep_{surface}", "onNameConflict": "merge"
    })
```

### Import Audio Files
```python
waapi("ak.wwise.core.audio.import_", {
    "importOperation": "useExisting",
    "imports": [{
        "audioFile": "/path/to/Footstep_01.wav",
        "objectPath": "\\Containers\\Default Work Unit\\Player_Audio\\Footsteps\\Footstep_Concrete\\<Sound>Footstep_01"
    }]
})
```

## Full Build Recipe — What The Agent Does

This is the exact sequence to build a complete Wwise project from scratch via WAAPI.
Tested on Wwise 2025.1.5, UE 5.7.2, macOS.

### Phase 1: Bus Hierarchy
```
1. Create Main Audio Bus children: SFX, NPC, Ambient, Music, VO, AudioLink
2. Create SFX/Player sub-buses: Footsteps, Foley
3. Create SFX/Weapons sub-buses: Weapons_Rifle, Weapons_Shotgun, Weapons_Pistol
4. Create SFX sub-buses: Impacts, Meta_Footsteps
5. Create NPC sub-buses: NPC_Footsteps, NPC_Vocals, NPC_Actions
6. Create Ambient sub-buses: General_SoundBed, Location_A, Location_B
7. Create AudioLink sub-buses: AudioLink_Footsteps, AudioLink_Weapons, AudioLink_Ambient
8. Create AuxBusses: Reverb_Small, Reverb_Medium, Reverb_Large
```
All via `ak.wwise.core.object.create` with `type: "Bus"` or `type: "AuxBus"`.

### Phase 2: Game Parameters (RTPCs)
```
Parent: \\Game Parameters\\Default Work Unit
Type: GameParameter
Names: Distance, FootstepIntensity, CombatIntensity, PlayerHealth, Surface, WeaponFireRate, MusicVolume, ReverbSend
```

### Phase 3: Switches & States
```
Switch Groups:
  Surface → Concrete, Glass, Metal, Wood, Dirt, Grass
  Location → Exterior, Interior_Small, Interior_Medium, Interior_Large
  Weapon → Rifle, Shotgun, Pistol

State Groups:
  Music_State → Music_On, Music_Off
  Combat_State → Combat_Active, Combat_Idle
```
**Note**: Surface switching is handled by SwitchContainer inside Footsteps — no separate bus per surface needed.

### Phase 4: Actor-Mixer Hierarchy (Sound Containers)
```
\\Actor-Mixer Hierarchy\\Default Work Unit\\
├── Player_Audio
│   ├── Footsteps (SwitchContainer → Surface switch group)
│   │   ├── Footstep_Concrete (RandomSequenceContainer)
│   │   ├── Footstep_Glass (RandomSequenceContainer)
│   │   ├── Footstep_Metal (RandomSequenceContainer)
│   │   └── Footstep_Dirt (RandomSequenceContainer)
│   ├── Weapons_Rifle (SwitchContainer or RandomSequence)
│   ├── Weapons_Shotgun (SwitchContainer or RandomSequence)
│   ├── Weapons_Pistol (SwitchContainer or RandomSequence)
│   └── Player_Foley (RandomSequenceContainer)
├── NPC_Audio
│   ├── NPC_Footsteps (SwitchContainer → Surface switch group)
│   ├── NPC_Vocals (RandomSequenceContainer)
│   └── NPC_Actions (RandomSequenceContainer)
├── Environment_Audio
│   ├── Ambience_General (BlendContainer, looping)
│   ├── Ambience_Location_A (Sound, looping)
│   └── Ambience_Location_B (Sound, looping)
├── UI_Audio
└── AudioLink_Sources (ActorMixer)
    ├── AudioLink_Footsteps (Sound + Audio Input plugin)
    ├── AudioLink_Weapons (Sound + Audio Input plugin)
    ├── AudioLink_Ambient (Sound + Audio Input plugin)
    └── AudioLink_General (Sound + Audio Input plugin)
```

**Routing**: Each container → its matching bus via `setReference` → `OutputBus`.
- Footsteps → SFX/Player/Footsteps bus
- Weapons_Rifle → SFX/Weapons/Weapons_Rifle bus
- NPC_Footsteps → NPC/NPC_Footsteps bus
- Ambience_Location_A → Ambient/Location_A bus

### Phase 5: Import Audio Files
```python
waapi("ak.wwise.core.audio.import_", {
    "importOperation": "useExisting",
    "imports": [{"audioFile": "/path/to.wav", "objectPath": "\\...\\<Sound>Name"}]
})
```
Set looping on ambient: `setProperty` → `IsLoopingEnabled` → `true`

### Phase 6: Events
Create Play/Stop pairs for each sound:
```
Player:
  Play_Footstep / Stop_Footstep → Footsteps SwitchContainer
  Play_Weapon_Rifle / Stop_Weapon_Rifle → Weapons_Rifle
  Play_Weapon_Shotgun / Stop_Weapon_Shotgun → Weapons_Shotgun
  Play_Weapon_Pistol / Stop_Weapon_Pistol → Weapons_Pistol

NPC:
  Play_NPC_Footstep / Stop_NPC_Footstep → NPC_Footsteps
  Play_NPC_Vocal → NPC_Vocals
  Play_NPC_Action → NPC_Actions

Environment:
  Play_Ambience_General / Stop_Ambience_General → Ambience_General
  Play_Ambience_Location_A / Stop_Ambience_Location_A → Ambience_Location_A
  Play_Ambience_Location_B / Stop_Ambience_Location_B → Ambience_Location_B

Other:
  Play_Music / Stop_Music → Music container
  Play_AudioLink_Footsteps/Weapons/Ambient/General → AudioLink sounds
```
**ActionType**: 1=Play for Play events, 2=Stop for Stop events.
Wire each action's `Target` reference to the sound container.

### Phase 7: SoundBank
```
1. Create SoundBank "LyraDemo"
2. setInclusions: add ALL events with filter ["events", "structures", "media"]
3. Generate: platforms=["Mac"], writeToDisk=true, clearAudioFileCache=true
```

### Phase 8: Save
```
ak.wwise.core.project.save
```
