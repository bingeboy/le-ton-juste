# JBL E120-8 Speakers

## Specifications

| Parameter | Value |
|---|---|
| Model | JBL E120-8 |
| Nominal Impedance | 8Ω |
| Power Rating | 150W RMS |
| Sensitivity | ~103dB (1W/1m) |
| Size | 12" |
| Voice Coil | 4" edge-wound copper |
| Dust Cap | Aluminum dome |
| Frequency Response | 50Hz–6kHz (±3dB) |
| Weight | ~22 lbs each |

## Why JBLs for the Jerry/Bob Tone

The JBL D120F (Fender branded), K120, and E120 were the speakers that defined Jerry Garcia's tone. Key characteristics:

1. **Aluminum dome dust cap.** Extended high-frequency response compared to traditional paper-dome guitar speakers. This gives the "glassy," articulate top end.
2. **Wide, flat frequency response.** Designed more like studio monitors than guitar speakers. No midrange honk. Equal energy across the spectrum.
3. **Very high power handling.** Each E120 handles 150W RMS. Two in parallel handle 300W into a 100W amp — essentially impossible to blow.
4. **No speaker breakup.** Unlike Celestions or Jensens that compress and distort at high volume, JBLs stay clean and articulate. This is essential to the hi-fi approach.
5. **Tight, punchy bass.** The 4" voice coil provides excellent cone control at low frequencies.

## Current Wiring — Parallel Configuration

```
MC100 4Ω Tap
    ├── JBL E120-8 #1 (+) → 1+
    ├── JBL E120-8 #1 (−) → 1−
    ├── JBL E120-8 #2 (+) → 1+
    └── JBL E120-8 #2 (−) → 1−
```

- Two 8Ω speakers in parallel = **4Ω total load**
- MC100 set to **4Ω output tap** via autoformer
- Cable: Canare 4S11 speaker cable (4-conductor, 14 AWG)
- Connector: Neutrik Speakon NL4FC (NL4FX)

### Canare 4S11 Wiring (to NL4FC)

```
R+W conductors = Pin 1+ (hot)
B+Black conductors = Pin 1− (cold/ground)
```

## Cabinet Notes

- JBL E120s are heavy — each speaker weighs ~22 lbs. Cabinet must be robust.
- The aluminum dome is delicate — grille cloth is essential for protection.
- Ported or sealed cab? JBLs work well in both. Garcia's Wall of Sound columns were sealed. A well-braced sealed 2x12 would be historically informed and sonically tight.
- JBL E120s are extremely efficient (103dB). Even 10W is very loud. The MC100 at half power is deafening.
