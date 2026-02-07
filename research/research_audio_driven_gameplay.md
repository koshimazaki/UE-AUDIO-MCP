# Audio-Driven Gameplay - Research Summary

_Generated: 2026-02-07 | Sources: 25+ | Engine: UE 4.26 (concepts transfer to UE5)_

## Quick Reference

<key-points>
- Learning path with 3 courses + 12 individual tutorials on Epic Dev Community
- Core concept: Audio amplitude/frequency analysis drives gameplay parameters
- Three analysis approaches: Real-Time Envelope, Real-Time Frequency (FFT), Non-Real-Time (Synesthesia)
- Key Blueprint nodes: Start Envelope Following, Add Spectral Analysis Delegate, Audio Capture Component
- UE5 equivalent: MetaSounds Envelope Follower node + Audio Synesthesia plugin (LoudnessNRT, ConstantQNRT, OnsetNRT)
- Content pack available on Fab/Marketplace with full UE project template
</key-points>

---

## Overview

<summary>
The "Audio-Driven Gameplay" learning path teaches how to make game actors "hear" and respond
to in-game audio. It covers driving gameplay parameters by analyzing audio amplitude (envelope
following) and frequency content (spectral/FFT analysis), plus using microphone input via
Audio Capture Components. Originally built for UE 4.26, the patterns transfer directly to UE5
with additional MetaSounds-native analysis capabilities.

Practical examples: leaf animations driven by wind sound, camera shake from explosion
frequencies, in-game actors reacting to music tracks, microphone-driven game events.
</summary>

---

## Learning Path Structure

The learning path contains **3 courses** with **12+ individual video tutorials**.

**Learning Path URL:**
https://dev.epicgames.com/community/learning/paths/60/unreal-engine-audio-driven-gameplay

**Marketplace Content Pack:**
https://www.unrealengine.com/marketplace/en-US/product/audio-driven-gameplay

**Authors/Instructors:** Epic Games Online Learning team (collaboration with Richard Stevens
and Dave Raybould from Leeds Beckett University, who created the related "Dynamic Audio" and
"Ambient and Procedural Sound Design" courses for the same learning platform).

---

## Course 1: Introduction to Audio-Driven Gameplay

**URL:** https://dev.epicgames.com/community/learning/courses/2y/unreal-engine-introduction-to-audio-driven-gameplay

**Description:** Introduces the concepts of audio-driven gameplay. Covers the fundamentals of
submix routing, how audio analysis works in UE, and sets up the content pack project.

**Key Concepts:**
- What audio-driven gameplay is and why it matters
- Submix architecture and audio routing
- How to route audio to submixes for analysis
- Understanding the audio pipeline from source to analysis

---

## Course 2: Audio-Driven Gameplay - Non-Real-Time Analysis

**URL:** https://dev.epicgames.com/community/learning/courses/LA/audio-driven-gameplay-non-real-time-analysis

**Description:** Covers using Non-Real-Time (NRT) Audio Analysis to drive gameplay. Uses the
Audio Synesthesia plugin to pre-analyze audio assets at cook time and query results at runtime
with zero performance cost.

### Individual Tutorials in Course 2:

#### 2.1 Non-Real-Time Audio Analysis: Synesthesia Part One
- **URL:** https://dev.epicgames.com/community/learning/tutorials/JWJ/unreal-engine-non-real-time-audio-analysis-synesthesia-part-one
- **Description:** Begin learning about the use of synesthesia tools for audio analysis.
- **Key Nodes:** LoudnessNRT, ConstantQNRT, OnsetNRT asset creation
- **Pattern:** Create NRT analyzer asset -> Assign USoundWave -> Query results in Blueprint

#### 2.2 Non-Real-Time Audio Analysis: Synesthesia Part Two
- **URL:** https://dev.epicgames.com/community/learning/tutorials/dVx/unreal-engine-non-real-time-audio-analysis-synesthesia-part-two
- **Description:** Continue learning about synesthesia tools in the second video of this two-part module.
- **Key Nodes:** GetLoudnessAtTime, GetConstantQAtTime, GetOnsetAtTime Blueprint functions

#### 2.3 Non-Real-Time Envelope Analysis: Audio Component Averaged Values
- **URL:** https://dev.epicgames.com/community/learning/courses/LA/audio-driven-gameplay-non-real-time-analysis/z3q/unreal-engine-non-real-time-envelope-analysis-audio-component-averaged-values
- **Description:** Use pre-analyzed envelope data to drive gameplay parameters with averaged amplitude values.

#### 2.4 Non-Real-Time Frequency Analysis: Audio Component Averaged Values
- **URL:** https://dev.epicgames.com/community/learning/courses/LA/audio-driven-gameplay-non-real-time-analysis/eZk/non-real-time-frequency-analysis-audio-component-averaged-values
- **Description:** Use pre-analyzed frequency data to drive parameters based on specific frequency band strengths.

#### 2.5 Non-Real-Time Envelope Analysis: Scaling Envelope Data Over Distance for Audio 'Listeners'
- **URL:** https://dev.epicgames.com/community/learning/tutorials/Pq7/unreal-engine-non-real-time-envelope-analysis-scaling-envelope-data-over-distance-for-audio-listeners
- **Description:** Create the equivalent of an "audio listener" that can detect how loudly a sound will be "heard" at a specific location in the world. Scale envelope data based on distance for spatial awareness.
- **Pattern:** NRT envelope value x distance attenuation = perceived loudness at listener location

---

## Course 3: Audio-Driven Gameplay - Real-Time Analysis

**URL:** https://dev.epicgames.com/community/learning/courses/Vm/unreal-engine-audio-driven-gameplay-real-time-analysis

**Description:** Covers using Real-Time Audio Analysis (envelope following and spectral/FFT
analysis on submixes) to drive gameplay. Includes microphone input via Audio Capture Components.

### Individual Tutorials in Course 3:

#### 3.1 Real-Time Envelope Analysis: Audio Component Averaged Values
- **URL:** https://dev.epicgames.com/community/learning/tutorials/Z23/unreal-engine-real-time-envelope-analysis-audio-component-averaged-values
- **Description:** Affect the movement of a game actor by using the averaged amplitude of a sound cue. Assess when real-time audio analysis is appropriate vs NRT.
- **Pattern:** Sound Cue -> Submix -> Start Envelope Following -> Delegate fires -> Averaged amplitude drives actor movement
- **Key Nodes:** Start Envelope Following, Add Envelope Follower Delegate

#### 3.2 Real-Time Envelope Analysis: Audio Component Individual Values
- **URL:** https://dev.epicgames.com/community/learning/tutorials/abo/unreal-engine-real-time-envelope-analysis-audio-component-individual-values
- **Description:** Trigger additional sounds or particle effects by using the amplitude of a specific soundwave within a sound cue.
- **Pattern:** Individual soundwave amplitude -> threshold check -> trigger sound/particle
- **Key Nodes:** Start Envelope Following, Envelope Follower Delegate (per-channel values)

#### 3.3 Real-Time Envelope Analysis: Audio Input with Audio Capture Components
- **URL:** https://dev.epicgames.com/community/learning/tutorials/b2V/unreal-engine-real-time-envelope-analysis-audio-input-with-audio-capture-components
- **Description:** Use audio capture components (microphone input) to generate variables and determine events within a game.
- **Pattern:** Microphone -> Audio Capture Component -> Submix -> Envelope Following -> Game Variable
- **Key Nodes:** Audio Capture Component, Start Capture, Stop Capture, Sound Submix

#### 3.4 Real-Time Frequency Analysis: Submix Frequency Bands
- **URL:** https://dev.epicgames.com/community/learning/tutorials/jZv/unreal-engine-real-time-frequency-analysis-submix-frequency-bands
- **Description:** Determine when and how to use different types of spectral analysis band settings by using the audio on a submix.
- **Pattern:** Audio -> Submix -> Add Spectral Analysis Delegate -> Band settings -> Frequency data per band
- **Key Nodes:** Add Spectral Analysis Delegate, FSoundSubmixSpectralAnalysisBandSettings

#### 3.5 Real-Time Frequency Analysis: Submix Frequencies and Audio Capture Components
- **URL:** https://dev.epicgames.com/community/learning/tutorials/rpl/unreal-engine-real-time-frequency-analysis-submix-frequencies-and-audio-capture-components
- **Description:** Launch events within a game by analyzing the amplitude of specific frequencies of an audio input (typically a microphone).
- **Pattern:** Microphone -> Audio Capture -> Submix -> Spectral Analysis -> Frequency threshold -> Game Event
- **Key Nodes:** Audio Capture Component, Add Spectral Analysis Delegate, frequency band thresholds

#### 3.6 Real-Time Frequency Analysis: Submix Interfacing with Niagara Visual Effects
- **URL:** https://dev.epicgames.com/community/learning/tutorials/YGn/unreal-engine-real-time-frequency-analysis-submix-interfacing-with-niagara-visual-effects
- **Description:** Examine how Niagara can interface with both non-real-time and real-time audio via submixes to create visual effects (audio-reactive particles).
- **Pattern:** Submix spectral data -> Niagara User Parameter -> Particle system reacts to frequency bands
- **Key Nodes:** Niagara System, Audio Spectrum parameter, Submix spectral output

---

## Blueprint Node Reference

### Submix Envelope Following (Real-Time Amplitude)

| Node | Category | Description |
|------|----------|-------------|
| `Start Envelope Following` | Audio > Analysis | Starts the submix envelope follower; delegate begins firing |
| `Stop Envelope Following` | Audio > Analysis | Stops the envelope follower on the submix |
| `Add Envelope Follower Delegate` | Audio > Analysis | Called when new envelope data is available; returns envelope value per channel (L, R, C, LS, RS, etc.) |

**How it works:** An Envelope Follower is a DSP algorithm that outputs the amplitude of an
audio signal smoothed over time. This is more effective than raw audio data because audio runs
at 48,000 samples/sec while game runs at 60 fps. The envelope follower bridges this gap.

### Submix Spectral Analysis (Real-Time Frequency / FFT)

| Node | Category | Description |
|------|----------|-------------|
| `Add Spectral Analysis Delegate` | Audio > Spectrum | Provides FFT spectral analysis data per configured band |
| `Start Spectral Analysis` | Audio > Spectrum | Activates the spectrum analyzer on a submix |

**Parameters for Spectral Analysis:**
- `In Band Settings` - Struct defining analyzer configuration
- `In Num Bands` - Number of spectral bands to analyze
- `In Minimum Frequency` - Minimum frequency range (Hz)
- `In Maximum Frequency` - Maximum frequency range (Hz)

**Band Types:**
- `Custom` - User-specified frequency ranges
- `EqualWidth` - Equal frequency width per band
- `ConstantQ` - Perceptually-spaced (like piano keys, logarithmic)

### Audio Capture Component (Microphone Input)

| Node | Category | Description |
|------|----------|-------------|
| `Audio Capture Component` | Component | Captures microphone input during gameplay |
| `Start Capture` | AudioCapture | Begins recording from microphone |
| `Stop Capture` | AudioCapture | Stops recording |
| `Get Audio Capture Device Info` | AudioCapture | Lists available audio input devices |

**Setup Pattern:**
1. Add Audio Capture Component to Actor
2. Set Sound Submix property on the component
3. Call Start Capture on BeginPlay
4. Route submix to Envelope Following or Spectral Analysis
5. Use delegates to receive analysis data

**Limitation:** The component's raw audio buffer is not directly exposed to Blueprints.
Audio data flows through the submix system for analysis. Direct sample access requires C++.

### Audio Synesthesia (Non-Real-Time / Pre-Analyzed)

| Analyzer Class | What It Measures | Key Parameters |
|---------------|-----------------|----------------|
| `LoudnessNRT` | Perceptual loudness (accounts for human frequency sensitivity) | AnalysisPeriod, MinFreq, MaxFreq, CurveType, NoiseFloorDb |
| `ConstantQNRT` | Frequency band strength (perceptually-spaced like piano keys) | AnalysisPeriod, StartingFrequency, NumBands, NumBandsPerOctave, DownMixToMono |
| `OnsetNRT` | Audio events (note onsets, percussion, plosives, explosions) | GranularityInSeconds, Sensitivity, MinFreq, MaxFreq, DownMixToMono |

**How NRT works:**
1. Analysis happens in the editor at cook time (not runtime)
2. Results are cached in uasset files
3. Blueprint queries cached data at runtime with zero performance cost
4. Best for known audio assets (music tracks, sound effects)
5. Cannot analyze live/dynamic audio (use real-time for that)

---

## Core Patterns

### Pattern 1: Amplitude Analysis -> Parameter

```
[Sound Source] -> [Submix] -> Start Envelope Following
                                    |
                          Envelope Follower Delegate
                                    |
                          float EnvelopeValue (0.0-1.0)
                                    |
                          [Map Range / Clamp]
                                    |
                          [Set Actor Property]
                          (Scale, Position, Opacity, etc.)
```

**Use cases:**
- Wind sound amplitude drives leaf animation intensity
- Music loudness drives light pulsing
- Explosion envelope drives camera shake magnitude
- Voice amplitude drives NPC lip-sync or awareness

### Pattern 2: Frequency Analysis -> Parameter

```
[Sound Source] -> [Submix] -> Add Spectral Analysis Delegate
                                    |
                          Spectral Data per Band
                          (Array of {Frequency, Magnitude})
                                    |
                          [Select Frequency Range]
                          Low (20-250Hz), Mid (250-4kHz), High (4k-20kHz)
                                    |
                          [Threshold Check / Map Range]
                                    |
                          [Drive Parameter per Band]
                          (Bass drives ground shake, treble drives sparkles)
```

**Use cases:**
- Bass frequencies (20-250Hz) trigger ground rumble / camera shake
- Mid frequencies (250-4000Hz) drive NPC awareness
- High frequencies (4000-20000Hz) trigger sparkle / shimmer VFX
- Full spectrum drives audio visualizer / Niagara particles

### Pattern 3: Microphone Input -> Game Event

```
[Microphone] -> [Audio Capture Component] -> [Sound Submix]
                                                   |
                              +---------+---------+
                              |                   |
                    Envelope Following    Spectral Analysis
                              |                   |
                    Amplitude > Threshold   Freq Band > Threshold
                              |                   |
                    [Game Event]           [Game Event]
                    (Shout to scare enemy)  (Whistle frequency detected)
```

**Use cases:**
- Player shouts into mic -> scare nearby enemies (amplitude threshold)
- Specific pitch/whistle -> trigger puzzle mechanism (frequency detection)
- Blow into mic -> extinguish in-game candle (sustained amplitude)
- Clap detection -> toggle game state (onset/transient detection)

### Pattern 4: NRT Analysis -> Timed Events (Synesthesia)

```
[Sound Wave Asset] -> [LoudnessNRT / ConstantQNRT / OnsetNRT]
                              |
                    Pre-analyzed at cook time
                              |
                    Blueprint: GetLoudnessAtTime(timestamp)
                              |
                    [Sync game events to music]
                    (Beat-matched effects, rhythm gameplay)
```

**Use cases:**
- Music track onset data drives rhythm game hit markers
- Loudness curve drives environment intensity over time
- ConstantQ bands drive per-frequency visual effects synced to music
- Audio listeners that "hear" at a distance (NRT envelope x distance attenuation)

---

## UE5 / MetaSounds Equivalents

The UE 4.26 patterns transfer to UE5 with these equivalents:

### MetaSounds Native Nodes

| UE4 Concept | UE5 MetaSounds Equivalent | Notes |
|-------------|--------------------------|-------|
| Submix Envelope Following | `Envelope Follower` node | Native MetaSounds node, outputs amplitude envelope from audio input |
| Submix Spectral Analysis | No direct equivalent | MetaSounds does not have built-in FFT/spectral nodes; use Submix analysis or Synesthesia |
| Sound Cue routing | MetaSounds patch graph | MetaSounds replaces Sound Cues as the primary audio system |
| Audio Component | MetaSounds Source Component | Attach MetaSounds sources to actors |

### MetaSounds Envelope Follower Node

- **Category:** Analysis / Dynamics
- **Analyzer Name:** `UE.Audio.EnvelopeFollower`
- **Analyzer Output:** `EnvelopeValue`
- **Inputs:** Audio (audio-rate signal), Attack Time (ms), Release Time (ms)
- **Output:** Envelope value (float, 0.0-1.0)
- **Usage:** Watch output via `SetWatchOutput` on MetaSounds source, or use within graph

### Audio Synesthesia Plugin (UE5)

The Synesthesia plugin is **fully available in UE5** and is the recommended approach for
pre-analyzed audio-driven gameplay:

| NRT Analyzer | UE5 Class | Blueprint Access |
|-------------|-----------|-----------------|
| LoudnessNRT | `ULoudnessNRT` | `GetLoudnessAtTime()`, `GetNormalizedLoudnessAtTime()` |
| ConstantQNRT | `UConstantQNRT` | `GetConstantQAtTime()`, `GetNormalizedConstantQAtTime()` |
| OnsetNRT | `UOnsetNRT` | `GetOnsetAtTime()`, onset timestamps + strengths |

### Submix Analysis (Still Works in UE5)

The UE4 submix-based envelope following and spectral analysis **still work in UE5**.
The submix system is unchanged:
- `Start Envelope Following` / `Stop Envelope Following` - still available
- `Add Envelope Follower Delegate` - still fires with per-channel data
- `Add Spectral Analysis Delegate` - still provides FFT data
- Audio Capture Component - still captures microphone input

### Recommended UE5 Approach

For new UE5 projects, the recommended stack is:

1. **Known audio assets** -> Audio Synesthesia NRT (zero runtime cost)
2. **Live audio / procedural** -> MetaSounds Envelope Follower (within graph)
3. **Microphone input** -> Audio Capture Component -> Submix -> Envelope/Spectral analysis
4. **Audio-reactive VFX** -> Submix spectral data -> Niagara parameters
5. **MetaSounds output analysis** -> MetaSounds Source -> Submix -> Analysis delegates

---

## Related Tutorials (Outside the Learning Path)

| Tutorial | URL | Relevance |
|----------|-----|-----------|
| Synesthesia Audio Visualization using Blueprints | https://dev.epicgames.com/community/learning/tutorials/0lKo/unreal-engine-synesthesia-audio-visualization-using-blueprints | Community tutorial on frequency spectrum visualization |
| Sequencer Event Tracks For Audio-Driven Sync | https://dev.epicgames.com/community/learning/tutorials/qEY/unreal-engine-sequencer-event-tracks-for-audio-driven-sync | Sync game events to audio via Sequencer |
| Understanding Submix and Master Submix Effects | https://dev.epicgames.com/community/learning/tutorials/KXr/unreal-engine-understanding-submix-and-master-submix-effects | Foundation knowledge for submix routing |
| Using Audio Capture Component for Mic Capture | https://dev.epicgames.com/community/learning/knowledge-base/Oak2/unreal-engine-using-audio-capture-component-for-mic-capture | Official KB article on microphone setup |
| Ambient and Procedural Sound Design (Course) | https://dev.epicgames.com/community/learning/courses/qR/unreal-engine-ambient-and-procedural-sound-design | Related course by same instructors |
| Dynamic Audio (Course) | https://dev.epicgames.com/community/learning/courses/Eq/unreal-engine-dynamic-audio | Related course on dynamic audio systems |

---

## Content Pack Details

**Product:** Audio-Driven Gameplay in UE Online Learning
**Platform:** Unreal Engine Marketplace / Fab
**URL:** https://www.unrealengine.com/marketplace/en-US/product/audio-driven-gameplay
**Engine Version:** UE 4.26
**Publisher:** Unreal Online Learning (Epic Games)
**Type:** Full project template (Config + Content + .uproject)

**What's included:**
- Complete UE project with all tutorial examples
- Pre-built Blueprints for envelope following
- Pre-built Blueprints for spectral analysis
- Audio Capture Component examples (microphone input)
- Synesthesia NRT analyzer examples
- Example game mechanics driven by audio
- Sound Cue assets for testing

**Example Scenarios in Pack:**
1. Leaf animations driven by wind sound amplitude
2. Camera shake driven by explosion frequency content
3. In-game actors reacting to music tracks
4. Microphone-driven gameplay events

---

## Important Considerations

<warnings>
- UE 4.26 content: Blueprint screenshots may differ from UE5 UI but logic is identical
- Audio Capture Component buffer is NOT exposed to Blueprints directly; data flows through submix system
- Real-time analysis has CPU cost; use NRT (Synesthesia) for known audio assets whenever possible
- Envelope Follower smooths 48kHz samples to game framerate (~60fps); configure attack/release appropriately
- MetaSounds does NOT have native FFT/spectral analysis nodes; use Submix-level spectral analysis instead
- Spectral analysis band types matter: ConstantQ for music, EqualWidth for effects, Custom for specific frequencies
- Microphone input requires user permission on some platforms
- Audio Synesthesia NRT requires the AudioSynesthesia plugin to be enabled
- OnsetNRT sensitivity parameter is critical: too low = missed events, too high = false positives
</warnings>

---

## Resources

<references>
- [Learning Path: Audio-Driven Gameplay](https://dev.epicgames.com/community/learning/paths/60/unreal-engine-audio-driven-gameplay) - Main learning path hub
- [Course 1: Introduction](https://dev.epicgames.com/community/learning/courses/2y/unreal-engine-introduction-to-audio-driven-gameplay) - Fundamentals
- [Course 2: Non-Real-Time Analysis](https://dev.epicgames.com/community/learning/courses/LA/audio-driven-gameplay-non-real-time-analysis) - Synesthesia NRT
- [Course 3: Real-Time Analysis](https://dev.epicgames.com/community/learning/courses/Vm/unreal-engine-audio-driven-gameplay-real-time-analysis) - Envelope + Spectral
- [Marketplace Content Pack](https://www.unrealengine.com/marketplace/en-US/product/audio-driven-gameplay) - Full project template
- [Audio Synesthesia Docs (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/audio-synesthesia-in-unreal-engine) - NRT analyzer reference
- [Submix Overview (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-submixes-in-unreal-engine) - Envelope/Spectral analysis docs
- [Submix Docs (UE 4.27)](https://docs.unrealengine.com/4.27/en-US/WorkingWithAudio/Submixes/) - Original UE4 submix reference
- [MetaSounds Reference (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-reference-guide-in-unreal-engine) - MetaSounds node catalog
- [MetaSounds Function Nodes (UE 5.7)](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasound-function-nodes-reference-guide-in-unreal-engine) - Envelope Follower node
- [ULoudnessNRT API](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/AudioSynesthesia/ULoudnessNRT) - C++ API reference
- [Forum: Learning Path Discussion](https://forums.unrealengine.com/t/learning-path-audio-driven-gameplay/587181) - Community discussion
- [Forum: Real-Time Analysis Course](https://forums.unrealengine.com/t/course-audio-driven-gameplay-real-time-analysis/610328) - Course feedback
- [Forum: RT Audio Analyzer with MetaSounds](https://forums.unrealengine.com/t/realtime-audio-analyzer-with-metasounds/578728) - UE5 MetaSounds analysis discussion
</references>

---

## Metadata

<meta>
research-date: 2026-02-07
confidence: high
version-checked: UE 4.26 (original), UE 5.7 (equivalents verified)
courses: 3
tutorials: 12+
blueprint-nodes-catalogued: 15
patterns-documented: 4
</meta>
