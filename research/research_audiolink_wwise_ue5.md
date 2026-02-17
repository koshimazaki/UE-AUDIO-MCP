# AudioLink: MetaSounds to Wwise Bridge in UE5

_Generated: 2026-02-15 | Updated: 2026-02-15 | Sources: 12+ | Version: UE 5.7 + Wwise 2025.1_

## Quick Reference

<key-points>
- AudioLink is a Beta UE feature (UE 5.1+) routing UE Audio Engine output into middleware -- ONE-WAY ONLY
- Signal path: MetaSounds Patch --> AudioLink Protocol --> Wwise "Audio Input" Source Plugin --> Wwise Bus
- Two routing methods: Source AudioLink (per-sound via Attenuation) and Submix AudioLink (per-submix)
- Wwise side requires: SoundSFX with "Audio Input" source plugin + Event + SoundBank generation
- UE side requires: Project Settings toggle + WwiseAudioLinkSettings asset + Attenuation or Submix config
- C++ architecture: IAudioLinkFactory (single instance) + IAudioLink + PCM circular buffers (FIFO)
- Known limitations: no reverse routing, obstruction/occlusion issues, spatialization ambiguity, single factory constraint
</key-points>

---

## Overview

<summary>
AudioLink is an Unreal Engine feature (UE 5.1+) that enables simultaneous use of UE's native audio system (MetaSounds, Sound Cues) alongside audio middleware like Wwise. It acts as a one-way bridge, routing audio generated in the UE Audio Engine through Wwise's processing pipeline for spatialization, mixing, and effects.

**Architecture**: UE Audio Source → Sound Attenuation (AudioLink settings) → AudioLink Submix → Wwise Audio Input Plugin → Wwise Mixing/Spatial Pipeline

**Key Paradigm Shift**: Traditionally, game projects chose "one or the other" (pure Wwise OR pure UE Audio). AudioLink enables a "both at the same time" approach—using MetaSounds for procedural/generative audio while leveraging Wwise's professional mixing, spatial audio, and content management.
</summary>

---

## Setup Instructions

### 1. Required Plugins

#### UE5 Side
- **AudioLink** plugin (built-in since UE 5.1, no separate install)
- **Wwise Integration** plugin (install via Audiokinetic Launcher)
  - Minimum: Wwise 2022.1+ for AudioLink support
  - Tested: Wwise 2025.1 with UE 5.7

#### Wwise Side
- **Audio Input** source plugin (built-in, no separate install)
  - Found in Wwise under: Sources → Wwise Audio Input

**Verification**:
```bash
# Check UE5 plugins are enabled
Project Settings → Plugins → Audio → AudioLink (enabled)
Project Settings → Plugins → Audio → Wwise (enabled)

# Check Wwise Audio Input plugin availability
Wwise Authoring → Installed Plug-ins → Wwise Audio Input (should be listed)
```

---

### 2. UE5 Project Settings

<details>

#### Step 2.1: Enable AudioLink Routing

1. Open UE5 Editor
2. Navigate to: **Edit → Project Settings**
3. Go to: **Plugins → Wwise → Integration Settings → Initialization**
4. Find: **Unreal Audio Routing** (marked "Experimental")
5. Set to: **"Route through AudioLink [UE5.1+]"**

**Critical**: This setting MUST be enabled BEFORE creating AudioLink Settings assets. The "Create New Asset" button won't appear in Attenuation dropdowns until this is set.

#### Step 2.2: (Optional) Configure Producer-Consumer Buffer

For systems experiencing audio glitches with AudioLink:
1. Project Settings → Engine → Audio → AudioLink
2. Increase **Producer to Consumer Buffer Ratio** slightly (default: 1.0, try 1.5-2.0)
3. Trade-off: Higher values reduce glitches but increase latency

</details>

---

### 3. Wwise Setup

<details>

#### Step 3.1: Create Audio Input Event

1. Open Wwise Authoring Application
2. In **Actor-Mixer Hierarchy**, create new Sound SFX:
   - Right-click on Work Unit → **New Child → Sound SFX**
   - Name: `AudioLink_Input` (or your preferred name)

3. Assign **Audio Input** source plugin:
   - Select the Sound SFX
   - In **Source Editor** (bottom panel) → **Source** dropdown
   - Choose: **Wwise Audio Input**
   - (No additional configuration needed—plugin auto-receives AudioLink data)

4. Create Wwise Event:
   - Switch to **Events** tab
   - Right-click → **New Event → Play**
   - Name: `Play_AudioLink_Input`
   - Drag the `AudioLink_Input` Sound SFX into the event's action target

5. (Optional) Configure spatialization/attenuation:
   - Select `AudioLink_Input` Sound SFX
   - **Positioning** tab → Enable **3D Spatialization**
   - **Attenuation** tab → Create/assign attenuation curve
   - **General Settings** → Output Bus routing (default Master Audio Bus)

#### Step 3.2: Generate SoundBanks

1. Switch to **SoundBanks** layout
2. Add `Play_AudioLink_Input` event to a SoundBank
3. Generate SoundBanks for your platform(s)
4. Ensure SoundBanks are copied to UE project: `Content/WwiseAudio/`

</details>

---

### 4. UE5 AudioLink Configuration (Two Methods)

AudioLink supports two routing methods. Choose one per signal chain -- do NOT combine both for the same audio source (causes duplication and loud stacking).

<details>

#### Step 4.1: Create Wwise AudioLink Settings Asset (shared by both methods)

1. In **Content Browser**, right-click → **Audio → AudioLink → Wwise AudioLink Settings**
2. Name: `WwiseAudioLinkSettings_Default`
3. Open the asset:
   - **AudioLink - Start Event**: Select `Play_AudioLink_Input` (Wwise Event)
   - **AudioLink - Stop Event**: (Optional) Create a corresponding Stop event
   - (Leave other settings default for initial setup)

#### Method A: Source AudioLink (per-sound, via Attenuation)

Best for: Individual MetaSounds that each need their own Wwise processing/spatialization.

**Step A.1: Create or Modify Sound Attenuation Asset**

1. In **Content Browser**, right-click → **Sounds → Sound Attenuation**
2. Name: `Attenuation_AudioLink` (or edit existing attenuation)
3. Open the asset:
   - Scroll to **Attenuation (AudioLink)** section
   - **AudioLink Settings Override**: Select `WwiseAudioLinkSettings_Default`
   - **Attenuation Spatialization**: Check to allow Wwise to control 3D positioning
   - If you do NOT need UE-side attenuation, uncheck "Enabled" for all Attenuation sections except AudioLink

**Step A.2: Assign to MetaSound/Sound Cue**

For MetaSound Source:
1. Open your MetaSound Source asset
2. In **Details** panel:
   - **Attenuation Settings**: Select `Attenuation_AudioLink`
   - (Alternatively, check **Override Attenuation** directly on Audio Component and set AudioLink override)

For Sound Cue:
1. Open Sound Cue
2. In **Details** panel → **Attenuation**:
   - **Attenuation Settings**: Select `Attenuation_AudioLink`

#### Method B: Submix AudioLink (per-submix, batch routing)

Best for: All sounds in a category (e.g., all procedural SFX) going to the same Wwise bus.

**Step B.1: Create Sound Submix**

1. In **Content Browser**, click **Add → Audio → Mix → Sound Submix**
2. Name: `Submix_ProceduralToWwise`

**Step B.2: Enable AudioLink on Submix**

1. Open the Submix asset
2. In the Details panel under **Audio Link**:
   - Enable **"Send to Audio Link"**
   - Set **Audio Link Settings**: Select `WwiseAudioLinkSettings_Default`

**Step B.3: Route sounds to this Submix**

1. On your Audio Component (MetaSound/SoundCue):
   - Set **Sound Submix Send** to `Submix_ProceduralToWwise`
2. All audio routed through this submix now flows to Wwise

#### C++ Assignment (either method)

```cpp
// Method A: Source AudioLink via Attenuation
USoundAttenuation* AttenuationAsset = LoadObject<USoundAttenuation>(
    nullptr, TEXT("/Game/Audio/Attenuation_AudioLink"));
AudioComponent->AttenuationSettings = AttenuationAsset;

// Method B: Submix AudioLink
USoundSubmix* Submix = LoadObject<USoundSubmix>(
    nullptr, TEXT("/Game/Audio/Submix_ProceduralToWwise"));
AudioComponent->SoundSubmixObject = Submix;
```

</details>

---

### 5. Testing the Setup

<details>

#### Validation Checklist

1. **UE5 Side**:
   - Play your level with a MetaSound Source placed in world
   - MetaSound should be visible in **Audio Insights** (Tools → Audit → Audio)
   - Sound should play (even if routing is broken)

2. **Wwise Side**:
   - Open **Wwise Profiler** (F5 in Wwise Authoring)
   - Connect to running UE5 game instance
   - Verify `Play_AudioLink_Input` event fires in Profiler
   - Check **Performance Monitor** → **Voices** → `AudioLink_Input` should be active
   - Audio waveform should be visible in **Wwise Audio Input** source slot

3. **Audio Output**:
   - You should hear the MetaSound audio processed through Wwise
   - If spatialization is enabled, test 3D positioning (move listener/source)

#### Troubleshooting

| Issue | Solution |
|-------|----------|
| No sound in Wwise Profiler | Check Project Settings → Unreal Audio Routing is set to AudioLink |
| Event fires but no audio | Verify Wwise SoundBanks are generated and loaded |
| Audio glitches/crackling | Increase Producer to Consumer Buffer Ratio in Project Settings |
| Spatialization not working | Enable "Attenuation Spatialization" in Sound Attenuation asset |
| MetaSound plays but not through Wwise | Verify "Enable Send to AudioLink" is checked in Attenuation asset |

</details>

---

## Programmatic Configuration

### C++ API (UE5 Side)

<details>

#### Setting AudioLink via Code

```cpp
// Create or load Sound Attenuation asset
USoundAttenuation* AttenuationAsset = NewObject<USoundAttenuation>();

// Enable AudioLink (requires access to internal Attenuation struct)
FSoundAttenuationSettings& Settings = AttenuationAsset->Attenuation;
Settings.bEnableSendToAudioLink = true;

// Assign Wwise AudioLink Settings
Settings.AudioLinkSettingsOverride = LoadObject<UWwiseAudioLinkSettings>(
    nullptr,
    TEXT("/Game/Audio/WwiseAudioLinkSettings_Default")
);

// Apply to Audio Component
UAudioComponent* AudioComp = GetAudioComponent();
AudioComp->AttenuationSettings = AttenuationAsset;
```

#### Per-Component AudioLink Settings

```cpp
// Via WwiseAudioLink component (dropped on Actor)
#include "AkAudioLink/AkAudioLinkComponent.h"

AActor* MyActor = GetOwner();
UAkAudioLinkComponent* AudioLinkComp = NewObject<UAkAudioLinkComponent>(MyActor);
AudioLinkComp->RegisterComponent();

// Set MetaSound and AudioLink Settings
UMetaSoundSource* MetaSound = LoadObject<UMetaSoundSource>(...);
UWwiseAudioLinkSettings* Settings = LoadObject<UWwiseAudioLinkSettings>(...);

AudioLinkComp->SetSound(MetaSound);
AudioLinkComp->SetAudioLinkSettings(Settings);
AudioLinkComp->Play();
```

</details>

---

### WAAPI (Wwise Side)

<details>

#### Querying Audio Input Objects

```python
from waapi import WaapiClient

client = WaapiClient()

# Find all Audio Input sources
result = client.call("ak.wwise.core.object.get", {
    "from": {"ofType": ["Sound"]},
    "options": {"return": ["id", "name", "type", "audioSource"]}
})

audio_input_sounds = [
    obj for obj in result["return"]
    if obj.get("audioSource", {}).get("pluginName") == "Wwise Audio Input"
]

print(f"Found {len(audio_input_sounds)} Audio Input sources")
```

#### Creating Audio Input Source Programmatically

```python
# Create Sound SFX with Audio Input source
result = client.call("ak.wwise.core.object.create", {
    "parent": "\\Actor-Mixer Hierarchy\\Default Work Unit",
    "type": "Sound",
    "name": "AudioLink_Procedural",
    "onNameConflict": "merge"
})

sound_id = result["id"]

# Set source to Audio Input plugin
client.call("ak.wwise.core.object.setProperty", {
    "object": sound_id,
    "property": "PluginID",
    "value": 0x00640002  # Wwise Audio Input plugin ID
})
```

**Note**: No Wwise-side API exists to control AudioLink-specific settings (channel routing, buffer size, etc.)—those are managed in UE5 Project Settings.

</details>

---

## C++ Class Reference

### UE Engine Side (AudioLink Framework)

Source code: `Engine/Source/Runtime/AudioLink/`

| Class | Module | Role |
|-------|--------|------|
| `IAudioLinkFactory` | AudioLinkEngine | Factory interface. Registers via `IModularFeature`. **Only ONE factory per project** (additional factories assert fatal error). |
| `IAudioLink` | AudioLinkEngine | Opaque link abstraction. Contains paired producer/consumer shared pointers for thread-safe lifetime management. |
| `UAudioLinkSettingsAbstract` | AudioLinkEngine | Base UObject settings class. Serialized as engine assets. Requires `UPROPERTY(Config, EditAnywhere)` and `defaultconfig`. |
| `FAudioLinkSettingsProxy` | AudioLinkEngine | Thread-safe proxy. Ferries editor changes to audio threads via `RefreshFromSettings()`. GC protection via shared pointers. |
| `IBufferedAudioOutput` | AudioLinkEngine | PCM circular buffer (FIFO) interface. |
| `FBufferedSourceListener` | AudioLinkEngine | Built-in source-level buffer consumer. |
| `FBufferedSubmixListener` | AudioLinkEngine | Built-in submix-level buffer consumer. |
| `IAudioLinkSynchronizer` | AudioLinkEngine | External clock sync. Delegates: `Suspend`, `Resume`, `OpenStream`, `CloseStream`, `BeginRender`, `EndRender`. |

**Factory methods** (implemented by middleware like Wwise):
- `CreateSubmixAudioLink()` -- processes submix output
- `CreateSourceAudioLink()` -- handles individual source playback
- `CreateSourcePushedAudioLink()` -- accepts externally-pushed audio
- `CreateSynchronizerAudioLink()` -- manages clock synchronization
- `GetSettingsClass()` -- returns associated settings UClass
- `GetFactoryName()` -- identifies the implementation (e.g., "Wwise")

**Link lifetime rules:**
- Source links terminate when source playback ends
- Submix links persist during application runtime (potential editor lifetime issues)
- `OnFormatKnown` delegate fires when audio format is discovered, triggering playback startup

### Wwise Side (WwiseAudioLink Plugin)

| Class | Module | Role |
|-------|--------|------|
| `WwiseAudioLinkFactory` | WwiseAudioLinkRuntime | Implements `IAudioLinkFactory`. Registered in `StartupModule()`. |
| `WwiseAudioLinkSettings` | WwiseAudioLinkRuntime | Derives from `UAudioLinkSettingsAbstract`. Holds the `AkAudioEvent` reference (Start/Stop events). |
| `WwiseAudioLinkComponent` | WwiseAudioLinkRuntime | Component for per-actor AudioLink management. |
| `WwiseAudioLinkInputClient` | WwiseAudioLinkRuntime | Feeds PCM buffers from UE into the Wwise Audio Input callback. |
| `WwiseAudioLinkSettingsProxy` | WwiseAudioLinkRuntime | Thread-safe proxy for WwiseAudioLinkSettings. |
| `WwiseAudioLinkSynchronizer` | WwiseAudioLinkRuntime | Manages clock sync between UE audio thread and Wwise. |
| `WwiseAudioLinkSettingsFactory` | WwiseAudioLinkEditor | UFactory for creating WwiseAudioLinkSettings assets in Content Browser. |
| `AkAudioInputComponent` | AkAudio | Wwise component with `FillSamplesBuffer` and `GetChannelConfig` overrides. Uses `PostAssociatedAudioInputEvent`. |

### Wwise Plugin Module Structure

Two modules ship as part of the Wwise UE integration:

1. **WwiseAudioLinkRuntime** (Runtime)
   - 9+ source files: Factory, Component, InputClient, Settings, SettingsProxy, Synchronizer
   - Enabled via `bWwiseAudioLinkEnabled` in `/Script/AkAudio.AkSettings` (DefaultEngine.ini)
   - Loaded via `.uplugin` manifest

2. **WwiseAudioLinkEditor** (Editor-only)
   - Settings factory for Content Browser asset creation
   - Editor UI integration

### Blueprint Configuration (no dedicated Blueprint nodes)

AudioLink has NO dedicated Blueprint nodes. All configuration is done through asset properties:

1. **Audio Component** properties: `Sound Attenuation`, `Override Attenuation`, `Sound Submix`
2. **Sound Attenuation** asset: `Attenuation (AudioLink)` section with `AudioLink Settings Override`
3. **Sound Submix** asset: `Audio Link` section with `Send to Audio Link` checkbox + `Audio Link Settings`
4. **Wwise AudioLink Settings** asset: `AudioLink Start Event` (AkAudioEvent reference)

---

## Bus and Submix Routing Architecture

### Recommended Wwise Bus Layout

```
Wwise Master Audio Bus
  |-- SFX Bus (traditional Wwise sounds)
  |     |-- Weapons
  |     |-- Footsteps
  |     |-- Impacts
  |-- Dialogue Bus
  |-- Music Bus
  |-- Procedural Bus (AudioLink destination)
  |     |-- Engines (MetaSounds via AudioLink)
  |     |-- Weather (MetaSounds via AudioLink)
  |     |-- UI Synth (MetaSounds via AudioLink)
  |-- Aux Buses (reverbs, delays)
```

### UE Submix Structure (if using Submix AudioLink method)

```
Master Submix (UE default)
  |-- ProceduralAudio_Submix (Send to AudioLink = true)
  |     Settings: WwiseAudioLinkSettings -> Play_ProceduralInput event
  |-- UIAudio_Submix (Send to AudioLink = true)
        Settings: WwiseAudioLinkSettings -> Play_UIInput event
```

Each AudioLink-enabled submix can point to a different Wwise Audio Input Event, allowing separate Wwise bus routing per audio category.

### Wwise Audio Input Plugin Details

- Built-in plugin (no separate installation)
- Receives PCM data from AudioLink's circular buffer
- Acts as a "feed from a mixer" rather than a spatializable point source
- Appears in Voice Graph only during active playback
- Buffer sizing: use 2:1+ ratio versus consumer bitrate (undersized = dropouts, oversized = latency)

---

## Technical Specifications

### Limitations and Performance

<limitations>

#### Channel Count
- **Maximum channels per AudioLink source**: Not explicitly documented
- **Practical limit**: Stereo (2 channels) most common; multichannel (5.1, 7.1) untested
- **Wwise voice limits apply**: PS4/Xbox One/Switch typically < 100 total voices, desktop/next-gen much higher
- Each AudioLink source consumes 1 Wwise voice (same as any Sound SFX)

#### Latency
- **Typical latency**: 10-50ms (engine + middleware processing)
- **Factors affecting latency**:
  - UE5 audio buffer size (Project Settings → Engine → Audio)
  - Wwise I/O pool size
  - Producer to Consumer Buffer Ratio (higher = more latency)
- **Not suitable for**: Real-time music performance, sample-accurate sync
- **Suitable for**: Game SFX, procedural ambiences, generative audio

#### CPU Overhead
- **AudioLink bridge overhead**: Minimal (< 1% on modern CPUs)
- **Main cost**: Running both UE Audio Engine AND Wwise simultaneously
- **Optimization**: Use AudioLink selectively for procedural sounds; route traditional assets directly through Wwise

#### One-Way Only
- **Direction**: UE Audio --> Wwise (cannot send Wwise audio back to UE)
- **No feedback loop**: Cannot analyze Wwise output in MetaSounds
- **Workaround**: Use RTPC to share game state between systems

#### Single Factory Constraint
- Only ONE `IAudioLinkFactory` can be registered per project
- Cannot use Wwise AudioLink + FMOD AudioLink simultaneously
- Additional factory registrations assert a fatal error on startup

#### Spatialization and Occlusion
- **Obstruction/Occlusion**: Cannot create exclusive occlusion/obstruction in Wwise when source is AudioLink. UE handles it natively but interaction with Wwise spatial features is unclear.
- **Diffraction/Transmission**: Audio Input sources may profile as "100% Transmission Loss" (silent) when Wwise diffraction/transmission features are enabled.
- **3D positioning ambiguity**: When both UE attenuation and Wwise 3D settings are active, behavior is poorly defined. Recommendation: disable one side.
- **Workaround for occlusion**: Use RTPCs to set up level/EQ automation that adapts to environment instead.

#### Stability
- **Audio glitches**: Random loud noise bursts reported. Mitigate with low output levels, master limiters, and app restarts after creating new AudioLink objects.
- **Single-instance looping**: Early iterations only worked reliably with single-instance looping patches.
- **Voice starvation**: Can occur if Wwise voice limits are not configured to account for AudioLink voices.
- **Submix link persistence**: Submix links persist during application runtime, potentially causing editor lifetime issues.

#### Platform Support
- **Confirmed**: Windows, macOS, Linux, PS5, Xbox Series X/S, Switch
- **Not tested**: Mobile (iOS/Android) -- likely works but performance unverified

</limitations>

---

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    UNREAL ENGINE 5                          │
│                                                             │
│  ┌──────────────┐      ┌────────────────┐                 │
│  │ MetaSound    │─────▶│ Audio Component│                 │
│  │ Source       │      │ (with Attenuation)               │
│  └──────────────┘      └────────┬───────┘                 │
│                                  │                          │
│                        Enable Send to AudioLink            │
│                                  │                          │
│                        ┌─────────▼────────┐                │
│                        │ Sound Attenuation│                │
│                        │ - AudioLink Settings Override     │
│                        │ - Wwise Event Reference           │
│                        └─────────┬────────┘                │
│                                  │                          │
│                        ┌─────────▼────────┐                │
│                        │  AudioLink       │                │
│                        │  Submix/Bridge   │                │
│                        └─────────┬────────┘                │
└──────────────────────────────────┼──────────────────────────┘
                                   │ Audio Buffer Stream
                                   │ (PCM, 48kHz typical)
┌──────────────────────────────────▼──────────────────────────┐
│                         WWISE                               │
│                                                             │
│  ┌─────────────────────┐      ┌──────────────┐            │
│  │ Wwise Event         │─────▶│ Sound SFX    │            │
│  │ Play_AudioLink_Input│      │ (Audio Input)│            │
│  └─────────────────────┘      └──────┬───────┘            │
│                                       │                     │
│                             ┌─────────▼────────┐           │
│                             │ Audio Input      │           │
│                             │ Source Plugin    │           │
│                             │ (receives PCM)   │           │
│                             └─────────┬────────┘           │
│                                       │                     │
│                             ┌─────────▼────────┐           │
│                             │ Wwise Audio Graph│           │
│                             │ - Spatialization │           │
│                             │ - Effects        │           │
│                             │ - Mixing         │           │
│                             │ - Bus Routing    │           │
│                             └─────────┬────────┘           │
│                                       │                     │
│                             ┌─────────▼────────┐           │
│                             │ Output (Speakers)│           │
│                             └──────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## Use Cases and Patterns

### 1. Procedural Engine Sounds via MetaSounds

**Problem**: Vehicle engine requires complex synthesis (RPM, load, gear), but needs Wwise's doppler/occlusion/reverb.

**Solution**:
- Build engine synthesis graph in MetaSounds (oscillators, filters, LFO)
- Wire Blueprint parameters (RPM, Throttle) to MetaSound inputs
- Route output through AudioLink to Wwise for spatial processing
- Wwise handles distance attenuation, doppler shift, environmental effects

```
Blueprint (RPM value) → MetaSound (synthesis) → AudioLink → Wwise (spatial) → Output
```

---

### 2. Generative Ambiences with Wwise States

**Problem**: Procedural wind/weather needs to react to Wwise game states (indoor/outdoor).

**Solution**:
- Generate wind noise/modulation in MetaSounds
- Route to Wwise via AudioLink
- Wwise State Group (Indoor/Outdoor) controls reverb, EQ, volume on Audio Input bus
- MetaSounds doesn't need to know about states—Wwise handles context

```
MetaSound (wind generator) → AudioLink → Wwise (state-driven mixing) → Output
```

---

### 3. Rapid Prototyping → Production Handoff

**Problem**: Sound designer needs placeholder procedural audio during development, final sounds via Wwise later.

**Solution**:
- Implement procedural versions in MetaSounds quickly (no Wwise authoring needed)
- Route through AudioLink for spatial consistency
- Later, replace `AudioLink_Input` source in Wwise with authored samples
- No Blueprint/C++ changes needed—swap happens in Wwise project

```
Early: MetaSound → AudioLink → Wwise Audio Input → Output
Late:  [Disabled MetaSound] → Wwise Sample Playback → Output
```

---

### 4. MetaSounds for UI, Wwise for Game Audio

**Problem**: Want MetaSounds' ease for UI bleeps/bloops, but Wwise for all in-game audio.

**Solution**:
- UI sounds: Pure MetaSounds, NO AudioLink (play directly via UE Audio)
- Game audio: Pure Wwise (no MetaSounds)
- Hybrid: Use AudioLink ONLY for specific procedural SFX (e.g., sci-fi interfaces)

**Routing**:
```
UI MetaSounds → UE Audio Engine → UI Submix → Output
Game Audio → Wwise → Master Bus → Output
Hybrid Procedural → MetaSounds → AudioLink → Wwise → Master Bus → Output
```

---

## Common Gotchas

<warnings>

### 1. Attenuation Override Required
**Issue**: Enabling AudioLink in Project Settings alone does nothing.
**Fix**: MUST create Sound Attenuation asset with "Enable Send to AudioLink" checked and assign to each sound individually.

### 2. Wwise Event Must Use Audio Input Source
**Issue**: Creating a generic Wwise Event won't receive AudioLink audio.
**Fix**: Event's target Sound SFX MUST have "Wwise Audio Input" as its source plugin.

### 3. SoundBanks Must Be Regenerated
**Issue**: Adding new AudioLink events doesn't automatically update SoundBanks.
**Fix**: Regenerate SoundBanks in Wwise after creating Audio Input events, ensure they're loaded in UE5.

### 4. Spatialization Conflicts
**Issue**: Both UE and Wwise try to spatialize audio, causing strange positioning.
**Fix**: In Sound Attenuation asset, enable "Attenuation Spatialization" to hand control to Wwise. Disable UE5's built-in spatialization.

### 5. Buffer Underruns on Low-End Hardware
**Issue**: Audio glitches on Switch/mobile when using AudioLink.
**Fix**: Increase Producer to Consumer Buffer Ratio (trade latency for stability). Consider avoiding AudioLink on constrained platforms.

### 6. No Runtime Modification of AudioLink Settings
**Issue**: Cannot change AudioLink routing/settings at runtime via Blueprint.
**Fix**: AudioLink settings are "baked" into Sound Attenuation assets. Create multiple attenuation presets (e.g., `Attenuation_AudioLink_Low_Latency`, `Attenuation_AudioLink_High_Quality`) and swap them on Audio Components.

### 7. Wwise Must Be Running for Editor Testing
**Issue**: AudioLink sounds don't play in UE5 Editor when Wwise Authoring is closed.
**Fix**: Launch Wwise Authoring before testing AudioLink in-editor. For packaged builds, only Wwise runtime (SoundBanks) is needed.

### 8. Do NOT Combine Source + Submix AudioLink for Same Signal
**Issue**: Using both Attenuation-based AudioLink AND Submix-based AudioLink for the same sound causes data duplication.
**Fix**: Choose ONE method per signal chain. Source AudioLink for per-sound control, Submix AudioLink for batch routing.

### 9. Project Settings Gate
**Issue**: Cannot create WwiseAudioLinkSettings assets or see AudioLink options in attenuation dropdown.
**Fix**: "Route through AudioLink [UE5.1+]" in Project Settings MUST be set FIRST. This is a prerequisite gate for the entire AudioLink UI.

</warnings>

---

## Resources

<references>

### Official Documentation
- [AudioLink Overview (Epic Docs)](https://dev.epicgames.com/documentation/en-us/unreal-engine/audiolink) - UE 5.5+ official reference
- [AudioLink Reference Guide (Epic Docs)](https://dev.epicgames.com/documentation/en-us/unreal-engine/audiolink-reference-guide) - UE 5.7 detailed guide
- [Combining Unreal and Wwise Audio with AudioLink (Audiokinetic)](https://www.audiokinetic.com/library/2024.1.7_8863/?id=using_audio_link.html) - Official Wwise integration docs
- [Wwise 2025.1 Release Notes](https://www.audiokinetic.com/en/blog/wwise-2025.1-whats-new/) - Latest Wwise features

### Tutorials and Guides
- [How to use AudioLink in Unreal Engine (Audiokinetic Blog)](https://www.audiokinetic.com/en/blog/how-to-use-audiolink/) - Step-by-step setup
- [Adventures With AudioLink (Audiokinetic Blog)](https://www.audiokinetic.com/en/blog/adventures-with-audiolink/) - Deep-dive use cases
- [Audio Tunnels – UE Audiolink via Wwise (Night on Mars)](https://blog.nightonmars.com/audio-tunnels-ue-audiolink-via-wwise/) - Practical implementation tips
- [Wwise Unreal Engine Integration Tutorial 2025](https://generalistprogrammer.com/tutorials/wwise-unreal-engine-integration-complete-audio-tutorial) - Full Wwise setup

### Community Resources
- [UE5 Audiolink and Wwise spatialisation (UE Forums)](https://forums.unrealengine.com/t/ue5-audiolink-and-wwise-spatialisation-obstruction-occlusion-not-working-as-expected/1735692) - Troubleshooting spatial audio
- [AudioLink spatialization issues (Audiokinetic Q&A)](https://www.audiokinetic.com/qa/12719/audiolink-spatialisation-obstruction-occlusion-expected) - Official Audiokinetic response on limitations
- [Is Audiolink plugin without using middleware? (UE Forums)](https://forums.unrealengine.com/t/is-audiolink-plugin-without-using-any-middleware-fmod-wwise/781765) - Architecture clarification
- [Lyra Game Core Audio Breakdown](https://www.jaydengames.com/posts/ue5-black-magic-game-core-audio/) - Lyra audio architecture analysis
- [IAudioLinkFactory API (UE 5.0 Docs)](https://docs.unrealengine.com/5.0/en-US/API/Runtime/AudioLinkEngine/IAudioLinkFactory/) - Factory interface C++ reference
- [Wwise Audio Input Plugin Docs](https://audiokinetic.com/library/edge/?id=wwise_audio_input_plug_in) - Audio Input source plugin reference
- [Audiokinetic Q&A Forum](https://www.audiokinetic.com/qa/) - Official support forum

</references>

---

## Metadata

<meta>
research-date: 2026-02-15
confidence: high
version-checked: UE 5.1-5.7, Wwise 2022.1-2025.1
last-verified: 2026-02-15
audiolink-status: Beta/Experimental
one-way-only: true (MetaSounds --> Wwise, no reverse)
minimum-ue-version: 5.1
primary-sources: Audiokinetic official docs, Epic Developer Community docs, community blogs
limitations-verified: via community reports, forum threads, and official blog posts
api-availability: UE5 C++ (full), WAAPI (limited to Audio Input object creation), Blueprint (none)
platform-support: Desktop (verified), Console (verified), Mobile (unverified)
</meta>
