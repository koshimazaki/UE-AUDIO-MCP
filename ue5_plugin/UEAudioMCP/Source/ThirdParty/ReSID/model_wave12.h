// 12-bit wave tables for combined waveforms (VICE reSID format)
// model_wave[chip_model][waveform][4096]
// chip_model: 0=6581, 1=8580
// waveform: 0-7 (triangle, saw, tri+saw, pulse, pulse+tri, pulse+saw, pulse+tri+saw, noise)
//
// Basic waveforms (0-4) are computed at runtime in wave_impl.h
// Combined waveforms (5-7) are from measured SID chips

#ifndef MODEL_WAVE12_H
#define MODEL_WAVE12_H

const unsigned short model_wave[ 2 ][ 8 ][ 1 << 12 ] = {
  // MOS6581
  {
    {0},  // 0: None (computed)
    {0},  // 1: Triangle (computed)
    {0},  // 2: Sawtooth (computed)
#include "wave6581__ST.h"  // 3: Triangle + Sawtooth
    {0},  // 4: Pulse (computed)
#include "wave6581_P_T.h"  // 5: Pulse + Triangle
#include "wave6581_PS_.h"  // 6: Pulse + Sawtooth
#include "wave6581_PST.h"  // 7: Pulse + Sawtooth + Triangle
  },
  // MOS8580
  {
    {0},  // 0: None (computed)
    {0},  // 1: Triangle (computed)
    {0},  // 2: Sawtooth (computed)
#include "wave8580__ST.h"  // 3: Triangle + Sawtooth
    {0},  // 4: Pulse (computed)
#include "wave8580_P_T.h"  // 5: Pulse + Triangle
#include "wave8580_PS_.h"  // 6: Pulse + Sawtooth
#include "wave8580_PST.h"  // 7: Pulse + Sawtooth + Triangle
  }
};

#endif // MODEL_WAVE12_H
