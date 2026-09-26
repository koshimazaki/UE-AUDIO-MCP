# Wwise ↔ UE5 Integration

Part of the `ue5-wwise-setup` skill: AudioLink routing and enabling Wwise in an Unreal project.

## AudioLink Setup

AudioLink routes MetaSounds audio → Wwise (one way) for mixing/spatialization.

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

1. **Config goes in DefaultGame.ini** — Wwise settings are `[/Script/AkAudio.AkSettings]` in DefaultGame.ini. Adding `[/Script/AkAudio.AkSettings]` to DefaultEngine.ini causes `Audio Device Manager Initialization Failed`
2. **UE overwrites config on save** — If you edit DefaultGame.ini while UE is open, UE may overwrite your changes on next save. Edit while UE is closed
3. **AudioRouting enum is strict** — Invalid values (like `EnableWwiseAndAudioLink`) cause `FEnumProperty invalid value` error and silently revert to default
4. **AudioLink toggle grayed out** — The UI toggle only works if `bWwiseAudioLinkEnabled` is set in config. Set it in DefaultGame.ini, not through UI
5. **Wwise plugin NOT auto-discovered** — Even with files in `Plugins/Wwise/`, must explicitly add to .uproject Plugins array
6. **Wwise replaces UE audio completely** — In `EnableWwiseOnly` mode, ALL UE native audio (MetaSounds, AudioComponents) goes silent. Lyra has no sound because it doesn't post Wwise events
7. **Content Browser hides plugin content** — Maps in GameFeature plugins (like L_ShooterPerf) don't appear unless "Show Plugin Content" is enabled. Use Ctrl+P to search instead
8. **MetaSounds Presets are read-only** — `_Preset` suffix assets inherit from parent Source. Cannot add nodes. Must duplicate the parent Source to edit the graph
9. **`EnableUnrealOnly` for demo without AudioLink** — Keeps all Lyra audio working while Wwise project exists for separate showcase
10. **Two plugins required** — `Wwise` (integration) + `WwiseSoundEngine` (SDK) both needed in .uproject. Missing either = no Wwise
