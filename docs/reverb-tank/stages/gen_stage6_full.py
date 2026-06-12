#!/usr/bin/env python3
"""
gen_stage6_full.py - Generate stage_06_full.asc (+ matching .net sidecar).

Stage 6 of the Ghost Spring reverb build: FULL-INTEGRATION verification. Stage 6
adds NO new components. It carries the complete Stage 5 circuit (real PSU + BD139
driver + REB3S transformer + spring tank + input protection + the three op-amp
stages) BYTE-FOR-BYTE and re-runs the original Stage 1 MVP signal-path assertion
suite against the whole real circuit. The point is a clean regression gate: if any
Stage 1 number drifted as the real supply/driver/protection were added, it surfaces
here and bisects to the stage that introduced it.

Carried unchanged from Stage 5 (see gen_stage5_psu.py for the full rationale):
  - T1 15-0-15VAC secondary (two anti-phase 60Hz SINE(0 21.2 60), center tap=GND)
  - F2/F3 polyfuses (0.5 ohm), BR1 bridge (4x 1N4007, DBR1a..d)
  - C11/C12 1000u bulk + 10k bleed, U4 LM7815 / U5 LM7915 (inline behavioural
    subckts), C13/C14 75u (3x 25u parallel) + C17/C18 100n reg out caps
  - C5-C8 / C15/C16 rail decoupling
  - Input protection: TVS1 (back-to-back BZX84C15L), C_in/R1, clamp pair
  - U1 buffer, RV1 dwell, BD139 driver (Q1 + bias), REB3S transformer (L1/L2/K1)
  - Spring tank RLC, U2 recovery (214x), post-recovery HPF (R6/C4)
  - Tone RV3, Mix RV2, U3 output buffer, 47k load

Stage 1 assertion suite (test-assertions.md), now re-run on the FULL circuit:

  | Assertion  | Expression                          | Pass condition |
  |------------|-------------------------------------|----------------|
  | off_u1     | V(u1_out)                           | +/-10mV        |
  | off_u2     | V(u2_out)                           | +/-10mV        |
  | off_u3     | V(v_out)                            | +/-10mV        |
  | q1_ve      | V(q1_e)                             | 1.0..1.4V      |
  | recov_gain | V(u2_out)/V(u2_in_pos) @1kHz        | 205..225x      |
  | hpf_m3db   | -3dB corner of wet (hpf_out)        | 250..320Hz     |
  | vout_pk    | MAX abs(V(v_out))                   | < 14V          |
  | osc_ratio  | RMS(90m..100ms)/RMS(40m..50ms) vout | < 1.05         |

Analysis variants (ONE active at a time):
  op    : DC operating point. A true .op is DEGENERATE for the PSU - the SINE
          sources freeze at t=0 (0V), the bridge sees no drive and the caps never
          charge. So we run a SHORT transient (.tran 0 20m 0 1u) WITH THE SIGNAL
          SOURCE KILLED (V1 amplitude 0) and read the settled DC at the tail
          (AVG FROM=15m TO=20m). With no signal injected the op-amp outputs and the
          driver emitter sit at their pure DC bias points:
            off_u1 = AVG V(u1_out)  in +/-10mV
            off_u2 = AVG V(u2_out)  in +/-10mV
            off_u3 = AVG V(v_out)   in +/-10mV
            q1_ve  = AVG V(q1_e)    in 1.0..1.4V
  ac    : recovery gain + wet HPF corner. The PSU SINE sources carry NO AC spec
          (AC defaults to 0), so they are invisible to a .ac sweep - only the
          signal source V1 (AC 1) drives the small-signal analysis. .ac dec 100
          20 20k:
            recov_gain = V(u2_out)/V(u2_in_pos) AT=1k  in 205..225
            hpf_m3db   = freq where V(hpf_out) = 0.7079*ref(@5k)  in 250..320Hz
  tran  : output peak + no-oscillation. 100ms run, 100mVpk 1kHz signal:
            vout_pk   = MAX abs(V(v_out))                     < 14V
            osc_ratio = RMS(90m..100m)/RMS(40m..50m) of V(v_out)  < 1.05

  Pot-position sweep variants (Stage 7, GitHub #43) — one pot to a travel
  extreme, others at noon; each is a 200ms tran:
    dwell_min        : Dwell fully CCW (min drive to tank)
    dwell_max        : Dwell fully CW  (max drive to tank)
    mix_ccw          : Mix fully CCW   (dry-only path)
    mix_cw           : Mix fully CW    (wet-only path)
    dwell_max_mix_cw : Dwell CW + Mix CW (worst-case clip / settle)

  Stage 8 realistic hardware stress variants:
    stage6_vos : U2 Vos stress — 500uV DC source at U2 non-inverting input
    lo_beta    : BD139 low-beta corner — BF forced to datasheet hFE minimum

Connectivity strategy identical to gen_stage5_psu.py: every pin gets a FLAG at its
exact coordinate so nets join by name; the script emits BOTH the .asc schematic and
a matching .net sidecar from the same component list so they cannot drift.

Generator fixes applied (per Stage 6 spec):
  1. Diode instances use the D prefix (DBR1a..d, DTVS1a/b, Dclamp_*, D3).
  2. OPA_PARAMS_NET is a single 'level2 ...' string.
  3. .OPTIONS ALLOW_AMBIGUOUS_MODELS is the third line of every .net.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
import circuit_params as P  # noqa: E402  single source of truth (see THE CASCADE)

OPA_PARAMS = P.OPA_PARAMS
OPA_PARAMS_NET = P.OPA_PARAMS_NET

BD139_MODEL = P.BD139_MODEL

# BZX84C15L: 15V 250mW zener, back-to-back pair modelling the SMBJ15CA TVS.
BZX84C15L_MODEL = P.BZX84C15L_MODEL

# 1N4007 bridge-rectifier diode: 1000V 1A general-purpose rectifier.
DN4007_MODEL = P.DN4007_MODEL

# Behavioural linear-regulator subckts (no 78xx/79xx ships with this LTspice).
LM78XX_SUBCKT = P.LM78XX_SUBCKT
LM79XX_SUBCKT = P.LM79XX_SUBCKT


class Build:
    def __init__(self):
        self.asc = ["Version 4", "SHEET 1 2400 1600"]
        self.net = []          # SPICE element/card lines
        self.subckts = []      # inline .subckt blocks (list of line-lists)
        self.directives = []   # analysis + .meas + .model cards (placed near end)

    # ---- schematic helpers ----
    def _atext(self, x, y, s, size=2):
        self.asc.append(f"TEXT {x} {y} Left {size} {s}")

    def _aflag(self, x, y, name):
        self.asc.append(f"FLAG {x} {y} {name}")

    def _asym(self, kind, x, y, rot, name, attrs):
        self.asc.append(f"SYMBOL {kind} {x} {y} {rot}")
        self.asc.append(f"SYMATTR InstName {name}")
        for k, v in attrs:
            self.asc.append(f"SYMATTR {k} {v}")

    def text(self, x, y, s, size=2):
        self._atext(x, y, s, size)

    # ---- components: emit both schematic symbol and netlist card ----
    def res(self, name, value, x, y, na, nb):
        self._asym("res", x, y, "R0", name, [("Value", value)])
        self._aflag(x + 16, y + 16, na)
        self._aflag(x + 16, y + 96, nb)
        self.net.append(f"{name} {na} {nb} {value}")

    def cap(self, name, value, x, y, na, nb):
        self._asym("cap", x, y, "R0", name, [("Value", value)])
        self._aflag(x + 16, y + 0, na)
        self._aflag(x + 16, y + 64, nb)
        self.net.append(f"{name} {na} {nb} {value}")

    def ind(self, name, value, x, y, na, nb):
        self._asym("ind", x, y, "R0", name,
                   [("Value", value), ("SpiceLine", "Rser=0")])
        self._aflag(x + 16, y + 16, na)
        self._aflag(x + 16, y + 96, nb)
        self.net.append(f"{name} {na} {nb} {value} Rser=0")

    def diode(self, name, model, x, y, na, nk):
        self._asym("diode", x, y, "R0", name, [("Value", model)])
        self._aflag(x + 16, y + 0, na)
        self._aflag(x + 16, y + 64, nk)
        self.net.append(f"{name} {na} {nk} {model}")

    def vsrc(self, name, value, x, y, np_, nn, value2=None):
        attrs = [("Value", value)]
        if value2:
            attrs.append(("Value2", value2))
        self._asym("voltage", x, y, "R0", name, attrs)
        self._aflag(x + 0, y + 16, np_)
        self._aflag(x + 0, y + 96, nn)
        extra = f" {value2}" if value2 else ""
        self.net.append(f"{name} {np_} {nn} {value}{extra}")

    def npn(self, name, model, x, y, nc, nb, ne):
        self._asym("npn", x, y, "R0", name, [("Value", model)])
        self._aflag(x + 0, y + 48, nb)
        self._aflag(x + 64, y + 0, nc)
        self._aflag(x + 64, y + 96, ne)
        self.net.append(f"{name} {nc} {nb} {ne} {model}")

    def opa(self, name, x, y, ninp, ninn, nvp, nvn, nout):
        self._asym("UniversalOpamp2", x, y, "R0", name,
                   [("Value", "level2"), ("Value2", OPA_PARAMS)])
        self._aflag(x - 32, y + 16, ninp)
        self._aflag(x - 32, y - 16, ninn)
        self._aflag(x + 0, y - 32, nvp)
        self._aflag(x + 0, y + 32, nvn)
        self._aflag(x + 32, y + 0, nout)
        self.net.append(
            f"X§{name} {ninp} {ninn} {nvp} {nvn} {nout} {OPA_PARAMS_NET}")

    def kcouple(self, name, la, lb, k, x, y):
        card = f"{name} {la} {lb} {k}"
        self._atext(x, y, "!" + card)
        self.net.append(card)

    def reg(self, name, subckt, x, y, nin, ncom, nout):
        self._atext(x, y, f"{name}: {subckt}  IN={nin} COM={ncom} OUT={nout}", 2)
        self.net.append(f"X{name} {nin} {ncom} {nout} {subckt}")

    def subckt(self, lines):
        self.subckts.append(lines)

    def directive(self, card):
        self.directives.append(card)

    def dump(self, asc_path, net_path):
        # --- finish .asc: place directives as TEXT lines (bang = active) ---
        y = 1360
        for card in self.directives:
            self._atext(16, y, "!" + card)
            y += 32
        open(asc_path, "w").write("\n".join(self.asc) + "\n")

        # --- finish .net sidecar ---
        net = [f"* {os.path.basename(asc_path)}",
               "* Generated by gen_stage6_full.py for installed LTspice 26 symbols.",
               ".OPTIONS ALLOW_AMBIGUOUS_MODELS"]
        net += self.net
        net.append(".model D D")
        net.append(r".lib standard.dio")
        # inline regulator subckts
        for blk in self.subckts:
            net += blk
        net.append("* BD139 driver model + zener/rectifier models + analysis directives")
        for card in self.directives:
            net.append(card)
        net.append(".lib UniversalOpAmp2.lib")
        net.append(".backanno")
        net.append(".end")
        open(net_path, "w").write("\n".join(net) + "\n")


def _spice_to_ohms(tok):
    """Minimal SPICE magnitude parser for the pot total strings ('10k','100k')."""
    t = tok.strip().lower()
    mult = 1.0
    for suf, m in (("meg", 1e6), ("k", 1e3), ("m", 1e-3), ("u", 1e-6)):
        if t.endswith(suf):
            t = t[: -len(suf)]
            mult = m
            break
    return float(t) * mult


def _fmt_ohms(ohms):
    """Format a resistance back to a compact SPICE string (e.g. 5000 -> '5k')."""
    if ohms >= 1e6 and abs(ohms / 1e6 - round(ohms / 1e6)) < 1e-9:
        return "%gMeg" % (ohms / 1e6)
    if ohms >= 1e3 and abs(ohms / 1e3 - round(ohms / 1e3)) < 1e-9:
        return "%gk" % (ohms / 1e3)
    return "%g" % ohms


def pot_split(total, position):
    """Split a pot of total resistance `total` (SPICE string or ohms) at travel
    `position` (0.0=CCW/min .. 1.0=CW/max) into (a_val, b_val) SPICE strings for
    the two series halves (a = CCW-end..wiper, b = wiper..CW-end).

    a = position * total, b = (1-position) * total. At an extreme one half would
    be 0 Ω, which can float/short the wiper node in SPICE, so each half is floored
    at circuit_params.POT_MIN_OHMS (0.001 Ω) instead of exactly 0.

      position=0.0 -> a≈0.001, b=total   (wiper at CCW end)
      position=0.5 -> a=b=total/2         (noon, matches the baseline netlist)
      position=1.0 -> a=total, b≈0.001    (wiper at CW end)
    """
    tot = total if isinstance(total, (int, float)) else _spice_to_ohms(total)
    floor = _spice_to_ohms(P.POT_MIN_OHMS)
    a = max(position * tot, floor)
    b = max((1.0 - position) * tot, floor)
    # Keep the exact constant string for the floor so it reads as '0.001'.
    a_str = P.POT_MIN_OHMS if a == floor else _fmt_ohms(a)
    b_str = P.POT_MIN_OHMS if b == floor else _fmt_ohms(b)
    return a_str, b_str


# Pot-position variants: name -> (dwell_pos, mix_pos, tone_pos). The three base
# analyses (op/ac/tran) keep the baseline 50/50 split via the circuit_params
# RV*A/RV*B constants; the sweep variants override the relevant pot halves.
POT_SWEEP_VARIANTS = {
    "dwell_min":        (P.POT_MIN, P.POT_MID, P.POT_MID),
    "dwell_max":        (P.POT_MAX, P.POT_MID, P.POT_MID),
    "mix_ccw":          (P.POT_MID, P.POT_MIN, P.POT_MID),
    "mix_cw":           (P.POT_MID, P.POT_MAX, P.POT_MID),
    "dwell_max_mix_cw": (P.POT_MAX, P.POT_MAX, P.POT_MID),
}


def build(active_analysis="op"):
    """active_analysis in {'op','ac','tran'} (baseline 50/50 pots) or one of the
    POT_SWEEP_VARIANTS keys (a tran run with one or more pots driven to a travel
    extreme; the others held at noon). Only ONE analysis active at a time."""
    b = Build()

    # Resolve the pot half values for this variant. Baseline analyses use the
    # circuit_params 50/50 constants verbatim (so op/ac/tran netlists are
    # byte-identical to before); sweep variants compute the halves via pot_split.
    if active_analysis in POT_SWEEP_VARIANTS:
        dwell_pos, mix_pos, tone_pos = POT_SWEEP_VARIANTS[active_analysis]
        rv1a, rv1b = pot_split(P.RV1_TOTAL, dwell_pos)
        rv2a, rv2b = pot_split(P.RV2_TOTAL, mix_pos)
        rv3a, rv3b = pot_split(P.RV3_TOTAL, tone_pos)
    else:
        rv1a, rv1b = P.RV1A, P.RV1B
        rv2a, rv2b = P.RV2A, P.RV2B
        rv3a, rv3b = P.RV3A, P.RV3B

    b.text(16, -40, "Ghost Spring Stage 6 - FULL INTEGRATION verification (Stage 5 complete circuit, Stage 1 MVP assertions re-run)", 4)
    b.text(16, 8, "Stage 6 adds NOTHING. It carries the complete Stage 5 circuit (real PSU + BD139 driver + REB3S transformer + spring tank + input protection + U1/U2/U3) byte-for-byte and re-runs the original Stage 1 signal-path assertion suite (off_u1/2/3, q1_ve, recov_gain, hpf_m3db, vout_pk, osc_ratio) against the WHOLE real circuit. Connectivity by net labels (FLAG at each pin).", 2)

    # ====================================================================
    # === STAGE 5: +/-15V LINEAR POWER SUPPLY (carried unchanged) =========
    # ====================================================================
    # IMPORTANT - rails for the .ac variant.
    # The real PSU is DEGENERATE at any DC operating point: the T1 SINE sources
    # freeze at their t=0 value (0V), so the bridge sees no drive, the bulk caps
    # never charge, and the regulated rails sit at 0V. A .ac analysis linearises
    # the circuit about exactly that dead DC point, which leaves every op-amp
    # UNPOWERED (the UniversalOpAmp2 level2 references its V+/V- pins; with both
    # rails at 0V its gain collapses to ~unity). The recovery-gain and HPF-corner
    # assertions are small-signal properties of the SIGNAL PATH and are completely
    # independent of HOW the +/-15V is produced, so for the .ac variant ONLY we
    # power the rails from ideal +/-15V DC sources (the same bench rails Stages 1-4
    # used) and omit the rectifier/regulator network. The op and tran variants
    # carry the FULL real PSU (those are where rail DC and ripple actually matter).
    if active_analysis == "ac":
        b.vsrc("Vpos", P.VRAIL_IDEAL, 64, 1000, "+15V", "0")
        b.vsrc("Vneg", P.VRAIL_IDEAL, 224, 1000, "0", "-15V")
        b.text(64, 960, "AC variant: ideal +/-15V bench rails (real PSU is degenerate at the DC op-point used by .ac). Signal-path small-signal is independent of rail origin.", 2)
    else:
        # T1 secondary: 15-0-15VAC, center tap = GND. Two anti-phase 60Hz SINE
        # sources, 21.2V peak = 15Vrms * sqrt(2). PSU SINE sources carry NO AC
        # spec (AC defaults to 0).
        b.vsrc("Vsec_p", P.VSEC_SINE, 64, 1000, "ac_pos", "0")
        b.vsrc("Vsec_n", P.VSEC_SINE, 224, 1000, "0", "ac_neg")
        b.text(64, 960, "T1 Triad F-219X 15-0-15VAC. Center tap = GND. 21.2Vpk = 15Vrms*sqrt(2).", 2)

        # BR1 = W04G full-wave bridge off the center-tapped winding, 4x 1N4007.
        b.diode("DBR1a", "DN4007", 640, 880, "ac_pos", "pos_rect")
        b.diode("DBR1b", "DN4007", 760, 880, "ac_neg", "pos_rect")
        b.diode("DBR1c", "DN4007", 640, 1080, "neg_rect", "ac_pos")
        b.diode("DBR1d", "DN4007", 760, 1080, "neg_rect", "ac_neg")
        b.text(640, 840, "BR1 W04G = 4x 1N4007. pos_rect=+ve bus, neg_rect=-ve bus.", 2)

        # Bulk filter caps + bleed resistors, one set per rail.
        b.cap("C11", P.C11, 900, 880, "pos_rect", "0")     # +ve bulk filter
        b.res("R_bleed1", P.R_BLEED1, 1020, 880, "pos_rect", "0")  # +ve bleed
        b.cap("C12", P.C12, 900, 1080, "neg_rect", "0")     # -ve bulk filter
        b.res("R_bleed2", P.R_BLEED2, 1020, 1080, "neg_rect", "0")  # -ve bleed

        # Regulators: U4 LM7815 (+15), U5 LM7915 (-15). Inline behavioural subckts.
        # Output caps sit directly on the regulator output pin (reg_pos/reg_neg).
        b.reg("U4", "LM78xx", 1160, 860, "pos_rect", "0", "reg_pos")
        b.reg("U5", "LM79xx", 1160, 1100, "neg_rect", "0", "reg_neg")

        # Regulator output caps + HF bypass directly at each regulator output pin.
        b.cap("C13", P.C13, 1320, 880, "reg_pos", "0")
        b.cap("C17", P.C17, 1440, 880, "reg_pos", "0")
        b.cap("C14", P.C14, 1320, 1080, "reg_neg", "0")
        b.cap("C18", P.C18, 1440, 1080, "reg_neg", "0")
        b.text(1320, 840, "C13/C14 75u (3x 25u parallel) reg out caps, C17/C18 100n HF bypass.", 2)

        # F2/F3 MF-R050 polyfuses -> 0.5 ohm series R (RF2/RF3 in SPICE).
        # On the DC RAIL OUTPUT (reg pin -> +15V/-15V bus), AFTER the regulator
        # and its output cap, so a downstream PCB short trips the fuse and
        # protects the regulator (per parts-spec F2/F3, BOM, build-plan, builder
        # guide). Modeled as 0.5 ohm series R; MF-R050 hold resistance ~0.7 ohm.
        b.res("RF2", P.RF2, 1500, 880, "reg_pos", "+15V")
        b.res("RF3", P.RF3, 1500, 1080, "reg_neg", "-15V")
        b.text(1500, 840, "F2/F3 MF-R050 polyfuse = 0.5ohm on DC rail (RF2/RF3).", 2)

        # Inline regulator subckts (no 78xx/79xx ships with installed LTspice).
        b.subckt(LM78XX_SUBCKT)
        b.subckt(LM79XX_SUBCKT)

    # ====================================================================
    # === STAGE 4 SIGNAL PATH (carried unchanged) - fed from the PSU rails =
    # ====================================================================
    # Extra rail decoupling (C5-C8 100n, C15/C16 10u bulk).
    b.cap("C15", P.C15, 1580, 880, "+15V", "0")
    b.cap("C16", P.C16, 1580, 1080, "-15V", "0")
    b.cap("C5", P.C5, 1700, 880, "+15V", "0")
    b.cap("C6", P.C6, 1700, 1080, "-15V", "0")
    b.cap("C7", P.C7, 1820, 880, "+15V", "0")
    b.cap("C8", P.C8, 1820, 1080, "-15V", "0")

    # Input source. For op (DC bias) the signal is KILLED (amplitude 0) so the
    # op-amp outputs / driver emitter read pure DC. For ac the AC=1 token drives
    # the small-signal sweep. For tran it's the 100mVpk 1kHz test stimulus.
    if active_analysis in ("op", "stage6_vos", "lo_beta"):
        # No signal -> off_u1/2/3, q1_ve and the stress reads are pure DC bias.
        b.vsrc("V1", P.V1_SINE_KILLED, 64, 160, "vin", "0", value2=P.V1_AC_TOKEN)
    else:
        b.vsrc("V1", P.V1_SINE_NORMAL, 64, 160, "vin", "0", value2=P.V1_AC_TOKEN)

    # TVS1 at the jack (vin -> 0), two zeners back-to-back (cathodes at tvs_mid).
    b.diode("DTVS1a", "BZX84C15L", 64, 400, "vin", "tvs_mid")
    b.diode("DTVS1b", "BZX84C15L", 64, 528, "0", "tvs_mid")

    # Input buffer U1 front-end (C_in, R1, clamp pair).
    b.cap("C_in", P.C_IN, 160, 144, "vin", "u1_pos")
    b.res("R1", P.R1, 280, 144, "u1_pos", "0")
    b.diode("Dclamp_p", P.D_1N4148, 400, 96, "u1_pos", "+15V")
    b.diode("Dclamp_n", P.D_1N4148, 400, 224, "-15V", "u1_pos")
    b.opa("U1", 560, 200, "u1_pos", "u1_out", "+15V", "-15V", "u1_out")
    b.res("R2", P.R2, 640, 144, "u1_out", "u1_buf")

    # Dwell pot divider. RV1a is the wiper-to-GND half (a = position×total),
    # RV1b is the signal-to-wiper half (b = (1-position)×total). At CW (max
    # Dwell) a≈total, b≈0 -> wiper ≈ u1_buf = MAXIMUM wet drive.
    b.res("RV1a", rv1a, 760, 60, "rv1_wiper", "0")
    b.res("RV1b", rv1b, 760, 180, "u1_buf", "rv1_wiper")

    # BD139 discrete driver.
    b.cap("C_drive", P.C_DRIVE, 880, 144, "rv1_wiper", "q1_drv")
    b.res("R3b", P.R3B, 1000, 40, "+15V", "q1_base")
    b.res("R4", P.R4, 1000, 200, "q1_base", "0")
    b.res("R3", P.R3, 880, 300, "q1_drv", "q1_base")
    # Q1 references the low-beta model in the lo_beta corner variant, else BD139.
    q1_model = "BD139_lo" if active_analysis == "lo_beta" else "BD139"
    b.npn("Q1", q1_model, 1140, 360, "q1_c", "q1_base", "q1_e")
    b.res("R5", P.R5, 1140, 520, "q1_e", "0")
    b.cap("C2", P.C2, 1280, 520, "q1_e", "0")
    b.diode("D3", P.D_1N4148, 1140, 220, "q1_c", "+15V")

    # REB3S driver transformer.
    b.ind("L1", P.L1, 1140, 60, "+15V", "q1_c")
    b.ind("L2", P.L2, 1300, 60, "tank_in", "0")
    b.kcouple("K1", "L1", "L2", P.K1, 1280, 200)

    # Spring tank RLC.
    b.res("R_tank_in", P.R_TANK_IN, 1300, 240, "tank_in", "0")
    b.ind("L_tank", P.L_TANK, 1420, 60, "tank_in", "tank_mid")
    b.res("R_tank_mech", P.R_TANK_MECH, 1540, 240, "tank_mid", "tk_a")
    b.ind("L_tank_mech", P.L_TANK_MECH, 1540, 360, "tk_a", "tk_b")
    b.cap("C_tank_mech", P.C_TANK_MECH, 1540, 480, "tk_b", "0")
    b.res("R_tank_out", P.R_TANK_OUT, 1660, 60, "tank_mid", "tank_out")
    b.ind("L_tank_out", P.L_TANK_OUT, 1660, 240, "tank_out", "0")

    # Recovery preamp U2. In the Vos-stress variant a small DC source (500uV) is
    # inserted IN SERIES between the C3/Rbias network node and U2's non-inverting
    # input, modelling the OPA2134's worst-case input offset voltage. The network
    # (C3 coupling + Rbias to GND) stays on u2_in_pos_src; the Vos source drives
    # U2(+) at u2_in_pos. For all other variants the Vos source is absent and the
    # network feeds U2(+) directly at u2_in_pos.
    if active_analysis == "stage6_vos":
        b.cap("C3", P.C3, 1780, 144, "tank_out", "u2_in_pos_src")
        b.res("Rbias", P.RBIAS, 1900, 240, "u2_in_pos_src", "0")
        # Vos_u2: 500uV DC offset in series at U2's + input (u2_in_pos_src -> +).
        b.vsrc("Vos_u2", P.U2_VOS_INJECT, 1960, 120, "u2_in_pos", "u2_in_pos_src")
        b.text(1900, 80, "Vos_u2: 500uV OPA2134 worst-case input offset in series at U2(+).", 2)
    else:
        b.cap("C3", P.C3, 1780, 144, "tank_out", "u2_in_pos")
        b.res("Rbias", P.RBIAS, 1900, 240, "u2_in_pos", "0")
    b.opa("U2", 2060, 200, "u2_in_pos", "u2_inv", "+15V", "-15V", "u2_out")
    b.res("Ri", P.RI, 2000, 360, "u2_inv", "0")
    b.res("Rf", P.RF, 2120, 360, "u2_out", "u2_inv")
    b.cap("Cf", P.CF, 2200, 360, "u2_out", "u2_inv")

    # Post-recovery HPF.
    b.cap("C4", P.C4, 2240, 144, "u2_out", "hpf_out")
    b.res("R6", P.R6, 2360, 240, "hpf_out", "0")

    # Tone RV3, Mix RV2, output buffer U3.
    b.res("RV3a", rv3a, 2180, 600, "hpf_out", "rv3_wiper")
    b.res("RV3b", rv3b, 2180, 720, "rv3_wiper", "0")
    # --- Mix RV2: 3-terminal PASSIVE BLEND (not a volume knob). ---------------
    # Physical wiring (parts-spec "Mix Stage Topology"):
    #   Dry  (u1_buf) -> Rdry -> RV2 pin 1 (CCW end)  == node mix_dry
    #   Wet  (rv3_wiper, Tone output) -> RV2 pin 3 (CW end) == node mix_wet
    #   RV2 wiper (pin 2) -> U3(+)                     == node mix_node
    #   C_bright (47p) bridges pin1<->pin3 (full pot, mix_dry<->mix_wet)
    # RV2a = CCW half (pin1->wiper), RV2b = CW half (wiper->pin3). Full-CCW puts
    # the wiper at mix_dry (100% dry); full-CW puts it at mix_wet (100% wet).
    # The wet source ties DIRECTLY to mix_wet (no Rwet) so neither end is shorted.
    b.res("Rdry", P.RDRY, 640, 360, "u1_buf", "mix_dry")
    b.res("RV2a", rv2a, 2300, 760, "mix_dry", "mix_node")   # CCW half of pot
    b.res("RV2b", rv2b, 2300, 880, "mix_node", "mix_wet")   # CW half of pot
    b.cap("C_bright", P.C_BRIGHT, 2420, 760, "mix_dry", "mix_wet")  # bright cap across full pot
    # Wet (Tone wiper) connects directly to the CW end of the pot.
    b.res("Rwet_wire", P.RWET_WIRE, 2300, 600, "rv3_wiper", "mix_wet")  # direct hookup wire, modelled 1mΩ (LTspice rejects R=0)
    b.opa("U3", 2560, 900, "mix_node", "u3_out", "+15V", "-15V", "u3_out")
    b.res("R7", P.R7, 2640, 844, "u3_out", "v_out")
    b.res("Rload", P.RLOAD, 2760, 844, "v_out", "0")
    b.text(2640, 820, "J2 -> MC100 input (47k load)", 2)

    # === Models ===
    b.directive(f".model BD139 {BD139_MODEL}")
    # Low-beta corner: BD139_lo copies the BD139 params with BF forced to the
    # datasheet hFE minimum (40). Q1 references it only in the lo_beta variant.
    if active_analysis == "lo_beta":
        b.directive(f".model BD139_lo {P.BD139_LO_BETA_MODEL}")
    b.directive(f".model BZX84C15L {BZX84C15L_MODEL}")
    b.directive(f".model DN4007 {DN4007_MODEL}")

    # === Analysis (only ONE active at a time) - Stage 1 MVP assertion suite ===
    if active_analysis == "op":
        # DC operating point. .op is DEGENERATE for the PSU (SINE freeze at t=0),
        # so run a transient with the SIGNAL KILLED and read settled DC at the
        # tail. With no signal injected the op-amp outputs / driver emitter sit at
        # their pure bias points.
        #
        # The run is 200ms (not 20ms): the recovery stage U2 reads any residual
        # tank/coupling DC through C3(470n)+Rbias(100k) into a 214x-gain stage, so
        # the start-up transient of the high-L tank (L_tank_out=2H, L_tank_mech=
        # 500m) takes >100ms to bleed out. At 20ms off_u2 still shows ~72mV of
        # decaying transient; by 190-200ms it has settled to <1mV (pure DC bias).
        # Measure all bias points in the 190..200ms tail window.
        b.directive(".tran 0 200m 0 2u")
        b.directive(".meas TRAN off_u1 AVG V(u1_out) FROM=190m TO=200m")
        b.directive(".meas TRAN off_u2 AVG V(u2_out) FROM=190m TO=200m")
        b.directive(".meas TRAN off_u3 AVG V(v_out)  FROM=190m TO=200m")
        # U2 non-inverting input DC bias: Rbias holds u2_in_pos at 0V and C3
        # blocks tank/rail DC. If Rbias opened or a rail leaked in, this node
        # floats to a DC offset the 214x stage multiplies into U2 clipping.
        b.directive(".meas TRAN u2_inpos_bias AVG V(u2_in_pos) FROM=190m TO=200m")
        b.directive(".meas TRAN q1_ve  AVG V(q1_e)   FROM=190m TO=200m")
        # Q1 collector DC and the active-region guards. An NPN driver MUST stay in
        # forward-active (CBJ reverse-biased): V(q1_c) above the base, Vce well
        # above Vce(sat). If Q1 saturates the transformer drive flat-tops and the
        # reverb send distorts badly -- a failure q1_ve/q1_ic alone never catch
        # (they'd both still read in-window with a saturated, clipping collector).
        b.directive(".meas TRAN q1_vc AVG V(q1_c) FROM=190m TO=200m")
        b.directive(".meas TRAN q1_vb AVG V(q1_base) FROM=190m TO=200m")
        b.directive(".meas TRAN q1_vce PARAM {q1_vc - q1_ve}")
        b.directive(".meas TRAN q1_vcb PARAM {q1_vc - q1_vb}")
        # Cross-check: the emitter-implied collector current (q1_ic_calc = Ve/R5,
        # which is really Ie/Ic via R5) against the collector current measured
        # DIRECTLY through the BJT (q1_ic = Ic(Q1)). These are independent reads:
        # I(R5) is identically V(q1_e)/R5, so the old q1_ic = AVG I(R5) made the
        # cross-check a tautology (q1_ic_err ~= 0 regardless of circuit health).
        # Ic(Q1) goes through the transistor model and differs from Ie by the base
        # current (~1% at Bf=100), so q1_ic_err is a real ~1% read, well inside the
        # 10% tolerance. The divisor tracks circuit_params.R5 (not a hardcoded 68)
        # so the formula never silently drifts if R5 changes. q1_ve is a 190-200ms
        # AVG, so q1_ic MUST also be an AVG over the SAME 190-200ms window --
        # comparing the windowed-average Ve against a single instantaneous Ic(Q1)
        # point would mix two sampling modes and inflate q1_ic_err on any ripple.
        b.directive(f".meas TRAN q1_ic_calc PARAM {{q1_ve/{P.R5}}}")
        b.directive(".meas TRAN q1_ic AVG Ic(Q1) FROM=190m TO=200m")
        # Flag disagreement: |q1_ic - q1_ic_calc| / q1_ic_calc must stay under 10%.
        b.directive(".meas TRAN q1_ic_err PARAM {abs(q1_ic - q1_ic_calc) / q1_ic_calc}")
        # Settled rail sanity (the bias points depend on them).
        b.directive(".meas TRAN rail_pos AVG V(+15V) FROM=190m TO=200m")
        b.directive(".meas TRAN rail_neg AVG V(-15V) FROM=190m TO=200m")
    elif active_analysis == "stage6_vos":
        # Stress 3b: U2 input offset (Vos) injection. A 500uV DC source sits in
        # series at U2's non-inverting input; the 213.8x recovery gain multiplies
        # it to ~107mV DC at u2_out. C4 blocks this from v_out, but it stresses U2
        # headroom. Run the same signal-killed transient as the op variant and read
        # the SETTLED DC at u2_out over the 190-200ms tail: it must stay within
        # U2_VOS_OUT_WINDOW (+/-150mV = the bench-documented 20-150mV typical band).
        # The recovery GAIN is unaffected by Vos (gain is an AC property), so this
        # variant only adds the DC-offset stress read; the AC gain stays in the ac
        # variant. (Run as .tran because the real PSU is degenerate at .op.)
        b.directive(".tran 0 200m 0 2u")
        b.directive(".meas TRAN u2_out_dc_vos AVG V(u2_out) FROM=190m TO=200m")
        # Context: the U2 + input node now carries the injected offset.
        b.directive(".meas TRAN u2_inpos_vos AVG V(u2_in_pos) FROM=190m TO=200m")
        b.directive(".meas TRAN rail_pos AVG V(+15V) FROM=190m TO=200m")
        b.directive(".meas TRAN rail_neg AVG V(-15V) FROM=190m TO=200m")
    elif active_analysis == "lo_beta":
        # Stress 3c: BD139 low-beta corner (BF=40, datasheet hFE min). The emitter
        # degeneration (R5=68) + stiff base bias make the Q1 bias point largely
        # beta-independent, so the SAME q1_ve / q1_ic windows must still pass; if
        # they fail at BF=40 the bias design is not beta-independent. Same
        # signal-killed transient + 190-200ms tail read as the op variant.
        b.directive(".tran 0 200m 0 2u")
        b.directive(".meas TRAN q1_ve AVG V(q1_e) FROM=190m TO=200m")
        # Ic(Q1) (collector current through the BJT), NOT I(R5) (emitter current
        # Ie=Ve/R5). At BF=40 the base current is ~2.4% of Ie, exactly the corner
        # where Ic and Ie diverge -- so measure the real collector current to match
        # the op netlist's q1_ic = Ic(Q1) and gate the genuine quiescent Ic.
        b.directive(".meas TRAN q1_ic AVG Ic(Q1) FROM=190m TO=200m")
        b.directive(".meas TRAN rail_pos AVG V(+15V) FROM=190m TO=200m")
        b.directive(".meas TRAN rail_neg AVG V(-15V) FROM=190m TO=200m")
    elif active_analysis == "ac":
        # Recovery gain + wet HPF corner. PSU SINE sources have no AC spec (AC=0),
        # so only V1 (AC 1) drives the sweep. .ac dec 100 20 20k.
        b.directive(".ac dec 100 20 20k")
        # U1 input buffer is a unity-gain follower: V(u1_buf) must track V(vin).
        # A dead/mis-wired U1 (gain stage, or out of loop) would not pass signal at
        # unity -- nothing else in the suite checks the front-end buffer's gain.
        b.directive(".meas AC u1_buf_gain FIND mag(V(u1_buf)/V(vin)) AT=1k")
        b.directive(".meas AC recov_gain FIND mag(V(u2_out)/V(u2_in_pos)) AT=1k")
        # Wet HPF -3dB corner. In the FULL circuit the absolute hpf_out level is
        # shaped by the tank transfer (a resonant "drip" peak near 2kHz) on top of
        # the R6/C4 high-pass, so a 0.7079*ref crossing on V(hpf_out) alone does
        # NOT isolate the HPF corner (it finds the resonance flank). Measure the
        # R6/C4 high-pass TRANSFER directly - V(hpf_out)/V(u2_out) - which removes
        # the tank+U2 shaping and leaves the clean first-order HPF whose corner is
        # 1/(2*pi*R6*C4) = 1/(2*pi*5.6k*100n) = 284Hz. Reference at 5kHz (flat
        # passband of the HPF transfer), find the rising 0.7079*ref crossing.
        b.directive(".meas AC hpf_ref  FIND mag(V(hpf_out)/V(u2_out)) AT=5k")
        b.directive(".meas AC hpf_m3db WHEN mag(V(hpf_out)/V(u2_out))=hpf_ref*0.7079 RISE=1")
        # Recovery-stage gain end-to-end, in dB. This measures the SAME thing as
        # recov_gain above (V(u2_out)/V(u2_in_pos), the 214x non-inverting stage),
        # just expressed in dB so it can be pass-checked against RECOV_GAIN_DB_SIM /
        # CHAIN_GAIN_DB_WINDOW (44.6-48.6 dB). It deliberately does NOT measure the
        # full vin->v_out chain: the dry path attenuates (~-5 dB) and the wet path
        # is shaped by the tank+HPF, so 20*log10(V(v_out)/V(vin)) is ~15-21 dB, not
        # the 46.6 dB recovery gain -- a vin->v_out measurement would fail the
        # recovery-gain window. Reference level at 1kHz for context.
        b.directive(".meas AC recov_lvl FIND V(u2_out) AT=1k")
        b.directive(".meas AC recov_gain_db FIND 20*log10(V(u2_out)/V(u2_in_pos)) AT=1k")
    elif active_analysis == "tran":
        # Output peak + no-oscillation. 100mVpk 1kHz signal.
        #
        # osc_ratio compares a late-window RMS to an early-window RMS: >1 means the
        # signal is GROWING (oscillation/instability), <=1.05 means stable. In the
        # FULL circuit the start-up transient lasts ~40ms (the real PSU bulk caps
        # charge, and the high-L spring tank - L_tank_out=2H, L_tank_mech=500m -
        # rings up to steady state). A 0..10ms "early" window therefore sits in the
        # transient and reads LOW, inflating the ratio to ~1.17 even though the
        # signal is dead stable afterwards. So BOTH windows are placed past the
        # settle: early=40..50ms, late=90..100ms. (Probed to 400ms: v_out RMS is
        # flat-to-slightly-decreasing 0.4381 -> 0.4377, i.e. no growth.)
        b.directive(".tran 0 100m 0 5u")
        # LTSpice 26 silently ignores FROM/TO on MAX .meas; bare MAX is used
        # deliberately (FROM/TO qualifiers would be a no-op and misleading).
        b.directive(".meas TRAN vout_pk  MAX abs(V(v_out))")
        b.directive(".meas TRAN rms_early RMS V(v_out) FROM=40m TO=50m")
        b.directive(".meas TRAN rms_late  RMS V(v_out) FROM=90m TO=100m")
        b.directive(".meas TRAN osc_ratio PARAM rms_late/rms_early")
    elif active_analysis in POT_SWEEP_VARIANTS:
        # Pot-extreme sweep (GitHub issue #43). 200ms tran, 100mVpk 1kHz signal
        # (V1 already set to V1_SINE_NORMAL above). 200ms gives the high-L tank +
        # real-PSU start-up transient time to settle before the 190-200ms tail
        # windows. Each variant gates the failure mode its pot extreme exposes.
        #
        # Level measures use MAX abs(). NOTE: LTSpice 26 silently ignores FROM/TO
        # on MAX, so the FROM=/TO= qualifiers below do not window the measurement —
        # the full 0–200ms run is always captured. AVG is used for DC-bias reads
        # where FROM/TO windowing works correctly.
        b.directive(".tran 0 200m 0 5u")
        if active_analysis == "dwell_min":
            # Dwell at 0% (CCW) -> RV1a≈0 (wiper shunted to GND) = MINIMUM wet
            # drive. The dry path is independent. The DRY path (u1_buf->Rdry->
            # mix_dry) is independent of Dwell and must still pass. At Mix noon the
            # dry signal reaches v_out at ~0.1V pk.
            b.directive(".meas TRAN dwell_min_vout MAX abs(V(v_out)) FROM=190m TO=200m")
            b.directive(".meas TRAN dwell_min_dry  MAX abs(V(mix_dry)) FROM=190m TO=200m")
        elif active_analysis == "dwell_max":
            # Dwell at 100% (CW) -> RV1b≈0 (wiper pulled to u1_buf) = MAXIMUM wet
            # drive. Check U2 output does not hard-clip. dwell_max_wiper_pk gates
            # the AC level at the wiper, which IS what the Dwell position controls.
            b.directive(".meas TRAN dwell_max_u2_pk MAX abs(V(u2_out)) FROM=50m TO=200m")
            b.directive(".meas TRAN dwell_max_wiper_pk MAX abs(V(rv1_wiper)) FROM=190m TO=200m")
        elif active_analysis == "mix_ccw":
            # Mix at 0% -> RV2a≈0, the wiper (mix_node) ties to mix_dry: 100% DRY.
            # v_out should carry the dry signal.
            #
            # Wet-chain integrity probe: mix_ccw_wet_ratio = V(mix_wet)/V(hpf_out).
            # These nodes are separated by the real RV3 divider (RV3a=50k series,
            # RV3b=50k||RV2b=100k shunt). At center-wiper the ratio is ~0.40.
            # A broken RV3 wiper, open Rwet_wire, or shorted RV3b all push it
            # outside the window. Cannot be 1.0 by construction -- hpf_out and
            # mix_wet are always separated by RV3a=50k, so this is a genuine test.
            #
            # Previous attempts were tautologies:
            #   v1: V(mix_node)/V(mix_dry) -- RV2a=0.001 hard-shorts both nodes.
            #   v2: V(mix_wet)/V(rv3_wiper) -- Rwet_wire=1mR makes them the same node (to within nV).
            b.directive(".meas TRAN mix_ccw_vout_pk  MAX abs(V(v_out))   FROM=190m TO=200m")
            b.directive(".meas TRAN mix_ccw_wet_src  RMS V(hpf_out)  FROM=190m TO=200m")
            b.directive(".meas TRAN mix_ccw_wet_node RMS V(mix_wet)   FROM=190m TO=200m")
            b.directive(".meas TRAN mix_ccw_wet_ratio PARAM {mix_ccw_wet_node/mix_ccw_wet_src}")
        elif active_analysis == "mix_cw":
            # Mix at 100% -> RV2b≈0, the wiper ties to mix_wet (Tone output): 100%
            # WET. v_out carries the wet (reverb) signal. mix_cw_dry_attn compares
            # the dry-node level to the wiper level: at full-CW the wiper is the
            # wet node, so the dry node sees little of the wiper signal.
            b.directive(".meas TRAN mix_cw_vout_pk   MAX abs(V(v_out))   FROM=50m TO=200m")
            b.directive(".meas TRAN mix_cw_mix_node  MAX abs(V(mix_node)) FROM=190m TO=200m")
            b.directive(".meas TRAN mix_cw_dry_lvl   MAX abs(V(mix_dry))  FROM=190m TO=200m")
            b.directive(".meas TRAN mix_cw_dry_attn  PARAM {mix_cw_dry_lvl/mix_cw_mix_node}")
        elif active_analysis == "dwell_max_mix_cw":
            # Worst-case clip path: Dwell max + Mix full-CW. With this (correct)
            # pot convention Dwell max means RV1b≈0 pulls the wiper to u1_buf =
            # MAXIMUM wet drive (RV1a is the 10k wiper-to-GND leg, not a short to
            # ground). So this combines the loudest wet send (Dwell CW) with the
            # 100%-wet Mix position -- the genuine worst case for U2 headroom. The
            # gate is that v_out (downstream of U3) never exceeds WORST_CASE_PK_MAX
            # and its DC settles back to ~0 (no latch-up).
            b.directive(".meas TRAN worst_case_pk     MAX abs(V(v_out)) FROM=50m TO=200m")
            b.directive(".meas TRAN worst_case_settle AVG V(v_out)      FROM=190m TO=200m")

    b.text(16, 1620,
           "Active analysis: ." + active_analysis +
           ". Regenerate: gen_stage6_full.py {op|ac|tran|dwell_min|dwell_max|mix_ccw|mix_cw|dwell_max_mix_cw|stage6_vos|lo_beta}", 2)

    return b


if __name__ == "__main__":
    import sys
    analysis = sys.argv[1] if len(sys.argv) > 1 else "op"
    base = os.path.dirname(os.path.abspath(__file__))
    b = build(analysis)
    asc = f"{base}/stage_06_full.asc"
    net = f"{base}/stage_06_full.net"
    b.dump(asc, net)
    print(f"wrote {asc} and {net} (analysis={analysis})")
