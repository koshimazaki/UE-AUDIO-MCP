"""UE5 Blueprint audio function catalogue — GameplayStatics, AudioComponent, Quartz.

Complete reference for Blueprint-callable audio functions in Unreal Engine 5.
Used by:
  - The UE5 plugin bridge (Blueprint tool validation + hints)
  - The knowledge DB seeder (bulk upload to SQLite/D1)
  - The semantic search tool (description + tag matching)

All data sourced from Epic's official UE5 API documentation and
dev.epicgames.com Blueprint API reference.
"""

from __future__ import annotations


# ===================================================================
# Helper types
# ===================================================================

Param = dict         # {"name": str, "type": str, "default": ...}
BlueprintFunc = dict  # Full function definition


def _param(name: str, type_: str, default: object = None) -> Param:
    """Build a parameter descriptor."""
    p: Param = {"name": name, "type": type_}
    if default is not None:
        p["default"] = default
    return p


def _func(
    name: str,
    category: str,
    description: str,
    params: list[Param],
    returns: str | None = None,
    tags: list[str] | None = None,
) -> BlueprintFunc:
    """Build a Blueprint function definition."""
    return {
        "name": name,
        "category": category,
        "description": description,
        "params": params,
        "returns": returns,
        "tags": tags or [],
    }


# ===================================================================
# BLUEPRINT_AUDIO_FUNCTIONS — keyed by name, ~65 entries
# ===================================================================

BLUEPRINT_AUDIO_FUNCTIONS: dict[str, BlueprintFunc] = {}


def _reg(func: BlueprintFunc) -> None:
    BLUEPRINT_AUDIO_FUNCTIONS[func["name"]] = func


# -------------------------------------------------------------------
# GameplayStatics — Sound Playback (fire-and-forget)
# -------------------------------------------------------------------

_reg(_func(
    "PlaySound2D", "GameplayStatics",
    "Play sound with no attenuation, fire-and-forget. Perfect for UI sounds.",
    [_param("Sound", "USoundBase*"),
     _param("VolumeMultiplier", "float", 1.0),
     _param("PitchMultiplier", "float", 1.0),
     _param("StartTime", "float", 0.0),
     _param("ConcurrencySettings", "USoundConcurrency*"),
     _param("OwningActor", "AActor*"),
     _param("bIsUISound", "bool", False)],
    None,
    ["play", "2D", "UI", "fire-and-forget", "non-spatial"],
))

_reg(_func(
    "PlaySoundAtLocation", "GameplayStatics",
    "Play sound at world location with 3D attenuation, fire-and-forget.",
    [_param("Sound", "USoundBase*"),
     _param("Location", "FVector"),
     _param("Rotation", "FRotator"),
     _param("VolumeMultiplier", "float", 1.0),
     _param("PitchMultiplier", "float", 1.0),
     _param("StartTime", "float", 0.0),
     _param("AttenuationSettings", "USoundAttenuation*"),
     _param("ConcurrencySettings", "USoundConcurrency*"),
     _param("OwningActor", "AActor*")],
    None,
    ["play", "3D", "location", "spatial", "fire-and-forget", "attenuation"],
))

_reg(_func(
    "PlayDialogue2D", "GameplayStatics",
    "Play DialogueWave with no attenuation, fire-and-forget.",
    [_param("Dialogue", "UDialogueWave*"),
     _param("Context", "FDialogueContext"),
     _param("VolumeMultiplier", "float", 1.0),
     _param("PitchMultiplier", "float", 1.0),
     _param("StartTime", "float", 0.0)],
    None,
    ["dialogue", "2D", "localisation", "voice"],
))

_reg(_func(
    "PlayDialogueAtLocation", "GameplayStatics",
    "Play DialogueWave at location with 3D attenuation, fire-and-forget.",
    [_param("Dialogue", "UDialogueWave*"),
     _param("Context", "FDialogueContext"),
     _param("Location", "FVector"),
     _param("Rotation", "FRotator"),
     _param("VolumeMultiplier", "float", 1.0),
     _param("PitchMultiplier", "float", 1.0),
     _param("StartTime", "float", 0.0),
     _param("AttenuationSettings", "USoundAttenuation*")],
    None,
    ["dialogue", "3D", "location", "localisation", "voice"],
))

# -------------------------------------------------------------------
# GameplayStatics — Audio Component Creation (controllable)
# -------------------------------------------------------------------

_reg(_func(
    "SpawnSound2D", "GameplayStatics",
    "Create audio component for non-spatial sound with dynamic control.",
    [_param("Sound", "USoundBase*"),
     _param("VolumeMultiplier", "float", 1.0),
     _param("PitchMultiplier", "float", 1.0),
     _param("StartTime", "float", 0.0),
     _param("ConcurrencySettings", "USoundConcurrency*"),
     _param("bPersistAcrossLevelTransition", "bool", False),
     _param("bAutoDestroy", "bool", True)],
    "UAudioComponent*",
    ["spawn", "2D", "component", "controllable", "non-spatial"],
))

_reg(_func(
    "SpawnSoundAtLocation", "GameplayStatics",
    "Create audio component at location for 3D sound with dynamic control.",
    [_param("Sound", "USoundBase*"),
     _param("Location", "FVector"),
     _param("Rotation", "FRotator"),
     _param("VolumeMultiplier", "float", 1.0),
     _param("PitchMultiplier", "float", 1.0),
     _param("StartTime", "float", 0.0),
     _param("AttenuationSettings", "USoundAttenuation*"),
     _param("ConcurrencySettings", "USoundConcurrency*"),
     _param("bAutoDestroy", "bool", True)],
    "UAudioComponent*",
    ["spawn", "3D", "location", "component", "controllable", "spatial"],
))

_reg(_func(
    "SpawnSoundAttached", "GameplayStatics",
    "Create audio component attached to scene component, follows parent transform.",
    [_param("Sound", "USoundBase*"),
     _param("AttachToComponent", "USceneComponent*"),
     _param("AttachPointName", "FName"),
     _param("Location", "FVector"),
     _param("Rotation", "FRotator"),
     _param("LocationType", "EAttachLocation"),
     _param("bStopWhenAttachedToDestroyed", "bool", True),
     _param("VolumeMultiplier", "float", 1.0),
     _param("PitchMultiplier", "float", 1.0),
     _param("StartTime", "float", 0.0),
     _param("AttenuationSettings", "USoundAttenuation*"),
     _param("ConcurrencySettings", "USoundConcurrency*"),
     _param("bAutoDestroy", "bool", True)],
    "UAudioComponent*",
    ["spawn", "attached", "component", "follow", "actor", "3D"],
))

_reg(_func(
    "SpawnDialogue2D", "GameplayStatics",
    "Create audio component for DialogueWave, non-spatial.",
    [_param("Dialogue", "UDialogueWave*"),
     _param("Context", "FDialogueContext"),
     _param("VolumeMultiplier", "float", 1.0),
     _param("PitchMultiplier", "float", 1.0),
     _param("StartTime", "float", 0.0),
     _param("bAutoDestroy", "bool", True)],
    "UAudioComponent*",
    ["dialogue", "spawn", "2D", "component"],
))

_reg(_func(
    "SpawnDialogueAtLocation", "GameplayStatics",
    "Create audio component for DialogueWave at location with 3D attenuation.",
    [_param("Dialogue", "UDialogueWave*"),
     _param("Context", "FDialogueContext"),
     _param("Location", "FVector"),
     _param("Rotation", "FRotator"),
     _param("VolumeMultiplier", "float", 1.0),
     _param("PitchMultiplier", "float", 1.0),
     _param("StartTime", "float", 0.0),
     _param("AttenuationSettings", "USoundAttenuation*"),
     _param("bAutoDestroy", "bool", True)],
    "UAudioComponent*",
    ["dialogue", "spawn", "3D", "location", "component"],
))

_reg(_func(
    "SpawnDialogueAttached", "GameplayStatics",
    "Create audio component for DialogueWave attached to scene component.",
    [_param("Dialogue", "UDialogueWave*"),
     _param("Context", "FDialogueContext"),
     _param("AttachToComponent", "USceneComponent*"),
     _param("AttachPointName", "FName"),
     _param("Location", "FVector"),
     _param("Rotation", "FRotator"),
     _param("LocationType", "EAttachLocation"),
     _param("bStopWhenAttachedToDestroyed", "bool", True),
     _param("VolumeMultiplier", "float", 1.0),
     _param("PitchMultiplier", "float", 1.0),
     _param("StartTime", "float", 0.0),
     _param("AttenuationSettings", "USoundAttenuation*"),
     _param("bAutoDestroy", "bool", True)],
    "UAudioComponent*",
    ["dialogue", "spawn", "attached", "component"],
))

_reg(_func(
    "CreateSound2D", "GameplayStatics",
    "Create audio component without auto-playing, for manual control.",
    [_param("Sound", "USoundBase*"),
     _param("VolumeMultiplier", "float", 1.0),
     _param("PitchMultiplier", "float", 1.0),
     _param("StartTime", "float", 0.0),
     _param("ConcurrencySettings", "USoundConcurrency*"),
     _param("bPersistAcrossLevelTransition", "bool", False),
     _param("bAutoDestroy", "bool", True)],
    "UAudioComponent*",
    ["create", "2D", "component", "manual", "no-autoplay"],
))

# -------------------------------------------------------------------
# GameplayStatics — Sound Mix
# -------------------------------------------------------------------

_reg(_func(
    "SetBaseSoundMix", "GameplayStatics",
    "Set the base sound mix for the audio system EQ and mixing.",
    [_param("InSoundMix", "USoundMix*")],
    None,
    ["mix", "EQ", "base", "global"],
))

_reg(_func(
    "PushSoundMixModifier", "GameplayStatics",
    "Push a sound mix modifier onto the active stack.",
    [_param("InSoundMixModifier", "USoundMix*")],
    None,
    ["mix", "modifier", "push", "stack"],
))

_reg(_func(
    "ClearSoundMixModifiers", "GameplayStatics",
    "Clear all sound mix modifiers from the audio system.",
    [],
    None,
    ["mix", "clear", "reset"],
))

_reg(_func(
    "SetSoundMixClassOverride", "GameplayStatics",
    "Override sound class adjuster in the given sound mix.",
    [_param("InSoundMixModifier", "USoundMix*"),
     _param("InSoundClass", "USoundClass*"),
     _param("Volume", "float", 1.0),
     _param("Pitch", "float", 1.0),
     _param("FadeInTime", "float", 1.0),
     _param("bApplyToChildren", "bool", True)],
    None,
    ["mix", "override", "sound class", "volume", "pitch"],
))

# -------------------------------------------------------------------
# GameplayStatics — Global Audio Settings
# -------------------------------------------------------------------

_reg(_func(
    "SetGlobalPitchModulation", "GameplayStatics",
    "Set global pitch modulation for all sounds.",
    [_param("PitchModulation", "float", 1.0),
     _param("TimeSec", "float", 0.0)],
    None,
    ["global", "pitch", "modulation", "slow-motion"],
))

_reg(_func(
    "SetGlobalListenerFocusParameters", "GameplayStatics",
    "Set parameters for audio focus system affecting spatialization.",
    [_param("FocusAzimuthScale", "float"),
     _param("NonFocusAzimuthScale", "float"),
     _param("FocusDistanceScale", "float"),
     _param("NonFocusDistanceScale", "float"),
     _param("FocusVolumeScale", "float"),
     _param("NonFocusVolumeScale", "float"),
     _param("FocusPriorityScale", "float"),
     _param("NonFocusPriorityScale", "float")],
    None,
    ["global", "listener", "focus", "spatial", "attention"],
))

# -------------------------------------------------------------------
# UAudioComponent — Playback Control
# -------------------------------------------------------------------

_reg(_func(
    "AudioComponent.Play", "AudioComponent",
    "Start audio playback from specified time.",
    [_param("StartTime", "float", 0.0)],
    None,
    ["play", "start", "playback", "component"],
))

_reg(_func(
    "AudioComponent.Stop", "AudioComponent",
    "Stop audio playback immediately.",
    [],
    None,
    ["stop", "playback", "component"],
))

_reg(_func(
    "AudioComponent.StopDelayed", "AudioComponent",
    "Stop audio after delay in seconds.",
    [_param("DelayTime", "float")],
    None,
    ["stop", "delay", "playback"],
))

_reg(_func(
    "AudioComponent.Pause", "AudioComponent",
    "Pause audio playback, can be resumed.",
    [],
    None,
    ["pause", "playback"],
))

_reg(_func(
    "AudioComponent.SetPaused", "AudioComponent",
    "Set pause state explicitly.",
    [_param("bPause", "bool")],
    None,
    ["pause", "resume", "toggle"],
))

_reg(_func(
    "AudioComponent.PlayQuantized", "AudioComponent",
    "Start playback on quantization boundary with Quartz clock.",
    [_param("ClockHandle", "UQuartzClockHandle*"),
     _param("QuantizationBoundary", "FQuartzQuantizationBoundary"),
     _param("Delegate", "FOnQuartzCommandEventBP"),
     _param("StartTime", "float", 0.0),
     _param("FadeInDuration", "float", 0.0),
     _param("FadeVolumeLevel", "float", 1.0),
     _param("FadeCurve", "EAudioFaderCurve", "Linear")],
    None,
    ["play", "quantized", "Quartz", "sync", "beat", "music"],
))

# -------------------------------------------------------------------
# UAudioComponent — Volume Control
# -------------------------------------------------------------------

_reg(_func(
    "AudioComponent.SetVolumeMultiplier", "AudioComponent",
    "Set volume multiplier for the audio component.",
    [_param("NewVolumeMultiplier", "float")],
    None,
    ["volume", "set", "multiplier"],
))

_reg(_func(
    "AudioComponent.AdjustVolume", "AudioComponent",
    "Adjust volume over time with fade curve.",
    [_param("AdjustVolumeDuration", "float"),
     _param("AdjustVolumeLevel", "float"),
     _param("FadeCurve", "EAudioFaderCurve", "Linear")],
    None,
    ["volume", "adjust", "fade", "transition"],
))

_reg(_func(
    "AudioComponent.FadeIn", "AudioComponent",
    "Play sound with volume fade in over duration.",
    [_param("FadeInDuration", "float"),
     _param("FadeVolumeLevel", "float", 1.0),
     _param("StartTime", "float", 0.0),
     _param("FadeCurve", "EAudioFaderCurve", "Linear")],
    None,
    ["fade", "in", "volume", "play", "transition"],
))

_reg(_func(
    "AudioComponent.FadeOut", "AudioComponent",
    "Fade out volume over duration then stop.",
    [_param("FadeOutDuration", "float"),
     _param("FadeVolumeLevel", "float"),
     _param("FadeCurve", "EAudioFaderCurve", "Linear")],
    None,
    ["fade", "out", "volume", "stop", "transition"],
))

# -------------------------------------------------------------------
# UAudioComponent — Pitch & Sound Assignment
# -------------------------------------------------------------------

_reg(_func(
    "AudioComponent.SetPitchMultiplier", "AudioComponent",
    "Set pitch multiplier for the audio component.",
    [_param("NewPitchMultiplier", "float")],
    None,
    ["pitch", "set", "multiplier"],
))

_reg(_func(
    "AudioComponent.SetSound", "AudioComponent",
    "Set the sound asset to be played by this component.",
    [_param("NewSound", "USoundBase*")],
    None,
    ["sound", "set", "assign", "asset"],
))

# -------------------------------------------------------------------
# UAudioComponent — Parameter Control
# -------------------------------------------------------------------

_reg(_func(
    "AudioComponent.SetBoolParameter", "AudioComponent",
    "Set a bool parameter on the sound instance.",
    [_param("InName", "FName"),
     _param("InBool", "bool")],
    None,
    ["parameter", "bool", "MetaSounds"],
))

_reg(_func(
    "AudioComponent.SetFloatParameter", "AudioComponent",
    "Set a float parameter on the sound instance.",
    [_param("InName", "FName"),
     _param("InFloat", "float")],
    None,
    ["parameter", "float", "MetaSounds", "RTPC"],
))

_reg(_func(
    "AudioComponent.SetIntParameter", "AudioComponent",
    "Set an integer parameter on the sound instance.",
    [_param("InName", "FName"),
     _param("InInt", "int32")],
    None,
    ["parameter", "int", "MetaSounds"],
))

_reg(_func(
    "AudioComponent.SetWaveParameter", "AudioComponent",
    "Set a wave parameter (SoundCue compatibility).",
    [_param("InName", "FName"),
     _param("InWave", "USoundWave*")],
    None,
    ["parameter", "wave", "SoundCue"],
))

# -------------------------------------------------------------------
# UAudioComponent — Submix & Bus Control
# -------------------------------------------------------------------

_reg(_func(
    "AudioComponent.SetSubmixSend", "AudioComponent",
    "Set send level to a specified submix.",
    [_param("Submix", "USoundSubmixBase*"),
     _param("SendLevel", "float")],
    None,
    ["submix", "send", "routing", "effect"],
))

_reg(_func(
    "AudioComponent.SetSourceBusSendPreEffect", "AudioComponent",
    "Set audio send to source bus pre-effect.",
    [_param("SoundSourceBus", "USoundSourceBus*"),
     _param("SourceBusSendLevel", "float")],
    None,
    ["bus", "send", "pre-effect", "routing"],
))

_reg(_func(
    "AudioComponent.SetSourceBusSendPostEffect", "AudioComponent",
    "Set audio send to source bus post-effect.",
    [_param("SoundSourceBus", "USoundSourceBus*"),
     _param("SourceBusSendLevel", "float")],
    None,
    ["bus", "send", "post-effect", "routing"],
))

# -------------------------------------------------------------------
# UAudioComponent — Spatialization & Attenuation
# -------------------------------------------------------------------

_reg(_func(
    "AudioComponent.AdjustAttenuation", "AudioComponent",
    "Modify attenuation settings on audio component instance.",
    [_param("InAttenuationSettings", "FSoundAttenuationSettings")],
    None,
    ["attenuation", "3D", "distance", "modify"],
))

_reg(_func(
    "AudioComponent.SetLowPassFilterFrequency", "AudioComponent",
    "Set low-pass filter cutoff frequency in Hz.",
    [_param("InLowPassFilterFrequency", "float")],
    None,
    ["filter", "lowpass", "frequency", "occlusion"],
))

_reg(_func(
    "AudioComponent.SetUISound", "AudioComponent",
    "Mark sound as UI sound (non-spatial, unaffected by pause).",
    [_param("bInUISound", "bool")],
    None,
    ["UI", "non-spatial", "pause"],
))

# -------------------------------------------------------------------
# UAudioComponent — Playback Query
# -------------------------------------------------------------------

_reg(_func(
    "AudioComponent.IsPlaying", "AudioComponent",
    "Returns whether audio is currently playing.",
    [],
    "bool",
    ["query", "playing", "status"],
))

_reg(_func(
    "AudioComponent.GetPlaybackPercentage", "AudioComponent",
    "Returns playback progress as percentage (0-100).",
    [],
    "float",
    ["query", "progress", "percentage"],
))

_reg(_func(
    "AudioComponent.GetPlaybackTime", "AudioComponent",
    "Returns current playback time in seconds.",
    [],
    "float",
    ["query", "time", "position"],
))

# -------------------------------------------------------------------
# AudioVolume — Reverb & Environment
# -------------------------------------------------------------------

_reg(_func(
    "AudioVolume.SetReverbSettings", "AudioVolume",
    "Set reverb settings for audio volume at runtime.",
    [_param("NewReverbSettings", "FReverbSettings")],
    None,
    ["reverb", "volume", "environment", "room"],
))

_reg(_func(
    "AudioVolume.SetInteriorSettings", "AudioVolume",
    "Set interior settings (volume, LPF) for audio volume.",
    [_param("NewInteriorSettings", "FInteriorSettings")],
    None,
    ["interior", "volume", "LPF", "environment"],
))

_reg(_func(
    "AudioVolume.SetEnabled", "AudioVolume",
    "Enable or disable an audio volume.",
    [_param("bNewEnabled", "bool")],
    None,
    ["volume", "enable", "disable", "toggle"],
))

# -------------------------------------------------------------------
# Quartz — Music Timing System
# -------------------------------------------------------------------

_reg(_func(
    "QuartzSubsystem.CreateNewClock", "Quartz",
    "Create a new Quartz clock for sample-accurate scheduling.",
    [_param("ClockName", "FName"),
     _param("InSettings", "FQuartzClockSettings"),
     _param("bOverrideSettingsIfClockExists", "bool", False),
     _param("bUseAudioEngineClockManager", "bool", True)],
    "UQuartzClockHandle*",
    ["Quartz", "clock", "create", "timing", "music"],
))

_reg(_func(
    "QuartzSubsystem.DoesClockExist", "Quartz",
    "Check if a named Quartz clock exists.",
    [_param("ClockName", "FName")],
    "bool",
    ["Quartz", "clock", "exists", "query"],
))

_reg(_func(
    "QuartzClock.StartClock", "Quartz",
    "Start a Quartz clock metronome.",
    [_param("ClockHandle", "UQuartzClockHandle*")],
    None,
    ["Quartz", "clock", "start", "metronome"],
))

_reg(_func(
    "QuartzClock.StopClock", "Quartz",
    "Stop a Quartz clock.",
    [_param("CancelPendingEvents", "bool", False),
     _param("ClockHandle", "UQuartzClockHandle*")],
    None,
    ["Quartz", "clock", "stop"],
))

_reg(_func(
    "QuartzClock.PauseClock", "Quartz",
    "Pause a Quartz clock.",
    [_param("ClockHandle", "UQuartzClockHandle*")],
    None,
    ["Quartz", "clock", "pause"],
))

_reg(_func(
    "QuartzClock.ResumeClock", "Quartz",
    "Resume a paused Quartz clock.",
    [_param("ClockHandle", "UQuartzClockHandle*")],
    None,
    ["Quartz", "clock", "resume"],
))

_reg(_func(
    "QuartzClock.SetBeatsPerMinute", "Quartz",
    "Change BPM on quantization boundary.",
    [_param("QuantizationBoundary", "FQuartzQuantizationBoundary"),
     _param("Delegate", "FOnQuartzCommandEventBP"),
     _param("ClockHandle", "UQuartzClockHandle*"),
     _param("BeatsPerMinute", "float")],
    None,
    ["Quartz", "BPM", "tempo", "change"],
))

_reg(_func(
    "QuartzClock.SetTicksPerSecond", "Quartz",
    "Change clock tick rate on quantization boundary.",
    [_param("QuantizationBoundary", "FQuartzQuantizationBoundary"),
     _param("Delegate", "FOnQuartzCommandEventBP"),
     _param("ClockHandle", "UQuartzClockHandle*"),
     _param("TicksPerSecond", "float")],
    None,
    ["Quartz", "tick", "rate", "timing"],
))

_reg(_func(
    "QuartzClock.SubscribeToQuantizationEvent", "Quartz",
    "Subscribe to quantization events (bars, beats) for gameplay sync.",
    [_param("InQuantizationBoundary", "EQuartzCommandQuantization"),
     _param("OnQuantizationEvent", "FOnQuartzMetronomeEventBP"),
     _param("ClockHandle", "UQuartzClockHandle*")],
    None,
    ["Quartz", "subscribe", "event", "beat", "bar", "sync"],
))

_reg(_func(
    "QuartzClock.SubscribeToAllQuantizationEvents", "Quartz",
    "Subscribe to all quantization event types.",
    [_param("OnQuantizationEvent", "FOnQuartzMetronomeEventBP"),
     _param("ClockHandle", "UQuartzClockHandle*")],
    None,
    ["Quartz", "subscribe", "all", "events"],
))


# ===================================================================
# Quartz quantization boundaries (enum values)
# ===================================================================

QUARTZ_QUANTIZATION_TYPES: list[str] = [
    "Bar",
    "Beat",
    "ThirtySecondNote",
    "SixteenthNote",
    "EighthNote",
    "QuarterNote",
    "HalfNote",
    "WholeNote",
    "DottedSixteenthNote",
    "DottedEighthNote",
    "DottedQuarterNote",
    "DottedHalfNote",
    "DottedWholeNote",
    "SixteenthNoteTriplet",
    "EighthNoteTriplet",
    "QuarterNoteTriplet",
    "HalfNoteTriplet",
]

# ===================================================================
# Audio fade curves (enum values)
# ===================================================================

AUDIO_FADER_CURVES: list[str] = [
    "Linear",
    "Logarithmic",
    "SCurve",
    "Sin",
]


# ===================================================================
# Query / search helpers
# ===================================================================

def get_functions_by_category(category: str) -> list[BlueprintFunc]:
    """Return all functions in a category (case-insensitive)."""
    cat = category.lower()
    return [f for f in BLUEPRINT_AUDIO_FUNCTIONS.values()
            if f["category"].lower() == cat]


def search_functions(query: str) -> list[BlueprintFunc]:
    """Substring search across name, description, and tags."""
    q = query.lower()
    name_hits: list[BlueprintFunc] = []
    tag_hits: list[BlueprintFunc] = []
    desc_hits: list[BlueprintFunc] = []
    seen: set[str] = set()

    for func in BLUEPRINT_AUDIO_FUNCTIONS.values():
        fid = func["name"]
        if q in func["name"].lower():
            name_hits.append(func)
            seen.add(fid)
        elif any(q in t.lower() for t in func["tags"]):
            if fid not in seen:
                tag_hits.append(func)
                seen.add(fid)
        elif q in func["description"].lower():
            if fid not in seen:
                desc_hits.append(func)
    return name_hits + tag_hits + desc_hits


def get_all_categories() -> dict[str, int]:
    """Return a dict of category -> number of functions."""
    counts: dict[str, int] = {}
    for func in BLUEPRINT_AUDIO_FUNCTIONS.values():
        cat = func["category"]
        counts[cat] = counts.get(cat, 0) + 1
    return dict(sorted(counts.items()))
