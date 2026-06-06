# Ghost Spring Reverb — Builder Verification Guide

This guide is for the person assembling the physical unit on a bench. Each stage of assembly has a small set of measurements to make **before** moving to the next. These measurements correspond directly to the SPICE simulations in [`test-assertions.md`](./test-assertions.md) that verified the design: if the simulation passed and your bench measurement lands in the same window, that stage is correct and you can move on. If a bench number is out of range, the "Fail action" column tells you the most likely cause — fix it before adding more parts, exactly the way you'd keep a test suite green before writing the next feature.

The assembly order below (visual → power → driver → transformer → input protection → full chain) is the order it's easiest to build and test on a bench. It is **not** the same numbering as the SPICE build stages, which replace one idealized block at a time. The cross-reference is noted under each section so you can find the matching simulation. Component values and the reason behind each are in [`parts-spec.md`](../parts-spec.md) — read the rationale before substituting anything.

**Equipment needed**

| Tool | Use |
|---|---|
| DMM (digital multimeter) | DC voltages, resistance, diode-check, leakage |
| Oscilloscope, 2-channel preferred | Waveforms, clipping, phase, resonant peak |
| Signal generator or audio interface | Sine sweeps and fixed-tone test signals |
| ±15V bench supply | Powers the circuit before the on-board PSU stage is built |

> **Safety — PSU filter caps hold charge.** Once the on-board power supply (C11/C12, 2200µF) is built, those caps hold ~21V after power-off. The 10kΩ bleed resistors (R_bleed1/2) drain them, but it takes time: τ = 10kΩ × 2200µF = 22s, so ~110s to reach <2V. **Wait at least 1–2 minutes after switching off — or measure across the caps with the DMM — before touching the supply.** Until the PSU stage exists you are on the bench supply, which has no stored charge, but build the habit now.

---

## Stage 1 — Signal path baseline (before powering up)

Visual checks only. No power yet. Corresponds to the SPICE **Stage 1 MVP** `.op` (DC offset) checks — you can't measure DC offset before power, so this is the pre-power equivalent: get the parts in correctly so the power-on checks pass.

- [ ] All op-amp ICs seated correctly (pin 1 orientation — notch/dot toward the pin-1 mark on the board)
- [ ] No solder bridges visible under magnification
- [ ] All capacitor polarities correct — **C2** (100µF electrolytic at Q1 emitter) is the polarized signal-path cap; the supply electrolytics C13–C16 are also polarized
- [ ] **R1 is placed AFTER C_in** — from the U1(+) pin to GND, **NOT** in series between the jack and C_in. This is the single most common front-end wiring error. R1 is the FET input's DC return; in series it would block the signal instead of biasing the input. (See parts-spec R1 and C_in entries.)

---

## Stage 2 — Power-on checks (±15V bench supply, no signal)

Connect the ±15V bench supply. No input signal. Corresponds to the SPICE **Stage 1** `.op` DC-offset assertions (`off_u1`, `off_u2`, `off_u3`, each |val| ≤ 10mV).

| Test point | Expected | Instrument | Fail action |
|---|---|---|---|
| +15V rail to GND | 14.85–15.15V | DMM DC | Check bench supply / rail wiring |
| −15V rail to GND | −14.85 to −15.15V | DMM DC | Check bench supply / rail wiring |
| U1 output pin | < ±10mV | DMM DC | Check R1 placement (after C_in), op-amp orientation |
| U2 output pin | < ±10mV | DMM DC | Check Ri (470Ω) / Rf (100kΩ); check C3 not leaking DC |
| U3 output pin | < ±10mV | DMM DC | Check mix-stage wiring (Rdry, RV2, C_bright) |

> If any op-amp output sits at or near a rail (±~13V) instead of near 0V, that stage's input has no DC reference or the op-amp is in backwards. On a FET-input part with no DC return the output slams to a rail — for U1 that almost always means R1 is missing or wired in series.

---

## Stage 3 — BD139 driver bias (±15V, no signal)

Corresponds to SPICE **Stage 2** `.op` (`q1_ve` 1.0–1.4V, `q1_ic` 10–26mA). Measure the bias point with no signal applied.

| Test point | Expected | Instrument | Fail action |
|---|---|---|---|
| Q1 emitter (R5 top) to GND | 1.0–1.4V DC (target 1.22V) | DMM DC | Low: check R3b (6.8k) / R4 (1k) divider. Zero: Q1 reversed or open |
| Q1 base to GND | ~1.7–2.0V DC (target 1.92V) | DMM DC | Check R3b, R4, R3 (1k base series) |
| Q1 collector to GND | ~13–14V DC | DMM DC | High (=+15V): Q1 not conducting — check bias chain |
| Across R5 (68Ω) | ~65–95mV | DMM DC | Ic = V/68Ω should land 10–26mA (target ~18mA) |

> The collector sits a volt or two below +15V because L1 (transformer primary) is a near-DC-short to the +15V rail, so the collector idles close to the rail and only swings *down* under drive. Don't expect a mid-rail collector here — this is a transformer-loaded collector, not a resistor-loaded one.

**Signal check (signal generator + oscilloscope):**

- Apply 100mVpp, 1kHz sine to the input jack.
- Probe the transformer primary (L1 / Q1 collector): expect a clean AC swing with **no flat-top clipping**. (SPICE **Stage 2** `drv_pk` — clean drive current, no flat-top.)
- Probe D3 cathode (collector side): should sit at +15V DC and only spike above it on hard transients. (SPICE **Stage 2** `d3_pk` < 1mA — D3 idle in normal use.) Continuous conduction here means the flyback clamp is engaging when it shouldn't — check the bias point first.

---

## Stage 4 — Transformer resonance ("the drip")

Corresponds to SPICE **Stage 3** `.ac` (`tank_pk_f` 1–5kHz, `tank_drive_db` > −60dB). This is the resonant peak that gives the unit its 6G15-style attack character. (Note on equipment: the macOS Wine LTspice build runs `.tran`/`.op` headlessly but `.ac` sweeps are unreliable headless — on the bench you sweep this by hand with the generator, which is the real verification anyway.)

| Test | Method | Expected | Fail action |
|---|---|---|---|
| Resonant peak frequency | Sweep generator 500Hz–10kHz, probe tank input (L2 secondary, at the 8Ω RCA) | Peak amplitude between 1–5kHz (target ~2–3kHz) | No peak: check L1/L2 coupling and K1 (transformer orientation); confirm primary→collector, secondary→tank |
| Tank input impedance | DMM resistance, tank **disconnected** | 8Ω ±20% at the tank input RCA (8Ω side) | Wrong value: tank is in backwards — verify input (8Ω) vs output (2550Ω) side |

> **Transformer orientation is directional.** The REB3S primary goes to Q1's collector (L1); the 8Ω secondary goes to the tank input (L2). Wire it backwards and you get no reverb at all — the secondary can't drive the high-Z collector node. If you measure ~2550Ω where you expect 8Ω, you have the tank (or the transformer) reversed.

---

## Stage 5 — Input protection

Corresponds to SPICE **Stage 4** (`stage_04_input_protect.asc`): `.op` clamp reverse-bias (`clamp_p_i`, `clamp_n_i` < 1µA) and the 20Vpp overload `.tran` (`u1pos_hi` ≤ +16V, `u1pos_lo` ≥ −16V). This is the front-end: C_in, R1, the 1N4148 clamp pair (Dclamp+/−), and TVS1 (SMBJ15CA) across the jack.

| Test | Method | Expected | Fail action |
|---|---|---|---|
| Input clamp diodes idle | DMM diode-check across Dclamp+ (and Dclamp−) with power on | Reverse-biased — diode-check reads open/OL in the blocking direction; leakage < 1µA | Reads a forward drop (~0.6V) or conducts at idle: clamp diode is in backwards |
| TVS1 at idle | DMM DC across input jack tip–sleeve, nothing plugged in | 0V (TVS not conducting) | Any standing voltage: wiring fault at the jack or a shorted TVS |
| Overload clamp | Apply 20Vpp 1kHz to the input (**careful — this is a deliberate overload**), probe U1(+) | Waveform clamped, U1(+) never exceeds ±16V (design clamps at ~±15.7V) | Exceeds ±16V: check TVS1 (both zeners / correct bidirectional part) and the 1N4148 clamp-pair orientation |

> **Two protectors, two nodes.** TVS1 sits at the *jack* (before C_in) and catches the nanosecond ESD strike — the kind you get hot-plugging a cable while other gear is running. The 1N4148 clamp pair sits at the *U1(+) pin* (after C_in) and hard-limits slow DC overloads that make it through C_in. They are not redundant; they protect different points in the path. In the SPICE model TVS1 is two BZX84C15L zeners back-to-back, which is exactly how a bidirectional SMBJ15CA behaves: clamp = one zener breakdown (15V) plus one forward drop (~0.7V) ≈ ±15.7V. (See parts-spec: TVS1, D_clamp+, D_clamp−, C_in.)

---

## Stage 6 — Full signal chain verification

Corresponds to SPICE **Stage 6** integration: re-run the Stage 1 numbers on the complete chain (`recov_gain` 200–228×, `hpf_m3db` 250–320Hz, `off_u3` ≤ 10mV, `osc_ratio` < 1.05).

| Test | Method | Expected | Fail action |
|---|---|---|---|
| Recovery gain | Apply −40dBu to input, probe U2 output | ~46dB gain (≈214×; ~100mV in → ~10V out at U2) | Low: check Ri (470Ω) / Rf (100kΩ) ratio and Rbias (100kΩ, not 470Ω). Very high or oscillating: check feedback wiring and R2/R7 output isolation resistors |
| HPF corner | Sweep generator, probe the wet signal at U2 output / HPF node | −3dB at ~284Hz (accept 250–320Hz) | Wrong corner: check C4 (100nF) and R6 (5.6kΩ exactly — 4.7k → 338Hz, 6.8k → 234Hz) |
| Output DC offset | DMM DC at J2 output jack | < ±10mV | Check U3 output and C3 (no DC leaking from the tank into U2) |
| Reverb sound check | Guitar / audio source in, monitor the output | Clear spring-reverb tail, dry signal audible and clean | No wet signal: check tank RCA connections and tank/transformer orientation; check polarity (see phase note below) |

### Phase note for builder

If the reverb sounds hollow, thin, or "phasey" with the Mix pot at 50/50, the tank output is out of phase with the dry signal. Spring-tank polarity varies between Accutronics batches — this is normal and expected on some units. **Fix: swap the two wires on the tank OUTPUT connector (the 2550Ω side).** It's a 10-second wire swap at the RCA / Molex connector — no schematic change. (parts-spec Build Note 6.)

### Noise floor check

With the input shorted (no cable plugged in), the output should be quiet down into your monitoring chain's own noise floor.

- **Audible 60Hz hum** usually means a ground loop. Flip the ground-lift switch on the rear panel (it inserts a 10Ω + 100nF network in place of the direct audio-ground-to-chassis tie, breaking the loop without lifting safety earth). If hum changes with the tank position, also check transformer-to-tank orientation (toroid axis perpendicular to the spring axis) and that the tank output shield is grounded at the U2 end only.
- **Hiss above your monitoring floor** usually means the C5–C8 decoupling caps (100nF film) are not close enough to the op-amp supply pins — they must be within ~1" of the IC — or a ground path back to the star ground is missing. At U2's 214× recovery gain the circuit is unforgiving about supply decoupling and grounding.

---

## Orientation quick-reference

Three things are directional and produce *no reverb* (or wrong behavior) if reversed. Verify all three:

| Part | Correct orientation | Symptom if reversed |
|---|---|---|
| **R1** | After C_in: from U1(+) pin to GND (shunt) | U1 output slams to a rail; no/weak dry signal (parts-spec R1) |
| **Driver transformer (REB3S)** | Primary (L1) → Q1 collector; 8Ω secondary (L2) → tank input | No reverb — secondary can't drive the collector node |
| **Spring tank** | 8Ω input side fed from the transformer; 2550Ω output side to U2. Mount **open-side DOWN, horizontal** | No/wrong reverb; springs drift over time if mounted open-side up (parts-spec Build Note 3) |
