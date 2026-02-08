// Copyright UE Audio MCP Project. All Rights Reserved.

#include "SIDNodeEnums.h"

// ============================================================================
// MetaSounds enum registration for SID types
// ============================================================================

DEFINE_METASOUND_ENUM_BEGIN(ESIDWaveform, FEnumSIDWaveform, "SIDWaveform")
	DEFINE_METASOUND_ENUM_ENTRY(ESIDWaveform::Triangle,    "TriangleDescription",  "Triangle",     "TriangleTT",     "Smooth, hollow tone"),
	DEFINE_METASOUND_ENUM_ENTRY(ESIDWaveform::Sawtooth,    "SawtoothDescription",  "Sawtooth",     "SawtoothTT",     "Bright, buzzy tone"),
	DEFINE_METASOUND_ENUM_ENTRY(ESIDWaveform::Pulse,       "PulseDescription",     "Pulse",        "PulseTT",        "Variable duty cycle square wave"),
	DEFINE_METASOUND_ENUM_ENTRY(ESIDWaveform::Noise,       "NoiseDescription",     "Noise",        "NoiseTT",        "LFSR pseudo-random noise"),
	DEFINE_METASOUND_ENUM_ENTRY(ESIDWaveform::SawTri,      "SawTriDescription",    "Saw+Tri",      "SawTriTT",       "Combined sawtooth and triangle"),
	DEFINE_METASOUND_ENUM_ENTRY(ESIDWaveform::PulseSaw,    "PulseSawDescription",  "Pulse+Saw",    "PulseSawTT",     "Combined pulse and sawtooth"),
	DEFINE_METASOUND_ENUM_ENTRY(ESIDWaveform::PulseTri,    "PulseTriDescription",  "Pulse+Tri",    "PulseTriTT",     "Combined pulse and triangle"),
	DEFINE_METASOUND_ENUM_ENTRY(ESIDWaveform::PulseSawTri, "PulseSawTriDescription","Pulse+Saw+Tri","PulseSawTriTT", "Combined pulse, sawtooth, and triangle"),
DEFINE_METASOUND_ENUM_END()

DEFINE_METASOUND_ENUM_BEGIN(ESIDFilterMode, FEnumSIDFilterMode, "SIDFilterMode")
	DEFINE_METASOUND_ENUM_ENTRY(ESIDFilterMode::LowPass,   "LowPassDescription",  "Low Pass",  "LowPassTT",  "Warm, muffled - removes highs"),
	DEFINE_METASOUND_ENUM_ENTRY(ESIDFilterMode::BandPass,  "BandPassDescription", "Band Pass", "BandPassTT", "Nasal, vocal - removes lows and highs"),
	DEFINE_METASOUND_ENUM_ENTRY(ESIDFilterMode::HighPass,  "HighPassDescription", "High Pass", "HighPassTT", "Thin, bright - removes lows"),
	DEFINE_METASOUND_ENUM_ENTRY(ESIDFilterMode::Notch,     "NotchDescription",    "Notch",     "NotchTT",    "LP+HP - phaser-like cancellation"),
	DEFINE_METASOUND_ENUM_ENTRY(ESIDFilterMode::LowBand,   "LowBandDescription",  "Low+Band",  "LowBandTT",  "LP+BP - thick low end"),
	DEFINE_METASOUND_ENUM_ENTRY(ESIDFilterMode::BandHigh,  "BandHighDescription", "Band+High", "BandHighTT", "BP+HP - crispy resonance"),
	DEFINE_METASOUND_ENUM_ENTRY(ESIDFilterMode::All,       "AllDescription",      "All",       "AllTT",      "LP+BP+HP - all filter modes"),
DEFINE_METASOUND_ENUM_END()

DEFINE_METASOUND_ENUM_BEGIN(ESIDChipModel, FEnumSIDChipModel, "SIDChipModel")
	DEFINE_METASOUND_ENUM_ENTRY(ESIDChipModel::MOS6581, "MOS6581Description", "MOS 6581", "MOS6581TT", "Classic C64 - warm non-linear analog filter"),
	DEFINE_METASOUND_ENUM_ENTRY(ESIDChipModel::MOS8580, "MOS8580Description", "MOS 8580", "MOS8580TT", "C64C/C128 - cleaner linear filter"),
DEFINE_METASOUND_ENUM_END()
