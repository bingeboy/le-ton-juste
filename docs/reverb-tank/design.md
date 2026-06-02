# Custom Spring Reverb Tank — Design Document

## Concept

A rackmount spring reverb unit that sits **last in the signal chain before the McIntosh MC100 power amp**. Based on the Fender 6G15 Reverb Unit topology (which Jerry Garcia used between his Alembic F-2B and McIntosh MC2300), but modernized for rack format with a solid-state low-impedance output buffer.

## Signal Path

```
Line In (from QuadraVerb/Preamp)
    ↓
Input Buffer (high-Z in, low-Z out)
    ↓
Dwell Control (how hard springs are driven)
    ↓
Spring Driver Stage
    ↓
Spring Tank (Accutronics/Belton)
    ↓
Recovery Preamp (brings transducer output to line level)
    ↓
Tone Control (wet signal only)
    ↓
Mix Control (dry/wet blend)
    ↓
Output Buffer (low-impedance, ~100Ω out)
    ↓
Line Out (to McIntosh MC100)
```

## Design Decisions

### Tube vs. Solid State

The Fender 6G15 uses a 12AT7 driver and 12AX7 recovery — both tubes. For this build:

**Solid state option (recommended for this rig):**
- Cleaner, more transparent
- Lower noise floor
- Easier to achieve the low-impedance output buffer requirement
- No tube maintenance or microphonics
- Can use high-quality op-amps (NE5532, OPA2134) for the recovery and buffer stages

**Tube option (more authentic to Jerry):**
- Adds subtle harmonic coloration from the recovery stage
- Requires a power transformer and high-voltage supply
- More complex build
- The 6G15 circuit is well-documented and proven

**Recommendation:** Start with solid state for the output buffer, and evaluate whether a tube driver/recovery stage adds desirable coloration. The output buffer MUST be solid state to achieve the low-impedance requirement.

### Spring Tank Selection

| Parameter | Common Values | Recommended |
|---|---|---|
| Type | Accutronics 4AB3C1B (long decay) or 8EB2C1B (medium decay) | 8EB2C1B or 9EB2C1B |
| Input Impedance | 8Ω (type 8) or 10Ω (type 9) | Type 8 or 9 |
| Output Impedance | 2250Ω (type E), 2575Ω (type B) | Type E or B |
| Decay | Short (1), Medium (2), Long (3) | Medium (2) for Jerry tone |
| Mounting | Horizontal open-side down | Rack chassis floor mount with grommets |

### Output Buffer Requirements

The MC100 has ~100kΩ input impedance (RCA). The output buffer should:
- Output impedance: <100Ω (for driving cables and the MC100 input)
- Drive capability: Clean signal up to +20dBu
- Unity gain or slight boost to compensate for reverb circuit insertion loss
- Low noise: -90dB or better
- Optional balanced output (XLR) for future flexibility

### Panel Layout

**Front Panel (1U or 2U):**
- Dwell (10k linear pot)
- Tone (100k audio pot with capacitor high-shelf or low-pass)
- Mix (100k audio pot — dry to wet blend)
- Power LED

**Rear Panel:**
- 1/4" TS Input
- 1/4" TS Output
- Optional: 1/4" TS Send/Return (for using an external tank)
- Optional: XLR balanced output
- IEC Power inlet (with fuse)
- Power switch (if not on front panel)

## Gain Staging

```
Line In (~1V / +0dBu)
    → Input Buffer (unity gain)
    → Dwell control (attenuates to control spring drive)
    → Driver (current gain, drives 8Ω tank input)
    → [Spring Tank — mechanical gain ~30-40dB loss]
    → Recovery Preamp (~35-40dB gain, brings back to line level)
    → Tone (passive or active)
    → Mix (dry + processed wet)
    → Output Buffer (unity gain, low-Z out)
    → Line Out (~1V / +0dBu)
```

## Form Factor

**Rackmount chassis:** 1U (1.75") or 2U (3.5") aluminum enclosure.
- 1U is tight — requires PCB-based construction and careful layout
- 2U gives room for the spring tank internal mounting, tube circuits if desired, and better ventilation
- Standard 19" rack width, depth TBD based on tank length

The spring tank can be:
1. **Internally mounted** — simplest, but may pick up mechanical vibration from the rack
2. **Externally mounted** — requires a separate enclosure for the tank with send/return cables; better isolation

**Recommendation:** Internal mount in a 2U chassis with heavy-duty grommet isolation. 2U provides enough depth to mount a 17" tank.

## References

- Fender 6G15 Reverb Unit schematic (available at fenderguru.com and other sources)
- Accutronics/Belton reverb tank datasheets
- Classic op-amp textbook circuits for recovery and buffer stages
