# Ghost Spring Reverb — Builder Verification Guide

This guide is for the person assembling the physical unit on a bench. Each stage of assembly has a small set of measurements to make **before** moving to the next. These measurements correspond directly to the SPICE simulations in [`test-assertions.md`](./test-assertions.md) that verified the design: if the simulation passed and your bench measurement lands in the same window, that stage is correct and you can move on. If a bench number is out of range, the "Fail action" column tells you the most likely cause — fix it before adding more parts, exactly the way you'd keep a test suite green before writing the next feature.

The assembly order below (visual → power → driver → transformer → input protection → full chain) is the order it's easiest to build and test on a bench. It is **not** the same numbering as the SPICE build stages, which replace one idealized block at a time. The cross-reference is noted under each section so you can find the matching simulation. Component values and the reason behind each are in [`parts-spec.md`](../parts-spec.md) — read the rationale before substituting anything.

**Equipment needed**

| Tool | Use |
|---|---|
| DMM (digital multimeter) | DC voltages, resistance, diode-check, leakage |
| Oscilloscope, 2-channel preferred | Waveforms, clipping, phase, resonant peak |
| Signal generator or audio interface | Sine sweeps and fixed-tone test signals |
| ±15V bench supply (current-limited) | Powers the circuit before the on-board PSU stage is built. Set the current limit to ~100mA for the first power-on of each stage — a wiring fault then trips the limit instead of cooking a part |
| Series bulb (lamp) limiter | **Required for the first mains power-on (Stage 6 only).** A 40–60W incandescent bulb in series with the mains. A dead short downstream lights the bulb fully and drops the voltage across the transformer, so a build error can't blow the fuse or the bridge. See Stage 6 |
| IR thermometer or thermocouple (optional) | Spot-checking Q1 and regulator tab temperatures — see the thermal notes in Stages 3 and 6 |

> **Read this before any power-on.** For every stage on the bench supply (Stages 2–5), bring the supply up with the current limit set low (~100mA) and watch the meter as you switch on. The circuit draws roughly 30–50mA idle. If the supply jumps straight to its current limit, **switch off immediately** — you have a short or a backwards part. Do not "push through" a current-limited bring-up.

> **Safety — PSU filter caps hold charge.** Once the on-board power supply (C11/C12, 2200µF) is built, those caps hold ~21V after power-off. The 10kΩ bleed resistors (R_bleed1/2) drain them, but it takes time: τ = 10kΩ × 2200µF = 22s, so ~110s to reach <2V. **Wait at least 1–2 minutes after switching off — or measure across the caps with the DMM — before touching the supply.** Until the PSU stage exists you are on the bench supply, which has no stored charge, but build the habit now.

---

## Pot positions for every test

The SPICE assertions were run with the controls in defined positions. Set the pots the same way before each bench test or your numbers will not match the simulation. If a pot isn't fitted yet at a given stage, ignore its row.

| Control | Ref / Value | Stage 3 (driver bias + signal) | Stage 4 (resonance) | Stage 6 (full chain) |
|---|---|---|---|---|
| **Dwell** | RV1 10kΩ linear | **Fully CW (max drive)** — gives the largest, easiest-to-see collector swing and the worst-case clipping check | **Fully CW** — you want maximum drive into the tank so the resonant peak is unambiguous | **~50% (noon)** for the sound check; **fully CW** when verifying recovery gain / headroom |
| **Mix** | RV2 100kΩ audio | n/a | n/a | **Recovery-gain / HPF tests: fully CW (full wet)** so the dry path doesn't sum in and skew the reading. **Sound + phase check: 50/50 (noon).** **Output-DC-offset test: any position — DC offset is independent of mix** |
| **Tone** | RV3 100kΩ audio | n/a | n/a | **Fully CW (full treble/open)** for gain and HPF measurements so the wet path isn't rolled off; set to taste for listening |
| **Bright cap** | C_bright 47pF (not a control) | — | — | Fixed part across RV2; nothing to set. Its effect only appears with Mix near full-wet, which is why the gain test uses that position |

> **Why full-wet for the gain and HPF tests.** The recovery gain (`recov_gain`) and HPF corner (`hpf_m3db`) are properties of the U2 → C4/R6 path alone. With the Mix pot anywhere but full wet, the dry signal from U1 sums into the same node and you measure a blend, not the wet path. Probe *at U2's output* (and after C4/R6 for the HPF) rather than at the output jack to isolate the wet path regardless of Mix setting — but keeping Mix full-wet also lets you confirm the result end-to-end at J2.

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

> **Q1 temperature — warm is normal, hot is not.** At the design bias point (Ic ≈ 16–18mA, Vce ≈ 13.8V) Q1 dissipates ≈ 13.8V × 18mA ≈ **0.25W**. A TO-126 with the small clip-on heatsink fitted (parts-spec) will settle around **40–50°C** — warm to the touch, you can hold a finger on it indefinitely. This is correct. **What is NOT normal:**
> - **Too hot to touch (>60°C) and climbing** → thermal runaway or a bias fault. Power down. Re-check R5 (68Ω emitter degeneration — if it's open or a wrong high value the current isn't limited), then the R3b/R4 divider, then confirm C2 isn't shorted (a shorted emitter bypass cap removes the DC drop across R5).
> - **Ve drifting upward over the first minute** as the part warms is a small, expected settle (a few mV). Ve *running away* upward is the thermal-runaway signature — R5's degeneration should arrest it. If it doesn't, R5 is suspect.
> - **Stone cold with Vc pinned at +15V** → Q1 isn't conducting at all (open device, reversed device, or broken bias chain), not a thermal issue. See the bias table above.
>
> Fit the BD139 heatsink before running this stage for any length of time — it holds the junction below 50°C and stops the long-term hFE drift that would walk the bias point over the life of the unit. **Check the TO-126 tab is not shorting to anything:** on the BD139 the metal tab is the collector, so it sits near +15V — if it touches the chassis or a grounded heatsink without isolation you short the collector. Use an isolating pad if the heatsink is grounded.

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

## Stage 6 — Power supply rails

Corresponds to SPICE **Stage 5** (`stage_05_psu.asc`): the `op` (settled-DC) run measures the regulated rails (`rail_pos` 14.85–15.15V, `rail_neg` −15.15 to −14.85V), and the `tran` run measures post-regulator ripple over a 100–120ms window (`ripple_pos` < 10mVpp, `ripple_neg` < 10mVpp). This is the real ±15V linear supply that replaces the bench rails used through Stages 1–5: T1 (15‑0‑15VAC) → F2/F3 polyfuses → BR1 bridge → C11/C12 2200µF bulk + 10k bleed → U4 LM7815 / U5 LM7915 → C13/C14 100µF + C17/C18 100nF.

> **Mains warning.** This stage carries line voltage on the T1 primary. Verify all primary-side wiring, fusing (F1), and earth bonding before first power-on, and keep fingers clear of the primary and the bridge while live. All DMM probing below is on the *secondary/DC* side.

### First mains power-on — do this exactly once, in this order

This is the only stage that has ever seen line voltage. Treat the very first switch-on as a deliberate, slow ceremony. Do not skip the bulb limiter.

**Before applying any power (unit unplugged):**

1. **Verify the T1 primary wiring.** The F-219X has two 115VAC primaries. For 120VAC mains they go in **parallel** (observe the phasing dots — both starts together, both finishes together). Series wiring makes it a 230VAC transformer and you'll get ~half the secondary voltage. (parts-spec T1.)
2. **Verify the T1 secondary wiring.** The two 15VAC secondaries go in **series** to make 15-0-15: one end of winding A ties to one end of winding B, and *that junction is your 0V/GND center tap*. The two outer ends go to BR1's AC pins. Parallel secondaries give one ~20V rail and **no negative rail** — the LM7915 and every negative op-amp pin will be dead.
3. **Confirm the mains-side parts are in:** F1 fuse fitted (500mA slow-blow), NTC1 inrush limiter in series after the fuse, MOV1 across L–N, and **safety earth bonded to the chassis** with a star washer. The earth bond is not optional.
4. **DMM continuity, power off:** confirm no short from either DC rail to GND, and no short between +rail and −rail. Confirm the LM7815 and LM7915 tabs are *isolated from the chassis* by their mica pads — measure tab-to-chassis, expect open. (The 7815 tab is +15V, the 7915 tab is −15V; a missing mica pad on either shorts a rail to chassis, and if both are grounded you short +15V to −15V through the chassis.)
5. **Disconnect the DC rails from the rest of the board** for the very first PSU bring-up if you can (unplug the Molex power feed to the signal board). Prove the supply alone before you let it feed everything.

**Bulb-limiter bring-up:**

6. Put the **40–60W incandescent bulb in series with the mains** (in series with Live, ahead of the IEC inlet). Plug in, switch on, and **watch the bulb.**
   - **Bulb flashes bright then dims to a dim glow / out** → normal. That's the inrush charging C11/C12, then the steady ~3VA load. Good.
   - **Bulb stays fully lit** → a hard short downstream (bridge in backwards, a rail shorted to ground, a regulator tab shorted to chassis). Switch off. The bulb just saved your bridge and fuse — find the short before trying again.
7. With the bulb still in series, measure the unregulated bus and both rails per the table below. They'll read a little low because the bulb drops some voltage under load — that's expected. You're confirming polarity and that both regulators produce roughly ±15V, not final precision.
8. **Remove the bulb limiter, plug straight into mains, switch on.** Re-measure the rails — now they should land in the 14.85–15.15V windows.
9. **Reconnect the signal board** (Molex power feed) and re-check the rails under real load. A rail that was fine unloaded but sags now points to a regulator dropping out (check the unregulated bus headroom) or a downstream short pulling a polyfuse (F2/F3) toward trip.

**What to look, listen, and smell for during the first minute live:**

- **Smell:** any hot-varnish, scorched-resin, or "electrical" smell → switch off immediately. Usually a backwards electrolytic (C11/C12/C13/C14) or a regulator with no heatsink shorting.
- **Look:** any electrolytic bulging or venting, any discoloration at a regulator or R_bleed resistor.
- **Touch (after the rails check good):** the regulator tabs will get **warm** — see the thermal note below. The R_bleed resistors run barely-warm (44mW). Anything *hot* in the first minute is a fault.
- **Listen:** a faint mechanical hum from the toroid is normal; a loud buzz or a rising whine is not.

> **Regulator heatsinking — they run warm, and they must be heatsinked and isolated.** Each regulator drops (≈20.4V bus − 15V) ≈ **5–6V** at the unit's ~30–50mA load, so it dissipates roughly **0.15–0.3W** at idle. That is modest, but the LM78xx/79xx will still climb toward 60–70°C *without* a heatsink in a closed 2U chassis, and they thermally throttle (rail sags) before they fault. **Fit the TO-220 heatsink + mica isolation pad + thermal compound on both** (parts-spec Heatsinks). The mica pad is mandatory for the isolation reason in step 4 above, not just for heat. Expected tab temperature with heatsink fitted: **warm, ~45–55°C — comfortable to keep a finger on.** If a regulator is too hot to touch, check (a) it actually has its heatsink and compound, (b) the load isn't excessive (downstream short edging the polyfuse), and (c) the unregulated bus isn't abnormally high.

> **In SPICE, the `op` rail check is a *settled-transient* average, not a true `.op`.** A rectifier-plus-filter supply has no meaningful DC operating point — the solver freezes the SINE sources at their t=0 value (0V), so the bridge sees no drive and the caps never charge. The generator therefore runs a 150ms transient and averages V(+15V)/V(−15V) over 100–120ms. That average is exactly the steady DC a bench DMM reads.

| Test | Method | SPICE assertion | Expected | Fail action |
|---|---|---|---|---|
| Unregulated bus | DMM DC: pos_rect to GND, then neg_rect to GND (across C11 / C12) | `unreg_pos` / `unreg_neg` ≈ ±20.4V (avg) | ~+19 to +22V / −19 to −22V (peak ≈ 21.2V minus 2 diode drops, held up by the bulk cap) | Near 0V or only ~half: a bridge diode (DBR1a–d) is open/backwards, or a polyfuse (F2/F3) is open. Big AC component: C11/C12 (2200µF) open or wrong polarity |
| +15V rail | DMM DC at U4 (LM7815) output / +15V rail | `rail_pos` 14.85–15.15V | +14.85 to +15.15V | Low (~+2V below bus): U4 dropout — bus too low, check unregulated bus first. Equal to bus: U4 shorted IN→OUT. 0V: U4 in backwards or no output cap |
| −15V rail | DMM DC at U5 (LM7915) output / −15V rail | `rail_neg` −15.15 to −14.85V | −14.85 to −15.15V | Same checks as +15V but for U5 (LM7915) — note the 7915 pinout differs from the 7815, a common build error |
| +15V ripple | AC-couple scope on +15V rail, 60Hz+ timebase | `ripple_pos` < 10mVpp | < 10mVpp (essentially flat; the reg rejects the bus ripple) | Visible 120Hz sawtooth >10mVpp: C13 (100µF) missing, or the regulator is dropping out on ripple troughs (bus headroom too low — check C11) |
| −15V ripple | AC-couple scope on −15V rail | `ripple_neg` < 10mVpp | < 10mVpp | Same as +15V but C14 / U5 |
| HF bypass present | Visual / continuity: C17, C18 (100nF) directly at each regulator output pin to GND | n/a (models PSRR floor) | Fitted within ~1" of the reg pins | Missing: regulator can oscillate or pass HF trash; add the 100nF |

> **What the simulated 0mVpp ripple means.** The behavioural 78xx/79xx model holds its output dead-flat at 15.0V as long as the unregulated bus stays above the ~17V dropout point — which it does (bus ≈ 20.4V with ≈21mVpp of its own ripple). So the *post*-regulator ripple computes as ~0, demonstrating the rail rejects the upstream ripple. On the bench you will see a few mV of real ripple/noise (finite PSRR, layout, load steps); the <10mVpp budget is what matters. The unregulated-bus ripple at C11/C12 (`unreg_pos_pp` ≈ 21mVpp in the model, far larger in reality under load) is the honest indicator that the rectifier and bulk caps are doing their job — probe *there* to confirm the supply is alive before trusting the flat regulated rails.

> **Bleed resistors.** R_bleed1/R_bleed2 (10kΩ across C11/C12) discharge the 2200µF bulk caps after power-down — at ~20V they hold ~40mA·s of charge. With power off, the rails should sag to near 0V within a couple of seconds; if a rail stays charged, its bleed resistor is open (shock/measurement hazard on a big cap).

---

## Stage 7 — Full-chain integration verification

This is the **integration stage**: it adds *no new parts*. Corresponds to SPICE **Stage 6** (`stage_06_full.asc` / `gen_stage6_full.py`), which carries the complete real circuit — the ±15V linear PSU, BD139 driver, REB3S transformer, spring tank, input protection, and all three op-amp stages — byte-for-byte, and **re-runs the original Stage 1 MVP signal-path assertions against the whole thing**. The point is a clean regression gate: if any baseline number drifted as the real supply/driver/protection were added, it surfaces here. Everything below is the verified bench equivalent of the simulated assertion suite.

> **Bring-up order for the fully assembled unit.** Do the Stage 6 PSU first-mains-power-on ceremony (bulb limiter, rails verified) *with the signal board disconnected*, then reconnect the board and power up. Set the pots per the **Pot positions for every test** table at the top of this guide. Confirm the power LED lights (it's wired from +15V through 10kΩ — ~1.2mA, deliberately dim; a dark LED with good rails just means a reversed LED or wrong resistor, not a supply fault). Then work down the table below. Keep a hand near the switch for the first powered minute and watch/smell for the fault signs listed in the Stage 6 power-on section.

**Verified simulation results** (all pass; three analysis variants, one active at a time — regenerate with `gen_stage6_full.py {op|ac|tran}`):

| Assertion | Variant | Measured | Pass band | Result |
|---|---|---|---|---|
| `off_u1` | op | ≈0V (+0.8fV) | ±10mV | ✅ |
| `off_u2` | op | +0.47mV | ±10mV | ✅ |
| `off_u3` | op | −0.35µV (≈0V) | ±10mV | ✅ |
| `q1_ve` | op | 1.092V | 1.0–1.4V | ✅ |
| `recov_gain` | ac | 46.59dB = 213.6× @1kHz | 200–228× | ✅ |
| `hpf_m3db` | ac | 312Hz | 250–320Hz | ✅ |
| `vout_pk` | tran | 1.16V | < 14V | ✅ |
| `osc_ratio` | tran | 0.9998 | < 1.05 | ✅ |

> **Why three variants, and why the windows are where they are.** The real PSU is *degenerate* at any DC operating point (the 60Hz transformer sources freeze at 0V, so the rectifier sees no drive and the rails read 0V). So:
> - **op** (DC bias) runs a 200ms transient with the *signal source killed* and reads the settled DC at the 190–200ms tail. The 200ms run matters — the recovery stage reads residual tank DC through C3/Rbias into a 214× gain, and the high-L tank (L_tank_out 2H) takes >100ms to bleed its start-up transient (`off_u2` reads ~72mV at 20ms but settles to <0.5mV by 200ms).
> - **ac** (gain + HPF corner) powers the op-amps from *ideal ±15V bench rails* and omits the rectifier network — small-signal behaviour of the signal path is independent of how the rails are made, and a `.ac` would otherwise linearize about the dead 0V DC point and leave the op-amps unpowered. The HPF corner is measured as the **R6/C4 transfer V(hpf_out)/V(u2_out)** to isolate it from the tank's resonant "drip" shaping (measuring `hpf_out` alone would catch the ~2kHz tank peak, not the 284Hz design corner).
> - **tran** (peak + stability) runs 100ms with the 100mVpk 1kHz stimulus; the no-oscillation ratio compares 90–100ms vs **40–50ms** (both past the ~40ms start-up settle, so the ratio measures *growth*, not the charge-up transient).

| Test | Method | Expected | Fail action |
|---|---|---|---|
| Recovery gain | Apply −40dBu to input, probe U2 output | ~46.6dB gain (≈213.6×; ~100mV in → ~10V out at U2) | Low: check Ri (470Ω) / Rf (100kΩ) ratio and Rbias (100kΩ, not 470Ω). Very high or oscillating: check feedback wiring and R2/R7 output isolation resistors |
| HPF corner | Sweep generator, probe wet at U2 output then after C4/R6 (ratio = the HPF transfer) | −3dB at ~312Hz (design 284Hz; accept 250–320Hz) | Wrong corner: check C4 (100nF) and R6 (5.6kΩ exactly — 4.7k → 338Hz, 6.8k → 234Hz) |
| Output DC offset | DMM DC at J2 output jack | < ±10mV (sim ≈ 0V) | Check U3 output and C3 (no DC leaking from the tank into U2) |
| Q1 emitter bias | DMM DC at Q1 emitter / R5 top | ≈1.09V (1.0–1.4V) — unchanged under the real regulated rails | Bias shifted: check R3b/R4 divider and R5 (68Ω); confirm the +15V rail first (Stage 6 above) |
| Reverb sound check | Guitar / audio source in, monitor the output | Clear spring-reverb tail, dry signal audible and clean | No wet signal: check tank RCA connections and tank/transformer orientation; check polarity (see phase note below) |

### Phase note for builder

If the reverb sounds hollow, thin, or "phasey" with the Mix pot at 50/50, the tank output is out of phase with the dry signal. Spring-tank polarity varies between Accutronics batches — this is normal and expected on some units. **Fix: swap the two wires on the tank OUTPUT connector (the 2550Ω side).** It's a 10-second wire swap at the RCA / Molex connector — no schematic change. (parts-spec Build Note 6.)

### Noise floor check

With the input shorted (no cable plugged in), the output should be quiet down into your monitoring chain's own noise floor.

- **Audible 60Hz hum** usually means a ground loop. Flip the ground-lift switch on the rear panel (it inserts a 10Ω + 100nF network in place of the direct audio-ground-to-chassis tie, breaking the loop without lifting safety earth). If hum changes with the tank position, also check transformer-to-tank orientation (toroid axis perpendicular to the spring axis) and that the tank output shield is grounded at the U2 end only.
- **Hiss above your monitoring floor** usually means the C5–C8 decoupling caps (100nF film) are not close enough to the op-amp supply pins — they must be within ~1" of the IC — or a ground path back to the star ground is missing. At U2's 214× recovery gain the circuit is unforgiving about supply decoupling and grounding.

---

## Orientation, polarity & pinout quick-reference

These are the parts that are directional and cost real bench time — or real parts — if they go in wrong. Verify every row before first power-on of the relevant stage.

### Directional — wrong = no reverb / wrong behavior

| Part | Correct orientation | Symptom if reversed |
|---|---|---|
| **R1** | After C_in: from U1(+) pin to GND (shunt) | U1 output slams to a rail; no/weak dry signal (parts-spec R1) |
| **Driver transformer (T2 / REB3S)** | Primary (L1) → Q1 collector; 8Ω secondary (L2) → tank input | No reverb — secondary can't drive the collector node |
| **Spring tank (RT1 / 9AB3C1B)** | 8Ω input side fed from the transformer; 2550Ω output side to U2. Mount **open-side DOWN, horizontal** | No/wrong reverb; springs drift over time if mounted open-side up (parts-spec Build Note 3) |
| **Tank output phase** | Either way works electrically; phase may need swapping vs the dry path | "Phasey"/hollow at 50/50 Mix — swap the 2550Ω-side wires (Phase note, Stage 7) |

### Polarity & pinout — wrong = a destroyed part or a dead rail

| Part | Watch out for | Symptom / consequence if wrong |
|---|---|---|
| **LM7815 vs LM7915** | **The 7915 pinout is NOT a mirror of the 7815.** 7815 (TO-220, tab = OUT/+15V): pin1=IN, pin2=GND, pin3=OUT. 7915 (tab = IN/−15V): pin1=GND, pin2=IN(−), pin3=OUT(−15V). Do not assume symmetry | Dead or wrong-polarity negative rail; part may overheat. Single most common PSU build error |
| **Electrolytics C11/C12 (2200µF)** | C11 sits on the **+** unregulated bus, C12 on the **−** bus. Get the can polarity right per rail | Backwards electrolytic on a 20V bus vents/explodes within seconds of power-on. This is why first power-on uses the bulb limiter |
| **Electrolytics C2, C13/C14, C15/C16** | C2 (+ toward Q1 emitter), C13/C15 on +15V, C14/C16 on −15V | Reversed cap heats, leaks, then vents |
| **Bridge BR1 (W04G)** | The two ~ pins go to the transformer AC; **+** and **−** go to C11/C12. Don't swap AC pins for DC pins | Near-0V or half-wave bus; possible blown bridge if it shorts the transformer |
| **D3, D_clamp+, D_clamp− (1N4148)** | Cathode = banded end. D3: anode→collector, cathode→+15V. D_clamp+: anode→U1(+), cathode→+15V. D_clamp−: anode→−15V, cathode→U1(+) | A reversed clamp reads ~0.6V forward at idle (Stage 5 diode-check catches it) and clamps the wrong polarity, leaving U1 unprotected |
| **TVS1 (SMBJ15CA)** | Bidirectional — orientation doesn't matter electrically, but verify it's the **CA** (bidirectional) part, not a unidirectional SMBJ15A | A unidirectional TVS only clamps one polarity at the jack |
| **Op-amps U1–U3 (OPA2134)** | Pin-1 notch/dot toward the board's pin-1 mark | Backwards IC = supply pins swapped, op-amp pulls hard or cooks |
| **Q1 (BD139)** | **BD139 standard pinout — printed/marked face toward you, leads pointing down: pin1 = Emitter, pin2 = Collector, pin3 = Base.** The metal tab is also the Collector (internally tied to pin 2). This is **not** the EBC/“flat-side” order of common TO-92 small-signal parts — confirm against the BD139 datasheet before soldering | Reversed Q1 = no bias, stone-cold device with the collector pinned at +15V. Easy to mis-wire by assuming a 2N-series pin order |
| **Regulator tabs vs chassis** | Both LM78xx/79xx tabs **must** be isolated from the chassis with mica pads (7815 tab=+15V, 7915 tab=−15V) | No pad = rail shorted to chassis; both unpadded = +15V shorted to −15V through the chassis |
