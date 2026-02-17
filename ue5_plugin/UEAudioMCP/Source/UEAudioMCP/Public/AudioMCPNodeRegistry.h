// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

/**
 * Static registry of MetaSound display-name -> class-name mappings.
 * Separated from BuilderManager for easy maintenance and extension.
 *
 * UE 5.7 class name format: "Namespace::Name::Variant"
 * - Namespace is typically "UE" (StandardNodes::Namespace)
 * - Name is the operator/node name (may contain spaces)
 * - Variant is usually the data type: "Audio", "Float", "Int32", "Time", "Stereo"
 *
 * Source: MetasoundStandardNodes source files in UE 5.7
 * Verified against: MetasoundOscillatorNodes.cpp, MetasoundMathNodes.cpp,
 *                   MetasoundBasicFilters.cpp, MetasoundCompressorNode.cpp, etc.
 */
namespace AudioMCPNodeRegistry
{
	inline void InitNodeTypeMap(TMap<FString, FString>& Map)
	{
		// =================================================================
		// Oscillators (MetasoundOscillatorNodes.cpp)
		// =================================================================
		Map.Add(TEXT("Sine"),                TEXT("UE::Sine::Audio"));
		Map.Add(TEXT("Saw"),                 TEXT("UE::Saw::Audio"));
		Map.Add(TEXT("Square"),              TEXT("UE::Square::Audio"));
		Map.Add(TEXT("Triangle"),            TEXT("UE::Triangle::Audio"));
		Map.Add(TEXT("LFO"),                 TEXT("UE::LFO::Audio"));

		// =================================================================
		// Wave Players (MetasoundEngine)
		// =================================================================
		Map.Add(TEXT("Wave Player"),         TEXT("UE::Wave Player::Audio"));
		Map.Add(TEXT("Wave Player (Mono)"),  TEXT("UE::Wave Player::Mono"));
		Map.Add(TEXT("Wave Player (Stereo)"),TEXT("UE::Wave Player::Stereo"));

		// =================================================================
		// Envelopes (MetasoundADEnvelopeNode.cpp, MetasoundADSREnvelopeNode.cpp)
		// =================================================================
		Map.Add(TEXT("AD Envelope"),          TEXT("AD Envelope::AD Envelope::Audio"));
		Map.Add(TEXT("AD Envelope (Audio)"),  TEXT("AD Envelope::AD Envelope::Audio"));
		Map.Add(TEXT("AD Envelope (Float)"),  TEXT("AD Envelope::AD Envelope::Float"));
		Map.Add(TEXT("ADSR Envelope"),        TEXT("ADSR Envelope::ADSR Envelope::Audio"));
		Map.Add(TEXT("ADSR Envelope (Audio)"),TEXT("ADSR Envelope::ADSR Envelope::Audio"));
		Map.Add(TEXT("ADSR Envelope (Float)"),TEXT("ADSR Envelope::ADSR Envelope::Float"));

		// =================================================================
		// Filters (MetasoundBasicFilters.cpp)
		// =================================================================
		Map.Add(TEXT("Biquad Filter"),              TEXT("UE::Biquad Filter::Audio"));
		Map.Add(TEXT("State Variable Filter"),       TEXT("UE::State Variable Filter::Audio"));
		Map.Add(TEXT("Ladder Filter"),               TEXT("UE::Ladder Filter::Audio"));
		Map.Add(TEXT("One-Pole Low Pass Filter"),    TEXT("UE::One-Pole Low Pass Filter::Audio"));
		Map.Add(TEXT("One-Pole High Pass Filter"),   TEXT("UE::One-Pole High Pass Filter::Audio"));
		Map.Add(TEXT("One-Pole Lowpass"),             TEXT("UE::One-Pole Low Pass Filter::Audio"));
		Map.Add(TEXT("One-Pole Highpass"),            TEXT("UE::One-Pole High Pass Filter::Audio"));
		Map.Add(TEXT("Dynamic Filter"),              TEXT("UE::DynamicFilter::Audio"));
		// Legacy aliases
		Map.Add(TEXT("Lowpass Filter"),               TEXT("UE::One-Pole Low Pass Filter::Audio"));
		Map.Add(TEXT("Highpass Filter"),              TEXT("UE::One-Pole High Pass Filter::Audio"));

		// =================================================================
		// Math (MetasoundMathNodes.cpp — DEFINE_METASOUND_MATHOP macro)
		// =================================================================
		// Float variants (default)
		Map.Add(TEXT("Add"),                 TEXT("UE::Add::Float"));
		Map.Add(TEXT("Subtract"),            TEXT("UE::Subtract::Float"));
		Map.Add(TEXT("Multiply"),            TEXT("UE::Multiply::Float"));
		Map.Add(TEXT("Divide"),              TEXT("UE::Divide::Float"));
		Map.Add(TEXT("Power"),               TEXT("UE::Power::Float"));
		Map.Add(TEXT("Logarithm"),           TEXT("UE::Logarithm::Float"));
		Map.Add(TEXT("Modulo"),              TEXT("UE::Modulo::Int32"));

		// Audio variants
		Map.Add(TEXT("Add (Audio)"),          TEXT("UE::Add::Audio"));
		Map.Add(TEXT("Subtract (Audio)"),     TEXT("UE::Subtract::Audio"));
		Map.Add(TEXT("Multiply (Audio)"),     TEXT("UE::Multiply::Audio"));
		Map.Add(TEXT("Multiply (Audio by Float)"), TEXT("UE::Multiply::Audio by Float"));

		// Int32 variants
		Map.Add(TEXT("Add (Int32)"),          TEXT("UE::Add::Int32"));
		Map.Add(TEXT("Subtract (Int32)"),     TEXT("UE::Subtract::Int32"));
		Map.Add(TEXT("Multiply (Int32)"),     TEXT("UE::Multiply::Int32"));

		// Time variants
		Map.Add(TEXT("Add (Time)"),           TEXT("UE::Add::Time"));
		Map.Add(TEXT("Multiply (Time by Float)"), TEXT("UE::Multiply::Time by Float"));
		Map.Add(TEXT("Divide (Time by Float)"),   TEXT("UE::Divide::Time by Float"));

		// Gain is just Multiply (Audio by Float)
		Map.Add(TEXT("Gain"),                TEXT("UE::Multiply::Audio by Float"));

		// Control math
		Map.Add(TEXT("Clamp"),               TEXT("UE::Clamp::Float"));
		Map.Add(TEXT("Clamp (Audio)"),       TEXT("UE::Clamp::Audio"));
		Map.Add(TEXT("Map Range"),           TEXT("UE::Map Range::Float"));
		Map.Add(TEXT("Map Range (Audio)"),   TEXT("UE::Map Range::Audio"));
		Map.Add(TEXT("InterpTo"),            TEXT("UE::InterpTo::Float"));
		Map.Add(TEXT("InterpTo (Audio)"),    TEXT("UE::InterpTo::Audio"));
		Map.Add(TEXT("Interpolate"),         TEXT("UE::InterpTo::Float"));
		Map.Add(TEXT("Sample And Hold"),     TEXT("UE::Sample And Hold::Float"));

		// =================================================================
		// Random
		// =================================================================
		Map.Add(TEXT("Random (Float)"),      TEXT("UE::Random::Float"));
		Map.Add(TEXT("Random Get (Float)"),  TEXT("UE::Random Get::Float"));
		Map.Add(TEXT("Random Get (WaveAsset:Array)"), TEXT("Array::Random Get::WaveAsset:Array"));
		Map.Add(TEXT("Random Get (WaveAssetArray)"),  TEXT("Array::Random Get::WaveAsset:Array"));
		Map.Add(TEXT("Random Get (Int32:Array)"),     TEXT("Array::Random Get::Int32:Array"));
		Map.Add(TEXT("Random Get (Bool:Array)"),      TEXT("Array::Random Get::Bool:Array"));
		Map.Add(TEXT("RandomFloat"),         TEXT("UE::RandomFloat::None"));
		Map.Add(TEXT("RandomInt32"),          TEXT("UE::RandomInt32::None"));

		// =================================================================
		// Mixing / Routing
		// =================================================================
		Map.Add(TEXT("Stereo Mixer"),        TEXT("UE::Stereo Mixer::Audio"));
		Map.Add(TEXT("Mono To Stereo"),      TEXT("UE::Mono To Stereo::Audio"));
		Map.Add(TEXT("Stereo To Mono"),      TEXT("UE::Stereo To Mono::Audio"));
		Map.Add(TEXT("Crossfade"),           TEXT("UE::Crossfade::Audio"));
		Map.Add(TEXT("Mix"),                 TEXT("UE::Mix::Audio"));

		// =================================================================
		// Effects
		// =================================================================
		Map.Add(TEXT("Delay"),               TEXT("UE::Delay::Audio"));
		Map.Add(TEXT("Stereo Delay"),        TEXT("UE::Stereo Delay::Audio"));
		Map.Add(TEXT("Plate Reverb"),        TEXT("UE::Plate Reverb::Stereo"));
		Map.Add(TEXT("Reverb"),              TEXT("UE::Plate Reverb::Stereo"));
		Map.Add(TEXT("Chorus"),              TEXT("UE::Chorus::Audio"));
		Map.Add(TEXT("Phaser"),              TEXT("UE::Phaser::Audio"));
		Map.Add(TEXT("Flanger"),             TEXT("UE::Flanger"));

		// =================================================================
		// Dynamics (MetasoundCompressorNode.cpp, MetasoundLimiterNode.cpp)
		// =================================================================
		Map.Add(TEXT("Compressor"),          TEXT("UE::Compressor::Audio"));
		Map.Add(TEXT("Limiter"),             TEXT("UE::Limiter::Audio"));
		Map.Add(TEXT("Gate"),                TEXT("UE::Gate::Audio"));

		// =================================================================
		// Distortion / Spectral
		// =================================================================
		Map.Add(TEXT("Bitcrusher"),          TEXT("UE::Bitcrusher::Audio"));
		Map.Add(TEXT("BitCrusher"),          TEXT("UE::Bitcrusher::Audio"));
		Map.Add(TEXT("Ring Modulator"),      TEXT("UE::RingMod::Audio"));
		Map.Add(TEXT("WaveShaper"),          TEXT("UE::WaveShaper::Audio"));

		// =================================================================
		// Noise (MetasoundLowFrequencyNoise.cpp)
		// =================================================================
		Map.Add(TEXT("Noise"),               TEXT("UE::Noise::Audio"));
		Map.Add(TEXT("White Noise"),         TEXT("UE::White Noise::Audio"));
		Map.Add(TEXT("Perlin Noise"),        TEXT("UE::Perlin Noise::Audio"));
		Map.Add(TEXT("LFO Noise"),           TEXT("UE::Lfo Frequency Noise::Audio"));

		// =================================================================
		// Triggers
		// =================================================================
		Map.Add(TEXT("Trigger Repeat"),       TEXT("UE::Trigger Repeat::"));
		Map.Add(TEXT("Trigger Counter"),      TEXT("UE::Trigger Counter::"));
		Map.Add(TEXT("Trigger Delay"),        TEXT("UE::Trigger Delay::"));
		Map.Add(TEXT("Trigger On Threshold"), TEXT("UE::Trigger On Threshold::"));
		Map.Add(TEXT("Trigger Control"),      TEXT("UE::Trigger Control::"));
		Map.Add(TEXT("Trigger Route"),        TEXT("UE::Trigger Route::"));
		Map.Add(TEXT("Trigger Toggle"),       TEXT("UE::Trigger Toggle::"));
		Map.Add(TEXT("Trigger Filter"),       TEXT("UE::Trigger Filter::"));

		// =================================================================
		// Conversions / Utility
		// =================================================================
		Map.Add(TEXT("BPM To Seconds"),                TEXT("UE::BPM To Seconds::Float"));
		Map.Add(TEXT("Freq To MIDI"),                  TEXT("UE::Freq To MIDI::Float"));
		Map.Add(TEXT("MIDI To Freq"),                  TEXT("UE::MIDI To Freq::Float"));
		Map.Add(TEXT("Semitones To Freq Multiplier"),  TEXT("UE::Semitones To Frequency Multiplier::Float"));
		Map.Add(TEXT("dB To Linear"),                  TEXT("UE::Decibels To Linear Gain::Float"));
		Map.Add(TEXT("Decibels to Linear Gain"),       TEXT("UE::Decibels to Linear Gain::Float"));
		Map.Add(TEXT("Linear To dB"),                  TEXT("UE::Linear Gain To Decibels::Float"));
		Map.Add(TEXT("Linear To Log Frequency"),       TEXT("UE::Linear To Log Frequency::Float"));
		Map.Add(TEXT("Convert Filter Q To Bandwidth"), TEXT("UE::Convert Filter Q To Bandwidth::"));
		Map.Add(TEXT("Frequency Multiplier to Semitone"), TEXT("UE::Frequency Multiplier to Semitone::Float"));
		Map.Add(TEXT("Audio Mixer (Stereo, 2)"),       TEXT("AudioMixer::Audio Mixer (Stereo, 2)::None"));

		// =================================================================
		// Spatialization (MetasoundStereopannerNode.cpp, MetasoundITDPannerNode.cpp)
		// =================================================================
		Map.Add(TEXT("Stereo Panner"),       TEXT("UE::Stereo Panner::Audio"));
		Map.Add(TEXT("ITD Panner"),          TEXT("UE::ITD Panner::Audio"));

		// =================================================================
		// Mid-Side (MetasoundMidSideNodes.cpp)
		// =================================================================
		Map.Add(TEXT("Mid-Side Encode"),     TEXT("UE::Mid-Side Encode::Audio"));
		Map.Add(TEXT("Mid-Side Decode"),     TEXT("UE::Mid-Side Decode::Audio"));

		// =================================================================
		// Envelope Follower
		// =================================================================
		Map.Add(TEXT("Envelope Follower"),   TEXT("UE::Envelope Follower::Audio"));

		// =================================================================
		// Send / Receive
		// =================================================================
		Map.Add(TEXT("Send"),                TEXT("UE::Audio Send::Audio"));
		Map.Add(TEXT("Receive"),             TEXT("UE::Audio Receive::Audio"));

		// =================================================================
		// Wave Writer (for debugging)
		// =================================================================
		Map.Add(TEXT("Wave Writer"),         TEXT("UE::Wave Writer::Audio"));

		// =================================================================
		// ReSID SIDKIT Edition — MOS 6581/8580 emulation nodes
		// =================================================================
		Map.Add(TEXT("SID Oscillator"),      TEXT("UE::SID Oscillator::Audio"));
		Map.Add(TEXT("SID Envelope"),        TEXT("UE::SID Envelope::Float"));
		Map.Add(TEXT("SID Filter"),          TEXT("UE::SID Filter::Audio"));
		Map.Add(TEXT("SID Voice"),           TEXT("UE::SID Voice::Audio"));
		Map.Add(TEXT("SID Chip"),            TEXT("UE::SID Chip::Audio"));
	}
}
