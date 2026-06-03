# Rack Parallel Mixer — Exact Parts Specification

Same standard as the Ghost Spring reverb tank — every component with exact value, part number, and engineering rationale. Builder should not substitute without understanding the reason.

---

## Op-Amps

| Ref | Part | Package | Qty | Why |
|---|---|---|---|---|
| U1, U2, U3 | Texas Instruments OPA2134PA | DIP-8 (dual) | **2 packages** (4 sections — 3 used, 1 spare) | Same rationale as Ghost Spring: FET-input, 10¹³Ω input impedance, THD+N 0.00008%, slew rate 20V/µs. Consistency across both DIY builds means one spare part covers both units. The summing amp (U2) must drive 4 resistors simultaneously — the OPA2134 has no issue with this load at ±15V. |

---

## Resistors

All: **metal film, 1%, 250mW** (Yageo MFR or Vishay CMF series).

| Ref | Value | Qty | Location | Why |
|---|---|---|---|---|
| R_in | 100kΩ | 1 | U1 non-inv input to jack | Sets input impedance seen by Alembic FX-1. 100kΩ places virtually zero load on the preamp output. |
| R_iso | 1kΩ | 4 | U1 output → each send branch | Isolation resistors between the splitter output and each load (3 sends + dry path). Prevents a fault or short on one send from loading the others. Without isolation, plugging/unplugging a send cable would momentarily load U1's output and cause a pop in the dry signal. |
| R_dry | 22kΩ | 1 | Dry path → U2 summing input | Dry path input resistor for the summing amp. 22kΩ chosen so dry path gain through U2 = Rf/R_dry = 22k/22k = 1 (unity, inverted). Dry path has no level pot — it's always at unity. |
| R_L1–R_L3 | 22kΩ | 3 | Level pot output → U2 summing input | Loop return input resistors. Same value as R_dry for consistent gain structure across all inputs. The level pots (RV_L1–L3) attenuate before these resistors. |
| R_f | 22kΩ | 1 | U2 feedback (out → inv input) | Sets summing amp gain. With all R_in = R_f = 22kΩ, each channel contributes unity gain to the sum. |
| R_pc_in | 10kΩ | 1 | U3a phase-correct input | Input resistor for phase-correct stage. |
| R_pc_f | 10kΩ | 1 | U3a phase-correct feedback | Feedback resistor — with R_pc_in = R_pc_f, gain = −1 (unity, corrects U2 inversion). |
| R_out | 100Ω | 1 | U3a output (series) | Output isolation — prevents oscillation driving cable capacitance to the MC100. Same role as in Ghost Spring and every other op-amp output in this rig. |

---

## Capacitors

### Signal Path / Decoupling — Film
All film caps: **WIMA MKS2, 100nF/63V**.

| Ref | Value | Qty | Location | Why |
|---|---|---|---|---|
| C_dec | 100nF/63V film | 8 | 2 per OPA2134 package supply pin pair × 2 packages × 2 rails | Op-amp supply decoupling — same requirement and rationale as Ghost Spring. Placed physically as close to supply pins as possible. |
| C_psu_hf | 100nF/63V film | 2 | In parallel with PSU output electrolytics | HF bypass on regulator outputs — electrolytics become inductive above ~100kHz, film caps take over. |

### Decoupling — Electrolytic
| Ref | Value | Type | Qty | Location | Why |
|---|---|---|---|---|---|
| C_bulk | 10µF/25V | Nichicon UKW | 2 | One per rail at PCB power entry | Bulk energy reservoir on the board. Handles transient current demands during summing of multiple simultaneous signals. |

### Power Supply Capacitors
| Ref | Value | Type | Qty | Location | Why |
|---|---|---|---|---|---|
| C_filt | 2200µF/35V | Nichicon KW low-ESR | 2 | Main filter after bridge rectifier | Ripple filtering — same spec and rationale as Ghost Spring. |
| C_reg_out | 100µF/35V | Nichicon KW | 2 | LM7815/7915 output | Regulator stability and local storage. |

---

## Potentiometers

| Ref | Value | Taper | Part | Why |
|---|---|---|---|---|
| RV_L1, L2, L3 (Level pots) | 100kΩ | **Audio (A)** | **Vishay/Spectrol 296UAL104B2** | Controls wet signal blend per loop. Audio taper gives perceptually even blend — 50% rotation sounds like 50% mix. Same mil-spec grade as Ghost Spring pots: MIL-PRF-39023 rated, cermet element, gold wiper, stainless shaft. |
| RV_T1, T2, T3 (Send trims) | 10kΩ | Linear | **Bourns 3296W-1-103LF** (cermet trimmer) | Internal send level trim per loop. Set once during initial calibration. Bourns 3296W is the industry-standard 25-turn cermet trimmer — stable over temperature, sealed against dust. Do not use carbon trimmers — they drift with temperature and humidity. |

---

## Switches

| Ref | Part | Qty | Why |
|---|---|---|---|
| SW_PH1–PH3 | **Carling DPDT toggle, ON-ON, PC or solder lug** | 3 | Phase invert per loop return. DPDT wiring swaps + and − of the return signal. Carling toggles are the professional standard — positive feel, gold contacts, rated 50,000 cycles. Do not use cheap mini-toggles: contact bounce causes clicks when switching. |

---

## Jacks

| Ref | Part | Qty | Why |
|---|---|---|---|
| J_in, J_out, J_S1–S3, J_R1–R3 | **Switchcraft 112A ¼" TS mono** | 8 | Same rationale as Ghost Spring — professional standard, nickel-plated, low contact resistance. The send jacks see the splitter output (low impedance, robust) — the return jacks see the effects unit outputs, which vary widely in impedance. Switchcraft's consistent contact resistance prevents level differences between loops. |

---

## Power Supply

| Ref | Part | Spec | Why |
|---|---|---|---|
| T1 | Antek AN-0115 (or equivalent toroidal) | 15VA, dual 15VAC | Same transformer as Ghost Spring for parts commonality. Toroidal for low magnetic leakage — this unit sits in the rack between the Alembic FX-1 and Ghost Spring, so stray magnetic fields must be minimized. |
| BR1 | Vishay W02G | 1A/200V bridge rectifier | Same as Ghost Spring. |
| U4 | LM7815 TO-220 | +15V | Same as Ghost Spring. Mount to chassis with insulating mica pad. |
| U5 | LM7915 TO-220 | −15V | Same as Ghost Spring. Insulating pad mandatory — TO-220 tab is electrically live. |

---

## Hardware & PCB

| Item | Spec | Why |
|---|---|---|
| Perfboard | Vector T44 FR4 fibreglass | Same as Ghost Spring — FR4 mandatory, not phenolic. |
| IC sockets | 2× DIP-8 machine-pin | OPA2134 packages — same rationale as Ghost Spring. |
| PCB standoffs | 4× M3 nylon 10mm | Chassis isolation — same rationale. |
| Hookup wire (signal) | Belden 8451 shielded 24AWG | All signal paths. The summing amp input node (where dry + 3 returns combine) is particularly sensitive — any unshielded wire here will pick up hum from the transformer. |
| Hookup wire (power) | 22AWG stranded 300V | PSU connections. |
| Solder | Kester 44, 63/37, 0.031" | Same as Ghost Spring. |
| Heatsinks | 2× TO-220 + insulating mica pads | LM7815/7915. This unit draws less current than the Ghost Spring (no driver transistor) but the regulators still dissipate ~300mW each — heatsinks required for long-term reliability. |

---

## Build Notes for Dan Jams LLC

1. **Star ground:** Single-point star ground to chassis — identical requirement to Ghost Spring. All grounds (op-amp pins, pot grounds, jack grounds) return to one point. With 8 jacks and 3 pots, the temptation to daisy-chain is high. Do not.

2. **Decoupling caps:** 100nF film caps as close as physically possible to OPA2134 supply pins. Same rule as Ghost Spring — if more than 1" away, they are not effective.

3. **Send trim calibration:** After build, connect all three effects units. Set each unit's input to its normal operating sensitivity. Adjust each send trimmer until the effect's input meter peaks at −6dBFS with a normal playing level at the guitar. This is a one-time setup step.

4. **Phase switch testing:** With the mixer running, blend in each loop one at a time. If the tone sounds thin, hollow, or loses low end when a loop is added — flip that loop's phase switch. The correct phase position is the one that sounds fuller. The QuadraVerb almost certainly needs phase correction.

5. **Kill dry verification:** Before using any effects unit in the loops, verify it is set to 100% wet. Plug the send but not the return, then listen to the output. You should hear only the dry signal (the effects unit's output is disconnected). Now plug the return — if the dry signal level changes significantly, the effects unit is passing dry signal and needs to be adjusted.

6. **Transformer placement:** Mount T1 at maximum distance from the summing amp node and input buffer. The summing node handles 4 combined signals at line level — any hum induced here appears in all channels simultaneously and cannot be corrected downstream.
