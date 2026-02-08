// Copyright UE Audio MCP Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "MetasoundEnumRegistrationMacro.h"

// ============================================================================
// SID Waveform selection (matches SID register bits 4-7)
// ============================================================================
UENUM()
enum class ESIDWaveform : uint8
{
	Triangle,      // Bit 4 - smooth, hollow tone
	Sawtooth,      // Bit 5 - bright, buzzy
	Pulse,         // Bit 6 - variable duty cycle
	Noise,         // Bit 7 - LFSR noise
	SawTri,        // Bits 4+5 - combined waveform (analog short-circuit)
	PulseSaw,      // Bits 5+6 - combined waveform
	PulseTri,      // Bits 4+6 - combined waveform
	PulseSawTri,   // Bits 4+5+6 - combined waveform
};

DECLARE_METASOUND_ENUM(
	ESIDWaveform,
	ESIDWaveform::Sawtooth,
	SIDMETASOUNDNODES_API,
	FEnumSIDWaveform,
	FEnumSIDWaveformInfo,
	FEnumSIDWaveformReadRef,
	FEnumSIDWaveformWriteRef
);

// ============================================================================
// SID Filter mode (matches SID register 24 bits 4-6)
// ============================================================================
UENUM()
enum class ESIDFilterMode : uint8
{
	LowPass,      // Bit 4 - warm, muffled
	BandPass,     // Bit 5 - nasal, vocal
	HighPass,     // Bit 6 - thin, bright
	Notch,        // Bits 4+6 (LP+HP) - phaser-like
	LowBand,      // Bits 4+5 - thick low end
	BandHigh,     // Bits 5+6 - crispy
	All,           // Bits 4+5+6 - all modes combined
};

DECLARE_METASOUND_ENUM(
	ESIDFilterMode,
	ESIDFilterMode::LowPass,
	SIDMETASOUNDNODES_API,
	FEnumSIDFilterMode,
	FEnumSIDFilterModeInfo,
	FEnumSIDFilterModeReadRef,
	FEnumSIDFilterModeWriteRef
);

// ============================================================================
// SID Chip model
// ============================================================================
UENUM()
enum class ESIDChipModel : uint8
{
	MOS6581,  // Warm, non-linear filter, DC offset, classic C64 (1982)
	MOS8580,  // Cleaner, linear filter, no DC, C64C/C128 (1985)
};

DECLARE_METASOUND_ENUM(
	ESIDChipModel,
	ESIDChipModel::MOS6581,
	SIDMETASOUNDNODES_API,
	FEnumSIDChipModel,
	FEnumSIDChipModelInfo,
	FEnumSIDChipModelReadRef,
	FEnumSIDChipModelWriteRef
);
