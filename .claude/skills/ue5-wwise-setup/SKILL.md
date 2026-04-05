---
name: ue5-wwise-setup
description: Wwise project setup via WAAPI HTTP API. Use when creating bus hierarchies, RTPCs, switches, states, events, SoundBanks, AudioLink containers, or any Wwise authoring automation. Covers the full WAAPI HTTP workflow on port 8090.
allowed-tools: Read, Grep, Glob, Bash
argument-hint: [wwise-setup-task]
---

# Wwise Setup — WAAPI HTTP Automation

Set up complete Wwise projects programmatically: bus hierarchies, RTPCs, switches, events, SoundBanks, and AudioLink routing.

## WAAPI HTTP API (Port 8090)

All calls use `curl -s -X POST http://127.0.0.1:8090/waapi` with JSON body:

```json
{
  "uri": "ak.wwise.core.object.create",
  "args": { ... },
  "options": {}
}
```

**Key format rules:**
- `args` contains the call parameters
- `options` is top-level (NOT inside args), used for `return` fields
- `return` goes in `options`, NOT in `args`
- Always include `"options": {}` even if empty
- Object paths use **backslashes**: `\\Busses\\Default Work Unit\\Main Audio Bus`

### Return Fields

```json
{
  "uri": "ak.wwise.core.object.get",
  "args": { "from": {"id": ["{GUID}"]} },
  "options": { "return": ["id", "name", "type", "path"] }
}
```

## Core WAAPI Operations

### Create Object
```bash
curl -s -X POST http://127.0.0.1:8090/waapi -H "Content-Type: application/json" -d '{
  "uri": "ak.wwise.core.object.create",
  "args": {
    "parent": "\\Busses\\Default Work Unit\\Main Audio Bus",
    "type": "Bus",
    "name": "SFX",
    "onNameConflict": "merge"
  },
  "options": {}
}'
```

### Set Property
```bash
curl -s -X POST http://127.0.0.1:8090/waapi -d '{
  "uri": "ak.wwise.core.object.setProperty",
  "args": {"object": "{GUID}", "property": "Volume", "value": -6.0},
  "options": {}
}'
```

### Set Reference (e.g. OutputBus)
```bash
curl -s -X POST http://127.0.0.1:8090/waapi -d '{
  "uri": "ak.wwise.core.object.setReference",
  "args": {"object": "{GUID}", "reference": "OutputBus", "value": "{BUS_GUID}"},
  "options": {}
}'
```

### Delete Object
```bash
curl -s -X POST http://127.0.0.1:8090/waapi -d '{
  "uri": "ak.wwise.core.object.delete",
  "args": {"object": "{GUID}"},
  "options": {}
}'
```

### Search / Query
```bash
# By ID
"from": {"id": ["{GUID}"]}

# By type
"from": {"ofType": ["Event"]}

# Text search
"from": {"search": ["AudioLink"]}

# By path
"from": {"path": ["\\Events\\Default Work Unit"]}

# Children of object
"transform": [{"select": ["children"]}]
```

### Save Project
```bash
curl -s -X POST http://127.0.0.1:8090/waapi -d '{
  "uri": "ak.wwise.core.project.save", "args": {}, "options": {}
}'
```

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

## AudioLink Setup

AudioLink routes MetaSounds audio → Wwise for mixing/spatialization.

### Architecture
```
MetaSounds Source → AudioLink Component → Wwise Event → Audio Input Sound → Wwise Bus
```

### Wwise Side (4 steps)
1. **Create AudioLink buses** under Main Audio Bus
2. **Create ActorMixer** "AudioLink_Sources" via WAAPI
3. **Create Sound SFX** objects under ActorMixer (one per channel)
4. **Set Audio Input plugin** on each Sound (MANUAL in Wwise UI — WAAPI cannot create SourcePlugin)

```python
# Create ActorMixer
am = waapi("ak.wwise.core.object.create", {
    "parent": "\\Containers\\Default Work Unit",
    "type": "ActorMixer", "name": "AudioLink_Sources",
    "onNameConflict": "merge"
})
# Route to AudioLink bus
waapi("ak.wwise.core.object.setReference", {
    "object": am["id"], "reference": "OutputBus",
    "value": "{AUDIOLINK_BUS_GUID}"
})
# Create Sound children
for name in ["AudioLink_Footsteps", "AudioLink_Weapons", "AudioLink_Ambient", "AudioLink_General"]:
    waapi("ak.wwise.core.object.create", {
        "parent": am["id"], "type": "Sound",
        "name": name, "onNameConflict": "merge"
    })
```

**MANUAL STEP**: In Wwise UI, right-click each Sound → set source to **"Wwise Audio Input"** plugin.

### UE5 Side (4 steps)

#### Step 1: Create WwiseAudioLinkSettings Data Assets
In UE5 Content Browser: Right-click → Miscellaneous → Data Asset → select `WwiseAudioLinkSettings`

Create one per channel:
| Asset Name | StartEvent |
|------------|------------|
| `AL_Settings_Footsteps` | Play_AudioLink_Footsteps |
| `AL_Settings_Weapons` | Play_AudioLink_Weapons |
| `AL_Settings_Ambient` | Play_AudioLink_Ambient |
| `AL_Settings_General` | Play_AudioLink_General |

Set the `StartEvent` property to the matching Wwise AkAudioEvent asset.
**Note**: Wwise UE integration auto-generates AkAudioEvent assets from SoundBank metadata.

#### Step 2: Add WwiseAudioLinkComponent to Actor Blueprint
```
1. Open Actor BP (e.g. BP_Creature, BP_AmbientSource)
2. Add Component → search "Wwise Audio Link"
3. In Details panel set:
   - Sound: Your MetaSounds Source asset (e.g. MS_LyraFootstep_Layered)
   - Settings: The matching WwiseAudioLinkSettings asset (e.g. AL_Settings_Footsteps)
   - Auto Play: true (starts on BeginPlay)
```

#### Step 3: Verify Audio Flow
```
MetaSounds Source (synthesis)
  → WwiseAudioLinkComponent (bridge)
    → Wwise Play Event (triggers Audio Input)
      → Audio Input Sound (receives audio)
        → Wwise Bus (mixing/spatialization)
```

#### Step 4: Test In-Editor
- Play in Editor (PIE)
- Open Wwise Profiler → verify audio appears on AudioLink buses
- Check levels in Wwise Mixing Desk

### Key Classes
- `UWwiseAudioLinkSettings` — `StartEvent` (TSoftObjectPtr<UAkAudioEvent>)
- `UWwiseAudioLinkComponent` — `Sound` (USoundBase), `Settings` (UWwiseAudioLinkSettings*), `bAutoPlay`
- `UAkAudioEvent` — Auto-generated from Wwise SoundBank, found in Content/WwiseAudio/

### AudioLink via TCP Plugin (Partial)
Our TCP plugin can add components to BPs but **cannot** create data assets yet:
```python
# Add WwiseAudioLinkComponent to a Blueprint (via bp_add_node)
# Set component properties (via bp_set_pin_default)
# Wire to BeginPlay (via bp_connect_pins)
# Compile (via bp_compile)
```
**Missing**: `create_data_asset` command for WwiseAudioLinkSettings — requires new C++ command.

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

## Transport / Playback Testing

```bash
# Play in Wwise transport (NOT ak.soundengine.postEvent)
curl -s -X POST http://127.0.0.1:8090/waapi -d '{
  "uri": "ak.wwise.ui.commands.execute",
  "args": {"command": "TransportPlayDirectly", "objects": ["{EVENT_GUID}"]},
  "options": {}
}'
```

## Reload / Recovery

```bash
# Force reload project from disk
"command": "ForceReloadProject"

# Save project
"uri": "ak.wwise.core.project.save"
```

## Critical Gotchas

1. **WAAPI cannot create SourcePlugin** — Audio Input must be set manually in Wwise UI
2. **Never edit .wwu XML files** — not with Python ET, not with string replacement. Use WAAPI only
3. **Delete macOS `._*.wwu` files** on external drives — Wwise tries to parse them as work units
4. **`clearAudioFileCache: true`** required when SoundBanks are empty/stale
5. **`onNameConflict: "merge"`** prevents duplicate creation errors
6. **Paths use backslashes** even on macOS: `\\Busses\\Default Work Unit\\...`
7. **`options: {}`** required in every WAAPI HTTP call (even empty)
8. **SoundBank "Init" is auto-generated** — don't include in generate call
9. **`return` goes in `options`** at top level, NOT in `args`
10. **ForceReloadProject** may show dialog — user must click through
11. **SoundBank stale GUIDs** — if events were deleted+recreated, old GUIDs persist in SoundBank inclusions. Fix: delete entire SoundBank, recreate, re-add inclusions fresh
12. **WAAPI `setInclusions` with "replace"** does NOT always update on-disk .wwu file — Wwise caches its own version
13. **Audio Input source name doesn't matter** — just select "Wwise Audio Input" plugin, naming is irrelevant

## Lyra Demo Bus IDs (Reference)

| Bus | GUID |
|-----|------|
| Main Audio Bus | {1514A4D8-1DA6-412A-A17E-75CA0C2149F3} |
| SFX | {E846F1FB-12DF-4C31-869B-4458F7EC3E34} |
| Footsteps | {8C4CDC41-5441-4315-BC4E-B481E49A5A50} |
| Weapons | {A05FFC03-3991-44E9-9C31-50FFCD922457} |
| Impacts | {BED62D6D-E566-48C4-B5A7-46AE8567B08E} |
| Ambient | {5C0C54F6-F005-4282-A866-83D55DB77B40} |
| Music | {09AF1FE3-329E-49ED-936B-262BE76D3906} |
| VO | {C0071867-68AF-4982-AFB0-2A9AB69FA3D0} |
| AudioLink | {1A33D85D-C61B-49B2-8F67-9BCF7412FEBD} |
| AudioLink_Footsteps | {9D85A7F6-6F92-4E21-AF02-5558FE66ED07} |
| AudioLink_Weapons | {1FFF2706-690A-4800-B4ED-170B3F3CD8F8} |

## Lyra Demo AudioLink IDs (Reference)

| Object | Type | GUID |
|--------|------|------|
| AudioLink_Sources | ActorMixer | {AFEA4AEC-0011-495F-8DF5-410C88FEFCC0} |
| AudioLink_Footsteps | Sound | {B39B9305-C24A-4BCD-9C80-E971503DEBFB} |
| AudioLink_Weapons | Sound | {188E955C-321A-482D-938E-54C841953608} |
| AudioLink_Ambient | Sound | {81F2FF30-3D4B-432C-B19D-846704FE8F1B} |
| AudioLink_General | Sound | {1A895170-85E6-4C52-972A-2B0ECA597ABC} |
| Play_AudioLink_Footsteps | Event | {A1AF956E-158B-431D-8B98-5ACC37165F9C} |
| Play_AudioLink_Weapons | Event | {CE1F96EF-AF11-4EA5-B03F-01DB73B513EC} |
| Play_AudioLink_Ambient | Event | {472B1B7D-921A-4E99-A521-809E9596AE8F} |
| Play_AudioLink_General | Event | {516872EF-0B23-4A0C-AAE2-6804E641B2AA} |
| LyraDemo | SoundBank | {78D6CFDE-B75B-496D-9D5C-8C55C969A63C} |

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

## UE5 Wwise Integration Setup

### Step 1: Enable Wwise Plugin in .uproject
Add to the Plugins array in `YourProject.uproject`:
```json
{"Name": "Wwise", "Enabled": true},
{"Name": "WwiseSoundEngine", "Enabled": true}
```
Both plugins must be present on disk at `Plugins/Wwise/` and `Plugins/WwiseSoundEngine/`.

### Step 2: Config — DefaultGame.ini
Wwise writes its settings to `[/Script/AkAudio.AkSettings]` in DefaultGame.ini.
Key fields:
```ini
[/Script/AkAudio.AkSettings]
WwiseProjectPath=(FilePath="YourProject_WwiseProject/YourProject_WwiseProject.wproj")
RootOutputPath=(Path="../YourProject_WwiseProject/GeneratedSoundBanks")
WwiseStagingDirectory=(Path="WwiseAudio")
InitBank=/Game/WwiseAudio/InitBank.InitBank
AudioRouting=EnableWwiseOnly
bWwiseSoundEngineEnabled=True
bWwiseAudioLinkEnabled=False
```

### Step 3: Audio Routing Modes
The `AudioRouting` enum (`EAkUnrealAudioRouting`) has 5 values:
| Value | Effect |
|-------|--------|
| `EnableWwiseOnly` | Only Wwise produces audio. UE native audio silent. |
| `Separate` | Both Wwise and UE audio play simultaneously. |
| `AudioLink` | All UE audio routes through AudioLink → Wwise. |
| `EnableUnrealOnly` | Only UE audio. Wwise SoundEngine disabled. |
| `Custom` | Developer configures manually. |

**For demos without AudioLink**: Use `EnableUnrealOnly` to keep Lyra audio working, show Wwise project separately.
**For full integration**: Use `AudioLink` (requires `bWwiseAudioLinkEnabled=True`).

### Step 4: AudioLink Enable Flag
AudioLink is controlled by TWO settings:
1. `AudioRouting=AudioLink` in `[/Script/AkAudio.AkSettings]`
2. `bWwiseAudioLinkEnabled=True` in same section

The runtime module reads from `GGameIni`:
```cpp
GConfig->GetBool(TEXT("/Script/AkAudio.AkSettings"),
    TEXT("bWwiseAudioLinkEnabled"), bWwiseAudioLinkEnabled, GGameIni);
```

### Step 5: Root Output Path
The GeneratedSoundBanks path must be set in **two places**:
1. **DefaultGame.ini**: `RootOutputPath=(Path="../YourProject_WwiseProject/GeneratedSoundBanks")`
2. **Per-user settings** (Saved/Config/MacEditor/EditorPerProjectUserSettings.ini):
   `RootOutputPathOverride=(Path="/full/path/to/GeneratedSoundBanks")`

If RootOutputPathOverride is empty, UE shows "Root Output Path is empty" warning and banks won't load.

### Step 6: Reconcile Wwise Assets
After SoundBanks are generated and paths configured:
1. Open **Wwise Browser** in UE (Window → Wwise Browser)
2. Select all Events → Right-click → **Reconcile Selection**
3. This creates `.uasset` files in `Content/WwiseAudio/` that UE can reference
4. Without reconciliation, AkAmbientSound/AkComponent can't find events

### Step 7: Verify Initialization
Check Output Log for these lines (in order):
```
LogAkAudio: OnAudioRoutingUpdate: Wwise SoundEngine Enabled: true
LogAkAudio: Wwise SoundEngine successfully initialized.
LogAkAudio: Initialization complete.
LogAkAudio: Audiokinetic Audio Device initialized.
LogAkAudio: Successfully connected to Wwise Authoring on localhost.
```

**If `Audio Device Manager Initialization Failed`**: Revert any manual DefaultEngine.ini changes. Wwise config belongs in DefaultGame.ini, NOT DefaultEngine.ini.

## UE5 Integration Gotchas (Learned the Hard Way)

14. **Config goes in DefaultGame.ini** — Wwise settings are `[/Script/AkAudio.AkSettings]` in DefaultGame.ini. Adding `[/Script/AkAudio.AkSettings]` to DefaultEngine.ini causes `Audio Device Manager Initialization Failed`
15. **UE overwrites config on save** — If you edit DefaultGame.ini while UE is open, UE may overwrite your changes on next save. Edit while UE is closed
16. **AudioRouting enum is strict** — Invalid values (like `EnableWwiseAndAudioLink`) cause `FEnumProperty invalid value` error and silently revert to default
17. **AudioLink toggle grayed out** — The UI toggle only works if `bWwiseAudioLinkEnabled` is set in config. Set it in DefaultGame.ini, not through UI
18. **Wwise plugin NOT auto-discovered** — Even with files in `Plugins/Wwise/`, must explicitly add to .uproject Plugins array
19. **Wwise replaces UE audio completely** — In `EnableWwiseOnly` mode, ALL UE native audio (MetaSounds, AudioComponents) goes silent. Lyra has no sound because it doesn't post Wwise events
20. **Content Browser hides plugin content** — Maps in GameFeature plugins (like L_ShooterPerf) don't appear unless "Show Plugin Content" is enabled. Use Ctrl+P to search instead
21. **MetaSounds Presets are read-only** — `_Preset` suffix assets inherit from parent Source. Cannot add nodes. Must duplicate the parent Source to edit the graph
22. **`EnableUnrealOnly` for demo without AudioLink** — Keeps all Lyra audio working while Wwise project exists for separate showcase
23. **Two plugins required** — `Wwise` (integration) + `WwiseSoundEngine` (SDK) both needed in .uproject. Missing either = no Wwise

## Source Files

- Wwise tools: `src/ue_audio_mcp/tools/wwise_*.py` (20 tools)
- Wwise types: `src/ue_audio_mcp/knowledge/wwise_types.py`
- Wwise templates: `src/ue_audio_mcp/templates/wwise/` (6 JSON)
- WAAPI research: `research/research_waapi_mcp_server.md` (87 functions)

$ARGUMENTS
