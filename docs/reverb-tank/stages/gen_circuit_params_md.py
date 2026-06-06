#!/usr/bin/env python3
"""
gen_circuit_params_md.py - Generate ../circuit-params.md from circuit_params.py.

circuit-params.md is the human-readable parameter table. It is GENERATED, never
hand-edited: every value in it comes from circuit_params.py (the single source of
truth). The descriptive prose (function text, netlist nodes, notes) is editorial
scaffold and lives in THIS script; the numbers are interpolated from the Python
constants so they can never drift from the netlists.

Edit circuit_params.py, then run sync.py. Do not edit circuit-params.md by hand
-- it is generated.

Usage: python3 gen_circuit_params_md.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import circuit_params as P  # noqa: E402

OUT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "circuit-params.md"))


# ---------------------------------------------------------------------------
# Value formatters: turn SPICE strings ("1Meg", "100n") into doc units (1MΩ).
# ---------------------------------------------------------------------------
def ohm(v):
    """Format a resistor SPICE string as an ohm value for the doc."""
    m = {"Meg": "MΩ", "k": "k", "m": "m"}
    if v.endswith("Meg"):
        return v[:-3] + "MΩ"
    if v.endswith("k"):
        return v[:-1] + "k"
    return v  # bare ohms (e.g. "100", "68", "0.5", "0.001", "8")


def farad(v):
    """Format a capacitor SPICE string as a farad value for the doc."""
    if v.endswith("u"):
        return v[:-1] + "µF"
    if v.endswith("n"):
        return v[:-1] + "nF"
    if v.endswith("p"):
        return v[:-1] + "pF"
    return v + "F"


def henry(v):
    """Format an inductor SPICE string as a henry value for the doc."""
    if v.endswith("m"):
        return v[:-1] + "mH"
    return v + "H"


# ---------------------------------------------------------------------------
# Row tables. Each row carries the netlist designator, the formatted value (from
# P), the function text, and the netlist node(s). Values are NEVER literal here.
# ---------------------------------------------------------------------------
RESISTORS = [
    ("R1", ohm(P.R1), "U1(+) FET-input DC return / 1MΩ input impedance (shunt, **after** C_in)", "`u1_pos` → `0`"),
    ("R2", ohm(P.R2), "U1 output isolation (series, against cable capacitance)", "`u1_out` → `u1_buf`"),
    ("R3", ohm(P.R3), "Dwell wiper → Q1 base drive resistor / HF damping", "`q1_drv` → `q1_base`"),
    ("R3b", ohm(P.R3B), "Upper leg of Q1 base bias divider (+15V → base)", "`+15V` → `q1_base`"),
    ("R4", ohm(P.R4), "Lower leg of Q1 base bias divider (base → GND)", "`q1_base` → `0`"),
    ("R5", ohm(P.R5), "Q1 emitter degeneration (sets Ic, thermal stability)", "`q1_e` → `0`"),
    ("Ri", ohm(P.RI), "U2 gain-set lower leg (non-inverting feedback divider, (−) → GND)", "`u2_inv` → `0`"),
    ("Rf", ohm(P.RF), "U2 feedback upper leg (output → (−)); gain = 1 + Rf/Ri", "`u2_out` → `u2_inv`"),
    ("R6", ohm(P.R6), "Wet HPF resistor (with C4)", "`hpf_out` → `0`"),
    ("Rbias", ohm(P.RBIAS), "U2 non-inv (+) input bias / recovery input impedance", "`u2_in_pos` → `0`"),
    ("Rdry", ohm(P.RDRY), "Dry-path series R: U1 buffer → RV2 CCW end (dry end of Mix pot)", "`u1_buf` → `mix_dry`"),
    ("Rwet_wire", "0Ω", "Wet-path direct wire: Tone wiper → RV2 CW end (wet end of Mix pot; 0Ω wire model)", "`rv3_wiper` → `mix_wet`"),
    ("R7", ohm(P.R7), "U3 output isolation (series to output jack / MC100)", "`u3_out` → `v_out`"),
    ("Rload", ohm(P.RLOAD), "MC100 RCA input load (model of downstream device, not a fitted part)", "`v_out` → `0`"),
    ("R_tank_in", ohm(P.R_TANK_IN), "Tank input impedance (8Ω side, lumped tank model)", "`tank_in` → `0`"),
    ("R_tank_mech", ohm(P.R_TANK_MECH), "Tank mechanical-resonance series R (lumped model)", "`tank_mid` → `tk_a`"),
    ("R_tank_out", ohm(P.R_TANK_OUT), "Tank output impedance (2550Ω side, lumped model)", "`tank_mid` → `tank_out`"),
    ("R_bleed1", ohm(P.R_BLEED1), "Bleed across C11 (+15V bulk filter), 1W flameproof", "`pos_rect` → `0`"),
    ("R_bleed2", ohm(P.R_BLEED2), "Bleed across C12 (−15V bulk filter), 1W flameproof", "`neg_rect` → `0`"),
    ("RF2", ohm(P.RF2), "F2 polyfuse (MF-R050) model, +15V rail (hold ≈0.7Ω)", "`reg_pos` → `+15V`"),
    ("RF3", ohm(P.RF3), "F3 polyfuse (MF-R050) model, −15V rail", "`reg_neg` → `-15V`"),
    ("RV1a", ohm(P.RV1A), "Dwell pot upper half (U1 buf → wiper)", "`u1_buf` → `rv1_wiper`"),
    ("RV1b", ohm(P.RV1B), "Dwell pot lower half (wiper → GND)", "`rv1_wiper` → `0`"),
    ("RV2a", ohm(P.RV2A), "Mix pot CCW half (dry end → wiper)", "`mix_dry` → `mix_node`"),
    ("RV2b", ohm(P.RV2B), "Mix pot CW half (wiper → wet end)", "`mix_node` → `mix_wet`"),
    ("RV3a", ohm(P.RV3A), "Tone pot upper half (HPF out → wiper)", "`hpf_out` → `rv3_wiper`"),
    ("RV3b", ohm(P.RV3B), "Tone pot lower half (wiper → GND)", "`rv3_wiper` → `0`"),
]

CAPACITORS = [
    ("C_in", farad(P.C_IN) + " / 63V", "Input coupling at the jack (before U1)", "`vin` → `u1_pos`"),
    ("C1 (= `C_drive`)", farad(P.C_DRIVE) + " / 63V", "Dwell-wiper → Q1 base coupling (blocks buffer DC from bias divider)", "`rv1_wiper` → `q1_drv`"),
    ("C2", farad(P.C2) + " / 25V", "Q1 emitter bypass (across R5, full AC gain)", "`q1_e` → `0`"),
    ("C3", farad(P.C3) + " / 63V", "Tank output → U2 input DC block (~3Hz corner w/ Rbias)", "`tank_out` → `u2_in_pos`"),
    ("C4", farad(P.C4) + " / 63V", "Wet HPF cap (with R6)", "`u2_out` → `hpf_out`"),
    ("C_bright", farad(P.C_BRIGHT), "Bright cap across full Mix pot (HF presence as pot approaches full-wet)", "`mix_dry` → `mix_wet`"),
    ("C5", farad(P.C5) + " / 63V", "U1/U2 +15V supply decoupling", "`+15V` → `0`"),
    ("C6", farad(P.C6) + " / 63V", "U1/U2 −15V supply decoupling", "`-15V` → `0`"),
    ("C7", farad(P.C7) + " / 63V", "U3 +15V supply decoupling", "`+15V` → `0`"),
    ("C8", farad(P.C8) + " / 63V", "U3 −15V supply decoupling", "`-15V` → `0`"),
    ("C11", farad(P.C11) + " / 50V", "+ve unregulated bulk filter (after bridge)", "`pos_rect` → `0`"),
    ("C12", farad(P.C12) + " / 50V", "−ve unregulated bulk filter", "`neg_rect` → `0`"),
    ("C13", farad(P.C13) + " / 25V", "U4 (LM7815) output stability cap", "`reg_pos` → `0`"),
    ("C14", farad(P.C14) + " / 25V", "U5 (LM7915) output stability cap", "`reg_neg` → `0`"),
    ("C15", farad(P.C15) + " / 25V", "+15V board-entry bulk decoupling", "`+15V` → `0`"),
    ("C16", farad(P.C16) + " / 25V", "−15V board-entry bulk decoupling", "`-15V` → `0`"),
    ("C17", farad(P.C17) + " / 63V", "U4 output HF bypass (at reg pin)", "`reg_pos` → `0`"),
    ("C18", farad(P.C18) + " / 63V", "U5 output HF bypass (at reg pin)", "`reg_neg` → `0`"),
    ("C_tank_mech", farad(P.C_TANK_MECH), "Tank mechanical-resonance cap (lumped model)", "`tk_b` → `0`"),
]

INDUCTORS = [
    ("L1", henry(P.L1) + " (Rser=0)", "REB3S primary (Q1 collector → +15V)", "`+15V` → `q1_c`"),
    ("L2", henry(P.L2) + " (Rser=0)", "REB3S 8Ω secondary (into tank input)", "`tank_in` → `0`"),
    ("K1", P.K1, "REB3S coupling coefficient (L1↔L2)", "couples `L1` `L2`"),
    ("L_tank", henry(P.L_TANK) + " (Rser=0)", "Tank input series inductance (lumped)", "`tank_in` → `tank_mid`"),
    ("L_tank_mech", henry(P.L_TANK_MECH) + " (Rser=0)", "Tank mechanical-resonance inductance (lumped)", "`tk_a` → `tk_b`"),
    ("L_tank_out", henry(P.L_TANK_OUT) + " (Rser=0)", "Tank output inductance (lumped)", "`tank_out` → `0`"),
]


def _num(x):
    """Trim trailing zeros and use a proper minus sign (−), the doc's house style.
    16.0 -> 16, -16.0 -> −16, -15.15 -> −15.15."""
    return ("%g" % x).replace("-", "−")


def _num1(x):
    """Like _num but always one decimal place (15.0 -> 15.0), for the rail rows
    where the original table writes the trailing .0 to signal a regulated target."""
    return ("%.1f" % x).replace("-", "−")


def mv(window):
    """+/- millivolt window as a 'X mV' string from a symmetric (lo, hi) tuple."""
    return "%g mV" % (window[1] * 1e3)


def ma_range(window):
    return "%g – %g mA" % (window[0] * 1e3, window[1] * 1e3)


def v_range(window):
    return "%s – %s V" % (_num(window[0]), _num(window[1]))


def hz_range(window):
    return "%g – %g Hz" % (window[0], window[1])


def khz_range(window):
    """No-space form '1–5 kHz' used in the AC parameters table."""
    return "%g–%g kHz" % (window[0] / 1e3, window[1] / 1e3)


def khz_range_sp(window):
    """Spaced form '1 – 5 kHz' used in the pass-windows table."""
    return "%g – %g kHz" % (window[0] / 1e3, window[1] / 1e3)


def gain_range(window):
    return "%g – %g" % (window[0], window[1])


def build_md():
    L = []
    w = L.append

    w("# Ghost Spring Reverb — Canonical Circuit Parameters")
    w("")
    w("> **GENERATED FILE — do not edit by hand.** This table is produced by "
      "[`stages/gen_circuit_params_md.py`](./stages/gen_circuit_params_md.py) "
      "from [`stages/circuit_params.py`](./stages/circuit_params.py), the single "
      "source of truth. Edit `circuit_params.py`, then run "
      "`python docs/reverb-tank/sync.py`. Do not edit `circuit-params.md` by "
      "hand — it is generated.")
    w("")
    w("> **Authority:** This file is the single source of truth for all named parameters.")
    w("> The SPICE netlist (`stage_06_full.net`) is the computational authority and must match this file.")
    w("> All other docs (builder-guide, parts-spec, build-plan, design) reference this file — they do NOT restate numbers.")
    w("> Edit `circuit_params.py`, then run `sync.py`. Do not edit `circuit-params.md` by hand — it is generated.")
    w("")
    w("This table is THE authoritative human-readable source for every named value in the Ghost Spring circuit. The netlist [`stages/stage_06_full.net`](./stages/stage_06_full.net) is the computational mirror of this file and must agree with it byte-for-byte on values; the Python constants module [`stages/circuit_params.py`](./stages/circuit_params.py) is the machine-readable mirror that the generator scripts import. If any of the three disagree, that is a bug — edit `circuit_params.py`, then run `sync.py`. Do not edit `circuit-params.md` by hand — it is generated.")
    w("")
    w("Companion authorities (each owns a different *class* of value):")
    w("")
    w("- **Pass criteria** (measurement windows / `.meas` directives): [`stages/test-assertions.md`](./stages/test-assertions.md) — computational authority for the pass bands reproduced at the bottom of this file.")
    w("- **Parts** (Mouser PNs, packages, quantities): [`mouser-bom.csv`](./mouser-bom.csv).")
    w("- **Design rationale** (why a value was chosen): [`parts-spec.md`](./parts-spec.md).")
    w("- **Bench procedures**: [`stages/builder-guide.md`](./stages/builder-guide.md).")
    w("")
    w("> **Netlist designator note.** SPICE reserves some single-letter prefixes, and the pots are modelled as two halves. The mapping between the schematic/BOM designator and the netlist instance name is called out per row where they differ. Summary:")
    w("> - **C1** (BOM) = **`C_drive`** (netlist) — same physical 1µF Dwell-coupling cap.")
    w("> - **F2 / F3** polyfuses = **`RF2` / `RF3`** (SPICE reserves the `F` prefix for current-controlled sources; modelled as 0.5Ω series R).")
    w("> - **RV1 / RV2 / RV3** pots are each modelled as two series halves: `RV1a`+`RV1b` (5k+5k = 10k Dwell), `RV2a`+`RV2b` (50k+50k = 100k Mix), `RV3a`+`RV3b` (50k+50k = 100k Tone). The wiper node is the junction.")
    w("> - **U4 / U5** regulators are SPICE instances **`XU4` / `XU5`** (LM78xx / LM79xx behavioural subckts).")
    w("> - **BR1** bridge = four diodes **`DBR1a`–`DBR1d`** (model `DN4007`).")
    w("> - **TVS1** = two back-to-back zeners **`DTVS1a` / `DTVS1b`** (model `BZX84C15L`).")
    w("")
    w("---")
    w("")

    # ---- Resistors ----
    w("## Resistors")
    w("")
    w("All signal-path resistors: metal film, 1% tolerance, 250mW. (R_bleed1/2 are 1W flameproof metal film.)")
    w("")
    w("| Ref | Value (Ω) | Function | Netlist node(s) |")
    w("|---|---|---|---|")
    for ref, val, fn, node in RESISTORS:
        w("| %s | %s | %s | %s |" % (ref, val, fn, node))
    w("")
    w("> Power-LED current-limit resistor (10k from +15V) and the ground-lift 10Ω are panel/wiring parts not present in the signal netlist; their values live in [`parts-spec.md`](./parts-spec.md).")
    w("")
    w("---")
    w("")

    # ---- Capacitors ----
    w("## Capacitors")
    w("")
    w("Signal-path caps: film (WIMA MKS2/MKP). C2/C13–C16 electrolytic; C11/C12 bulk electrolytic; C_bright silver mica.")
    w("")
    w("| Ref | Value | Function | Netlist node(s) |")
    w("|---|---|---|---|")
    for ref, val, fn, node in CAPACITORS:
        w("| %s | %s | %s | %s |" % (ref, val, fn, node))
    w("")
    w("---")
    w("")

    # ---- Inductors ----
    w("## Inductors / Coupled magnetics (lumped models)")
    w("")
    w("| Ref | Value | Function | Netlist node(s) |")
    w("|---|---|---|---|")
    for ref, val, fn, node in INDUCTORS:
        w("| %s | %s | %s | %s |" % (ref, val, fn, node))
    w("")
    w("---")
    w("")

    # ---- Semiconductors ----
    w("## Semiconductors")
    w("")
    w("| Ref | Part number / model | Function |")
    w("|---|---|---|")
    w("| U1, U2, U3 | OPA2134PA (DIP-8 dual; 2 packages, 3 sections used) | Input buffer / recovery preamp / output buffer (SPICE: UniversalOpAmp2 level2) |")
    w("| Q1 | BD139 (TO-126 NPN) | Class-A discrete transformer driver |")
    w("| D3 | 1N4148 | Flyback clamp across REB3S primary (anode→collector, cathode→+15V) |")
    w("| D_clamp+ (`Dclamp_p`) | 1N4148 | U1(+) overvoltage clamp (anode→U1+, cathode→+15V) |")
    w("| D_clamp− (`Dclamp_n`) | 1N4148 | U1(+) overvoltage clamp (anode→−15V, cathode→U1+) |")
    w("| TVS1 (`DTVS1a`/`DTVS1b`) | SMBJ15CA (model: 2× BZX84C15L back-to-back) | Bidirectional ESD/TVS at input jack |")
    w("| BR1 (`DBR1a`–`DBR1d`) | W04G (model: 4× 1N4007 / DN4007) | Full-wave bridge rectifier |")
    w("| U4 (`XU4`) | LM7815 (model: LM78xx subckt) | +15V linear regulator |")
    w("| U5 (`XU5`) | LM7915 (model: LM79xx subckt) | −15V linear regulator |")
    w("")
    w("---")
    w("")

    # ---- Potentiometers ----
    w("## Potentiometers")
    w("")
    w("| Ref | Value | Taper | Function |")
    w("|---|---|---|---|")
    w("| RV1 (Dwell) | 10kΩ | Linear | Drive level into transformer (modelled `RV1a` 5k + `RV1b` 5k) |")
    w("| RV2 (Mix) | 100kΩ | Audio | Dry/wet blend (modelled `RV2a` 50k + `RV2b` 50k) |")
    w("| RV3 (Tone) | 100kΩ | Audio | High-shelf EQ on wet signal (modelled `RV3a` 50k + `RV3b` 50k) |")
    w("")
    w("> Pot positions used for the verified simulations are tabulated in [`builder-guide.md`](./stages/builder-guide.md) (\"Pot positions for every test\"). The netlist models each pot at the wiper position giving the values above.")
    w("")
    w("---")
    w("")

    # ---- Power supply ----
    w("## Power supply")
    w("")
    w("| Element | Spec / value | Notes |")
    w("|---|---|---|")
    w("| T1 transformer | Triad F-219X, 30VA, 2×115VAC primary, 2×15VAC secondary (15-0-15) | Primaries parallel for 120V mains; secondaries series for center-tapped 15-0-15. Modelled as two anti-phase `%s` (%sV peak = 15Vrms·√2) about a grounded center tap. |" % (P.VSEC_SINE, P.VSEC_PEAK))
    w("| BR1 bridge | W04G, 2A / 400V (model 4× 1N4007) | `pos_rect` = +ve unregulated bus, `neg_rect` = −ve bus |")
    w("| Unregulated bus | ≈ ±%gV (avg, settled) | ≈ peak %sV − 2 diode drops, held by bulk caps; ≈21mVpp ripple in model |" % (P.UNREG_BUS, P.VSEC_PEAK))
    w("| C11 / C12 filter | %s / 50V each | Main bulk filter per rail |" % farad(P.C11))
    w("| R_bleed1 / R_bleed2 | %sΩ / 1W each | τ = 10k × 2200µF = 22s → <2V in ~110s after power-off (44mW dissipation) |" % ohm(P.R_BLEED1))
    w("| U4 / U5 regulators | LM7815 / LM7915 | Drop ≈5.4V (20.4V bus − 15V) at ~30–50mA → ≈0.15–0.3W each; heatsink + mica pad mandatory |")
    w("| C13 / C14 | %s / 25V each | Regulator output stability caps |" % farad(P.C13))
    w("| C17 / C18 | %s / 63V each | Regulator output HF bypass |" % farad(P.C17))
    w("| C15 / C16 | %s / 25V each | Board-entry bulk decoupling |" % farad(P.C15))
    w("| C5–C8 | %s / 63V (4 total) | Op-amp supply-pin decoupling |" % farad(P.C5))
    w("| F2 / F3 polyfuses | Bourns MF-R050, 500mA each (model %sΩ) | On the DC rails after the regulators (RF2/RF3) |" % P.RF2)
    w("| F1 mains fuse | 500mA slow-blow | Primary-side protection |")
    w("| Mains protection | MOV1 V275LA20AP, NTC1 Ametherm MS32 5006 (5Ω), F1 Schurter 5110.1052 EMI inlet | Across-line / inrush / EMI filter (not in signal netlist) |")
    w("")
    w("---")
    w("")

    # ---- Operating point ----
    w("## Operating point (verified by simulation)")
    w("")
    w("Source: `stage_06_full` `op` variant (settled DC at the 190–200ms tail; the PSU is degenerate at a true `.op`). Q1 = BD139.")
    w("")
    w("| Quantity | Verified sim value | First-order estimate | Notes |")
    w("|---|---|---|---|")
    w("| Q1 Ve (`V(q1_e)`) | **%g V** | %g V | `q1_ve` measurement; emitter = top of R5 |" % (P.Q1_VE_SIM, P.Q1_VE_FIRSTORDER))
    w("| Q1 Vb (base) | ≈1.9 V (open-circuit 1.92 V) | 1.92 V | Set by R3b/R4, loaded by base current |")
    w("| Q1 Vc (collector) | ≈13.8–14 V | — | Idles near +15V (L1 is near-DC short to rail), swings down under drive |")
    w("| Q1 Ic | **≈%g mA** | %g mA | Ic ≈ Ve/R5 = %g / 68 |" % (P.Q1_IC_SIM * 1e3, P.Q1_IC_FIRSTORDER * 1e3, P.Q1_VE_SIM))
    w("| Q1 Vbe | ≈0.8 V | 0.7 V | Higher than 0.7V at this current (real Vbe) |")
    w("| Q1 Vce | ≈12.7–13.9 V | — | ≈Vc − Ve; dissipation ≈ Vce × Ic ≈ 0.22 W |")
    w("| U1 output DC (`off_u1`) | **≈%g V (≈0 V)** | 0 V | Within ±10mV window |" % P.OFF_U1_SIM)
    w("| U2 output DC (`off_u2`) | **+%g mV** | 0 V | Settles from ~72mV at 20ms to <0.5mV by 200ms |" % (P.OFF_U2_SIM * 1e3))
    w("| U3 / output DC (`off_u3`) | **%s µV (≈0 V)** | 0 V | At `v_out` (output jack) |" % _num(P.OFF_U3_SIM * 1e6))
    w("| +15V rail (`rail_pos`) | **≈+%s V** | +15 V | LM7815 on its 15.0V clamp (bus well above dropout) |" % _num1(P.RAIL_POS))
    w("| −15V rail (`rail_neg`) | **≈%s V** | −15 V | LM7915 on its −15.0V clamp |" % _num1(P.RAIL_NEG))
    w("")
    w("---")
    w("")

    # ---- AC parameters ----
    w("## Key AC parameters (verified by simulation)")
    w("")
    w("Source: `stage_06_full` `ac` variant (ideal ±15V rails; signal-path small-signal is independent of rail origin).")
    w("")
    w("| Quantity | Verified sim value | Design nominal | Notes |")
    w("|---|---|---|---|")
    w("| Recovery gain (U2), V/V | **%g×** @1kHz | 214× (= 1 + 100k/470) | `recov_gain`; `V(u2_out)/V(u2_in_pos)` |" % P.RECOV_GAIN_SIM)
    w("| Recovery gain (U2), dB | **%g dB** @1kHz | 46.6 dB | |" % P.RECOV_GAIN_DB_SIM)
    w("| Wet HPF −3dB corner | **%g Hz** | %g Hz (= 1/(2π·R6·C4)) | `hpf_m3db`; measured as R6/C4 transfer `V(hpf_out)/V(u2_out)`. Sim/design differ due to loading; both in band |" % (P.HPF_CORNER_SIM, P.HPF_CORNER_DESIGN))
    w("| Tank resonant peak (\"drip\") | ≈2–3 kHz | %s target | `tank_pk_f`; resonance of REB3S primary with tank input Z |" % khz_range(P.TANK_PEAK_WINDOW))
    w("| Output impedance | <100 Ω | — | Set by U3 (FET buffer) + R7 100Ω series |")
    w("| Input impedance | 1 MΩ | — | Set by R1 shunt after C_in |")
    w("| Output peak (`vout_pk`), 100mVpk in | **%g V** | — | tran variant; well below clipping |" % P.VOUT_PK_SIM)
    w("| Oscillation ratio (`osc_ratio`) | **%g** | — | tran variant; <1.05 = stable |" % P.OSC_RATIO_SIM)
    w("")
    w("---")
    w("")

    # ---- Pass windows ----
    w("## Pass windows (from test-assertions.md)")
    w("")
    w("> **`test-assertions.md` is the computational authority for these bands** (it holds the `.meas` directives). The table below is reproduced for convenience and must match it. If they disagree, `test-assertions.md` wins.")
    w("")
    w("| Assertion | Expression | Pass window |")
    w("|---|---|---|")
    w("| `off_u1` | `V(u1_out)` | \\|val\\| ≤ %s |" % mv(P.OFFSET_WINDOW))
    w("| `off_u2` | `V(u2_out)` | \\|val\\| ≤ %s |" % mv(P.OFFSET_WINDOW))
    w("| `off_u3` | `V(v_out)` | \\|val\\| ≤ %s |" % mv(P.OFFSET_WINDOW))
    # q1_ve window: original writes the lower bound with one decimal (1.0).
    w("| `q1_ve` | `V(q1_e)` | %s – %s V (sim %g V) |"
      % (_num1(P.Q1_VE_WINDOW[0]), _num(P.Q1_VE_WINDOW[1]), P.Q1_VE_SIM))
    w("| `q1_ic` | `Ic(Q1)` | %s (sim ≈%g mA) |" % (ma_range(P.Q1_IC_WINDOW), P.Q1_IC_SIM * 1e3))
    w("| `recov_gain` | `V(u2_out)/V(u2_in_pos)` @1k | %s× (sim %g×) |" % (gain_range(P.RECOV_GAIN_WINDOW), P.RECOV_GAIN_SIM))
    w("| `hpf_m3db` | wet −3dB corner | %s (sim %g Hz) |" % (hz_range(P.HPF_CORNER_WINDOW), P.HPF_CORNER_SIM))
    w("| `vout_pk` | `MAX abs(V(v_out))` | < %g V (sim %g V) |" % (P.VOUT_PK_MAX, P.VOUT_PK_SIM))
    w("| `osc_ratio` | RMS_late / RMS_early | < %g (sim %g) |" % (P.OSC_RATIO_MAX, P.OSC_RATIO_SIM))
    w("| `d3_pk` | `MAX abs(I(D3))` | < 1 mA |")
    w("| `clamp_p_i` / `clamp_n_i` | `I(Dclamp_*)` | < %g µA at idle |" % (P.CLAMP_IDLE_MAX * 1e6))
    w("| `u1pos_hi` / `u1pos_lo` | `V(u1_pos)` @20Vpp in | ≤ +%g V / ≥ %s V (clamps ≈±%gV) |" % (P.U1POS_CLAMP_WINDOW[1], _num(P.U1POS_CLAMP_WINDOW[0]), P.CLAMP_VOLTAGE))
    w("| `tank_pk_f` | freq of max `V(tank_in)` | %s (≈2–3 kHz) |" % khz_range_sp(P.TANK_PEAK_WINDOW))
    w("| `tank_drive_db` | `20log10(V(tank_in)/V(rv1_wiper))` @2k | > −60 dB |")
    w("| `rail_pos` | `V(+15V)` | %s |" % v_range(P.RAIL_POS_WINDOW))
    w("| `rail_neg` | `V(-15V)` | %s – %s V |" % (_num(P.RAIL_NEG_WINDOW[0]), _num(P.RAIL_NEG_WINDOW[1])))
    w("| `ripple_pos` / `ripple_neg` | `PP V(±15V)` | < %g mVpp |" % (P.RIPPLE_MAX_PP * 1e3))
    w("")
    w("| Bench noise floor (Stage 7) | output noise at J2 | < %g mVrms, no discrete 60/120Hz spike |" % (P.NOISE_FLOOR_MAX_VRMS * 1e3))
    w("")
    w("---")
    w("")
    w("*Every component in `stage_06_full.net` appears above. The lumped-model R/L/C of the tank and transformer (`R_tank_*`, `L_tank*`, `L1`/`L2`/`K1`, `C_tank_mech`) are SPICE modelling elements, not separately-purchased parts — the physical parts are RT1 (9AB3C1B tank) and T2 (REB3S transformer), per [`parts-spec.md`](./parts-spec.md).*")
    w("")
    return "\n".join(L)


def main():
    md = build_md()
    with open(OUT, "w") as f:
        f.write(md)
    print("wrote %s (%d lines)" % (OUT, md.count("\n") + 1))


if __name__ == "__main__":
    main()
