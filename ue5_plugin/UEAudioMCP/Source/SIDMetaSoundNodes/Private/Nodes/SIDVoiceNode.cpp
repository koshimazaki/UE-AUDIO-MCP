// Copyright UE Audio MCP Project. All Rights Reserved.
// SID Voice Node — ReSID SIDKIT Edition
// Convenience combo: Oscillator x Envelope in a single node.
// Wraps reSID WaveformGenerator + EnvelopeGenerator with proper voice output math.

#include "SIDNodeEnums.h"

#include "MetasoundExecutableOperator.h"
#include "MetasoundNodeRegistrationMacro.h"
#include "MetasoundParamHelper.h"
#include "MetasoundPrimitives.h"
#include "MetasoundAudioBuffer.h"
#include "MetasoundOperatorSettings.h"
#include "MetasoundTrigger.h"
#include "MetasoundFacade.h"
#include "MetasoundVertex.h"

#define RESID_HEADER_ONLY
THIRD_PARTY_INCLUDES_START
#include "siddefs.h"
#include "voice.h"
THIRD_PARTY_INCLUDES_END

#define LOCTEXT_NAMESPACE "SIDMetaSoundNodes"

namespace Metasound
{
	namespace SIDVoiceNodeNames
	{
		METASOUND_PARAM(InGate,      "Gate",        "Note on/off trigger (toggles gate)")
		METASOUND_PARAM(InFrequency, "Frequency",   "Oscillator frequency in Hz")
		METASOUND_PARAM(InPulseWidth,"Pulse Width",  "Pulse width 0.0-1.0")
		METASOUND_PARAM(InWaveform,  "Waveform",    "Saw, Triangle, Pulse, Noise, or combined")
		METASOUND_PARAM(InAttack,    "Attack",      "Attack rate 0-15")
		METASOUND_PARAM(InDecay,     "Decay",       "Decay rate 0-15")
		METASOUND_PARAM(InSustain,   "Sustain",     "Sustain level 0-15")
		METASOUND_PARAM(InRelease,   "Release",     "Release rate 0-15")
		METASOUND_PARAM(InChipModel, "Chip Model",  "MOS 6581 or MOS 8580")
		METASOUND_PARAM(OutAudio,    "Out",         "Voice output: Waveform × Envelope")
	}

	class FSIDVoiceOperator : public TExecutableOperator<FSIDVoiceOperator>
	{
	public:
		static const FNodeClassMetadata& GetNodeInfo()
		{
			auto InitNodeInfo = []() -> FNodeClassMetadata
			{
				FNodeClassMetadata Info;
				Info.ClassName        = { TEXT("UE"), TEXT("SID Voice"), TEXT("Audio") };
				Info.MajorVersion     = 1;
				Info.MinorVersion     = 0;
				Info.DisplayName      = LOCTEXT("SIDVoiceDisplayName", "SID Voice");
				Info.Description      = LOCTEXT("SIDVoiceDesc", "Complete SID voice: oscillator × envelope. Combines waveform generation with ADSR in a single node for quick patching.");
				Info.Author           = TEXT("Koshi Mazaki");
				Info.PromptIfMissing  = LOCTEXT("SIDVoicePrompt", "SID Voice");
				Info.DefaultInterface = GetVertexInterface();
				Info.CategoryHierarchy = { LOCTEXT("SIDKITCategory", "ReSID SIDKIT Edition") };
				return Info;
			};
			static const FNodeClassMetadata Info = InitNodeInfo();
			return Info;
		}

		static const FVertexInterface& GetVertexInterface()
		{
			using namespace SIDVoiceNodeNames;
			static const FVertexInterface Interface(
				FInputVertexInterface({
					TInputDataVertex<FTrigger>(METASOUND_GET_PARAM_NAME_AND_METADATA(InGate)),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InFrequency), 440.0f),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InPulseWidth), 0.5f),
					TInputDataVertex<FEnumSIDWaveform>(METASOUND_GET_PARAM_NAME_AND_METADATA(InWaveform)),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InAttack), 0),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InDecay), 9),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InSustain), 0),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InRelease), 9),
					TInputDataVertex<FEnumSIDChipModel>(METASOUND_GET_PARAM_NAME_AND_METADATA(InChipModel)),
				}),
				FOutputVertexInterface({
					TOutputDataVertex<FAudioBuffer>(METASOUND_GET_PARAM_NAME_AND_METADATA(OutAudio)),
				})
			);
			return Interface;
		}

		static TUniquePtr<IOperator> CreateOperator(const FBuildOperatorParams& InParams, FBuildResults& OutResults)
		{
			const FInputVertexInterfaceData& InputData = InParams.InputData;
			using namespace SIDVoiceNodeNames;

			FTriggerReadRef GateIn = InputData.GetOrCreateDefaultDataReadReference<FTrigger>(METASOUND_GET_PARAM_NAME(InGate), InParams.OperatorSettings);
			FFloatReadRef FreqIn   = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InFrequency), InParams.OperatorSettings);
			FFloatReadRef PWIn     = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InPulseWidth), InParams.OperatorSettings);
			FEnumSIDWaveformReadRef WaveIn = InputData.GetOrCreateDefaultDataReadReference<FEnumSIDWaveform>(METASOUND_GET_PARAM_NAME(InWaveform), InParams.OperatorSettings);
			FInt32ReadRef AttIn    = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InAttack), InParams.OperatorSettings);
			FInt32ReadRef DecIn    = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InDecay), InParams.OperatorSettings);
			FInt32ReadRef SusIn    = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InSustain), InParams.OperatorSettings);
			FInt32ReadRef RelIn    = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InRelease), InParams.OperatorSettings);
			FEnumSIDChipModelReadRef ChipIn = InputData.GetOrCreateDefaultDataReadReference<FEnumSIDChipModel>(METASOUND_GET_PARAM_NAME(InChipModel), InParams.OperatorSettings);

			return MakeUnique<FSIDVoiceOperator>(InParams.OperatorSettings, GateIn, FreqIn, PWIn, WaveIn, AttIn, DecIn, SusIn, RelIn, ChipIn);
		}

		FSIDVoiceOperator(
			const FOperatorSettings& InSettings,
			const FTriggerReadRef& InGate,
			const FFloatReadRef& InFrequency,
			const FFloatReadRef& InPulseWidth,
			const FEnumSIDWaveformReadRef& InWaveform,
			const FInt32ReadRef& InAttack,
			const FInt32ReadRef& InDecay,
			const FInt32ReadRef& InSustain,
			const FInt32ReadRef& InRelease,
			const FEnumSIDChipModelReadRef& InChipModel)
			: GateInput(InGate)
			, FrequencyInput(InFrequency)
			, PulseWidthInput(InPulseWidth)
			, WaveformInput(InWaveform)
			, AttackInput(InAttack)
			, DecayInput(InDecay)
			, SustainInput(InSustain)
			, ReleaseInput(InRelease)
			, ChipModelInput(InChipModel)
			, AudioOutput(FAudioBufferWriteRef::CreateNew(InSettings))
			, SampleRate(InSettings.GetSampleRate())
		{
			SIDVoice.set_chip_model(MOS6581);
			// Voice needs a sync source (itself for standalone use)
			SIDVoice.wave.set_sync_source(&SIDVoice.wave);
			SIDVoice.reset();
		}

		FDataReferenceCollection GetInputs() const override
		{
			using namespace SIDVoiceNodeNames;
			FDataReferenceCollection Inputs;
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InGate), GateInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InFrequency), FrequencyInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InPulseWidth), PulseWidthInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InWaveform), WaveformInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InAttack), AttackInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InDecay), DecayInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InSustain), SustainInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InRelease), ReleaseInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InChipModel), ChipModelInput);
			return Inputs;
		}

		FDataReferenceCollection GetOutputs() const override
		{
			using namespace SIDVoiceNodeNames;
			FDataReferenceCollection Outputs;
			Outputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(OutAudio), AudioOutput);
			return Outputs;
		}

		void Execute()
		{
			FAudioBuffer& OutBuffer = *AudioOutput;
			const int32 NumSamples = OutBuffer.Num();

			// Update chip model
			ESIDChipModel ChipModel = *ChipModelInput;
			chip_model Model = (ChipModel == ESIDChipModel::MOS6581) ? MOS6581 : MOS8580;
			SIDVoice.set_chip_model(Model);

			// Update frequency
			const float SIDClockRate = 985248.0f;
			float FreqHz = FMath::Clamp(*FrequencyInput, 0.1f, 20000.0f);
			reg24 SIDFreq = static_cast<reg24>((FreqHz * 16777216.0f) / SIDClockRate);
			SIDVoice.wave.writeFREQ_LO(SIDFreq & 0xFF);
			SIDVoice.wave.writeFREQ_HI((SIDFreq >> 8) & 0xFF);

			// Update pulse width
			float PW = FMath::Clamp(*PulseWidthInput, 0.0f, 1.0f);
			reg12 PWValue = static_cast<reg12>(PW * 4095.0f);
			SIDVoice.wave.writePW_LO(PWValue & 0xFF);
			SIDVoice.wave.writePW_HI((PWValue >> 8) & 0x0F);

			// Update ADSR
			int32 A = FMath::Clamp(*AttackInput, 0, 15);
			int32 D = FMath::Clamp(*DecayInput, 0, 15);
			int32 S = FMath::Clamp(*SustainInput, 0, 15);
			int32 R = FMath::Clamp(*ReleaseInput, 0, 15);
			SIDVoice.envelope.writeATTACK_DECAY((A << 4) | D);
			SIDVoice.envelope.writeSUSTAIN_RELEASE((S << 4) | R);

			// Map waveform enum to control register bits
			ESIDWaveform Wave = *WaveformInput;
			reg8 WaveBits = 0;
			switch (Wave)
			{
			case ESIDWaveform::Triangle:    WaveBits = 0x10; break;
			case ESIDWaveform::Sawtooth:    WaveBits = 0x20; break;
			case ESIDWaveform::Pulse:       WaveBits = 0x40; break;
			case ESIDWaveform::Noise:       WaveBits = 0x80; break;
			case ESIDWaveform::SawTri:      WaveBits = 0x30; break;
			case ESIDWaveform::PulseSaw:    WaveBits = 0x60; break;
			case ESIDWaveform::PulseTri:    WaveBits = 0x50; break;
			case ESIDWaveform::PulseSawTri: WaveBits = 0x70; break;
			}

			const float CyclesPerSampleF = SIDClockRate / SampleRate;
			float* OutputData = OutBuffer.GetData();

			// Process triggers for gate control
			GateInput->ExecuteBlock(
				[this, &OutputData, WaveBits, CyclesPerSampleF](int32 StartFrame, int32 EndFrame)
				{
					// No trigger — just generate audio
					GenerateSamples(OutputData, StartFrame, EndFrame, WaveBits, CyclesPerSampleF);
				},
				[this, &OutputData, WaveBits, CyclesPerSampleF](int32 StartFrame, int32 EndFrame)
				{
					// Trigger — toggle gate
					bGateOn = !bGateOn;
					reg8 ControlReg = WaveBits | (bGateOn ? 0x01 : 0x00);
					SIDVoice.writeCONTROL_REG(ControlReg);
					GenerateSamples(OutputData, StartFrame, EndFrame, WaveBits, CyclesPerSampleF);
				}
			);
		}

		void Reset(const IOperator::FResetParams& InParams)
		{
			SIDVoice.reset();
			SIDVoice.wave.set_sync_source(&SIDVoice.wave);
			CycleAccumulator = 0.0f;
			bGateOn = false;
		}

	private:
		void GenerateSamples(float* OutputData, int32 StartFrame, int32 EndFrame, reg8 WaveBits, float CyclesPerSampleF)
		{
			for (int32 i = StartFrame; i < EndFrame; ++i)
			{
				CycleAccumulator += CyclesPerSampleF;
				int32 WholeCycles = static_cast<int32>(CycleAccumulator);
				CycleAccumulator -= static_cast<float>(WholeCycles);

				// Clock voice (both wave and envelope)
				SIDVoice.wave.clock(WholeCycles);
				SIDVoice.wave.set_waveform_output(WholeCycles);
				SIDVoice.envelope.clock(WholeCycles);

				// Voice output = waveform * envelope (SID math: 12-bit × 8-bit = 20-bit)
				// waveform output is 12-bit (0-4095), envelope is 8-bit (0-255)
				int32 WaveOut = SIDVoice.wave.output(); // 12-bit signed short
				int32 EnvOut = SIDVoice.envelope.output(); // 0-255

				// SID voice output: (waveform - 2048) * envelope
				// This gives a signed 20-bit result, normalize to [-1, 1]
				float VoiceOut = static_cast<float>((WaveOut - 2048) * EnvOut);
				OutputData[i] = VoiceOut / (2048.0f * 255.0f);
			}
		}

		FTriggerReadRef GateInput;
		FFloatReadRef FrequencyInput;
		FFloatReadRef PulseWidthInput;
		FEnumSIDWaveformReadRef WaveformInput;
		FInt32ReadRef AttackInput;
		FInt32ReadRef DecayInput;
		FInt32ReadRef SustainInput;
		FInt32ReadRef ReleaseInput;
		FEnumSIDChipModelReadRef ChipModelInput;
		FAudioBufferWriteRef AudioOutput;

		Voice SIDVoice;
		float SampleRate;
		float CycleAccumulator = 0.0f;
		bool bGateOn = false;
	};

	using FSIDVoiceNode = TNodeFacade<FSIDVoiceOperator>;

	METASOUND_REGISTER_NODE(FSIDVoiceNode)
}

#undef LOCTEXT_NAMESPACE
