# Ghost Spring Reverb — Exact Parts Specification

This document lists every component with exact values, a suggested part number, and the engineering reason it was chosen. The builder should not substitute without understanding the rationale first.

---

## Spring Tank

| Ref | Part | Value / PN | Why |
|---|---|---|---|
| RT1 | Accutronics spring tank | **9AB3C1B** | 3-spring long-decay tank, 8Ω input / 2550Ω output. The "A" decay code = long decay — the sustained ambient tail Jerry Garcia's sound requires. 3 springs give a denser, more uniform tail than 2-spring tanks, which can produce a metallic "ping" on hard attacks. The 8Ω input matches the REB3S transformer secondary exactly — no impedance mismatch, no power loss, no high-frequency rolloff. |

---

## Driver Transformer

| Ref | Part | Value / PN | Why |
|---|---|---|---|
| T2 | Accutronics reverb driver transformer | **REB3S** | Specifically designed for driving spring reverb tanks. The transformer's primary inductance forms a resonant circuit with the tank's input impedance, producing a slight peak at ~2–3kHz on attack transients — this is the "drip" character of the original Fender 6G15 that no direct solid-state drive can replicate. Also provides galvanic isolation between the driver transistor and the spring tank, eliminating any DC offset risk to the tank coil. 8Ω secondary matches RT1 input directly. |

---

## Transistor

| Ref | Part | Package | Why |
|---|---|---|---|
| Q1 | BD139 NPN | TO-126 | High-current NPN bipolar transistor rated 1.5A / 80V. Used as the Class A driver amplifier that pushes current through T2's primary. At ~19mA quiescent current it runs well within ratings with minimal heat. The TO-126 package mounts flat to the chassis for passive heatsinking if ever needed. BD139 has high hFE linearity at low currents — critical for low distortion in the driver stage. Do not substitute a TO-92 small-signal transistor (e.g. 2N3904) — insufficient current capacity will clip drive transients and harden the reverb sound. |

---

## Op-Amps

All three signal stages use the same op-amp for consistency of character and simplified sourcing.

| Ref | Part | Package | Qty | Why |
|---|---|---|---|---|
| U1, U2, U3 | Texas Instruments OPA2134PA | DIP-8 (dual) | **2 packages** (4 sections — 3 used, 1 spare) | FET-input op-amp with extremely high input impedance (10¹³Ω) — essential for U2 (Recovery), which must load the tank's 2550Ω output without attenuating the signal. THD+N = 0.00008% — audibly transparent. Slew rate 20V/µs eliminates any slew-limiting distortion on pick transients. The OPA2134 is the gold standard for hi-fi audio DIY and is used consistently throughout this circuit so the builder only needs one part number. Do not substitute NE5532 or TL072 — both have higher noise floors and lower input impedance, which will degrade recovery signal quality. |

---

## Resistors

All resistors: **metal film, 1% tolerance, 250mW** (Yageo MFR or Vishay CMF series). Do not use carbon film — higher noise and temperature drift will degrade the signal floor.

| Ref | Value | Location | Why |
|---|---|---|---|
| R1 | 1MΩ | Input to U1 non-inv input | Sets the input impedance seen by the upstream device (Alesis QuadraVerb). 1MΩ places virtually zero load on the QuadraVerb output, preserving the hi-fi signal integrity of the preceding stage. |
| R2 | 100Ω | U1 output (series) | Isolates the op-amp output from capacitive cable loads. Prevents U1 from oscillating when driving a cable to the next stage. Required on all op-amp outputs driving cable runs. |
| R3 | 1kΩ | Dwell pot wiper → Q1 base | Limits base drive current into Q1 and damps any tendency to oscillate at high frequencies. Without this resistor, the Dwell pot wiper impedance varies with rotation, causing the driver gain to be nonlinear. |
| R3b | 6.8kΩ | +15V → Q1 base (upper bias) | Upper leg of the BD139 base voltage divider. With R4, sets base voltage to ~1.96V, which sets emitter at ~1.3V and quiescent collector current at ~19mA. |
| R4 | 1kΩ | Q1 base → GND (lower bias) | Lower leg of the bias divider. Value chosen so divider current (~2mA) is 10× the base current (~0.19mA), making the bias point stable against transistor hFE variation between units. |
| R5 | 68Ω | Q1 emitter → GND | Emitter degeneration resistor. Sets quiescent current (Ic ≈ Ve/R5 ≈ 1.3V / 68Ω ≈ 19mA) and provides thermal stability — if Q1 heats up and hFE rises, the increased emitter voltage reduces Vbe, self-limiting the current. Without this resistor, the transistor will thermally run away. |
| Ri | 470Ω | U2 inverting input (gain set) | With Rf, sets recovery gain: Gain = 1 + (Rf/Ri) = 1 + (100k/470) = 214× (≈46dB). This brings the spring tank's output (~1–5mV) up to line level (~1Vrms). Value chosen to give correct gain without making the feedback network too high-impedance (which would increase noise). |
| Rf | 100kΩ | U2 feedback (out → inv input) | Feedback resistor that sets recovery gain with Ri. 100kΩ chosen to keep thermal noise contribution below the OPA2134's own input noise. |
| R6 | 5.6kΩ | HPF node → GND | With C4 (100nF), sets the 300Hz wet-signal high-pass corner: f = 1 / (2π × 5600 × 100nF) = 284Hz ≈ 300Hz. This rolls off low-end boom in the reverb tail without affecting the dry signal path. Use 5.6kΩ exactly — 4.7kΩ pushes cutoff to 338Hz (too high), 6.8kΩ drops it to 234Hz (too low, insufficient mud rejection). |
| Rdry | 10kΩ | Dry path → Mix node | Mixing resistor for the dry signal at the Mix pot input. Combines with the wet signal from the Tone stage. Value chosen to balance the two sources — if changed, the effective Mix pot ratio changes. |
| R7 | 100Ω | U3 output (series) | Same role as R2 — isolates U3 from capacitive load of the output cable to the MC100. The MC100's RCA input is ~47kΩ, but the cable itself has capacitance; this resistor prevents U3 oscillation. |
| Rbias | 470Ω | U2 non-inv input → GND | Bias current compensation for U2. The OPA2134 is FET-input so bias current is negligible (~5pA), but this resistor provides a defined DC path to ground at U2's non-inverting input. Without it, the input is floating through the tank's secondary coil, which can cause an offset voltage to build up and clip the recovery stage. |

---

## Capacitors

### Signal Path — Film Only
All capacitors in the signal path **must be film type** (WIMA MKS2 or MKP series). Ceramic capacitors have piezoelectric microphonics and voltage-dependent capacitance (distortion) at audio frequencies — unacceptable in a hi-fi circuit.

| Ref | Value | Type | Location | Why |
|---|---|---|---|---|
| C1 | 1µF / 63V | WIMA MKS2 film | Dwell pot input coupling | Blocks any DC offset from the input buffer output before the driver stage. Prevents DC from biasing the Dwell pot and reaching Q1's base. At 1µF with the ~10kΩ driver input impedance, the high-pass corner is ~16Hz — well below guitar fundamentals, so no bass rolloff in the reverb drive. |
| C3 | 470nF / 63V | WIMA MKS2 film | Tank output → U2 input | Blocks DC from the tank's output terminals. The tank output coil can develop a small DC offset; this cap prevents it from reaching U2's input and causing an output DC offset that would clip the mix stage. 470nF with the ~10kΩ U2 input impedance gives a corner at ~34Hz — passes all audio frequencies. |
| C4 | 100nF / 63V | WIMA MKS2 film | HPF — wet signal | Sets the 300Hz wet HPF corner with R6. Film type is mandatory here — a ceramic cap would shift value with temperature, drifting the cutoff frequency. WIMA MKS2 is stable to ±5% over the full operating temperature range. |
| C_bright | 47pF | Silver mica | Across RV2 Mix pot | Bright cap — maintains high-frequency content in the reverb tail at low mix settings. The Mix pot acts as a voltage divider at audio frequencies; at low settings it attenuates high frequencies more than low. The 47pF cap bypasses the pot for HF, keeping the reverb "glassy." Silver mica is specified for its extreme stability (±1% over temperature) and lowest possible distortion at high frequencies. Do not use ceramic disc — it will add HF distortion audible in reverb tails. |

### Signal Path — Electrolytic
| Ref | Value | Type | Location | Why |
|---|---|---|---|---|
| C2 | 100µF / 25V | Nichicon UKW (low-ESR audio grade) | Q1 emitter bypass | Bypasses R5 at audio frequencies, allowing full AC gain from the driver stage. Without this cap, R5 provides heavy degeneration at audio frequencies and the spring tank is underdriven. Low-ESR audio grade is specified because a high-ESR cap will not effectively bypass R5 at high audio frequencies — the driver's HF response will roll off early, losing the "air" in the reverb sound. |

### Op-Amp Decoupling — Film
| Ref | Value | Type | Location | Why |
|---|---|---|---|---|
| C5–C10 | 100nF / 63V | WIMA MKS2 film | One per op-amp supply pin (6 total — 2 per OPA2134 package, ×3 stages) | Prevents high-frequency noise on the ±15V supply rails from entering the op-amp and appearing as distortion on the output. Must be placed as close to the supply pins as physically possible on the PCB/perfboard. If omitted, the circuit will likely oscillate or have a high noise floor. |

### Op-Amp Decoupling — Bulk Electrolytic
| Ref | Value | Type | Location | Why |
|---|---|---|---|---|
| C11–C12 | 10µF / 25V | Nichicon UKW | One per rail at PCB power entry | Bulk energy storage at the board level. Handles sudden current demands (e.g. when the driver stage is hit with a loud transient) without drooping the supply voltage. Works in parallel with the 100nF film caps — the 10µF handles low frequencies, 100nF handles high frequencies. |

### Power Supply Capacitors
| Ref | Value | Type | Location | Why |
|---|---|---|---|---|
| C13–C14 | 2200µF / 35V | Nichicon KW (low-ESR) | Main filter after bridge rectifier | Primary AC ripple filtering. 2200µF per rail is sized so that at 20mA load, ripple voltage stays below 1Vrms — keeping well within the LM7815/7915 input range. Low-ESR specified to minimize heat dissipation and maintain regulation at audio-frequency load variations. |
| C15–C16 | 100µF / 35V | Nichicon KW | LM7815/7915 output | Regulator output stability cap. The LM78xx/79xx series requires a capacitor on the output to prevent oscillation. 100µF also provides local energy storage for the op-amp stages. |
| C17–C18 | 100nF / 63V | WIMA MKS2 film | In parallel with C15–C16 | HF bypass on the regulator output. The electrolytic caps above are ineffective above ~100kHz; the film caps handle RF suppression and keep the supply quiet across the full audio band and beyond. |

---

## Potentiometers

| Ref | Value | Taper | Part | Why |
|---|---|---|---|---|
| RV1 (Dwell) | 10kΩ | **Linear (B)** | Alpha 16mm B10K | Controls the signal level into the driver stage. Linear taper is correct here — the relationship between pot rotation and spring drive level should be proportional. An audio (log) taper would compress most of the useful range into the last 30% of rotation. |
| RV2 (Mix) | 100kΩ | **Audio (A)** | Alpha 16mm A100K | Controls dry/wet blend. Audio taper provides a perceptually even crossfade — at 50% rotation the mix sounds balanced, not heavily wet-biased as it would be with a linear pot. |
| RV3 (Tone) | 100kΩ | **Audio (A)** | Alpha 16mm A100K | Controls the high-shelf EQ on the wet signal only. Audio taper ensures the tone sweep feels even across the full rotation rather than most of the action happening at one end. |

---

## Jacks

| Ref | Part | Why |
|---|---|---|
| J1 (Line In) | Switchcraft 112A — ¼" TS mono | Switchcraft is the professional standard for 1/4" connectors. Nickel-plated contacts, low and stable contact resistance. Open-circuit switching (unloads input when nothing is plugged in). Do not use inexpensive "Cliff" or generic jacks — contact resistance variation causes noise, especially with high-impedance sources. |
| J2 (Line Out) | Switchcraft 112A — ¼" TS mono | Same as J1. The output jack sees the full line-level signal going to the MC100 — compromised contact resistance here adds directly to the noise floor of the entire rig. |

---

## Power Supply

| Ref | Part | Spec | Why |
|---|---|---|---|
| T1 | Antek AN-0115 (or equivalent toroidal) | 15VA, dual 15VAC secondary | Toroidal transformers have ~10× lower magnetic field leakage than standard E-I laminate transformers. This is critical in a reverb unit — the spring tank is a sensitive magnetic transducer and will pick up 60Hz hum from a nearby transformer. The toroidal's closed-core geometry keeps the field contained. 15VA is sized at 5× the actual load (~3VA) for cool, quiet operation. |
| BR1 | Vishay W02G | 1A / 200V bridge rectifier | Converts transformer AC to pulsating DC. 200V rating is derated 2× from the peak voltage (~42V peak from dual 15VAC) for long-term reliability. |
| U4 | LM7815 (TO-220) | +15V linear regulator | Sets the positive supply rail. Linear regulators produce zero switching noise — essential for a hi-fi circuit. Switching regulators (buck converters, etc.) inject kHz-range noise that passes through the op-amp supply rejection and appears as distortion. The LM7815 is proven, inexpensive, and stable. Mount to the chassis with a small insulating pad for heatsinking. |
| U5 | LM7915 (TO-220) | −15V linear regulator | Same rationale as U4. The negative rail powers the inverting inputs and negative supply pins of all op-amps. |

---

## Hardware & Chassis

| Item | Spec | Why |
|---|---|---|
| Chassis | Hammond 1455T2201 2U aluminum rackmount (or equivalent) | Aluminum is mandatory — steel chassis would be a magnetic shield but would also interact with the toroidal transformer's residual field. Aluminum is non-magnetic, lightweight, and provides adequate RF shielding. 2U gives sufficient internal height to mount the 9AB3C1B tank horizontally with clearance. |
| Front panel | Custom aluminum via Front Panel Express | Laser-drilled aluminum front panel with engraved labels. Aluminum does not corrode and maintains a consistent ground connection to the chassis. The panel must be grounded to chassis to shield the controls from RF pickup (especially the Dwell pot, which is in the high-gain driver section). |
| Tank grommets | 4× M3 soft silicone/rubber isolation grommets (Shore 30A or softer) | The spring tank must be mechanically decoupled from the chassis. Any vibration transmitted through the chassis (footsteps, rack fans, amp vibration) will be picked up by the springs as noise. Soft grommets prevent this. Shore 30A or softer is essential — harder rubber transmits more vibration. |
| IC sockets | 2× DIP-8 machine-pin sockets | Allows the OPA2134 op-amps to be replaced without desoldering. Machine-pin (turned-pin) sockets maintain reliable contact over years of use and do not add audible resistance. Spring-contact (leaf-spring) sockets degrade over time and can cause intermittent noise. |
| Hookup wire (signal) | Belden 8451 shielded twisted pair, 24AWG | All internal signal connections must be made with shielded wire. The reverb circuit has high-gain stages (U2 at 214×) — any unshielded wire in the high-gain section will act as an antenna and pick up hum. Belden 8451 is the industry standard for internal audio wiring. |
| Hookup wire (power) | 22AWG stranded, rated 300V | Power connections from the transformer secondary and between regulator components. Stranded wire is mandatory — solid wire will work-harden and break at solder joints over time due to vibration. |
| Fuse | 500mA slow-blow | Protects the transformer and wiring. Slow-blow type is essential — the transformer inrush current at power-on will blow a fast-blow fuse immediately. 500mA is sized above the ~200mA operating current but below the transformer's thermal limit. |
| Power switch | SPST rocker, 6A/250V rated | Interrupts the mains before the transformer primary. 6A rating is massive overkill for this circuit but ensures zero contact heating and long life. |

---

## Build Notes for Dan Jams LLC

1. **Grounding:** Use a single-point star ground connected to the chassis at one point. All circuit grounds (op-amp ground pins, pot grounds, jack grounds) run back to this single point. Do not daisy-chain grounds — ground loops cause hum.

2. **Decoupling caps:** Place C5–C10 (100nF film) physically as close to the OPA2134 supply pins as possible. If they are more than 1" away from the IC, they will not effectively suppress HF noise.

3. **Tank orientation:** Mount RT1 open-side down, horizontally. If mounted open-side up, the springs can shift position over time and the reverb character will drift.

4. **Transformer placement:** Mount T1 as far from RT1 as the chassis allows and orient it so the transformer's toroid axis is perpendicular to the tank's spring axis. This minimizes inductive coupling between transformer and tank (which causes 60Hz hum in the reverb tail).

5. **Shielding the recovery stage:** The wire from RT1's output (2550Ω side) to U2's non-inverting input (Rbias → C3 → U2) carries the most sensitive signal in the entire circuit — approximately 1–5mV. This wire must be shielded (Belden 8451) with the shield grounded at the U2 end only (not at the tank end — one-end grounding prevents a ground loop through the shield).
