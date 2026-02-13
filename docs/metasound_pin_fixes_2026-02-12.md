# MetaSounds Catalogue Pin Fix - 2026-02-12

## Summary

Fixed pin names in `/src/ue_audio_mcp/knowledge/metasound_nodes.py` to match ground truth engine export data from UE 5.7.2.

**Verified nodes:** 8 critical nodes now match engine export perfectly  
**Total catalogue:** 174 nodes loaded successfully  
**Ground truth source:** `/exports/all_metasound_nodes.json` (157 engine nodes)

---

## Fixed Nodes

### 1. Wave Player (Mono) — `UE::Wave Player::Mono`
- **Added input:** `Maintain Audio Sync` (Bool, optional)
- **Added outputs:** `On Play`, `On Cue Point`, `Cue Point ID`, `Cue Point Label`, `Loop Percent`, `Playback Location`, `Playback Time`
- **Changed:** Output `Audio` → `Out Mono`
- **Changed:** Input `Loop` default `False` → `True`
- **Removed:** Default values from optional inputs (Start Time, Pitch Shift, Loop Start)

### 2. Wave Player (Stereo) — `UE::Wave Player::Stereo`
- Same input changes as Mono variant
- **Fixed output order:** Metadata outputs first, audio outputs (Out Left, Out Right) at end
- **Changed:** `Loop Ratio` → `Loop Percent`
- **Changed:** `Playback Time` type `Time` → `Float`

### 3. ADSR Envelope (Audio) — `ADSR Envelope::ADSR Envelope::Audio`
**CRITICAL:** This node has TWO trigger inputs, not one!

**Old:**
```
Inputs: Trigger, Attack, Decay, Sustain, Release
Outputs: Envelope, OnDone
```

**New:**
```
Inputs: Trigger Attack, Trigger Release, Attack Time, Decay Time, 
        Sustain Level, Release Time, Attack Curve, Decay Curve, 
        Release Curve, Hard Reset
Outputs: On Attack Triggered, On Decay Triggered, On Sustain Triggered,
         On Release Triggered, On Done, Out Envelope
```

### 4. InterpTo — `UE::InterpTo::Audio`
**REMOVED:** `Current` input pin does NOT exist!

Node maintains internal state and interpolates toward target value.

**Inputs:** `Interp Time`, `Target`  
**Outputs:** `Value`

### 5. Biquad Filter — `UE::Biquad Filter::Audio`
- Removed default values from all inputs
- `Type` changed to `required=False`
- Added class_name

### 6. Low-Frequency Oscillator — `UE::LFO::Audio`
- Removed all default values (engine provides defaults)
- All inputs except `Frequency` are now `required=False`
- Added class_name

### 7. Noise — `UE::Noise::Audio`
- No pin changes
- Added class_name

### 8. Trigger Filter — `UE::Trigger Filter::None`
- `Probability` default `1.0` → `0.5`
- Added class_name

---

## Template Updates Needed (270 errors found)

### Critical (Breaking Changes)

**ADSR Envelope (Audio)** templates must update:
```diff
- "Trigger" → "Trigger Attack" + "Trigger Release"
- "Attack" → "Attack Time"
- "Decay" → "Decay Time"
- "Sustain" → "Sustain Level"
- "Release" → "Release Time"
- "Envelope" → "Out Envelope"
- "OnDone" → "On Done"
```

**Wave Player** templates must update:
```diff
- "Audio" → "Out Mono" (Mono variant)
- "Loop Ratio" → "Loop Percent" (Stereo variant)
```

**InterpTo** templates must update:
```diff
- REMOVE "Current" pin (does not exist!)
```

Affected templates:
- `weather.json` - has `Current` default on InterpTo
- `wind.json` - has `Current` pin reference + wrong node type references
- `gunshot.json` - ADSR pin names wrong
- `procedural_engine.json` - Wave Player output pins
- Many others (see verification report)

---

## Verification Commands

Check catalogue loads:
```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from ue_audio_mcp.knowledge.metasound_nodes import METASOUND_NODES
print(f'Loaded {len(METASOUND_NODES)} nodes')
"
```

Verify against engine export:
```bash
python3 << 'VERIFY'
import json, sys
sys.path.insert(0, 'src')
from ue_audio_mcp.knowledge.metasound_nodes import METASOUND_NODES
data = json.load(open('exports/all_metasound_nodes.json'))
engine = {n['class_name']: n for n in data['nodes']}
# ... verification logic
VERIFY
```

Check template validation:
```bash
python3 scripts/verify_templates.py
```

---

## Next Actions

1. **Update templates** - Fix 22 MetaSounds templates to use correct pin names
2. **Test with UE5** - Verify Builder API accepts corrected pins
3. **Update docs** - Fix any documentation referencing old pin names
4. **Run tests** - Ensure knowledge base tests pass

---

## Files Modified

- `/src/ue_audio_mcp/knowledge/metasound_nodes.py`

## References

- Ground truth: `/exports/all_metasound_nodes.json`
- Verification: `scripts/verify_templates.py`
- Memory: `~/.claude/projects/-Users-radek-Documents-GIthub-UE5-WWISE/memory/MEMORY.md`

---

**Status:** Catalogue pins fixed ✅  
**Next:** Template updates required ⚠️
