// Copyright UE Audio MCP Project. All Rights Reserved.
// SID Envelope Node — ReSID SIDKIT Edition
// Non-linear exponential ADSR with authentic SID timing.
// Wraps reSID EnvelopeGenerator. Outputs Float (0.0-1.0) for modulation use.

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
#include "envelope.h"
THIRD_PARTY_INCLUDES_END

#define LOCTEXT_NAMESPACE "SIDMetaSoundNodes"

namespace Metasound
{
	namespace SIDEnvelopeNodeNames
	{
		METASOUND_PARAM(InGate,    "Gate",    "Trigger on = note on (attack), trigger off/next trigger = note off (release)")
		METASOUND_PARAM(InAttack,  "Attack",  "Attack rate 0-15 (SID register values: 0=2ms, 15=8s)")
		METASOUND_PARAM(InDecay,   "Decay",   "Decay rate 0-15 (SID register values: 0=6ms, 15=24s)")
		METASOUND_PARAM(InSustain, "Sustain", "Sustain level 0-15 (0=silent, 15=max)")
		METASOUND_PARAM(InRelease, "Release", "Release rate 0-15 (SID register values: 0=6ms, 15=24s)")
		METASOUND_PARAM(OutEnv,    "Out",     "Envelope output 0.0-1.0")
	}

	class FSIDEnvelopeOperator : public TExecutableOperator<FSIDEnvelopeOperator>
	{
	public:
		static const FNodeClassMetadata& GetNodeInfo()
		{
			auto InitNodeInfo = []() -> FNodeClassMetadata
			{
				FNodeClassMetadata Info;
				Info.ClassName        = { TEXT("UE"), TEXT("SID Envelope"), TEXT("Float") };
				Info.MajorVersion     = 1;
				Info.MinorVersion     = 0;
				Info.DisplayName      = LOCTEXT("SIDEnvDisplayName", "SID Envelope");
				Info.Description      = LOCTEXT("SIDEnvDesc", "MOS 6581/8580 ADSR envelope generator with non-linear exponential decay and authentic SID timing including the ADSR delay bug.");
				Info.Author           = TEXT("Koshi Mazaki");
				Info.PromptIfMissing  = LOCTEXT("SIDEnvPrompt", "SID Envelope");
				Info.DefaultInterface = GetVertexInterface();
				Info.CategoryHierarchy = { LOCTEXT("SIDKITCategory", "ReSID SIDKIT Edition") };
				return Info;
			};
			static const FNodeClassMetadata Info = InitNodeInfo();
			return Info;
		}

		static const FVertexInterface& GetVertexInterface()
		{
			using namespace SIDEnvelopeNodeNames;
			static const FVertexInterface Interface(
				FInputVertexInterface({
					TInputDataVertex<FTrigger>(METASOUND_GET_PARAM_NAME_AND_METADATA(InGate)),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InAttack), 0),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InDecay), 9),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InSustain), 0),
					TInputDataVertex<int32>(METASOUND_GET_PARAM_NAME_AND_METADATA(InRelease), 9),
				}),
				FOutputVertexInterface({
					TOutputDataVertex<FAudioBuffer>(METASOUND_GET_PARAM_NAME_AND_METADATA(OutEnv)),
				})
			);
			return Interface;
		}

		static TUniquePtr<IOperator> CreateOperator(const FBuildOperatorParams& InParams, FBuildResults& OutResults)
		{
			const FInputVertexInterfaceData& InputData = InParams.InputData;
			using namespace SIDEnvelopeNodeNames;

			FTriggerReadRef GateIn    = InputData.GetOrCreateDefaultDataReadReference<FTrigger>(METASOUND_GET_PARAM_NAME(InGate), InParams.OperatorSettings);
			FInt32ReadRef AttackIn    = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InAttack), InParams.OperatorSettings);
			FInt32ReadRef DecayIn     = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InDecay), InParams.OperatorSettings);
			FInt32ReadRef SustainIn   = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InSustain), InParams.OperatorSettings);
			FInt32ReadRef ReleaseIn   = InputData.GetOrCreateDefaultDataReadReference<int32>(METASOUND_GET_PARAM_NAME(InRelease), InParams.OperatorSettings);

			return MakeUnique<FSIDEnvelopeOperator>(InParams.OperatorSettings, GateIn, AttackIn, DecayIn, SustainIn, ReleaseIn);
		}

		FSIDEnvelopeOperator(
			const FOperatorSettings& InSettings,
			const FTriggerReadRef& InGate,
			const FInt32ReadRef& InAttack,
			const FInt32ReadRef& InDecay,
			const FInt32ReadRef& InSustain,
			const FInt32ReadRef& InRelease)
			: GateInput(InGate)
			, AttackInput(InAttack)
			, DecayInput(InDecay)
			, SustainInput(InSustain)
			, ReleaseInput(InRelease)
			, EnvOutput(FAudioBufferWriteRef::CreateNew(InSettings))
			, SampleRate(InSettings.GetSampleRate())
		{
			EnvGen.set_chip_model(MOS6581);
			EnvGen.reset();
			// Set default ADSR
			EnvGen.writeATTACK_DECAY(0x09);   // A=0, D=9
			EnvGen.writeSUSTAIN_RELEASE(0x09); // S=0, R=9
		}

		FDataReferenceCollection GetInputs() const override
		{
			using namespace SIDEnvelopeNodeNames;
			FDataReferenceCollection Inputs;
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InGate), GateInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InAttack), AttackInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InDecay), DecayInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InSustain), SustainInput);
			Inputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(InRelease), ReleaseInput);
			return Inputs;
		}

		FDataReferenceCollection GetOutputs() const override
		{
			using namespace SIDEnvelopeNodeNames;
			FDataReferenceCollection Outputs;
			Outputs.AddDataReadReference(METASOUND_GET_PARAM_NAME(OutEnv), EnvOutput);
			return Outputs;
		}

		void Execute()
		{
			FAudioBuffer& OutBuffer = *EnvOutput;
			const int32 NumSamples = OutBuffer.Num();

			// Update ADSR registers
			int32 A = FMath::Clamp(*AttackInput, 0, 15);
			int32 D = FMath::Clamp(*DecayInput, 0, 15);
			int32 S = FMath::Clamp(*SustainInput, 0, 15);
			int32 R = FMath::Clamp(*ReleaseInput, 0, 15);
			EnvGen.writeATTACK_DECAY((A << 4) | D);
			EnvGen.writeSUSTAIN_RELEASE((S << 4) | R);

			const float SIDClockRate = 985248.0f;
			const float CyclesPerSampleF = SIDClockRate / SampleRate;
			float* OutputData = OutBuffer.GetData();

			// Process trigger events for gate on/off
			// Gate on = trigger received, gate off = next trigger toggles off
			GateInput->ExecuteBlock(
				[this, &OutputData, &CyclesPerSampleF, NumSamples](int32 StartFrame, int32 EndFrame)
				{
					// No trigger in this range — just clock the envelope
					for (int32 i = StartFrame; i < EndFrame; ++i)
					{
						CycleAccumulator += CyclesPerSampleF;
						int32 WholeCycles = static_cast<int32>(CycleAccumulator);
						CycleAccumulator -= static_cast<float>(WholeCycles);

						EnvGen.clock(WholeCycles);
						OutputData[i] = static_cast<float>(EnvGen.output()) / 255.0f;
					}
				},
				[this, &OutputData, &CyclesPerSampleF, NumSamples](int32 StartFrame, int32 EndFrame)
				{
					// Trigger received — toggle gate
					bGateOn = !bGateOn;
					if (bGateOn)
					{
						// Gate on: set gate bit in control register
						EnvGen.writeCONTROL_REG(0x01); // Gate on (waveform bits don't matter for envelope)
					}
					else
					{
						// Gate off: clear gate bit
						EnvGen.writeCONTROL_REG(0x00);
					}

					for (int32 i = StartFrame; i < EndFrame; ++i)
					{
						CycleAccumulator += CyclesPerSampleF;
						int32 WholeCycles = static_cast<int32>(CycleAccumulator);
						CycleAccumulator -= static_cast<float>(WholeCycles);

						EnvGen.clock(WholeCycles);
						OutputData[i] = static_cast<float>(EnvGen.output()) / 255.0f;
					}
				}
			);
		}

		void Reset(const IOperator::FResetParams& InParams)
		{
			EnvGen.reset();
			CycleAccumulator = 0.0f;
			bGateOn = false;
		}

	private:
		FTriggerReadRef GateInput;
		FInt32ReadRef AttackInput;
		FInt32ReadRef DecayInput;
		FInt32ReadRef SustainInput;
		FInt32ReadRef ReleaseInput;
		FAudioBufferWriteRef EnvOutput;

		EnvelopeGenerator EnvGen;
		float SampleRate;
		float CycleAccumulator = 0.0f;
		bool bGateOn = false;
	};

	using FSIDEnvelopeNode = TNodeFacade<FSIDEnvelopeOperator>;

	METASOUND_REGISTER_NODE(FSIDEnvelopeNode)
}

#undef LOCTEXT_NAMESPACE
