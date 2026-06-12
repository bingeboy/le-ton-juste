#!/usr/bin/env python3
"""
gen_stage4_asc.py - Generate stage_04_input_protect.asc (+ matching .net sidecar).

Stage 4 of the Ghost Spring reverb build: promote the input front-end to its
final form and add the ESD TVS across the input jack.

Delta from Stage 3 (stage_03_transformer.asc):
  - CONFIRM (unchanged, already present since the MVP and carried through
    Stages 2/3):
      * C_in    1u   : vin -> u1_pos   (first in the signal path, before R1)
      * R1      1Meg : u1_pos -> 0      (SHUNT after C_in, NOT in series)
      * Dclamp_p 1N4148 : anode u1_pos -> cathode +15V  (positive overvoltage)
      * Dclamp_n 1N4148 : anode -15V    -> cathode u1_pos (negative overvoltage)
  - ADD TVS1 (SMBJ15CA bidirectional) across the input jack tip->sleeve, i.e.
    across the V1 source node `vin` -> GND. A bidirectional TVS is modelled as
    two BZX84C15L zeners back-to-back so that EITHER polarity is clamped at one
    diode forward drop above the 15V zener knee:
      * TVS1a : anode `vin`  -> cathode `tvs_mid`   (BZX84C15L)
      * TVS1b : anode `0`    -> cathode `tvs_mid`   (BZX84C15L)
    With the two cathodes tied at `tvs_mid`, a positive `vin` excursion is held
    by TVS1a's zener BV (15V) in series with TVS1b's forward drop (~0.7V) ->
    ~+15.7V clamp; a negative excursion is the mirror -> ~-15.7V. This is the
    standard back-to-back-zener model of a bidirectional TVS and gives the same
    +/-16V-max clamp window the real SMBJ15CA holds. The TVS catches nanosecond
    ESD that the 1N4148 clamp pair is too slow to absorb.

    NOTE the TVS sits at the JACK (node `vin`), BEFORE C_in. The 1N4148 clamp
    pair sits at the OP-AMP input (node `u1_pos`), AFTER C_in. They protect two
    different nodes:
      * TVS1 protects the jack / the whole front end from the fast ESD strike.
      * Dclamp_p/n protect the U1 FET gate from slow DC overloads that make it
        through C_in.

Zener model: BZX84C15L is a 15V, 250mW zener. We define it explicitly in the
deck (.model BZX84C15L D(BV=15 ...)) so the +/-16V clamp window is exact and
self-contained, exactly as the BD139 transistor model is defined inline. This
does not depend on whether the installed standard.dio carries the part.

Analysis variants (ONE active at a time):
  op            : idle reverse-bias check on the clamp diodes (Stage 4 green #1)
  overload      : 40Vpp (20Vpk) transient overload (V1 = SINE(0 20 1k)); confirm
                  the U1(+) node is clamped to +/-16V max (Stage 4 green #2)
  tran          : normal-level transient (V1 = SINE(0 100m 1k)); driver/output
                  regression (D3 idle, no clipping, no oscillation)
  ac            : Stage 3 resonance regression (the "drip")
  ac_regression : Stage 1 recovery-gain + HPF-corner regression

Everything except the TVS1 addition (and the analysis directive) is BYTE-FOR-BYTE
the Stage 3 topology, so any regression bisects cleanly to "added TVS1".

Connectivity strategy is identical to gen_stage3_asc.py: every component pin
gets a FLAG (net label) at its exact pin coordinate, so nets connect by name.

On macOS the LTspice CLI cannot netlist a .asc headlessly, so this script emits
BOTH the .asc schematic and a matching .net sidecar (the file the ltspice-mcp
daemon batch-simulates). Both are generated from the same component list so they
can never drift.

Installed-symbol pin offsets (rotation R0):
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

# BZX84C15L: 15V 250mW zener used as the back-to-back pair modelling the
# SMBJ15CA bidirectional TVS.
BZX84C15L_MODEL = P.BZX84C15L_MODEL


class Build:
    def __init__(self):
        self.asc = ["Version 4", "SHEET 1 2400 1600"]
        self.net = []          # SPICE element/card lines
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
               "* Generated by gen_stage4_asc.py for installed LTspice 26 symbols.",
               ".OPTIONS ALLOW_AMBIGUOUS_MODELS"]
        net += self.net
        net.append(".model D D")
        net.append(r".lib standard.dio")
        net.append("* BD139 driver model + BZX84C15L zener model + analysis directives")
        for card in self.directives:
            net.append(card)
        net.append(".lib UniversalOpAmp2.lib")
        net.append(".backanno")
        net.append(".end")
        open(net_path, "w").write("\n".join(net) + "\n")


def build(active_analysis="op"):
    """active_analysis in {'op','overload','tran','ac','ac_regression'}.
    Only ONE analysis active at a time. Stage 4's primary analyses are .op
    (idle clamp reverse-bias) and the 'overload' .tran (40Vpp/20Vpk clamp window)."""
    b = Build()
    b.text(16, -40, "Ghost Spring Stage 4 - Input Protection (C_in, R1, Dclamp+/-, TVS1)", 4)
    b.text(16, 8, "Stage 3 + TVS1 (SMBJ15CA) across the input jack vin->0, modelled as two BZX84C15L zeners back-to-back (cathodes tied at tvs_mid). C_in/R1/Dclamp_p/Dclamp_n confirmed unchanged from MVP. Connectivity by net labels (FLAG at each pin).", 2)

    # === Power & input source (unchanged from Stage 3) ===
    b.vsrc("Vpos", P.VRAIL_IDEAL, 64, 1200, "+15V", "0")
    b.vsrc("Vneg", P.VRAIL_IDEAL, 224, 1200, "0", "-15V")
    b.cap("C15", P.C15, 384, 1200, "+15V", "0")
    b.cap("C16", P.C16, 512, 1200, "-15V", "0")
    b.cap("C5", P.C5, 640, 1200, "+15V", "0")
    b.cap("C6", P.C6, 768, 1200, "-15V", "0")
    b.cap("C7", P.C7, 896, 1200, "+15V", "0")
    b.cap("C8", P.C8, 1024, 1200, "-15V", "0")
    b.text(64, 1160, "Power: idealised +/-15V. C5-C8 100n decoupling, C15/C16 10u bulk.", 2)

    # Input source. Normal 100mVpk; the 'overload' analysis swaps to 40Vpp (20Vpk).
    vin_value = P.V1_SINE_OVERLOAD if active_analysis == "overload" else P.V1_SINE_NORMAL
    b.vsrc("V1", vin_value, 64, 160, "vin", "0", value2=P.V1_AC_TOKEN)

    # === STAGE 4: TVS1 at the jack (vin -> 0), modelled as two zeners B2B ===
    # Placed to the LEFT/below the source, between vin and 0, BEFORE C_in.
    # TVS1a: anode vin -> cathode tvs_mid ; TVS1b: anode 0 -> cathode tvs_mid.
    # Cathodes tied at tvs_mid -> either polarity clamped at BV(15) + Vf(~0.7).
    b.diode("DTVS1a", "BZX84C15L", 64, 400, "vin", "tvs_mid")
    b.diode("DTVS1b", "BZX84C15L", 64, 528, "0", "tvs_mid")
    b.text(160, 420, "TVS1 = SMBJ15CA (two BZX84C15L B2B): clamps vin to +/-~15.7V on ESD.", 2)

    # === Input buffer U1 front-end (C_in, R1, clamp pair: unchanged from MVP) ===
    b.cap("C_in", P.C_IN, 160, 144, "vin", "u1_pos")       # first in path, before R1
    b.res("R1", P.R1, 280, 144, "u1_pos", "0")          # SHUNT after C_in, not series
    b.diode("Dclamp_p", P.D_1N4148, 400, 96, "u1_pos", "+15V")   # +overvoltage clamp
    b.diode("Dclamp_n", P.D_1N4148, 400, 224, "-15V", "u1_pos")  # -overvoltage clamp
    b.opa("U1", 560, 200, "u1_pos", "u1_out", "+15V", "-15V", "u1_out")
    b.res("R2", P.R2, 640, 144, "u1_out", "u1_buf")

    # === Dwell pot divider (unchanged) ===
    # RV1a is the wiper-to-GND half; RV1b is the signal-to-wiper half. This
    # matches stage_06_full and builder-guide.md: GND->lug1(CCW)=RV1a rv1_wiper 0,
    # dry(u1_buf)->lug3(CW)=RV1b u1_buf rv1_wiper. At CW the wiper sits on u1_buf
    # (max drive); at CCW it is shunted to GND (min drive).
    b.res("RV1a", P.RV1A, 760, 60, "rv1_wiper", "0")
    b.res("RV1b", P.RV1B, 760, 180, "u1_buf", "rv1_wiper")

    # === BD139 discrete driver (unchanged from Stage 3) ===
    b.cap("C_drive", P.C_DRIVE, 880, 144, "rv1_wiper", "q1_drv")
    b.res("R3b", P.R3B, 1000, 40, "+15V", "q1_base")
    b.res("R4", P.R4, 1000, 200, "q1_base", "0")
    b.res("R3", P.R3, 880, 300, "q1_drv", "q1_base")
    b.npn("Q1", "BD139", 1140, 360, "q1_c", "q1_base", "q1_e")
    b.res("R5", P.R5, 1140, 520, "q1_e", "0")
    b.cap("C2", P.C2, 1280, 520, "q1_e", "0")
    b.diode("D3", P.D_1N4148, 1140, 220, "q1_c", "+15V")

    # === REB3S driver transformer (unchanged from Stage 3) ===
    b.ind("L1", P.L1, 1140, 60, "+15V", "q1_c")
    b.ind("L2", P.L2, 1300, 60, "tank_in", "0")
    b.kcouple("K1", "L1", "L2", P.K1, 1280, 200)

    # === Spring tank RLC (unchanged from Stage 3) ===
    b.res("R_tank_in", P.R_TANK_IN, 1300, 240, "tank_in", "0")
    b.ind("L_tank", P.L_TANK, 1420, 60, "tank_in", "tank_mid")
    b.res("R_tank_mech", P.R_TANK_MECH, 1540, 240, "tank_mid", "tk_a")
    b.ind("L_tank_mech", P.L_TANK_MECH, 1540, 360, "tk_a", "tk_b")
    b.cap("C_tank_mech", P.C_TANK_MECH, 1540, 480, "tk_b", "0")
    b.res("R_tank_out", P.R_TANK_OUT, 1660, 60, "tank_mid", "tank_out")
    b.ind("L_tank_out", P.L_TANK_OUT, 1660, 240, "tank_out", "0")

    # === Recovery preamp U2 (unchanged) ===
    b.cap("C3", P.C3, 1780, 144, "tank_out", "u2_in_pos")
    b.res("Rbias", P.RBIAS, 1900, 240, "u2_in_pos", "0")
    b.opa("U2", 2060, 200, "u2_in_pos", "u2_inv", "+15V", "-15V", "u2_out")
    b.res("Ri", P.RI, 2000, 360, "u2_inv", "0")
    b.res("Rf", P.RF, 2120, 360, "u2_out", "u2_inv")

    # === Post-recovery HPF (unchanged) ===
    b.cap("C4", P.C4, 2240, 144, "u2_out", "hpf_out")
    b.res("R6", P.R6, 2360, 240, "hpf_out", "0")

    # === Tone RV3, Mix RV2, output buffer U3 (unchanged) ===
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
    b.res("Rwet_wire", P.RWET_WIRE, 2300, 600, "rv3_wiper", "mix_wet")  # direct hookup wire, modelled 1mΩ (LTspice rejects R=0)
    b.opa("U3", 2560, 900, "mix_node", "u3_out", "+15V", "-15V", "u3_out")
    b.res("R7", P.R7, 2640, 844, "u3_out", "v_out")
    b.res("Rload", P.RLOAD, 2760, 844, "v_out", "0")
    b.text(2640, 820, "J2 -> MC100 input (47k load)", 2)

    # === Models ===
    b.directive(f".model BD139 {BD139_MODEL}")
    b.directive(f".model BZX84C15L {BZX84C15L_MODEL}")

    # === Analysis (only ONE active at a time) ===
    if active_analysis == "op":
        # Stage 4 green #1: clamp diodes reverse-biased at idle (< 1uA).
        b.directive(".op")
        b.directive(".meas OP clamp_p_i FIND I(Dclamp_p)")
        b.directive(".meas OP clamp_n_i FIND I(Dclamp_n)")
        # Idle TVS leakage (each zener reverse-biased ~0V across the pair).
        b.directive(".meas OP tvs_a_i FIND I(DTVS1a)")
        b.directive(".meas OP tvs_b_i FIND I(DTVS1b)")
        b.directive(".meas OP vin_idle FIND V(vin)")
        # Carry the bias-point sanity checks too (cheap regression).
        b.directive(".meas OP q1_ve FIND V(q1_e)")
        b.directive(".meas OP off_u1 FIND V(u1_out)")
        b.directive(".meas OP off_u2 FIND V(u2_out)")
        b.directive(".meas OP off_u3 FIND V(v_out)")
    elif active_analysis == "overload":
        # Stage 4 green #2: 40Vpp (20Vpk) overload -> U1(+) node clamped to +/-16V max,
        # and the clamp diodes MUST conduct (forward current) to prove the clamp
        # actually engages under overload (positive peak forces Dclamp_p, negative
        # peak forces Dclamp_n).
        b.directive(".tran 0 5m 0 10u")
        b.directive(".meas TRAN u1pos_hi MAX V(u1_pos)")
        b.directive(".meas TRAN u1pos_lo MIN V(u1_pos)")
        b.directive(".meas TRAN clamp_p_pk MAX I(Dclamp_p)")
        b.directive(".meas TRAN clamp_n_pk MIN I(Dclamp_n)")
    elif active_analysis == "tran":
        # Normal-level driver/output regression (Stage 1/2 transient checks).
        b.directive(".tran 0 100m 0 1u")
        b.directive(".meas TRAN d3_pk MAX abs(I(D3))")
        b.directive(".meas TRAN drv_pk MAX abs(I(L1))")
        b.directive(".meas TRAN drv_rms RMS I(L1)")
        b.directive(".meas TRAN vout_pk MAX abs(V(v_out))")
        b.directive(".meas TRAN rms_early RMS V(v_out) FROM=0 TO=10m")
        b.directive(".meas TRAN rms_late RMS V(v_out) FROM=90m TO=100m")
        b.directive(".meas TRAN osc_ratio PARAM rms_late/rms_early")
    elif active_analysis == "ac":
        # Stage 3 resonance regression (the "drip").
        b.directive(".ac dec 100 20 20k")
        b.directive(".meas AC tank_pk_lvl MAX V(tank_in)")
        b.directive(".meas AC tank_pk_f   WHEN V(tank_in)=tank_pk_lvl")
        b.directive(".meas AC tank_drive_db FIND 20*log10(V(tank_in)/V(rv1_wiper)) AT=2k")
    elif active_analysis == "ac_regression":
        # Stage 1 regression checks via AC (recovery gain + HPF corner).
        b.directive(".ac dec 100 20 20k")
        b.directive(".meas AC recov_gain FIND mag(V(u2_out)/V(u2_in_pos)) AT=1k")
        b.directive(".meas AC hpf_pb FIND mag(V(hpf_out)/V(u2_out)) AT=5k")
        b.directive(".meas AC hpf_m3db WHEN mag(V(hpf_out)/V(u2_out))=hpf_pb*0.7079 RISE=1")

    b.text(16, 1620,
           "Active analysis: ." + active_analysis +
           ". Regenerate with gen_stage4_asc.py {op|overload|tran|ac|ac_regression} -- ONE analysis at a time.", 2)

    return b


if __name__ == "__main__":
    import sys
    analysis = sys.argv[1] if len(sys.argv) > 1 else "op"
    base = os.path.dirname(os.path.abspath(__file__))
    b = build(analysis)
    asc = f"{base}/stage_04_input_protect.asc"
    net = f"{base}/stage_04_input_protect.net"
    b.dump(asc, net)
    print(f"wrote {asc} and {net} (analysis={analysis})")
