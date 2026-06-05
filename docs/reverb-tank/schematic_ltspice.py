#!/usr/bin/env python3
"""
schematic_ltspice.py — Ghost Spring Tank LTspice schematic generator.

Writes `ghost_spring.asc`, a complete, simulatable LTspice XVII schematic for
the Ghost Spring Tank: a DIY hi-fi transformer-coupled spring reverb.

Signal path: 1/4" input -> TVS/clamp -> OPA2134 input buffer (U1) -> Dwell pot
-> BD139 class-A driver (Q1) -> REB3S driver transformer (coupled inductors)
-> spring tank (behavioural RLC) -> OPA2134 recovery amp (U2, G=214) ->
post-recovery HPF -> tone (RV3) / mix (RV2) -> OPA2134 output buffer (U3) ->
output jack.  Power is an idealised +/-15V rail pair.

Embedded directives: .op, .ac, .tran, .meas, the BD139 .model and the
transformer coupling K statement.

Self-contained: Python standard library only.  Run:  python schematic_ltspice.py

------------------------------------------------------------------------------
LTspice .asc geometry notes
------------------------------------------------------------------------------
Coordinates: +x right, +y DOWN.  Grid = 16 units; every pin/wire endpoint here
is a multiple of 16 so the netlister connects them.

Stock-symbol pin offsets at rotation R0 (taken from the .asy PIN records):

  res     : (16,16) top      , (16,96) bottom
  cap     : (16, 0) top      , (16,64) bottom
  ind     : (16,16) top      , (16,96) bottom
  diode   : (16, 0) cathode  , (16,64) anode
  zener   : (16, 0) cathode  , (16,64) anode
  voltage : ( 0,16) +        , ( 0,96) -
  npn     : ( 0,48) base     , (64, 0) collector , (64,96) emitter
  UniversalOpamp2 : (0,16) IN+, (0,80) IN-, (64,0) V+, (64,96) V-, (128,48) OUT

Rotations are applied with the standard LTspice transform so rotated pins are
computed, never hand-guessed.
"""

import os
import sys


# ──────────────────────────────────────────────────────────────────────────────
# Rotation transform
# ──────────────────────────────────────────────────────────────────────────────
def _rotate(dx, dy, rot):
    """Rotate a symbol-local pin offset (dx,dy) by an LTspice orientation token.

    LTspice rotates clockwise on screen (y points down).  Mirror tokens (M*)
    flip x first, then rotate.
    """
    mirror = rot.startswith("M")
    angle = int(rot[1:])
    if mirror:
        dx = -dx
    # Clockwise rotation in a y-down coordinate system.
    if angle == 0:
        return dx, dy
    if angle == 90:
        return -dy, dx
    if angle == 180:
        return -dx, -dy
    if angle == 270:
        return dy, -dx
    raise ValueError(f"bad rotation {rot}")


# ──────────────────────────────────────────────────────────────────────────────
# .asc builder
# ──────────────────────────────────────────────────────────────────────────────
class Asc:
    def __init__(self, width, height):
        self.lines = ["Version 4", f"SHEET 1 {width} {height}"]
        self._wires = set()   # dedupe + drop zero-length segments

    # -- primitives -----------------------------------------------------------
    def wire(self, x1, y1, x2, y2):
        if (x1, y1) == (x2, y2):
            return                       # zero-length: nothing to draw
        key = frozenset(((x1, y1), (x2, y2)))
        if key in self._wires:
            return                       # already drawn this segment
        self._wires.add(key)
        self.lines.append(f"WIRE {x1} {y1} {x2} {y2}")

    def polyline(self, pts):
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            self.wire(x1, y1, x2, y2)

    def flag(self, x, y, name):
        self.lines.append(f"FLAG {x} {y} {name}")

    def text(self, x, y, justify, size, body, directive=False):
        prefix = "!" if directive else ""
        body = body.replace("\n", "\\n")
        self.lines.append(f"TEXT {x} {y} {justify} {size} {prefix}{body}")

    def render(self):
        # LTspice expects CRLF line endings.
        return "\r\n".join(self.lines) + "\r\n"

    # -- symbol placement -----------------------------------------------------
    def place(self, kind, x, y, rot, pins, attrs):
        """Emit a SYMBOL + SYMATTRs and return absolute pin coords.

        `pins` maps pin-name -> (dx,dy) local offset at R0.  Returns a dict of
        pin-name -> (abs_x, abs_y) after applying rotation and the (x,y) anchor.
        """
        self.lines.append(f"SYMBOL {kind} {x} {y} {rot}")
        for key, value in attrs:
            self.lines.append(f"SYMATTR {key} {value}")
        out = {}
        for name, (dx, dy) in pins.items():
            rx, ry = _rotate(dx, dy, rot)
            out[name] = (x + rx, y + ry)
        return out


# Pin maps (R0 local offsets).
P_RES = {"a": (16, 16), "b": (16, 96)}
P_CAP = {"a": (16, 0), "b": (16, 64)}
P_IND = {"a": (16, 16), "b": (16, 96)}
P_DIODE = {"k": (16, 0), "a": (16, 64)}      # k=cathode, a=anode
P_VOLT = {"p": (0, 16), "n": (0, 96)}
P_NPN = {"B": (0, 48), "C": (64, 0), "E": (64, 96)}
P_OPA = {"inp": (0, 16), "inn": (0, 80), "vp": (64, 0), "vn": (64, 96),
         "out": (128, 48)}


# ──────────────────────────────────────────────────────────────────────────────
# Part helpers — each returns the placed-symbol pin dict
# ──────────────────────────────────────────────────────────────────────────────
def R(asc, name, value, x, y, rot="R0"):
    return asc.place("res", x, y, rot, P_RES,
                     [("InstName", name), ("Value", value)])


def C(asc, name, value, x, y, rot="R0", value2=None):
    attrs = [("InstName", name), ("Value", value)]
    if value2:
        attrs.append(("Value2", value2))
    return asc.place("cap", x, y, rot, P_CAP, attrs)


def L(asc, name, value, x, y, rot="R0"):
    return asc.place("ind", x, y, rot, P_IND,
                     [("InstName", name), ("Value", value),
                      ("SpiceLine", "Rser=0")])


def D(asc, name, model, x, y, rot="R0"):
    return asc.place("diode", x, y, rot, P_DIODE,
                     [("InstName", name), ("Value", model)])


def Z(asc, name, model, x, y, rot="R0", value2=None):
    attrs = [("InstName", name), ("Value", model)]
    if value2:
        attrs.append(("Value2", value2))
    return asc.place("zener", x, y, rot, P_DIODE, attrs)


def V(asc, name, value, x, y, rot="R0", value2=None):
    attrs = [("InstName", name), ("Value", value)]
    if value2:
        attrs.append(("Value2", value2))
    return asc.place("voltage", x, y, rot, P_VOLT, attrs)


def NPN(asc, name, model, x, y, rot="R0"):
    return asc.place("npn", x, y, rot, P_NPN,
                     [("InstName", name), ("Value", model)])


def OPA(asc, name, x, y, rot="R0"):
    return asc.place(
        "UniversalOpamp2", x, y, rot, P_OPA,
        [("InstName", name),
         ("Value", "UniversalOpamp2"),
         ("Value2", "Avol=1Meg GBW=8Meg Slew=20Meg Ilimit=25m Rail=0 Rinc=1T")],
    )


# ──────────────────────────────────────────────────────────────────────────────
# Schematic
# ──────────────────────────────────────────────────────────────────────────────
def build():
    a = Asc(width=3600, height=1900)
    VP, VN, GND = "+15V", "-15V", "0"

    # ── Title block & explanatory notes ─────────────────────────────────────
    a.text(48, 32, "Left", 4, "Ghost Spring Tank — LTspice Verification Schematic")
    a.text(48, 88, "Left", 2,
           "Op-amps modeled as UniversalOpamp2 with OPA2134 parameters. For "
           "accurate noise/distortion simulation, replace with TI OPA2134 SPICE "
           "model (download from ti.com).")
    a.text(48, 128, "Left", 2,
           "Spring tank modeled as simplified RLC network for impedance/gain "
           "verification only. Does not simulate acoustic spring behavior.")

    # ── Simulation directives (top, clear of parts) ─────────────────────────
    a.text(48, 1720, "Left", 2, ".op", directive=True)
    a.text(48, 1752, "Left", 2, ".ac dec 100 20 20k", directive=True)
    a.text(48, 1784, "Left", 2, ".tran 0 50m 0 1u", directive=True)
    a.text(48, 1816, "Left", 2, ".meas AC gain_recovery MAX V(u2_out)",
           directive=True)
    a.text(48, 1848, "Left", 2,
           ".model BD139 NPN(Is=1e-14 Bf=100 Vaf=50 Rb=1 Rc=0.1 Re=0.05 "
           "Cje=30p Cjc=15p)", directive=True)
    a.text(48, 1880, "Left", 2, "K1 L1 L2 0.98", directive=True)

    # ════════════════════════════════════════════════════════════════════════
    # INPUT STAGE
    # ════════════════════════════════════════════════════════════════════════
    ROW = 560            # main signal row (driver/input)

    # V1 : 1kHz / 100mV sine, AC=1 for the AC sweep.
    v1 = V(a, "V1", "SINE(0 100m 1k)", 192, 560, value2="AC 1")
    a.flag(*v1["n"], GND)
    a.flag(v1["p"][0], v1["p"][1] - 16, "V_in")
    a.wire(v1["p"][0], v1["p"][1] - 16, *v1["p"])
    # V_in node onto the horizontal rail.
    a.wire(*v1["p"], 192, ROW)
    in_node = (192, ROW)

    # TVS1 : SMBJ15CA bidirectional, modeled as two anti-series 15V zeners from
    # the input node to GND (symmetric clamp).
    # z1 at R0 (cathode up = toward node), z2 at R180 (cathode down = toward GND).
    # Due to R180 rotation, z2 pins are offset in x; route anode-to-anode via a
    # corner (vertical then horizontal) to keep all wires orthogonal.
    z1 = Z(a, "TVS1", "BZX84C15L", in_node[0] - 16, ROW + 16,
           value2="SMBJ15CA bidir (modeled)")
    a.wire(in_node[0], in_node[1], z1["k"][0], z1["k"][1])
    z2 = Z(a, "TVS1b", "BZX84C15L", in_node[0] - 16, ROW + 176, rot="R180")
    # Route z1.a -> z2.a orthogonally: drop vertically then step left.
    a.wire(z1["a"][0], z1["a"][1], z1["a"][0], z2["a"][1])   # vertical
    a.wire(z1["a"][0], z2["a"][1], z2["a"][0], z2["a"][1])   # horizontal
    a.flag(z2["k"][0], z2["k"][1], GND)

    # C_in : 1uF series DC block (vertical, rail enters bottom / exits top).
    cin = C(a, "C_in", "1u", 400, 496)        # a=(416,496) top, b=(416,560) bot
    a.wire(in_node[0], ROW, cin["b"][0], ROW)  # node rail to C_in bottom column
    a.wire(cin["b"][0], ROW, *cin["b"])        # rail up to C_in bottom pin
    a.wire(cin["a"][0], cin["a"][1], cin["a"][0], 432)   # C_in top stub up
    a.wire(cin["a"][0], 432, 528, 432)        # across toward bias node
    bias = (528, 432)
    a.flag(*bias, "u1_pos")

    # R1 : 1M shunt from bias node to GND.
    r1 = R(a, "R1", "1Meg", 512, 432)         # a=(528,448) top, b=(528,528) bot
    a.wire(*bias, r1["a"][0], r1["a"][1])
    a.flag(*r1["b"], GND)

    # D_clamp+ : 1N4148 anode at node, cathode to +15V.
    # diode R180: cathode (16,0)->(-16,0)=>(x-16,y); anode (16,64)->(-16,-64)=>(x-16,y-64)
    dcp = D(a, "Dclamp_p", "1N4148", 656, 320, rot="R180")
    # dcp k=(640,320) top? compute: x=656,y=320 -> k:(656-16,320)=(640,320); a:(640,320-64)=(640,256)
    a.flag(dcp["k"][0], dcp["k"][1], VP)
    a.wire(dcp["a"][0], dcp["a"][1], dcp["a"][0], bias[1])
    a.wire(bias[0], bias[1], dcp["a"][0], bias[1])

    # D_clamp- : 1N4148 cathode at node, anode to -15V.
    # diode R0: k=(16,0) top, a=(16,64) bottom.
    dcn = D(a, "Dclamp_n", "1N4148", 624, 448)   # k=(640,448), a=(640,512)
    a.wire(dcn["k"][0], dcn["k"][1], dcn["k"][0], bias[1])
    a.flag(dcn["a"][0], dcn["a"][1], VN)

    # U1 : unity-gain follower.
    u1 = OPA(a, "U1", 768, 400)
    a.flag(*u1["vp"], VP)
    a.flag(*u1["vn"], VN)
    # bias node -> IN+.
    a.wire(dcn["k"][0], bias[1], u1["inp"][0] - 32, bias[1])
    a.wire(u1["inp"][0] - 32, bias[1], u1["inp"][0] - 32, u1["inp"][1])
    a.wire(u1["inp"][0] - 32, u1["inp"][1], *u1["inp"])
    # OUT -> IN- feedback.
    a.polyline([u1["out"], (u1["out"][0] + 32, u1["out"][1]),
                (u1["out"][0] + 32, 560), (u1["inp"][0] - 64, 560),
                (u1["inp"][0] - 64, u1["inn"][1]), u1["inn"]])
    a.flag(u1["out"][0] + 16, u1["out"][1], "u1_out")
    a.wire(u1["out"][0], u1["out"][1], u1["out"][0] + 16, u1["out"][1])

    # R2 : 100R series output (horizontal R90).
    # res R90: a=(16,16)->(-16,16)=>(x-16,y+16); b=(16,96)->(-96,16)=>(x-96,y+16)
    r2 = R(a, "R2", "100", 1008, 432, rot="R90")
    # r2 a=(992,448), b=(912,448)
    a.wire(u1["out"][0] + 16, u1["out"][1], r2["b"][0], r2["b"][1])
    u1_buf = r2["a"]
    a.flag(u1_buf[0] + 16, u1_buf[1], "u1_out_buf")
    a.wire(u1_buf[0], u1_buf[1], u1_buf[0] + 16, u1_buf[1])
    u1_buf = (u1_buf[0] + 16, u1_buf[1])

    # ════════════════════════════════════════════════════════════════════════
    # DRIVER STAGE
    # ════════════════════════════════════════════════════════════════════════
    DRV = 448            # driver signal row

    # C1 : 1uF coupling from u1_buf to RV1.
    a.wire(u1_buf[0], u1_buf[1], 1120, u1_buf[1])
    a.wire(1120, u1_buf[1], 1120, DRV)
    c1 = C(a, "C1", "1u", 1104, DRV)            # a=(1120,448) top, b=(1120,512) bot
    a.wire(*c1["a"], c1["a"][0], DRV - 48)      # top stub up
    a.wire(c1["a"][0], DRV - 48, 1232, DRV - 48)
    # connect c1 bottom to the incoming rail.
    a.wire(1120, DRV, *c1["b"])

    # RV1 "Dwell" 10k lin @ 5k mid: upper half C1->wiper, lower half wiper->GND.
    rv1a = R(a, "RV1a", "5k", 1216, DRV - 96)   # a top, b bottom(=wiper)
    a.wire(rv1a["a"][0], rv1a["a"][1], 1232, DRV - 48)
    a.wire(1232, DRV - 48, rv1a["a"][0], rv1a["a"][1])
    wiper1 = rv1a["b"]
    a.flag(*wiper1, "rv1_wiper")
    rv1b = R(a, "RV1b", "5k", 1216, DRV + 32)
    a.wire(*wiper1, rv1b["a"][0], rv1b["a"][1])
    a.flag(*rv1b["b"], GND)

    # R3 : 1k from wiper to Q1 base (horizontal R90).
    r3 = R(a, "R3", "1k", 1408, wiper1[1] - 16, rot="R90")
    # r3 a=(1392, wiper1[1]); b=(1312, wiper1[1])
    a.wire(*wiper1, r3["b"][0], r3["b"][1])
    q1_base = r3["a"]
    a.flag(*q1_base, "q1_base")

    # R3b : 6.8k +15V -> base.  Place at q1_base.x-16 so "b" pin lands at q1_base.x.
    r3b = R(a, "R3b", "6.8k", q1_base[0] - 16, q1_base[1] - 144)
    a.flag(*r3b["a"], VP)
    a.wire(r3b["b"][0], r3b["b"][1], q1_base[0], q1_base[1])

    # R4 : 1k base -> GND.  Same x alignment as R3b.
    r4 = R(a, "R4", "1k", q1_base[0] - 16, q1_base[1] + 48)
    a.wire(q1_base[0], q1_base[1], r4["a"][0], r4["a"][1])
    a.flag(*r4["b"], GND)

    # Q1 : BD139.
    q1 = NPN(a, "Q1", "BD139", 1488, q1_base[1] - 48)
    # q1 B=(1488, q1_base[1]); aligns with base row.
    a.wire(q1_base[0], q1_base[1], q1["B"][0], q1["B"][1])
    a.flag(*q1["E"], "q1_emitter")
    a.flag(*q1["C"], "q1_collector")

    # R5 : 68R emitter -> GND.
    r5 = R(a, "R5", "68", q1["E"][0] - 16, q1["E"][1] + 16)
    a.wire(*q1["E"], r5["a"][0], r5["a"][1])
    a.flag(*r5["b"], GND)

    # C2 : 100uF emitter bypass -> GND.
    c2 = C(a, "C2", "100u", q1["E"][0] + 112, q1["E"][1] + 16, value2="25V")
    a.wire(q1["E"][0], r5["a"][1], c2["a"][0], r5["a"][1])
    a.wire(c2["a"][0], r5["a"][1], *c2["a"])
    a.flag(*c2["b"], GND)

    # D3 : flyback, anode at collector, cathode to +15V.
    d3 = D(a, "D3", "1N4148", q1["C"][0] + 96, q1["C"][1] - 160)
    a.flag(*d3["k"], VP)
    a.wire(d3["a"][0], d3["a"][1], d3["a"][0], q1["C"][1])
    a.wire(q1["C"][0], q1["C"][1], d3["a"][0], q1["C"][1])

    # T2 : REB3S driver transformer = coupled inductors L1 (primary 100mH) and
    # L2 (secondary 5mH); coupling K1=0.98 declared as a directive above.
    # L1 primary: top to +15V, bottom to Q1 collector.
    l1 = L(a, "L1", "100m", q1["C"][0] + 192, q1["C"][1] - 96)
    a.flag(*l1["a"], VP)
    a.wire(l1["b"][0], l1["b"][1], l1["b"][0], q1["C"][1])
    a.wire(q1["C"][0], q1["C"][1], l1["b"][0], q1["C"][1])

    # L2 secondary: top = tank_in, bottom = GND.
    l2 = L(a, "L2", "5m", l1["a"][0] + 128, q1["C"][1] - 96)
    a.flag(*l2["b"], GND)
    tank_in = l2["a"]
    a.flag(tank_in[0], tank_in[1] - 16, "tank_in")
    a.wire(tank_in[0], tank_in[1] - 16, *tank_in)

    # ════════════════════════════════════════════════════════════════════════
    # SPRING TANK (behavioural RLC)
    # ════════════════════════════════════════════════════════════════════════
    TKX = tank_in[0]
    # Input side: R_tank_in 8R + L_tank 15mH in series, tank_in -> tank_mid.
    rti = R(a, "R_tank_in", "8", TKX - 16, tank_in[1] + 48)
    a.wire(tank_in[0], tank_in[1], rti["a"][0], rti["a"][1])
    ltk = L(a, "L_tank", "15m", TKX - 16, rti["b"][1])
    a.wire(rti["b"][0], rti["b"][1], ltk["a"][0], ltk["a"][1])
    tank_mid = ltk["b"]
    a.flag(*tank_mid, "tank_mid")

    # Mechanical resonance: series R200 + L500mH + C10nF, tank_mid -> GND.
    rm = R(a, "R_tank_mech", "200", TKX - 16, tank_mid[1] + 32)
    a.wire(*tank_mid, rm["a"][0], rm["a"][1])
    lm = L(a, "L_tank_mech", "500m", TKX - 16, rm["b"][1])
    a.wire(rm["b"][0], rm["b"][1], lm["a"][0], lm["a"][1])
    cm = C(a, "C_tank_mech", "10n", TKX - 16, lm["b"][1])
    a.wire(lm["b"][0], lm["b"][1], cm["a"][0], cm["a"][1])
    a.flag(*cm["b"], GND)

    # Output coil: R_tank_out 2550 + L_tank_out 2H, tank_mid -> tank_out.
    rto = R(a, "R_tank_out", "2550", TKX + 96, tank_mid[1] - 16, rot="R90")
    a.wire(tank_mid[0], tank_mid[1], rto["b"][0], rto["b"][1])
    lto = L(a, "L_tank_out", "2", TKX + 240, tank_mid[1] - 16, rot="R90")
    a.wire(rto["a"][0], rto["a"][1], lto["b"][0], lto["b"][1])
    tank_out = lto["a"]
    a.flag(*tank_out, "tank_out")

    # ════════════════════════════════════════════════════════════════════════
    # RECOVERY STAGE  (G = 1 + 100k/470 ≈ 214)
    # ════════════════════════════════════════════════════════════════════════
    RECX = tank_out[0] + 96
    # C3 470n coupling tank_out -> u2 IN+ node.
    a.wire(tank_out[0], tank_out[1], RECX, tank_out[1])
    c3 = C(a, "C3", "470n", RECX - 16, tank_out[1] + 48)
    a.wire(RECX, tank_out[1], c3["a"][0], tank_out[1])
    a.wire(c3["a"][0], tank_out[1], *c3["a"])
    u2pos = (c3["b"][0], c3["b"][1] + 32)
    a.wire(c3["b"][0], c3["b"][1], *u2pos)
    a.flag(*u2pos, "u2_in_pos")

    # Rbias 100k shunt -> GND.
    rb = R(a, "Rbias", "100k", u2pos[0] - 16, u2pos[1])
    a.wire(*u2pos, rb["a"][0], rb["a"][1])
    a.flag(*rb["b"], GND)

    # U2.
    u2 = OPA(a, "U2", u2pos[0] + 96, u2pos[1] - 32)
    a.flag(*u2["vp"], VP)
    a.flag(*u2["vn"], VN)
    a.wire(u2pos[0], u2pos[1], u2["inp"][0] - 32, u2pos[1])
    a.wire(u2["inp"][0] - 32, u2pos[1], u2["inp"][0] - 32, u2["inp"][1])
    a.wire(u2["inp"][0] - 32, u2["inp"][1], *u2["inp"])
    a.flag(u2["out"][0] + 16, u2["out"][1], "u2_out")
    a.wire(u2["out"][0], u2["out"][1], u2["out"][0] + 16, u2["out"][1])
    u2_out = (u2["out"][0] + 16, u2["out"][1])

    # Ri 470 IN- -> GND.
    ri_node_x = u2["inn"][0] - 48
    a.wire(u2["inn"][0], u2["inn"][1], ri_node_x, u2["inn"][1])
    ri = R(a, "Ri", "470", ri_node_x - 16, u2["inn"][1] + 32)
    a.wire(ri_node_x, u2["inn"][1], ri["a"][0], ri["a"][1])
    a.flag(*ri["b"], GND)

    # Rf 100k OUT -> IN- (horizontal R90 over the top).
    rf = R(a, "Rf", "100k", u2["out"][0], u2["inn"][1] + 80, rot="R90")
    a.polyline([(u2["out"][0], u2["out"][1]),
                (u2["out"][0], rf["a"][1]), rf["a"]])
    a.polyline([rf["b"], (ri_node_x, rf["b"][1]),
                (ri_node_x, u2["inn"][1])])

    # ════════════════════════════════════════════════════════════════════════
    # POST-RECOVERY HPF  (wet only): C4 100n series + R6 5.6k to GND.
    # ════════════════════════════════════════════════════════════════════════
    c4 = C(a, "C4", "100n", u2_out[0] + 80, u2_out[1] - 32, rot="R90")
    # cap R90: a=(0,16)=>(x,y+16); b=(-64,16)=>(x-64,y+16).
    # Route orthogonally: drop from u2_out to cap-pin level, then horizontal into c4.b.
    a.wire(u2_out[0], u2_out[1], u2_out[0], c4["b"][1])        # vertical drop
    a.wire(u2_out[0], c4["b"][1], c4["b"][0], c4["b"][1])      # horizontal to c4.b
    hpf_out = c4["a"]
    a.flag(*hpf_out, "hpf_out")
    r6 = R(a, "R6", "5.6k", hpf_out[0] - 16, hpf_out[1] + 16)
    a.wire(*hpf_out, r6["a"][0], r6["a"][1])
    a.flag(*r6["b"], GND)

    # ════════════════════════════════════════════════════════════════════════
    # TONE & MIX
    # ════════════════════════════════════════════════════════════════════════
    # RV3 wet level 100k (50k mid): hpf_out -> wiper -> GND.
    rv3a = R(a, "RV3a", "50k", hpf_out[0] + 112, hpf_out[1])
    a.wire(*hpf_out, rv3a["a"][0], hpf_out[1])
    a.wire(rv3a["a"][0], hpf_out[1], rv3a["a"][0], rv3a["a"][1])
    rv3w = rv3a["b"]
    a.flag(*rv3w, "rv3_wiper")
    rv3b = R(a, "RV3b", "50k", hpf_out[0] + 112, rv3w[1] + 16)
    a.wire(*rv3w, rv3b["a"][0], rv3b["a"][1])
    a.flag(*rv3b["b"], GND)

    # Mix summing node "mix_top": wet (from RV3 wiper) + dry (via Rdry).
    mix_top = (rv3w[0] + 160, rv3w[1] - 32)
    a.flag(*mix_top, "mix_top")
    a.wire(rv3w[0], rv3w[1], mix_top[0], rv3w[1])
    a.wire(mix_top[0], rv3w[1], mix_top[0], mix_top[1])

    # Dry bus from u1_out_buf along the bottom, up through Rdry to mix_top.
    DRY_BUS = 1360
    a.wire(u1_buf[0], u1_buf[1], u1_buf[0], DRY_BUS)
    a.wire(u1_buf[0], DRY_BUS, mix_top[0] + 144, DRY_BUS)
    a.wire(mix_top[0] + 144, DRY_BUS, mix_top[0] + 144, mix_top[1] + 96)
    rdry = R(a, "Rdry", "10k", mix_top[0] + 128, mix_top[1])
    a.wire(rdry["b"][0], rdry["b"][1], mix_top[0] + 144, mix_top[1] + 96)
    a.wire(rdry["a"][0], rdry["a"][1], rdry["a"][0], mix_top[1] - 32)
    a.wire(rdry["a"][0], mix_top[1] - 32, mix_top[0], mix_top[1] - 32)
    a.wire(mix_top[0], mix_top[1] - 32, mix_top[0], mix_top[1])

    # RV2 mix 100k (50k mid): mix_top -> wiper(mix_node) -> GND.
    rv2a = R(a, "RV2a", "50k", mix_top[0] - 16, mix_top[1])
    a.wire(*mix_top, rv2a["a"][0], rv2a["a"][1])
    mix_node = rv2a["b"]
    a.flag(*mix_node, "mix_node")
    rv2b = R(a, "RV2b", "50k", mix_top[0] - 16, mix_node[1] + 16)
    a.wire(*mix_node, rv2b["a"][0], rv2b["a"][1])
    a.flag(*rv2b["b"], GND)

    # C_bright 47p across RV2 (mix_top -> mix_node).
    cb = C(a, "C_bright", "47p", mix_top[0] + 96, mix_top[1] + 16)
    a.wire(cb["a"][0], cb["a"][1], cb["a"][0], mix_top[1])
    a.wire(cb["a"][0], mix_top[1], mix_top[0], mix_top[1])
    a.wire(cb["b"][0], cb["b"][1], cb["b"][0], mix_node[1])
    a.wire(cb["b"][0], mix_node[1], mix_node[0], mix_node[1])

    # ════════════════════════════════════════════════════════════════════════
    # OUTPUT BUFFER
    # ════════════════════════════════════════════════════════════════════════
    u3 = OPA(a, "U3", mix_node[0] + 160, mix_node[1] - 48)
    a.flag(*u3["vp"], VP)
    a.flag(*u3["vn"], VN)
    a.wire(mix_node[0], mix_node[1], u3["inp"][0] - 32, mix_node[1])
    a.wire(u3["inp"][0] - 32, mix_node[1], u3["inp"][0] - 32, u3["inp"][1])
    a.wire(u3["inp"][0] - 32, u3["inp"][1], *u3["inp"])
    # Unity feedback OUT -> IN-.
    a.polyline([u3["out"], (u3["out"][0] + 32, u3["out"][1]),
                (u3["out"][0] + 32, u3["out"][1] + 144),
                (u3["inp"][0] - 64, u3["out"][1] + 144),
                (u3["inp"][0] - 64, u3["inn"][1]), u3["inn"]])

    # R7 100R series output (horizontal R90).
    r7 = R(a, "R7", "100", u3["out"][0] + 112, u3["out"][1] - 16, rot="R90")
    a.wire(u3["out"][0], u3["out"][1], r7["b"][0], r7["b"][1])
    v_out = r7["a"]
    a.flag(*v_out, "V_out")

    # J2 output jack: 47k load (MC100 input model) -> GND.
    rload = R(a, "Rload_J2", "47k", v_out[0] - 16, v_out[1] + 16)
    a.wire(*v_out, rload["a"][0], rload["a"][1])
    a.flag(*rload["b"], GND)
    a.text(v_out[0] - 8, v_out[1] - 40, "Left", 2, "J2 -> MC100 input")

    # ════════════════════════════════════════════════════════════════════════
    # POWER SUPPLY  (idealised rails, bottom-left)
    # ════════════════════════════════════════════════════════════════════════
    PSY = 1560
    a.text(160, PSY - 80, "Left", 3, "Power Supply — idealised +/-15V rails")

    # Vpos = +15V: + to +15V rail, - to GND.
    vpos = V(a, "Vpos", "15", 256, PSY)
    a.flag(vpos["p"][0], vpos["p"][1] - 16, VP)
    a.wire(vpos["p"][0], vpos["p"][1] - 16, *vpos["p"])
    a.flag(*vpos["n"], GND)

    # Vneg = -15V: + to GND, - to -15V rail (so node sits at -15V).
    vneg = V(a, "Vneg", "15", 448, PSY)
    a.flag(vneg["p"][0], vneg["p"][1] - 16, GND)
    a.wire(vneg["p"][0], vneg["p"][1] - 16, *vneg["p"])
    a.flag(vneg["n"][0], vneg["n"][1], VN)

    # Bulk rail caps C15 (+15V) / C16 (-15V), 10uF.
    c15 = C(a, "C15", "10u", 640, PSY - 64)
    a.flag(*c15["a"], VP)
    a.flag(*c15["b"], GND)
    c16 = C(a, "C16", "10u", 800, PSY - 64)
    a.flag(*c16["a"], VN)
    a.flag(*c16["b"], GND)

    # Decoupling C5..C8 100n (one per op-amp rail, lumped).
    for i, name in enumerate(("C5", "C6", "C7", "C8")):
        x = 1000 + i * 160
        cc = C(a, name, "100n", x, PSY - 64)
        a.flag(*cc["a"], VP if i % 2 == 0 else VN)
        a.flag(*cc["b"], GND)
    a.text(992, PSY - 100, "Left", 2,
           "C5-C8: 100n op-amp supply decoupling (per rail, per device)")

    return a.render()


def main():
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "ghost_spring.asc")
    content = build()
    # LTspice XVII on Windows reads .asc as ANSI (cp1252); write that encoding
    # explicitly so non-ASCII glyphs (e.g. the em dash in the title) round-trip
    # identically regardless of the host locale.
    with open(out_path, "w", newline="", encoding="cp1252") as fh:
        fh.write(content)

    rows = content.split("\r\n")
    counts = {}
    for kind in ("WIRE", "FLAG", "SYMBOL", "TEXT"):
        counts[kind] = sum(1 for r in rows if r.startswith(kind + " "))
    insts = [r.split(None, 2)[2] for r in rows if r.startswith("SYMATTR InstName")]

    print(f"Wrote {out_path}")
    print(f"  lines        : {len(rows) - 1}")
    print(f"  WIRE         : {counts['WIRE']}")
    print(f"  FLAG (nets)  : {counts['FLAG']}")
    print(f"  SYMBOL       : {counts['SYMBOL']}")
    print(f"  TEXT/dirs    : {counts['TEXT']}")
    print(f"  instances    : {len(insts)} -> {', '.join(insts)}")
    print("Directives embedded: .op, .ac, .tran, .meas, .model BD139, K1 L1 L2 0.98")
    print("Open in LTspice XVII (File > Open) and press Run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
