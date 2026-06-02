# Low-Impedance Output Buffer Circuit

## Requirements

The custom reverb tank's output buffer must:
- Present a **low output impedance** (<100Ω) to drive the McIntosh MC100's ~100kΩ RCA input
- Provide **clean, unity-gain buffering** (no coloration)
- Drive **long cable runs** without treble loss
- Have **high input impedance** to avoid loading the mix stage
- Be **quiet** (low noise, no hum)

## Recommended Topology: Op-Amp Voltage Follower

### Schematic (Simplified)

```
                      +15V
                       │
                      ─── C1 (100nF bypass)
                       │
                       │    ┌───────────┐
Input (from Mix) ──┬───┼────┤+          │
                   │   │    │  NE5532   ├─── Output
                   R1  │ ┌──┤-   (1/2)  │
                  1MΩ  │ │  └───────────┘
                   │   │ │       │
                   GND │ │      ─── C2 (100nF bypass)
                       │ │       │
                       └─┼───────┤
                         │      -15V
                         │
                        R2 100Ω
                         │
                        GND
```

The op-amp is configured as a **non-inverting unity-gain buffer** (voltage follower). Output is connected directly to the inverting input. This provides:
- Input impedance: ~1MΩ (set by R1, optional but good practice)
- Output impedance: <1Ω at audio frequencies (op-amp closed-loop output)
- Bandwidth: >100kHz (well beyond audio)
- THD: <0.001% (inaudible)
- Optional output series resistor (R2, 47–100Ω) for short-circuit protection

### Why NE5532

- Industry-standard audio op-amp
- Very low noise (5 nV/√Hz)
- Drives 600Ω loads easily (overkill for 100kΩ MC100 input)
- Widely available, inexpensive
- Dual package — second op-amp can be used for input buffer or recovery stage

### Power Supply

The op-amp requires a **bipolar ±15V supply**. This is standard for pro audio gear and can be generated from:
- A center-tapped transformer secondary (15-0-15V AC → rectified ±21V → regulated ±15V)
- An AC wall wart + DC-DC converter module (simpler but potentially noisier)
- A standard 2x15V toroidal or EI transformer + bridge rectifier + LM7815/LM7915 regulators (recommended)

## Alternative: Discrete Buffer (JFET + BJT)

For a more "boutique" approach, a discrete JFET-input buffer:

```
                       Vcc (+9 to +24V)
                         │
                        R3 10k
                         │
                         ├── Output (via coupling cap)
                         │
                         │   C
             Input ──────┤── B   (NPN, BC550 or 2N5088)
                     JFET   │ E
                   (J201/2N5457) │
                     S├──────────┘
                       │
                      R2 4.7k
                       │
                       GND
```

- Input impedance: Very high (JFET gate, >10MΩ)
- Output impedance: ~100Ω (emitter follower)
- Simpler circuit, single-rail supply
- Slightly more harmonic coloration (JFET character)
- No negative supply needed

## Recommendation

Use the op-amp voltage follower (NE5532 or OPA2134) for the output buffer. It's cleaner, simpler to design, and achieves the sub-100Ω output impedance goal with no fuss. If the goal is maximum "vintage character," the discrete JFET buffer could be used for the input/driver stages while the op-amp handles the output.

## MC100 Input Interface

- MC100 has **RCA unbalanced inputs** with ~100kΩ input impedance
- Use a high-quality 1/4" TS to RCA cable, or install an RCA jack on the reverb unit's rear panel
- Keep the cable between reverb output and MC100 input short (<6ft) to avoid hum pickup
- If hum is an issue, consider adding a ground lift switch or a balancing transformer
