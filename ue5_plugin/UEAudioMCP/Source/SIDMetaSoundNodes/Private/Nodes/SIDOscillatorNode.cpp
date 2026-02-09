// Copyright UE Audio MCP Project. All Rights Reserved.
// SID Oscillator Node — ReSID SIDKIT Edition
// 24-bit accumulator waveform generator with combined waveforms.
// Wraps reSID WaveformGenerator with fractional clock accumulator for sample-rate conversion.

#include "SIDNodeEnums.h"

#include "MetasoundExecutableOperator.h"
#include "MetasoundNodeRegistrationMacro.h"
#include "MetasoundParamHelper.h"
#include "MetasoundPrimitives.h"
#include "MetasoundAudioBuffer.h"
#include "MetasoundOperatorSettings.h"
#include "MetasoundFacade.h"
#include "MetasoundVertex.h"

#define RESID_HEADER_ONLY
THIRD_PARTY_INCLUDES_START
#include "siddefs.h"
#include "wave.h"
THIRD_PARTY_INCLUDES_END

#define LOCTEXT_NAMESPACE "SIDMetaSoundNodes"

namespace Metasound
{
	namespace SIDOscillatorNodeNames
	{
		METASOUND_PARAM(InFrequency,  "Frequency",       "Oscillator frequency in Hz (20-20000)")
		METASOUND_PARAM(InPulseWidth, "Pulse Width",     "Pulse width 0.0-1.0 (only affects Pulse waveform)")
		METASOUND_PARAM(InWaveform,   "Waveform",        "Waveform: Triangle, Sawtooth, Pulse, Noise, or combined")
		METASOUND_PARAM(InChipModel,  "Chip Model",      "MOS 6581 or MOS 8580 (affects combined waveform tables)")
		METASOUND_PARAM(OutAudio,     "Out",             "12-bit waveform output normalized to float [-1, 1]")
	}

	class FSIDOscillatorOperator : public TExecutableOperator<FSIDOscillatorOperator>
	{
	public:
		static const FNodeClassMetadata& GetNodeInfo()
		{
			auto InitNodeInfo = []() -> FNodeClassMetadata
			{
				FNodeClassMetadata Info;
				Info.ClassName        = { TEXT("UE"), TEXT("SID Oscillator"), TEXT("Audio") };
				Info.MajorVersion     = 1;
				Info.MinorVersion     = 0;
				Info.DisplayName      = LOCTEXT("SIDOscDisplayName", "SID Oscillator");
				Info.Description      = LOCTEXT("SIDOscDesc", "MOS 6581/8580 waveform generator. 24-bit accumulator with saw, triangle, pulse, noise, and combined waveforms from actual chip samples.");
				Info.Author           = TEXT("Koshi Mazaki");
				Info.PromptIfMissing  = LOCTEXT("SIDOscPrompt", "SID Oscillator");
				Info.DefaultInterface = GetVertexInterface();
				Info.CategoryHierarchy = { LOCTEXT("SIDKITCategory", "ReSID SIDKIT Edition") };
				return Info;
			};
			static const FNodeClassMetadata Info = InitNodeInfo();
			return Info;
		}

		static const FVertexInterface& GetVertexInterface()
		{
			using namespace SIDOscillatorNodeNames;
			static const FVertexInterface Interface(
				FInputVertexInterface({
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InFrequency), 440.0f),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InPulseWidth), 0.5f),
					TInputDataVertex<FEnumSIDWaveform>(METASOUND_GET_PARAM_NAME_AND_METADATA(InWaveform)),
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
			using namespace SIDOscillatorNodeNames;

			FFloatReadRef FreqIn = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InFrequency), InParams.OperatorSettings);
			FFloatReadRef PWIn   = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InPulseWidth), InParams.OperatorSettings);
			FEnumSIDWaveformReadRef WaveIn = InputData.GetOrCreateDefaultDataReadReference<FEnumSIDWaveform>(METASOUND_GET_PARAM_NAME(InWaveform), InParams.OperatorSettings);
			FEnumSIDChipModelReadRef ChipIn = InputData.GetOrCreateDefaultDataReadReference<FEnumSIDChipModel>(METASOUND_GET_PARAM_NAME(InChipModel), InParams.OperatorSettings);

			return MakeUnique<FSIDOscillatorOperator>(InParams.OperatorSettings, FreqIn, PWIn, WaveIn, ChipIn);
		}

		FSIDOscillatorOperator(
			const FOperatorSettings& InSettings,
			const FFloatReadRef& InFrequency,
			const FFloatReadRef& InPulseWidth,
			const FEnumSIDWaveformReadRef& InWaveform,
			const FEnumSIDChipModelReadRef& InChipModel)
			: FrequencyInput(InFrequency)
			, PulseWidthInput(InPulseWidth)
			, WaveformInput(InWaveform)
			, ChipModelInput(InChipModel)
			, AudioOutput(FAudioBufferWriteRef::CreateNew(InSettings))
			, SampleRate(InSettings.GetSampleRate())
		{
			// WaveformGenerator needs a sync source (itself for no-sync)
			WaveGen.set_sync_source(&WaveGen);
			WaveGen.set_chip_model(MOS6581);
			WaveGen.reset();
		}

		FDataReferenceCollection GetInputs() const override
		{
			using namespace SIDOscillatorNodeNames;
			FDataReferenceCollection Inputs;
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InFrequency), FrequencyInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InPulseWidth), PulseWidthInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InWaveform), WaveformInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InChipModel), ChipModelInput);
			return Inputs;
		}

		FDataReferenceCollection GetOutputs() const override
		{
			using namespace SIDOscillatorNodeNames;
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
			WaveGen.set_chip_model(Model);

			// Convert Hz to SID frequency register value
			// SID freq register: Fout = (Fn * Fclk) / 16777216
			// So Fn = (Fout * 16777216) / Fclk
			const float SIDClockRate = 985248.0f;
			float FreqHz = FMath::Clamp(*FrequencyInput, 0.1f, 20000.0f);
			reg24 SIDFreq = static_cast<reg24>((FreqHz * 16777216.0f) / SIDClockRate);
			WaveGen.writeFREQ_LO(SIDFreq & 0xFF);
			WaveGen.writeFREQ_HI((SIDFreq >> 8) & 0xFF);

			// Update pulse width (0.0-1.0 → 12-bit register 0-4095)
			float PW = FMath::Clamp(*PulseWidthInput, 0.0f, 1.0f);
			reg12 PWValue = static_cast<reg12>(PW * 4095.0f);
			WaveGen.writePW_LO(PWValue & 0xFF);
			WaveGen.writePW_HI((PWValue >> 8) & 0x0F);

			// Update waveform — map enum to SID control register bits
			ESIDWaveform Wave = *WaveformInput;
			reg8 ControlBits = 0;
			switch (Wave)
			{
			case ESIDWaveform::Triangle:    ControlBits = 0x11; break; // Bit 4 + gate
			case ESIDWaveform::Sawtooth:    ControlBits = 0x21; break; // Bit 5 + gate
			case ESIDWaveform::Pulse:       ControlBits = 0x41; break; // Bit 6 + gate
			case ESIDWaveform::Noise:       ControlBits = 0x81; break; // Bit 7 + gate
			case ESIDWaveform::SawTri:      ControlBits = 0x31; break; // Bits 4+5 + gate
			case ESIDWaveform::PulseSaw:    ControlBits = 0x61; break; // Bits 5+6 + gate
			case ESIDWaveform::PulseTri:    ControlBits = 0x51; break; // Bits 4+6 + gate
			case ESIDWaveform::PulseSawTri: ControlBits = 0x71; break; // Bits 4+5+6 + gate
			}
			WaveGen.writeCONTROL_REG(ControlBits);

			// Generate audio
			const float SIDCyclesPerSample = SIDClockRate / SampleRate;
			float* OutputData = OutBuffer.GetData();

			for (int32 i = 0; i < NumSamples; ++i)
			{
				CycleAccumulator += SIDCyclesPerSample;
				int32 WholeCycles = static_cast<int32>(CycleAccumulator);
				CycleAccumulator -= static_cast<float>(WholeCycles);

				// Clock the waveform generator
				WaveGen.clock(WholeCycles);
				WaveGen.set_waveform_output(WholeCycles);

				// Get 12-bit waveform output, normalize to [-1, 1]
				// Output range is 0-4095 (12-bit unsigned), center at 2048
				short RawOutput = WaveGen.output();
				OutputData[i] = (static_cast<float>(RawOutput) - 2048.0f) / 2048.0f;
			}
		}

		void Reset(const IOperator::FResetParams& InParams)
		{
			WaveGen.reset();
			WaveGen.set_sync_source(&WaveGen);
			CycleAccumulator = 0.0f;
		}

	private:
		FFloatReadRef FrequencyInput;
		FFloatReadRef PulseWidthInput;
		FEnumSIDWaveformReadRef WaveformInput;
		FEnumSIDChipModelReadRef ChipModelInput;
		FAudioBufferWriteRef AudioOutput;

		WaveformGenerator WaveGen;
		float SampleRate;
		float CycleAccumulator = 0.0f;
	};

	using FSIDOscillatorNode = TNodeFacade<FSIDOscillatorOperator>;

	METASOUND_REGISTER_NODE(FSIDOscillatorNode)
}

#undef LOCTEXT_NAMESPACE
