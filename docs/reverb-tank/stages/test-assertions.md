# Ghost Spring Reverb — SPICE Test Assertions

> **Authority scope (single source of truth).** This file is **THE authority for all numerical pass criteria** (the measurement windows every bench and SPICE test must land in). If a pass band quoted anywhere else disagrees with the value here, **this file wins.** For other classes of value, go to the authoritative source:
> - **Component values** (R/C/L, ratios): [`stage_06_full.net`](./stage_06_full.net) — the netlist is ground truth.
> - **Parts** (Mouser PNs, quantities, packages): [`mouser-bom.csv`](../mouser-bom.csv).
> - **Design rationale** (why a value was chosen): [`parts-spec.md`](../parts-spec.md).
> - **Bench procedures** (what the builder does): [`builder-guide.md`](./builder-guide.md).
>
> The pass windows defined here are **also tabulated for convenience in [`circuit-params.md`](../circuit-params.md)** (the canonical parameter table). **This file remains the computational authority for the `.meas` directives and pass bands** — if circuit-params.md disagrees with a window here, this file wins.

The `.meas` directives below are the **PASS conditions** for each build stage in [`build-plan.md`](./build-plan.md). They are the SPICE equivalent of a unit-test suite.

## What SPICE TDD means in practice

You write the `.meas` assertions **before** adding the component group, run the simulation, and confirm they *fail* — the component isn't there yet, so the number is wrong (or the node doesn't exist). Then you add the component and run again, confirming the assertion now *passes*. It's the same red-green-refactor loop as software TDD: the failing measurement is your "red," the passing measurement is your "green," and tightening values/parts to keep all prior stages green is the "refactor."

LTspice prints `.meas` results to the SPICE Error Log (Ctrl+L). A measurement that can't evaluate (missing node, no crossing) reports `FAIL`/no value — that *is* your red state.

---

## Stage 1 — MVP baseline

```spice
; Stage 1 — TRAN: every op-amp output DC-settles near 0V (Vos=0 model)
.meas TRAN off_u1 AVG V(u1_out) FROM=190m TO=200m
.meas TRAN off_u2 AVG V(u2_out) FROM=190m TO=200m
.meas TRAN off_u3 AVG V(v_out)  FROM=190m TO=200m

; Stage 1 — AC: recovery stage gain = 1 + Rf/Ri = 1 + 100k/470 = 213.8x nominal
;   (component values per stage_06_full.net; pass band below covers 1% Rf/Ri parts + meas error)
.meas AC recov_gain FIND mag(V(u2_out)/V(u2_in_pos)) AT=1k

; Stage 1 — AC: wet HPF -3dB corner. DESIGN corner = 1/(2*pi*R6*C4)
;   = 1/(2*pi*5.6k*100n) = 284Hz. MEASURED in stage_06_full sim = 312Hz
;   (the two differ because of loading; both fall inside the 250-320Hz pass band).
.meas AC hpf_ref  FIND mag(V(hpf_out)/V(u2_out)) AT=5k
.meas AC hpf_m3db WHEN mag(V(hpf_out)/V(u2_out))=hpf_ref*0.7079 RISE=1

; Stage 1 — TRAN: output not clipping (settled window, skips power-up surge)
.meas TRAN vout_pk MAX abs(V(v_out)) FROM=50m TO=100m

; Stage 1 — TRAN: no oscillation — RMS late window vs early window
.meas TRAN rms_early RMS V(v_out) FROM=40m   TO=50m
.meas TRAN rms_late  RMS V(v_out) FROM=90m   TO=100m
.meas TRAN osc_ratio PARAM rms_late/rms_early
```

| Assertion name | Expression | Pass condition | Fail means |
|---|---|---|---|
| `off_u1` | `V(u1_out)` | \|val\| ≤ 10 mV | U1 has a DC offset — bias/coupling error |
| `off_u2` | `V(u2_out)` | \|val\| ≤ 10 mV | Recovery DC offset — Rbias/C3 issue, will clip mix |
| `off_u3` | `V(v_out)` | \|val\| ≤ 10 mV | Output offset — DC to the MC100 |
| `recov_gain` | `V(u2_out)/V(u2_in_pos)` @1k | 205 – 225 | Wrong Rf/Ri ratio — recovery gain off |
| `hpf_m3db` | freq where wet = 0.7079×ref | 250 – 320 Hz | HPF corner wrong — R6/C4 value error |
| `vout_pk` | `MAX abs(V(v_out))` | < 14 V | Output clipping into the rails |
| `osc_ratio` | RMS_late / RMS_early | < 1.05 | Signal growing — oscillation/instability |

> **`off_u2` is a *simulation* window, not a bench expectation.** The SPICE op-amp model uses `Vos=0`, so the simulated `off_u2` settles near 0 V and the ±10 mV window is meaningful in sim. A **real OPA2134** has an input offset (Vos up to ~500 µV) that the 214× recovery gain multiplies to a steady **20–150 mV DC at U2's output** — this is *normal*, and C4 blocks it before the output. **Do not apply the ±10 mV `off_u2` window to the bench measurement at U2's output.** The bench pass/fail for U2 output DC is in [`builder-guide.md`](./builder-guide.md) Stage 2 (20–150 mV typical, normal for OPA2134 at 214× gain; blocked by C4). The ±10 mV bench window *does* still apply at U1's output (`off_u1`) and at the final output after C4 (`off_u3`, < 5 mV at J2).

---

## Stage 2 — BD139 driver

```spice
; Stage 2 — TRAN: Q1 bias point (steady-state AVG over 190–200ms)
.meas TRAN q1_ve AVG V(q1_e) FROM=190m TO=200m
.meas TRAN q1_ic AVG Ic(Q1)  FROM=190m TO=200m

; Stage 2 — OP cross-check: the collector current implied by the emitter
;   voltage across R5 (Ic ~= Ie = Ve/R5) must agree with the collector current
;   measured DIRECTLY through the BJT, Ic(Q1). The op variant of stage_06_full.net
;   emits BOTH the implied current (q1_ic_calc = Ve/R5) AND its INDEPENDENT
;   comparison target q1_ic = Ic(Q1), plus q1_ic_err = |q1_ic - q1_ic_calc| /
;   q1_ic_calc, which must stay under 10%. (The old target q1_ic = I(R5) made this
;   a tautology: I(R5) is identically V(q1_e)/R5, so q1_ic_err was always ~0. Ic(Q1)
;   goes through the transistor model and differs from Ie by the base current ~1%
;   at Bf=100, so the cross-check is now a real ~1% read.) This catches an
;   inconsistent bias read that q1_ve / q1_ic alone would each pass. The divisor
;   tracks circuit_params.R5, so it never silently drifts if R5 changes.
;   (R5=68Ω, interpolated by the generator — 'R5' is a component instance name in
;   LTspice, NOT a .param, so the literal {q1_ve/68} is what the netlist carries.)
.meas TRAN q1_ic_calc PARAM {q1_ve/68}
.meas TRAN q1_ic      AVG Ic(Q1) FROM=190m TO=200m
.meas TRAN q1_ic_err  PARAM {abs(q1_ic - q1_ic_calc) / q1_ic_calc}

; Stage 2 — TRAN: Q1 must stay FORWARD-ACTIVE (not saturated). Read the collector
;   DC and derive Vce = V(q1_c)-V(q1_e) and Vcb = V(q1_c)-V(q1_base). If Q1
;   saturates (Vce -> Vce(sat) ~0.2V, Vcb < 0) the transformer drive flat-tops
;   and the reverb send distorts -- a failure q1_ve/q1_ic alone never catch.
.meas TRAN q1_vc  AVG V(q1_c)    FROM=190m TO=200m
.meas TRAN q1_vb  AVG V(q1_base) FROM=190m TO=200m
.meas TRAN q1_vce PARAM {q1_vc - q1_ve}
.meas TRAN q1_vcb PARAM {q1_vc - q1_vb}

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
| `q1_ic_calc` | `q1_ve/68` (Ve across R5; R5=68Ω, interpolated by generator) | compared to `q1_ic` below | Ve-implied Ic and the BJT collector current disagree — wrong R5 or mis-probed emitter |
| `q1_ic` | `Ic(Q1)` (collector current through the BJT) | 10 – 26 mA | the independent comparison target for `q1_ic_calc` |
| `q1_ic_err` | `\|q1_ic − q1_ic_calc\| / q1_ic_calc` | < 10% | Ve-implied Ic and the measured collector current disagree by > 10% |
| `q1_vb` | `V(q1_base)` | 1.65 – 2.05 V (unloaded 1.92 V from R3b/R4 divider; base current loads it slightly lower → Q1_VB_WINDOW) | Base bias wrong — R3b or R4 value off, or divider open |
| `q1_vc` | `V(q1_c)` (collector DC) | 3 – 15.2 V (sim ≈14.6 V) | Collector pinned low — Q1 saturated or transformer/D3 short |
| `q1_vce` | `V(q1_c) − V(q1_e)` | > 1 V (≫ Vce(sat) 0.2 V) | Q1 saturated — collector swing flat-tops, send distorts |
| `q1_vcb` | `V(q1_c) − V(q1_base)` | ≥ 0 V (CBJ reverse-biased) | Collector below base — Q1 in saturation |
| `d3_pk` | `MAX abs(I(D3))` | < 1 mA | D3 conducting in normal use — clamp engaging wrongly |
| `drv_pk` | `MAX abs(I(L1))` | < 45 mA (≈2.8× quiescent Ic; within linear swing, no flat-top) | Driver clipping the transient |
| `drv_rms` | `RMS I(L1)` | < 40 mA (DC-dominated, ≈2.5× quiescent Ic) | Driver over-driven / clipping |

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
| `tank_pk_f` | freq of max `V(tank_in)` | 1 – 5 kHz (≈2–3 kHz → TANK_PEAK_WINDOW) | No "drip" — transformer L or K1 coupling wrong |
| `tank_drive_db` | `20log10(V(tank_in)/V(rv1_wiper))` @2k | > −60 dB (→ TANK_DRIVE_DB_MIN) | No signal reaching tank — winding/K1 error |

---

## Stage 4 — Input protection

```spice
; Stage 4 — OP: clamp diodes reverse biased at idle; TVS pair non-conducting;
;   the jack node vin at 0V DC (no DC path charges it).
.meas OP clamp_p_i FIND I(Dclamp_p)
.meas OP clamp_n_i FIND I(Dclamp_n)
.meas OP tvs_a_i FIND I(DTVS1a)
.meas OP tvs_b_i FIND I(DTVS1b)
.meas OP vin_idle FIND V(vin)

; Stage 4 — TRAN (overload variant): with 40Vpp overload, U1+ node is clamped
;   AND the clamp diodes MUST conduct on the peaks (proving the clamp engages).
;   (drive V1 = SINE(0 20 1k) for this run = 20Vpk / 40Vpp; .tran 0 5m 0 10u.)
;   The input MUST exceed the ~15.7V clamp threshold for this assertion to mean
;   anything — a sub-threshold drive passes trivially without testing the clamp.
;   On the bench, see builder-guide Stage 5 PRE-CHECK (generator must hit >=38Vpp).
.meas TRAN u1pos_hi MAX V(u1_pos)
.meas TRAN u1pos_lo MIN V(u1_pos)
.meas TRAN clamp_p_pk MAX I(Dclamp_p)
.meas TRAN clamp_n_pk MIN I(Dclamp_n)
```

| Assertion name | Expression | Pass condition | Fail means |
|---|---|---|---|
| `clamp_p_i` | `I(Dclamp_p)` | < 1 µA | Clamp leaking/forward at idle — wrong orientation |
| `clamp_n_i` | `I(Dclamp_n)` | > −1 µA (reverse-biased) | Negative clamp leaking/forward at idle — wrong orientation |
| `tvs_a_i` | `I(DTVS1a)` | −1 µA – +1 µA (idle, not conducting) | TVS conducting at idle — wrong part/orientation |
| `tvs_b_i` | `I(DTVS1b)` | −1 µA – +1 µA (idle, not conducting) | TVS conducting at idle — wrong part/orientation |
| `vin_idle` | `V(vin)` | −10 mV – +10 mV (0 V DC) | Jack node biased off 0 V — DC leak onto the input |
| `u1pos_hi` | `MAX V(u1_pos)` (40 Vpp in) | ≤ +16 V | Positive overload not clamped — U1 input at risk |
| `u1pos_lo` | `MIN V(u1_pos)` (40 Vpp in) | ≥ −16 V | Negative overload not clamped |
| `clamp_p_pk` | `MAX I(Dclamp_p)` (40 Vpp in) | > 1e-06 (clamp conducts) | +clamp never engages — positive overload not absorbed |
| `clamp_n_pk` | `MIN I(Dclamp_n)` (40 Vpp in) | < -1e-06 (clamp conducts) | −clamp never engages — negative overload not absorbed |

---

## Stage 5 — Power supply

```spice
; Stage 5 — TRAN: regulated rails within +/-1% (steady-state AVG after settle)
.meas TRAN rail_pos AVG V(+15V) FROM=100m TO=120m
.meas TRAN rail_neg AVG V(-15V) FROM=100m TO=120m

; Stage 5 — TRAN: unregulated-bus headroom. The 78xx/79xx need their input
;   >= Vout + ~2V dropout to stay IN regulation; the bulk caps hold the bus
;   near the rectified peak (~19V). If |bus| sags below ~17V the regulator
;   drops out and the rail follows the ripple. (Measured but previously ungated.)
.meas TRAN unreg_pos AVG V(pos_rect) FROM=100m TO=120m
.meas TRAN unreg_neg AVG V(neg_rect) FROM=100m TO=120m

; Stage 5 — TRAN: supply ripple under load (settle first, then measure)
.meas TRAN ripple_pos PP V(+15V) FROM=100m TO=120m
.meas TRAN ripple_neg PP V(-15V) FROM=100m TO=120m
; Decorative informational probes — no gated window, reported for context only:
.meas TRAN rail_pos_avg AVG V(+15V) FROM=100m TO=120m   ; settled rail mean (duplicates ripple context)
.meas TRAN rail_neg_avg AVG V(-15V) FROM=100m TO=120m   ; settled rail mean (duplicates ripple context)
.meas TRAN unreg_pos_pp PP V(pos_rect) FROM=100m TO=120m ; unregulated-bus ripple (bench context)
.meas TRAN unreg_neg_pp PP V(neg_rect) FROM=100m TO=120m ; unregulated-bus ripple (bench context)
```

| Assertion name | Expression | Pass condition | Fail means |
|---|---|---|---|
| `rail_pos` | `V(+15V)` | 14.85 – 15.15 V | +rail out of regulation — LM7815/filter issue |
| `rail_neg` | `V(-15V)` | −15.15 – −14.85 V | −rail out of regulation — LM7915/filter issue |
| `unreg_pos` | `V(pos_rect)` | > 17 V (sim ≈19 V) | +reg dropout — bus below Vout+dropout, rail unregulates |
| `unreg_neg` | `\|V(neg_rect)\|` | > 17 V (sim ≈19 V) | −reg dropout — bus too low, −rail unregulates |
| `ripple_pos` | `PP V(+15V)` | < 10 mVpp | Insufficient filtering — ripple into recovery stage |
| `ripple_neg` | `PP V(-15V)` | < 10 mVpp | Same on negative rail |
| `rail_pos_avg` `rail_neg_avg` `unreg_pos_pp` `unreg_neg_pp` | — | *decorative — no gated window* | Informational only; not checked by validate.py |

> *Note: `rail_pos`/`rail_neg` (14.85–15.15 V) and `ripple_pos`/`ripple_neg` (< 10 mVpp) pass by construction under the behavioural LM78xx/LM79xx model (`min(V(IN,COM)−2, Vout)`): as long as the unregulated bus clears ~17 V the regulator output is pinned to ±15 V with zero ripple, regardless of bulk capacitor values. The binding rows in this variant are `unreg_pos`/`unreg_neg` (bus AVG ≥ 17 V) — those are the only rows with real teeth in simulation. Actual rail ripple must be verified on the bench.*

---

## Stage 6 — Full integration

```spice
; Stage 6 — re-run ALL Stage 1 assertions (off_u1/2/3, recov_gain,
;           hpf_m3db, vout_pk, osc_ratio) unchanged.

; Stage 6 — TRAN: DC operating point extracted as steady-state AVG (190–200ms)
.meas TRAN off_u1 AVG V(u1_out) FROM=190m TO=200m
.meas TRAN off_u2 AVG V(u2_out) FROM=190m TO=200m
.meas TRAN off_u3 AVG V(v_out)  FROM=190m TO=200m
.meas TRAN q1_ve  AVG V(q1_e)   FROM=190m TO=200m

; Stage 6 — TRAN: U2 non-inverting input DC bias. Rbias (100k) holds u2_in_pos at
;   0V and C3 (470n) blocks tank/rail DC. If Rbias opened or a rail leaked in,
;   this node floats to a DC offset that the 214x stage multiplies into U2 clip.
.meas TRAN u2_inpos_bias AVG V(u2_in_pos) FROM=190m TO=200m

; Stage 6 — AC: U1 input buffer is a unity-gain follower. V(u1_buf) must track
;   V(vin) at ~1.0x; a dead/mis-wired U1 would not pass signal at unity.
.meas AC u1_buf_gain FIND mag(V(u1_buf)/V(vin)) AT=1k

; Stage 6 — AC: recovery-stage gain (across U2) in dB, within +/-2dB of target.
;   recov_gain_db measures the SAME thing as recov_gain above —
;   20*log10(V(u2_out)/V(u2_in_pos)), the 214x non-inverting recovery stage —
;   expressed in dB. It deliberately does NOT measure the full vin->v_out chain:
;   the dry path attenuates (~-5 dB) and the wet path is tank/HPF-shaped, so
;   20*log10(V(v_out)/V(vin)) is only ~15-21 dB and would fail this window.
;   Target = CHAIN_GAIN_DB_SIM = 46.59 dB (= simulated recov_gain 213.8x);
;   pass window CHAIN_GAIN_DB_WINDOW = 44.6 - 48.6 dB (+/-2 dB).
.meas AC recov_lvl  FIND V(u2_out) AT=1k
.meas AC recov_gain_db FIND 20*log10(V(u2_out)/V(u2_in_pos)) AT=1k
```

| Assertion name | Expression | Pass condition | Fail means |
|---|---|---|---|
| Stage 1 set | (as above) | all still pass | A later stage regressed the baseline |
| `off_u1/2/3` | op-amp outputs | \|val\| ≤ 10 mV | Real PSU/driver introduced DC offset |
| `q1_ve` | `V(q1_e)` | 1.0 – 1.4 V | Bias shifted under regulated rails |
| `u2_inpos_bias` | `V(u2_in_pos)` | \|val\| ≤ 10 mV | Rbias open / rail leak — U2 + input floats, 214× clips |
| `u1_buf_gain` | `\|V(u1_buf)/V(vin)\|` @1k | 0.9 – 1.05 | U1 buffer dead/mis-wired — front-end not passing signal |
| `recov_gain_db` | `20log10(V(u2_out)/V(u2_in_pos))` @1k | 44.6 – 48.6 dB (target 46.59 dB ±2 dB) | Recovery-stage gain drifted out of spec |
| `recov_lvl` | `V(u2_out)` @1k | *decorative — no gated window* | Context probe: raw U2 output level; the gated quantity is `recov_gain_db` |
| `rail_pos` `rail_neg` | `AVG V(±15V)` | *decorative — no gated window* | Context: rail stability in TRAN run; the gated rail windows live in Stage 5 |

---

## Stage 7 — Mix blend

The Mix pot (RV2) is a **3-terminal passive blend**, not a volume knob: the dry
signal enters the CCW end (`mix_dry`, fed by `Rdry` from `u1_buf`), the wet
signal enters the CW end (`mix_wet`, fed directly from the Tone wiper
`rv3_wiper`), and the wiper (`mix_node`) feeds U3. `C_bright` (47pF) bridges the
full pot (`mix_dry`↔`mix_wet`). This cannot be expressed as a single `.meas`
crossing on the current tran/op runs (the pot wiper position is not a swept SPICE
variable), so the expected behavior is documented here and verified on the bench
(builder-guide Stage 7a sanity gates) and by `validate.py check_mix_topology()`:

Pre-condition: signal applied to INPUT
- Mix full-CCW: V(u3_out) ≈ V(u1_buf) (dry only, attenuation < 3dB)
- Mix full-CW: V(u3_out) contains only wet signal (no dry)
- Mix noon: both dry and wet present at u3_out

| Assertion name | Expression | Pass condition | Fail means |
|---|---|---|---|
| `mix_ccw_dry` | V(u3_out) vs V(u1_buf), Mix full-CCW | dry passes, atten < 3 dB; no wet | Wet bleeds at full-CCW — Rwet short or bridged mix node |
| `mix_cw_wet` | V(u3_out), Mix full-CW | wet only, dry absent | Dry bleeds at full-CW — pot/Rdry mis-wired |
| `mix_noon` | V(u3_out), Mix noon | both dry + wet present | One path dead — open pot half or missing wire |

> **Topology guard.** `validate.py` parses `stage_06_full.net` and fails the
> build if the Mix node is wired as a volume knob (a near-zero `Rwet` shorting
> the wet source onto the dry node, collapsing the blend). This is the static
> check that would have caught the original `Rwet = 0.001Ω` bug.

---

## Stage 7 — Pot position sweep (GitHub issue #43)

All the op/ac/tran variants above hardcode every pot at **50 % (equal halves)**.
That leaves the travel **extremes** untested — yet the real failure modes live
there (zero drive, hard clip, dry/wet bleed, tone cut/peak). This stage adds
**pot-extreme variants** of `stage_06_full`: each drives **one** pot to a rail
(`0.0` = CCW/min, `1.0` = CW/max) while holding the others at noon, then runs a
**200 ms `.tran` with the 100 mVpk 1 kHz stimulus** and gates the failure mode
that extreme exposes.

The two pot halves are modelled by `pot_split(total, position)` in
`gen_stage6_full.py`: `a = position·total`, `b = (1−position)·total`, each floored
at `POT_MIN_OHMS = 0.001 Ω` (a true 0 Ω half can float/short the wiper node in
SPICE). Pot totals (from the netlist): Dwell `RV1 = 10k`, Mix `RV2 = 100k`, Tone
`RV3 = 100k`. The variants are generated by `sync.py` and structurally guarded by
`validate.py check_variant_netlists()` + the `test_sync.py` meta-guard.

**Level vs DC reads.** A clean sine's raw `AVG` over whole cycles is ~0, so the
`.meas` directives that gate a **signal level** use `MAX abs()` over a settled
tail (`190 m–200 m`); `AVG` is reserved for the **DC-bias** reads (the bypassed
Q1 emitter `q1_e`, and the post-clip DC-settle at `u2_out`).

```spice
; dwell_min — Dwell 0% (CCW): RV1a≈0 shunts the wiper to GND = MINIMUM wet drive.
;   The DRY path (u1_buf->Rdry->mix_dry) is independent of Dwell and must still pass.
.meas TRAN dwell_min_vout MAX abs(V(v_out))  FROM=190m TO=200m
.meas TRAN dwell_min_dry  MAX abs(V(mix_dry)) FROM=190m TO=200m

; dwell_max — Dwell 100% (CW): RV1b≈0 pulls the wiper to u1_buf = MAXIMUM wet
;   drive. U2 output must not hard-clip and the wiper must carry the drive signal.
.meas TRAN dwell_max_u2_pk MAX abs(V(u2_out)) FROM=50m TO=200m
.meas TRAN dwell_max_wiper_pk MAX abs(V(rv1_wiper)) FROM=190m TO=200m

; mix_ccw — Mix 0% (RV2a≈0, RV2b=100k = full dry): wiper ties to mix_dry. Two
;   prior attempts were tautologies:
;     v1: V(mix_node)/V(mix_dry) — RV2a=0.001 hard-shorts both to the same node.
;     v2: V(mix_wet)/V(rv3_wiper) — Rwet_wire=0R makes these the same node.
;   Correct probe: mix_ccw_wet_ratio = V(mix_wet)/V(hpf_out). hpf_out and mix_wet
;   are separated by RV3a=50k (series) + RV3b=50k||RV2b=100k (shunt). At center
;   wiper the ratio is ~0.40. A broken RV3 wiper, open Rwet_wire, or shorted RV3b
;   all push outside the 0.20–0.65 window. Cannot be 1.0 by construction.
.meas TRAN mix_ccw_vout_pk   MAX abs(V(v_out))    FROM=190m TO=200m
.meas TRAN mix_ccw_wet_src   RMS V(hpf_out)   FROM=190m TO=200m
.meas TRAN mix_ccw_wet_node  RMS V(mix_wet)   FROM=190m TO=200m
.meas TRAN mix_ccw_wet_ratio PARAM {mix_ccw_wet_node/mix_ccw_wet_src}

; mix_cw — Mix 100% (RV2a=100k, RV2b≈0 = full wet): wiper ties to mix_wet (Tone
;   output); the dry node sees little of the wiper (dry_attn small).
.meas TRAN mix_cw_vout_pk  MAX abs(V(v_out))    FROM=50m TO=200m
.meas TRAN mix_cw_mix_node MAX abs(V(mix_node)) FROM=190m TO=200m
.meas TRAN mix_cw_dry_lvl  MAX abs(V(mix_dry))  FROM=190m TO=200m
.meas TRAN mix_cw_dry_attn PARAM {mix_cw_dry_lvl/mix_cw_mix_node}

; dwell_max_mix_cw — worst-case clip path (Dwell max + Mix full-CW): v_out
;   (downstream of U3) must not exceed WORST_CASE_PK_MAX and its DC must settle
;   back to ~0 (no latch-up).
.meas TRAN worst_case_pk     MAX abs(V(v_out)) FROM=50m TO=200m
.meas TRAN worst_case_settle AVG V(v_out)      FROM=190m TO=200m
```

| Variant | Pots (Dwell / Mix / Tone) | Assertion | Pass condition | Fail means |
|---|---|---|---|---|
| `dwell_min` | 0 % / 50 % / 50 % | `dwell_min_dry` | 0.05 – 0.15 V (≈0.1 V pk) | Dry path dead at min Dwell — Dwell wrongly gates dry |
| `dwell_min` | 0 % / 50 % / 50 % | `dwell_min_vout` | 0.02 – 0.12 V (≈0.045 V pk; dry-only through RV2 noon divider → DWELL_MIN_VOUT_WINDOW) | Whole output dead at min Dwell — Rdry open or RV2 mis-wired |
| `dwell_max` | 100 % / 50 % / 50 % | `dwell_max_u2_pk` | < 13.5 V (no hard clip at U2; probes `V(u2_out)` → DWELL_MAX_U2_PK_MAX) | U2 railing at max Dwell drive |
| `dwell_max` | 100 % / 50 % / 50 % | `dwell_max_wiper_pk` | 0.03 – 0.15 V (wiper carries the drive) | Wet drive dead at max Dwell — Dwell pot inverted or wiper open |
| `mix_ccw` | 50 % / 0 % / 50 % | `mix_ccw_vout_pk` | 0.05 – 0.15 V (dry present) | Dry signal absent at full-CCW |
| `mix_ccw` | 50 % / 0 % / 50 % | `mix_ccw_wet_ratio` | 0.2 – 0.65 (`V(mix_wet)/V(hpf_out)` across RV3 divider; ~0.40 at center wiper) | Wet chain broken: open RV3 wiper, shorted RV3b, or open Rwet_wire |
| `mix_cw` | 50 % / 100 % / 50 % | `mix_cw_vout_pk` | > 0.2 V (wet signal at useful level; baseline Mix-noon sim = 1.16 V) | Output dead or badly attenuated at full-CW |
| `mix_cw` | 50 % / 100 % / 50 % | `mix_cw_dry_attn` | < 0.5 (dry node attenuated vs wiper) | Dry bleeds through at full-CW |
| `dwell_max_mix_cw` | 100 % / 100 % / 50 % | `worst_case_pk` | ≤ 6 V (`v_out` at Dwell-max/Mix-CW → WORST_CASE_PK_MAX; analytical ceiling 0.4 × 13.5 V = 5.4 V) | U3 rails on worst-case path |
| `dwell_max_mix_cw` | 100 % / 100 % / 50 % | `worst_case_settle` | \|DC\| < 0.5 V (settles after clip) | U3 latched off-zero after a clip |

> *Note: `worst_case_settle` (AVG V(v_out) over 190–200 ms) passes by construction under the ideal `Vos=0` op-amp model — the AVG of a 1 kHz sine over exactly 10 cycles is ≈ 0 regardless of amplitude, so the < 0.5 V gate is trivially satisfied without any latch-up present. The check only acquires teeth under realistic conditions: a non-zero Vos (Stage 8b), an asymmetric clip, or a genuine DC latch-up. The binding worst-case assertion on this variant is `worst_case_pk` (≤ 6 V → WORST_CASE_PK_MAX).*

> **Pass windows** are grounded in the circuit and tabulated in
> `circuit_params.py` (`DWELL_MIN_DRY_WINDOW`, `DWELL_MAX_WIPER_PK_WINDOW`,
> `DWELL_MAX_U2_PK_MAX`, `WORST_CASE_PK_MAX`, `MIX_CCW_VOUT_WINDOW`,
> `WORST_CASE_SETTLE_MAX`). The dry level ≈ 0.1 V pk follows from the 100 mVpk
> input through the unity U1 buffer and the Rdry/RV2 divider; the < 13.5 V ceiling
> gates U2's output (`dwell_max_u2_pk`); the ≤ 6 V ceiling gates `v_out`
> downstream of U3 (`worst_case_pk`, analytical ceiling 0.4 × 13.5 = 5.4 V). As
> with the Mix-blend section, the **wiper position is not a swept SPICE variable**,
> so each pot extreme is a SEPARATE generated netlist rather than one parametric
> `.meas`.

---

## Stage 8 — Stress variants (realistic hardware conditions)

The baseline op/ac/tran sims are **idealized**: every op-amp uses `Vos=0`, the
mains sits at its nominal voltage, and the BD139 uses its nominal forward beta.
Real hardware won't be ideal. These variants re-run the relevant pass criteria
under the **most likely real-world deviations** and confirm the design still
passes the **same windows** — a deviation that pushes any quantity out of its
existing window is a real design weakness, not a modelling artifact.

Each variant is a separate generated netlist (`sync.py`) and is structurally
guarded by `validate.py check_variant_netlists()` + the `test_sync.py` meta-guard.

### 8a — Low mains voltage (PSU headroom)

ANSI C84.1 allows **114–126 V** for a 120 V nominal mains; older homes can sag to
**~108 V** under load. The `psu_low_mains` variant scales the T1 secondary AC
source by `PSU_LOW_MAINS_VFACTOR = 0.9×` (108 V = 10 % low) and re-runs the
**identical** Stage 5 ripple/rail checks. With ~+19 V of unregulated bus at
nominal mains there is ample dropout headroom, so even at 0.90× the regulators
must still hold ±15 V and ripple must stay in spec. **Same windows apply** —
`rail_pos`/`rail_neg` (14.85 – 15.15 V), `ripple_pos`/`ripple_neg` (< 10 mVpp),
and `unreg_pos`/`unreg_neg` (> 17 V dropout headroom on the sagged bus). The AVG
headroom check can pass while the **rippling bus trough** dips below dropout, so
the variant also gates the instantaneous trough — `unreg_pos_min` (bus MIN) and
`unreg_neg_min` (the −bus MAX = least-negative = its trough) — against the SAME
floor `UNREG_TROUGH_MIN` (> 17 V (trough)).

```spice
; psu_low_mains — T1 secondary scaled to 108V (0.90x), SAME ripple/rail checks
.meas TRAN ripple_pos PP V(+15V) FROM=100m TO=120m
.meas TRAN ripple_neg PP V(-15V) FROM=100m TO=120m
.meas TRAN rail_pos AVG V(+15V) FROM=100m TO=120m
.meas TRAN rail_neg AVG V(-15V) FROM=100m TO=120m
.meas TRAN unreg_pos AVG V(pos_rect) FROM=100m TO=120m
.meas TRAN unreg_neg AVG V(neg_rect) FROM=100m TO=120m
; trough (instantaneous) — must clear dropout, not just the average
.meas TRAN unreg_pos_min MIN V(pos_rect) FROM=50m TO=100m
.meas TRAN unreg_neg_min MAX V(neg_rect) FROM=50m TO=100m
```

| Variant | Assertion | Pass condition | Fail means |
|---|---|---|---|
| `psu_low_mains` (0.90×) | `ripple_pos` / `ripple_neg` | < 10 mVpp | Ripple rejection fails on low mains |
| `psu_low_mains` (0.90×) | `rail_pos` / `rail_neg` | 14.85 – 15.15 V | Regulator drops out on low mains |
| `psu_low_mains` (0.90×) | `unreg_pos` / `unreg_neg` | > 17 V | Bus below dropout — rail unregulates |
| `psu_low_mains` (0.90×) | `unreg_pos_min` / `\|unreg_neg_min\|` | > 17 V (trough) | Ripple trough dips below dropout — rail unregulates at the bottom of each cycle |

> *Note: the `rail_pos`/`rail_neg` and `ripple_pos`/`ripple_neg` rows pass by construction under the behavioural LM78xx/LM79xx model (`min(V(IN,COM)−2, 15)`): as long as the bus trough clears 17 V the regulator output is pinned to ±15 V with no ripple. The binding constraint on this variant is `unreg_pos_min`/`unreg_neg_min` (trough ≥ 17 V) — that is the only row with real teeth here.*

### 8b — U2 input offset injection (Vos stress)

A real **OPA2134** has an input offset voltage **Vos up to 500 µV** (typ 50 µV).
The `stage6_vos` variant inserts a 500 µV DC source (`Vos_u2`) **in series** at
U2's non-inverting input; the **213.8× recovery gain** multiplies it to **~107 mV
DC at u2_out**. The recovery **gain** is an AC property and is *unaffected* by
Vos, so `recov_gain_db` stays in its window (verified in the `ac` variant). The
new check is the **settled DC offset at U2's output**: `u2_out_dc_vos` must land
within `U2_VOS_OUT_WINDOW = ±150 mV` — confirming 214× × 500 µV stays inside the
bench-documented **20–150 mV** typical band and is blocked by C4 before v_out.

```spice
; stage6_vos — 500uV in series at U2(+); settled DC at u2_out (gain unaffected)
.meas TRAN u2_out_dc_vos AVG V(u2_out) FROM=190m TO=200m
.meas TRAN u2_inpos_vos  AVG V(u2_in_pos) FROM=190m TO=200m
```

| Variant | Assertion | Pass condition | Fail means |
|---|---|---|---|
| `stage6_vos` (500 µV) | `u2_out_dc_vos` | \|val\| ≤ 150 mV | Vos×214 exceeds C4-blockable headroom — U2 near clip |
| `stage6_vos` (500 µV) | `u2_inpos_vos` | *decorative — no gated window* | Context probe: actual U2(+) DC under Vos injection (≈ Vos = 500 µV) |
| `stage6_vos` (500 µV) | `rail_pos` `rail_neg` | *decorative — no gated window* | Context: rail stability unchanged by Vos injection |

### 8c — BD139 low-beta corner

The BD139 datasheet specifies **hFE min = 40** (at Ic = 500 mA); typical is
~100–150. The emitter degeneration (R5 = 68 Ω) plus the stiff R3b/R4 base-bias
divider make the Q1 bias point **largely beta-independent**. The `lo_beta`
variant overrides the model with `.model BD139_lo NPN(... BF=40 ...)` (the BD139
params with **BF=40**) and re-runs the **same** Q1 bias checks. If `q1_ve`/`q1_ic`
fall out of window at BF=40, the bias design is *not* beta-independent — a real
defect.

```spice
; lo_beta — BD139 with BF=40 (datasheet hFE min); SAME Q1 bias windows.
;   q1_ic = Ic(Q1) (collector current through the BJT), NOT I(R5) (emitter Ie):
;   at BF=40 the base current is ~2.4% of Ie, the corner where Ic and Ie diverge.
.meas TRAN q1_ve AVG V(q1_e) FROM=190m TO=200m
.meas TRAN q1_ic AVG Ic(Q1)  FROM=190m TO=200m
```

| Variant | Assertion | Pass condition | Fail means |
|---|---|---|---|
| `lo_beta` (BF=40) | `q1_ve` | 1.0 – 1.4 V | Bias shifts with beta — divider too soft / R5 wrong |
| `lo_beta` (BF=40) | `q1_ic` | 10 – 26 mA | Quiescent current beta-dependent — under/over-driven tank |
| `lo_beta` (BF=40) | `rail_pos` `rail_neg` | *decorative — no gated window* | Context: rail stability unchanged at low beta |

---

## Running the suites

- One analysis directive active at a time (`.op` **or** `.ac` **or** `.tran`). Comment the others.
- Results print to the **SPICE Error Log** (Ctrl+L). A red run is a missing value or an out-of-range number; a green run is every assertion in range.
- Keep each stage's `.asc` so any regression bisects to the last component group added.
