"""MetaSounds node catalogue -- complete reference for graph generation.

Every node that the MCP server can place in a MetaSound graph is defined here
with its inputs, outputs, tags, and complexity rating.  The catalogue is the
single source of truth consumed by:
  - The Builder API bridge (graph spec -> UE5 C++ plugin)
  - The D1/Vectorize knowledge seeder (bulk upload)
  - The semantic search tool (tag + description matching)

All data sourced from research/research_metasounds_game_audio.md Section 2
and Epic's MetaSounds Function Nodes Reference Guide.
"""

from __future__ import annotations


# ===================================================================
# Helper type aliases (for readability only -- not enforced at runtime)
# ===================================================================
Pin = dict          # {"name": str, "type": str}
InputPin = dict     # {"name": str, "type": str, "required": bool, "default": ...}
NodeDef = dict      # full node definition


def _in(name: str, type_: str, *, required: bool = True, default: object = None) -> InputPin:
    """Build an input pin descriptor."""
    pin: InputPin = {"name": name, "type": type_, "required": required}
    if default is not None:
        pin["default"] = default
    return pin


def _out(name: str, type_: str) -> Pin:
    """Build an output pin descriptor."""
    return {"name": name, "type": type_}


def _node(
    name: str,
    category: str,
    description: str,
    inputs: list[InputPin],
    outputs: list[Pin],
    tags: list[str],
    complexity: int = 1,
) -> NodeDef:
    """Build a node definition dict."""
    return {
        "name": name,
        "category": category,
        "description": description,
        "inputs": inputs,
        "outputs": outputs,
        "tags": tags,
        "complexity": complexity,
    }


# ===================================================================
# METASOUND_NODES  --  keyed by node name, ~150 entries
# ===================================================================

METASOUND_NODES: dict[str, NodeDef] = {}


def _register(node: NodeDef) -> None:
    """Insert a node into the global catalogue."""
    METASOUND_NODES[node["name"]] = node


# -------------------------------------------------------------------
# Generators  (13 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Additive Synth", "Generators",
    "Generates audio from a bank of sine partials with controllable amplitudes.",
    [_in("Frequency", "Float", default=440.0),
     _in("Enabled", "Bool", default=True),
     _in("Partials", "Float[]", required=False)],
    [_out("Audio", "Audio")],
    ["oscillator", "additive", "synthesis", "harmonics", "partials"],
    complexity=3,
))

_register(_node(
    "Saw", "Generators",
    "Band-limited sawtooth oscillator.",
    [_in("Frequency", "Float", default=440.0),
     _in("Enabled", "Bool", default=True),
     _in("Glide Time", "Time", required=False, default=0.0)],
    [_out("Audio", "Audio")],
    ["oscillator", "sawtooth", "saw", "synthesis", "subtractive", "bright"],
    complexity=1,
))

_register(_node(
    "Sine", "Generators",
    "Pure sine wave oscillator.",
    [_in("Frequency", "Float", default=440.0),
     _in("Enabled", "Bool", default=True),
     _in("Glide Time", "Time", required=False, default=0.0)],
    [_out("Audio", "Audio")],
    ["oscillator", "sine", "synthesis", "pure", "tone", "fundamental"],
    complexity=1,
))

_register(_node(
    "Square", "Generators",
    "Band-limited square wave oscillator.",
    [_in("Frequency", "Float", default=440.0),
     _in("Enabled", "Bool", default=True),
     _in("Glide Time", "Time", required=False, default=0.0)],
    [_out("Audio", "Audio")],
    ["oscillator", "square", "synthesis", "hollow", "pulse"],
    complexity=1,
))

_register(_node(
    "Triangle", "Generators",
    "Band-limited triangle wave oscillator.",
    [_in("Frequency", "Float", default=440.0),
     _in("Enabled", "Bool", default=True),
     _in("Glide Time", "Time", required=False, default=0.0)],
    [_out("Audio", "Audio")],
    ["oscillator", "triangle", "synthesis", "mellow", "soft"],
    complexity=1,
))

_register(_node(
    "SuperOscillator", "Generators",
    "Multi-voice oscillator with waveform type selection, detuning, glide, and pulse-width control. "
    "Mono variant. Voices stacks unison voices with Detune spread. Entropy adds random per-voice drift. "
    "Blend crossfades between voices. Glide adds portamento between pitch changes. "
    "Limit Output prevents clipping when stacking many voices. Type: Saw/Square/Sine/Triangle. "
    "Best practice: send MIDI ints from Blueprint, convert to Hz with MIDI To Frequency inside MetaSounds.",
    [_in("Enabled", "Bool", default=True),
     _in("Limit Output", "Bool", default=True),
     _in("Voices", "Int32", required=False, default=16),
     _in("Frequency", "Float", default=440.0),
     _in("Modulation", "Audio", required=False),
     _in("Detune", "Float", required=False, default=-0.25),
     _in("Entropy", "Float", required=False, default=0.0),
     _in("Blend", "Float", required=False, default=0.0),
     _in("Glide", "Float", required=False, default=0.0),
     _in("PulseWidth", "Float", required=False, default=0.5),
     _in("Type", "Enum", default="Square")],
    [_out("Audio", "Audio")],
    ["oscillator", "super", "synthesis", "waveform", "morph", "pulse width",
     "unison", "detune", "voices", "glide", "pad", "synth"],
    complexity=3,
))

_register(_node(
    "WaveTable Oscillator", "Generators",
    "Oscillator that reads from a wavetable for arbitrary waveforms.",
    [_in("Frequency", "Float", default=440.0),
     _in("WaveTable", "UObject"),
     _in("WaveTableIndex", "Float", default=0.0),
     _in("Enabled", "Bool", default=True)],
    [_out("Audio", "Audio")],
    ["oscillator", "wavetable", "synthesis", "waveform"],
    complexity=3,
))

_register(_node(
    "WaveTable Player", "Generators",
    "Plays a wavetable at a given position for single-cycle waveform use.",
    [_in("Frequency", "Float", default=440.0),
     _in("WaveTable", "UObject"),
     _in("WaveTableIndex", "Float", default=0.0),
     _in("Enabled", "Bool", default=True)],
    [_out("Audio", "Audio")],
    ["wavetable", "player", "synthesis", "waveform"],
    complexity=2,
))

_register(_node(
    "Low Frequency Noise", "Generators",
    "Generates smooth random noise at low frequencies for organic modulation.",
    [_in("Frequency", "Float", default=1.0),
     _in("Seed", "Int32", required=False, default=-1)],
    [_out("Out", "Float")],
    ["noise", "modulation", "random", "organic", "drift", "lfo"],
    complexity=2,
))

_register(_node(
    "Low-Frequency Oscillator", "Generators",
    "LFO for modulation: sine, saw, square, triangle, sample-and-hold shapes.",
    [_in("Frequency", "Float", default=1.0),
     _in("Shape", "Enum", default="Sine"),
     _in("MinValue", "Float", default=-1.0),
     _in("MaxValue", "Float", default=1.0),
     _in("PhaseOffset", "Float", required=False, default=0.0)],
    [_out("Out", "Float")],
    ["lfo", "modulation", "tremolo", "vibrato", "wobble", "sweep"],
    complexity=2,
))

_register(_node(
    "Noise (Pink)", "Generators",
    "Pink noise generator (1/f spectrum, equal energy per octave).",
    [_in("Seed", "Int32", required=False, default=-1)],
    [_out("Audio", "Audio")],
    ["noise", "pink", "warm", "natural", "broadband"],
    complexity=1,
))

_register(_node(
    "Noise (White)", "Generators",
    "White noise generator (flat spectrum, equal energy per frequency).",
    [_in("Seed", "Int32", required=False, default=-1)],
    [_out("Audio", "Audio")],
    ["noise", "white", "bright", "hiss", "broadband"],
    complexity=1,
))

_register(_node(
    "Perlin Noise", "Generators",
    "Perlin-noise-based signal for smooth organic modulation.",
    [_in("Frequency", "Float", default=1.0),
     _in("Seed", "Int32", required=False, default=-1)],
    [_out("Out", "Float")],
    ["noise", "perlin", "organic", "modulation", "smooth", "procedural"],
    complexity=2,
))


# -------------------------------------------------------------------
# Wave Players  (7 nodes)
# -------------------------------------------------------------------

_WAVE_PLAYER_INPUTS: list[InputPin] = [
    _in("Play", "Trigger"),
    _in("Stop", "Trigger", required=False),
    _in("Wave Asset", "WaveAsset"),
    _in("Start Time", "Time", required=False, default=0.0),
    _in("Pitch Shift", "Float", required=False, default=0.0),
    _in("Loop", "Bool", default=False),
    _in("Loop Start", "Time", required=False, default=0.0),
    _in("Loop Duration", "Time", required=False, default=-1.0),
]

_WAVE_PLAYER_OUTPUTS_MONO: list[Pin] = [
    _out("Audio", "Audio"),
    _out("On Finished", "Trigger"),
    _out("On Looped", "Trigger"),
    _out("On Nearly Finished", "Trigger"),
]

_WAVE_PLAYER_OUTPUTS_STEREO: list[Pin] = [
    _out("Out Left", "Audio"),
    _out("Out Right", "Audio"),
    _out("On Play", "Trigger"),
    _out("On Finished", "Trigger"),
    _out("On Nearly Finished", "Trigger"),
    _out("On Looped", "Trigger"),
    _out("On Cue Point", "Trigger"),
    _out("Cue Point ID", "Int32"),
    _out("Cue Point Label", "String"),
    _out("Loop Ratio", "Float"),
    _out("Playback Location", "Float"),
    _out("Playback Time", "Time"),
]

for _ch, _desc, _outs, _cx in [
    ("Mono", "Mono wave file player with pitch shift, looping, and trigger outputs.",
     _WAVE_PLAYER_OUTPUTS_MONO, 1),
    ("Stereo", "Stereo wave file player with L/R outputs and looping.",
     _WAVE_PLAYER_OUTPUTS_STEREO, 1),
    ("Quad", "Quad (4-channel) wave file player.",
     [_out(f"Audio {i}", "Audio") for i in range(4)]
     + [_out("OnFinished", "Trigger"), _out("OnLooped", "Trigger"),
        _out("OnNearlyFinished", "Trigger")], 2),
    ("5.1", "5.1 surround wave file player.",
     [_out(f"Audio {ch}", "Audio") for ch in ("FL", "FR", "FC", "LFE", "SL", "SR")]
     + [_out("OnFinished", "Trigger"), _out("OnLooped", "Trigger"),
        _out("OnNearlyFinished", "Trigger")], 3),
    ("7.1", "7.1 surround wave file player.",
     [_out(f"Audio {ch}", "Audio") for ch in ("FL", "FR", "FC", "LFE", "SL", "SR", "BL", "BR")]
     + [_out("OnFinished", "Trigger"), _out("OnLooped", "Trigger"),
        _out("OnNearlyFinished", "Trigger")], 3),
]:
    _register(_node(
        f"Wave Player ({_ch})", "Wave Players", _desc,
        list(_WAVE_PLAYER_INPUTS), _outs,
        ["wave", "player", "sample", "playback", _ch.lower(), "loop"],
        complexity=_cx,
    ))

# Clean up loop variables
del _ch, _desc, _outs, _cx


# -------------------------------------------------------------------
# Envelopes  (8 nodes -- Audio and Float variants where applicable)
# -------------------------------------------------------------------

_register(_node(
    "AD Envelope", "Envelopes",
    "Attack-Decay envelope — real UE5 node name (no Audio/Float suffix in editor). "
    "Outputs audio-rate envelope signal. Real pin names from Chris Payne Sound Pads binary: "
    "On Trigger, Attack Time, Attack Curve, Decay Time, Decay Curve, Hard Reset, Looping → Out Envelope, On Done.",
    [_in("On Trigger", "Trigger"),
     _in("Attack Time", "Time", default=0.01),
     _in("Attack Curve", "Float", required=False, default=1.0),
     _in("Decay Time", "Time", default=0.1),
     _in("Decay Curve", "Float", required=False, default=1.0),
     _in("Hard Reset", "Bool", required=False, default=False),
     _in("Looping", "Bool", required=False, default=False)],
    [_out("Out Envelope", "Audio"),
     _out("On Done", "Trigger")],
    ["envelope", "AD", "attack", "decay", "percussive", "transient", "amplitude"],
    complexity=2,
))

_register(_node(
    "AD Envelope (Audio)", "Envelopes",
    "Attack-Decay envelope outputting audio-rate signal. "
    "Legacy pin names — use 'AD Envelope' for real UE5 pin names.",
    [_in("Trigger", "Trigger"),
     _in("Attack", "Time", default=0.01),
     _in("Decay", "Time", default=0.1),
     _in("AttackCurve", "Float", required=False, default=1.0),
     _in("DecayCurve", "Float", required=False, default=1.0)],
    [_out("Envelope", "Audio"),
     _out("OnDone", "Trigger")],
    ["envelope", "AD", "attack", "decay", "percussive", "transient", "amplitude"],
    complexity=2,
))

_register(_node(
    "AD Envelope (Float)", "Envelopes",
    "Attack-Decay envelope outputting block-rate float. "
    "Legacy pin names — use 'AD Envelope' for real UE5 pin names.",
    [_in("Trigger", "Trigger"),
     _in("Attack", "Time", default=0.01),
     _in("Decay", "Time", default=0.1),
     _in("AttackCurve", "Float", required=False, default=1.0),
     _in("DecayCurve", "Float", required=False, default=1.0)],
    [_out("Envelope", "Float"),
     _out("OnDone", "Trigger")],
    ["envelope", "AD", "attack", "decay", "percussive", "control"],
    complexity=2,
))

_register(_node(
    "ADSR Envelope (Audio)", "Envelopes",
    "Full ADSR envelope outputting audio-rate signal for sustained sounds.",
    [_in("Trigger", "Trigger"),
     _in("Attack", "Time", default=0.01),
     _in("Decay", "Time", default=0.1),
     _in("Sustain", "Float", default=0.7),
     _in("Release", "Time", default=0.2)],
    [_out("Envelope", "Audio"),
     _out("OnDone", "Trigger")],
    ["envelope", "ADSR", "attack", "decay", "sustain", "release", "amplitude", "gate"],
    complexity=2,
))

_register(_node(
    "ADSR Envelope (Float)", "Envelopes",
    "Full ADSR envelope outputting block-rate float.",
    [_in("Trigger", "Trigger"),
     _in("Attack", "Time", default=0.01),
     _in("Decay", "Time", default=0.1),
     _in("Sustain", "Float", default=0.7),
     _in("Release", "Time", default=0.2)],
    [_out("Envelope", "Float"),
     _out("OnDone", "Trigger")],
    ["envelope", "ADSR", "attack", "decay", "sustain", "release", "control"],
    complexity=2,
))

_register(_node(
    "Crossfade", "Envelopes",
    "Crossfade between two audio signals using a 0-1 control value.",
    [_in("Audio A", "Audio"),
     _in("Audio B", "Audio"),
     _in("Crossfade", "Float", default=0.5)],
    [_out("Audio", "Audio")],
    ["crossfade", "blend", "mix", "transition", "morph"],
    complexity=1,
))

_register(_node(
    "WaveTable Envelope", "Envelopes",
    "Envelope shaped by a wavetable for arbitrary envelope curves.",
    [_in("Trigger", "Trigger"),
     _in("WaveTable", "UObject"),
     _in("Duration", "Time", default=1.0),
     _in("Loop", "Bool", default=False)],
    [_out("Envelope", "Audio"),
     _out("OnDone", "Trigger")],
    ["envelope", "wavetable", "shape", "custom", "curve"],
    complexity=3,
))

_register(_node(
    "Evaluate WaveTable", "Envelopes",
    "Looks up a wavetable value at a given position (0-1).",
    [_in("WaveTable", "UObject"),
     _in("Position", "Float", default=0.0)],
    [_out("Value", "Float")],
    ["wavetable", "lookup", "evaluate", "curve", "position"],
    complexity=2,
))

_register(_node(
    "Envelope Follower", "Envelopes",
    "Tracks the amplitude envelope of an incoming audio signal.",
    [_in("Audio", "Audio"),
     _in("Attack", "Time", default=0.01),
     _in("Release", "Time", default=0.1)],
    [_out("Envelope", "Float")],
    ["envelope", "follower", "amplitude", "tracker", "dynamics", "sidechain"],
    complexity=2,
))


# -------------------------------------------------------------------
# Filters  (10 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Biquad Filter", "Filters",
    "Versatile second-order filter with selectable type (LPF, HPF, BPF, Notch, etc.).",
    [_in("Audio", "Audio"),
     _in("Cutoff Frequency", "Float", default=1000.0),
     _in("Bandwidth", "Float", default=1.0),
     _in("FilterType", "Enum", default="LPF"),
     _in("Gain dB", "Float", required=False, default=0.0)],
    [_out("Audio", "Audio")],
    ["filter", "biquad", "subtractive", "frequency", "EQ", "lowpass",
     "highpass", "bandpass", "notch", "underwater", "muffled"],
    complexity=2,
))

_register(_node(
    "Dynamic Filter", "Filters",
    "Biquad filter with audio-rate modulation of cutoff frequency.",
    [_in("Audio", "Audio"),
     _in("Cutoff Frequency", "Audio"),
     _in("Bandwidth", "Float", default=1.0),
     _in("FilterType", "Enum", default="LPF")],
    [_out("Audio", "Audio")],
    ["filter", "dynamic", "modulation", "sweep", "wah", "envelope filter"],
    complexity=3,
))

_register(_node(
    "Ladder Filter", "Filters",
    "Classic 4-pole ladder filter topology with resonance.",
    [_in("Audio", "Audio"),
     _in("Cutoff Frequency", "Float", default=1000.0),
     _in("Resonance", "Float", default=0.5),
     _in("FilterType", "Enum", default="LPF")],
    [_out("Audio", "Audio")],
    ["filter", "ladder", "moog", "resonance", "analog", "subtractive", "warm"],
    complexity=3,
))

_register(_node(
    "State Variable Filter", "Filters",
    "Simultaneous lowpass, highpass, bandpass, and notch outputs.",
    [_in("Audio", "Audio"),
     _in("Cutoff Frequency", "Float", default=1000.0),
     _in("Resonance", "Float", default=0.5)],
    [_out("Low Pass", "Audio"),
     _out("High Pass", "Audio"),
     _out("Band Pass", "Audio"),
     _out("Notch", "Audio")],
    ["filter", "SVF", "state variable", "multimode", "lowpass", "highpass",
     "bandpass", "notch"],
    complexity=3,
))

_register(_node(
    "One-Pole High Pass Filter", "Filters",
    "Simple first-order high-pass filter -- removes low frequencies.",
    [_in("Audio", "Audio"),
     _in("Cutoff Frequency", "Float", default=200.0)],
    [_out("Audio", "Audio")],
    ["filter", "highpass", "onepole", "simple", "rumble removal", "DC block"],
    complexity=1,
))

_register(_node(
    "One-Pole Low Pass Filter", "Filters",
    "Simple first-order low-pass filter -- removes high frequencies.",
    [_in("Audio", "Audio"),
     _in("Cutoff Frequency", "Float", default=5000.0)],
    [_out("Audio", "Audio")],
    ["filter", "lowpass", "onepole", "simple", "muffled", "distance",
     "underwater", "warm"],
    complexity=1,
))

_register(_node(
    "Sample And Hold", "Filters",
    "Samples the input signal value when triggered and holds it until next trigger.",
    [_in("Value", "Float"),
     _in("Trigger", "Trigger")],
    [_out("Value", "Float")],
    ["sample", "hold", "trigger", "quantize", "step"],
    complexity=1,
))

_register(_node(
    "Bitcrusher", "Filters",
    "Reduces bit depth and/or sample rate for lo-fi distortion effects.",
    [_in("Audio", "Audio"),
     _in("BitDepth", "Int32", default=8),
     _in("SampleRateCrush", "Float", default=8000.0)],
    [_out("Audio", "Audio")],
    ["distortion", "lofi", "retro", "8bit", "bitcrusher", "crush", "chiptune"],
    complexity=2,
))

_register(_node(
    "Mono Band Splitter", "Filters",
    "Splits mono audio into low, mid, and high frequency bands.",
    [_in("Audio", "Audio"),
     _in("Low Crossover", "Float", default=250.0),
     _in("High Crossover", "Float", default=4000.0)],
    [_out("Low", "Audio"),
     _out("Mid", "Audio"),
     _out("High", "Audio")],
    ["filter", "crossover", "band splitter", "multiband", "EQ"],
    complexity=2,
))

_register(_node(
    "Stereo Band Splitter", "Filters",
    "Splits stereo audio into low, mid, and high frequency bands (L+R pairs).",
    [_in("Audio L", "Audio"),
     _in("Audio R", "Audio"),
     _in("Low Crossover", "Float", default=250.0),
     _in("High Crossover", "Float", default=4000.0)],
    [_out("Low L", "Audio"), _out("Low R", "Audio"),
     _out("Mid L", "Audio"), _out("Mid R", "Audio"),
     _out("High L", "Audio"), _out("High R", "Audio")],
    ["filter", "crossover", "band splitter", "stereo", "multiband", "EQ"],
    complexity=3,
))


# -------------------------------------------------------------------
# Delays  (5 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Delay", "Delays",
    "Mono delay line with dry/wet mix.",
    [_in("Audio", "Audio"),
     _in("DelayTime", "Time", default=0.25),
     _in("DryLevel", "Float", default=1.0),
     _in("WetLevel", "Float", default=0.5),
     _in("Feedback", "Float", required=False, default=0.3)],
    [_out("Audio", "Audio")],
    ["delay", "echo", "time", "repeat", "feedback"],
    complexity=2,
))

_register(_node(
    "Stereo Delay", "Delays",
    "Stereo delay with independent L/R delay times and feedback.",
    [_in("Audio L", "Audio"),
     _in("Audio R", "Audio"),
     _in("DelayTime L", "Time", default=0.25),
     _in("DelayTime R", "Time", default=0.375),
     _in("DryLevel", "Float", default=1.0),
     _in("WetLevel", "Float", default=0.5),
     _in("Feedback", "Float", required=False, default=0.3)],
    [_out("Audio L", "Audio"),
     _out("Audio R", "Audio")],
    ["delay", "stereo", "echo", "ping pong", "time", "spatial"],
    complexity=3,
))

_register(_node(
    "Delay Pitch Shift", "Delays",
    "Pitch shifting via delay line manipulation (granular pitch shift).",
    [_in("Audio", "Audio"),
     _in("PitchShift", "Float", default=0.0),
     _in("DelayTime", "Time", required=False, default=0.1)],
    [_out("Audio", "Audio")],
    ["delay", "pitch", "shift", "transpose", "detune"],
    complexity=3,
))

_register(_node(
    "Diffuser", "Delays",
    "Multi-tap diffusion network for reverb-like smearing of transients.",
    [_in("Audio", "Audio"),
     _in("Density", "Float", default=0.5),
     _in("Duration", "Time", default=0.5)],
    [_out("Audio", "Audio")],
    ["diffuser", "reverb", "smear", "space", "diffusion", "ambience"],
    complexity=3,
))

_register(_node(
    "Plate Reverb", "Delays",
    "Plate reverb effect — simulates metal plate vibration for dense, smooth reverb tails. "
    "From TechAudioTools SFX Generator (Eric Buchholz). Used as one of three parallel temporal effects "
    "(Delay + Flanger + Plate Reverb) in the send effects section.",
    [_in("Audio", "Audio"),
     _in("Damping", "Float", default=0.5),
     _in("Decay", "Float", default=0.5),
     _in("DryWet", "Float", required=False, default=0.5),
     _in("PreDelay", "Time", required=False, default=0.02)],
    [_out("Audio", "Audio")],
    ["reverb", "plate", "space", "ambience", "tail", "dense", "smooth", "room"],
    complexity=3,
))

_register(_node(
    "Grain Delay", "Delays",
    "Granular delay with grain size, density, and pitch shift controls.",
    [_in("Audio", "Audio"),
     _in("GrainSize", "Time", default=0.05),
     _in("GrainDensity", "Float", default=0.5),
     _in("PitchShift", "Float", default=0.0),
     _in("DelayTime", "Time", default=0.25),
     _in("Feedback", "Float", required=False, default=0.3)],
    [_out("Audio", "Audio")],
    ["granular", "delay", "grain", "texture", "freeze", "glitch"],
    complexity=4,
))


# -------------------------------------------------------------------
# Dynamics  (4 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Compressor", "Dynamics",
    "Dynamic range compressor with threshold/ratio/knee, parallel mix (Wet/Dry), "
    "optional analog modeling, peak/RMS envelope modes, and upwards compression. "
    "At 30:1 ratio with low threshold acts as brick-wall limiter for vehicle/engine layers.",
    [_in("Bypass", "Bool", required=False, default=False),
     _in("Audio", "Audio"),
     _in("Ratio", "Float", default=4.0),
     _in("Threshold dB", "Float", default=-20.0),
     _in("Attack Time", "Time", default=0.01),
     _in("Release Time", "Time", default=0.1),
     _in("Lookahead Time", "Time", required=False, default=0.01),
     _in("Knee", "Float", required=False, default=6.0),
     _in("Sidechain", "Audio", required=False),
     _in("Envelope Mode", "Enum", required=False, default="Peak"),
     _in("Analog Mode", "Bool", required=False, default=False),
     _in("Upwards Mode", "Bool", required=False, default=False),
     _in("Wet/Dry", "Float", required=False, default=1.0)],
    [_out("Audio", "Audio"),
     _out("Gain Envelope", "Float")],
    ["compressor", "dynamics", "loudness", "squeeze", "punch", "sidechain",
     "parallel", "limiter", "vehicle", "engine"],
    complexity=3,
))

_register(_node(
    "Limiter", "Dynamics",
    "Hard limiter / brick-wall limiter preventing signal from exceeding threshold.",
    [_in("Audio", "Audio"),
     _in("Threshold", "Float", default=-1.0),
     _in("Release", "Time", required=False, default=0.05)],
    [_out("Audio", "Audio")],
    ["limiter", "dynamics", "ceiling", "clip", "protect"],
    complexity=2,
))

_register(_node(
    "Decibels to Linear Gain", "Dynamics",
    "Converts a decibel value to a linear gain multiplier.",
    [_in("dB", "Float", default=0.0)],
    [_out("Linear Gain", "Float")],
    ["convert", "dB", "linear", "gain", "volume"],
    complexity=1,
))

_register(_node(
    "Linear Gain to Decibels", "Dynamics",
    "Converts a linear gain multiplier to decibel value.",
    [_in("Linear Gain", "Float", default=1.0)],
    [_out("dB", "Float")],
    ["convert", "linear", "dB", "gain", "volume"],
    complexity=1,
))


# -------------------------------------------------------------------
# Triggers  (13 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Trigger Accumulate", "Triggers",
    "Counts incoming triggers and fires output when count reaches threshold.",
    [_in("Trigger", "Trigger"),
     _in("Threshold", "Int32", default=4),
     _in("Reset", "Trigger", required=False)],
    [_out("Trigger", "Trigger"),
     _out("Count", "Int32")],
    ["trigger", "count", "accumulate", "threshold", "gate"],
    complexity=2,
))

_register(_node(
    "Trigger Any", "Triggers",
    "Fires output when any of its input triggers fire.",
    [_in("Trigger 0", "Trigger"),
     _in("Trigger 1", "Trigger"),
     _in("Trigger 2", "Trigger", required=False),
     _in("Trigger 3", "Trigger", required=False)],
    [_out("Trigger", "Trigger")],
    ["trigger", "any", "or", "combine", "merge"],
    complexity=1,
))

_register(_node(
    "Trigger Compare", "Triggers",
    "Compares a float value to a threshold and fires trigger when condition is met.",
    [_in("Value", "Float"),
     _in("Threshold", "Float", default=0.5),
     _in("CompareOp", "Enum", default="GreaterThan")],
    [_out("Trigger", "Trigger")],
    ["trigger", "compare", "threshold", "condition", "gate"],
    complexity=2,
))

_register(_node(
    "Trigger Compare (Int32)", "Triggers",
    "Compares two Int32 values when triggered and fires True or False. Used for room/state selection.",
    [_in("Compare", "Trigger"),
     _in("A", "Int32"),
     _in("B", "Int32", default=0),
     _in("Type", "Enum", default="Equals")],
    [_out("True", "Trigger"),
     _out("False", "Trigger")],
    ["trigger", "compare", "int32", "equals", "switch", "condition", "gate"],
    complexity=2,
))

_register(_node(
    "Trigger Control", "Triggers",
    "Gates or enables trigger flow based on a boolean control input.",
    [_in("Trigger", "Trigger"),
     _in("Enabled", "Bool", default=True)],
    [_out("Trigger", "Trigger")],
    ["trigger", "gate", "control", "enable", "disable"],
    complexity=1,
))

_register(_node(
    "Trigger Counter", "Triggers",
    "Counts triggers up or down and exposes the current count.",
    [_in("Trigger Up", "Trigger"),
     _in("Trigger Down", "Trigger", required=False),
     _in("Reset", "Trigger", required=False),
     _in("ResetCount", "Int32", required=False, default=0)],
    [_out("Count", "Int32"),
     _out("Trigger", "Trigger")],
    ["trigger", "counter", "count", "increment", "decrement"],
    complexity=2,
))

_register(_node(
    "Trigger Delay", "Triggers",
    "Delays a trigger by a specified time duration.",
    [_in("Trigger", "Trigger"),
     _in("DelayTime", "Time", default=0.5),
     _in("Reset", "Trigger", required=False)],
    [_out("Trigger", "Trigger")],
    ["trigger", "delay", "time", "postpone", "wait"],
    complexity=1,
))

_register(_node(
    "Trigger Filter", "Triggers",
    "Passes or blocks triggers based on a boolean gate signal.",
    [_in("Trigger", "Trigger"),
     _in("Gate", "Bool", default=True)],
    [_out("Trigger", "Trigger")],
    ["trigger", "filter", "gate", "pass", "block"],
    complexity=1,
))

_register(_node(
    "Trigger Once", "Triggers",
    "Fires only on the first incoming trigger, ignores all subsequent ones.",
    [_in("Trigger", "Trigger"),
     _in("Reset", "Trigger", required=False)],
    [_out("Trigger", "Trigger")],
    ["trigger", "once", "oneshot", "first", "single"],
    complexity=1,
))

_register(_node(
    "Trigger On Threshold", "Triggers",
    "Fires trigger when a float value crosses a threshold (rising or falling).",
    [_in("Value", "Float"),
     _in("Threshold", "Float", default=0.5),
     _in("Direction", "Enum", default="Rising")],
    [_out("Trigger", "Trigger")],
    ["trigger", "threshold", "crossing", "edge", "detect"],
    complexity=2,
))

_register(_node(
    "Trigger On Value Change", "Triggers",
    "Fires trigger whenever the input value changes.",
    [_in("Value", "Float")],
    [_out("Trigger", "Trigger"),
     _out("Previous Value", "Float")],
    ["trigger", "change", "detect", "watch", "monitor"],
    complexity=1,
))

_register(_node(
    "Trigger Pipe", "Triggers",
    "Passes trigger through unchanged -- useful for debugging and routing.",
    [_in("Trigger", "Trigger")],
    [_out("Trigger", "Trigger")],
    ["trigger", "pipe", "passthrough", "debug", "routing"],
    complexity=1,
))

_register(_node(
    "Trigger Repeat", "Triggers",
    "Repeats trigger at a regular interval (periodic timer).",
    [_in("Start", "Trigger"),
     _in("Stop", "Trigger", required=False),
     _in("Period", "Time", default=0.5),
     _in("Enabled", "Bool", default=True)],
    [_out("Trigger", "Trigger"),
     _out("Count", "Int32")],
    ["trigger", "repeat", "timer", "periodic", "interval", "clock", "metronome"],
    complexity=2,
))

_register(_node(
    "Trigger Sequence", "Triggers",
    "Fires output triggers in sequential round-robin order (0, 1, 2, ...). "
    "When Loop is enabled, wraps back to Out 0 after the last output. "
    "Used for cycling through weapon shot layers.",
    [_in("In", "Trigger"),
     _in("Reset", "Trigger", required=False),
     _in("Loop", "Bool", required=False, default=False)],
    [_out("Out 0", "Trigger"),
     _out("Out 1", "Trigger"),
     _out("Out 2", "Trigger")],
    ["trigger", "sequence", "round-robin", "order", "cycle", "step", "rotate"],
    complexity=2,
))

_register(_node(
    "Trigger Route", "Triggers",
    "Routes trigger to one of N outputs based on an integer index.",
    [_in("Trigger", "Trigger"),
     _in("Index", "Int32", default=0),
     _in("NumOutputs", "Int32", default=2)],
    [_out("Trigger 0", "Trigger"),
     _out("Trigger 1", "Trigger"),
     _out("Trigger 2", "Trigger"),
     _out("Trigger 3", "Trigger")],
    ["trigger", "route", "switch", "select", "branch", "demux"],
    complexity=2,
))


# -------------------------------------------------------------------
# Arrays  (7 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Array Get", "Arrays",
    "Gets an element from an array at the specified index.",
    [_in("Array", "Float[]"),
     _in("Index", "Int32", default=0)],
    [_out("Value", "Float")],
    ["array", "get", "index", "access", "element"],
    complexity=1,
))

_register(_node(
    "Array Set", "Arrays",
    "Sets an element in an array at the specified index.",
    [_in("Array", "Float[]"),
     _in("Index", "Int32", default=0),
     _in("Value", "Float")],
    [_out("Array", "Float[]")],
    ["array", "set", "index", "modify", "element"],
    complexity=1,
))

_register(_node(
    "Array Num", "Arrays",
    "Returns the number of elements in an array.",
    [_in("Array", "Float[]")],
    [_out("Num", "Int32")],
    ["array", "count", "length", "size", "num"],
    complexity=1,
))

_register(_node(
    "Random Get (WaveAssetArray)", "Arrays",
    "Gets a random element from a WaveAsset array, optionally weighted. "
    "No Repeats prevents consecutive duplicates. Enable Shared State syncs across instances.",
    [_in("Next", "Trigger"),
     _in("Reset", "Trigger", required=False),
     _in("In Array", "WaveAsset[]"),
     _in("Weights", "Float[]", required=False),
     _in("Seed", "Int32", required=False, default=-1),
     _in("No Repeats", "Int32", required=False, default=1),
     _in("Enable Shared State", "Bool", required=False, default=False)],
    [_out("On Next", "Trigger"),
     _out("On Reset", "Trigger"),
     _out("Value", "WaveAsset")],
    ["array", "random", "get", "variation", "selection", "weighted", "no-repeat"],
    complexity=2,
))

_register(_node(
    "Array Shuffle", "Arrays",
    "Returns array elements in random order without repeats until exhausted.",
    [_in("Trigger", "Trigger"),
     _in("Array", "WaveAsset[]"),
     _in("Seed", "Int32", required=False, default=-1),
     _in("AutoReset", "Bool", required=False, default=True)],
    [_out("Value", "WaveAsset"),
     _out("Index", "Int32"),
     _out("Trigger", "Trigger")],
    ["array", "shuffle", "random", "no-repeat", "variation", "round-robin"],
    complexity=2,
))

_register(_node(
    "Array Concatenate", "Arrays",
    "Concatenates two arrays into one.",
    [_in("Array A", "Float[]"),
     _in("Array B", "Float[]")],
    [_out("Array", "Float[]")],
    ["array", "concatenate", "join", "merge", "combine", "append"],
    complexity=1,
))

_register(_node(
    "Array Subset", "Arrays",
    "Extracts a contiguous subset of elements from an array.",
    [_in("Array", "Float[]"),
     _in("Start Index", "Int32", default=0),
     _in("Count", "Int32", default=1)],
    [_out("Array", "Float[]")],
    ["array", "subset", "slice", "range", "sub"],
    complexity=1,
))


# -------------------------------------------------------------------
# Math  (15 nodes)
# -------------------------------------------------------------------

# Arithmetic operators -- support Float, Audio, and Int32 variants
for _op, _symbol, _desc in [
    ("Add", "+", "Adds two values (Float, Audio, or Int32)."),
    ("Subtract", "-", "Subtracts second value from first."),
    ("Multiply", "*", "Multiplies two values (commonly used for amplitude modulation)."),
    ("Divide", "/", "Divides first value by second."),
]:
    for _type in ("Float", "Audio", "Int32"):
        _suffix = f" ({_type})" if _type != "Float" else ""
        _register(_node(
            f"{_op}{_suffix}", "Math",
            f"{_desc} Operates on {_type} data.",
            [_in("A", _type), _in("B", _type, default=1 if _op == "Multiply" else 0)],
            [_out("Result", _type)],
            ["math", _op.lower(), _symbol, "arithmetic", _type.lower()],
            complexity=1,
        ))

del _op, _symbol, _desc, _type, _suffix

# Unary / utility math
_register(_node(
    "Abs", "Math",
    "Returns the absolute value of a float.",
    [_in("Value", "Float")],
    [_out("Result", "Float")],
    ["math", "abs", "absolute", "magnitude"],
    complexity=1,
))

_register(_node(
    "Clamp", "Math",
    "Clamps a float value between min and max bounds.",
    [_in("Value", "Float"),
     _in("Min", "Float", default=0.0),
     _in("Max", "Float", default=1.0)],
    [_out("Result", "Float")],
    ["math", "clamp", "limit", "bound", "constrain"],
    complexity=1,
))

_register(_node(
    "Log", "Math",
    "Computes the natural logarithm of a float.",
    [_in("Value", "Float")],
    [_out("Result", "Float")],
    ["math", "log", "logarithm", "natural"],
    complexity=1,
))

_register(_node(
    "Power", "Math",
    "Raises base to the power of exponent.",
    [_in("Base", "Float"),
     _in("Exponent", "Float", default=2.0)],
    [_out("Result", "Float")],
    ["math", "power", "exponent", "pow", "square"],
    complexity=1,
))

_register(_node(
    "Modulo", "Math",
    "Returns the remainder of dividing A by B.",
    [_in("A", "Float"),
     _in("B", "Float", default=1.0)],
    [_out("Result", "Float")],
    ["math", "modulo", "remainder", "mod", "wrap"],
    complexity=1,
))

_register(_node(
    "Map Range", "Math",
    "Remaps a float from one range to another (linear interpolation).",
    [_in("Value", "Float"),
     _in("InMin", "Float", default=0.0),
     _in("InMax", "Float", default=1.0),
     _in("OutMin", "Float", default=0.0),
     _in("OutMax", "Float", default=100.0),
     _in("Clamped", "Bool", required=False, default=True)],
    [_out("Result", "Float")],
    ["math", "map", "range", "rescale", "normalize", "remap", "lerp"],
    complexity=1,
))

_register(_node(
    "Float Compare", "Math",
    "Compares two float values and outputs a boolean. CompareOp: LessThan, GreaterThan, Equals, LessThanOrEqual, GreaterThanOrEqual.",
    [_in("A", "Float"),
     _in("B", "Float"),
     _in("CompareOp", "Enum", default="LessThan")],
    [_out("Result", "Bool")],
    ["math", "compare", "less", "greater", "equals", "condition", "boolean"],
    complexity=1,
))

_register(_node(
    "Min", "Math",
    "Returns the smaller of two float values.",
    [_in("A", "Float"), _in("B", "Float")],
    [_out("Result", "Float")],
    ["math", "min", "minimum", "compare", "smaller"],
    complexity=1,
))

_register(_node(
    "Max", "Math",
    "Returns the larger of two float values.",
    [_in("A", "Float"), _in("B", "Float")],
    [_out("Result", "Float")],
    ["math", "max", "maximum", "compare", "larger"],
    complexity=1,
))

_register(_node(
    "Filter Q To Bandwidth", "Math",
    "Converts filter Q factor to bandwidth value (octaves).",
    [_in("Q", "Float", default=0.707)],
    [_out("Bandwidth", "Float")],
    ["math", "convert", "Q", "bandwidth", "filter"],
    complexity=1,
))

_register(_node(
    "Linear To Log Frequency", "Math",
    "Converts a linear frequency value to logarithmic scale.",
    [_in("Linear Frequency", "Float")],
    [_out("Log Frequency", "Float")],
    ["math", "convert", "frequency", "linear", "log", "scale"],
    complexity=1,
))

_register(_node(
    "InterpTo", "Math",
    "Smoothly interpolates from current value toward target at a given speed.",
    [_in("Current", "Float"),
     _in("Target", "Float"),
     _in("Speed", "Float", default=5.0),
     _in("DeltaTime", "Float", required=False)],
    [_out("Result", "Float")],
    ["math", "smooth", "interpolation", "transition", "lerp", "glide", "ease"],
    complexity=2,
))


# -------------------------------------------------------------------
# Mix  (2 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Mono Mixer", "Mix",
    "Mixes N mono audio inputs into a single mono output with per-input gain. "
    "Real UE5 pin names: In 0..N, Gain 0..N (Lin), Out.",
    [_in("In 0", "Audio"),
     _in("Gain 0", "Float", default=1.0),
     _in("In 1", "Audio", required=False),
     _in("Gain 1", "Float", required=False, default=1.0),
     _in("In 2", "Audio", required=False),
     _in("Gain 2", "Float", required=False, default=1.0),
     _in("In 3", "Audio", required=False),
     _in("Gain 3", "Float", required=False, default=1.0)],
    [_out("Out", "Audio")],
    ["mix", "mixer", "mono", "sum", "combine", "bus"],
    complexity=1,
))

_register(_node(
    "Audio Mixer (Stereo, 2)", "Mix",
    "2-input stereo mixer — real UE5 node name. Mixes two stereo pairs with per-input gain. "
    "Pin names use 'In N L/R' format. From Chris Payne Sound Pads project binary extraction.",
    [_in("In 0 L", "Audio"), _in("In 0 R", "Audio"),
     _in("Gain 0", "Float", default=1.0),
     _in("In 1 L", "Audio", required=False), _in("In 1 R", "Audio", required=False),
     _in("Gain 1", "Float", required=False, default=1.0)],
    [_out("Out L", "Audio"),
     _out("Out R", "Audio")],
    ["mix", "mixer", "stereo", "sum", "combine", "audio mixer"],
    complexity=2,
))

_register(_node(
    "Stereo Mixer", "Mix",
    "Mixes N stereo audio input pairs into a single stereo output with per-input gain. "
    "Real UE5 pin names: In N L/R, Gain N (Lin), Out L/R. "
    "Variant suffix (N) sets input count: Stereo Mixer (2), (3), (4), (8).",
    [_in("In 0 L", "Audio"), _in("In 0 R", "Audio"),
     _in("Gain 0", "Float", default=1.0),
     _in("In 1 L", "Audio", required=False), _in("In 1 R", "Audio", required=False),
     _in("Gain 1", "Float", required=False, default=1.0),
     _in("In 2 L", "Audio", required=False), _in("In 2 R", "Audio", required=False),
     _in("Gain 2", "Float", required=False, default=1.0),
     _in("In 3 L", "Audio", required=False), _in("In 3 R", "Audio", required=False),
     _in("Gain 3", "Float", required=False, default=1.0)],
    [_out("Out L", "Audio"),
     _out("Out R", "Audio")],
    ["mix", "mixer", "stereo", "sum", "combine", "bus"],
    complexity=2,
))


# -------------------------------------------------------------------
# Spatialization  (3 nodes)
# -------------------------------------------------------------------

_register(_node(
    "ITD Panner", "Spatialization",
    "Interaural Time Difference panner for binaural 3D audio on headphones.",
    [_in("Audio", "Audio"),
     _in("Azimuth", "Float", default=0.0),
     _in("Elevation", "Float", required=False, default=0.0),
     _in("Distance", "Float", required=False, default=1.0)],
    [_out("Audio L", "Audio"),
     _out("Audio R", "Audio")],
    ["spatial", "3d", "binaural", "HRTF", "headphones", "panner", "ITD",
     "azimuth", "elevation"],
    complexity=3,
))

_register(_node(
    "Stereo Panner", "Spatialization",
    "Simple stereo pan from left (-1) to right (+1) for speaker output.",
    [_in("Audio", "Audio"),
     _in("Pan", "Float", default=0.0)],
    [_out("Audio L", "Audio"),
     _out("Audio R", "Audio")],
    ["spatial", "pan", "stereo", "speakers", "left", "right", "balance"],
    complexity=1,
))

_register(_node(
    "MSP_HeightEQ_Node", "Spatialization",
    "Height-based EQ for 3D spatialization. Applies frequency shaping based on "
    "azimuth and elevation angles for realistic height perception. From Craig Owen tutorial.",
    [_in("Audio", "Audio"),
     _in("UE.Spatialization.Azimuth", "Float", required=False, default=0.0),
     _in("UE.Spatialization.Elevation", "Float")],
    [_out("Output", "Audio")],
    ["spatial", "height", "EQ", "3d", "binaural", "azimuth", "elevation",
     "spatialization", "HRTF"],
    complexity=2,
))

_register(_node(
    "Mid-Side Encode/Decode", "Spatialization",
    "Converts between stereo L/R and mid/side representation for width control.",
    [_in("Audio L", "Audio"),
     _in("Audio R", "Audio"),
     _in("Mode", "Enum", default="Encode"),
     _in("Width", "Float", required=False, default=1.0)],
    [_out("Out A", "Audio"),
     _out("Out B", "Audio")],
    ["stereo", "width", "mid", "side", "encode", "decode", "spatial", "image"],
    complexity=2,
))


# -------------------------------------------------------------------
# Music  (5 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Frequency To MIDI", "Music",
    "Converts a frequency in Hz to a MIDI note number.",
    [_in("Frequency", "Float", default=440.0)],
    [_out("MIDI Note", "Float")],
    ["music", "frequency", "MIDI", "convert", "note", "pitch"],
    complexity=1,
))

_register(_node(
    "MIDI To Frequency", "Music",
    "Converts a MIDI note number (Int32) to frequency in Hz (Float). "
    "Real pin names from binary: MIDI In → Out Frequency. "
    "Best practice: send MIDI ints from Blueprint, convert to Hz here inside MetaSounds.",
    [_in("MIDI In", "Int32", default=69)],
    [_out("Out Frequency", "Float")],
    ["music", "MIDI", "frequency", "convert", "note", "pitch", "Hz"],
    complexity=1,
))

_register(_node(
    "MIDI Note Quantizer", "Music",
    "Quantizes a MIDI note number to the nearest note in a given scale.",
    [_in("MIDI Note", "Float"),
     _in("Scale", "Enum", default="Chromatic"),
     _in("Root Note", "Int32", required=False, default=0)],
    [_out("Quantized Note", "Float")],
    ["music", "MIDI", "quantize", "scale", "snap", "tuning"],
    complexity=2,
))

_register(_node(
    "Scale to Note Array", "Music",
    "Generates an array of MIDI note numbers or frequencies for a musical scale.",
    [_in("Scale", "Enum", default="Major"),
     _in("Root Note", "Int32", default=60),
     _in("NumOctaves", "Int32", required=False, default=1)],
    [_out("Notes", "Float[]")],
    ["music", "scale", "notes", "array", "melody", "chord"],
    complexity=2,
))

_register(_node(
    "BPM To Seconds", "Music",
    "Converts beats per minute to a time duration per beat in seconds.",
    [_in("BPM", "Float", default=120.0)],
    [_out("Seconds", "Time")],
    ["music", "BPM", "tempo", "beat", "time", "clock", "rhythm"],
    complexity=1,
))


# -------------------------------------------------------------------
# Random  (4 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Random Bool", "Random",
    "Generates a random boolean value when triggered.",
    [_in("Trigger", "Trigger"),
     _in("Probability", "Float", required=False, default=0.5),
     _in("Seed", "Int32", required=False, default=-1)],
    [_out("Value", "Bool"),
     _out("Trigger", "Trigger")],
    ["random", "bool", "chance", "probability", "coin flip"],
    complexity=1,
))

_register(_node(
    "Random Float", "Random",
    "Generates a random float within a range when triggered.",
    [_in("Trigger", "Trigger"),
     _in("Min", "Float", default=0.0),
     _in("Max", "Float", default=1.0),
     _in("Seed", "Int32", required=False, default=-1)],
    [_out("Value", "Float"),
     _out("Trigger", "Trigger")],
    ["random", "float", "variation", "procedural", "range", "jitter"],
    complexity=1,
))

_register(_node(
    "Random Int", "Random",
    "Generates a random integer within a range when triggered.",
    [_in("Trigger", "Trigger"),
     _in("Min", "Int32", default=0),
     _in("Max", "Int32", default=10),
     _in("Seed", "Int32", required=False, default=-1)],
    [_out("Value", "Int32"),
     _out("Trigger", "Trigger")],
    ["random", "int", "integer", "variation", "procedural", "range"],
    complexity=1,
))

_register(_node(
    "Random Time", "Random",
    "Generates a random time duration within a range when triggered.",
    [_in("Trigger", "Trigger"),
     _in("Min", "Time", default=0.1),
     _in("Max", "Time", default=1.0),
     _in("Seed", "Int32", required=False, default=-1)],
    [_out("Value", "Time"),
     _out("Trigger", "Trigger")],
    ["random", "time", "duration", "variation", "procedural", "interval"],
    complexity=1,
))


# -------------------------------------------------------------------
# Debug  (2 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Get Wave Info", "Debug",
    "Extracts metadata from a WaveAsset: channel count, sample rate, duration.",
    [_in("WaveAsset", "WaveAsset")],
    [_out("NumChannels", "Int32"),
     _out("SampleRate", "Float"),
     _out("Duration", "Time")],
    ["debug", "wave", "info", "metadata", "channels", "sample rate", "duration"],
    complexity=1,
))

_register(_node(
    "Get Wave Duration", "Debug",
    "Returns the duration of a WaveAsset in seconds. Simpler alternative to Get Wave Info.",
    [_in("Wave", "WaveAsset")],
    [_out("Duration", "Time")],
    ["wave", "duration", "length", "time", "info", "utility"],
    complexity=1,
))

_register(_node(
    "Print Log", "Debug",
    "Prints a string to the output log when triggered.",
    [_in("Trigger", "Trigger"),
     _in("Label", "String", required=False, default="MetaSound"),
     _in("Value", "Float", required=False)],
    [],
    ["debug", "print", "log", "console", "trace"],
    complexity=1,
))


# -------------------------------------------------------------------
# External IO  (2 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Audio Bus Reader", "External IO",
    "Reads audio from a submix bus for routing or analysis.",
    [_in("Bus Name", "String"),
     _in("NumChannels", "Int32", default=1)],
    [_out("Audio", "Audio")],
    ["bus", "submix", "read", "external", "routing", "input"],
    complexity=2,
))

_register(_node(
    "Wave Writer", "External IO",
    "Records audio to a WAV file on disk.",
    [_in("Audio", "Audio"),
     _in("Filename", "String", default="output"),
     _in("Start", "Trigger"),
     _in("Stop", "Trigger", required=False)],
    [_out("OnFinished", "Trigger")],
    ["wave", "writer", "record", "export", "file", "WAV", "capture"],
    complexity=2,
))


# -------------------------------------------------------------------
# General / Utility  (6 nodes)
# -------------------------------------------------------------------

_register(_node(
    "Flanger", "General",
    "Flanger effect using modulated short delay line.",
    [_in("Audio", "Audio"),
     _in("Rate", "Float", default=0.5),
     _in("Depth", "Float", default=0.5),
     _in("Feedback", "Float", default=0.3),
     _in("DryWet", "Float", required=False, default=0.5)],
    [_out("Audio", "Audio")],
    ["modulation", "chorus", "effect", "flanger", "sweep", "jet"],
    complexity=2,
))

_register(_node(
    "Ring Mod", "General",
    "Ring modulator -- multiplies audio by a modulation oscillator.",
    [_in("Audio", "Audio"),
     _in("ModFrequency", "Float", default=440.0),
     _in("DryWet", "Float", required=False, default=1.0)],
    [_out("Audio", "Audio")],
    ["modulation", "metallic", "effect", "ring", "inharmonic", "bell"],
    complexity=2,
))

_register(_node(
    "Wave Shaper", "General",
    "Waveshaping distortion -- soft clipping to hard clipping based on amount.",
    [_in("Audio", "Audio"),
     _in("Amount", "Float", default=0.5),
     _in("DryWet", "Float", required=False, default=1.0)],
    [_out("Audio", "Audio")],
    ["distortion", "saturation", "overdrive", "waveshaper", "clip", "warm",
     "crunch"],
    complexity=2,
))

_register(_node(
    "Get WaveTable From Bank", "General",
    "Extracts a single wavetable from a wavetable bank asset by index.",
    [_in("Bank", "UObject"),
     _in("Index", "Int32", default=0)],
    [_out("WaveTable", "UObject")],
    ["wavetable", "bank", "get", "extract", "index"],
    complexity=1,
))

_register(_node(
    "Send", "General",
    "Routes audio to a named bus or side-chain destination.",
    [_in("Audio", "Audio"),
     _in("Bus Name", "String"),
     _in("SendLevel", "Float", default=1.0)],
    [],
    ["send", "bus", "routing", "sidechain", "aux", "effect send"],
    complexity=1,
))

_register(_node(
    "Convert", "General",
    "Converts between compatible MetaSound data types.",
    [_in("Value", "Float")],
    [_out("Result", "Time")],
    ["convert", "type", "cast", "utility"],
    complexity=1,
))

_register(_node(
    "Get Variable", "General",
    "Reads the current value of a graph variable.",
    [],
    [_out("Value", "Float")],
    ["variable", "state", "get", "read", "graph variable"],
    complexity=1,
))

_register(_node(
    "Set Variable", "General",
    "Writes a new value to a graph variable. Execute pin triggers the write.",
    [_in("Value", "Float"),
     _in("Execute", "Trigger")],
    [],
    ["variable", "state", "set", "write", "graph variable"],
    complexity=1,
))


# -------------------------------------------------------------------
# Patches (reusable sub-graphs from Craig Owen tutorial)
# -------------------------------------------------------------------

_register(_node(
    "MSP_RandomizationNode", "Patches",
    "Wave asset array player with per-shot pitch and volume randomization. "
    "Selects from WaveAsset array on each Next trigger, applies random pitch/volume offsets. "
    "Used for weapon burst round-robin layers. From Craig Owen weapon burst tutorial.",
    [_in("In Array", "WaveAsset[]"),
     _in("Next", "Trigger"),
     _in("Pitch_RandomMax", "Float", required=False, default=0.0),
     _in("Pitch_RandomMin", "Float", required=False, default=0.0),
     _in("Volume_Master", "Float", required=False, default=1.0),
     _in("Volume_RandomMax", "Float", required=False, default=1.1),
     _in("Volume_RandomMin", "Float", required=False, default=0.9)],
    [_out("On Finished", "Trigger"),
     _out("On Nearly Finished", "Trigger"),
     _out("Out", "Audio"),
     _out("Value", "Float")],
    ["randomization", "wave", "variation", "weapon", "gunshot", "pitch", "volume",
     "patch", "reusable", "round-robin"],
    complexity=3,
))

_register(_node(
    "MSP_CrossFadeByParam_3Inputs", "Patches",
    "3-layer distance crossfade patch. Each layer: Shuffle→WavePlayer→MapRange gain→StereoMixer. "
    "Includes optimization gates (only processes active layers) and Mid-Side mono output. "
    "From Craig Owen weapon audio tutorial.",
    [_in("TriggerStart", "Trigger"),
     _in("InputParameter", "Float", default=0.0),
     _in("WaveAsset_A", "WaveAsset[]"),
     _in("WaveAsset_A_StartFadeOut", "Float", default=5000.0),
     _in("WaveAsset_A_EndFadeOut", "Float", default=7500.0),
     _in("WaveAsset_B", "WaveAsset[]"),
     _in("WaveAsset_B_StartFadeIn", "Float", default=5000.0),
     _in("WaveAsset_B_EndFadeIn", "Float", default=7500.0),
     _in("WaveAsset_B_StartFadeOut", "Float", default=15000.0),
     _in("WaveAsset_B_EndFadeOut", "Float", default=17500.0),
     _in("WaveAsset_C", "WaveAsset[]"),
     _in("WaveAsset_C_StartFadeIn", "Float", default=15000.0),
     _in("WaveAsset_C_EndFadeIn", "Float", default=17500.0)],
    [_out("OnFinished", "Trigger"),
     _out("Output_L", "Audio"),
     _out("Output_R", "Audio"),
     _out("AudioMono", "Audio")],
    ["crossfade", "distance", "layers", "weapon", "tail", "blend", "parameter",
     "patch", "reusable"],
    complexity=4,
))

_register(_node(
    "MSP_Switch_3Inputs", "Patches",
    "Hard switch between 3 WaveAsset array inputs based on an Int32 parameter (0/1/2). "
    "Used for room-size selection in weapon audio. Each input: Shuffle→WavePlayer→StereoMixer.",
    [_in("TriggerStart", "Trigger"),
     _in("InputParameter", "Int32", default=0),
     _in("WaveAsset_A", "WaveAsset[]"),
     _in("WaveAsset_B", "WaveAsset[]"),
     _in("WaveAsset_C", "WaveAsset[]")],
    [_out("OnFinished", "Trigger"),
     _out("Output_L", "Audio"),
     _out("Output_R", "Audio")],
    ["switch", "select", "room", "int32", "hard-switch", "patch", "reusable"],
    complexity=3,
))


# ===================================================================
# Query / search helpers
# ===================================================================

def get_nodes_by_category(category: str) -> list[NodeDef]:
    """Return all nodes belonging to a category (case-insensitive)."""
    cat_lower = category.lower()
    return [n for n in METASOUND_NODES.values() if n["category"].lower() == cat_lower]


def get_nodes_by_tag(tag: str) -> list[NodeDef]:
    """Return all nodes whose tags list contains the given tag (case-insensitive)."""
    tag_lower = tag.lower()
    return [n for n in METASOUND_NODES.values() if tag_lower in (t.lower() for t in n["tags"])]


def search_nodes(query: str) -> list[NodeDef]:
    """Substring search across node name, tags, and description (case-insensitive).

    Returns a list of matching nodes sorted by relevance:
      1. Name matches first
      2. Tag matches second
      3. Description matches last
    """
    q = query.lower()
    name_hits: list[NodeDef] = []
    tag_hits: list[NodeDef] = []
    desc_hits: list[NodeDef] = []
    seen: set[str] = set()

    for node in METASOUND_NODES.values():
        nid = node["name"]
        if q in node["name"].lower():
            name_hits.append(node)
            seen.add(nid)
        elif any(q in t.lower() for t in node["tags"]):
            tag_hits.append(node)
            seen.add(nid)
        elif q in node["description"].lower():
            if nid not in seen:
                desc_hits.append(node)
    return name_hits + tag_hits + desc_hits


def get_all_categories() -> dict[str, int]:
    """Return a dict of category name -> number of nodes in that category."""
    counts: dict[str, int] = {}
    for node in METASOUND_NODES.values():
        cat = node["category"]
        counts[cat] = counts.get(cat, 0) + 1
    return dict(sorted(counts.items()))
