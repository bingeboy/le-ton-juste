# Ghost Spring Reverb — SPICE Test Assertions

The `.meas` directives below are the **PASS conditions** for each build stage in [`build-plan.md`](./build-plan.md). They are the SPICE equivalent of a unit-test suite.

## What SPICE TDD means in practice

You write the `.meas` assertions **before** adding the component group, run the simulation, and confirm they *fail* — the component isn't there yet, so the number is wrong (or the node doesn't exist). Then you add the component and run again, confirming the assertion now *passes*. It's the same red-green-refactor loop as software TDD: the failing measurement is your "red," the passing measurement is your "green," and tightening values/parts to keep all prior stages green is the "refactor."

LTspice prints `.meas` results to the SPICE Error Log (Ctrl+L). A measurement that can't evaluate (missing node, no crossing) reports `FAIL`/no value — that *is* your red state.

---

## Stage 1 — MVP baseline

```spice
; Stage 1 — DC: every op-amp output sits at virtual 0V (no offset)
.meas OP off_u1 FIND V(u1_out)
.meas OP off_u2 FIND V(u2_out)
.meas OP off_u3 FIND V(v_out)

; Stage 1 — AC: recovery stage gain = 1 + Rf/Ri = 214x (+/-3%)
.meas AC recov_gain FIND V(u2_out)/V(u2_in_pos) AT=1k

; Stage 1 — AC: wet HPF -3dB corner (R6 5.6k + C4 100n ~= 284Hz)
.meas AC hpf_ref  FIND V(hpf_out) AT=5k
.meas AC hpf_m3db WHEN V(hpf_out)=hpf_ref*0.7079 RISE=1

; Stage 1 — TRAN: output not clipping
.meas TRAN vout_pk MAX abs(V(v_out))

; Stage 1 — TRAN: no oscillation — RMS late window vs early window
.meas TRAN rms_early RMS V(v_out) FROM=0     TO=10m
.meas TRAN rms_late  RMS V(v_out) FROM=90m   TO=100m
.meas TRAN osc_ratio PARAM rms_late/rms_early
```

| Assertion name | Expression | Pass condition | Fail means |
|---|---|---|---|
| `off_u1` | `V(u1_out)` | \|val\| ≤ 10 mV | U1 has a DC offset — bias/coupling error |
| `off_u2` | `V(u2_out)` | \|val\| ≤ 10 mV | Recovery DC offset — Rbias/C3 issue, will clip mix |
| `off_u3` | `V(v_out)` | \|val\| ≤ 10 mV | Output offset — DC to the MC100 |
| `recov_gain` | `V(u2_out)/V(u2_in_pos)` @1k | 200 – 228 | Wrong Rf/Ri ratio — recovery gain off |
| `hpf_m3db` | freq where wet = 0.7079×ref | 250 – 320 Hz | HPF corner wrong — R6/C4 value error |
| `vout_pk` | `MAX abs(V(v_out))` | < 14 V | Output clipping into the rails |
| `osc_ratio` | RMS_late / RMS_early | < 1.05 | Signal growing — oscillation/instability |

---

## Stage 2 — BD139 driver

```spice
; Stage 2 — OP: Q1 bias point
.meas OP q1_ve FIND V(q1_e)
.meas OP q1_ic FIND Ic(Q1)

; Stage 2 — TRAN: D3 flyback diode idle during normal drive
.meas TRAN d3_pk MAX abs(I(D3))

; Stage 2 — TRAN: clean drive current into the primary/load, no clip
.meas TRAN drv_pk  MAX abs(I(L1))
.meas TRAN drv_rms RMS I(L1)
```

| Assertion name | Expression | Pass condition | Fail means |
|---|---|---|---|
| `q1_ve` | `V(q1_e)` | 1.0 – 1.4 V (sim 1.09 V; first-order 1.22 V) | Bias divider/R5 wrong — wrong operating point |
| `q1_ic` | `Ic(Q1)` | 10 – 26 mA (sim 16 mA; first-order 18 mA) | Quiescent current off — under/over-driven tank |
| `d3_pk` | `MAX abs(I(D3))` | < 1 mA | D3 conducting in normal use — clamp engaging wrongly |
| `drv_pk` | `MAX abs(I(L1))` | within linear swing, no flat-top | Driver clipping the transient |

> Before the transformer exists (Stage 2 in isolation), substitute `I(R_drive)` / collector-load current for `I(L1)`.

---

## Stage 3 — REB3S transformer

```spice
; Stage 3 — AC: the "drip" — resonant peak at the tank interface in 1-5kHz
.meas AC tank_pk_lvl MAX V(tank_in)
.meas AC tank_pk_f   WHEN V(tank_in)=tank_pk_lvl

; Stage 3 — AC: signal actually present at tank input
.meas AC tank_drive_db FIND 20*log10(V(tank_in)/V(rv1_wiper)) AT=2k
```

| Assertion name | Expression | Pass condition | Fail means |
|---|---|---|---|
| `tank_pk_f` | freq of max `V(tank_in)` | 1 – 5 kHz (≈2–3 kHz) | No "drip" — transformer L or K1 coupling wrong |
| `tank_drive_db` | `20log10(V(tank_in)/V(rv1_wiper))` @2k | > −60 dB | No signal reaching tank — winding/K1 error |

---

## Stage 4 — Input protection

```spice
; Stage 4 — OP: clamp diodes reverse biased at idle
.meas OP clamp_p_i FIND I(Dclamp_p)
.meas OP clamp_n_i FIND I(Dclamp_n)

; Stage 4 — TRAN: with 20Vpp overload, U1+ node is clamped
;   (drive V1 = SINE(0 10 1k) for this run)
.meas TRAN u1pos_hi MAX V(u1_pos)
.meas TRAN u1pos_lo MIN V(u1_pos)
```

| Assertion name | Expression | Pass condition | Fail means |
|---|---|---|---|
| `clamp_p_i` | `I(Dclamp_p)` | < 1 µA | Clamp leaking/forward at idle — wrong orientation |
| `u1pos_hi` | `MAX V(u1_pos)` (20 Vpp in) | ≤ +16 V | Positive overload not clamped — U1 input at risk |
| `u1pos_lo` | `MIN V(u1_pos)` (20 Vpp in) | ≥ −16 V | Negative overload not clamped |

---

## Stage 5 — Power supply

```spice
; Stage 5 — OP: regulated rails within +/-1%
.meas OP rail_pos FIND V(+15V)
.meas OP rail_neg FIND V(-15V)

; Stage 5 — TRAN: supply ripple under load (settle first, then measure)
.meas TRAN ripple_pos PP V(+15V) FROM=100m TO=120m
.meas TRAN ripple_neg PP V(-15V) FROM=100m TO=120m
```

| Assertion name | Expression | Pass condition | Fail means |
|---|---|---|---|
| `rail_pos` | `V(+15V)` | 14.85 – 15.15 V | +rail out of regulation — LM7815/filter issue |
| `rail_neg` | `V(-15V)` | −15.15 – −14.85 V | −rail out of regulation — LM7915/filter issue |
| `ripple_pos` | `PP V(+15V)` | < 10 mVpp | Insufficient filtering — ripple into recovery stage |
| `ripple_neg` | `PP V(-15V)` | < 10 mVpp | Same on negative rail |

---

## Stage 6 — Full integration

```spice
; Stage 6 — re-run ALL Stage 1 assertions (off_u1/2/3, recov_gain,
;           hpf_m3db, vout_pk, osc_ratio) unchanged.

; Stage 6 — OP: complete DC operating point (op-amps + driver bias)
.meas OP off_u1 FIND V(u1_out)
.meas OP off_u2 FIND V(u2_out)
.meas OP off_u3 FIND V(v_out)
.meas OP q1_ve  FIND V(q1_e)

; Stage 6 — AC: full-chain gain within +/-2dB of design target
.meas AC chain_lvl  FIND V(v_out) AT=1k
.meas AC chain_gain_db FIND 20*log10(V(v_out)/V(vin)) AT=1k
```

| Assertion name | Expression | Pass condition | Fail means |
|---|---|---|---|
| Stage 1 set | (as above) | all still pass | A later stage regressed the baseline |
| `off_u1/2/3` | op-amp outputs | \|val\| ≤ 10 mV | Real PSU/driver introduced DC offset |
| `q1_ve` | `V(q1_e)` | 1.0 – 1.4 V | Bias shifted under regulated rails |
| `chain_gain_db` | `20log10(V(v_out)/V(vin))` @1k | design target ±2 dB | End-to-end gain drifted out of spec |

---

## Running the suites

- One analysis directive active at a time (`.op` **or** `.ac` **or** `.tran`). Comment the others.
- Results print to the **SPICE Error Log** (Ctrl+L). A red run is a missing value or an out-of-range number; a green run is every assertion in range.
- Keep each stage's `.asc` so any regression bisects to the last component group added.
