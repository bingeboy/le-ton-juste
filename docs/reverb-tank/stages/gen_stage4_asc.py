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
  overload      : 20Vpp transient overload (V1 = SINE(0 10 1k)); confirm the
                  U1(+) node is clamped to +/-16V max (Stage 4 green #2)
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

OPA_PARAMS = "Avol=1Meg GBW=8Meg Slew=20Meg Ilimit=25m Rail=0 Rinc=1T"
OPA_PARAMS_NET = ("level2 Avol=1Meg GBW=8Meg Slew=20Meg Ilimit=25m "
                  "Rail=0 Rinc=1T Vos=0 En=0 Enk=0 In=0 "
                  "Ink=0 Rin=500Meg")

BD139_MODEL = "NPN(Is=1e-14 Bf=100 Vaf=50 Rb=1 Rc=0.1 Re=0.05 Cje=30p Cjc=15p)"

# BZX84C15L: 15V 250mW zener used as the back-to-back pair modelling the
# SMBJ15CA bidirectional TVS. BV=15 sets the 15V breakdown; N/Rs/IBV give a
# realistic-enough knee for a clamp-window measurement; Cjo ~ the small TVS
# junction capacitance.
BZX84C15L_MODEL = "D(BV=15 N=1.6 Rs=2 IBV=5m Cjo=80p Iave=200m)"


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
        net.append(r".lib C:\users\crossover\AppData\Local\LTspice\lib\cmp\standard.dio")
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
    (idle clamp reverse-bias) and the 'overload' .tran (20Vpp clamp window)."""
    b = Build()
    b.text(16, -40, "Ghost Spring Stage 4 - Input Protection (C_in, R1, Dclamp+/-, TVS1)", 4)
    b.text(16, 8, "Stage 3 + TVS1 (SMBJ15CA) across the input jack vin->0, modelled as two BZX84C15L zeners back-to-back (cathodes tied at tvs_mid). C_in/R1/Dclamp_p/Dclamp_n confirmed unchanged from MVP. Connectivity by net labels (FLAG at each pin).", 2)

    # === Power & input source (unchanged from Stage 3) ===
    b.vsrc("Vpos", "15", 64, 1200, "+15V", "0")
    b.vsrc("Vneg", "15", 224, 1200, "0", "-15V")
    b.cap("C15", "10u", 384, 1200, "+15V", "0")
    b.cap("C16", "10u", 512, 1200, "-15V", "0")
    b.cap("C5", "100n", 640, 1200, "+15V", "0")
    b.cap("C6", "100n", 768, 1200, "-15V", "0")
    b.cap("C7", "100n", 896, 1200, "+15V", "0")
    b.cap("C8", "100n", 1024, 1200, "-15V", "0")
    b.text(64, 1160, "Power: idealised +/-15V. C5-C8 100n decoupling, C15/C16 10u bulk.", 2)

    # Input source. SINE(0 100m 1k) = normal 100mVpk; the 'overload' analysis
    # swaps this to SINE(0 10 1k) = 20Vpp for the clamp-window test.
    vin_value = "SINE(0 10 1k)" if active_analysis == "overload" else "SINE(0 100m 1k)"
    b.vsrc("V1", vin_value, 64, 160, "vin", "0", value2="AC 1")

    # === STAGE 4: TVS1 at the jack (vin -> 0), modelled as two zeners B2B ===
    # Placed to the LEFT/below the source, between vin and 0, BEFORE C_in.
    # TVS1a: anode vin -> cathode tvs_mid ; TVS1b: anode 0 -> cathode tvs_mid.
    # Cathodes tied at tvs_mid -> either polarity clamped at BV(15) + Vf(~0.7).
    b.diode("DTVS1a", "BZX84C15L", 64, 400, "vin", "tvs_mid")
    b.diode("DTVS1b", "BZX84C15L", 64, 528, "0", "tvs_mid")
    b.text(160, 420, "TVS1 = SMBJ15CA (two BZX84C15L B2B): clamps vin to +/-~15.7V on ESD.", 2)

    # === Input buffer U1 front-end (C_in, R1, clamp pair: unchanged from MVP) ===
    b.cap("C_in", "1u", 160, 144, "vin", "u1_pos")       # first in path, before R1
    b.res("R1", "1Meg", 280, 144, "u1_pos", "0")          # SHUNT after C_in, not series
    b.diode("Dclamp_p", "1N4148", 400, 96, "u1_pos", "+15V")   # +overvoltage clamp
    b.diode("Dclamp_n", "1N4148", 400, 224, "-15V", "u1_pos")  # -overvoltage clamp
    b.opa("U1", 560, 200, "u1_pos", "u1_out", "+15V", "-15V", "u1_out")
    b.res("R2", "100", 640, 144, "u1_out", "u1_buf")

    # === Dwell pot divider (unchanged) ===
    b.res("RV1a", "5k", 760, 60, "u1_buf", "rv1_wiper")
    b.res("RV1b", "5k", 760, 180, "rv1_wiper", "0")

    # === BD139 discrete driver (unchanged from Stage 3) ===
    b.cap("C_drive", "1u", 880, 144, "rv1_wiper", "q1_drv")
    b.res("R3b", "6.8k", 1000, 40, "+15V", "q1_base")
    b.res("R4", "1k", 1000, 200, "q1_base", "0")
    b.res("R3", "1k", 880, 300, "q1_drv", "q1_base")
    b.npn("Q1", "BD139", 1140, 360, "q1_c", "q1_base", "q1_e")
    b.res("R5", "68", 1140, 520, "q1_e", "0")
    b.cap("C2", "100u", 1280, 520, "q1_e", "0")
    b.diode("D3", "1N4148", 1140, 220, "q1_c", "+15V")

    # === REB3S driver transformer (unchanged from Stage 3) ===
    b.ind("L1", "100m", 1140, 60, "+15V", "q1_c")
    b.ind("L2", "5m", 1300, 60, "tank_in", "0")
    b.kcouple("K1", "L1", "L2", "0.98", 1280, 200)

    # === Spring tank RLC (unchanged from Stage 3) ===
    b.res("R_tank_in", "8", 1300, 240, "tank_in", "0")
    b.ind("L_tank", "15m", 1420, 60, "tank_in", "tank_mid")
    b.res("R_tank_mech", "200", 1540, 240, "tank_mid", "tk_a")
    b.ind("L_tank_mech", "500m", 1540, 360, "tk_a", "tk_b")
    b.cap("C_tank_mech", "10n", 1540, 480, "tk_b", "0")
    b.res("R_tank_out", "2550", 1660, 60, "tank_mid", "tank_out")
    b.ind("L_tank_out", "2", 1660, 240, "tank_out", "0")

    # === Recovery preamp U2 (unchanged) ===
    b.cap("C3", "470n", 1780, 144, "tank_out", "u2_in_pos")
    b.res("Rbias", "100k", 1900, 240, "u2_in_pos", "0")
    b.opa("U2", 2060, 200, "u2_in_pos", "u2_inv", "+15V", "-15V", "u2_out")
    b.res("Ri", "470", 2000, 360, "u2_inv", "0")
    b.res("Rf", "100k", 2120, 360, "u2_out", "u2_inv")

    # === Post-recovery HPF (unchanged) ===
    b.cap("C4", "100n", 2240, 144, "u2_out", "hpf_out")
    b.res("R6", "5.6k", 2360, 240, "hpf_out", "0")

    # === Tone RV3, Mix RV2, output buffer U3 (unchanged) ===
    b.res("RV3a", "50k", 2180, 600, "hpf_out", "rv3_wiper")
    b.res("RV3b", "50k", 2180, 720, "rv3_wiper", "0")
    b.res("Rdry", "10k", 640, 360, "u1_buf", "mix_top")
    b.res("Rwet", "0.001", 2300, 600, "rv3_wiper", "mix_top")
    b.res("RV2a", "50k", 2300, 760, "mix_top", "mix_node")
    b.res("RV2b", "50k", 2300, 880, "mix_node", "0")
    b.cap("C_bright", "47p", 2420, 760, "mix_top", "mix_node")
    b.opa("U3", 2560, 900, "mix_node", "u3_out", "+15V", "-15V", "u3_out")
    b.res("R7", "100", 2640, 844, "u3_out", "v_out")
    b.res("Rload", "47k", 2760, 844, "v_out", "0")
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
        # Stage 4 green #2: 20Vpp overload -> U1(+) node clamped to +/-16V max.
        b.directive(".tran 0 5m 0 1u")
        b.directive(".meas TRAN u1pos_hi MAX V(u1_pos)")
        b.directive(".meas TRAN u1pos_lo MIN V(u1_pos)")
        # Also report what the jack node itself does (TVS clamp window).
        b.directive(".meas TRAN vin_hi MAX V(vin)")
        b.directive(".meas TRAN vin_lo MIN V(vin)")
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
        b.directive(".meas AC recov_gain FIND V(u2_out)/V(u2_in_pos) AT=1k")
        b.directive(".meas AC hpf_pb FIND mag(V(hpf_out)/V(u2_out)) AT=5k")
        b.directive(".meas AC hpf_m3db WHEN mag(V(hpf_out)/V(u2_out))=hpf_pb*0.7079 RISE=1")

    b.text(16, 1620,
           "Active analysis: ." + active_analysis +
           ". Regenerate with gen_stage4_asc.py {op|overload|tran|ac|ac_regression} -- ONE analysis at a time.", 2)

    return b


if __name__ == "__main__":
    import sys
    analysis = sys.argv[1] if len(sys.argv) > 1 else "op"
    base = "/Users/bubblegum/projects/le-ton-juste/docs/reverb-tank/stages"
    b = build(analysis)
    asc = f"{base}/stage_04_input_protect.asc"
    net = f"{base}/stage_04_input_protect.net"
    b.dump(asc, net)
    print(f"wrote {asc} and {net} (analysis={analysis})")
