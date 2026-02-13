"""Cross-system pin mappings: Blueprint <-> MetaSounds <-> Wwise.

Documents every real connection point across all three audio layers in
UE5 + Wwise projects. These mappings represent how game code (Blueprint),
DSP synthesis (MetaSounds), and mixing/spatialization (Wwise) communicate
at runtime through their respective APIs.

Architecture (three-layer):
  Blueprint (WHEN) --PostEvent/SetRTPCValue-----> Wwise (HOW)
  Blueprint (WHEN) --SetXParameter/delegate-----> MetaSounds (WHAT)
  MetaSounds (WHAT) --AudioLink (one-way audio)-> Wwise (HOW)
  Wwise (HOW)      --callbacks/markers----------> Blueprint (WHEN)

Data sources:
  - src/ue_audio_mcp/knowledge/blueprint_audio.py (65 BP functions)
  - src/ue_audio_mcp/knowledge/metasound_nodes.py (144 MS nodes, 798 pins)
  - src/ue_audio_mcp/knowledge/wwise_types.py (19 types, 24 properties)
  - src/ue_audio_mcp/knowledge/tutorials.py (interfaces, Builder API, RTPC)
  - src/ue_audio_mcp/templates/blueprints/*.json (30 BP templates)
  - src/ue_audio_mcp/templates/metasounds/*.json (22 MS templates)
  - src/ue_audio_mcp/templates/wwise/*.json (6 Wwise hierarchy templates)
  - Epic MetaSounds Reference Guide, UAudioComponent API docs
  - Audiokinetic WAAPI Reference, Wwise SDK AkComponent documentation

Used by:
  - Knowledge DB seeder (seed.py) -> SQLite bp_ms_pin_mappings table
  - Semantic search for cross-layer wiring queries
  - build_audio_system orchestrator for connection validation
  - Agent context for answering "how do I connect X to Y" questions
"""
from __future__ import annotations


# ===================================================================
# PIN_MAPPINGS — comprehensive Blueprint <-> MetaSounds <-> Wwise table
# ===================================================================
#
# Directions:
#   "bp_to_ms"      — Blueprint sets a value that flows INTO a MetaSounds graph input
#   "ms_to_bp"      — MetaSounds graph output fires BACK to a Blueprint delegate/event
#   "bp_to_wwise"   — Blueprint sends a command/parameter TO Wwise (PostEvent, SetRTPC, etc.)
#   "ms_to_wwise"   — MetaSounds audio output routes TO Wwise via AudioLink
#   "wwise_to_bp"   — Wwise fires a callback/marker BACK to Blueprint delegates
#
# The ms_node field is either:
#   "__graph__"   — refers to a MetaSounds Source graph-level input/output
#   "(wwise)"     — refers to a Wwise object as the target (for BP->Wwise mappings)
#   "(audiolink)" — refers to the AudioLink bridge (for MS->Wwise mappings)
#   A specific node name from METASOUND_NODES (for internal pin references)
#
# All ms_pin names are verified against metasound_nodes.py, wwise_types.py,
# or template inputs/outputs.

PIN_MAPPINGS: list[dict] = [

    # =================================================================
    # Section 1: AudioComponent.Play/Stop -> MetaSounds Interface Triggers
    #
    # When a Blueprint calls AudioComponent.Play(), the engine sends the
    # OnPlay trigger to the MetaSounds graph. This is the UE.Source.OneShot
    # or UE.Source.Looping interface — automatic, not user-configurable.
    # =================================================================

    {
        "bp_function": "AudioComponent.Play",
        "bp_pin": "StartTime",
        "ms_node": "__graph__",
        "ms_pin": "OnPlay",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Calling Play() on AudioComponent fires the OnPlay trigger in the MetaSounds graph. StartTime parameter offsets playback position. This is the UE.Source.OneShot/Looping interface input — every MetaSounds Source receives this automatically.",
    },
    {
        "bp_function": "AudioComponent.Stop",
        "bp_pin": "(implicit)",
        "ms_node": "__graph__",
        "ms_pin": "OnFinished",
        "data_type": "Trigger",
        "direction": "ms_to_bp",
        "description": "When the MetaSounds graph fires OnFinished (via interface output), the engine triggers the AudioComponent's OnAudioFinished delegate in Blueprint. Stop() forces immediate shutdown.",
    },
    {
        "bp_function": "AudioComponent.PlayQuantized",
        "bp_pin": "ClockHandle",
        "ms_node": "__graph__",
        "ms_pin": "OnPlay",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "PlayQuantized defers the OnPlay trigger until the next Quartz quantization boundary (bar, beat, etc.). The MetaSounds graph receives the same OnPlay trigger but sample-accurately aligned to the clock.",
    },
    {
        "bp_function": "AudioComponent.FadeIn",
        "bp_pin": "FadeInDuration",
        "ms_node": "__graph__",
        "ms_pin": "OnPlay",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "FadeIn calls Play internally, sending OnPlay to the graph. The engine handles volume ramping externally — the MetaSounds graph receives a normal OnPlay trigger.",
    },

    # =================================================================
    # Section 2: SetFloatParameter -> MetaSounds Float Graph Inputs
    #
    # The primary real-time parameter bridge. Blueprint calls
    # AudioComponent.SetFloatParameter('ParamName', value) and the
    # engine writes to the matching graph input node.
    # =================================================================

    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "PawnSpeed",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Wind system: Blueprint reads character velocity magnitude per-tick, sends to MetaSounds PawnSpeed input. PawnSpeed drives Biquad Filter cutoff via Map Range — faster movement = higher cutoff = brighter wind noise.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Distance",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Gunshot/spatial system: Blueprint calculates distance from listener to source, sends normalized distance. MetaSounds uses it to crossfade between close/mid/far sample layers via MSP_CrossFadeByParam_3Inputs or Map Range -> mixer gains.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Intensity",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Ambient/weather system: Blueprint sends normalized intensity (0-1) from game state (weather system, time-of-day). MetaSounds uses it to control layer volumes, filter cutoffs, or LFO depths.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Morph",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Preset morph system: Blueprint sends morph value (0-1) to crossfade between two preset parameter sets. MetaSounds uses Map Range to interpolate cutoff, bandwidth, and other parameters.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Cutoff Frequency",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Synth/filter control: Blueprint sends filter cutoff in Hz directly to MetaSounds graph input. Wired internally to Biquad Filter or Ladder Filter 'Cutoff Frequency' input pin.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Bandwidth",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Synth/filter control: Blueprint sends filter bandwidth (Q) to MetaSounds. Wired to Biquad Filter 'Bandwidth' pin. Lower values = more resonant peak.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Frequency",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Oscillator frequency control: Blueprint sends frequency in Hz to MetaSounds graph input. Wired internally to oscillator (Sine/Saw/Square/Triangle) 'Frequency' pin. Used in SID lead, synths.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Filter Cutoff",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "SID chip / synth filter: Blueprint sends normalized cutoff (0-1) to MetaSounds. Wired to SID Filter 'Cutoff' pin or Biquad Filter with Map Range scaling.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Resonance",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Filter resonance control: Blueprint sends resonance (0-1) to MetaSounds. Wired to State Variable Filter, Ladder Filter, or SID Filter 'Resonance' pin.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Volume",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Volume control inside MetaSounds graph: Blueprint sends volume (0-1) to graph input, wired to Multiply (Audio) B pin or Mono Mixer gain pin. Different from AudioComponent.SetVolumeMultiplier which operates externally.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Volume_Master",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Weapon burst master volume: Blueprint controls overall loudness of the weapon sound. Wired to MSP_RandomizationNode 'Volume_Master' input across all layers.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Pitch Shift",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Sample pitch control: Blueprint sends pitch shift value to MetaSounds. Wired to Wave Player (Mono/Stereo) 'Pitch Shift' pin. Units are semitones.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Pulse Width",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "PWM synth control: Blueprint sends pulse width (0-1) to MetaSounds. Wired to Square oscillator 'Pulse Width' pin or SID Voice/Oscillator 'Pulse Width' pin.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Detune",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Dual-oscillator detune: Blueprint sends detune amount in Hz. Used in SID lead template — wired to Add node alongside main Frequency to offset second oscillator.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Glide",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Portamento control: Blueprint sends glide time to MetaSounds. Wired to InterpTo 'Interp Time' pin for smooth pitch transitions between notes.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Mixer Saw",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Mono synth oscillator mix: Blueprint sets Saw oscillator level. Wired to Mono Mixer 'Gain 0' pin. Allows real-time oscillator balance from gameplay code.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Mixer Noise",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Mono synth noise mix: Blueprint sets Pink Noise level. Wired to Mono Mixer 'Gain 1' pin.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Mixer Square",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Mono synth oscillator mix: Blueprint sets Square oscillator level. Wired to Mono Mixer 'Gain 2' pin.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Filter env amount",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Mono synth filter envelope depth: Blueprint sets how far the filter opens in Hz. Wired to Map Range 'Out Range B' pin — envelope peak cutoff frequency.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Period",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Mono synth note rate: Blueprint sends note duration in seconds. Wired to Trigger Repeat 'Period' pin for sequencer step timing.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Env Att / Dec ratio",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Mono synth envelope shape: Blueprint sends attack/decay ratio. Used by MSP_ADControl to split Period between attack and decay phases.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Azimuth",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Spatial panning: Blueprint calculates azimuth angle from listener to sound source, sends to MetaSounds. Wired to ITD Panner 'Angle' pin for binaural 3D positioning.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "WindSpeed",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Weather system: Blueprint sends wind speed from weather subsystem. MetaSounds uses it to modulate noise filter cutoff and LFO rate for procedural wind.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "TimeOfDay",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Ambient system: Blueprint sends hour (0-24) from day/night cycle. MetaSounds uses Map Range to crossfade between day and night ambient layers.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "BaseFrequency",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "SFX generator: Blueprint sends base frequency for procedural sound synthesis. Wired through Linear To Log Frequency to oscillator Frequency pins.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "BurstRate",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Weapon burst fire: Blueprint sends time between shots (seconds). Wired to Trigger Repeat 'Period' pin. 0.08 = 750 RPM, 0.12 = 500 RPM.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Pitch_RandomMin",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Weapon burst pitch variation: Blueprint sends minimum random pitch offset (semitones). Wired to MSP_RandomizationNode 'Pitch_RandomMin' pin.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Pitch_RandomMax",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Weapon burst pitch variation: Blueprint sends maximum random pitch offset (semitones). Wired to MSP_RandomizationNode 'Pitch_RandomMax' pin.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Res Boost",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "SID synth resonance boost: Blueprint sends boost amount for self-oscillation. Wired to SID Filter 'Res Boost' pin.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Pan Amount",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Stereo pan control: Blueprint sends pan position (-1 left, +1 right). Wired to Stereo Panner 'Pan Amount' pin.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Loop Start",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Sample loop point: Blueprint sets loop start time in seconds. Wired to Wave Player 'Loop Start' pin. Used in sample_player template with slider widget.",
    },
    {
        "bp_function": "AudioComponent.SetFloatParameter",
        "bp_pin": "InFloat",
        "ms_node": "__graph__",
        "ms_pin": "Loop Duration",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Sample loop length: Blueprint sets loop duration in seconds (-1 for whole file). Wired to Wave Player 'Loop Duration' pin.",
    },

    # =================================================================
    # Section 3: SetIntParameter -> MetaSounds Int32 Graph Inputs
    # =================================================================

    {
        "bp_function": "AudioComponent.SetIntParameter",
        "bp_pin": "InInt",
        "ms_node": "__graph__",
        "ms_pin": "SurfaceType",
        "data_type": "Int32",
        "direction": "bp_to_ms",
        "description": "Footstep system: Blueprint sends surface type index from physical material trace (0=concrete, 1=grass, 2=metal, 3=wood). Wired to Trigger Route 'Index' pin to select per-surface sample arrays.",
    },
    {
        "bp_function": "AudioComponent.SetIntParameter",
        "bp_pin": "InInt",
        "ms_node": "__graph__",
        "ms_pin": "WeatherState",
        "data_type": "Int32",
        "direction": "bp_to_ms",
        "description": "Weather system: Blueprint sends weather state index (0=clear, 1=rain, 2=storm, 3=snow). MetaSounds uses Trigger Route or Trigger Compare to switch between DSP processing branches.",
    },
    {
        "bp_function": "AudioComponent.SetIntParameter",
        "bp_pin": "InInt",
        "ms_node": "__graph__",
        "ms_pin": "RoomSize",
        "data_type": "Int32",
        "direction": "bp_to_ms",
        "description": "Weapon reverb selection: Blueprint sends room size index (0=outdoor, 1=small, 2=medium, 3=large) from room detection volume overlap. Wired to MSP_Switch_3Inputs 'InputParameter' pin.",
    },
    {
        "bp_function": "AudioComponent.SetIntParameter",
        "bp_pin": "InInt",
        "ms_node": "__graph__",
        "ms_pin": "RootNote",
        "data_type": "Int32",
        "direction": "bp_to_ms",
        "description": "Sound pad MIDI pitch: Blueprint sends MIDI note number (60=C4). Wired to MIDI To Frequency node 'MIDI In' pin — Hz conversion happens inside MetaSounds, keeping Blueprint code integer-clean.",
    },
    {
        "bp_function": "AudioComponent.SetIntParameter",
        "bp_pin": "InInt",
        "ms_node": "__graph__",
        "ms_pin": "ScaleDegree",
        "data_type": "Int32",
        "direction": "bp_to_ms",
        "description": "Sound pad scale degree: Blueprint sends index (0-6) into a scale array. MetaSounds looks up the interval from a graph variable array (MajorScaleArray) and adds to RootNote.",
    },
    {
        "bp_function": "AudioComponent.SetIntParameter",
        "bp_pin": "InInt",
        "ms_node": "__graph__",
        "ms_pin": "BurstCount",
        "data_type": "Int32",
        "direction": "bp_to_ms",
        "description": "Weapon burst shot count: Blueprint sends number of shots per burst (3 = 3-round burst, 0 = full auto). Wired to Trigger Compare (Int32) 'B' pin to stop the Trigger Repeat after N shots.",
    },

    # =================================================================
    # Section 4: SetBoolParameter -> MetaSounds Bool Graph Inputs
    # =================================================================

    {
        "bp_function": "AudioComponent.SetBoolParameter",
        "bp_pin": "InBool",
        "ms_node": "__graph__",
        "ms_pin": "Enabled",
        "data_type": "Bool",
        "direction": "bp_to_ms",
        "description": "General enable/disable: Blueprint toggles sound generation on/off. Wired to oscillator 'Enabled' pin or used as a gate condition for processing branches.",
    },
    {
        "bp_function": "AudioComponent.SetBoolParameter",
        "bp_pin": "InBool",
        "ms_node": "__graph__",
        "ms_pin": "Loop",
        "data_type": "Bool",
        "direction": "bp_to_ms",
        "description": "Loop control: Blueprint enables/disables looping at runtime. Wired to Wave Player 'Loop' pin. Allows switching between one-shot and looping modes from gameplay.",
    },
    {
        "bp_function": "AudioComponent.SetBoolParameter",
        "bp_pin": "InBool",
        "ms_node": "__graph__",
        "ms_pin": "Detonate",
        "data_type": "Bool",
        "direction": "bp_to_ms",
        "description": "Bomb fuse system: Blueprint sends true after timer delay to trigger explosion sound. From MetaSounds Quick Start tutorial — SetBoolParameter('Detonate', true) after 3-second delay.",
    },

    # =================================================================
    # Section 5: SetTriggerParameter / ExecuteTriggerParameter
    #            -> MetaSounds Trigger Graph Inputs
    #
    # Trigger parameters fire a one-shot pulse in the graph. Unlike
    # Float/Int/Bool, triggers don't hold a value — they pulse once.
    # =================================================================

    {
        "bp_function": "AudioComponent.SetTriggerParameter",
        "bp_pin": "InName",
        "ms_node": "__graph__",
        "ms_pin": "TriggerSound",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Sound pad synth trigger: Blueprint fires the synth playback path in MetaSounds. The trigger pulse flows to AD/ADSR Envelope 'Trigger' pin and Wave Player 'Play' pin.",
    },
    {
        "bp_function": "AudioComponent.SetTriggerParameter",
        "bp_pin": "InName",
        "ms_node": "__graph__",
        "ms_pin": "PlayAudioFile",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Sound pad sample trigger: Blueprint fires the sample playback path. The trigger flows to a separate Wave Player 'Play' pin for audio file mode.",
    },
    {
        "bp_function": "AudioComponent.ExecuteTriggerParameter",
        "bp_pin": "InName",
        "ms_node": "__graph__",
        "ms_pin": "On Stop",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Footfalls graceful stop: Blueprint sends On Stop trigger when character stops moving or becomes airborne. MetaSounds receives it to let current footfall finish naturally rather than cutting off abruptly.",
    },
    {
        "bp_function": "AudioComponent.SetTriggerParameter",
        "bp_pin": "InName",
        "ms_node": "__graph__",
        "ms_pin": "OnStop",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Ambient system stop: Blueprint fires OnStop trigger to gracefully fade out ambient loop. Wired to AD Envelope trigger for fade-out or Trigger Control 'Close' pin.",
    },
    {
        "bp_function": "AudioComponent.SetTriggerParameter",
        "bp_pin": "InName",
        "ms_node": "__graph__",
        "ms_pin": "MacroStep1",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Macro sequence trigger: Blueprint fires MacroStep1 to advance the sequence. Wired to graph variable set nodes for filter/amplitude parameter transitions.",
    },
    {
        "bp_function": "AudioComponent.SetTriggerParameter",
        "bp_pin": "InName",
        "ms_node": "__graph__",
        "ms_pin": "MacroStep2",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Macro sequence trigger: Blueprint fires MacroStep2 for second transition point. Same wiring pattern as MacroStep1 but targeting different parameter values.",
    },

    # =================================================================
    # Section 6: SetWaveParameter -> MetaSounds WaveAsset Graph Inputs
    # =================================================================

    {
        "bp_function": "AudioComponent.SetWaveParameter",
        "bp_pin": "InWave",
        "ms_node": "__graph__",
        "ms_pin": "AudioFile",
        "data_type": "WaveAsset",
        "direction": "bp_to_ms",
        "description": "Sound pad wave swap: Blueprint sets the wave asset for sample playback mode. Wired to Wave Player 'Wave Asset' pin. Allows per-pad audio file selection from struct configuration.",
    },
    {
        "bp_function": "AudioComponent.SetWaveParameter",
        "bp_pin": "InWave",
        "ms_node": "__graph__",
        "ms_pin": "Wave Asset",
        "data_type": "WaveAsset",
        "direction": "bp_to_ms",
        "description": "General sample swap: Blueprint sets the wave asset at runtime. Wired to Wave Player (Mono/Stereo) 'Wave Asset' input pin. Used in sample_player template.",
    },
    {
        "bp_function": "AudioComponent.SetWaveParameter",
        "bp_pin": "InWave",
        "ms_node": "__graph__",
        "ms_pin": "BaseLoop",
        "data_type": "WaveAsset",
        "direction": "bp_to_ms",
        "description": "Ambient system loop swap: Blueprint sets the base ambient loop wave asset at runtime. Wired to looping Wave Player 'Wave Asset' pin.",
    },

    # =================================================================
    # Section 7: MetaSounds Graph Outputs -> Blueprint Delegates
    #
    # These flow FROM MetaSounds BACK to Blueprint. The engine maps
    # graph output triggers to UAudioComponent multicast delegates.
    # =================================================================

    {
        "bp_function": "AudioComponent.OnAudioFinished",
        "bp_pin": "Delegate",
        "ms_node": "__graph__",
        "ms_pin": "OnFinished",
        "data_type": "Trigger",
        "direction": "ms_to_bp",
        "description": "MetaSounds graph fires OnFinished (UE.Source interface output) when playback completes. Blueprint receives this as OnAudioFinished delegate — used for chaining sounds, cleanup, or triggering next action.",
    },
    {
        "bp_function": "AudioComponent.OnAudioPlaybackPercent",
        "bp_pin": "Delegate(Percent)",
        "ms_node": "__graph__",
        "ms_pin": "Playback Location",
        "data_type": "Float",
        "direction": "ms_to_bp",
        "description": "Wave Player exposes Playback Location as a float output. The engine maps this to the OnAudioPlaybackPercent delegate, allowing Blueprint to react to playback progress (e.g. sync visual effects to audio position).",
    },
    {
        "bp_function": "AudioComponent.OnAudioFinished",
        "bp_pin": "Delegate",
        "ms_node": "Wave Player (Stereo)",
        "ms_pin": "On Finished",
        "data_type": "Trigger",
        "direction": "ms_to_bp",
        "description": "Individual Wave Player On Finished trigger — fires when a specific sample finishes playing. When wired to __graph__ OnFinished output, this becomes the AudioComponent.OnAudioFinished delegate.",
    },
    {
        "bp_function": "AudioComponent.OnAudioFinished",
        "bp_pin": "Delegate",
        "ms_node": "Wave Player (Mono)",
        "ms_pin": "On Finished",
        "data_type": "Trigger",
        "direction": "ms_to_bp",
        "description": "Mono Wave Player completion: On Finished trigger fires when sample ends. Wired to graph OnFinished output to propagate to Blueprint OnAudioFinished delegate.",
    },

    # =================================================================
    # Section 8: AudioComponent External Controls -> MetaSounds
    #
    # These are AudioComponent functions that affect the MetaSounds
    # playback externally (outside the graph), but have equivalent
    # in-graph pins if you want finer control.
    # =================================================================

    {
        "bp_function": "AudioComponent.SetVolumeMultiplier",
        "bp_pin": "NewVolumeMultiplier",
        "ms_node": "(external)",
        "ms_pin": "N/A",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "External volume scaling applied AFTER MetaSounds output. Multiplies the final audio signal. Does NOT enter the MetaSounds graph. For in-graph volume control, use SetFloatParameter with a custom graph input wired to Multiply (Audio) or mixer gain.",
    },
    {
        "bp_function": "AudioComponent.SetPitchMultiplier",
        "bp_pin": "NewPitchMultiplier",
        "ms_node": "(external)",
        "ms_pin": "N/A",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "External pitch scaling applied AFTER MetaSounds output. Does NOT enter the graph. For in-graph pitch control, use SetFloatParameter to a graph input wired to oscillator 'Frequency' or Wave Player 'Pitch Shift' pin.",
    },
    {
        "bp_function": "AudioComponent.AdjustVolume",
        "bp_pin": "AdjustVolumeLevel",
        "ms_node": "(external)",
        "ms_pin": "N/A",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "External volume fade over time. Does NOT enter the MetaSounds graph. For in-graph fading, use SetFloatParameter driving an InterpTo node connected to Multiply (Audio) gain.",
    },
    {
        "bp_function": "AudioComponent.SetLowPassFilterFrequency",
        "bp_pin": "InLowPassFilterFrequency",
        "ms_node": "(external)",
        "ms_pin": "N/A",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "External LPF applied outside the graph (used for occlusion). Does NOT enter MetaSounds. For in-graph filtering, use SetFloatParameter driving Biquad Filter 'Cutoff Frequency' or One-Pole Low Pass Filter 'Cutoff Frequency' pin.",
    },

    # =================================================================
    # Section 9: Physics/Animation -> MetaSounds via AudioComponent
    #
    # Blueprint physics events and animation notifies don't connect
    # directly to MetaSounds. They go through AudioComponent functions
    # which then set graph parameters.
    # =================================================================

    {
        "bp_function": "ReceiveHit (Physics)",
        "bp_pin": "NormalImpulse",
        "ms_node": "__graph__",
        "ms_pin": "Intensity",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Physics impact audio: Blueprint receives ReceiveHit event, VSize(NormalImpulse) gives impact magnitude, MapRangeClamped normalizes to 0-1, SetFloatParameter('Intensity', value) sends to MetaSounds. Graph uses Intensity for amplitude envelope or filter modulation.",
    },
    {
        "bp_function": "GetPhysicsAngularVelocityInDegrees",
        "bp_pin": "ReturnValue (VSize)",
        "ms_node": "__graph__",
        "ms_pin": "Frequency",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Rolling physics audio: Blueprint reads angular velocity per-tick, VSize gives rotation speed, MapRangeClamped maps to frequency range, SetFloatParameter sends to MetaSounds oscillator or filter cutoff. Faster rotation = higher frequency.",
    },
    {
        "bp_function": "GetPhysicsLinearVelocity",
        "bp_pin": "ReturnValue (VSize)",
        "ms_node": "__graph__",
        "ms_pin": "PawnSpeed",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Sliding/scraping physics: Blueprint reads linear velocity per-tick, VSize gives speed magnitude, MapRangeClamped normalizes, SetFloatParameter sends to MetaSounds. Speed drives filter cutoff or mix level for scraping sound.",
    },
    {
        "bp_function": "AnimNotify_PlaySound",
        "bp_pin": "Sound",
        "ms_node": "__graph__",
        "ms_pin": "OnPlay",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Animation notify: Animation montage fires PlaySound notify at specific frame. Engine plays the MetaSounds Source, sending OnPlay trigger. Used for character footsteps, weapon swing sounds, and impact moments synced to animation.",
    },
    {
        "bp_function": "PlayAnimNotifySound (Custom)",
        "bp_pin": "AudioComponent.Play",
        "ms_node": "__graph__",
        "ms_pin": "OnPlay",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Custom anim notify with pre-set parameters: Animation notify Blueprint calls AudioComponent.Play() plus SetIntParameter/SetFloatParameter before playing to configure the MetaSounds graph (e.g., surface type from physical material under foot).",
    },

    # =================================================================
    # Section 10: Quartz Clock -> MetaSounds Timing
    #
    # Quartz provides sample-accurate scheduling from Blueprint.
    # The clock coordinates when sounds play but timing info can
    # also flow into MetaSounds graphs.
    # =================================================================

    {
        "bp_function": "QuartzClock.SubscribeToQuantizationEvent",
        "bp_pin": "OnQuantizationEvent",
        "ms_node": "__graph__",
        "ms_pin": "OnPlay",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Quartz beat sync: Blueprint subscribes to beat/bar events, delegate fires AudioComponent.Play() or SetTriggerParameter on quantization boundary. MetaSounds receives perfectly timed triggers aligned to the musical grid.",
    },
    {
        "bp_function": "QuartzClock.SetBeatsPerMinute",
        "bp_pin": "BeatsPerMinute",
        "ms_node": "__graph__",
        "ms_pin": "Period",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "BPM to MetaSounds rate: Blueprint changes Quartz clock BPM, then calculates period = 60/BPM and sends via SetFloatParameter. MetaSounds Trigger Repeat uses Period for note timing. Can also use BPM To Seconds node inside MetaSounds.",
    },

    # =================================================================
    # Section 11: GameplayStatics -> MetaSounds (fire-and-forget)
    #
    # These create and play a MetaSounds Source without persistent
    # AudioComponent reference. OnPlay trigger is immediate.
    # =================================================================

    {
        "bp_function": "PlaySound2D",
        "bp_pin": "Sound",
        "ms_node": "__graph__",
        "ms_pin": "OnPlay",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Fire-and-forget 2D: Blueprint plays MetaSounds Source non-spatially. Engine sends OnPlay trigger immediately. No AudioComponent reference returned — cannot set parameters after playback starts. Best for UI sounds.",
    },
    {
        "bp_function": "PlaySoundAtLocation",
        "bp_pin": "Sound",
        "ms_node": "__graph__",
        "ms_pin": "OnPlay",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Fire-and-forget 3D: Blueprint plays MetaSounds Source at world location with attenuation. OnPlay trigger fires immediately. No parameter control after start. VolumeMultiplier and PitchMultiplier are external (not graph inputs).",
    },
    {
        "bp_function": "SpawnSoundAtLocation",
        "bp_pin": "ReturnValue",
        "ms_node": "__graph__",
        "ms_pin": "OnPlay",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Spawn 3D with control: Blueprint spawns MetaSounds Source at location, gets AudioComponent reference back. OnPlay trigger fires on spawn. AudioComponent reference enables subsequent SetFloatParameter/SetIntParameter calls.",
    },
    {
        "bp_function": "SpawnSoundAttached",
        "bp_pin": "ReturnValue",
        "ms_node": "__graph__",
        "ms_pin": "OnPlay",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Spawn attached with control: Blueprint spawns MetaSounds Source attached to a scene component (follows parent). Returns AudioComponent for runtime parameter control. OnPlay trigger fires on spawn.",
    },
    {
        "bp_function": "SpawnSound2D",
        "bp_pin": "ReturnValue",
        "ms_node": "__graph__",
        "ms_pin": "OnPlay",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Spawn 2D with control: Blueprint creates non-spatial AudioComponent playing MetaSounds Source. Returns reference for parameter control. OnPlay fires immediately.",
    },

    # =================================================================
    # Section 12: Trigger Box / Overlap -> MetaSounds Triggers
    #
    # Level Blueprint uses trigger volumes to fire named triggers
    # into MetaSounds via Audio Parameter Interface.
    # =================================================================

    {
        "bp_function": "OnActorBeginOverlap",
        "bp_pin": "OtherActor",
        "ms_node": "__graph__",
        "ms_pin": "Birds",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Ambient stinger trigger: Level Blueprint detects player entering Trigger_Birds volume, fires Trigger('Birds') via Audio Parameter Interface. MetaSounds receives trigger to start birds ambient layer (fade in via InterpTo).",
    },
    {
        "bp_function": "OnActorBeginOverlap",
        "bp_pin": "OtherActor",
        "ms_node": "__graph__",
        "ms_pin": "Bugs",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Ambient stinger trigger: Level Blueprint detects player entering Trigger_Bugs volume, fires Trigger('Bugs') via Audio Parameter Interface. MetaSounds receives trigger to start bugs ambient layer.",
    },
    {
        "bp_function": "OnComponentBeginOverlap",
        "bp_pin": "OtherActor",
        "ms_node": "__graph__",
        "ms_pin": "OnPlay",
        "data_type": "Trigger",
        "direction": "bp_to_ms",
        "description": "Zone-based audio: Blueprint detects player entering audio zone (SphereComponent overlap), enables tick for per-frame parameter updates and calls AudioComponent.Play() to start MetaSounds playback.",
    },

    # =================================================================
    # Section 13: MetaSounds Interface Pins (UE.Source, UE.Attenuation,
    #             UE.Spatialization)
    #
    # These are engine-managed connections — the engine automatically
    # feeds distance, azimuth, and elevation from the AudioComponent's
    # world position into the MetaSounds graph.
    # =================================================================

    {
        "bp_function": "(Engine: AudioComponent WorldPosition)",
        "bp_pin": "Distance (calculated)",
        "ms_node": "__graph__",
        "ms_pin": "Distance",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "UE.Attenuation interface: Engine automatically calculates listener-to-source distance and feeds it into the MetaSounds graph 'Distance' input. Used by custom attenuation curves built inside MetaSounds (Map Range -> Multiply for volume falloff).",
    },
    {
        "bp_function": "(Engine: AudioComponent WorldPosition)",
        "bp_pin": "Azimuth (calculated)",
        "ms_node": "__graph__",
        "ms_pin": "Azimuth",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "UE.Spatialization interface: Engine calculates azimuth angle from listener forward vector to source direction. Fed into MetaSounds graph for custom spatialization (ITD Panner, MSP_HeightEQ_Node).",
    },
    {
        "bp_function": "(Engine: AudioComponent WorldPosition)",
        "bp_pin": "Elevation (calculated)",
        "ms_node": "__graph__",
        "ms_pin": "Elevation",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "UE.Spatialization interface: Engine calculates elevation angle from listener to source. Fed into MetaSounds for height-based EQ or spatialization (MSP_HeightEQ_Node 'UE.Spatialization.Elevation' pin).",
    },

    # =================================================================
    # Section 14: MetaSounds Audio Outputs -> Engine Output Bus
    #
    # The stereo audio outputs from MetaSounds flow to the engine's
    # audio pipeline. These are set by the UE.Source interface.
    # =================================================================

    {
        "bp_function": "(Engine: Audio Pipeline)",
        "bp_pin": "Left Channel",
        "ms_node": "__graph__",
        "ms_pin": "Out Left",
        "data_type": "Audio",
        "direction": "ms_to_bp",
        "description": "UE.Source interface stereo left output: MetaSounds graph routes processed audio to Out Left. Engine receives this as the left channel for the AudioComponent's audio stream, subject to external attenuation, spatialization, and submix routing.",
    },
    {
        "bp_function": "(Engine: Audio Pipeline)",
        "bp_pin": "Right Channel",
        "ms_node": "__graph__",
        "ms_pin": "Out Right",
        "data_type": "Audio",
        "direction": "ms_to_bp",
        "description": "UE.Source interface stereo right output: MetaSounds graph routes processed audio to Out Right. Engine receives this as the right channel.",
    },

    # =================================================================
    # Section 15: Submix/Bus Control from Blueprint
    # =================================================================

    {
        "bp_function": "AudioComponent.SetSubmixSend",
        "bp_pin": "SendLevel",
        "ms_node": "(external submix)",
        "ms_pin": "N/A",
        "data_type": "Float",
        "direction": "bp_to_ms",
        "description": "Submix routing: Blueprint controls how much of the AudioComponent's output is sent to a submix (reverb, EQ, analysis). This is external to MetaSounds — operates on the engine's submix graph after MetaSounds output.",
    },

    # =================================================================
    # Section 16: Wave Player Cue Points -> Blueprint
    # =================================================================

    {
        "bp_function": "AudioComponent.OnAudioCuePoint (via graph output)",
        "bp_pin": "CuePointID",
        "ms_node": "Wave Player (Stereo)",
        "ms_pin": "On Cue Point",
        "data_type": "Trigger",
        "direction": "ms_to_bp",
        "description": "Cue point callback: Wave Player fires 'On Cue Point' trigger when playback reaches a cue point marker embedded in the WAV file. Cue Point ID (Int32) and Cue Point Label (String) outputs provide marker identification. Wired to graph outputs, these can drive Blueprint events for gameplay synchronization.",
    },
    {
        "bp_function": "AudioComponent.OnAudioCuePoint (via graph output)",
        "bp_pin": "CuePointLabel",
        "ms_node": "Wave Player (Stereo)",
        "ms_pin": "Cue Point Label",
        "data_type": "String",
        "direction": "ms_to_bp",
        "description": "Cue point label: String identifier for the cue point marker. Blueprint can switch on label name to trigger different gameplay events (e.g., 'verse', 'chorus', 'impact_frame').",
    },

    # =================================================================
    # Section 17: Playback State Queries
    # =================================================================

    {
        "bp_function": "AudioComponent.IsPlaying",
        "bp_pin": "ReturnValue",
        "ms_node": "(engine state)",
        "ms_pin": "N/A",
        "data_type": "Bool",
        "direction": "ms_to_bp",
        "description": "Blueprint queries whether the MetaSounds source is currently generating audio. Returns true between Play() and OnFinished/Stop(). Does not query internal MetaSounds graph state — only engine-level playback status.",
    },
    {
        "bp_function": "AudioComponent.GetPlaybackTime",
        "bp_pin": "ReturnValue",
        "ms_node": "Wave Player (Stereo)",
        "ms_pin": "Playback Time",
        "data_type": "Float",
        "direction": "ms_to_bp",
        "description": "Current playback position: Engine-level query that returns the elapsed time. The internal Wave Player 'Playback Time' output can also be exposed as a graph output for MetaSounds-level time tracking.",
    },

    # =================================================================
    # Section 18: Blueprint -> Wwise (AkComponent / WAAPI)
    #
    # Blueprint communicates with Wwise through AkComponent functions
    # and UAkGameplayStatics. These drive Wwise event playback,
    # RTPC values, switch/state changes, and spatial positioning.
    # =================================================================

    {
        "bp_function": "AkComponent.PostEvent",
        "bp_pin": "AkEvent",
        "ms_node": "(wwise)",
        "ms_pin": "Event.Play",
        "data_type": "String",
        "direction": "bp_to_wwise",
        "description": "Posts a Wwise event by name or reference. The event executes its action list (Play, Stop, SetRTPC, etc.) on the target sound object. Primary entry point for all Wwise audio playback from Blueprint.",
    },
    {
        "bp_function": "AkComponent.PostEvent",
        "bp_pin": "CallbackMask",
        "ms_node": "(wwise)",
        "ms_pin": "Event.Callback",
        "data_type": "Int32",
        "direction": "bp_to_wwise",
        "description": "Bitmask specifying which Wwise callbacks to receive: EndOfEvent (1), Marker (4), Duration (8), MusicSync (16). Combined with OnEventCallback delegate to receive notifications during playback.",
    },
    {
        "bp_function": "AkComponent.SetRTPCValue",
        "bp_pin": "Value",
        "ms_node": "(wwise)",
        "ms_pin": "GameParameter",
        "data_type": "Float",
        "direction": "bp_to_wwise",
        "description": "Sets a Wwise Game Parameter (RTPC) value. Drives property curves on Wwise objects (volume, pitch, filter, effect wet/dry). Blueprint sends per-tick for continuous parameters like distance, speed, or health.",
    },
    {
        "bp_function": "AkComponent.SetRTPCValue",
        "bp_pin": "RTPC_Distance",
        "ms_node": "(wwise)",
        "ms_pin": "RTPC_Distance",
        "data_type": "Float",
        "direction": "bp_to_wwise",
        "description": "Common RTPC: listener-to-source distance (0-100 normalized). Drives low-pass filter and reverb send amount on weapon/foley sounds. Wwise attenuation curves map this to volume, LPF, and aux send levels.",
    },
    {
        "bp_function": "AkComponent.SetRTPCValue",
        "bp_pin": "RTPC_Speed",
        "ms_node": "(wwise)",
        "ms_pin": "RTPC_Speed",
        "data_type": "Float",
        "direction": "bp_to_wwise",
        "description": "Common RTPC: character movement speed (0-1 normalized). Drives footstep volume/pitch variation and wind intensity. Wwise pitch RTPC curve maps speed to pitch cents offset.",
    },
    {
        "bp_function": "AkComponent.SetRTPCValue",
        "bp_pin": "RTPC_Health",
        "ms_node": "(wwise)",
        "ms_pin": "RTPC_Health",
        "data_type": "Float",
        "direction": "bp_to_wwise",
        "description": "Common RTPC: player health percentage (0-100). At low health, Wwise applies low-pass filter on master bus, increases heartbeat volume, and modulates reverb for 'underwater' near-death effect.",
    },
    {
        "bp_function": "AkComponent.SetRTPCValue",
        "bp_pin": "RTPC_RPM",
        "ms_node": "(wwise)",
        "ms_pin": "RTPC_Vehicle_RPM",
        "data_type": "Float",
        "direction": "bp_to_wwise",
        "description": "Common RTPC: engine RPM (0-10000). Drives pitch on engine loops and crossfade between idle/mid/high RPM layers in BlendContainer. Blueprint reads from vehicle physics component per-tick.",
    },
    {
        "bp_function": "AkComponent.SetRTPCValue",
        "bp_pin": "RTPC_WindSpeed",
        "ms_node": "(wwise)",
        "ms_pin": "RTPC_Wind_Speed",
        "data_type": "Float",
        "direction": "bp_to_wwise",
        "description": "Common RTPC: wind speed (0-100). Drives wind noise layer volume and filter cutoff in ambient BlendContainer. Blueprint reads from weather subsystem or height-based calculation.",
    },
    {
        "bp_function": "AkComponent.SetRTPCValue",
        "bp_pin": "RTPC_WeatherIntensity",
        "ms_node": "(wwise)",
        "ms_pin": "RTPC_Weather_Intensity",
        "data_type": "Float",
        "direction": "bp_to_wwise",
        "description": "Common RTPC: weather severity (0-100). Drives rain/wind layer volumes in weather SwitchContainer. Blueprint sends per-tick during weather transitions for smooth interpolation.",
    },
    {
        "bp_function": "AkComponent.SetRTPCValue",
        "bp_pin": "RTPC_UIVolume",
        "ms_node": "(wwise)",
        "ms_pin": "RTPC_UI_Volume",
        "data_type": "Float",
        "direction": "bp_to_wwise",
        "description": "Common RTPC: UI volume from settings menu (0-100). Applied to UI bus volume via RTPC curve. Blueprint reads from game settings Save Game and applies on load.",
    },
    {
        "bp_function": "UAkGameplayStatics.SetSwitch",
        "bp_pin": "SwitchValue",
        "ms_node": "(wwise)",
        "ms_pin": "SwitchGroup.Value",
        "data_type": "String",
        "direction": "bp_to_wwise",
        "description": "Sets the active switch value on a Wwise SwitchGroup for a specific game object. SwitchContainers route to the matching child. Used for surface-type footsteps, weapon type selection, and character voice sets.",
    },
    {
        "bp_function": "UAkGameplayStatics.SetSwitch",
        "bp_pin": "Surface_Type",
        "ms_node": "(wwise)",
        "ms_pin": "SwitchGroup.Surface_Type",
        "data_type": "String",
        "direction": "bp_to_wwise",
        "description": "Footstep surface switch: Blueprint line-traces from character foot to ground, reads physical material, maps to switch value (Concrete/Wood/Grass/Metal/Gravel/Water). SwitchContainer routes to per-surface RandomSequenceContainer.",
    },
    {
        "bp_function": "UAkGameplayStatics.SetState",
        "bp_pin": "StateValue",
        "ms_node": "(wwise)",
        "ms_pin": "StateGroup.Value",
        "data_type": "String",
        "direction": "bp_to_wwise",
        "description": "Sets a global Wwise State value. States affect all subscribed objects simultaneously (unlike Switches which are per-game-object). Used for weather states, game phases (Menu/Gameplay/Pause), and environment zones.",
    },
    {
        "bp_function": "UAkGameplayStatics.SetState",
        "bp_pin": "Weather",
        "ms_node": "(wwise)",
        "ms_pin": "StateGroup.Weather",
        "data_type": "String",
        "direction": "bp_to_wwise",
        "description": "Weather state: Blueprint sets Weather StateGroup to Clear/Cloudy/LightRain/HeavyRain/Storm/Snow. Wwise SwitchContainer crossfades between per-state children (3s default transition). Affects all weather sounds globally.",
    },
    {
        "bp_function": "AkComponent.SetMultiplePositions",
        "bp_pin": "Positions",
        "ms_node": "(wwise)",
        "ms_pin": "3DPosition",
        "data_type": "Transform[]",
        "direction": "bp_to_wwise",
        "description": "Sets multiple emitter positions for a single Wwise game object. Used for large area emitters (river, highway) or objects with multiple sound-emitting points. MultiPositionType: SingleSource, MultiSources, or MultiDirections.",
    },
    {
        "bp_function": "UAkGameplayStatics.PostTrigger",
        "bp_pin": "TriggerName",
        "ms_node": "(wwise)",
        "ms_pin": "Trigger",
        "data_type": "String",
        "direction": "bp_to_wwise",
        "description": "Posts a Wwise Trigger by name. Triggers fire Stinger responses in Wwise Music segments (music system transitions). Also used for one-shot gameplay moments like turbo engage/disengage in vehicle audio.",
    },
    {
        "bp_function": "AkComponent.PostEvent",
        "bp_pin": "Stop_Event",
        "ms_node": "(wwise)",
        "ms_pin": "Event.Stop",
        "data_type": "String",
        "direction": "bp_to_wwise",
        "description": "Posts a Stop event to halt playback on a Wwise game object. The event's Stop action targets a specific sound object or all sounds on the game object. Used when player exits zones, weapons holstered, or vehicle engine off.",
    },
    {
        "bp_function": "AkComponent.SetOutputBusVolume",
        "bp_pin": "BusVolume",
        "ms_node": "(wwise)",
        "ms_pin": "Bus.Volume",
        "data_type": "Float",
        "direction": "bp_to_wwise",
        "description": "Sets the output bus volume for this AkComponent. Used to duck individual sound categories (weapons during dialogue, ambience during cutscenes). Value in linear scale (0-1).",
    },
    {
        "bp_function": "UAkGameplayStatics.SetBusConfig",
        "bp_pin": "BusName",
        "ms_node": "(wwise)",
        "ms_pin": "Bus.Config",
        "data_type": "String",
        "direction": "bp_to_wwise",
        "description": "Configures a Wwise bus speaker configuration at runtime. Used to switch between stereo/surround/Ambisonics output based on detected playback device. Rarely called, typically once at initialization.",
    },
    {
        "bp_function": "UAkGameplayStatics.PostEventAtLocation",
        "bp_pin": "Location",
        "ms_node": "(wwise)",
        "ms_pin": "Event.PlayAtLocation",
        "data_type": "Vector",
        "direction": "bp_to_wwise",
        "description": "Posts a Wwise event at a specific world location without a persistent game object. Fire-and-forget for explosions, impacts, and debris sounds. Wwise applies 3D spatialization based on the position.",
    },

    # =================================================================
    # Section 19: MetaSounds -> Wwise (AudioLink Bridge)
    #
    # AudioLink is UE5's one-way audio routing bridge from the native
    # audio engine (MetaSounds) into Wwise. Audio flows as a bus capture,
    # not as individual parameter values.
    # =================================================================

    {
        "bp_function": "(AudioLink: MetaSounds Output)",
        "bp_pin": "Out Left",
        "ms_node": "(audiolink)",
        "ms_pin": "AudioLink Bus Input",
        "data_type": "Audio",
        "direction": "ms_to_wwise",
        "description": "MetaSounds stereo left output routed through AudioLink into a Wwise bus. AudioLink captures the MetaSounds Source audio output and injects it into Wwise's mixing pipeline. Requires AudioLink plugin enabled in UE5 project settings.",
    },
    {
        "bp_function": "(AudioLink: MetaSounds Output)",
        "bp_pin": "Out Right",
        "ms_node": "(audiolink)",
        "ms_pin": "AudioLink Bus Input",
        "data_type": "Audio",
        "direction": "ms_to_wwise",
        "description": "MetaSounds stereo right output routed through AudioLink into Wwise. The left and right channels are captured together as a stereo pair into the assigned Wwise AudioLink bus.",
    },
    {
        "bp_function": "(AudioLink: Bus Routing)",
        "bp_pin": "AudioLink_Weapons",
        "ms_node": "(audiolink)",
        "ms_pin": "Wwise Bus: Weapons",
        "data_type": "Audio",
        "direction": "ms_to_wwise",
        "description": "Weapon MetaSounds Source output routed via AudioLink to Wwise Weapons bus. Wwise applies weapon-specific attenuation (logarithmic falloff), distance-based low-pass filter, and reverb send. MetaSounds handles the DSP synthesis, Wwise handles the mixing.",
    },
    {
        "bp_function": "(AudioLink: Bus Routing)",
        "bp_pin": "AudioLink_Ambience",
        "ms_node": "(audiolink)",
        "ms_pin": "Wwise Bus: Ambience",
        "data_type": "Audio",
        "direction": "ms_to_wwise",
        "description": "Ambient MetaSounds Source output routed via AudioLink to Wwise Ambience bus. Wwise BlendContainer RTPC curves control per-layer volumes while MetaSounds generates procedural ambient content (noise + filter + LFO).",
    },
    {
        "bp_function": "(AudioLink: Bus Routing)",
        "bp_pin": "AudioLink_Foley",
        "ms_node": "(audiolink)",
        "ms_pin": "Wwise Bus: Foley",
        "data_type": "Audio",
        "direction": "ms_to_wwise",
        "description": "Footstep/foley MetaSounds Source output routed via AudioLink to Wwise Foley bus. Wwise handles surface-based SwitchContainer routing and attenuation while MetaSounds runs per-step DSP (sample selection, AD envelope, filter).",
    },
    {
        "bp_function": "(AudioLink: Bus Routing)",
        "bp_pin": "AudioLink_UI",
        "ms_node": "(audiolink)",
        "ms_pin": "Wwise Bus: UI",
        "data_type": "Audio",
        "direction": "ms_to_wwise",
        "description": "UI MetaSounds Source output routed via AudioLink to Wwise UI bus. The UI bus has no 3D spatialization — clean direct-to-master output. Wwise handles volume via RTPC_UI_Volume curve.",
    },
    {
        "bp_function": "(AudioLink: Bus Routing)",
        "bp_pin": "AudioLink_Vehicles",
        "ms_node": "(audiolink)",
        "ms_pin": "Wwise Bus: Vehicles",
        "data_type": "Audio",
        "direction": "ms_to_wwise",
        "description": "Vehicle engine MetaSounds Source output routed via AudioLink to Wwise Vehicles bus. MetaSounds outputs the full engine mix (repulsor layers + compressed mono engine), Wwise applies RPM-driven pitch curves, attenuation, and environmental reverb.",
    },
    {
        "bp_function": "(AudioLink: Bus Routing)",
        "bp_pin": "AudioLink_Weather",
        "ms_node": "(audiolink)",
        "ms_pin": "Wwise Bus: Weather",
        "data_type": "Audio",
        "direction": "ms_to_wwise",
        "description": "Weather MetaSounds Source output routed via AudioLink to Wwise Weather bus. Wwise StateGroup manages crossfade transitions between weather states (3s default). MetaSounds generates procedural rain/wind/thunder DSP.",
    },
    {
        "bp_function": "(AudioLink: RTPC Bridge)",
        "bp_pin": "Graph Output Float",
        "ms_node": "(audiolink)",
        "ms_pin": "GameParameter (via Blueprint relay)",
        "data_type": "Float",
        "direction": "ms_to_wwise",
        "description": "MetaSounds graph Float output can drive a Wwise RTPC through a Blueprint relay: MS graph output -> BP OnAudioParameterChange delegate -> SetRTPCValue. No direct MS->Wwise parameter path exists. Used for analysis-driven mixing (envelope follower -> bus volume).",
    },
    {
        "bp_function": "(AudioLink: Submix Capture)",
        "bp_pin": "Submix Output",
        "ms_node": "(audiolink)",
        "ms_pin": "Wwise AuxBus",
        "data_type": "Audio",
        "direction": "ms_to_wwise",
        "description": "MetaSounds audio routed through UE5 submix can be captured by AudioLink into a Wwise auxiliary bus. Used for send-based effects where MetaSounds generates dry audio and Wwise applies reverb/delay via AuxBus routing.",
    },

    # =================================================================
    # Section 20: Wwise -> Blueprint (Callbacks and Notifications)
    #
    # Wwise sends event callbacks, markers, and state-change
    # notifications back to Blueprint through delegates and
    # callback functions on AkComponent and UAkGameplayStatics.
    # =================================================================

    {
        "bp_function": "AkComponent.OnEventCallback",
        "bp_pin": "EndOfEvent",
        "ms_node": "(wwise)",
        "ms_pin": "Event.EndOfEvent",
        "data_type": "Trigger",
        "direction": "wwise_to_bp",
        "description": "Wwise fires EndOfEvent callback when a posted event finishes all its actions. Blueprint receives this via OnEventCallback delegate with AkCallbackType::EndOfEvent. Used to chain sounds, spawn effects, or clean up game objects after audio completes.",
    },
    {
        "bp_function": "AkComponent.OnEventCallback",
        "bp_pin": "Marker",
        "ms_node": "(wwise)",
        "ms_pin": "Event.Marker",
        "data_type": "String",
        "direction": "wwise_to_bp",
        "description": "Wwise fires Marker callback when playback reaches a marker embedded in a WAV file. Blueprint receives marker label string via OnEventCallback. Used for lip-sync points, gameplay sync (hit frame, step frame), and subtitle timing.",
    },
    {
        "bp_function": "AkComponent.OnEventCallback",
        "bp_pin": "Duration",
        "ms_node": "(wwise)",
        "ms_pin": "Event.Duration",
        "data_type": "Float",
        "direction": "wwise_to_bp",
        "description": "Wwise fires Duration callback with the estimated duration in milliseconds when an event starts playing. Blueprint can use this to schedule visual effects, UI countdowns, or next-event timing without hardcoding durations.",
    },
    {
        "bp_function": "AkComponent.OnEventCallback",
        "bp_pin": "MusicSyncBeat",
        "ms_node": "(wwise)",
        "ms_pin": "MusicSync.Beat",
        "data_type": "Trigger",
        "direction": "wwise_to_bp",
        "description": "Wwise Interactive Music fires MusicSyncBeat callback on each musical beat. Blueprint receives beat notifications for rhythmic gameplay mechanics, visual beat indicators, or camera shake synced to music tempo.",
    },
    {
        "bp_function": "AkComponent.OnEventCallback",
        "bp_pin": "MusicSyncBar",
        "ms_node": "(wwise)",
        "ms_pin": "MusicSync.Bar",
        "data_type": "Trigger",
        "direction": "wwise_to_bp",
        "description": "Wwise Interactive Music fires MusicSyncBar callback at each bar boundary. Blueprint uses this for bar-level gameplay events (phase changes, intensity shifts). Less frequent than beat callbacks.",
    },
    {
        "bp_function": "AkComponent.OnEventCallback",
        "bp_pin": "MusicSyncEntry",
        "ms_node": "(wwise)",
        "ms_pin": "MusicSync.Entry",
        "data_type": "Trigger",
        "direction": "wwise_to_bp",
        "description": "Wwise fires MusicSyncEntry when a music segment begins playing. Blueprint uses this to trigger level events, change lighting, or start particle effects synchronized to music segment transitions.",
    },
    {
        "bp_function": "AkComponent.OnEventCallback",
        "bp_pin": "MusicSyncExit",
        "ms_node": "(wwise)",
        "ms_pin": "MusicSync.Exit",
        "data_type": "Trigger",
        "direction": "wwise_to_bp",
        "description": "Wwise fires MusicSyncExit when a music segment ends. Blueprint can clean up segment-specific effects, transition level state, or prepare for the next music section.",
    },
    {
        "bp_function": "AkComponent.OnEventCallback",
        "bp_pin": "Starvation",
        "ms_node": "(wwise)",
        "ms_pin": "Event.Starvation",
        "data_type": "Trigger",
        "direction": "wwise_to_bp",
        "description": "Wwise fires Starvation callback when a voice cannot be played due to voice limiting or virtual voice management. Blueprint can log this for audio debugging or trigger fallback behavior (e.g., reduce audio complexity).",
    },
    {
        "bp_function": "UAkGameplayStatics.OnStateChanged",
        "bp_pin": "NewState",
        "ms_node": "(wwise)",
        "ms_pin": "StateGroup.Changed",
        "data_type": "String",
        "direction": "wwise_to_bp",
        "description": "Wwise notifies Blueprint when a StateGroup value changes. Blueprint can react to state transitions initiated by other systems (e.g., Wwise Music state changes triggering gameplay effects, or verifying weather state was applied).",
    },
    {
        "bp_function": "AkComponent.GetPlayingID",
        "bp_pin": "PlayingID",
        "ms_node": "(wwise)",
        "ms_pin": "Event.PlayingID",
        "data_type": "Int32",
        "direction": "wwise_to_bp",
        "description": "Wwise returns a unique PlayingID when PostEvent is called. Blueprint stores this ID to later stop specific instances, set instance-specific RTPCs, or track which events are currently playing on a game object.",
    },
    {
        "bp_function": "AkComponent.OnEventCallback",
        "bp_pin": "MIDIEvent",
        "ms_node": "(wwise)",
        "ms_pin": "MIDI.NoteOn",
        "data_type": "Int32",
        "direction": "wwise_to_bp",
        "description": "Wwise fires MIDI callback when a MIDI event occurs in the Wwise Music system. Blueprint receives note-on/note-off with pitch and velocity for driving procedural visuals, haptics, or MetaSounds parameter changes synced to MIDI playback.",
    },
    {
        "bp_function": "AkComponent.OnEventCallback",
        "bp_pin": "EnableGetSourcePlayPosition",
        "ms_node": "(wwise)",
        "ms_pin": "Event.PlaybackPosition",
        "data_type": "Float",
        "direction": "wwise_to_bp",
        "description": "With EnableGetSourcePlayPosition flag, Blueprint can query current playback position of a playing Wwise event. Used for progress bars, timeline scrubbing UI, or syncing visual animations to audio playback position.",
    },
    {
        "bp_function": "UAkGameplayStatics.GetRTPCValue",
        "bp_pin": "ReturnValue",
        "ms_node": "(wwise)",
        "ms_pin": "GameParameter.CurrentValue",
        "data_type": "Float",
        "direction": "wwise_to_bp",
        "description": "Blueprint queries current value of a Wwise Game Parameter (RTPC). Returns the interpolated value accounting for Wwise-side smoothing. Used for debugging, HUD display of audio parameters, or driving non-audio systems from RTPC state.",
    },

]


# ===================================================================
# Convenience accessors
# ===================================================================

# All valid direction values
DIRECTIONS = frozenset({
    "bp_to_ms", "ms_to_bp",
    "bp_to_wwise", "ms_to_wwise", "wwise_to_bp",
})


def get_mappings_by_direction(direction: str) -> list[dict]:
    """Return mappings filtered by direction.

    Valid directions: bp_to_ms, ms_to_bp, bp_to_wwise, ms_to_wwise, wwise_to_bp.
    """
    return [m for m in PIN_MAPPINGS if m["direction"] == direction]


def get_mappings_by_data_type(data_type: str) -> list[dict]:
    """Return mappings filtered by data type (Float, Trigger, Int32, etc.)."""
    dt = data_type.lower()
    return [m for m in PIN_MAPPINGS if m["data_type"].lower() == dt]


def get_mappings_by_bp_function(func_name: str) -> list[dict]:
    """Return mappings for a specific Blueprint/Wwise function (substring match)."""
    fn = func_name.lower()
    return [m for m in PIN_MAPPINGS if fn in m["bp_function"].lower()]


def get_mappings_by_ms_pin(pin_name: str) -> list[dict]:
    """Return mappings for a specific MetaSounds/Wwise pin (exact match)."""
    return [m for m in PIN_MAPPINGS if m["ms_pin"] == pin_name]


def get_mappings_by_layer(layer: str) -> list[dict]:
    """Return mappings involving a specific layer: 'blueprint', 'metasounds', or 'wwise'.

    Matches any direction that includes the layer as source or target.
    """
    layer_lower = layer.lower()
    layer_directions = {
        "blueprint": {"bp_to_ms", "ms_to_bp", "bp_to_wwise", "wwise_to_bp"},
        "metasounds": {"bp_to_ms", "ms_to_bp", "ms_to_wwise"},
        "wwise": {"bp_to_wwise", "ms_to_wwise", "wwise_to_bp"},
    }
    dirs = layer_directions.get(layer_lower, set())
    return [m for m in PIN_MAPPINGS if m["direction"] in dirs]


def get_wwise_rtpc_mappings() -> list[dict]:
    """Return all Blueprint -> Wwise RTPC mappings."""
    return [m for m in PIN_MAPPINGS
            if m["direction"] == "bp_to_wwise"
            and "RTPC" in m.get("ms_pin", "")]


def search_mappings(query: str) -> list[dict]:
    """Substring search across all mapping fields."""
    q = query.lower()
    return [m for m in PIN_MAPPINGS
            if q in m["bp_function"].lower()
            or q in m["bp_pin"].lower()
            or q in m["ms_pin"].lower()
            or q in m["description"].lower()]
