//  ---------------------------------------------------------------------------
//  This file is part of reSID, a MOS6581 SID emulator engine.
//  Copyright (C) 2004  Dag Lem <resid@nimrod.no>
//
//  This program is free software; you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation; either version 2 of the License, or
//  (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program; if not, write to the Free Software
//  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
//  ---------------------------------------------------------------------------

// Modifications for TeensySID (Teensy 4.1) - ported from SIDKick-pico
// Original SIDKick modifications by Carsten Dachsbacher

#ifndef __SID16_H__
#define __SID16_H__

#include "siddefs.h"
#include "voice.h"
#include "filter.h"
#include "extfilt.h"
#include "pot.h"

class SID16
{
public:
  SID16();
  ~SID16();

  void set_chip_model(chip_model model);
  void enable_filter(bool enable);
  void enable_dithering(bool enable);  // SIDKIT v0.1.1
  void enable_external_filter(bool enable);

  // =========================================================================
  // SIDKIT Extension API (v0.1.8) - All opt-in, zero cost when disabled
  // =========================================================================

  // Per-voice volume (0-282, 256=unity, 282=110% overdrive)
  inline void setVoiceVolume(int v, int vol) { if (v >= 0 && v < 3) voice_volume[v] = vol; }
  inline int getVoiceVolume(int v) const { return (v >= 0 && v < 3) ? voice_volume[v] : 256; }
  inline void enableVoiceVolume(bool enable) { voice_volume_enabled = enable; }
  inline bool isVoiceVolumeEnabled() const { return voice_volume_enabled; }

  // FM cross-modulation (source: 0=off, 1=OSC1, 2=OSC2, 3=OSC3)
  inline void setFM(int v, int source, int amount) {
    if (v >= 0 && v < 3) { fm_mod_source[v] = source - 1; fm_mod_depth[v] = amount; }
  }
  inline int getFMSource(int v) const { return (v >= 0 && v < 3) ? fm_mod_source[v] + 1 : 0; }
  inline int getFMAmount(int v) const { return (v >= 0 && v < 3) ? fm_mod_depth[v] : 0; }
  inline void enableFM(bool enable) { fm_enabled = enable; }
  inline bool isFMEnabled() const { return fm_enabled; }

  // Resonance boost (0-255, 0=stock, 255=self-oscillation)
  inline void setResBoost(int boost) { res_boost = boost; filter.set_resonance_boost(boost); }
  inline int getResBoost() const { return res_boost; }
  inline void enableResBoost(bool enable) { res_boost_enabled = enable; if (enable) filter.set_resonance_boost(res_boost); else filter.set_resonance_boost(0); }
  inline bool isResBoostEnabled() const { return res_boost_enabled; }

  // Monitoring API (read current state for visualization)
  inline int getVoiceOutput(int v) { return (v >= 0 && v < 3) ? voice_output[v] : 0; }
  inline int getEnvelopeOutput(int v) { return (v >= 0 && v < 3) ? voice[v].envelope.output() : 0; }
  inline int getMasterVolume() { return filter.vol; }
  inline int getFilterCutoff() { return filter.fc; }

  // Legacy API (deprecated, implementations in sid_impl.h call new API)
  void set_voice_volume(int voice, int vol);
  void set_resonance_boost(int boost);
  void set_fm_mod(int carrier, int modulator, int depth);
  void set_soft_sync(int voice, int amount);  // SIDKIT v0.1.7: 0=hard, 255=soft (stock SID behavior)
  bool set_sampling_parameters(float clock_freq, sampling_method method,
			       float sample_freq, float pass_freq = -1,
			       float filter_scale = 0.97);
  void adjust_sampling_frequency(float sample_freq);

  //void fc_default(const fc_point*& points, int& count);
  //PointPlotter<sound_sample> fc_plotter();

  void clock();
  void clock(cycle_count delta_t);
  int clock(cycle_count& delta_t, short* buf, int n, int interleave = 1);
  void reset();
  
  // Read/write registers.
  reg8 read(reg8 offset);
  void write(reg8 offset, reg8 value);
  void readRegisters( unsigned char *p );

  // Read/write state.
  class State
  {
  public:
    State();

    char sid_register[0x20];

    reg8 bus_value;
    cycle_count bus_value_ttl;

    reg24 accumulator[3];
    reg24 shift_register[3];
    reg16 rate_counter[3];
    reg16 rate_counter_period[3];
    reg16 exponential_counter[3];
    reg16 exponential_counter_period[3];
    reg8 envelope_counter[3];
    EnvelopeGenerator::State envelope_state[3];
    bool hold_zero[3];
  };
    
  State read_state();
  void write_state(const State& state);

  // 16-bit input (EXT IN).
  void input(int sample);

  // 16-bit output (AUDIO OUT).
  int output();
  // n-bit output.
  int output(int bits);

  void forceDigiOutput( int voice, int value );

  // Direct modulation access (bypasses register writes for audio-rate modulation)
  inline void setVoiceFreqDirect(int v, reg24 freq) { voice[v].wave.freq = freq; }
  inline void setFilterCutoffDirect(reg12 fc) { filter.fc = fc; }
  inline void setPulseWidthDirect(int v, reg12 pw) { voice[v].wave.pw = pw; }

  // SIDKIT v0.1.4: Getters for ModMatrix cross-SID routing
  inline int16_t getVoiceWaveform(int v) { return prev_waveform[v]; }  // For FM mod source
  inline reg24 getVoiceFreq(int v) { return voice[v].wave.freq; }      // Current frequency
  inline reg24 getVoiceAccumulator(int v) { return voice[v].wave.accumulator; }  // Phase

  #ifdef USE_RGB_LED
  int voiceOut[ 3 ];
  #endif

protected:
  static float I0(float x);
  RESID_INLINE int clock_fast(cycle_count& delta_t, short* buf, int n,
			      int interleave);
  RESID_INLINE int clock_interpolate(cycle_count& delta_t, short* buf, int n,
				     int interleave);
  RESID_INLINE int clock_resample_interpolate(cycle_count& delta_t, short* buf,
					      int n, int interleave);
  RESID_INLINE int clock_resample_fast(cycle_count& delta_t, short* buf,
				       int n, int interleave);

  Voice voice[3];
  Filter filter;
  ExternalFilter extfilt;
  Potentiometer potx;
  Potentiometer poty;

  reg8 bus_value;
  cycle_count bus_value_ttl;

  float clock_frequency;

  // External audio input.
  int ext_in;

  // Resampling constants.
  // The error in interpolated lookup is bounded by 1.234/L^2,
  // while the error in non-interpolated lookup is bounded by
  // 0.7854/L + 0.4113/L^2, see
  // http://www-ccrma.stanford.edu/~jos/resample/Choice_Table_Size.html
  // For a resolution of 16 bits this yields L >= 285 and L >= 51473,
  // respectively.
  static const int FIR_N = 125;
  static const int FIR_RES_INTERPOLATE = 285;
  static const int FIR_RES_FAST = 51473;
  static const int FIR_SHIFT = 15;
  static const int RINGSIZE = 16384;

  // Fixpoint constants (16.16 bits).
  static const int FIXP_SHIFT = 16;
  static const int FIXP_MASK = 0xffff;

  // Sampling variables.
  sampling_method sampling;
  cycle_count cycles_per_sample;
  cycle_count sample_offset;
  int sample_index;
  short sample_prev;
  int fir_N;
  int fir_RES;

  int v0p;
  int forceOutput[ 3 ];

  // SIDKIT v0.1.8: Extension state (all opt-in)
  int8_t fm_mod_source[3] = {-1, -1, -1};  // -1=off, 0/1/2=voice
  int16_t fm_mod_depth[3] = {0, 0, 0};      // 0-255
  int16_t prev_waveform[3] = {0, 0, 0};     // Previous output for FM
  bool fm_enabled = false;                  // FM master enable

  int voice_volume[3] = {256, 256, 256};    // Per-voice volume (256=unity)
  bool voice_volume_enabled = false;        // Voice volume master enable

  int res_boost = 0;                        // Resonance boost (0-255)
  bool res_boost_enabled = false;           // Resonance boost enable

  int voice_output[3] = {0, 0, 0};          // Cached voice output for monitoring

  // Ring buffer with overflow for contiguous storage of RINGSIZE samples.
  short* sample;

  // FIR_RES filter tables (FIR_N*FIR_RES).
  short* fir;
};

// Include implementation (header-only build)
#ifndef RESID_HEADER_ONLY
#include "sid_impl.h"
#endif

#endif // not __SID_H__
