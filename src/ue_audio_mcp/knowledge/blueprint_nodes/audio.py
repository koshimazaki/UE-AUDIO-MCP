"""Audio nodes: UE audio, Wwise integration, game audio patterns.

Source: UGameplayStatics API, Audiokinetic Wwise UE5 Integration docs.
"""
from __future__ import annotations

from ue_audio_mcp.knowledge.blueprint_nodes import _n

# ===================================================================
# 1. UGameplayStatics -- Sound Playback (12 nodes)
# ===================================================================

_n("PlaySound2D", "UGameplayStatics", "audio",
   "Plays non-spatial audio (UI sounds)",
   ["audio", "sound", "playback", "spatial"])

_n("PlaySoundAtLocation", "UGameplayStatics", "audio",
   "Plays sound at world position",
   ["audio", "sound", "playback", "spatial"])

_n("SpawnSoundAtLocation", "UGameplayStatics", "audio",
   "Spawns audio component at location (returns component)",
   ["audio", "sound", "playback", "spatial"])

_n("SpawnSoundAttached", "UGameplayStatics", "audio",
   "Spawns audio component attached to component",
   ["audio", "sound", "playback", "spatial"])

_n("CreateSound2D", "UGameplayStatics", "audio",
   "Creates 2D audio component without auto-play",
   ["audio", "sound", "playback", "spatial"])

_n("PlayDialogue2D", "UGameplayStatics", "audio",
   "Plays dialogue without spatial attenuation",
   ["audio", "sound", "playback", "spatial"])

_n("PlayDialogueAtLocation", "UGameplayStatics", "audio",
   "Plays dialogue at world location",
   ["audio", "sound", "playback", "spatial"])

_n("SpawnDialogue2D", "UGameplayStatics", "audio",
   "Spawns 2D dialogue component",
   ["audio", "sound", "playback", "spatial"])

_n("SpawnDialogueAtLocation", "UGameplayStatics", "audio",
   "Spawns dialogue at location",
   ["audio", "sound", "playback", "spatial"])

_n("SpawnDialogueAttached", "UGameplayStatics", "audio",
   "Spawns dialogue attached to component",
   ["audio", "sound", "playback", "spatial"])

_n("PrimeSound", "UGameplayStatics", "audio",
   "Caches initial streamed audio chunk",
   ["audio", "sound", "playback", "spatial"])

_n("PrimeAllSoundsInSoundClass", "UGameplayStatics", "audio",
   "Primes all sounds in a sound class",
   ["audio", "sound", "playback", "spatial"])

# ===================================================================
# 2. UGameplayStatics -- Sound Mix & Modulation (10 nodes)
# ===================================================================

_n("SetBaseSoundMix", "UGameplayStatics", "audio_mix",
   "Sets base sound mix for EQ",
   ["audio", "mix", "modulation"])

_n("PushSoundMixModifier", "UGameplayStatics", "audio_mix",
   "Pushes sound mix modifier onto stack",
   ["audio", "mix", "modulation"])

_n("PopSoundMixModifier", "UGameplayStatics", "audio_mix",
   "Pops sound mix modifier from stack",
   ["audio", "mix", "modulation"])

_n("ClearSoundMixModifiers", "UGameplayStatics", "audio_mix",
   "Clears all sound mix modifiers",
   ["audio", "mix", "modulation"])

_n("SetSoundMixClassOverride", "UGameplayStatics", "audio_mix",
   "Overrides sound class in a mix",
   ["audio", "mix", "modulation"])

_n("ClearSoundMixClassOverride", "UGameplayStatics", "audio_mix",
   "Clears sound class override",
   ["audio", "mix", "modulation"])

_n("SetGlobalPitchModulation", "UGameplayStatics", "audio_mix",
   "Global pitch scalar for non-UI sounds",
   ["audio", "mix", "modulation"])

_n("SetGlobalListenerFocusParameters", "UGameplayStatics", "audio_mix",
   "Scales focus behavior by azimuth",
   ["audio", "mix", "modulation"])

_n("GetMaxAudioChannelCount", "UGameplayStatics", "audio_mix",
   "Returns current audio voice count",
   ["audio", "mix", "modulation"])

_n("AreSubtitlesEnabled", "UGameplayStatics", "audio_mix",
   "Returns subtitle enabled state",
   ["audio", "mix", "modulation"])

# ===================================================================
# 3. UGameplayStatics -- Reverb (3 nodes)
# ===================================================================

_n("ActivateReverbEffect", "UGameplayStatics", "audio_reverb",
   "Activates reverb without audio volume",
   ["audio", "reverb", "effect"])

_n("DeactivateReverbEffect", "UGameplayStatics", "audio_reverb",
   "Deactivates reverb effect",
   ["audio", "reverb", "effect"])

_n("GetCurrentReverbEffect", "UGameplayStatics", "audio_reverb",
   "Returns highest priority active reverb",
   ["audio", "reverb", "effect"])

# ===================================================================
# 4. UGameplayStatics -- Listener (3 nodes)
# ===================================================================

_n("AreAnyListenersWithinRange", "UGameplayStatics", "audio_listener",
   "Checks if any listeners within distance",
   ["audio", "listener", "spatial"])

_n("GetClosestListenerLocation", "UGameplayStatics", "audio_listener",
   "Finds nearest listener position",
   ["audio", "listener", "spatial"])

_n("SetSubtitlesEnabled", "UGameplayStatics", "audio_listener",
   "Enables/disables subtitles",
   ["audio", "listener", "spatial"])

# ===================================================================
# 5. Wwise Integration (25 nodes)
# ===================================================================

_n("Ak_PostEvent", "UAkGameplayStatics", "wwise",
   "Post Wwise event by name on actor",
   ["wwise", "event", "post", "play"])

_n("Ak_PostEventAtLocation", "UAkGameplayStatics", "wwise",
   "Post Wwise event at world location",
   ["wwise", "event", "location", "3d"])

_n("Ak_PostEventByName", "UAkGameplayStatics", "wwise",
   "Post Wwise event by string name",
   ["wwise", "event", "name"])

_n("Ak_SetRTPCValue", "UAkGameplayStatics", "wwise",
   "Set RTPC value by name on actor",
   ["wwise", "rtpc", "parameter"])

_n("Ak_SetState", "UAkGameplayStatics", "wwise",
   "Set Wwise State value",
   ["wwise", "state", "group"])

_n("Ak_SetSwitch", "UAkGameplayStatics", "wwise",
   "Set Wwise Switch value on actor",
   ["wwise", "switch", "group"])

_n("Ak_PostTrigger", "UAkGameplayStatics", "wwise",
   "Post Wwise Trigger on actor",
   ["wwise", "trigger", "post"])

_n("Ak_SetMultiplePositions", "UAkGameplayStatics", "wwise",
   "Set multiple positions for emitter",
   ["wwise", "position", "multi"])

_n("Ak_SetOutputBusVolume", "UAkGameplayStatics", "wwise",
   "Set output bus volume",
   ["wwise", "bus", "volume"])

_n("Ak_LoadBank", "UAkGameplayStatics", "wwise",
   "Load Wwise SoundBank",
   ["wwise", "bank", "load"])

_n("Ak_UnloadBank", "UAkGameplayStatics", "wwise",
   "Unload Wwise SoundBank",
   ["wwise", "bank", "unload"])

_n("Ak_SetBusConfig", "UAkGameplayStatics", "wwise",
   "Set bus channel configuration",
   ["wwise", "bus", "config"])

_n("Ak_StartAllAmbientSounds", "UAkGameplayStatics", "wwise",
   "Start all ambient sound actors",
   ["wwise", "ambient", "start"])

_n("Ak_StopAllAmbientSounds", "UAkGameplayStatics", "wwise",
   "Stop all ambient sound actors",
   ["wwise", "ambient", "stop"])

_n("Ak_StopAll", "UAkGameplayStatics", "wwise",
   "Stop all sounds on actor",
   ["wwise", "stop", "all"])

_n("Ak_GetRTPCValue", "UAkGameplayStatics", "wwise",
   "Get current RTPC value",
   ["wwise", "rtpc", "get"])

_n("Ak_StopActor", "UAkGameplayStatics", "wwise",
   "Stop all Wwise events on actor",
   ["wwise", "stop", "actor"])

_n("AkComponent_PostEvent", "UAkComponent", "wwise",
   "Post Wwise event on AkComponent",
   ["wwise", "component", "event"])

_n("AkComponent_Stop", "UAkComponent", "wwise",
   "Stop all sounds on AkComponent",
   ["wwise", "component", "stop"])

_n("AkComponent_SetRTPCValue", "UAkComponent", "wwise",
   "Set RTPC value on AkComponent",
   ["wwise", "component", "rtpc"])

_n("AkComponent_SetSwitch", "UAkComponent", "wwise",
   "Set Switch on AkComponent",
   ["wwise", "component", "switch"])

_n("AkComponent_SetOcclusionRefreshInterval", "UAkComponent", "wwise",
   "Set occlusion check interval",
   ["wwise", "occlusion", "interval"])

_n("AkComponent_SetAttenuationScalingFactor", "UAkComponent", "wwise",
   "Set attenuation scaling",
   ["wwise", "attenuation", "distance"])

_n("Ak_SetSpeakerAngles", "UAkGameplayStatics", "wwise",
   "Set speaker panning angles",
   ["wwise", "speaker", "panning"])

_n("Ak_GetSpeakerAngles", "UAkGameplayStatics", "wwise",
   "Get speaker panning angles",
   ["wwise", "speaker", "get"])

# ===================================================================
# 6. Game Audio Helpers (12 nodes)
# ===================================================================

_n("GetActorLocation", "AActor", "game_audio",
   "Get world location of actor",
   ["actor", "location", "position"])

_n("GetActorRotation", "AActor", "game_audio",
   "Get world rotation of actor",
   ["actor", "rotation", "direction"])

_n("GetVelocity", "AActor", "game_audio",
   "Get actor movement velocity",
   ["velocity", "speed", "movement"])

_n("GetDistanceTo", "AActor", "game_audio",
   "Get distance between two actors",
   ["distance", "between", "actors"])

_n("VectorLength", "UKismetMathLibrary", "game_audio",
   "Get length of vector (VSize)",
   ["vector", "length", "magnitude"])

_n("GetMaxSpeed", "UMovementComponent", "game_audio",
   "Get max movement speed",
   ["speed", "max", "movement"])

_n("SetActorTickEnabled", "AActor", "game_audio",
   "Enable/disable actor tick",
   ["tick", "enable", "disable"])

_n("GetAudioTimeSeconds", "UGameplayStatics", "game_audio",
   "Audio-synced time for beat matching",
   ["audio", "time", "sync"])

_n("GetWorldDeltaSeconds", "UGameplayStatics", "game_audio",
   "Frame delta time for smooth interpolation",
   ["delta", "time", "frame"])

_n("MapRangeClamped", "UKismetMathLibrary", "game_audio",
   "Map value from one range to another (clamped) for RTPC",
   ["map", "range", "rtpc", "parameter"])

_n("FInterpTo", "UKismetMathLibrary", "game_audio",
   "Smooth float interpolation toward target",
   ["interpolation", "smooth", "parameter"])

_n("PerlinNoise1D", "UKismetMathLibrary", "game_audio",
   "1D Perlin noise for audio modulation",
   ["noise", "perlin", "modulation", "random"])
