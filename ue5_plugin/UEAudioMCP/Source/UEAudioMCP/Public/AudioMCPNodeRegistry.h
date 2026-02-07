// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

/**
 * Static registry of MetaSound display-name -> class-name mappings.
 * Separated from BuilderManager for easy maintenance and extension.
 *
 * To add new nodes: append to the InitNodeTypeMap() function below.
 * Class names come from Shift+hover on nodes in MetaSounds editor,
 * or from MetaSounds export "Copy full snippet" format.
 */
namespace AudioMCPNodeRegistry
{
	inline void InitNodeTypeMap(TMap<FString, FString>& Map)
	{
		// --- Generators ---
		Map.Add(TEXT("Sine"), TEXT("UE::MathOps::Sine"));
		Map.Add(TEXT("Noise"), TEXT("UE::Generators::Noise"));
		Map.Add(TEXT("White Noise"), TEXT("UE::Generators::WhiteNoise"));
		Map.Add(TEXT("LFO"), TEXT("UE::Generators::LFO"));
		Map.Add(TEXT("Oscillator"), TEXT("UE::Generators::Oscillator"));
		Map.Add(TEXT("Saw"), TEXT("UE::Generators::Saw"));
		Map.Add(TEXT("Square"), TEXT("UE::Generators::Square"));
		Map.Add(TEXT("Triangle"), TEXT("UE::Generators::Triangle"));
		Map.Add(TEXT("Pulse"), TEXT("UE::Generators::Pulse"));
		Map.Add(TEXT("WaveTable"), TEXT("UE::Generators::WaveTable"));
		Map.Add(TEXT("Granulator"), TEXT("UE::Generators::Granulator"));

		// --- Wave Players ---
		Map.Add(TEXT("Wave Player (Mono)"), TEXT("UE::WavePlayer::Mono"));
		Map.Add(TEXT("Wave Player (Stereo)"), TEXT("UE::WavePlayer::Stereo"));

		// --- Envelopes ---
		Map.Add(TEXT("AD Envelope"), TEXT("UE::Generators::ADEnvelope"));
		Map.Add(TEXT("ADSR Envelope"), TEXT("UE::Generators::ADSREnvelope"));

		// --- Filters ---
		Map.Add(TEXT("Biquad Filter"), TEXT("UE::Filters::BiquadFilter"));
		Map.Add(TEXT("State Variable Filter"), TEXT("UE::State Variable Filter::Audio"));
		Map.Add(TEXT("Lowpass Filter"), TEXT("UE::Filters::LowpassFilter"));
		Map.Add(TEXT("Highpass Filter"), TEXT("UE::Filters::HighpassFilter"));
		Map.Add(TEXT("Bandpass Filter"), TEXT("UE::Filters::BandpassFilter"));
		Map.Add(TEXT("Ladder Filter"), TEXT("UE::Filters::LadderFilter"));
		Map.Add(TEXT("One-Pole Lowpass"), TEXT("UE::Filters::OnePoleLowpass"));
		Map.Add(TEXT("One-Pole Highpass"), TEXT("UE::Filters::OnePoleHighpass"));

		// --- Math ---
		Map.Add(TEXT("Gain"), TEXT("UE::MathOps::Gain"));
		Map.Add(TEXT("Multiply"), TEXT("UE::MathOps::Multiply"));
		Map.Add(TEXT("Multiply (Audio)"), TEXT("UE::MathOps::Multiply::Audio"));
		Map.Add(TEXT("Add"), TEXT("UE::MathOps::Add"));
		Map.Add(TEXT("Add (Audio)"), TEXT("UE::MathOps::Add::Audio"));
		Map.Add(TEXT("Subtract"), TEXT("UE::MathOps::Subtract"));
		Map.Add(TEXT("Divide"), TEXT("UE::MathOps::Divide"));
		Map.Add(TEXT("Clamp"), TEXT("UE::MathOps::Clamp"));
		Map.Add(TEXT("Map Range"), TEXT("UE::MathOps::MapRange"));
		Map.Add(TEXT("Interpolate"), TEXT("UE::MathOps::Interpolate"));
		Map.Add(TEXT("Sample And Hold"), TEXT("UE::MathOps::SampleAndHold"));

		// --- Random ---
		Map.Add(TEXT("Random (Float)"), TEXT("UE::Random::Float"));
		Map.Add(TEXT("Random Get (Float)"), TEXT("UE::Random::GetFloat"));

		// --- Mixing ---
		Map.Add(TEXT("Stereo Mixer"), TEXT("UE::Mixing::StereoMixer"));
		Map.Add(TEXT("Mono Mixer"), TEXT("UE::Mixing::MonoMixer"));
		Map.Add(TEXT("Mix"), TEXT("UE::Mixing::Mix"));

		// --- Effects ---
		Map.Add(TEXT("Delay"), TEXT("UE::Effects::Delay"));
		Map.Add(TEXT("Stereo Delay"), TEXT("UE::Effects::StereoDelay"));
		Map.Add(TEXT("Reverb"), TEXT("UE::Effects::Reverb"));
		Map.Add(TEXT("Chorus"), TEXT("UE::Effects::Chorus"));
		Map.Add(TEXT("Phaser"), TEXT("UE::Effects::Phaser"));
		Map.Add(TEXT("Flanger"), TEXT("UE::Effects::Flanger"));

		// --- Dynamics ---
		Map.Add(TEXT("Compressor"), TEXT("UE::Dynamics::Compressor"));
		Map.Add(TEXT("Limiter"), TEXT("UE::Dynamics::Limiter"));
		Map.Add(TEXT("Gate"), TEXT("UE::Dynamics::Gate"));

		// --- Triggers ---
		Map.Add(TEXT("Trigger Repeat"), TEXT("UE::Triggers::TriggerRepeat"));
		Map.Add(TEXT("Trigger Counter"), TEXT("UE::Triggers::TriggerCounter"));
		Map.Add(TEXT("Trigger Control"), TEXT("UE::Triggers::TriggerControl"));
		Map.Add(TEXT("Trigger On Threshold"), TEXT("UE::Triggers::TriggerOnThreshold"));
		Map.Add(TEXT("Trigger Delay"), TEXT("UE::Triggers::TriggerDelay"));
		Map.Add(TEXT("Trigger Route"), TEXT("UE::Triggers::TriggerRoute"));

		// --- Timing / Conversions ---
		Map.Add(TEXT("BPM To Seconds"), TEXT("UE::Timing::BPMToSeconds"));
		Map.Add(TEXT("Freq To MIDI"), TEXT("UE::Conversions::FreqToMIDI"));
		Map.Add(TEXT("MIDI To Freq"), TEXT("UE::Conversions::MIDIToFreq"));
		Map.Add(TEXT("Semitones To Freq Multiplier"), TEXT("UE::Conversions::SemitonesToFreqMultiplier"));
		Map.Add(TEXT("dB To Linear"), TEXT("UE::Conversions::dBToLinear"));
		Map.Add(TEXT("Linear To dB"), TEXT("UE::Conversions::LineardB"));
		Map.Add(TEXT("Float To Audio"), TEXT("UE::Conversions::FloatToAudio"));
		Map.Add(TEXT("Audio To Float"), TEXT("UE::Conversions::AudioToFloat"));

		// --- Routing ---
		Map.Add(TEXT("Mono To Stereo"), TEXT("UE::Routing::MonoToStereo"));
		Map.Add(TEXT("Stereo To Mono"), TEXT("UE::Routing::StereoToMono"));
		Map.Add(TEXT("Send"), TEXT("UE::Routing::Send"));
		Map.Add(TEXT("Receive"), TEXT("UE::Routing::Receive"));

		// --- Spatialization ---
		Map.Add(TEXT("ITD Panner"), TEXT("UE::Spatialization::ITDPanner"));
		Map.Add(TEXT("Stereo Panner"), TEXT("UE::Spatialization::StereoPanner"));

		// --- Variables ---
		Map.Add(TEXT("Get"), TEXT("UE::Variables::Get"));
		Map.Add(TEXT("Set"), TEXT("UE::Variables::Set"));
	}
}
