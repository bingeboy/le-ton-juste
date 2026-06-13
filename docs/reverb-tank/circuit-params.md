# Ghost Spring Reverb — Canonical Circuit Parameters

> **GENERATED FILE — do not edit by hand.** This table is produced by [`stages/gen_circuit_params_md.py`](./stages/gen_circuit_params_md.py) from [`stages/circuit_params.py`](./stages/circuit_params.py), the single source of truth. Edit `circuit_params.py`, then run `python docs/reverb-tank/sync.py`. Do not edit `circuit-params.md` by hand — it is generated.

> **Authority:** This file is the single source of truth for all named parameters.
> The SPICE netlist (`stage_06_full.net`) is the computational authority and must match this file.
> All other docs (builder-guide, parts-spec, build-plan, design) reference this file — they do NOT restate numbers.
> Edit `circuit_params.py`, then run `sync.py`. Do not edit `circuit-params.md` by hand — it is generated.

This table is THE authoritative human-readable source for every named value in the Ghost Spring circuit. The netlist [`stages/stage_06_full.net`](./stages/stage_06_full.net) is the computational mirror of this file and must agree with it byte-for-byte on values; the Python constants module [`stages/circuit_params.py`](./stages/circuit_params.py) is the machine-readable mirror that the generator scripts import. If any of the three disagree, that is a bug — edit `circuit_params.py`, then run `sync.py`. Do not edit `circuit-params.md` by hand — it is generated.

Companion authorities (each owns a different *class* of value):

- **Pass criteria** (measurement windows / `.meas` directives): [`stages/test-assertions.md`](./stages/test-assertions.md) — computational authority for the pass bands reproduced at the bottom of this file.
- **Parts** (Mouser PNs, packages, quantities): [`mouser-bom.csv`](./mouser-bom.csv).
- **Design rationale** (why a value was chosen): [`parts-spec.md`](./parts-spec.md).
- **Bench procedures**: [`stages/builder-guide.md`](./stages/builder-guide.md).

> **Netlist designator note.** SPICE reserves some single-letter prefixes, and the pots are modelled as two halves. The mapping between the schematic/BOM designator and the netlist instance name is called out per row where they differ. Summary:
> - **C1** (BOM) = **`C_drive`** (netlist) — same physical 1µF Dwell-coupling cap.
> - **F2 / F3** polyfuses = **`RF2` / `RF3`** (SPICE reserves the `F` prefix for current-controlled sources; modelled as 0.5Ω series R).
> - **RV1 / RV2 / RV3** pots are each modelled as two series halves: `RV1a`+`RV1b` (5k+5k = 10k Dwell), `RV2a`+`RV2b` (50k+50k = 100k Mix), `RV3a`+`RV3b` (50k+50k = 100k Tone). The wiper node is the junction.
> - **U4 / U5** regulators are SPICE instances **`XU4` / `XU5`** (LM78xx / LM79xx behavioural subckts).
> - **BR1** bridge = four diodes **`DBR1a`–`DBR1d`** (model `DN4007`).
> - **TVS1** = two back-to-back zeners **`DTVS1a` / `DTVS1b`** (model `BZX84C15L`).

---

## Resistors

All signal-path resistors: metal film, 1% tolerance, 250mW. (R_bleed1/2 are 1W flameproof metal film.)

| Ref | Value (Ω) | Function | Netlist node(s) |
|---|---|---|---|
| R1 | 1MΩ | U1(+) FET-input DC return / 1MΩ input impedance (shunt, **after** C_in) | `u1_pos` → `0` |
| R2 | 100 | U1 output isolation (series, against cable capacitance) | `u1_out` → `u1_buf` |
| R3 | 1k | Dwell wiper → Q1 base drive resistor / HF damping | `q1_drv` → `q1_base` |
| R3b | 6.8k | Upper leg of Q1 base bias divider (+15V → base) | `+15V` → `q1_base` |
| R4 | 1k | Lower leg of Q1 base bias divider (base → GND) | `q1_base` → `0` |
| R5 | 68 | Q1 emitter degeneration (sets Ic, thermal stability) | `q1_e` → `0` |
| Ri | 470 | U2 gain-set lower leg (non-inverting feedback divider, (−) → GND) | `u2_inv` → `0` |
| Rf | 100k | U2 feedback upper leg (output → (−)); gain = 1 + Rf/Ri | `u2_out` → `u2_inv` |
| R6 | 5.6k | Wet HPF resistor (with C4) | `hpf_out` → `0` |
| Rbias | 100k | U2 non-inv (+) input bias / recovery input impedance | `u2_in_pos` → `0` |
| Rdry | 10k | Dry-path series R: U1 buffer → RV2 CCW end (dry end of Mix pot) | `u1_buf` → `mix_dry` |
| Rwet_wire | 1mΩ | Wet-path direct hookup wire: Tone wiper → RV2 CW end (wet end of Mix pot; modelled 1mΩ — LTspice rejects R=0) | `rv3_wiper` → `mix_wet` |
| R7 | 100 | U3 output isolation (series to output jack / MC100) | `u3_out` → `v_out` |
| Rload | 47k | MC100 RCA input load (model of downstream device, not a fitted part) | `v_out` → `0` |
| R_tank_in | 8 | Tank input impedance (8Ω side, lumped tank model) | `tank_in` → `0` |
| R_tank_mech | 200 | Tank mechanical-resonance series R (lumped model) | `tank_mid` → `tk_a` |
| R_tank_out | 2550 | Tank output impedance (2550Ω side, lumped model) | `tank_mid` → `tank_out` |
| R_bleed1 | 10k | Bleed across C11 (+15V bulk filter), 1W flameproof | `pos_rect` → `0` |
| R_bleed2 | 10k | Bleed across C12 (−15V bulk filter), 1W flameproof | `neg_rect` → `0` |
| RF2 | 0.5 | F2 polyfuse (MF-R050) model, +15V rail (hold ≈0.7Ω) | `reg_pos` → `+15V` |
| RF3 | 0.5 | F3 polyfuse (MF-R050) model, −15V rail | `reg_neg` → `-15V` |
| RV1a | 5k | Dwell pot upper half (U1 buf → wiper) | `u1_buf` → `rv1_wiper` |
| RV1b | 5k | Dwell pot lower half (wiper → GND) | `rv1_wiper` → `0` |
| RV2a | 50k | Mix pot CCW half (dry end → wiper) | `mix_dry` → `mix_node` |
| RV2b | 50k | Mix pot CW half (wiper → wet end) | `mix_node` → `mix_wet` |
| RV3a | 50k | Tone pot upper half (HPF out → wiper) | `hpf_out` → `rv3_wiper` |
| RV3b | 50k | Tone pot lower half (wiper → GND) | `rv3_wiper` → `0` |

> Power-LED current-limit resistor (10k from +15V) and the ground-lift 10Ω are panel/wiring parts not present in the signal netlist; their values live in [`parts-spec.md`](./parts-spec.md).

---

## Capacitors

Signal-path caps: film (WIMA MKS2/MKP). C2/C13–C16 electrolytic; C11/C12 bulk electrolytic; C_bright silver mica.

| Ref | Value | Function | Netlist node(s) |
|---|---|---|---|
| C_in | 1µF / 63V | Input coupling at the jack (before U1) | `vin` → `u1_pos` |
| C1 (= `C_drive`) | 1µF / 63V | Dwell-wiper → Q1 base coupling (blocks buffer DC from bias divider) | `rv1_wiper` → `q1_drv` |
| C2 | 100µF / 25V | Q1 emitter bypass (across R5, full AC gain) | `q1_e` → `0` |
| C3 | 470nF / 63V | Tank output → U2 input DC block (~3Hz corner w/ Rbias) | `tank_out` → `u2_in_pos` |
| C4 | 100nF / 63V | Wet HPF cap (with R6) | `u2_out` → `hpf_out` |
| C_bright | 47pF | Bright cap across full Mix pot (HF presence as pot approaches full-wet) | `mix_dry` → `mix_wet` |
| Cf | 22pF | U2 feedback compensation — rolls off the 214× loop to ~72kHz corner; mandatory on perfboard (C0G/NP0) | `u2_out` → `u2_inv` |
| C5 | 100nF / 63V | U1/U2 +15V supply decoupling | `+15V` → `0` |
| C6 | 100nF / 63V | U1/U2 −15V supply decoupling | `-15V` → `0` |
| C7 | 100nF / 63V | U3 +15V supply decoupling | `+15V` → `0` |
| C8 | 100nF / 63V | U3 −15V supply decoupling | `-15V` → `0` |
| C11 | 1000µF / 50V | +ve unregulated bulk filter (after bridge) | `pos_rect` → `0` |
| C12 | 1000µF / 50V | −ve unregulated bulk filter | `neg_rect` → `0` |
| C13 | 75µF / 25V | U4 (LM7815) output stability cap | `reg_pos` → `0` |
| C14 | 75µF / 25V | U5 (LM7915) output stability cap | `reg_neg` → `0` |
| C15 | 10µF / 25V | +15V board-entry bulk decoupling | `+15V` → `0` |
| C16 | 10µF / 25V | −15V board-entry bulk decoupling | `-15V` → `0` |
| C17 | 100nF / 63V | U4 output HF bypass (at reg pin) | `reg_pos` → `0` |
| C18 | 100nF / 63V | U5 output HF bypass (at reg pin) | `reg_neg` → `0` |
| C_tank_mech | 10nF | Tank mechanical-resonance cap (lumped model) | `tk_b` → `0` |

---

## Inductors / Coupled magnetics (lumped models)

| Ref | Value | Function | Netlist node(s) |
|---|---|---|---|
| L1 | 100mH (Rser=0) | REB3S primary (Q1 collector → +15V) | `+15V` → `q1_c` |
| L2 | 5mH (Rser=0) | REB3S 8Ω secondary (into tank input) | `tank_in` → `0` |
| K1 | 0.98 | REB3S coupling coefficient (L1↔L2) | couples `L1` `L2` |
| L_tank | 15mH (Rser=0) | Tank input series inductance (lumped) | `tank_in` → `tank_mid` |
| L_tank_mech | 500mH (Rser=0) | Tank mechanical-resonance inductance (lumped) | `tk_a` → `tk_b` |
| L_tank_out | 2H (Rser=0) | Tank output inductance (lumped) | `tank_out` → `0` |

---

## Semiconductors

| Ref | Part number / model | Function |
|---|---|---|
| U1, U2, U3 | OPA2134PA (DIP-8 dual; 2 packages, 3 sections used) | Input buffer / recovery preamp / output buffer (SPICE: UniversalOpAmp2 level2) |
| Q1 | BD139 (TO-126 NPN) | Class-A discrete transformer driver |
| D3 | 1N4148 | Flyback clamp across REB3S primary (anode→collector, cathode→+15V) |
| D_clamp+ (`Dclamp_p`) | 1N4148 | U1(+) overvoltage clamp (anode→U1+, cathode→+15V) |
| D_clamp− (`Dclamp_n`) | 1N4148 | U1(+) overvoltage clamp (anode→−15V, cathode→U1+) |
| TVS1 (`DTVS1a`/`DTVS1b`) | SMBJ15CA (model: 2× BZX84C15L back-to-back) | Bidirectional ESD/TVS at input jack |
| BR1 (`DBR1a`–`DBR1d`) | W04G (model: 4× 1N4007 / DN4007) | Full-wave bridge rectifier |
| U4 (`XU4`) | LM7815 (model: LM78xx subckt) | +15V linear regulator |
| U5 (`XU5`) | LM7915 (model: LM79xx subckt) | −15V linear regulator |

---

## Potentiometers

| Ref | Value | Taper | Function |
|---|---|---|---|
| RV1 (Dwell) | 10kΩ | Linear | Drive level into transformer (modelled `RV1a` 5k + `RV1b` 5k) |
| RV2 (Mix) | 100kΩ | Audio | Dry/wet blend (modelled `RV2a` 50k + `RV2b` 50k) |
| RV3 (Tone) | 100kΩ | Audio | High-shelf EQ on wet signal (modelled `RV3a` 50k + `RV3b` 50k) |

> Pot positions used for the verified simulations are tabulated in [`builder-guide.md`](./stages/builder-guide.md) ("Pot positions for every test"). The netlist models each pot at the wiper position giving the values above.

---

## Power supply

| Element | Spec / value | Notes |
|---|---|---|
| T1 transformer | Triad F-219X, 30VA, 2×115VAC primary, 2×15VAC secondary (15-0-15) | Primaries parallel for 120V mains; secondaries series for center-tapped 15-0-15. Modelled as two anti-phase `SINE(0 21.2 60)` (21.2V peak = 15Vrms·√2) about a grounded center tap. |
| BR1 bridge | W04G, 2A / 400V (model 4× 1N4007) | `pos_rect` = +ve unregulated bus, `neg_rect` = −ve bus |
| Unregulated bus | ≈ ±20.4V (avg, settled) | ≈ peak 21.2V − 2 diode drops, held by bulk caps; ≈21mVpp ripple in model |
| C11 / C12 filter | 1000µF / 50V each | Main bulk filter per rail |
| R_bleed1 / R_bleed2 | 10kΩ / 1W each | τ = 10k × 1000µF = 10s → <2V in ~50s after power-off (44mW dissipation) |
| U4 / U5 regulators | LM7815 / LM7915 | Drop ≈5.4V (20.4V bus − 15V) at ~30–50mA → ≈0.15–0.3W each; heatsink + mica pad mandatory |
| C13 / C14 | 75µF / 25V each | Regulator output stability caps |
| C17 / C18 | 100nF / 63V each | Regulator output HF bypass |
| C15 / C16 | 10µF / 25V each | Board-entry bulk decoupling |
| C5–C8 | 100nF / 63V (4 total) | Op-amp supply-pin decoupling |
| F2 / F3 polyfuses | Bourns MF-R050, 500mA each (model 0.5Ω) | On the DC rails after the regulators (RF2/RF3) |
| F1 mains fuse | 500mA slow-blow | Primary-side protection |
| Mains protection | MOV1 V275LA20AP, NTC1 Ametherm MS32 5006 (5Ω), F1 Schurter 5110.1052 EMI inlet | Across-line / inrush / EMI filter (not in signal netlist) |

---

## Operating point (verified by simulation)

Source: `stage_06_full` `op` variant (settled DC at the 190–200ms tail; the PSU is degenerate at a true `.op`). Q1 = BD139.

| Quantity | Verified sim value | First-order estimate | Notes |
|---|---|---|---|
| Q1 Ve (`V(q1_e)`) | **1.092 V** | 1.22 V | `q1_ve` measurement; emitter = top of R5 |
| Q1 Vb (base) | ≈1.9 V (open-circuit 1.92 V) | 1.92 V | Set by R3b/R4, loaded by base current |
| Q1 Vc (collector) | ≈13.8–14 V | — | Idles near +15V (L1 is near-DC short to rail), swings down under drive |
| Q1 Ic | **≈16 mA** | 18 mA | Ic ≈ Ve/R5 = 1.092 / 68 |
| Q1 Vbe | ≈0.8 V | 0.7 V | Higher than 0.7V at this current (real Vbe) |
| Q1 Vce | ≈12.7–13.9 V | — | ≈Vc − Ve; dissipation ≈ Vce × Ic ≈ 0.22 W |
| U1 output DC (`off_u1`) | **≈0 V (≈0 V)** | 0 V | Within ±10mV window |
| U2 output DC (`off_u2`) | **+0.47 mV** | 0 V | Settles from ~72mV at 20ms to <0.5mV by 200ms |
| U3 / output DC (`off_u3`) | **−0.35 µV (≈0 V)** | 0 V | At `v_out` (output jack) |
| +15V rail (`rail_pos`) | **≈+15.0 V** | +15 V | LM7815 on its 15.0V clamp (bus well above dropout) |
| −15V rail (`rail_neg`) | **≈−15.0 V** | −15 V | LM7915 on its −15.0V clamp |

---

## Key AC parameters (verified by simulation)

Source: `stage_06_full` `ac` variant (ideal ±15V rails; signal-path small-signal is independent of rail origin).

| Quantity | Verified sim value | Design nominal | Notes |
|---|---|---|---|
| Recovery gain (U2), V/V | **213.8×** @1kHz | ~214× (= 1 + 100k/470) | `recov_gain`; `V(u2_out)/V(u2_in_pos)` |
| Recovery gain (U2), dB | **46.59 dB** @1kHz | 46.6 dB | |
| Wet HPF −3dB corner | **312 Hz** | 284 Hz (= 1/(2π·R6·C4)) | `hpf_m3db`; measured as R6/C4 transfer `V(hpf_out)/V(u2_out)`. Sim/design differ due to loading; both in band |
| Tank resonant peak ("drip") | ≈2–3 kHz | 1–5 kHz target | `tank_pk_f`; resonance of REB3S primary with tank input Z |
| Output impedance | <100 Ω | — | Set by U3 (FET buffer) + R7 100Ω series |
| Input impedance | 1 MΩ | — | Set by R1 shunt after C_in |
| Output peak (`vout_pk`), 100mVpk in | **1.16 V** | — | tran variant; well below clipping |
| Oscillation ratio (`osc_ratio`) | **0.9998** | — | tran variant; <1.05 = stable |

---

## Pass windows (from test-assertions.md)

> **`test-assertions.md` is the computational authority for these bands** (it holds the `.meas` directives). The table below is reproduced for convenience and must match it. If they disagree, `test-assertions.md` wins.

| Assertion | Expression | Pass window |
|---|---|---|
| `off_u1` | `V(u1_out)` | \|val\| ≤ 10 mV |
| `off_u2` | `V(u2_out)` | \|val\| ≤ 10 mV |
| `off_u3` | `V(v_out)` | \|val\| ≤ 10 mV |
| `q1_ve` | `V(q1_e)` | 1.0 – 1.4 V (sim 1.092 V) |
| `q1_ic` | `Ic(Q1)` | 10 – 26 mA (sim ≈16 mA) |
| `recov_gain` | `V(u2_out)/V(u2_in_pos)` @1k | 205 – 225× (sim 213.8×) |
| `hpf_m3db` | wet −3dB corner | 250 – 320 Hz (sim 312 Hz) |
| `vout_pk` | `MAX abs(V(v_out))` | < 14 V (sim 1.16 V) |
| `osc_ratio` | RMS_late / RMS_early | < 1.05 (sim 0.9998) |
| `d3_pk` | `MAX abs(I(D3))` | < 1 mA |
| `clamp_p_i` / `clamp_n_i` | `I(Dclamp_*)` | < 1 µA at idle |
| `u1pos_hi` / `u1pos_lo` | `V(u1_pos)` @20Vpp in | ≤ +16 V / ≥ −16 V (clamps ≈±15.7V) |
| `tank_pk_f` | freq of max `V(tank_in)` | 1 – 5 kHz (≈2–3 kHz) |
| `tank_drive_db` | `20log10(V(tank_in)/V(rv1_wiper))` @2k | > −60 dB |
| `rail_pos` | `V(+15V)` | 14.85 – 15.15 V |
| `rail_neg` | `V(-15V)` | −15.15 – −14.85 V |
| `ripple_pos` / `ripple_neg` | `PP V(±15V)` | < 10 mVpp |

| Bench noise floor (Stage 7) | output noise at J2 | < 1 mVrms, no discrete 60/120Hz spike |

---

*Every component in `stage_06_full.net` appears above. The lumped-model R/L/C of the tank and transformer (`R_tank_*`, `L_tank*`, `L1`/`L2`/`K1`, `C_tank_mech`) are SPICE modelling elements, not separately-purchased parts — the physical parts are RT1 (9AB3C1B tank) and T2 (REB3S transformer), per [`parts-spec.md`](./parts-spec.md).*
