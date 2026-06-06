#!/usr/bin/env python3
"""
gen_stage5_psu.py - Generate stage_05_psu.asc (+ matching .net sidecar).

Stage 5 of the Ghost Spring reverb build: replace the idealised +/-15V bench
rails (Vpos/Vneg) from Stage 4 with the REAL linear power supply that ships in
the pedal - a center-tapped transformer, a full-wave bridge, bulk filter caps,
and a 78xx/79xx regulator pair.

Delta from Stage 4 (stage_04_input_protect.asc):
  - REMOVE the two ideal sources:
        Vpos +15V 0 15
        Vneg 0   -15V 15
  - ADD the full PSU that PRODUCES the +15V / -15V rails:

        T1 secondary (Triad F-219X, 15-0-15VAC) modelled as two 60Hz SINE
        sources of 21.2V peak (= 15Vrms * sqrt(2)) referenced to the center
        tap, which is GROUND:
            Vsec_p  ac_pos 0  SINE(0 21.2 60)
            Vsec_n  0 ac_neg  SINE(0 21.2 60)   (anti-phase -> ac_neg swings
                                                  opposite ac_pos)

        BR1 = W04G full-wave bridge, 4 x 1N4007 (D-prefix instance names),
        fed DIRECTLY from the AC secondary (no fuse on the AC side):
            DBR1a  ac_pos  pos_rect   (top-half +, ac_pos -> +bus)
            DBR1b  ac_neg  pos_rect   (top-half +, ac_neg -> +bus)
            DBR1c  neg_rect ac_pos    (bottom-half -, -bus -> ac_pos)
            DBR1d  neg_rect ac_neg    (bottom-half -, -bus -> ac_neg)
          With the center tap = GND, this is the standard full-wave bridge off a
          center-tapped winding: pos_rect is the unregulated +ve bus, neg_rect
          the unregulated -ve bus, each ~ +/-(21.2 - 2*Vf) before the cap, held
          up near the peak by the bulk caps.

        Bulk filter + bleed (one set per rail):
            C11  pos_rect 0  2200u      ; +ve bulk filter
            R_bleed1 pos_rect 0  10k    ; bleed
            C12  neg_rect 0  2200u      ; -ve bulk filter
            R_bleed2 neg_rect 0  10k    ; bleed

        Regulators (no LM7815/LM7915 model ships with this LTspice install -
        verified - so we define simple behavioural subckts inline, see below).
        Outputs go to intermediate nodes reg_pos / reg_neg:
            XU4  pos_rect 0 reg_pos  LM78xx   ; +15 out
            XU5  neg_rect 0 reg_neg  LM79xx   ; -15 out

        Regulator output caps + HF bypass on the regulator output pin:
            C13  reg_pos 0  100u
            C17  reg_pos 0  100n
            C14  reg_neg 0  100u
            C18  reg_neg 0  100n

        F2/F3 MF-R050 polyfuses -> modelled as 0.5 ohm series R (a polyfuse is
        just wire until it trips; we test NORMAL operation). They sit on the DC
        RAIL OUTPUT, AFTER the regulator + output cap (reg pin -> +15V/-15V bus),
        so a downstream PCB short trips the fuse and protects the regulator:
            RF2  reg_pos +15V  0.5
            RF3  reg_neg -15V  0.5
          The +15V and -15V nodes are what the rest of the circuit uses.

Everything downstream of the rails (U1/U2/U3, Q1 driver, transformer, tank,
input protection TVS1 + clamp pair) is BYTE-FOR-BYTE the Stage 4 topology and
now draws from the +15V / -15V nodes the PSU produces. Only the supply origin
changes, so any regression bisects cleanly to "swapped ideal rails for the PSU".

Regulator models. No 78xx/79xx subckt ships with the installed LTspice (only
LTC switchers), so we define simple BEHAVIOURAL linear-regulator subckts inline.
The behavioural source models the ~2V dropout and the output clamp:
    LM78xx (positive): OUT = min(V(IN,COM) - 2, +Vout)
    LM79xx (negative): OUT = max(V(IN,COM) + 2, -Vout)
With +21.2V peak filtered to ~+19V on pos_rect (well above 15+2), the +reg sits
on its 15.0V clamp; mirror for the -reg. This reproduces both the .op rail
voltage and the post-regulation ripple rejection (the reg holds 15.0V flat while
the unregulated bus ripples, so output ripple collapses to ~uV).

Analysis variants (ONE active at a time):
  op    : DC operating point - settled rail voltages (Stage 5 green #1/#2)
            rail_pos = V(+15V) in 14.85..15.15
            rail_neg = V(-15V) in -15.15..-14.85
  tran  : 150ms transient, ripple measured FROM=100m TO=120m (Stage 5 green
          #3/#4)
            ripple_pos = PP V(+15V) < 10mVpp
            ripple_neg = PP V(-15V) < 10mVpp

Connectivity strategy is identical to gen_stage4_asc.py: every component pin
gets a FLAG (net label) at its exact pin coordinate, so nets connect by name.
On macOS the LTspice CLI cannot netlist a .asc headlessly, so this script emits
BOTH the .asc schematic and a matching .net sidecar (the file actually
batch-simulated). Both are generated from the same component list so they can
never drift.

Installed-symbol pin offsets (rotation R0) - same as Stage 4:
  res     : (16,16) pinA(top)   , (16,96) pinB(bottom)
  cap     : (16, 0) pinA(top)   , (16,64) pinB(bottom)
  ind     : (16,16) pinA(top)   , (16,96) pinB(bottom)
  diode   : (16, 0) A(anode,top), (16,64) K(cathode,bottom)
  voltage : ( 0,16) plus        , ( 0,96) minus
  npn     : ( 0,48) B(base)     , (64, 0) C(collector) , (64,96) E(emitter)
  UniversalOpamp2 : (-32,16) IN+ , (-32,-16) IN- , (0,-32) V+ , (0,32) V- , (32,0) OUT
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
        """Coupled-inductor (mutual) statement. No schematic symbol exists for
        K; place it as a SPICELINE TEXT directive on the .asc and a card in the
        .net. K<name> L<a> L<b> <coeff>."""
        card = f"{name} {la} {lb} {k}"
        self._atext(x, y, "!" + card)
        self.net.append(card)

    def reg(self, name, subckt, x, y, nin, ncom, nout):
        """Linear-regulator instance referencing an inline .subckt. No symbol
        ships for a generic 78xx, so place a block symbol stand-in (a res
        outline would mislead); we emit a TEXT label on the .asc at (x,y) and
        the real X-card in the .net. Pins: IN COM OUT."""
        self._atext(x, y, f"{name}: {subckt}  IN={nin} COM={ncom} OUT={nout}", 2)
        # net card: X<name> <in> <com> <out> <subckt>
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
        net = [f"* {asc_path}",
               "* Generated by gen_stage5_psu.py for installed LTspice 26 symbols.",
               ".OPTIONS ALLOW_AMBIGUOUS_MODELS"]
        net += self.net
        net.append(".model D D")
        net.append(r".lib C:\users\crossover\AppData\Local\LTspice\lib\cmp\standard.dio")
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


def _low_mains_sine():
    """Return the T1 secondary SINE() string scaled to the low-mains corner.

    Nominal is VSEC_SINE = 'SINE(0 21.2 60)' (21.2Vpk = 15Vrms*sqrt(2)). The
    low-mains variant scales the peak amplitude by PSU_LOW_MAINS_VFACTOR (0.90,
    = 108V on a 120V nominal mains) and leaves offset/frequency untouched, so the
    bridge+caps see a 10%-low secondary. Parses the nominal string so a change to
    VSEC_SINE flows here (single source of truth)."""
    inner = P.VSEC_SINE[P.VSEC_SINE.index("(") + 1:P.VSEC_SINE.rindex(")")]
    off, peak, freq = inner.split()
    scaled = float(peak) * P.PSU_LOW_MAINS_VFACTOR
    return "SINE(%s %g %s)" % (off, scaled, freq)


def build(active_analysis="op"):
    """active_analysis in {'op','tran','psu_low_mains'}. Only ONE analysis active
    at a time. psu_low_mains is the 'tran' variant with the T1 secondary scaled to
    the 108V (10%-low) mains corner; it runs the SAME ripple/rail checks."""
    b = Build()
    b.text(16, -40, "Ghost Spring Stage 5 - +/-15V Linear Power Supply (T1, BR1, C11/C12, U4 LM7815, U5 LM7915)", 4)
    b.text(16, 8, "Stage 4 signal path UNCHANGED, now fed from the real PSU. T1 15-0-15VAC (two SINE(0 21.2 60), center tap=GND) -> BR1 (4x 1N4007) -> C11/C12 2200u bulk + 10k bleed -> U4 LM7815 / U5 LM7915 -> C13/C14 100u + C17/C18 100n -> F2/F3 polyfuses (0.5ohm) on DC rails -> +/-15V rails. Connectivity by net labels (FLAG at each pin).", 2)

    # ====================================================================
    # === STAGE 5: +/-15V LINEAR POWER SUPPLY (replaces ideal Vpos/Vneg) ==
    # ====================================================================
    # T1 secondary: 15-0-15VAC, center tap = GND. Two anti-phase 60Hz SINE
    # sources, 21.2V peak = 15Vrms * sqrt(2). Vsec_n is written 0 -> ac_neg so
    # ac_neg swings opposite ac_pos (true center-tapped winding).
    # Low-mains variant scales the secondary peak to the 108V (10%-low) corner;
    # all other analyses use the nominal 21.2Vpk secondary.
    sec_sine = _low_mains_sine() if active_analysis == "psu_low_mains" else P.VSEC_SINE
    b.vsrc("Vsec_p", sec_sine, 64, 1000, "ac_pos", "0")
    b.vsrc("Vsec_n", sec_sine, 224, 1000, "0", "ac_neg")
    if active_analysis == "psu_low_mains":
        b.text(64, 960, "T1 secondary scaled to 108V (10%% low mains, 0.90x). Center tap = GND.", 2)
    else:
        b.text(64, 960, "T1 Triad F-219X 15-0-15VAC. Center tap = GND. 21.2Vpk = 15Vrms*sqrt(2).", 2)

    # BR1 = W04G full-wave bridge off the center-tapped winding, 4x 1N4007.
    # D-prefix instance names (DBR1a..d). pos_rect = +ve bus, neg_rect = -ve bus.
    # The AC secondary feeds the bridge DIRECTLY (no fuse on the AC side).
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
    b.text(1320, 840, "C13/C14 100u reg out caps, C17/C18 100n HF bypass.", 2)

    # F2/F3 MF-R050 polyfuses -> 0.5 ohm series R (RF2/RF3 in SPICE).
    # On the DC RAIL OUTPUT (reg pin -> +15V/-15V bus), AFTER the regulator
    # and its output cap, so a downstream PCB short trips the fuse and
    # protects the regulator (per parts-spec F2/F3, BOM, build-plan, builder
    # guide). Modeled as 0.5 ohm series R; MF-R050 hold resistance ~0.7 ohm.
    # SPICE reserves the F prefix for current-controlled sources, so the
    # resistor instances are RF2/RF3 (F2/F3 designators live on the label).
    b.res("RF2", P.RF2, 1500, 880, "reg_pos", "+15V")
    b.res("RF3", P.RF3, 1500, 1080, "reg_neg", "-15V")
    b.text(1500, 840, "F2/F3 MF-R050 polyfuse = 0.5ohm on DC rail (RF2/RF3).", 2)

    # Inline regulator subckts (no 78xx/79xx ships with installed LTspice).
    b.subckt(LM78XX_SUBCKT)
    b.subckt(LM79XX_SUBCKT)

    # ====================================================================
    # === STAGE 4 SIGNAL PATH (UNCHANGED) - now fed from the PSU rails ====
    # ====================================================================
    # Extra rail decoupling kept from Stage 4 (C5-C8 100n, C15/C16 10u bulk).
    b.cap("C15", P.C15, 1580, 880, "+15V", "0")
    b.cap("C16", P.C16, 1580, 1080, "-15V", "0")
    b.cap("C5", P.C5, 1700, 880, "+15V", "0")
    b.cap("C6", P.C6, 1700, 1080, "-15V", "0")
    b.cap("C7", P.C7, 1820, 880, "+15V", "0")
    b.cap("C8", P.C8, 1820, 1080, "-15V", "0")

    # Input source. Normal 100mVpk; the PSU stages do not drive the input.
    b.vsrc("V1", P.V1_SINE_NORMAL, 64, 160, "vin", "0", value2=P.V1_AC_TOKEN)

    # TVS1 at the jack (vin -> 0), two zeners back-to-back (cathodes at tvs_mid).
    b.diode("DTVS1a", "BZX84C15L", 64, 400, "vin", "tvs_mid")
    b.diode("DTVS1b", "BZX84C15L", 64, 528, "0", "tvs_mid")

    # Input buffer U1 front-end (C_in, R1, clamp pair: unchanged from MVP).
    b.cap("C_in", P.C_IN, 160, 144, "vin", "u1_pos")
    b.res("R1", P.R1, 280, 144, "u1_pos", "0")
    b.diode("Dclamp_p", P.D_1N4148, 400, 96, "u1_pos", "+15V")
    b.diode("Dclamp_n", P.D_1N4148, 400, 224, "-15V", "u1_pos")
    b.opa("U1", 560, 200, "u1_pos", "u1_out", "+15V", "-15V", "u1_out")
    b.res("R2", P.R2, 640, 144, "u1_out", "u1_buf")

    # Dwell pot divider. RV1a is the wiper-to-GND half (a = position×total),
    # RV1b is the signal-to-wiper half (b = (1-position)×total). At CW (max
    # Dwell) a≈total, b≈0 -> wiper ≈ u1_buf = MAXIMUM wet drive.
    b.res("RV1a", P.RV1A, 760, 60, "rv1_wiper", "0")
    b.res("RV1b", P.RV1B, 760, 180, "u1_buf", "rv1_wiper")

    # BD139 discrete driver (unchanged from Stage 4).
    b.cap("C_drive", P.C_DRIVE, 880, 144, "rv1_wiper", "q1_drv")
    b.res("R3b", P.R3B, 1000, 40, "+15V", "q1_base")
    b.res("R4", P.R4, 1000, 200, "q1_base", "0")
    b.res("R3", P.R3, 880, 300, "q1_drv", "q1_base")
    b.npn("Q1", "BD139", 1140, 360, "q1_c", "q1_base", "q1_e")
    b.res("R5", P.R5, 1140, 520, "q1_e", "0")
    b.cap("C2", P.C2, 1280, 520, "q1_e", "0")
    b.diode("D3", P.D_1N4148, 1140, 220, "q1_c", "+15V")

    # REB3S driver transformer (unchanged).
    b.ind("L1", P.L1, 1140, 60, "+15V", "q1_c")
    b.ind("L2", P.L2, 1300, 60, "tank_in", "0")
    b.kcouple("K1", "L1", "L2", P.K1, 1280, 200)

    # Spring tank RLC (unchanged).
    b.res("R_tank_in", P.R_TANK_IN, 1300, 240, "tank_in", "0")
    b.ind("L_tank", P.L_TANK, 1420, 60, "tank_in", "tank_mid")
    b.res("R_tank_mech", P.R_TANK_MECH, 1540, 240, "tank_mid", "tk_a")
    b.ind("L_tank_mech", P.L_TANK_MECH, 1540, 360, "tk_a", "tk_b")
    b.cap("C_tank_mech", P.C_TANK_MECH, 1540, 480, "tk_b", "0")
    b.res("R_tank_out", P.R_TANK_OUT, 1660, 60, "tank_mid", "tank_out")
    b.ind("L_tank_out", P.L_TANK_OUT, 1660, 240, "tank_out", "0")

    # Recovery preamp U2 (unchanged).
    b.cap("C3", P.C3, 1780, 144, "tank_out", "u2_in_pos")
    b.res("Rbias", P.RBIAS, 1900, 240, "u2_in_pos", "0")
    b.opa("U2", 2060, 200, "u2_in_pos", "u2_inv", "+15V", "-15V", "u2_out")
    b.res("Ri", P.RI, 2000, 360, "u2_inv", "0")
    b.res("Rf", P.RF, 2120, 360, "u2_out", "u2_inv")

    # Post-recovery HPF (unchanged).
    b.cap("C4", P.C4, 2240, 144, "u2_out", "hpf_out")
    b.res("R6", P.R6, 2360, 240, "hpf_out", "0")

    # Tone RV3, Mix RV2, output buffer U3 (unchanged).
    b.res("RV3a", P.RV3A, 2180, 600, "hpf_out", "rv3_wiper")
    b.res("RV3b", P.RV3B, 2180, 720, "rv3_wiper", "0")
    # --- Mix RV2: 3-terminal PASSIVE BLEND (not a volume knob). ---------------
    # Dry (u1_buf)->Rdry->RV2 pin1 (CCW)==mix_dry; Wet (rv3_wiper)->RV2 pin3
    # (CW)==mix_wet; wiper (pin2)->U3==mix_node. C_bright bridges pin1<->pin3
    # (full pot). Wet ties DIRECTLY to mix_wet (no Rwet short). See parts-spec
    # "Mix Stage Topology". Full-CCW=100% dry, full-CW=100% wet.
    b.res("Rdry", P.RDRY, 640, 360, "u1_buf", "mix_dry")
    b.res("RV2a", P.RV2A, 2300, 760, "mix_dry", "mix_node")   # CCW half of pot
    b.res("RV2b", P.RV2B, 2300, 880, "mix_node", "mix_wet")   # CW half of pot
    b.cap("C_bright", P.C_BRIGHT, 2420, 760, "mix_dry", "mix_wet")  # bright cap across full pot
    b.res("Rwet_wire", "0", 2300, 600, "rv3_wiper", "mix_wet")  # direct wire, modelled 0 ohm
    b.opa("U3", 2560, 900, "mix_node", "u3_out", "+15V", "-15V", "u3_out")
    b.res("R7", P.R7, 2640, 844, "u3_out", "v_out")
    b.res("Rload", P.RLOAD, 2760, 844, "v_out", "0")
    b.text(2640, 820, "J2 -> MC100 input (47k load)", 2)

    # === Models ===
    b.directive(f".model BD139 {BD139_MODEL}")
    b.directive(f".model BZX84C15L {BZX84C15L_MODEL}")
    b.directive(f".model DN4007 {DN4007_MODEL}")

    # === Analysis (only ONE active at a time) ===
    if active_analysis == "op":
        # Stage 5 green #1/#2: SETTLED DC rail voltages.
        # NOTE: a true .op is meaningless for a rectifier+filter PSU because the
        # solver freezes the SINE sources at their t=0 value (0V), so the bridge
        # sees no drive and the caps never charge. "After caps settle" therefore
        # means a transient run measured in a late window - exactly what a DMM
        # reads on the bench. We average V(+15V)/V(-15V) over 100ms..120ms.
        b.directive(".tran 0 150m 0 10u")
        b.directive(".meas TRAN rail_pos AVG V(+15V) FROM=100m TO=120m")
        b.directive(".meas TRAN rail_neg AVG V(-15V) FROM=100m TO=120m")
        # Unregulated bus headroom (sanity: > 17V so the reg has its 2V dropout).
        b.directive(".meas TRAN unreg_pos AVG V(pos_rect) FROM=100m TO=120m")
        b.directive(".meas TRAN unreg_neg AVG V(neg_rect) FROM=100m TO=120m")
        # Cheap downstream bias regression.
        b.directive(".meas TRAN q1_ve AVG V(q1_e) FROM=100m TO=120m")
        b.directive(".meas TRAN off_u3 AVG V(v_out) FROM=100m TO=120m")
    elif active_analysis in ("tran", "psu_low_mains"):
        # Stage 5 green #3/#4: ripple on the regulated rails after caps settle.
        # 150ms run, ripple window 100ms..120ms (>= 1 full 120Hz ripple period).
        # psu_low_mains runs the IDENTICAL checks on a 108V (10%-low) secondary:
        # the regulators must still hit +/-15V and ripple stays < 10mVpp, AND the
        # unregulated bus must keep its dropout headroom on the sagged mains.
        b.directive(".tran 0 150m 0 10u")
        b.directive(".meas TRAN ripple_pos PP V(+15V) FROM=100m TO=120m")
        b.directive(".meas TRAN ripple_neg PP V(-15V) FROM=100m TO=120m")
        # Also report the settled mean and the unregulated-bus ripple for context.
        b.directive(".meas TRAN rail_pos_avg AVG V(+15V) FROM=100m TO=120m")
        b.directive(".meas TRAN rail_neg_avg AVG V(-15V) FROM=100m TO=120m")
        b.directive(".meas TRAN unreg_pos_pp PP V(pos_rect) FROM=100m TO=120m")
        b.directive(".meas TRAN unreg_neg_pp PP V(neg_rect) FROM=100m TO=120m")
        if active_analysis == "psu_low_mains":
            # On low mains the unregulated bus sags toward the dropout floor, so
            # guard rail regulation AND unreg-bus headroom on the sagged supply.
            b.directive(".meas TRAN rail_pos AVG V(+15V) FROM=100m TO=120m")
            b.directive(".meas TRAN rail_neg AVG V(-15V) FROM=100m TO=120m")
            b.directive(".meas TRAN unreg_pos AVG V(pos_rect) FROM=100m TO=120m")
            b.directive(".meas TRAN unreg_neg AVG V(neg_rect) FROM=100m TO=120m")

    b.text(16, 1620,
           "Active analysis: ." + active_analysis +
           ". Regenerate with gen_stage5_psu.py {op|tran|psu_low_mains} -- ONE analysis at a time.", 2)

    return b


if __name__ == "__main__":
    import sys
    analysis = sys.argv[1] if len(sys.argv) > 1 else "op"
    base = "/Users/bubblegum/projects/le-ton-juste/docs/reverb-tank/stages"
    b = build(analysis)
    asc = f"{base}/stage_05_psu.asc"
    net = f"{base}/stage_05_psu.net"
    b.dump(asc, net)
    print(f"wrote {asc} and {net} (analysis={analysis})")
