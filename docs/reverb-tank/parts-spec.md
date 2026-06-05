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
| D3 | 1N4148 fast signal diode | Anode → Q1 collector, cathode → +15V rail | Flyback clamp across T2 primary. When Q1 current changes during audio transients, T2's primary inductance generates a voltage spike at Q1's collector. D3 conducts whenever Vc rises above +15V, clamping the spike harmlessly back into the supply rail. Same part as D_clamp+/D_clamp− (input protection) — no new BOM line, just increment the 1N4148 count to 3. |

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
| Ri | 470Ω | U2 gain set — (−) pin to GND | U2 is **non-inverting**: tank signal enters the (+) input; Ri is the lower leg of the feedback divider at the (−) pin. With Rf: Gain = 1 + (Rf/Ri) = 1 + (100k/470) = 214× (≈46dB). Brings tank output (~1–5mV) to line level (~1Vrms). |
| Rf | 100kΩ | U2 feedback — output → (−) pin | Upper leg of the non-inverting feedback divider. 100kΩ chosen to keep thermal noise contribution below the OPA2134's own input noise. |
| R6 | 5.6kΩ | HPF node → GND | With C4 (100nF), sets the 300Hz wet-signal high-pass corner: f = 1 / (2π × 5600 × 100nF) = 284Hz ≈ 300Hz. This rolls off low-end boom in the reverb tail without affecting the dry signal path. Use 5.6kΩ exactly — 4.7kΩ pushes cutoff to 338Hz (too high), 6.8kΩ drops it to 234Hz (too low, insufficient mud rejection). |
| Rdry | 10kΩ | Dry path → Mix node | Mixing resistor for the dry signal at the Mix pot input. Combines with the wet signal from the Tone stage. Value chosen to balance the two sources — if changed, the effective Mix pot ratio changes. |
| R7 | 100Ω | U3 output (series) | Same role as R2 — isolates U3 from capacitive load of the output cable to the MC100. The MC100's RCA input is ~47kΩ, but the cable itself has capacitance; this resistor prevents U3 oscillation. |
| Rbias | 100kΩ | U2 non-inv (+) input → GND | Sets the input impedance of the recovery stage. The standard Rbias = Rf\|\|Ri formula (which gives ~470Ω) applies to BJT op-amps with significant bias current — the OPA2134's 5pA FET input makes that formula irrelevant. With 470Ω the 2550Ω tank drives into a 470Ω load: only 15.6% of the signal transfers, reducing effective gain from 214× to 33×. At 100kΩ, signal transfer is 97.5% and the C3 coupling corner is ~3Hz (purely DC-blocking, no audio attenuation). DC offset from 5pA × 100kΩ = 500nV — inaudible. Sources from the same 100kΩ stock as Rf, no new BOM line required. |

### Mix Stage Topology — Passive Blend into Voltage Follower

The Mix node is a **passive resistive blend**, not an active summing network. There are no virtual-ground summing resistors here.

Signal flow:
- **Dry path:** U1 output → Rdry (10kΩ) → RV2 pin 1 (CCW terminal)
- **Wet path:** RV3 (Tone) wiper → RV2 pin 3 (CW terminal)
- **C_bright** (47pF silver mica) bridges RV2 pin 1 to pin 3 — adds air and treble presence on the wet signal as the pot approaches full wet
- **RV2 wiper** (pin 2) → U3 non-inverting (+) input

At full CCW (dry): wiper is at the Rdry terminal, wet signal is at the other end of the pot and fully attenuated. At full CW (wet): wiper is at the Tone output terminal, dry signal is attenuated through Rdry + pot. At center: passive blend of both paths. The 100kΩ pot value is large enough relative to Rdry (10kΩ) that the Mix pot itself contributes minimal loading to the U3 input.

**U3 (output buffer):** Unity-gain voltage follower. FET input (10¹³Ω) draws negligible current from the wiper — no loading effect on the blend. Output through R7 (100Ω series) to the output jack.

---

## Capacitors

### Signal Path — Film Only
All capacitors in the signal path **must be film type** (WIMA MKS2 or MKP series). Ceramic capacitors have piezoelectric microphonics and voltage-dependent capacitance (distortion) at audio frequencies — unacceptable in a hi-fi circuit.

| Ref | Value | Type | Location | Why |
|---|---|---|---|---|
| C1 | 1µF / 63V | WIMA MKS2 film | Dwell pot input coupling | Blocks any DC offset from the input buffer output before the driver stage. Prevents DC from biasing the Dwell pot and reaching Q1's base. At 1µF with the ~10kΩ driver input impedance, the high-pass corner is ~16Hz — well below guitar fundamentals, so no bass rolloff in the reverb drive. |
| C3 | 470nF / 63V | WIMA MKS2 film | Tank output → U2 input | Blocks DC from the tank's output terminals. The tank output coil can develop a small DC offset; this cap prevents it from reaching U2's input and causing an output DC offset that would clip the mix stage. 470nF with Rbias = 100kΩ gives a corner at ~3Hz — purely DC-blocking, passes all audio frequencies without attenuation. |
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
| C13–C14 | 2200µF / **50V** | Nichicon KW (low-ESR) | Main filter after bridge rectifier | Primary AC ripple filtering. 2200µF per rail keeps ripple below 1Vrms at 20mA load. **Upgraded from 35V to 50V rating** — the unregulated rail sits at ~21V, so 35V was 1.67× margin. 50V gives 2.4× margin. Capacitor lifespan increases significantly when operated well below rated voltage, and the cost difference is negligible. |
| C15–C16 | 100µF / 35V | Nichicon KW | LM7815/7915 output | Regulator output stability cap. The LM78xx/79xx series requires a capacitor on the output to prevent oscillation. 100µF also provides local energy storage for the op-amp stages. |
| C17–C18 | 100nF / 63V | WIMA MKS2 film | In parallel with C15–C16 | HF bypass on the regulator output. The electrolytic caps above are ineffective above ~100kHz; the film caps handle RF suppression and keep the supply quiet across the full audio band and beyond. |

---

## Potentiometers

Military-spec grade. Vishay/Spectrol 296 series — cermet element, MIL-PRF-39023 rated construction, gold-plated wiper, stainless shaft, rated to 10,000+ cycles minimum. Far beyond the Alpha consumer pots originally specced.

**Note on taper:** True MIL-SPEC pots are only certified in linear taper. RV1 (Dwell) is correctly linear. For RV2 (Mix) and RV3 (Tone), the Vishay/Spectrol 296 is specced linear — this is acceptable because the OPA2134 op-amp circuitry provides enough gain that the taper difference is not perceptually significant at line level. If audio taper is strongly preferred, substitute **Bourns PDB18-B415** series (pro audio grade, not formally MIL-certified but built to equivalent standard, available in audio taper).

| Ref | Value | Taper | Part Number | Why |
|---|---|---|---|---|
| RV1 (Dwell) | 10kΩ | Linear | **Vishay/Spectrol 296UAL103B2** | Driver level control. Linear taper is electrically correct here. MIL-PRF-39023 rated cermet element — will not drift over temperature or years of use. Gold wiper ensures zero contact noise. |
| RV2 (Mix) | 100kΩ | Linear (see note above) | **Vishay/Spectrol 296UAL104B2** | Dry/wet blend. Cermet element rated for 10,000 cycles minimum. Gold wiper. Stainless shaft resists corrosion in rack environments. |
| RV3 (Tone) | 100kΩ | Linear (see note above) | **Vishay/Spectrol 296UAL104B2** | Wet signal high-shelf EQ. Same part as RV2 for simplified sourcing. |

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
| BR1 | W04G | 2A / 400V bridge rectifier *(upgraded from W02G 1A)* | Converts transformer AC to pulsating DC. Upgraded to 2A for 10× current margin at 200mA load — the rectifier is the one PSU component that fails silently and takes the whole supply down. 400V rating is derated 10× from the 42V peak. Costs $0.10 more than the W02G. |
| U4 | LM7815 (TO-220) | +15V linear regulator | Sets the positive supply rail. Linear regulators produce zero switching noise — essential for a hi-fi circuit. Switching regulators (buck converters, etc.) inject kHz-range noise that passes through the op-amp supply rejection and appears as distortion. The LM7815 is proven, inexpensive, and stable. Mount to chassis with mica insulating pad and thermal compound. |
| U5 | LM7915 (TO-220) | −15V linear regulator | Same rationale as U4. The negative rail powers the inverting inputs and negative supply pins of all op-amps. |

---

## Protection & Reliability Upgrades

### Mains Protection

| Ref | Part | Spec | Why |
|---|---|---|---|
| MOV1 | Littelfuse V275LA20AP | 275V Metal Oxide Varistor | Clamps mains voltage spikes — lightning nearby, switching transients from other rack gear — before they reach the transformer. Wired directly across the mains input (L to N). When a spike exceeds 275V the MOV conducts and absorbs the energy. Costs $0.75 and protects the entire circuit from the most common real-world fault condition. |
| NTC1 | Ametherm MS32 5006 | 5Ω NTC inrush limiter | Every time the power switch is flipped, the filter caps charge from zero causing a large inrush current spike through BR1 and T1. Over years of power cycles this stresses the rectifier and transformer. The NTC thermistor starts at 5Ω cold (limiting inrush) and drops to near-zero resistance when warm (no effect on normal operation). Wired in series with the mains after the fuse. |
| F1 (IEC) | Schurter 5110.1052 | EMI-filtered IEC inlet with fuse holder | Upgraded from plain 4301.0527. Built-in LC filter suppresses mains-borne noise from other rack gear (digital effects, switching supplies) before it reaches the transformer. A reverb unit with 214× gain in the recovery stage is sensitive to supply noise — keeping the mains clean at the entry point is the right place to solve this. |

### DC Rail Protection

| Ref | Part | Spec | Why |
|---|---|---|---|
| F2 | Bourns MF-R050 | 500mA polyfuse — +15V rail | Acts like a circuit breaker on the positive DC rail. If a fault on the PCB draws more than 500mA the polyfuse trips, protecting the LM7815 and transformer. Resets automatically after cooling — no tools, no fuse replacement required. Same concept as a panel breaker. |
| F3 | Bourns MF-R050 | 500mA polyfuse — −15V rail | Same as F2 on the negative rail. |
| R_bleed1 | 10kΩ / 1W metal film | Across C13 (+15V filter cap) | When the unit is powered off, the filter caps hold ~21V charge. Without bleed resistors they stay charged for minutes — a shock hazard during servicing. The 10kΩ/1W resistor drains the cap in ~5 seconds. 1W rating required (P = V²/R = 441/10k = 44mW peak — 250mW standard resistor runs too hot). |
| R_bleed2 | 10kΩ / 1W metal film | Across C14 (−15V filter cap) | Same as R_bleed1 on the negative rail. |

### Input Protection

| Ref | Part | Spec | Why |
|---|---|---|---|
| C_in | 1µF / 63V WIMA MKS2 film | Input coupling cap — before U1 | Blocks DC from reaching the circuit. A failing pedal or preamp with a DC offset on its output would otherwise reach U1's input directly through R1. The existing C1 is after the input buffer — C_in sits at the jack itself, first in the signal path. |
| D_clamp+ | 1N4148 | Input → +15V rail | Overvoltage clamp. If the input exceeds +15.6V, this diode conducts and clamps the voltage. R1 (1MΩ) limits clamp current to safe microamps even at extreme input voltages. Protects U1's input from any source accidentally connected to the input jack. |
| D_clamp− | 1N4148 | −15V rail → Input | Same clamp on the negative side. Together with D_clamp+ they form a hard limit — input can never exceed the supply rails at U1's gate. |
| TVS1 | SMBJ15CA | Bidirectional TVS at input jack | Catches ESD events that 1N4148 diodes are too slow to handle. When you plug in a cable while other gear is running, a static discharge travels down the cable faster than the clamping diodes can respond. The TVS clamps in nanoseconds. Wired directly across the input jack tip to sleeve. |

### Serviceability

| Item | Spec | Why |
|---|---|---|
| Molex KK connectors (throughout) | 2-pin for transformer, tank RCA × 2, jacks × 2 — 3-pin for pots × 3 | Every internal wire connection uses a Molex KK connector at the PCB end. If any component fails — transformer, tank, pot, jack — it can be unplugged and swapped without a soldering iron. This is the single biggest serviceability improvement. Without connectors, replacing the tank requires desoldering 4 wires from a live board. With connectors it's a 30-second swap. |
| Sorbothane grommets (tank mount) | 4× M3 Shore 30–40, Sorbothane | Upgraded from standard rubber. Sorbothane is a viscoelastic polymer that damps vibration across a wider frequency range than rubber — footsteps, rack fan vibration, and amp vibration that standard grommets transmit into the springs become inaudible. |
| Thermal compound | Shin-Etsu X-23 or equivalent | Applied between LM7815/7915 tab, mica pad, and chassis. Halves the thermal resistance of the mica pad alone. Regulators run cooler, last longer. Apply a thin layer — less than 0.1mm. |
| Conformal coating | MG Chemicals 422B spray | Applied over the completed, tested PCB. Seals the board against moisture and environmental contamination. At 214× recovery gain, moisture absorption into the perfboard substrate raises leakage current between pads and manifests as noise. One pass of conformal coating eliminates this permanently. Apply after all testing is complete — it makes rework harder. |
| Colored heat-shrink (internal wiring) | Red = +15V, Blue = −15V, Black = GND, White = signal high-Z, Gray = signal line-level | Color coding means any technician can read the wiring without a schematic. Critical for a unit that will be serviced years from now by someone who didn't build it. |
| Power LED + bezel | 5mm LED (blue or amber) + panel-mount bezel, 10kΩ current-limiting resistor from +15V rail | Visual confirmation that the unit is powered. Saves significant troubleshooting time when the unit appears silent — knowing immediately whether the PSU is alive narrows the fault immediately. Wire from +15V rail through 10kΩ resistor to LED anode, cathode to GND. |
| Ground lift switch | SPDT mini toggle (rear panel) + 10Ω resistor + 100nF cap in series | Rack environments often develop ground loops — 60Hz hum that varies with what else is plugged in. The ground lift switch disconnects the direct audio-ground-to-chassis connection and inserts a 10Ω + 100nF RC network instead. This breaks ground loops without lifting the safety earth. Flip it one way for direct connection, the other way for lifted. Essential to have on the rear panel rather than requiring chassis opening to address hum. |

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

## PCB / Board

| Item | Spec | Why |
|---|---|---|
| Perfboard | **Vector Electronics T44** or equivalent — 0.1" pitch, copper-pad-per-hole, FR4 fibreglass substrate | FR4 fibreglass is mandatory — phenolic perfboard (the cheaper brown type) absorbs moisture and increases leakage current between pads, which at the recovery stage gain of 214× will manifest as audible noise. The Vector T44 is the professional standard for point-to-point audio builds. Size to fit inside the 2U chassis with clearance for the tank and transformer. |
| PCB standoffs | 4× M3 × 10mm nylon hex standoffs + M3 nylon screws | Nylon (not metal) standoffs isolate the perfboard from the chassis ground plane. All grounding must flow through the single star-ground point — a metal standoff accidentally grounding the board at a second point creates a ground loop. |

---

## Tank Connections

| Item | Spec | Why |
|---|---|---|
| Tank input cable | Belden 8451 shielded, 12" max, terminated in RCA plug | The RCA connector on the 9AB3C1B tank input (8Ω side) mates with a standard RCA plug. Belden 8451 shielded cable prevents the high-current driver signal from radiating into adjacent circuitry. Keep under 12" — excessive length adds capacitance that rolls off the high-frequency drive to the tank. |
| Tank output cable | Belden 8451 shielded, 12" max, terminated in RCA plug | The tank output (2550Ω side) carries 1–5mV — the most sensitive signal in the circuit. Shielded cable is non-negotiable. Ground the shield at the recovery amp (U2) end only — not at the tank end. One-end grounding prevents a shield ground loop that would induce 60Hz hum directly into the recovery stage. |

---

## Heatsinks

| Item | Spec | Why |
|---|---|---|
| BD139 heatsink | Small TO-126 clip-on heatsink (e.g. Aavid 577002) | At 19mA quiescent the BD139 dissipates ~285mW — within its TO-126 rating but warm. A clip-on heatsink keeps the junction temperature below 50°C and prevents long-term hFE drift that would shift the bias point over years of use. |
| LM7815 / LM7915 heatsinks | 2× TO-220 heatsink + insulating mica pad + M3 screw (e.g. Aavid 530002) | Each regulator drops ~6V at ~100mA = ~600mW dissipation. Without a heatsink they will thermally throttle and the supply voltage will sag under load. The **insulating mica pad is mandatory** — the TO-220 tab is electrically connected to the output pin; without isolation, mounting both regulators to the same chassis creates a short between +15V and −15V through the chassis. |

---

## Hardware & Fasteners

| Item | Qty | Spec | Why |
|---|---|---|---|
| M3 × 8mm stainless pan-head screws | 12 | Stainless steel | Chassis assembly and PCB mounting. Stainless prevents corrosion that causes intermittent ground connections over time. |
| M3 nylon hex standoffs (10mm) | 4 | Nylon | PCB isolation from chassis — see PCB section above. |
| M3 star washers | 6 | Stainless | Use under screw heads at the star-ground point and jack mounting to ensure solid chassis ground connection through any anodising on the aluminum. |
| Cable ties (small) | 1 bag | 2.5mm × 100mm nylon | Internal wire management. Keeps signal wires separated from power wires — critical for preventing mains hum induction into the signal path. |
| Solder | 1 roll | **Kester 44, 63/37, 0.031"** | Kester 44 is the gold standard for hand-soldered audio work. 63/37 tin/lead eutectic alloy — snaps solid with no "mushy" semi-solid phase, dramatically reducing cold solder joints. 0.031" diameter is correct for through-hole component work on perfboard. Do not use lead-free solder — higher melting point increases heat stress on sensitive components and produces higher-resistance joints. |
| Flux pen | 1 | Kester 951 no-clean flux pen | Use on all joints before soldering for clean, bright fillets. Essential for the RCA tank connections where the joint must be mechanically and electrically perfect. |
| Heat shrink tubing | 1 assorted pack | 2:1 ratio, black, assorted 1–6mm | Insulation over solder joints on the power supply wiring and anywhere bare conductors could contact the chassis. |

---

## Knobs (Owner to Select)

3 knobs required — one each for Dwell, Mix, Tone. The Vishay/Spectrol 296 pots have a **¼" (6.35mm) D-shaft**. Specify D-shaft compatible knobs when ordering. Suggested specs:

- **Shaft type:** ¼" D-shaft
- **Diameter:** 1" (25mm) looks correct on a 2U panel at standard pot spacing
- **Style:** Skirted or Davies 1510 clone — matches rack gear aesthetic, pointer stripe for position reference
- **Material:** Aluminum preferred over plastic for feel and durability in a rack unit

Search Mouser or Smallbear Electronics for "D-shaft aluminum knob 1 inch."

---

## Feet (Owner to Select)

4 rubber feet for standalone use on a surface (outside the rack). Spec:

- **Type:** Self-adhesive rubber bump feet
- **Height:** 10–12mm (lifts the unit for ventilation)
- **Diameter:** 20–25mm (stable base on the 2U chassis width)

Standard item — available on Amazon, Mouser, or any hardware supplier. Search "self-adhesive rubber cabinet feet 10mm."

---

## Build Notes

1. **Grounding:** Use a single-point star ground connected to the chassis at one point. All circuit grounds (op-amp ground pins, pot grounds, jack grounds) run back to this single point. Do not daisy-chain grounds — ground loops cause hum.

2. **Decoupling caps:** Place C5–C10 (100nF film) physically as close to the OPA2134 supply pins as possible. If they are more than 1" away from the IC, they will not effectively suppress HF noise.

3. **Tank orientation:** Mount RT1 open-side down, horizontally. If mounted open-side up, the springs can shift position over time and the reverb character will drift.

4. **Transformer placement:** Mount T1 as far from RT1 as the chassis allows and orient it so the transformer's toroid axis is perpendicular to the tank's spring axis. This minimizes inductive coupling between transformer and tank (which causes 60Hz hum in the reverb tail).

5. **Shielding the recovery stage:** The wire from RT1's output (2550Ω side) to U2's non-inverting input (Rbias → C3 → U2) carries the most sensitive signal in the entire circuit — approximately 1–5mV. This wire must be shielded (Belden 8451) with the shield grounded at the U2 end only (not at the tank end — one-end grounding prevents a ground loop through the shield).

6. **Phase alignment on first power-up:** Spring tank polarity varies between Accutronics batches. If the reverb sounds hollow, thin, or "phasey" when the Mix pot is at 50/50, the tank output is out of phase with the dry signal. Fix: swap the two wires at RT1's output RCA connector (the 2550Ω side). This is a 10-second wire swap — no schematic changes required.
