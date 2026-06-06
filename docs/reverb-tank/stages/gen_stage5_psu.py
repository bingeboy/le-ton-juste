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

        F2/F3 MF-R050 polyfuses -> modelled as 0.5 ohm series R (a polyfuse is
        just wire until it trips; we test NORMAL operation):
            F2  ac_pos f2_out  0.5
            F3  ac_neg f3_out  0.5

        BR1 = W04G full-wave bridge, 4 x 1N4007 (D-prefix instance names):
            DBR1a  f2_out  pos_rect   (top-half +, ac_pos -> +bus)
            DBR1b  f3_out  pos_rect   (top-half +, ac_neg -> +bus)
            DBR1c  neg_rect f2_out    (bottom-half -, -bus -> ac_pos)
            DBR1d  neg_rect f3_out    (bottom-half -, -bus -> ac_neg)
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
        verified - so we define simple behavioural subckts inline, see below):
            XU4  pos_rect 0 +15V  LM78xx   ; +15 out
            XU5  neg_rect 0 -15V  LM79xx   ; -15 out

        Regulator output caps + HF bypass:
            C13  +15V 0  100u
            C17  +15V 0  100n
            C14  -15V 0  100u
            C18  -15V 0  100n

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

OPA_PARAMS = "Avol=1Meg GBW=8Meg Slew=20Meg Ilimit=25m Rail=0 Rinc=1T"
OPA_PARAMS_NET = ("level2 Avol=1Meg GBW=8Meg Slew=20Meg Ilimit=25m "
                  "Rail=0 Rinc=1T Vos=0 En=0 Enk=0 In=0 "
                  "Ink=0 Rin=500Meg")

BD139_MODEL = "NPN(Is=1e-14 Bf=100 Vaf=50 Rb=1 Rc=0.1 Re=0.05 Cje=30p Cjc=15p)"

# BZX84C15L: 15V 250mW zener, back-to-back pair modelling the SMBJ15CA TVS.
BZX84C15L_MODEL = "D(BV=15 N=1.6 Rs=2 IBV=5m Cjo=80p Iave=200m)"

# 1N4007 bridge-rectifier diode: 1000V 1A general-purpose rectifier. A modest
# Rs and junction cap are enough for a 60Hz mains-frequency rectifier sim.
DN4007_MODEL = "D(Is=14.1n N=1.984 Rs=33.9m Ikf=94.8 Cjo=51.7p M=0.333 Vj=0.7 Bv=1000 Ibv=10u)"

# Behavioural linear-regulator subckts (no 78xx/79xx ships with this LTspice).
# Positive: OUT = min(Vin-2, +Vout). Negative: OUT = max(Vin+2, -Vout).
LM78XX_SUBCKT = [
    ".subckt LM78xx IN COM OUT",
    ".param Vout=15",
    "B1 OUT COM V=min(V(IN,COM)-2, {Vout})",
    ".ends LM78xx",
]
LM79XX_SUBCKT = [
    ".subckt LM79xx IN COM OUT",
    ".param Vout=15",
    "B1 OUT COM V=max(V(IN,COM)+2, -{Vout})",
    ".ends LM79xx",
]


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


def build(active_analysis="op"):
    """active_analysis in {'op','tran'}. Only ONE analysis active at a time."""
    b = Build()
    b.text(16, -40, "Ghost Spring Stage 5 - +/-15V Linear Power Supply (T1, BR1, C11/C12, U4 LM7815, U5 LM7915)", 4)
    b.text(16, 8, "Stage 4 signal path UNCHANGED, now fed from the real PSU. T1 15-0-15VAC (two SINE(0 21.2 60), center tap=GND) -> F2/F3 polyfuses (0.5ohm) -> BR1 (4x 1N4007) -> C11/C12 2200u bulk + 10k bleed -> U4 LM7815 / U5 LM7915 -> C13/C14 100u + C17/C18 100n -> +/-15V rails. Connectivity by net labels (FLAG at each pin).", 2)

    # ====================================================================
    # === STAGE 5: +/-15V LINEAR POWER SUPPLY (replaces ideal Vpos/Vneg) ==
    # ====================================================================
    # T1 secondary: 15-0-15VAC, center tap = GND. Two anti-phase 60Hz SINE
    # sources, 21.2V peak = 15Vrms * sqrt(2). Vsec_n is written 0 -> ac_neg so
    # ac_neg swings opposite ac_pos (true center-tapped winding).
    b.vsrc("Vsec_p", "SINE(0 21.2 60)", 64, 1000, "ac_pos", "0")
    b.vsrc("Vsec_n", "SINE(0 21.2 60)", 224, 1000, "0", "ac_neg")
    b.text(64, 960, "T1 Triad F-219X 15-0-15VAC. Center tap = GND. 21.2Vpk = 15Vrms*sqrt(2).", 2)

    # F2/F3 MF-R050 polyfuses -> 0.5 ohm series R (wire until tripped). SPICE
    # reserves the F prefix for current-controlled sources, so the resistor
    # instances are RF2/RF3 (the F2/F3 designators live on the schematic label).
    b.res("RF2", "0.5", 384, 1000, "ac_pos", "f2_out")
    b.res("RF3", "0.5", 512, 1000, "ac_neg", "f3_out")
    b.text(384, 960, "F2/F3 MF-R050 polyfuse = 0.5ohm (RF2/RF3 in SPICE).", 2)

    # BR1 = W04G full-wave bridge off the center-tapped winding, 4x 1N4007.
    # D-prefix instance names (DBR1a..d). pos_rect = +ve bus, neg_rect = -ve bus.
    b.diode("DBR1a", "DN4007", 640, 880, "f2_out", "pos_rect")
    b.diode("DBR1b", "DN4007", 760, 880, "f3_out", "pos_rect")
    b.diode("DBR1c", "DN4007", 640, 1080, "neg_rect", "f2_out")
    b.diode("DBR1d", "DN4007", 760, 1080, "neg_rect", "f3_out")
    b.text(640, 840, "BR1 W04G = 4x 1N4007. pos_rect=+ve bus, neg_rect=-ve bus.", 2)

    # Bulk filter caps + bleed resistors, one set per rail.
    b.cap("C11", "2200u", 900, 880, "pos_rect", "0")     # +ve bulk filter
    b.res("R_bleed1", "10k", 1020, 880, "pos_rect", "0")  # +ve bleed
    b.cap("C12", "2200u", 900, 1080, "neg_rect", "0")     # -ve bulk filter
    b.res("R_bleed2", "10k", 1020, 1080, "neg_rect", "0")  # -ve bleed

    # Regulators: U4 LM7815 (+15), U5 LM7915 (-15). Inline behavioural subckts.
    b.reg("U4", "LM78xx", 1160, 860, "pos_rect", "0", "+15V")
    b.reg("U5", "LM79xx", 1160, 1100, "neg_rect", "0", "-15V")

    # Regulator output caps + HF bypass on each regulated rail.
    b.cap("C13", "100u", 1320, 880, "+15V", "0")
    b.cap("C17", "100n", 1440, 880, "+15V", "0")
    b.cap("C14", "100u", 1320, 1080, "-15V", "0")
    b.cap("C18", "100n", 1440, 1080, "-15V", "0")
    b.text(1320, 840, "C13/C14 100u reg out caps, C17/C18 100n HF bypass.", 2)

    # Inline regulator subckts (no 78xx/79xx ships with installed LTspice).
    b.subckt(LM78XX_SUBCKT)
    b.subckt(LM79XX_SUBCKT)

    # ====================================================================
    # === STAGE 4 SIGNAL PATH (UNCHANGED) - now fed from the PSU rails ====
    # ====================================================================
    # Extra rail decoupling kept from Stage 4 (C5-C8 100n, C15/C16 10u bulk).
    b.cap("C15", "10u", 1580, 880, "+15V", "0")
    b.cap("C16", "10u", 1580, 1080, "-15V", "0")
    b.cap("C5", "100n", 1700, 880, "+15V", "0")
    b.cap("C6", "100n", 1700, 1080, "-15V", "0")
    b.cap("C7", "100n", 1820, 880, "+15V", "0")
    b.cap("C8", "100n", 1820, 1080, "-15V", "0")

    # Input source. Normal 100mVpk; the PSU stages do not drive the input.
    b.vsrc("V1", "SINE(0 100m 1k)", 64, 160, "vin", "0", value2="AC 1")

    # TVS1 at the jack (vin -> 0), two zeners back-to-back (cathodes at tvs_mid).
    b.diode("DTVS1a", "BZX84C15L", 64, 400, "vin", "tvs_mid")
    b.diode("DTVS1b", "BZX84C15L", 64, 528, "0", "tvs_mid")

    # Input buffer U1 front-end (C_in, R1, clamp pair: unchanged from MVP).
    b.cap("C_in", "1u", 160, 144, "vin", "u1_pos")
    b.res("R1", "1Meg", 280, 144, "u1_pos", "0")
    b.diode("Dclamp_p", "1N4148", 400, 96, "u1_pos", "+15V")
    b.diode("Dclamp_n", "1N4148", 400, 224, "-15V", "u1_pos")
    b.opa("U1", 560, 200, "u1_pos", "u1_out", "+15V", "-15V", "u1_out")
    b.res("R2", "100", 640, 144, "u1_out", "u1_buf")

    # Dwell pot divider (unchanged).
    b.res("RV1a", "5k", 760, 60, "u1_buf", "rv1_wiper")
    b.res("RV1b", "5k", 760, 180, "rv1_wiper", "0")

    # BD139 discrete driver (unchanged from Stage 4).
    b.cap("C_drive", "1u", 880, 144, "rv1_wiper", "q1_drv")
    b.res("R3b", "6.8k", 1000, 40, "+15V", "q1_base")
    b.res("R4", "1k", 1000, 200, "q1_base", "0")
    b.res("R3", "1k", 880, 300, "q1_drv", "q1_base")
    b.npn("Q1", "BD139", 1140, 360, "q1_c", "q1_base", "q1_e")
    b.res("R5", "68", 1140, 520, "q1_e", "0")
    b.cap("C2", "100u", 1280, 520, "q1_e", "0")
    b.diode("D3", "1N4148", 1140, 220, "q1_c", "+15V")

    # REB3S driver transformer (unchanged).
    b.ind("L1", "100m", 1140, 60, "+15V", "q1_c")
    b.ind("L2", "5m", 1300, 60, "tank_in", "0")
    b.kcouple("K1", "L1", "L2", "0.98", 1280, 200)

    # Spring tank RLC (unchanged).
    b.res("R_tank_in", "8", 1300, 240, "tank_in", "0")
    b.ind("L_tank", "15m", 1420, 60, "tank_in", "tank_mid")
    b.res("R_tank_mech", "200", 1540, 240, "tank_mid", "tk_a")
    b.ind("L_tank_mech", "500m", 1540, 360, "tk_a", "tk_b")
    b.cap("C_tank_mech", "10n", 1540, 480, "tk_b", "0")
    b.res("R_tank_out", "2550", 1660, 60, "tank_mid", "tank_out")
    b.ind("L_tank_out", "2", 1660, 240, "tank_out", "0")

    # Recovery preamp U2 (unchanged).
    b.cap("C3", "470n", 1780, 144, "tank_out", "u2_in_pos")
    b.res("Rbias", "100k", 1900, 240, "u2_in_pos", "0")
    b.opa("U2", 2060, 200, "u2_in_pos", "u2_inv", "+15V", "-15V", "u2_out")
    b.res("Ri", "470", 2000, 360, "u2_inv", "0")
    b.res("Rf", "100k", 2120, 360, "u2_out", "u2_inv")

    # Post-recovery HPF (unchanged).
    b.cap("C4", "100n", 2240, 144, "u2_out", "hpf_out")
    b.res("R6", "5.6k", 2360, 240, "hpf_out", "0")

    # Tone RV3, Mix RV2, output buffer U3 (unchanged).
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
    elif active_analysis == "tran":
        # Stage 5 green #3/#4: ripple on the regulated rails after caps settle.
        # 150ms run, ripple window 100ms..120ms (>= 1 full 120Hz ripple period).
        b.directive(".tran 0 150m 0 10u")
        b.directive(".meas TRAN ripple_pos PP V(+15V) FROM=100m TO=120m")
        b.directive(".meas TRAN ripple_neg PP V(-15V) FROM=100m TO=120m")
        # Also report the settled mean and the unregulated-bus ripple for context.
        b.directive(".meas TRAN rail_pos_avg AVG V(+15V) FROM=100m TO=120m")
        b.directive(".meas TRAN rail_neg_avg AVG V(-15V) FROM=100m TO=120m")
        b.directive(".meas TRAN unreg_pos_pp PP V(pos_rect) FROM=100m TO=120m")
        b.directive(".meas TRAN unreg_neg_pp PP V(neg_rect) FROM=100m TO=120m")

    b.text(16, 1620,
           "Active analysis: ." + active_analysis +
           ". Regenerate with gen_stage5_psu.py {op|tran} -- ONE analysis at a time.", 2)

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
