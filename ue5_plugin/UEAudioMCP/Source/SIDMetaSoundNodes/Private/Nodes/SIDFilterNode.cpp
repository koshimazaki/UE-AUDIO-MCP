// Copyright UE Audio MCP Project. All Rights Reserved.
// SID Filter Node — ReSID SIDKIT Edition
// Route any audio through the MOS 6581/8580 analog filter model.
// Uses reSID's two-integrator-loop biquad with non-linear VCR (6581) or linear (8580).

#include "SIDNodeEnums.h"

#include "MetasoundExecutableOperator.h"
#include "MetasoundNodeRegistrationMacro.h"
#include "MetasoundParamHelper.h"
#include "MetasoundPrimitives.h"
#include "MetasoundAudioBuffer.h"
#include "MetasoundOperatorSettings.h"
#include "MetasoundDataTypeRegistrationMacro.h"
#include "MetasoundVertex.h"

THIRD_PARTY_INCLUDES_START
#include "siddefs.h"
#include "spline.h"
#include "filter.h"
THIRD_PARTY_INCLUDES_END

#define LOCTEXT_NAMESPACE "SIDMetaSoundNodes"

namespace Metasound
{
	namespace SIDFilterNodeNames
	{
		METASOUND_PARAM(InAudio,      "In",         "Audio input to filter")
		METASOUND_PARAM(InCutoff,     "Cutoff",     "Filter cutoff 0.0-1.0 (maps through SID spline to w0)")
		METASOUND_PARAM(InResonance,  "Resonance",  "Filter resonance 0.0-1.0 (maps to SID 0-15)")
		METASOUND_PARAM(InMode,       "Mode",       "Filter mode: LP, BP, HP, Notch, etc.")
		METASOUND_PARAM(InChipModel,  "Chip Model", "MOS 6581 (non-linear, warm) or MOS 8580 (cleaner)")
		METASOUND_PARAM(InResBoost,   "Res Boost",  "Resonance boost 0.0-1.0 (SIDKIT extension, 1.0=self-oscillation)")
		METASOUND_PARAM(OutAudio,     "Out",        "Filtered audio output")
	}

	class FSIDFilterOperator : public TExecutableOperator<FSIDFilterOperator>
	{
	public:
		static const FNodeClassMetadata& GetNodeInfo()
		{
			auto InitNodeInfo = []() -> FNodeClassMetadata
			{
				FNodeClassMetadata Info;
				Info.ClassName        = { TEXT("UE"), TEXT("SID Filter"), TEXT("Audio") };
				Info.MajorVersion     = 1;
				Info.MinorVersion     = 0;
				Info.DisplayName      = LOCTEXT("SIDFilterDisplayName", "SID Filter");
				Info.Description      = LOCTEXT("SIDFilterDesc", "MOS 6581/8580 analog filter emulation. Route any audio through the SID chip's non-linear two-integrator-loop biquad filter.");
				Info.Author           = TEXT("Koshi Mazaki");
				Info.PromptIfMissing  = LOCTEXT("SIDFilterPrompt", "SID Filter");
				Info.DefaultInterface = GetVertexInterface();
				Info.CategoryHierarchy = { LOCTEXT("SIDKITCategory", "ReSID SIDKIT Edition") };
				return Info;
			};
			static const FNodeClassMetadata Info = InitNodeInfo();
			return Info;
		}

		static const FVertexInterface& GetVertexInterface()
		{
			using namespace SIDFilterNodeNames;
			static const FVertexInterface Interface(
				FInputVertexInterface({
					TInputDataVertex<FAudioBuffer>(METASOUND_GET_PARAM_NAME_AND_METADATA(InAudio)),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InCutoff), 0.5f),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InResonance), 0.0f),
					TInputDataVertex<FEnumSIDFilterMode>(METASOUND_GET_PARAM_NAME_AND_METADATA(InMode)),
					TInputDataVertex<FEnumSIDChipModel>(METASOUND_GET_PARAM_NAME_AND_METADATA(InChipModel)),
					TInputDataVertex<float>(METASOUND_GET_PARAM_NAME_AND_METADATA(InResBoost), 0.0f),
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
			using namespace SIDFilterNodeNames;

			FAudioBufferReadRef AudioIn   = InputData.GetOrConstructDataReadReference<FAudioBuffer>(METASOUND_GET_PARAM_NAME(InAudio), InParams.OperatorSettings);
			FFloatReadRef CutoffIn        = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InCutoff), InParams.OperatorSettings);
			FFloatReadRef ResonanceIn     = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InResonance), InParams.OperatorSettings);
			FEnumSIDFilterModeReadRef ModeIn = InputData.GetOrCreateDefaultDataReadReference<FEnumSIDFilterMode>(METASOUND_GET_PARAM_NAME(InMode), InParams.OperatorSettings);
			FEnumSIDChipModelReadRef ChipIn  = InputData.GetOrCreateDefaultDataReadReference<FEnumSIDChipModel>(METASOUND_GET_PARAM_NAME(InChipModel), InParams.OperatorSettings);
			FFloatReadRef ResBoostIn      = InputData.GetOrCreateDefaultDataReadReference<float>(METASOUND_GET_PARAM_NAME(InResBoost), InParams.OperatorSettings);

			return MakeUnique<FSIDFilterOperator>(InParams.OperatorSettings, AudioIn, CutoffIn, ResonanceIn, ModeIn, ChipIn, ResBoostIn);
		}

		FSIDFilterOperator(
			const FOperatorSettings& InSettings,
			const FAudioBufferReadRef& InAudio,
			const FFloatReadRef& InCutoff,
			const FFloatReadRef& InResonance,
			const FEnumSIDFilterModeReadRef& InMode,
			const FEnumSIDChipModelReadRef& InChipModel,
			const FFloatReadRef& InResBoost)
			: AudioInput(InAudio)
			, CutoffInput(InCutoff)
			, ResonanceInput(InResonance)
			, ModeInput(InMode)
			, ChipModelInput(InChipModel)
			, ResBoostInput(InResBoost)
			, AudioOutput(FAudioBufferWriteRef::CreateNew(InSettings))
			, SampleRate(InSettings.GetSampleRate())
		{
			SIDFilter.enable_filter(true);
			SIDFilter.set_chip_model(MOS6581);
			// Route voice 1 through filter, disable voice 2/3
			SIDFilter.writeRES_FILT(0x01);
			// LP mode, max volume
			SIDFilter.writeMODE_VOL(0x1F);
		}

		FDataReferenceCollection GetInputs() const override
		{
			using namespace SIDFilterNodeNames;
			FDataReferenceCollection InputDataReferences;
			InputDataReferences.AddDataReadReference(METASOUND_GET_PARAM_NAME(InAudio), AudioInput);
			InputDataReferences.AddDataReadReference(METASOUND_GET_PARAM_NAME(InCutoff), CutoffInput);
			InputDataReferences.AddDataReadReference(METASOUND_GET_PARAM_NAME(InResonance), ResonanceInput);
			InputDataReferences.AddDataReadReference(METASOUND_GET_PARAM_NAME(InMode), ModeInput);
			InputDataReferences.AddDataReadReference(METASOUND_GET_PARAM_NAME(InChipModel), ChipModelInput);
			InputDataReferences.AddDataReadReference(METASOUND_GET_PARAM_NAME(InResBoost), ResBoostInput);
			return InputDataReferences;
		}

		FDataReferenceCollection GetOutputs() const override
		{
			using namespace SIDFilterNodeNames;
			FDataReferenceCollection OutputDataReferences;
			OutputDataReferences.AddDataReadReference(METASOUND_GET_PARAM_NAME(OutAudio), AudioOutput);
			return OutputDataReferences;
		}

		void Execute()
		{
			const FAudioBuffer& InBuffer = *AudioInput;
			FAudioBuffer& OutBuffer = *AudioOutput;
			const int32 NumSamples = InBuffer.Num();

			// Update chip model
			ESIDChipModel ChipModel = *ChipModelInput;
			chip_model Model = (ChipModel == ESIDChipModel::MOS6581) ? MOS6581 : MOS8580;
			if (Model != CurrentChipModel)
			{
				CurrentChipModel = Model;
				SIDFilter.set_chip_model(Model);
			}

			// Update filter mode — maps enum to SID register bits
			ESIDFilterMode Mode = *ModeInput;
			reg8 ModeBits = 0;
			switch (Mode)
			{
			case ESIDFilterMode::LowPass:  ModeBits = 0x10; break;
			case ESIDFilterMode::BandPass: ModeBits = 0x20; break;
			case ESIDFilterMode::HighPass: ModeBits = 0x40; break;
			case ESIDFilterMode::Notch:    ModeBits = 0x50; break; // LP+HP
			case ESIDFilterMode::LowBand:  ModeBits = 0x30; break; // LP+BP
			case ESIDFilterMode::BandHigh: ModeBits = 0x60; break; // BP+HP
			case ESIDFilterMode::All:      ModeBits = 0x70; break; // LP+BP+HP
			}
			// MODE_VOL register: upper 4 bits = mode, lower 4 = volume (max=15)
			SIDFilter.writeMODE_VOL(ModeBits | 0x0F);

			// Update cutoff (0.0-1.0 → 11-bit SID register 0-2047)
			float Cutoff = FMath::Clamp(*CutoffInput, 0.0f, 1.0f);
			reg12 FCValue = static_cast<reg12>(Cutoff * 2047.0f);
			SIDFilter.writeFC_LO(FCValue & 0x07);
			SIDFilter.writeFC_HI(FCValue >> 3);

			// Update resonance (0.0-1.0 → 4-bit SID register 0-15)
			float Resonance = FMath::Clamp(*ResonanceInput, 0.0f, 1.0f);
			reg8 ResValue = static_cast<reg8>(Resonance * 15.0f);
			// RES_FILT: upper 4 bits = resonance, lower 4 = filter routing
			SIDFilter.writeRES_FILT((ResValue << 4) | 0x01); // Voice 1 routed through filter

			// Update resonance boost (SIDKIT extension)
			float ResBoost = FMath::Clamp(*ResBoostInput, 0.0f, 1.0f);
			SIDFilter.set_resonance_boost(static_cast<int>(ResBoost * 255.0f));

			// Process audio: scale float [-1,1] to SID internal range, filter, scale back
			// SID filter expects 20-bit voice input (after wave*envelope multiply)
			// We scale float to ~13-bit range since filter internally shifts down from 20 to 13
			const float InputScale = 8192.0f;  // 2^13 — matches SID internal 13-bit voice level
			const float OutputScale = 1.0f / 32768.0f; // Filter output is ~16-bit, normalize to float

			// SID clock rate / sample rate = cycles per sample
			// PAL: 985248 Hz, NTSC: 1022727 Hz
			const float SIDClockRate = 985248.0f;
			const float CyclesPerSampleF = SIDClockRate / SampleRate;

			const float* InputData = InBuffer.GetData();
			float* OutputData = OutBuffer.GetData();

			for (int32 i = 0; i < NumSamples; ++i)
			{
				// Convert float audio to SID voice-level input
				sound_sample VoiceIn = static_cast<sound_sample>(InputData[i] * InputScale);

				// Accumulate fractional cycles
				CycleAccumulator += CyclesPerSampleF;
				int32 WholeCycles = static_cast<int32>(CycleAccumulator);
				CycleAccumulator -= static_cast<float>(WholeCycles);

				// Clock filter with audio input as voice 1, silence on voices 2/3
				SIDFilter.clock(WholeCycles, VoiceIn, 0, 0, 0);

				// Get filter output and normalize to float
				OutputData[i] = static_cast<float>(SIDFilter.output()) * OutputScale;
			}
		}

		void Reset(const IOperator::FResetParams& InParams)
		{
			SIDFilter.reset();
			SIDFilter.enable_filter(true);
			SIDFilter.set_chip_model(CurrentChipModel);
			SIDFilter.writeRES_FILT(0x01);
			SIDFilter.writeMODE_VOL(0x1F);
			CycleAccumulator = 0.0f;
		}

	private:
		FAudioBufferReadRef AudioInput;
		FFloatReadRef CutoffInput;
		FFloatReadRef ResonanceInput;
		FEnumSIDFilterModeReadRef ModeInput;
		FEnumSIDChipModelReadRef ChipModelInput;
		FFloatReadRef ResBoostInput;
		FAudioBufferWriteRef AudioOutput;

		Filter SIDFilter;
		chip_model CurrentChipModel = MOS6581;
		float SampleRate;
		float CycleAccumulator = 0.0f;
	};

	class FSIDFilterNode : public FNodeFacade
	{
	public:
		FSIDFilterNode(const FNodeInitData& InitData)
			: FNodeFacade(InitData.InstanceName, InitData.InstanceID, FSIDFilterOperator::GetNodeInfo())
		{
		}
	};

	METASOUND_REGISTER_NODE(FSIDFilterNode)
}

#undef LOCTEXT_NAMESPACE
