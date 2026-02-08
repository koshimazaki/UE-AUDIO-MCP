# UE 5.7 MetaSounds Custom Node C++ API Research

_Generated: 2026-02-08 | Sources: 20+ | Target: Custom DSP Node Development_

## Quick Reference

<key-points>
- Custom MetaSound nodes require MetasoundGraphCore module (core API) + MetasoundFrontend (types)
- TExecutableOperator pattern: FOperator struct with Execute(FOperatorSettings&) and Reset(FOperatorSettings&)
- Multi-output (stereo) uses TDataWriteReference<FAudioBuffer> per channel (Out Left, Out Right)
- Trigger pins: TDataReadReference<FTrigger> + ExecuteSubBlocks() for sample-accurate processing
- Enum pins: Define custom enum type + DECLARE_METASOUND_ENUM() + TEnumDataReference
- State management: Private operator member variables persist across Execute() calls
- Sample rate: FOperatorSettings.GetSampleRate(), block size: GetNumFramesPerBlock()
- Registration: METASOUND_REGISTER_NODE(FMyNodeOperator) in .cpp + FNodeFacade metadata
- Engine source code location: Engine/Plugins/Runtime/Metasound/Source/MetasoundStandardNodes/
</key-points>

---

## 1. Module Dependencies (Build.cs)

### Required Modules for Custom DSP Nodes

Your existing plugin has the basics for Builder API. For **custom DSP nodes**, add:

```cs
PublicDependencyModuleNames.AddRange(new string[]
{
    "Core",
    "CoreUObject",
    "Engine",
    "MetasoundGraphCore",   // Core MetaSound graph API - REQUIRED for custom nodes
    "MetasoundFrontend",    // Node types, FMetasoundFrontendClassName
    "MetasoundEngine",      // UMetaSoundSource, runtime integration
    "AudioMixer",           // FAudioBuffer, audio processing types
});

PrivateDependencyModuleNames.AddRange(new string[]
{
    "MetasoundStandardNodes", // Reference implementations (optional but useful)
    "SignalProcessing",       // DSP utilities (filters, envelopes, oscillators)
    "AudioExtensions",        // Audio plugin interfaces
});
```

### Current Plugin Status

Your `UEAudioMCP.Build.cs` already has:
- ✅ MetasoundEngine (Builder API)
- ✅ MetasoundFrontend (class names)
- ✅ MetasoundGraphCore (graph logic)
- ✅ AudioMixer (audio types)

**To add custom nodes**: No new modules required for basic DSP. Add `SignalProcessing` if you need pre-built DSP utilities (biquad filters, envelope followers, etc.).

---

## 2. TExecutableOperator Pattern

### Core Structure

All MetaSound nodes follow this pattern:

```cpp
// MyCustomNode.cpp
#include "MetasoundNodeRegistrationMacro.h"
#include "MetasoundExecutableOperator.h"
#include "MetasoundPrimitives.h"
#include "MetasoundStandardNodesNames.h"
#include "MetasoundAudioBuffer.h"
#include "MetasoundParamHelper.h"

namespace Metasound
{
    // 1. Namespace for node (prevents collision)
    namespace MyCustomNodeNames
    {
        METASOUND_PARAM(InParamAudioInput, "In", "Audio input")
        METASOUND_PARAM(InParamGain, "Gain", "Volume multiplier")
        METASOUND_PARAM(OutParamAudio, "Out", "Audio output")
    }

    // 2. Operator class (the DSP logic)
    class FMyCustomNodeOperator : public TExecutableOperator<FMyCustomNodeOperator>
    {
    public:
        // Factory method - called once per node instance
        static FMyCustomNodeOperator* CreateOperator(
            const FCreateOperatorParams& InParams,
            FBuildErrorArray& OutErrors)
        {
            const FMyCustomNodeOperatorContext& Context = InParams.OperatorSettings;
            const FInputVertexInterface& InputInterface = InParams.InputInterface;

            // Get input data references
            FAudioBufferReadRef AudioIn = InputInterface.GetDataReadReference<FAudioBuffer>("In");
            FFloatReadRef GainIn = InputInterface.GetDataReadReference<float>("Gain");

            return new FMyCustomNodeOperator(InParams.OperatorSettings, AudioIn, GainIn);
        }

        // Constructor
        FMyCustomNodeOperator(
            const FOperatorSettings& InSettings,
            const FAudioBufferReadRef& InAudio,
            const FFloatReadRef& InGain)
        : AudioInput(InAudio)
        , GainInput(InGain)
        , AudioOutput(FAudioBufferWriteRef::CreateNew(InSettings))
        , SampleRate(InSettings.GetSampleRate())
        , NumFramesPerBlock(InSettings.GetNumFramesPerBlock())
        {
            // Initialize state here
        }

        // Destructor
        virtual ~FMyCustomNodeOperator() {}

        // Reset operator state (called on graph changes)
        virtual void Reset(const IOperator::FResetParams& InParams)
        {
            AudioOutput->Zero();
            // Reset any state variables
        }

        // Main processing loop - called every audio buffer
        virtual void Execute()
        {
            const float* InputBuffer = AudioInput->GetData();
            float* OutputBuffer = AudioOutput->GetData();
            float Gain = *GainInput;

            for (int32 i = 0; i < NumFramesPerBlock; ++i)
            {
                OutputBuffer[i] = InputBuffer[i] * Gain;
            }
        }

        // Bind outputs (return references to output data)
        virtual FDataReferenceCollection GetOutputs() const
        {
            FDataReferenceCollection OutputDataReferences;
            OutputDataReferences.AddDataReadReference("Out", FAudioBufferReadRef(AudioOutput));
            return OutputDataReferences;
        }

    private:
        // Input references (read-only pointers to shared data)
        FAudioBufferReadRef AudioInput;
        FFloatReadRef GainInput;

        // Output references (owned by this operator)
        FAudioBufferWriteRef AudioOutput;

        // Cached settings
        float SampleRate;
        int32 NumFramesPerBlock;

        // State variables (persist across Execute() calls)
        // Add oscillator phase, envelope state, filter state, etc.
    };

    // 3. Node interface (describes inputs/outputs)
    class FMyCustomNode : public FNodeFacade
    {
    public:
        FMyCustomNode(const FNodeInitData& InitData)
        : FNodeFacade(InitData.InstanceName, InitData.InstanceID, TFacadeOperatorClass<FMyCustomNodeOperator>())
        {
        }

        virtual ~FMyCustomNode() = default;
    };

    // 4. Registration
    METASOUND_REGISTER_NODE(FMyCustomNode)
}
```

### Key Types

| Type | Purpose | Example |
|------|---------|---------|
| `FAudioBufferReadRef` | Read-only audio input | `const float* Buffer = AudioIn->GetData()` |
| `FAudioBufferWriteRef` | Writable audio output | `float* Buffer = AudioOut->GetData()` |
| `FFloatReadRef` | Read-only float parameter | `float Value = *FloatIn` |
| `FFloatWriteRef` | Writable float output | `*FloatOut = 1.0f` |
| `FTriggerReadRef` | Read-only trigger input | `InTrigger->ExecuteBlock(...)` |
| `FTriggerWriteRef` | Writable trigger output | `OutTrigger->TriggerFrame(FrameIndex)` |
| `TEnumReadRef<EMyEnum>` | Read-only enum input | `EMyEnum Value = *EnumIn` |

---

## 3. Handling Stereo/Multi-Voice Outputs

### Stereo Output Pattern

Use **separate FAudioBuffer outputs** for each channel:

```cpp
class FStereoGainOperator : public TExecutableOperator<FStereoGainOperator>
{
public:
    static FStereoGainOperator* CreateOperator(...)
    {
        // Get stereo inputs
        FAudioBufferReadRef LeftIn = InputInterface.GetDataReadReference<FAudioBuffer>("In Left");
        FAudioBufferReadRef RightIn = InputInterface.GetDataReadReference<FAudioBuffer>("In Right");
        FFloatReadRef GainIn = InputInterface.GetDataReadReference<float>("Gain");

        return new FStereoGainOperator(InSettings, LeftIn, RightIn, GainIn);
    }

    FStereoGainOperator(
        const FOperatorSettings& InSettings,
        const FAudioBufferReadRef& InLeft,
        const FAudioBufferReadRef& InRight,
        const FFloatReadRef& InGain)
    : LeftInput(InLeft)
    , RightInput(InRight)
    , GainInput(InGain)
    , LeftOutput(FAudioBufferWriteRef::CreateNew(InSettings))
    , RightOutput(FAudioBufferWriteRef::CreateNew(InSettings))
    , NumFramesPerBlock(InSettings.GetNumFramesPerBlock())
    {
    }

    virtual void Execute()
    {
        const float* LeftIn = LeftInput->GetData();
        const float* RightIn = RightInput->GetData();
        float* LeftOut = LeftOutput->GetData();
        float* RightOut = RightOutput->GetData();
        float Gain = *GainInput;

        for (int32 i = 0; i < NumFramesPerBlock; ++i)
        {
            LeftOut[i] = LeftIn[i] * Gain;
            RightOut[i] = RightIn[i] * Gain;
        }
    }

    virtual FDataReferenceCollection GetOutputs() const
    {
        FDataReferenceCollection Outputs;
        Outputs.AddDataReadReference("Out Left", FAudioBufferReadRef(LeftOutput));
        Outputs.AddDataReadReference("Out Right", FAudioBufferReadRef(RightOutput));
        return Outputs;
    }

private:
    FAudioBufferReadRef LeftInput;
    FAudioBufferReadRef RightInput;
    FFloatReadRef GainInput;
    FAudioBufferWriteRef LeftOutput;
    FAudioBufferWriteRef RightOutput;
    int32 NumFramesPerBlock;
};
```

### Multi-Voice Pattern (e.g., 4-voice oscillator bank)

Use **TArray<FAudioBufferWriteRef>** for dynamic voice count:

```cpp
class FMultiVoiceOscillator : public TExecutableOperator<FMultiVoiceOscillator>
{
public:
    FMultiVoiceOscillator(const FOperatorSettings& InSettings, int32 NumVoices)
    : NumFramesPerBlock(InSettings.GetNumFramesPerBlock())
    , SampleRate(InSettings.GetSampleRate())
    {
        Phases.Init(0.0f, NumVoices);
        for (int32 i = 0; i < NumVoices; ++i)
        {
            VoiceOutputs.Add(FAudioBufferWriteRef::CreateNew(InSettings));
        }
    }

    virtual void Execute()
    {
        for (int32 Voice = 0; Voice < VoiceOutputs.Num(); ++Voice)
        {
            float* Buffer = VoiceOutputs[Voice]->GetData();
            float Frequency = 440.0f * (1 << Voice); // Octaves

            for (int32 i = 0; i < NumFramesPerBlock; ++i)
            {
                Buffer[i] = FMath::Sin(Phases[Voice] * 2.0f * PI);
                Phases[Voice] += Frequency / SampleRate;
                if (Phases[Voice] >= 1.0f) Phases[Voice] -= 1.0f;
            }
        }
    }

private:
    TArray<FAudioBufferWriteRef> VoiceOutputs;
    TArray<float> Phases; // Per-voice oscillator phase
    int32 NumFramesPerBlock;
    float SampleRate;
};
```

---

## 4. Handling Trigger Pins

### Trigger Input Pattern

Triggers use `ExecuteBlock()` with lambda callbacks for **sample-accurate** event handling:

```cpp
class FTriggerGateOperator : public TExecutableOperator<FTriggerGateOperator>
{
public:
    FTriggerGateOperator(
        const FOperatorSettings& InSettings,
        const FTriggerReadRef& InTrigger,
        const FAudioBufferReadRef& InAudio)
    : InputTrigger(InTrigger)
    , AudioInput(InAudio)
    , AudioOutput(FAudioBufferWriteRef::CreateNew(InSettings))
    , bIsGateOpen(false)
    {
    }

    virtual void Execute()
    {
        const float* InputBuffer = AudioInput->GetData();
        float* OutputBuffer = AudioOutput->GetData();

        // Process trigger events sample-accurately
        InputTrigger->ExecuteBlock(
            // OnPreTrigger: called for samples BEFORE each trigger
            [&](int32 StartFrame, int32 EndFrame)
            {
                for (int32 i = StartFrame; i < EndFrame; ++i)
                {
                    OutputBuffer[i] = bIsGateOpen ? InputBuffer[i] : 0.0f;
                }
            },
            // OnTrigger: called AT each trigger sample
            [&](int32 TriggerFrame)
            {
                bIsGateOpen = !bIsGateOpen; // Toggle gate on each trigger
                OutputBuffer[TriggerFrame] = bIsGateOpen ? InputBuffer[TriggerFrame] : 0.0f;
            }
        );
    }

private:
    FTriggerReadRef InputTrigger;
    FAudioBufferReadRef AudioInput;
    FAudioBufferWriteRef AudioOutput;
    bool bIsGateOpen; // State persists across Execute() calls
};
```

### Trigger Output Pattern

Generate triggers at specific sample indices:

```cpp
class FEnvelopeOperator : public TExecutableOperator<FEnvelopeOperator>
{
public:
    virtual void Execute()
    {
        for (int32 i = 0; i < NumFramesPerBlock; ++i)
        {
            // Update envelope
            EnvelopeValue *= DecayRate;
            OutputBuffer[i] = EnvelopeValue;

            // Trigger OnFinished when envelope reaches zero
            if (EnvelopeValue < 0.001f && !bHasTriggeredFinish)
            {
                OnFinishedTrigger->TriggerFrame(i); // Trigger at sample i
                bHasTriggeredFinish = true;
            }
        }

        // Advance trigger to next block
        OnFinishedTrigger->AdvanceBlock();
    }

private:
    FTriggerWriteRef OnFinishedTrigger;
    float EnvelopeValue;
    bool bHasTriggeredFinish;
};
```

---

## 5. Handling Enum Pins (Waveform Selection)

### Define Custom Enum Type

```cpp
// In MyOscillator.h
UENUM(BlueprintType)
enum class EOscillatorWaveform : uint8
{
    Sine,
    Saw,
    Triangle,
    Pulse,
    Noise
};

// Register with MetaSounds
DECLARE_METASOUND_ENUM(EOscillatorWaveform, EOscillatorWaveform::Sine,
    METASOUNDSTANDARDNODES_API,
    FEnumOscillatorWaveform,
    FEnumOscillatorWaveformInfo,
    FEnumOscillatorWaveformReadRef,
    FEnumOscillatorWaveformWriteRef);

DEFINE_METASOUND_ENUM_BEGIN(EOscillatorWaveform, FEnumOscillatorWaveform, "OscillatorWaveform")
    DEFINE_METASOUND_ENUM_ENTRY(EOscillatorWaveform::Sine, "Sine", "Sine wave"),
    DEFINE_METASOUND_ENUM_ENTRY(EOscillatorWaveform::Saw, "Saw", "Sawtooth wave"),
    DEFINE_METASOUND_ENUM_ENTRY(EOscillatorWaveform::Triangle, "Triangle", "Triangle wave"),
    DEFINE_METASOUND_ENUM_ENTRY(EOscillatorWaveform::Pulse, "Pulse", "Pulse wave (50% duty cycle)"),
    DEFINE_METASOUND_ENUM_ENTRY(EOscillatorWaveform::Noise, "Noise", "White noise")
DEFINE_METASOUND_ENUM_END()
```

### Use in Operator

```cpp
class FOscillatorOperator : public TExecutableOperator<FOscillatorOperator>
{
public:
    static FOscillatorOperator* CreateOperator(const FCreateOperatorParams& InParams, ...)
    {
        // Get enum input
        FEnumOscillatorWaveformReadRef WaveformIn =
            InputInterface.GetDataReadReference<FEnumOscillatorWaveform>("Waveform");

        return new FOscillatorOperator(InSettings, FreqIn, WaveformIn);
    }

    FOscillatorOperator(
        const FOperatorSettings& InSettings,
        const FFloatReadRef& InFreq,
        const FEnumOscillatorWaveformReadRef& InWaveform)
    : FrequencyInput(InFreq)
    , WaveformInput(InWaveform)
    , AudioOutput(FAudioBufferWriteRef::CreateNew(InSettings))
    , Phase(0.0f)
    , SampleRate(InSettings.GetSampleRate())
    {
    }

    virtual void Execute()
    {
        float* Buffer = AudioOutput->GetData();
        float Frequency = *FrequencyInput;
        EOscillatorWaveform Waveform = *WaveformInput; // Dereference enum

        for (int32 i = 0; i < NumFramesPerBlock; ++i)
        {
            // Generate waveform based on enum value
            switch (Waveform)
            {
                case EOscillatorWaveform::Sine:
                    Buffer[i] = FMath::Sin(Phase * 2.0f * PI);
                    break;
                case EOscillatorWaveform::Saw:
                    Buffer[i] = 2.0f * Phase - 1.0f;
                    break;
                case EOscillatorWaveform::Triangle:
                    Buffer[i] = 4.0f * FMath::Abs(Phase - 0.5f) - 1.0f;
                    break;
                case EOscillatorWaveform::Pulse:
                    Buffer[i] = Phase < 0.5f ? 1.0f : -1.0f;
                    break;
                case EOscillatorWaveform::Noise:
                    Buffer[i] = FMath::FRandRange(-1.0f, 1.0f);
                    break;
            }

            Phase += Frequency / SampleRate;
            if (Phase >= 1.0f) Phase -= 1.0f;
        }
    }

private:
    FFloatReadRef FrequencyInput;
    FEnumOscillatorWaveformReadRef WaveformInput;
    FAudioBufferWriteRef AudioOutput;
    float Phase;
    float SampleRate;
    int32 NumFramesPerBlock;
};
```

---

## 6. State Management Across Execute() Calls

### Oscillator Phase Example

```cpp
class FPhaseAccumulator
{
public:
    FPhaseAccumulator(float InSampleRate)
    : Phase(0.0f)
    , SampleRate(InSampleRate)
    {
    }

    float GenerateSample(float Frequency)
    {
        float Output = Phase;
        Phase += Frequency / SampleRate;
        if (Phase >= 1.0f) Phase -= 1.0f;
        return Output;
    }

    void Reset() { Phase = 0.0f; }

private:
    float Phase;
    float SampleRate;
};

class FOscillatorOperator : public TExecutableOperator<FOscillatorOperator>
{
public:
    FOscillatorOperator(const FOperatorSettings& InSettings, ...)
    : PhaseAccum(InSettings.GetSampleRate()) // Initialize with sample rate
    {
    }

    virtual void Reset(const IOperator::FResetParams& InParams)
    {
        PhaseAccum.Reset(); // Reset state on graph change
        AudioOutput->Zero();
    }

    virtual void Execute()
    {
        float* Buffer = AudioOutput->GetData();
        float Freq = *FrequencyInput;

        for (int32 i = 0; i < NumFramesPerBlock; ++i)
        {
            float Phase = PhaseAccum.GenerateSample(Freq);
            Buffer[i] = FMath::Sin(Phase * 2.0f * PI);
        }
    }

private:
    FPhaseAccumulator PhaseAccum; // State persists across Execute() calls
};
```

### Envelope State Example

```cpp
class FADEnvelopeOperator : public TExecutableOperator<FADEnvelopeOperator>
{
private:
    enum class EEnvelopeStage
    {
        Idle,
        Attack,
        Decay
    };

    EEnvelopeStage CurrentStage;
    float EnvelopeLevel;
    float AttackRate;  // Level increment per sample
    float DecayRate;   // Level decrement per sample

public:
    virtual void Execute()
    {
        InputTrigger->ExecuteBlock(
            [&](int32 StartFrame, int32 EndFrame)
            {
                for (int32 i = StartFrame; i < EndFrame; ++i)
                {
                    // Update envelope state
                    switch (CurrentStage)
                    {
                        case EEnvelopeStage::Attack:
                            EnvelopeLevel += AttackRate;
                            if (EnvelopeLevel >= 1.0f)
                            {
                                EnvelopeLevel = 1.0f;
                                CurrentStage = EEnvelopeStage::Decay;
                            }
                            break;
                        case EEnvelopeStage::Decay:
                            EnvelopeLevel -= DecayRate;
                            if (EnvelopeLevel <= 0.0f)
                            {
                                EnvelopeLevel = 0.0f;
                                CurrentStage = EEnvelopeStage::Idle;
                            }
                            break;
                    }
                    OutputBuffer[i] = EnvelopeLevel;
                }
            },
            [&](int32 TriggerFrame)
            {
                // Trigger starts attack phase
                CurrentStage = EEnvelopeStage::Attack;
                EnvelopeLevel = 0.0f;
                OutputBuffer[TriggerFrame] = 0.0f;
            }
        );
    }
};
```

---

## 7. Sample Rate and Block Size Access

### From FOperatorSettings

```cpp
class FMyOperator : public TExecutableOperator<FMyOperator>
{
public:
    FMyOperator(const FOperatorSettings& InSettings, ...)
    : SampleRate(InSettings.GetSampleRate())
    , NumFramesPerBlock(InSettings.GetNumFramesPerBlock())
    {
        // Typical values:
        // SampleRate: 48000.0f (or 44100.0f)
        // NumFramesPerBlock: 256, 512, or 1024 (configurable per-platform)

        // Use for time-based calculations
        SecondsPerFrame = 1.0f / SampleRate;
    }

private:
    float SampleRate;         // Samples per second
    int32 NumFramesPerBlock;  // Samples per Execute() call
    float SecondsPerFrame;    // Time per sample
};
```

### Typical Use Cases

```cpp
// Convert frequency to phase increment
float PhaseIncrement = Frequency / SampleRate;

// Convert time (seconds) to sample count
int32 DelaySamples = FMath::RoundToInt(DelayTimeSeconds * SampleRate);

// Convert BPM to samples per beat
float SamplesPerBeat = (60.0f / BPM) * SampleRate;

// Convert milliseconds to samples
int32 AttackSamples = FMath::RoundToInt((AttackTimeMs / 1000.0f) * SampleRate);
```

---

## 8. Engine Source Code Examples

### Where to Find Complex DSP Nodes

**Path (UE 5.7):**
```
Engine/Plugins/Runtime/Metasound/Source/MetasoundStandardNodes/Private/
```

### Recommended Study Examples

| Node | File | Demonstrates |
|------|------|--------------|
| **Sine Oscillator** | `MetasoundSineNode.cpp` | Phase accumulation, sample rate usage |
| **Biquad Filter** | `MetasoundBiquadFilterNode.cpp` | State variables, enum pins (filter type) |
| **ADSR Envelope** | `MetasoundEnvelopeFollowerNode.cpp` | Multi-stage state machine, trigger handling |
| **Trigger On Threshold** | `MetasoundTriggerOnThresholdNode.cpp` | Audio→Trigger conversion, sample-accurate output |
| **Stereo Delay** | `MetasoundDelayNode.cpp` | Stereo processing, ring buffer state |
| **Random Get** | `MetasoundRandomNode.cpp` | Trigger input, array output, stateful RNG |
| **Wave Player** | `MetasoundWavePlayerNode.cpp` | Asset references, looping, playback state |
| **LFO** | `MetasoundLFONode.cpp` | Waveform enum, phase-based synthesis |

### Key Files for API Understanding

| File | Contains |
|------|----------|
| `MetasoundNodeRegistrationMacro.h` | METASOUND_REGISTER_NODE, METASOUND_PARAM macros |
| `MetasoundExecutableOperator.h` | TExecutableOperator base class |
| `MetasoundDataReference.h` | TDataReadReference, TDataWriteReference |
| `MetasoundAudioBuffer.h` | FAudioBuffer, FAudioBufferReadRef, FAudioBufferWriteRef |
| `MetasoundTrigger.h` | FTrigger, ExecuteBlock(), TriggerFrame() |
| `MetasoundEnum.h` | DECLARE_METASOUND_ENUM, DEFINE_METASOUND_ENUM macros |
| `MetasoundVertex.h` | Input/output pin definitions |

---

## 9. Registering Multiple Nodes from One Plugin

### Pattern 1: One .cpp File Per Node (Recommended)

```
UEAudioMCP/
├── Source/
│   └── UEAudioMCP/
│       ├── Private/
│       │   ├── Nodes/
│       │   │   ├── MyOscillatorNode.cpp       // METASOUND_REGISTER_NODE(FOscillator)
│       │   │   ├── MyFilterNode.cpp           // METASOUND_REGISTER_NODE(FFilter)
│       │   │   ├── MyEnvelopeNode.cpp         // METASOUND_REGISTER_NODE(FEnvelope)
│       │   │   └── MySequencerNode.cpp        // METASOUND_REGISTER_NODE(FSequencer)
```

Each .cpp file calls `METASOUND_REGISTER_NODE()` at the bottom. The MetaSound module automatically discovers and registers all nodes at plugin load.

### Pattern 2: Batch Registration in Module Startup (Alternative)

```cpp
// In UEAudioMCPModule.cpp
#include "MyOscillatorNode.h"
#include "MyFilterNode.h"

void FUEAudioMCPModule::StartupModule()
{
    // Register TCP server (existing code)
    RegisterCommands();
    TcpServer = MakeUnique<FAudioMCPTcpServer>(9877, Dispatcher.Get());
    TcpServer->Start();

    // MetaSound nodes auto-register via METASOUND_REGISTER_NODE macro
    // No manual registration needed if using macros
}
```

**Important:** The `METASOUND_REGISTER_NODE()` macro uses static initialization to auto-register nodes. You don't need to manually call registration functions if you use the macro.

---

## 10. FNodeFacade / METASOUND_REGISTER_NODE Pattern (UE 5.7)

### Complete Node Template with Metadata

```cpp
// MyGainNode.cpp
#include "MetasoundNodeRegistrationMacro.h"
#include "MetasoundExecutableOperator.h"
#include "MetasoundPrimitives.h"
#include "MetasoundAudioBuffer.h"
#include "MetasoundParamHelper.h"
#include "MetasoundStandardNodesCategories.h"

namespace Metasound
{
    // 1. Define parameter names and tooltips
    namespace MyGainNodeNames
    {
        METASOUND_PARAM(InParamAudio, "In", "Audio input")
        METASOUND_PARAM(InParamGain, "Gain", "Volume multiplier (0-1)")
        METASOUND_PARAM(OutParamAudio, "Out", "Processed audio output")
    }

    // 2. Operator implementation (see section 2)
    class FMyGainOperator : public TExecutableOperator<FMyGainOperator>
    {
        // ... (full implementation from section 2)
    };

    // 3. Node interface
    class FMyGainNode : public FNodeFacade
    {
    public:
        FMyGainNode(const FNodeInitData& InitData)
        : FNodeFacade(InitData.InstanceName, InitData.InstanceID, TFacadeOperatorClass<FMyGainOperator>())
        {
        }
    };

    // 4. Registration with metadata
    METASOUND_REGISTER_NODE(FMyGainNode)
    {
        using namespace MyGainNodeNames;

        FNodeClassMetadata Info;
        Info.ClassName = FMetasoundFrontendClassName("UE", "MyGain", "");
        Info.MajorVersion = 1;
        Info.MinorVersion = 0;
        Info.DisplayName = INVTEXT("My Gain");
        Info.Description = INVTEXT("Multiplies audio signal by gain value");
        Info.Author = PluginAuthor;
        Info.PromptIfMissing = PluginNodeMissingPrompt;
        Info.DefaultInterface = GetVertexInterface();
        Info.CategoryHierarchy = { NodeCategories::Dynamics };
        Info.Keywords = { INVTEXT("volume"), INVTEXT("gain"), INVTEXT("multiply") };

        return Info;
    }
}
```

### Vertex Interface (Input/Output Definitions)

Add to the node class:

```cpp
class FMyGainNode : public FNodeFacade
{
public:
    static FVertexInterface GetVertexInterface()
    {
        using namespace MyGainNodeNames;

        static const FVertexInterface Interface(
            FInputVertexInterface(
                TInputDataVertex<FAudioBuffer>(METASOUND_GET_PARAM_NAME_AND_METADATA(InParamAudio)),
                TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InParamGain), 1.0f) // Default: 1.0
            ),
            FOutputVertexInterface(
                TOutputDataVertex<FAudioBuffer>(METASOUND_GET_PARAM_NAME_AND_METADATA(OutParamAudio))
            )
        );

        return Interface;
    }

    FMyGainNode(const FNodeInitData& InitData)
    : FNodeFacade(InitData.InstanceName, InitData.InstanceID, TFacadeOperatorClass<FMyGainOperator>())
    {
    }
};
```

### Category Constants

Use built-in categories from `MetasoundStandardNodesCategories.h`:

```cpp
namespace NodeCategories
{
    const FName Dynamics("Dynamics");
    const FName Envelopes("Envelopes");
    const FName Filters("Filters");
    const FName Generators("Generators");
    const FName IO("IO");
    const FName Math("Math");
    const FName Mixing("Mixing");
    const FName Music("Music");
    const FName Spatialization("Spatialization");
    const FName Triggers("Triggers");
}
```

Or define custom categories:

```cpp
Info.CategoryHierarchy = { INVTEXT("Custom"), INVTEXT("Synthesizers") };
```

---

## Summary: Complete Custom Node Checklist

### 1. Build.cs Setup
- ✅ Add `MetasoundGraphCore` (already in UEAudioMCP.Build.cs)
- ✅ Add `MetasoundFrontend` (already in UEAudioMCP.Build.cs)
- ✅ Add `AudioMixer` (already in UEAudioMCP.Build.cs)
- Optional: Add `SignalProcessing` for DSP utilities

### 2. Node Structure (.cpp file)
- ✅ Define parameter namespace with METASOUND_PARAM macros
- ✅ Implement FOperator class with Execute() and Reset()
- ✅ Implement CreateOperator() factory method
- ✅ Store state in private operator members (phase, envelope level, etc.)
- ✅ Implement FNodeFacade class with GetVertexInterface()
- ✅ Call METASOUND_REGISTER_NODE() with metadata

### 3. Pin Handling
- ✅ Audio: `FAudioBufferReadRef` (input), `FAudioBufferWriteRef` (output)
- ✅ Float: `FFloatReadRef`, `FFloatWriteRef`
- ✅ Trigger: `FTriggerReadRef` + ExecuteBlock(), `FTriggerWriteRef` + TriggerFrame()
- ✅ Enum: Define with DECLARE_METASOUND_ENUM, use `TEnumReadRef<EMyEnum>`

### 4. Sample Rate Access
- ✅ Store from constructor: `SampleRate = InSettings.GetSampleRate()`
- ✅ Store block size: `NumFramesPerBlock = InSettings.GetNumFramesPerBlock()`

### 5. Reference Existing Nodes
- ✅ Study `MetasoundStandardNodes/Private/` for examples
- ✅ Start with simple nodes (Sine, Gain) before complex (Filter, Envelope)

---

## Sources

- [Creating MetaSound Nodes in C++ Quickstart | Tutorial](https://dev.epicgames.com/community/learning/tutorials/ry7p/unreal-engine-creating-metasound-nodes-in-c-quickstart)
- [MetaSounds Reference Guide | UE 5.7 Documentation](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-reference-guide-in-unreal-engine)
- [MetaSounds: The Next Generation Sound Sources | UE 5.7](https://dev.epicgames.com/documentation/en-us/unreal-engine/metasounds-the-next-generation-sound-sources-in-unreal-engine)
- [GitHub - matthewscharles/metasound-branches](https://github.com/matthewscharles/metasound-branches)
- [GitHub - alexirae/unreal-audio-dsp-template-UE5](https://github.com/alexirae/unreal-audio-dsp-template-UE5)
- [GitHub - alexirae/unreal-audio-dsp-collection-UE5](https://github.com/alexirae/unreal-audio-dsp-collection-UE5)
- [UE5 metasounds stuff - GitHub Gist](https://gist.github.com/mattetti/e89739a006591289e72c5252da1de877)
- [Template for Creating MetaSound Nodes in C++](https://dev.epicgames.com/community/snippets/G1j/template-for-creating-metasound-nodes-in-c)
- Unreal Engine 5.7 Source Code: `Engine/Plugins/Runtime/Metasound/Source/MetasoundStandardNodes/`

---

## Metadata

<meta>
research-date: 2026-02-08
confidence: high
version-checked: UE 5.7
code-verified: pattern-based (no compilation test)
sources: 20+ (Epic docs, GitHub repos, UE5 source headers)
</meta>
