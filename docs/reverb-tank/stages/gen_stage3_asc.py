#!/usr/bin/env python3
"""
gen_stage3_asc.py - Generate stage_03_transformer.asc (+ matching .net sidecar).

Stage 3 of the Ghost Spring reverb build: insert the Accutronics REB3S driver
transformer between Q1's collector and the spring tank, replacing the Stage 2
direct C_drive_out coupling cap.

Delta from Stage 2 (stage_02_driver.asc):
  - KEEP L1 (100mH) in the collector path (+15V -> q1_c). L1 IS the transformer
    primary. It was already the collector DC load in Stage 2.
  - REMOVE C_drive_out (1u, q1_c -> tank_in). The transformer provides galvanic
    isolation, so no DC-blocking cap is needed; in fact there is now NO galvanic
    path at all from the collector to the tank -- only magnetic coupling.
  - ADD L2 (5mH) as the secondary, from tank_in -> 0. The 8R R_tank_in already
    sits tank_in -> 0, so L2 develops the induced drive across the tank input.
  - ADD K1 L1 L2 0.98 -- tight magnetic coupling (REB3S is a tightly wound
    dedicated reverb driver transformer; K~=0.98, not a perfect 1.0).

Why the peak lands ~2-3 kHz: the primary inductance L1 (100mH) reflected through
the turns ratio together with the secondary leakage/magnetizing inductance and
the tank input impedance (8R resistive + L_tank 15mH + the mechanical resonator)
forms a band-pass that peaks in the low-kHz "drip" band. L1/L2 = 100m/5m gives a
turns ratio of sqrt(20) ~= 4.47:1 step-down, matching a high-Z collector source
to the 8R tank input.

Connectivity strategy is identical to gen_stage2_asc.py / gen_mvp_asc.py: every
component pin gets a FLAG (net label) at its exact pin coordinate, so nets
connect by name and we never rely on fragile wire routing.

On macOS the LTspice CLI cannot netlist a .asc headlessly, so this script emits
BOTH the .asc schematic and a matching .net sidecar (the file the ltspice-mcp
daemon batch-simulates). Both are generated from the same component list so they
can never drift. K (coupled-inductor) statements have no schematic symbol -- they
are emitted as a SPICELINE directive in the .asc and a card in the .net.

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
        card = f".{name} {la} {lb} {k}" if name.upper().startswith("K") \
            else f"K{name} {la} {lb} {k}"
        # K statement form in a SPICE deck is just "K1 L1 L2 0.98" (no leading dot)
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
               "* Generated by gen_stage3_asc.py for installed LTspice 26 symbols.",
               ".OPTIONS ALLOW_AMBIGUOUS_MODELS"]
        net += self.net
        net.append(".model D D")
        net.append(r".lib C:\users\crossover\AppData\Local\LTspice\lib\cmp\standard.dio")
        net.append("* BD139 driver model + analysis/measurement directives")
        for card in self.directives:
            net.append(card)
        net.append(".lib UniversalOpAmp2.lib")
        net.append(".backanno")
        net.append(".end")
        open(net_path, "w").write("\n".join(net) + "\n")


def build(active_analysis="ac"):
    """active_analysis in {'ac','op','tran'}. Only ONE analysis active at a time.
    Stage 3's primary analysis is .ac (resonance + drive level)."""
    b = Build()
    b.text(16, -40, "Ghost Spring Stage 3 - REB3S Driver Transformer", 4)
    b.text(16, 8, "Stage 2 + REB3S coupled inductors L1(primary)/L2(secondary), K1=0.98. C_drive_out removed: transformer gives galvanic isolation. Connectivity by net labels (FLAG at each pin).", 2)

    # === Power & input source (unchanged from Stage 2) ===
    b.vsrc("Vpos", P.VRAIL_IDEAL, 64, 1200, "+15V", "0")
    b.vsrc("Vneg", P.VRAIL_IDEAL, 224, 1200, "0", "-15V")
    b.cap("C15", P.C15, 384, 1200, "+15V", "0")
    b.cap("C16", P.C16, 512, 1200, "-15V", "0")
    b.cap("C5", P.C5, 640, 1200, "+15V", "0")
    b.cap("C6", P.C6, 768, 1200, "-15V", "0")
    b.cap("C7", P.C7, 896, 1200, "+15V", "0")
    b.cap("C8", P.C8, 1024, 1200, "-15V", "0")
    b.text(64, 1160, "Power: idealised +/-15V. C5-C8 100n decoupling, C15/C16 10u bulk.", 2)

    b.vsrc("V1", P.V1_SINE_NORMAL, 64, 160, "vin", "0", value2=P.V1_AC_TOKEN)

    # === Input buffer U1 (unchanged) ===
    b.cap("C_in", P.C_IN, 160, 144, "vin", "u1_pos")
    b.res("R1", P.R1, 280, 144, "u1_pos", "0")
    b.diode("Dclamp_p", P.D_1N4148, 400, 96, "u1_pos", "+15V")
    b.diode("Dclamp_n", P.D_1N4148, 400, 224, "-15V", "u1_pos")
    b.opa("U1", 560, 200, "u1_pos", "u1_out", "+15V", "-15V", "u1_out")
    b.res("R2", P.R2, 640, 144, "u1_out", "u1_buf")

    # === Dwell pot divider (unchanged) ===
    # RV1a is the wiper-to-GND half; RV1b is the signal-to-wiper half. This
    # matches stage_06_full and builder-guide.md: GND->lug1(CCW)=RV1a rv1_wiper 0,
    # dry(u1_buf)->lug3(CW)=RV1b u1_buf rv1_wiper. At CW the wiper sits on u1_buf
    # (max drive); at CCW it is shunted to GND (min drive).
    b.res("RV1a", P.RV1A, 760, 60, "rv1_wiper", "0")
    b.res("RV1b", P.RV1B, 760, 180, "u1_buf", "rv1_wiper")

    # === BD139 discrete driver (unchanged from Stage 2) ===
    b.cap("C_drive", P.C_DRIVE, 880, 144, "rv1_wiper", "q1_drv")
    b.res("R3b", P.R3B, 1000, 40, "+15V", "q1_base")
    b.res("R4", P.R4, 1000, 200, "q1_base", "0")
    b.res("R3", P.R3, 880, 300, "q1_drv", "q1_base")
    b.npn("Q1", "BD139", 1140, 360, "q1_c", "q1_base", "q1_e")
    b.res("R5", P.R5, 1140, 520, "q1_e", "0")
    b.cap("C2", P.C2, 1280, 520, "q1_e", "0")
    b.diode("D3", P.D_1N4148, 1140, 220, "q1_c", "+15V")

    # === STAGE 3: REB3S driver transformer ===
    # L1 (100mH) = transformer PRIMARY. Stays in the collector path (+15V->q1_c):
    #   it carries Q1's collector DC (Rser=0 -> DC short to +15V, so Ic is set by
    #   R5/bias, identical to Stage 2) and its AC current is the primary drive.
    b.ind("L1", P.L1, 1140, 60, "+15V", "q1_c")
    # L2 (5mH) = transformer SECONDARY, into the 8R tank input. NO galvanic path
    #   from collector to tank now -- only magnetic coupling via K1. (C_drive_out
    #   from Stage 2 is removed: the transformer itself blocks DC.)
    #   L1/L2 = 100m/5m -> turns ratio sqrt(20) ~= 4.47:1 step-down to match the
    #   high-Z collector source to the 8R tank input. The primary inductance
    #   resonating against the tank input network puts the peak in the 1-5kHz
    #   "drip" band.
    b.ind("L2", P.L2, 1300, 60, "tank_in", "0")
    # K1: tight magnetic coupling, REB3S spec (~0.98, not ideal 1.0).
    b.kcouple("K1", "L1", "L2", P.K1, 1280, 200)

    # === Spring tank RLC (unchanged from Stage 2; now driven by L2 secondary) ===
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
    b.res("Rwet_wire", "0", 2300, 600, "rv3_wiper", "mix_wet")  # direct wire, modelled 0 ohm
    b.opa("U3", 2560, 900, "mix_node", "u3_out", "+15V", "-15V", "u3_out")
    b.res("R7", P.R7, 2640, 844, "u3_out", "v_out")
    b.res("Rload", P.RLOAD, 2760, 844, "v_out", "0")
    b.text(2640, 820, "J2 -> MC100 input (47k load)", 2)

    # === Models ===
    b.directive(f".model BD139 {BD139_MODEL}")

    # === Analysis (only ONE active at a time) ===
    if active_analysis == "ac":
        b.directive(".ac dec 100 20 20k")
        # Stage 3 -- the "drip": resonant peak at tank_in in 1-5kHz band.
        b.directive(".meas AC tank_pk_lvl MAX V(tank_in)")
        b.directive(".meas AC tank_pk_f   WHEN V(tank_in)=tank_pk_lvl")
        # Stage 3 -- signal actually present at the tank input.
        b.directive(".meas AC tank_drive_db FIND 20*log10(V(tank_in)/V(rv1_wiper)) AT=2k")
    elif active_analysis == "ac_regression":
        # Stage 1 regression checks via AC (recovery gain + HPF corner).
        b.directive(".ac dec 100 20 20k")
        b.directive(".meas AC recov_gain FIND V(u2_out)/V(u2_in_pos) AT=1k")
        b.directive(".meas AC hpf_pb FIND mag(V(hpf_out)/V(u2_out)) AT=5k")
        b.directive(".meas AC hpf_m3db WHEN mag(V(hpf_out)/V(u2_out))=hpf_pb*0.7079 RISE=1")
    elif active_analysis == "op":
        b.directive(".op")
        b.directive(".meas OP q1_ve FIND V(q1_e)")
        b.directive(".meas OP q1_ic FIND Ic(Q1)")
        b.directive(".meas OP off_u1 FIND V(u1_out)")
        b.directive(".meas OP off_u2 FIND V(u2_out)")
        b.directive(".meas OP off_u3 FIND V(v_out)")
    elif active_analysis == "tran":
        b.directive(".tran 0 100m 0 1u")
        b.directive(".meas TRAN d3_pk MAX abs(I(D3))")
        b.directive(".meas TRAN drv_pk MAX abs(I(L1))")
        b.directive(".meas TRAN drv_rms RMS I(L1)")
        b.directive(".meas TRAN vout_pk MAX abs(V(v_out))")
        b.directive(".meas TRAN rms_early RMS V(v_out) FROM=0 TO=10m")
        b.directive(".meas TRAN rms_late RMS V(v_out) FROM=90m TO=100m")
        b.directive(".meas TRAN osc_ratio PARAM rms_late/rms_early")

    b.text(16, 1620,
           "Active analysis: ." + active_analysis +
           ". Regenerate with gen_stage3_asc.py {ac|ac_regression|op|tran} -- ONE analysis at a time.", 2)

    return b


if __name__ == "__main__":
    import sys
    analysis = sys.argv[1] if len(sys.argv) > 1 else "ac"
    base = "/Users/bubblegum/projects/le-ton-juste/docs/reverb-tank/stages"
    b = build(analysis)
    asc = f"{base}/stage_03_transformer.asc"
    net = f"{base}/stage_03_transformer.net"
    b.dump(asc, net)
    print(f"wrote {asc} and {net} (analysis={analysis})")
