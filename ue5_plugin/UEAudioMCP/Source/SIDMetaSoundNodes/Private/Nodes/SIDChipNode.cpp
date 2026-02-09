// Copyright UE Audio MCP Project. All Rights Reserved.
// SID Chip Node — ReSID SIDKIT Edition
// Full 3-voice MOS 6581/8580 with filter, FM cross-modulation,
// per-voice volume, and resonance boost. Wraps the complete SID16 class from reSID.

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

// Provide VERSION string before including reSID
#ifndef VERSION
#define VERSION "SIDKIT-UE5-1.0"
#endif

#define RESID_HEADER_ONLY
THIRD_PARTY_INCLUDES_START
#include "siddefs.h"
#include "sid.h"
THIRD_PARTY_INCLUDES_END

#define LOCTEXT_NAMESPACE "SIDMetaSoundNodes"

namespace Metasound
{
	namespace SIDChipNodeNames
	{
		// Per-voice inputs (×3)
		METASOUND_PARAM(InGate1,  "Gate 1",  "Voice 1 note on/off")
		METASOUND_PARAM(InGate2,  "Gate 2",  "Voice 2 note on/off")
		METASOUND_PARAM(InGate3,  "Gate 3",  "Voice 3 note on/off")
		METASOUND_PARAM(InFreq1,  "Freq 1",  "Voice 1 frequency in Hz")
		METASOUND_PARAM(InFreq2,  "Freq 2",  "Voice 2 frequency in Hz")
		METASOUND_PARAM(InFreq3,  "Freq 3",  "Voice 3 frequency in Hz")
		METASOUND_PARAM(InPW1,    "PW 1",    "Voice 1 pulse width 0.0-1.0")
		METASOUND_PARAM(InPW2,    "PW 2",    "Voice 2 pulse width 0.0-1.0")
		METASOUND_PARAM(InPW3,    "PW 3",    "Voice 3 pulse width 0.0-1.0")
		METASOUND_PARAM(InWave1,  "Wave 1",  "Voice 1 waveform")
		METASOUND_PARAM(InWave2,  "Wave 2",  "Voice 2 waveform")
		METASOUND_PARAM(InWave3,  "Wave 3",  "Voice 3 waveform")
		METASOUND_PARAM(InA1,     "A 1",     "Voice 1 Attack 0-15")
		METASOUND_PARAM(InD1,     "D 1",     "Voice 1 Decay 0-15")
		METASOUND_PARAM(InS1,     "S 1",     "Voice 1 Sustain 0-15")
		METASOUND_PARAM(InR1,     "R 1",     "Voice 1 Release 0-15")
		METASOUND_PARAM(InA2,     "A 2",     "Voice 2 Attack 0-15")
		METASOUND_PARAM(InD2,     "D 2",     "Voice 2 Decay 0-15")
		METASOUND_PARAM(InS2,     "S 2",     "Voice 2 Sustain 0-15")
		METASOUND_PARAM(InR2,     "R 2",     "Voice 2 Release 0-15")
		METASOUND_PARAM(InA3,     "A 3",     "Voice 3 Attack 0-15")
		METASOUND_PARAM(InD3,     "D 3",     "Voice 3 Decay 0-15")
		METASOUND_PARAM(InS3,     "S 3",     "Voice 3 Sustain 0-15")
		METASOUND_PARAM(InR3,     "R 3",     "Voice 3 Release 0-15")

		// Filter inputs
		METASOUND_PARAM(InFilterCutoff,    "Filter Cutoff",    "Filter cutoff 0.0-1.0")
		METASOUND_PARAM(InFilterResonance, "Filter Resonance", "Filter resonance 0.0-1.0")
		METASOUND_PARAM(InFilterMode,      "Filter Mode",      "LP, BP, HP, Notch, etc.")
		METASOUND_PARAM(InFilterRouting,   "Filter Routing",   "Bitmask: which voices route through filter (1-7)")

		// Global inputs
		METASOUND_PARAM(InVolume,    "Volume",     "Master volume 0.0-1.0")
		METASOUND_PARAM(InChipModel, "Chip Model", "MOS 6581 or MOS 8580")
		METASOUND_PARAM(InResBoost,  "Res Boost",  "Resonance boost 0.0-1.0 (SIDKIT extension)")

		// Outputs
		METASOUND_PARAM(OutAudio,  "Out",       "Mixed + filtered master output")
		METASOUND_PARAM(OutVoice1, "Voice 1 Out", "Voice 1 pre-filter output")
		METASOUND_PARAM(OutVoice2, "Voice 2 Out", "Voice 2 pre-filter output")
		METASOUND_PARAM(OutVoice3, "Voice 3 Out", "Voice 3 pre-filter output")
	}

	class FSIDChipOperator : public TExecutableOperator<FSIDChipOperator>
	{
	public:
		static const FNodeClassMetadata& GetNodeInfo()
		{
			auto InitNodeInfo = []() -> FNodeClassMetadata
			{
				FNodeClassMetadata Info;
				Info.ClassName        = { TEXT("UE"), TEXT("SID Chip"), TEXT("Audio") };
				Info.MajorVersion     = 1;
				Info.MinorVersion     = 0;
				Info.DisplayName      = LOCTEXT("SIDChipDisplayName", "SID Chip");
				Info.Description      = LOCTEXT("SIDChipDesc", "Complete MOS 6581/8580 SID chip emulation. 3 voices with oscillator+envelope, analog filter, FM cross-modulation, and per-voice volume (SIDKIT extensions).");
				Info.Author           = TEXT("Koshi Mazaki");
				Info.PromptIfMissing  = LOCTEXT("SIDChipPrompt", "SID Chip");
				Info.DefaultInterface = GetVertexInterface();
				Info.CategoryHierarchy = { LOCTEXT("SIDKITCategory", "ReSID SIDKIT Edition") };
				return Info;
			};
			static const FNodeClassMetadata Info = InitNodeInfo();
			return Info;
		}

		static const FVertexInterface& GetVertexInterface()
		{
			using namespace SIDChipNodeNames;
			static const FVertexInterface Interface(
				FInputVertexInterface({
					// Voice 1
					TInputDataVertex<FTrigger>(METASOUND_GET_PARAM_NAME_AND_METADATA(InGate1)),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InFreq1), 440.0f),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InPW1), 0.5f),
					TInputDataVertex<FEnumSIDWaveform>(METASOUND_GET_PARAM_NAME_AND_METADATA(InWave1)),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InA1), 0),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InD1), 9),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InS1), 0),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InR1), 9),
					// Voice 2
					TInputDataVertex<FTrigger>(METASOUND_GET_PARAM_NAME_AND_METADATA(InGate2)),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InFreq2), 440.0f),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InPW2), 0.5f),
					TInputDataVertex<FEnumSIDWaveform>(METASOUND_GET_PARAM_NAME_AND_METADATA(InWave2)),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InA2), 0),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InD2), 9),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InS2), 0),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InR2), 9),
					// Voice 3
					TInputDataVertex<FTrigger>(METASOUND_GET_PARAM_NAME_AND_METADATA(InGate3)),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InFreq3), 440.0f),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InPW3), 0.5f),
					TInputDataVertex<FEnumSIDWaveform>(METASOUND_GET_PARAM_NAME_AND_METADATA(InWave3)),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InA3), 0),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InD3), 9),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InS3), 0),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InR3), 9),
					// Filter
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InFilterCutoff), 0.5f),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InFilterResonance), 0.0f),
					TInputDataVertex<FEnumSIDFilterMode>(METASOUND_GET_PARAM_NAME_AND_METADATA(InFilterMode)),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InFilterRouting), 1),
					// Global
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InVolume), 1.0f),
					TInputDataVertex<FEnumSIDChipModel>(METASOUND_GET_PARAM_NAME_AND_METADATA(InChipModel)),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InResBoost), 0.0f),
				}),
				FOutputVertexInterface({
					TOutputDataVertex<FAudioBuffer>(METASOUND_GET_PARAM_NAME_AND_METADATA(OutAudio)),
					TOutputDataVertex<FAudioBuffer>(METASOUND_GET_PARAM_NAME_AND_METADATA(OutVoice1)),
					TOutputDataVertex<FAudioBuffer>(METASOUND_GET_PARAM_NAME_AND_METADATA(OutVoice2)),
					TOutputDataVertex<FAudioBuffer>(METASOUND_GET_PARAM_NAME_AND_METADATA(OutVoice3)),
				})
			);
			return Interface;
		}

		static TUniquePtr<IOperator> CreateOperator(const FBuildOperatorParams& InParams, FBuildResults& OutResults)
		{
			const FInputVertexInterfaceData& InputData = InParams.InputData;
			using namespace SIDChipNodeNames;

			// Voice 1
			FTriggerReadRef Gate1 = InputData.GetOrCreateDefaultDataReadReference<FTrigger>(METASOUND_GET_PARAM_NAME(InGate1), InParams.OperatorSettings);
			FFloatReadRef Freq1   = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InFreq1), InParams.OperatorSettings);
			FFloatReadRef PW1     = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InPW1), InParams.OperatorSettings);
			FEnumSIDWaveformReadRef Wave1 = InputData.GetOrCreateDefaultDataReadReference<FEnumSIDWaveform>(METASOUND_GET_PARAM_NAME(InWave1), InParams.OperatorSettings);
			FInt32ReadRef A1 = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InA1), InParams.OperatorSettings);
			FInt32ReadRef D1 = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InD1), InParams.OperatorSettings);
			FInt32ReadRef S1 = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InS1), InParams.OperatorSettings);
			FInt32ReadRef R1 = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InR1), InParams.OperatorSettings);
			// Voice 2
			FTriggerReadRef Gate2 = InputData.GetOrCreateDefaultDataReadReference<FTrigger>(METASOUND_GET_PARAM_NAME(InGate2), InParams.OperatorSettings);
			FFloatReadRef Freq2   = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InFreq2), InParams.OperatorSettings);
			FFloatReadRef PW2     = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InPW2), InParams.OperatorSettings);
			FEnumSIDWaveformReadRef Wave2 = InputData.GetOrCreateDefaultDataReadReference<FEnumSIDWaveform>(METASOUND_GET_PARAM_NAME(InWave2), InParams.OperatorSettings);
			FInt32ReadRef A2 = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InA2), InParams.OperatorSettings);
			FInt32ReadRef D2 = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InD2), InParams.OperatorSettings);
			FInt32ReadRef S2 = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InS2), InParams.OperatorSettings);
			FInt32ReadRef R2 = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InR2), InParams.OperatorSettings);
			// Voice 3
			FTriggerReadRef Gate3 = InputData.GetOrCreateDefaultDataReadReference<FTrigger>(METASOUND_GET_PARAM_NAME(InGate3), InParams.OperatorSettings);
			FFloatReadRef Freq3   = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InFreq3), InParams.OperatorSettings);
			FFloatReadRef PW3     = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InPW3), InParams.OperatorSettings);
			FEnumSIDWaveformReadRef Wave3 = InputData.GetOrCreateDefaultDataReadReference<FEnumSIDWaveform>(METASOUND_GET_PARAM_NAME(InWave3), InParams.OperatorSettings);
			FInt32ReadRef A3 = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InA3), InParams.OperatorSettings);
			FInt32ReadRef D3 = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InD3), InParams.OperatorSettings);
			FInt32ReadRef S3 = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InS3), InParams.OperatorSettings);
			FInt32ReadRef R3 = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InR3), InParams.OperatorSettings);
			// Filter
			FFloatReadRef FCut = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InFilterCutoff), InParams.OperatorSettings);
			FFloatReadRef FRes = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InFilterResonance), InParams.OperatorSettings);
			FEnumSIDFilterModeReadRef FMode = InputData.GetOrCreateDefaultDataReadReference<FEnumSIDFilterMode>(METASOUND_GET_PARAM_NAME(InFilterMode), InParams.OperatorSettings);
			FInt32ReadRef FRoute = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InFilterRouting), InParams.OperatorSettings);
			// Global
			FFloatReadRef Vol = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InVolume), InParams.OperatorSettings);
			FEnumSIDChipModelReadRef Chip = InputData.GetOrCreateDefaultDataReadReference<FEnumSIDChipModel>(METASOUND_GET_PARAM_NAME(InChipModel), InParams.OperatorSettings);
			FFloatReadRef RBoost = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InResBoost), InParams.OperatorSettings);

			return MakeUnique<FSIDChipOperator>(InParams.OperatorSettings,
				Gate1, Freq1, PW1, Wave1, A1, D1, S1, R1,
				Gate2, Freq2, PW2, Wave2, A2, D2, S2, R2,
				Gate3, Freq3, PW3, Wave3, A3, D3, S3, R3,
				FCut, FRes, FMode, FRoute, Vol, Chip, RBoost);
		}

		FSIDChipOperator(
			const FOperatorSettings& InSettings,
			// Voice 1
			const FTriggerReadRef& G1, const FFloatReadRef& F1, const FFloatReadRef& P1, const FEnumSIDWaveformReadRef& W1,
			const FInt32ReadRef& A1, const FInt32ReadRef& D1, const FInt32ReadRef& S1, const FInt32ReadRef& R1,
			// Voice 2
			const FTriggerReadRef& G2, const FFloatReadRef& F2, const FFloatReadRef& P2, const FEnumSIDWaveformReadRef& W2,
			const FInt32ReadRef& A2, const FInt32ReadRef& D2, const FInt32ReadRef& S2, const FInt32ReadRef& R2,
			// Voice 3
			const FTriggerReadRef& G3, const FFloatReadRef& F3, const FFloatReadRef& P3, const FEnumSIDWaveformReadRef& W3,
			const FInt32ReadRef& A3, const FInt32ReadRef& D3, const FInt32ReadRef& S3, const FInt32ReadRef& R3,
			// Filter + Global
			const FFloatReadRef& FCut, const FFloatReadRef& FRes, const FEnumSIDFilterModeReadRef& FMode,
			const FInt32ReadRef& FRoute, const FFloatReadRef& Vol, const FEnumSIDChipModelReadRef& Chip,
			const FFloatReadRef& RBoost)
			: GateInputs{G1, G2, G3}
			, FreqInputs{F1, F2, F3}
			, PWInputs{P1, P2, P3}
			, WaveInputs{W1, W2, W3}
			, AttInputs{A1, A2, A3}
			, DecInputs{D1, D2, D3}
			, SusInputs{S1, S2, S3}
			, RelInputs{R1, R2, R3}
			, FilterCutoffInput(FCut)
			, FilterResonanceInput(FRes)
			, FilterModeInput(FMode)
			, FilterRoutingInput(FRoute)
			, VolumeInput(Vol)
			, ChipModelInput(Chip)
			, ResBoostInput(RBoost)
			, MasterOutput(FAudioBufferWriteRef::CreateNew(InSettings))
			, VoiceOutputs{
				FAudioBufferWriteRef::CreateNew(InSettings),
				FAudioBufferWriteRef::CreateNew(InSettings),
				FAudioBufferWriteRef::CreateNew(InSettings)
			}
			, SampleRate(InSettings.GetSampleRate())
		{
			SID.reset();
			SID.set_chip_model(MOS6581);
			SID.set_sampling_parameters(985248.0f, SAMPLE_FAST, SampleRate);
			SID.enable_filter(true);
		}

		FDataReferenceCollection GetInputs() const override
		{
			using namespace SIDChipNodeNames;
			FDataReferenceCollection Inputs;
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InGate1), GateInputs[0]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InFreq1), FreqInputs[0]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InPW1), PWInputs[0]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InWave1), WaveInputs[0]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InA1), AttInputs[0]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InD1), DecInputs[0]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InS1), SusInputs[0]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InR1), RelInputs[0]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InGate2), GateInputs[1]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InFreq2), FreqInputs[1]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InPW2), PWInputs[1]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InWave2), WaveInputs[1]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InA2), AttInputs[1]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InD2), DecInputs[1]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InS2), SusInputs[1]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InR2), RelInputs[1]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InGate3), GateInputs[2]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InFreq3), FreqInputs[2]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InPW3), PWInputs[2]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InWave3), WaveInputs[2]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InA3), AttInputs[2]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InD3), DecInputs[2]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InS3), SusInputs[2]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InR3), RelInputs[2]);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InFilterCutoff), FilterCutoffInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InFilterResonance), FilterResonanceInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InFilterMode), FilterModeInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InFilterRouting), FilterRoutingInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InVolume), VolumeInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InChipModel), ChipModelInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InResBoost), ResBoostInput);
			return Inputs;
		}

		FDataReferenceCollection GetOutputs() const override
		{
			using namespace SIDChipNodeNames;
			FDataReferenceCollection Outputs;
			Outputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(OutAudio), MasterOutput);
			Outputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(OutVoice1), VoiceOutputs[0]);
			Outputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(OutVoice2), VoiceOutputs[1]);
			Outputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(OutVoice3), VoiceOutputs[2]);
			return Outputs;
		}

		void Execute()
		{
			const int32 NumSamples = MasterOutput->Num();
			const float SIDClockRate = 985248.0f;

			// Update chip model
			ESIDChipModel ChipModel = *ChipModelInput;
			chip_model Model = (ChipModel == ESIDChipModel::MOS6581) ? MOS6581 : MOS8580;
			if (Model != CurrentChipModel)
			{
				CurrentChipModel = Model;
				SID.set_chip_model(Model);
			}

			// Update resonance boost
			float ResBoost = FMath::Clamp(*ResBoostInput, 0.0f, 1.0f);
			SID.setResBoost(static_cast<int>(ResBoost * 255.0f));
			SID.enableResBoost(ResBoost > 0.001f);

			// Update per-voice registers via SID register writes
			for (int32 v = 0; v < 3; ++v)
			{
				int32 RegBase = v * 7; // SID registers: voice 0=0x00, voice 1=0x07, voice 2=0x0E

				// Frequency
				float FreqHz = FMath::Clamp(*FreqInputs[v], 0.1f, 20000.0f);
				reg24 SIDFreq = static_cast<reg24>((FreqHz * 16777216.0f) / SIDClockRate);
				SID.write(RegBase + 0, SIDFreq & 0xFF);        // Freq LO
				SID.write(RegBase + 1, (SIDFreq >> 8) & 0xFF); // Freq HI

				// Pulse width
				float PW = FMath::Clamp(*PWInputs[v], 0.0f, 1.0f);
				reg12 PWVal = static_cast<reg12>(PW * 4095.0f);
				SID.write(RegBase + 2, PWVal & 0xFF);          // PW LO
				SID.write(RegBase + 3, (PWVal >> 8) & 0x0F);   // PW HI

				// Waveform + gate (control register)
				ESIDWaveform Wave = *WaveInputs[v];
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
				SID.write(RegBase + 4, WaveBits | (bGateOn[v] ? 0x01 : 0x00));

				// ADSR
				int32 A = FMath::Clamp(*AttInputs[v], 0, 15);
				int32 D = FMath::Clamp(*DecInputs[v], 0, 15);
				int32 S = FMath::Clamp(*SusInputs[v], 0, 15);
				int32 R = FMath::Clamp(*RelInputs[v], 0, 15);
				SID.write(RegBase + 5, (A << 4) | D);
				SID.write(RegBase + 6, (S << 4) | R);
			}

			// Filter cutoff (register 0x15-0x16)
			float Cutoff = FMath::Clamp(*FilterCutoffInput, 0.0f, 1.0f);
			reg12 FCValue = static_cast<reg12>(Cutoff * 2047.0f);
			SID.write(0x15, FCValue & 0x07);       // FC LO (3 bits)
			SID.write(0x16, FCValue >> 3);          // FC HI (8 bits)

			// Filter resonance + routing (register 0x17)
			float Resonance = FMath::Clamp(*FilterResonanceInput, 0.0f, 1.0f);
			reg8 ResValue = static_cast<reg8>(Resonance * 15.0f);
			int32 Routing = FMath::Clamp(*FilterRoutingInput, 0, 15);
			SID.write(0x17, (ResValue << 4) | (Routing & 0x0F));

			// Filter mode + volume (register 0x18)
			ESIDFilterMode FilterMode = *FilterModeInput;
			reg8 ModeBits = 0;
			switch (FilterMode)
			{
			case ESIDFilterMode::LowPass:  ModeBits = 0x10; break;
			case ESIDFilterMode::BandPass: ModeBits = 0x20; break;
			case ESIDFilterMode::HighPass: ModeBits = 0x40; break;
			case ESIDFilterMode::Notch:    ModeBits = 0x50; break;
			case ESIDFilterMode::LowBand:  ModeBits = 0x30; break;
			case ESIDFilterMode::BandHigh: ModeBits = 0x60; break;
			case ESIDFilterMode::All:      ModeBits = 0x70; break;
			}
			float Volume = FMath::Clamp(*VolumeInput, 0.0f, 1.0f);
			reg8 VolValue = static_cast<reg8>(Volume * 15.0f);
			SID.write(0x18, ModeBits | VolValue);

			// Process gate triggers for all 3 voices
			// We process voice 1 triggers as the master clock driver
			float* MasterData = MasterOutput->GetData();
			float* V1Data = VoiceOutputs[0]->GetData();
			float* V2Data = VoiceOutputs[1]->GetData();
			float* V3Data = VoiceOutputs[2]->GetData();

			const float CyclesPerSampleF = SIDClockRate / SampleRate;

			// Check for gate toggles on each voice
			for (int32 v = 0; v < 3; ++v)
			{
				GateInputs[v]->ExecuteBlock(
					[](int32, int32) {},
					[this, v](int32, int32)
					{
						bGateOn[v] = !bGateOn[v];
						int32 RegBase = v * 7;
						// Re-write control register with updated gate
						ESIDWaveform Wave = *WaveInputs[v];
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
						SID.write(RegBase + 4, WaveBits | (bGateOn[v] ? 0x01 : 0x00));
					}
				);
			}

			// Generate audio samples
			for (int32 i = 0; i < NumSamples; ++i)
			{
				CycleAccumulator += CyclesPerSampleF;
				int32 WholeCycles = static_cast<int32>(CycleAccumulator);
				CycleAccumulator -= static_cast<float>(WholeCycles);

				SID.clock(WholeCycles);

				// Master output
				MasterData[i] = static_cast<float>(SID.output()) / 32768.0f;

				// Per-voice outputs (SIDKIT monitoring API)
				V1Data[i] = static_cast<float>(SID.getVoiceOutput(0)) / 32768.0f;
				V2Data[i] = static_cast<float>(SID.getVoiceOutput(1)) / 32768.0f;
				V3Data[i] = static_cast<float>(SID.getVoiceOutput(2)) / 32768.0f;
			}
		}

		void Reset(const IOperator::FResetParams& InParams)
		{
			SID.reset();
			SID.set_chip_model(CurrentChipModel);
			SID.set_sampling_parameters(985248.0f, SAMPLE_FAST, SampleRate);
			SID.enable_filter(true);
			CycleAccumulator = 0.0f;
			for (int32 v = 0; v < 3; ++v) bGateOn[v] = false;
		}

	private:
		// Voice inputs (×3)
		FTriggerReadRef GateInputs[3];
		FFloatReadRef FreqInputs[3];
		FFloatReadRef PWInputs[3];
		FEnumSIDWaveformReadRef WaveInputs[3];
		FInt32ReadRef AttInputs[3];
		FInt32ReadRef DecInputs[3];
		FInt32ReadRef SusInputs[3];
		FInt32ReadRef RelInputs[3];

		// Filter + Global inputs
		FFloatReadRef FilterCutoffInput;
		FFloatReadRef FilterResonanceInput;
		FEnumSIDFilterModeReadRef FilterModeInput;
		FInt32ReadRef FilterRoutingInput;
		FFloatReadRef VolumeInput;
		FEnumSIDChipModelReadRef ChipModelInput;
		FFloatReadRef ResBoostInput;

		// Outputs
		FAudioBufferWriteRef MasterOutput;
		FAudioBufferWriteRef VoiceOutputs[3];

		// SID emulator instance
		SID16 SID;
		chip_model CurrentChipModel = MOS6581;
		float SampleRate;
		float CycleAccumulator = 0.0f;
		bool bGateOn[3] = {false, false, false};
	};

	using FSIDChipNode = TNodeFacade<FSIDChipOperator>;

	METASOUND_REGISTER_NODE(FSIDChipNode)
}

#undef LOCTEXT_NAMESPACE
