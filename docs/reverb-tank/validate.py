#!/usr/bin/env python3
"""
validate.py - Consistency gate for the Ghost Spring parameter cascade.

Checks (WITHOUT regenerating anything) that the three downstream artifacts agree
with circuit_params.py (the single source of truth):

  1. stages/stage_06_full.net  - every R/C/L/K value matches the constant.
  1b. per-stage netlists       - driver stages carry R5=68; stage_05_psu places
                                 RF2/RF3 on the DC rails (not the AC secondary).
  1c. mix topology             - RV2 (Mix) is wired as a 3-terminal PASSIVE
                                 BLEND, not a volume knob: Rdry feeds the pot's
                                 dry end (not the wiper), RV2a/RV2b form a chain
                                 through the wiper, no near-zero Rwet shorts the
                                 dry node, and C_bright spans the full pot. This
                                 is the guard for the Rwet=0.001 short bug.
  2. circuit-params.md         - spot-check key derived values AND check every
                                 R/C component row's value against the constant.
  3. stages/test-assertions.md - pass-window numbers match the tolerance tuples.

Exit 0 if everything is consistent; exit 1 with a clear report otherwise.
This is the CI check: if validate.py passes, the docs are in sync. To FIX drift,
edit circuit_params.py and run sync.py (which regenerates, then re-validates).

Usage: python docs/reverb-tank/validate.py
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STAGES = os.path.join(HERE, "stages")
sys.path.insert(0, STAGES)
import circuit_params as P  # noqa: E402

NET = os.path.join(STAGES, "stage_06_full.net")
NET6_AC = os.path.join(STAGES, "stage_06_full_ac.net")
NET6_TRAN = os.path.join(STAGES, "stage_06_full_tran.net")
NET5_TRAN = os.path.join(STAGES, "stage_05_psu_tran.net")
# Stage 7 pot-position sweep variants (GitHub issue #43).
NET6_DWELL_MIN = os.path.join(STAGES, "stage_06_full_dwell_min.net")
NET6_DWELL_MAX = os.path.join(STAGES, "stage_06_full_dwell_max.net")
NET6_MIX_CCW = os.path.join(STAGES, "stage_06_full_mix_ccw.net")
NET6_MIX_CW = os.path.join(STAGES, "stage_06_full_mix_cw.net")
NET6_DWELL_MAX_MIX_CW = os.path.join(STAGES, "stage_06_full_dwell_max_mix_cw.net")
# Dynamic / overload variants whose .meas live in NO other netlist.
NET2_TRAN = os.path.join(STAGES, "stage_02_driver_tran.net")
NET4_OVERLOAD = os.path.join(STAGES, "stage_04_input_protect_overload.net")
# Stage 8 realistic hardware stress variants.
NET5_LOW_MAINS = os.path.join(STAGES, "stage_05_psu_low_mains.net")
NET6_VOS = os.path.join(STAGES, "stage_06_full_vos.net")
NET6_LO_BETA = os.path.join(STAGES, "stage_06_full_lo_beta.net")
PARAMS_MD = os.path.join(HERE, "circuit-params.md")
ASSERT_MD = os.path.join(STAGES, "test-assertions.md")

# Per-stage netlists (W2): all stages that carry the BD139 driver, plus the PSU.
STAGE_NETS = {
    "stage_02_driver": os.path.join(STAGES, "stage_02_driver.net"),
    "stage_03_transformer": os.path.join(STAGES, "stage_03_transformer.net"),
    "stage_04_input_protect": os.path.join(STAGES, "stage_04_input_protect.net"),
    "stage_05_psu": os.path.join(STAGES, "stage_05_psu.net"),
}

errors = []
checks = 0


def fail(msg):
    errors.append(msg)


def _g(x):
    """'%g' with the doc's Unicode minus sign."""
    return ("%g" % x).replace("-", "−")


def _g1(x):
    """One-decimal form with Unicode minus (15.0, 1.0, −15.0)."""
    return ("%.1f" % x).replace("-", "−")


# ---------------------------------------------------------------------------
# 1. NETLIST: every R/C/L/K value must equal its circuit_params constant.
# ---------------------------------------------------------------------------
# Map: netlist instance name -> circuit_params value string. Only components
# whose value is a named constant are checked (models/sources are checked
# elsewhere or are topology, not single-valued).
NET_VALUE_MAP = {
    # resistors
    "R1": P.R1, "R2": P.R2, "R3": P.R3, "R3b": P.R3B, "R4": P.R4, "R5": P.R5,
    "Ri": P.RI, "Rf": P.RF, "R6": P.R6, "Rbias": P.RBIAS, "Rdry": P.RDRY,
    "R7": P.R7, "Rload": P.RLOAD,
    "R_tank_in": P.R_TANK_IN, "R_tank_mech": P.R_TANK_MECH,
    "R_tank_out": P.R_TANK_OUT,
    "R_bleed1": P.R_BLEED1, "R_bleed2": P.R_BLEED2, "RF2": P.RF2, "RF3": P.RF3,
    "RV1a": P.RV1A, "RV1b": P.RV1B, "RV2a": P.RV2A, "RV2b": P.RV2B,
    "RV3a": P.RV3A, "RV3b": P.RV3B,
    # capacitors
    "C_in": P.C_IN, "C_drive": P.C_DRIVE, "C2": P.C2, "C3": P.C3, "C4": P.C4,
    "C_bright": P.C_BRIGHT, "C5": P.C5, "C6": P.C6, "C7": P.C7, "C8": P.C8,
    "C11": P.C11, "C12": P.C12, "C13": P.C13, "C14": P.C14, "C15": P.C15,
    "C16": P.C16, "C17": P.C17, "C18": P.C18, "C_tank_mech": P.C_TANK_MECH,
    # inductors (netlist appends " Rser=0"; we compare the value token only)
    "L1": P.L1, "L2": P.L2, "L_tank": P.L_TANK, "L_tank_mech": P.L_TANK_MECH,
    "L_tank_out": P.L_TANK_OUT,
    # coupling coefficient
    "K1": P.K1,
}


def check_netlist():
    global checks
    with open(NET) as f:
        lines = f.readlines()

    seen = set()
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("*") or line.startswith("."):
            continue
        parts = line.split()
        name = parts[0]
        if name not in NET_VALUE_MAP:
            continue
        seen.add(name)
        expected = NET_VALUE_MAP[name]
        if name == "K1":
            # K1 L1 L2 0.98 -> value is the 4th token
            actual = parts[3] if len(parts) >= 4 else "?"
        else:
            # R/C: "<name> <n1> <n2> <value>"; L: "... <value> Rser=0"
            actual = parts[3] if len(parts) >= 4 else "?"
        checks += 1
        if actual != expected:
            fail("netlist: %s value '%s' != circuit_params '%s'"
                 % (name, actual, expected))

    missing = set(NET_VALUE_MAP) - seen
    if missing:
        fail("netlist: components in circuit_params not found in %s: %s"
             % (os.path.basename(NET), ", ".join(sorted(missing))))


def _net_card(path, instance):
    """Return the netlist card (token list) whose first token == instance, or
    None. Skips comments (*) and directives (.)."""
    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("*") or line.startswith("."):
                continue
            parts = line.split()
            if parts and parts[0] == instance:
                return parts
    return None


# ---------------------------------------------------------------------------
# 1b. PER-STAGE netlists (W2): the driver stages must carry R5=68 with its
#     circuit_params value, and stage_05_psu must place RF2/RF3 on the DC rails
#     (reg_pos->+15V, reg_neg->-15V), NOT on the AC secondary.
# ---------------------------------------------------------------------------
def check_stage_netlists():
    global checks
    for stage, path in STAGE_NETS.items():
        checks += 1
        if not os.path.exists(path):
            fail("stage netlist missing: %s" % os.path.basename(path))
            continue

        # Every driver-bearing stage carries R5 at circuit_params.R5.
        r5 = _net_card(path, "R5")
        checks += 1
        if r5 is None:
            fail("%s: R5 card not found (driver stage must include R5)" % stage)
        elif len(r5) < 4 or r5[3] != P.R5:
            fail("%s: R5 value '%s' != circuit_params '%s'"
                 % (stage, r5[3] if len(r5) >= 4 else "?", P.R5))

        # The PSU stage must place RF2/RF3 on the regulated DC rails.
        if stage == "stage_05_psu":
            for fuse, expect_nodes, val in (
                ("RF2", {"reg_pos", "+15V"}, P.RF2),
                ("RF3", {"reg_neg", "-15V"}, P.RF3),
            ):
                checks += 1
                card = _net_card(path, fuse)
                if card is None or len(card) < 4:
                    fail("%s: %s card not found / malformed" % (stage, fuse))
                    continue
                nodes = set(card[1:3])
                if nodes != expect_nodes:
                    fail("%s: %s should bridge %s (DC rail), got %s"
                         % (stage, fuse, expect_nodes, nodes))
                if {"ac_pos", "ac_neg"} & nodes:
                    fail("%s: %s wrongly on AC secondary node(s) %s"
                         % (stage, fuse, nodes & {"ac_pos", "ac_neg"}))
                if card[3] != val:
                    fail("%s: %s value '%s' != circuit_params '%s'"
                         % (stage, fuse, card[3], val))


# ---------------------------------------------------------------------------
# 1c. MIX TOPOLOGY (W3): stage_06_full.net must wire the Mix pot (RV2) as a
#     3-terminal PASSIVE BLEND, not a volume knob. The original bug shorted the
#     wet source onto the SAME node as the dry path through a near-zero Rwet
#     (Rwet = 0.001Ω), which clamps that node to the wet signal and attenuates
#     the dry path to ~-140dB. This guard is what would have caught it:
#       - Rdry must feed u1_buf into a DRY node that is NOT the wiper itself.
#       - RV2a and RV2b must form a CHAIN (dry_end -> wiper -> wet_end), i.e.
#         they must NOT both terminate on the same node (that is the volume-knob
#         topology: both halves to the wiper / both ends shorted).
#       - No near-zero (<=0.01Ω) resistor may tie the wet source onto the SAME
#         node Rdry feeds (the dry end) -- that is the short that killed the dry
#         path.
#       - C_bright must span the DRY end to the WET end (the full pot), not a
#         single half.
# ---------------------------------------------------------------------------
def _net_value_float(tok):
    """Parse a SPICE resistor value token to ohms, or None if unparseable."""
    return _spice_to_float(tok)


def check_mix_topology():
    global checks
    with open(NET) as f:
        cards = {}
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("*") or line.startswith("."):
                continue
            parts = line.split()
            cards[parts[0]] = parts  # last card wins (names are unique anyway)

    rdry = cards.get("Rdry")
    rv2a = cards.get("RV2a")
    rv2b = cards.get("RV2b")
    cbright = cards.get("C_bright")

    # (a) Rdry: u1_buf -> dry_end. dry_end must NOT be the wiper (mix_node).
    checks += 1
    if rdry is None or len(rdry) < 4:
        fail("mix topology: Rdry card missing/malformed in stage_06_full.net")
        dry_end = None
    else:
        rdry_nodes = rdry[1:3]
        if "u1_buf" not in rdry_nodes:
            fail("mix topology: Rdry must connect from u1_buf, got %s" % rdry_nodes)
        dry_end = rdry_nodes[1] if rdry_nodes[0] == "u1_buf" else rdry_nodes[0]
        if dry_end == "mix_node":
            fail("mix topology: Rdry feeds the wiper (mix_node) directly -- the "
                 "dry path must land on the pot's CCW end, not the wiper")

    # (b) RV2a / RV2b must form a chain, not both point at the same node.
    checks += 1
    if rv2a is None or rv2b is None or len(rv2a) < 3 or len(rv2b) < 3:
        fail("mix topology: RV2a/RV2b card missing/malformed")
    else:
        a_nodes = set(rv2a[1:3])
        b_nodes = set(rv2b[1:3])
        # A chain shares EXACTLY one node (the wiper, mix_node) and each half has
        # one distinct end. Volume-knob wiring shares both ends (a == b) or both
        # halves dead-end on the wiper.
        if a_nodes == b_nodes:
            fail("mix topology: RV2a and RV2b span the SAME two nodes %s -- that "
                 "is a volume-knob/short, not a 3-terminal blend" % a_nodes)
        shared = a_nodes & b_nodes
        if shared != {"mix_node"}:
            fail("mix topology: RV2a/RV2b must share exactly the wiper node "
                 "mix_node; shared=%s (RV2a=%s RV2b=%s)"
                 % (shared, a_nodes, b_nodes))

    # (c) No near-zero R may tie a wet source onto the SAME node Rdry feeds.
    #     Scan every resistor; if a <=0.01Ω resistor touches dry_end, it is the
    #     classic Rwet short that collapses the blend.
    checks += 1
    if dry_end is not None:
        for name, parts in cards.items():
            if not name[0] in ("R", "r"):
                continue
            if len(parts) < 4:
                continue
            val = _net_value_float(parts[3])
            if val is None:
                continue
            nodes = set(parts[1:3])
            if val <= 0.01 and dry_end in nodes:
                fail("mix topology: %s is a near-zero (%sΩ) resistor tying %s "
                     "onto the dry node %s -- this shorts the dry path (the "
                     "original Rwet=0.001 bug)"
                     % (name, parts[3], nodes - {dry_end}, dry_end))

    # (d) C_bright must span the full pot: dry_end <-> wet_end (the two pot ends,
    #     NOT including the wiper mix_node).
    checks += 1
    if cbright is None or len(cbright) < 3:
        fail("mix topology: C_bright card missing/malformed")
    elif dry_end is not None:
        cb_nodes = set(cbright[1:3])
        # Wet end = RV2b's end that is not the wiper.
        wet_end = None
        if rv2b is not None and len(rv2b) >= 3:
            b_nodes = rv2b[1:3]
            wet_end = b_nodes[1] if b_nodes[0] == "mix_node" else b_nodes[0]
        if "mix_node" in cb_nodes:
            fail("mix topology: C_bright touches the wiper (mix_node) -- it must "
                 "bridge the two pot ends (dry<->wet), not a single half")
        if dry_end not in cb_nodes:
            fail("mix topology: C_bright must include the dry end %s; got %s"
                 % (dry_end, cb_nodes))
        if wet_end is not None and wet_end not in cb_nodes:
            fail("mix topology: C_bright must include the wet end %s; got %s"
                 % (wet_end, cb_nodes))


# ---------------------------------------------------------------------------
# 1d. HPF wired to the WET path only (P1.3): the post-recovery high-pass
#     (C4 + R6) must sit in the WET signal chain between U2's output and the
#     Tone/Mix stage, and the DRY path (u1_buf -> mix_dry) must be DC-coupled
#     (purely resistive, NO series capacitor). The bug class this guards: a cap
#     accidentally inserted in the dry path (rolling off dry bass) or the HPF
#     wandering onto the dry node.
# ---------------------------------------------------------------------------
def _load_cards(path):
    """Return {instance: token-list} for every element card in a netlist."""
    cards = {}
    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("*") or line.startswith("."):
                continue
            parts = line.split()
            cards[parts[0]] = parts
    return cards


def check_hpf_wet_only():
    global checks
    cards = _load_cards(NET)

    c4 = cards.get("C4")
    r6 = cards.get("R6")
    rdry = cards.get("Rdry")

    # (a) C4 and R6 are the wet HPF: C4 from u2_out (recovery output) into
    #     hpf_out, R6 shunting hpf_out to ground. Both nodes are wet-chain nodes.
    checks += 1
    if c4 is None or len(c4) < 4:
        fail("hpf wet-only: C4 card missing/malformed in stage_06_full.net")
    else:
        c4_nodes = set(c4[1:3])
        if c4_nodes != {"u2_out", "hpf_out"}:
            fail("hpf wet-only: C4 must couple u2_out<->hpf_out (wet chain), "
                 "got %s" % c4_nodes)

    checks += 1
    if r6 is None or len(r6) < 4:
        fail("hpf wet-only: R6 card missing/malformed")
    else:
        r6_nodes = set(r6[1:3])
        if r6_nodes != {"hpf_out", "0"}:
            fail("hpf wet-only: R6 must shunt hpf_out<->0 (wet HPF), got %s"
                 % r6_nodes)

    # (b) The DRY path u1_buf -> mix_dry must be a single resistive hop (Rdry),
    #     with NO capacitor in series. Trace every component on u1_buf toward
    #     mix_dry and assert nothing on that path is a capacitor.
    checks += 1
    if rdry is None or len(rdry) < 4:
        fail("hpf wet-only: Rdry card missing/malformed")
    else:
        rdry_nodes = set(rdry[1:3])
        if rdry_nodes != {"u1_buf", "mix_dry"}:
            fail("hpf wet-only: Rdry must connect u1_buf<->mix_dry directly, "
                 "got %s" % rdry_nodes)
        if not rdry[0][0] in ("R", "r"):
            fail("hpf wet-only: dry coupler %s is not a resistor" % rdry[0])

    # (c) The dry SERIES path u1_buf -> mix_dry must be DC-coupled: no capacitor
    #     in series with it. A series-coupling cap would sit on u1_buf (the dry
    #     source node feeding Rdry), so forbid ANY cap on u1_buf. (C_bright is
    #     legitimately allowed: it bridges the two pot ends mix_dry<->mix_wet,
    #     i.e. it is in PARALLEL across the pot, not in series in the dry path;
    #     a cap on mix_dry is only forbidden if its other end is NOT the wet pot
    #     end mix_wet -- that would interrupt/AC-couple the dry signal flow.)
    checks += 1
    for name, parts in cards.items():
        if name[0] not in ("C", "c") or len(parts) < 3:
            continue
        nodes = set(parts[1:3])
        if "u1_buf" in nodes:
            fail("hpf wet-only: capacitor %s sits on the dry source node u1_buf "
                 "-- the dry path u1_buf->mix_dry must be DC-coupled (no series "
                 "cap)" % name)
        elif "mix_dry" in nodes and nodes != {"mix_dry", "mix_wet"}:
            fail("hpf wet-only: capacitor %s touches the dry node mix_dry with "
                 "other end %s (only the C_bright bridge mix_dry<->mix_wet is "
                 "allowed) -- the dry path must be DC-coupled"
                 % (name, nodes - {"mix_dry"}))


# ---------------------------------------------------------------------------
# 1e. OP-AMP FEEDBACK topology (P1.4): each op-amp's feedback wiring must be
#     correct, read from the X§Un subckt cards.
#       Card form: X§Un <in+> <in-> <V+> <V-> <out> level2 ...
#     U1 (input buffer)  : unity-gain follower -> out tied to inverting input
#                          (directly, or through R2 which is acceptable).
#     U2 (recovery 214x) : Ri u2_inv->0 (lower leg), Rf u2_out->u2_inv
#                          (feedback), signal into u2_in_pos (non-inverting),
#                          and 1 + Rf/Ri must land in RECOV_GAIN_WINDOW.
#     U3 (output buffer) : unity-gain follower -> out tied to inverting input.
# ---------------------------------------------------------------------------
def _opamp_pins(cards, inst):
    """Return (in_pos, in_neg, out) for op-amp instance 'Un' from its X§Un card,
    or None if absent/malformed. The netlist names it 'X§Un'."""
    card = cards.get("X§" + inst)
    if card is None or len(card) < 6:
        return None
    # X§Un <in+> <in-> <V+> <V-> <out> ...
    return card[1], card[2], card[5]


def check_opamp_feedback():
    global checks
    cards = _load_cards(NET)

    # --- U1: unity-gain follower (out == inverting input, direct or via R2) ---
    checks += 1
    u1 = _opamp_pins(cards, "U1")
    if u1 is None:
        fail("opamp feedback: U1 (X§U1) card missing/malformed")
    else:
        in_pos, in_neg, out = u1
        direct = (in_neg == out)
        via_r2 = False
        r2 = cards.get("R2")
        if r2 is not None and len(r2) >= 3:
            via_r2 = set(r2[1:3]) == {out, in_neg}
        if not (direct or via_r2):
            fail("opamp feedback: U1 must be a unity follower -- inverting "
                 "input (%s) tied to output (%s) directly or through R2; got "
                 "neither" % (in_neg, out))

    # --- U2: non-inverting 214x. Ri u2_inv->0, Rf u2_out->u2_inv, sig at in+ ---
    u2 = _opamp_pins(cards, "U2")
    ri = cards.get("Ri")
    rf = cards.get("Rf")

    checks += 1
    if u2 is None:
        fail("opamp feedback: U2 (X§U2) card missing/malformed")
    else:
        in_pos, in_neg, out = u2
        if in_pos != "u2_in_pos":
            fail("opamp feedback: U2 signal must enter the non-inverting input "
                 "u2_in_pos; got in+=%s" % in_pos)
        if in_neg != "u2_inv":
            fail("opamp feedback: U2 inverting input expected u2_inv; got %s"
                 % in_neg)
        if out != "u2_out":
            fail("opamp feedback: U2 output expected u2_out; got %s" % out)

    checks += 1
    if ri is None or len(ri) < 4:
        fail("opamp feedback: Ri (U2 lower feedback leg) card missing/malformed")
    elif set(ri[1:3]) != {"u2_inv", "0"}:
        fail("opamp feedback: Ri must connect u2_inv<->0 (gain-set lower leg), "
             "got %s" % set(ri[1:3]))

    checks += 1
    if rf is None or len(rf) < 4:
        fail("opamp feedback: Rf (U2 feedback resistor) card missing/malformed")
    elif set(rf[1:3]) != {"u2_out", "u2_inv"}:
        fail("opamp feedback: Rf must connect u2_out<->u2_inv (feedback), got %s"
             % set(rf[1:3]))

    # Gain formula: 1 + Rf/Ri within RECOV_GAIN_WINDOW.
    checks += 1
    rf_val = _spice_to_float(rf[3]) if rf and len(rf) >= 4 else None
    ri_val = _spice_to_float(ri[3]) if ri and len(ri) >= 4 else None
    if rf_val is None or ri_val is None or ri_val == 0:
        fail("opamp feedback: cannot derive U2 gain (Rf=%r, Ri=%r)"
             % (rf[3] if rf else None, ri[3] if ri else None))
    else:
        gain = 1.0 + rf_val / ri_val
        lo, hi = P.RECOV_GAIN_WINDOW
        if not (lo <= gain <= hi):
            fail("opamp feedback: U2 gain 1+Rf/Ri = %g outside RECOV_GAIN_WINDOW "
                 "%s" % (gain, P.RECOV_GAIN_WINDOW))

    # --- U3: unity-gain follower (out == inverting input) ---
    checks += 1
    u3 = _opamp_pins(cards, "U3")
    if u3 is None:
        fail("opamp feedback: U3 (X§U3) card missing/malformed")
    else:
        in_pos, in_neg, out = u3
        if in_neg != out:
            fail("opamp feedback: U3 must be a unity follower -- inverting "
                 "input (%s) tied to output (%s); got in-=%s out=%s"
                 % (in_neg, out, in_neg, out))


# ---------------------------------------------------------------------------
# 1f. DECOUPLING caps on the correct rails (P1.5): C5/C7 must bridge +15V->0
#     and C6/C8 must bridge -15V->0. All four must exist (a missing supply
#     bypass invites HF instability / oscillation that no value-only check sees).
# ---------------------------------------------------------------------------
def check_decoupling_caps():
    global checks
    cards = _load_cards(NET)
    for name, expect in (
        ("C5", {"+15V", "0"}), ("C7", {"+15V", "0"}),
        ("C6", {"-15V", "0"}), ("C8", {"-15V", "0"}),
    ):
        checks += 1
        card = cards.get(name)
        if card is None or len(card) < 4:
            fail("decoupling: %s card missing/malformed (supply bypass absent)"
                 % name)
            continue
        nodes = set(card[1:3])
        if nodes != expect:
            fail("decoupling: %s must bridge %s, got %s" % (name, expect, nodes))
        # VALUE check: a present-but-wrong-valued bypass (e.g. 100p) decouples
        # nothing at audio HF. Confirm the cap value equals DECOUPLE_VAL (100n).
        checks += 1
        want = _spice_to_float(P.DECOUPLE_VAL)
        got = _spice_to_float(card[3])
        if got is None or want is None or abs(got - want) > abs(want) * 1e-9:
            fail("decoupling: %s value '%s' != DECOUPLE_VAL '%s' (a wrong-valued "
                 "bypass passes a presence check but bypasses nothing at HF)"
                 % (name, card[3], P.DECOUPLE_VAL))


# ---------------------------------------------------------------------------
# 1f-bis. D3 FLYBACK CLAMP orientation (P1.6): D3 clamps Q1's collector to the
#     +15V rail. SPICE D-card form is 'D3 <anode> <cathode> <model>', so D3 MUST
#     read 'D3 q1_c +15V ...': anode at the collector, cathode at +15V. A reversed
#     D3 (anode/cathode swapped) is forward-biased by the rail and shorts the
#     collector, AND offers no flyback protection -- the transformer kick then
#     destroys Q1. Presence alone (test_sync) is not enough; the orientation is
#     the load-bearing property, so gate it statically here too.
# ---------------------------------------------------------------------------
def check_d3_flyback():
    global checks
    cards = _load_cards(NET)
    checks += 1
    d3 = cards.get("D3")
    if d3 is None or len(d3) < 4:
        fail("D3 flyback: card missing/malformed in stage_06_full.net")
        return
    anode, cathode = d3[1], d3[2]
    if anode != "q1_c" or cathode != "+15V":
        fail("D3 flyback: must be 'D3 q1_c +15V <model>' (anode=collector, "
             "cathode=+15V rail); got anode=%s cathode=%s -- a reversed D3 shorts "
             "the collector and gives no flyback protection" % (anode, cathode))


# ---------------------------------------------------------------------------
# 1f-ter. RV1 (Dwell pot) TOPOLOGY: every netlist that carries the Dwell pot must
#     wire it the SAME way as stage_06_full and builder-guide.md:
#       RV1a rv1_wiper 0       (the wiper-to-GND half)
#       RV1b u1_buf rv1_wiper  (the signal-to-wiper half)
#     The reverse wiring (RV1a u1_buf rv1_wiper / RV1b rv1_wiper 0) inverts the
#     Dwell control sense (CW would minimise drive instead of maximising it) and
#     diverges from the builder guide. Check EVERY netlist that contains an RV1a
#     or RV1b card so a single mis-wired stage cannot ship.
# ---------------------------------------------------------------------------
# mvp_reverb.net is the pre-Stage-2 prototype (not part of the sync cascade and
# carried frozen as a historical artifact), so it is excluded from the maintained-
# stage Dwell-pot topology check.
RV1_TOPOLOGY_SKIP = {"mvp_reverb.net"}


def check_rv1_topology():
    global checks
    for fname in sorted(os.listdir(STAGES)):
        if not fname.endswith(".net") or fname in RV1_TOPOLOGY_SKIP:
            continue
        path = os.path.join(STAGES, fname)
        rv1a = _net_card(path, "RV1a")
        rv1b = _net_card(path, "RV1b")
        if rv1a is None and rv1b is None:
            continue  # netlist has no Dwell pot (e.g. PSU stage)
        checks += 1
        if rv1a is None or len(rv1a) < 3:
            fail("rv1 topology: %s has RV1b but no/malformed RV1a card" % fname)
        elif rv1a[1:3] != ["rv1_wiper", "0"]:
            fail("rv1 topology: %s RV1a must be 'RV1a rv1_wiper 0' (wiper-to-GND "
                 "half), got nodes %s" % (fname, rv1a[1:3]))
        checks += 1
        if rv1b is None or len(rv1b) < 3:
            fail("rv1 topology: %s has RV1a but no/malformed RV1b card" % fname)
        elif rv1b[1:3] != ["u1_buf", "rv1_wiper"]:
            fail("rv1 topology: %s RV1b must be 'RV1b u1_buf rv1_wiper' (signal-"
                 "to-wiper half), got nodes %s" % (fname, rv1b[1:3]))


# ---------------------------------------------------------------------------
# 1g. DERIVED transfer functions (P1.8): confirm the component VALUES actually
#     produce the specified transfer function, not just that they exist.
#       recovery gain = 1 + Rf/Ri          -> RECOV_GAIN_WINDOW
#       hpf corner    = 1/(2*pi*R6*C4)     -> HPF_CORNER_WINDOW
# ---------------------------------------------------------------------------
def check_derived_transfer():
    global checks
    import math
    cards = _load_cards(NET)

    rf = cards.get("Rf")
    ri = cards.get("Ri")
    r6 = cards.get("R6")
    c4 = cards.get("C4")

    # Gain derived from the netlist values.
    checks += 1
    rf_val = _spice_to_float(rf[3]) if rf and len(rf) >= 4 else None
    ri_val = _spice_to_float(ri[3]) if ri and len(ri) >= 4 else None
    if rf_val is None or ri_val is None or ri_val == 0:
        fail("derived: cannot compute gain from netlist (Rf=%r, Ri=%r)"
             % (rf[3] if rf and len(rf) >= 4 else None,
                ri[3] if ri and len(ri) >= 4 else None))
    else:
        gain = 1.0 + rf_val / ri_val
        lo, hi = P.RECOV_GAIN_WINDOW
        if not (lo <= gain <= hi):
            fail("derived: gain 1+Rf/Ri = %g (Rf=%s Ri=%s) outside "
                 "RECOV_GAIN_WINDOW %s" % (gain, rf[3], ri[3], P.RECOV_GAIN_WINDOW))

    # HPF corner derived from the netlist values.
    checks += 1
    r6_val = _spice_to_float(r6[3]) if r6 and len(r6) >= 4 else None
    c4_val = _spice_to_float(c4[3]) if c4 and len(c4) >= 4 else None
    if not r6_val or not c4_val:
        fail("derived: cannot compute HPF corner from netlist (R6=%r, C4=%r)"
             % (r6[3] if r6 and len(r6) >= 4 else None,
                c4[3] if c4 and len(c4) >= 4 else None))
    else:
        corner = 1.0 / (2.0 * math.pi * r6_val * c4_val)
        lo, hi = P.HPF_CORNER_WINDOW
        if not (lo <= corner <= hi):
            fail("derived: HPF corner 1/(2*pi*R6*C4) = %g Hz (R6=%s C4=%s) "
                 "outside HPF_CORNER_WINDOW %s"
                 % (corner, r6[3], c4[3], P.HPF_CORNER_WINDOW))


# ---------------------------------------------------------------------------
# 1h. ANALYSIS-VARIANT netlists (C1/W2): the ripple, AC, and tran assertions
#     live ONLY in their analysis-specific netlist. The committed op netlist
#     never runs them, so without a tran/ac variant the < 10mVpp ripple spec
#     (and the recov_gain / hpf_m3db / vout_pk / osc_ratio specs) are documented
#     but verified in NO committed file. Confirm each variant exists and carries
#     its expected .meas directives.
# ---------------------------------------------------------------------------
def _netlist_meas_names(path):
    """Return the set of .meas result names declared in a netlist (the token
    after the analysis type), or None if the file is missing."""
    if not os.path.exists(path):
        return None
    names = set()
    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line.lower().startswith(".meas"):
                continue
            parts = line.split()
            # .meas <ANALYSIS> <name> ...
            if len(parts) >= 3:
                names.add(parts[2])
    return names


def check_variant_netlists():
    global checks
    for path, expected in (
        # Stage 2 dynamic driver: D3 idle + driver no-clip live only here.
        (NET2_TRAN, {"d3_pk", "drv_pk", "drv_rms"}),
        # Stage 4 overload: clamp-window + clamp-conduction live only here.
        (NET4_OVERLOAD,
         {"u1pos_hi", "u1pos_lo", "clamp_p_pk", "clamp_n_pk"}),
        (NET5_TRAN, {"ripple_pos", "ripple_neg"}),
        (NET6_TRAN, {"vout_pk", "osc_ratio"}),
        (NET6_AC, {"recov_gain", "hpf_m3db", "recov_gain_db", "u1_buf_gain"}),
        # Stage 7 pot-position sweep (GitHub issue #43): each pot-extreme variant
        # carries the .meas assertions that gate its specific failure mode and
        # that exist in NO other netlist.
        (NET6_DWELL_MIN, {"dwell_min_vout", "dwell_min_dry"}),
        (NET6_DWELL_MAX, {"dwell_max_u2_pk", "dwell_max_wiper_pk"}),
        (NET6_MIX_CCW, {"mix_ccw_vout_pk", "mix_ccw_wet_ratio"}),
        (NET6_MIX_CW, {"mix_cw_vout_pk", "mix_cw_dry_attn"}),
        (NET6_DWELL_MAX_MIX_CW, {"worst_case_pk", "worst_case_settle"}),
        # Stage 8 stress variants (idealized -> realistic hardware deviations).
        # 3a low mains: same ripple/rail checks on a 108V secondary, plus the
        # unreg-bus trough (MIN/MAX) so the dropout floor is gated on the
        # instantaneous trough, not just the average.
        (NET5_LOW_MAINS,
         {"ripple_pos", "ripple_neg", "unreg_pos_min", "unreg_neg_min"}),
        # 3b U2 Vos: settled DC at u2_out under a 500uV input offset.
        (NET6_VOS, {"u2_out_dc_vos"}),
        # 3c BD139 low-beta corner: same Q1 bias checks at BF=40.
        (NET6_LO_BETA, {"q1_ve", "q1_ic"}),
    ):
        base = os.path.basename(path)
        checks += 1
        names = _netlist_meas_names(path)
        if names is None:
            fail("variant netlist missing: %s (run sync.py)" % base)
            continue
        missing = expected - names
        if missing:
            fail("%s: missing .meas directive(s): %s"
                 % (base, ", ".join(sorted(missing))))


# ---------------------------------------------------------------------------
# 1i. Q1 Ic CROSS-CHECK (C2): the op netlist must carry BOTH q1_ic_calc (Ve/R5)
#     AND a real comparison target q1_ic (FIND I(R5)) plus the q1_ic_err PARAM
#     that flags their disagreement. Without q1_ic the cross-check compares
#     against nothing.
# ---------------------------------------------------------------------------
def check_q1_ic_crosscheck():
    global checks
    names = _netlist_meas_names(NET)
    checks += 1
    if names is None:
        fail("q1_ic cross-check: %s missing" % os.path.basename(NET))
        return
    for needed in ("q1_ic", "q1_ic_calc", "q1_ic_err"):
        checks += 1
        if needed not in names:
            fail("%s: missing .meas %s (Ic cross-check has no comparison target)"
                 % (os.path.basename(NET), needed))


# ---------------------------------------------------------------------------
# 1i-bis. OP-NETLIST BIAS GUARDS (M3 + new): the op netlist must carry the
#     active-region + node-bias measurements whose pass windows live in
#     circuit_params. Without the .meas present the window in test-assertions.md
#     gates a number that is never computed (a silent test).
#       q1_vc / q1_vce / q1_vcb : Q1 forward-active (not saturated)
#       u2_inpos_bias           : U2 + input held at ~0V (no rail/DC leak)
# ---------------------------------------------------------------------------
def check_op_bias_guards():
    global checks
    names = _netlist_meas_names(NET)
    checks += 1
    if names is None:
        fail("op bias guards: %s missing" % os.path.basename(NET))
        return
    for needed in ("q1_vc", "q1_vce", "q1_vcb", "u2_inpos_bias"):
        checks += 1
        if needed not in names:
            fail("%s: missing .meas %s (bias-guard window is silent without it)"
                 % (os.path.basename(NET), needed))


# ---------------------------------------------------------------------------
# 1k. PSU UNREG-BUS HEADROOM (new): the regulator needs its input >= Vout+~2V to
#     stay in regulation. The PSU netlists measure unreg_pos/unreg_neg but nothing
#     gated them. Confirm both PSU netlists still carry those .meas so the
#     UNREG_HEADROOM_MIN window in test-assertions.md is not a silent number.
# ---------------------------------------------------------------------------
def check_psu_unreg_meas():
    global checks
    # op variant of stage 5 (stage_05_psu.net) carries unreg_pos / unreg_neg.
    NET5_OP = os.path.join(STAGES, "stage_05_psu.net")
    names = _netlist_meas_names(NET5_OP)
    checks += 1
    if names is None:
        fail("psu unreg: %s missing" % os.path.basename(NET5_OP))
        return
    for needed in ("unreg_pos", "unreg_neg"):
        checks += 1
        if needed not in names:
            fail("%s: missing .meas %s (unreg-bus headroom window is silent "
                 "without it)" % (os.path.basename(NET5_OP), needed))


# ---------------------------------------------------------------------------
# 1j. recov_gain_db TARGET (W4): if recov_gain_db is asserted in any committed
#     ac netlist, its documented sim target (test-assertions.md / circuit-params)
#     must equal CHAIN_GAIN_DB_SIM. recov_gain_db measures the recovery-stage gain
#     end-to-end across U2 (20*log10(V(u2_out)/V(u2_in_pos))) in dB; it is NOT the
#     full vin->v_out chain gain (the original chain_gain_db measured vin->v_out,
#     which is ~15-21 dB and would have failed the 44.6-48.6 dB window). Guards a
#     numeric pass target existing at all.
# ---------------------------------------------------------------------------
def check_chain_gain_target():
    global checks
    names = _netlist_meas_names(NET6_AC)
    if names is None or "recov_gain_db" not in names:
        return  # nothing asserts recov_gain_db -> nothing to cross-check
    checks += 1
    with open(ASSERT_MD) as f:
        text = f.read()
    needle = "%g dB" % P.CHAIN_GAIN_DB_SIM
    if needle not in text:
        fail("test-assertions.md: recov_gain_db target '%s' "
             "(CHAIN_GAIN_DB_SIM) not found" % needle)


# ---------------------------------------------------------------------------
# 2. circuit-params.md: spot-check key derived values appear with the right
#    numbers, AND check EVERY component R/C row's value against circuit_params
#    (parse the value from the table row and compare numerically). This closes
#    the silent-pass hole where a wrong component row (e.g. R6 = 9.9k) would
#    slip through because only ~12 derived values were spot-checked.
# ---------------------------------------------------------------------------

# SPICE/doc magnitude suffixes -> multiplier. CASE MATTERS: 'M'/'Meg' = mega,
# 'm' = milli. SPICE itself is case-insensitive (it has no milli/mega clash
# because it uses 'Meg'), but the doc writes 'MΩ' for mega, so we must keep the
# capital-M vs lowercase-m distinction. Ordered longest-first so 'Meg' wins.
# Each entry is (suffix, multiplier); matched case-sensitively against the tail.
_SPICE_SUFFIXES = [
    ("Meg", 1e6), ("meg", 1e6),
    ("M", 1e6),                 # doc 'MΩ' -> mega (SPICE would read M as milli,
                                #   but no resistor/cap constant uses a bare 'M')
    ("G", 1e9), ("g", 1e9),
    ("T", 1e12), ("t", 1e12),
    ("k", 1e3), ("K", 1e3),
    ("m", 1e-3),               # milli (lowercase only)
    ("u", 1e-6), ("µ", 1e-6), ("U", 1e-6),
    ("n", 1e-9), ("N", 1e-9),
    ("p", 1e-12), ("P", 1e-12),
    ("f", 1e-15), ("F", 1e-15),
]


def _spice_to_float(s):
    """Convert a SPICE/doc magnitude string to a float.
    Handles bare numbers and unit suffixes from BOTH circuit_params strings
    ('1Meg','100n','68','0.5') and the md's doc units ('1MΩ','100nF','100k',
    '47pF','68'). Strips Ω/F/H unit letters and any '/ 63V' voltage rating
    tail before parsing. Case-sensitive on the magnitude suffix so MΩ (mega)
    and m (milli) never collide. Returns None if it cannot be parsed."""
    if s is None:
        return None
    t = s.strip()
    # Drop a voltage-rating tail like "1µF / 63V" -> "1µF".
    if "/" in t:
        t = t.split("/")[0].strip()
    # Drop trailing dimensional unit letters (Ω/F/H) that are NOT magnitude
    # suffixes, so the magnitude suffix (if any) becomes the new tail.
    for unit in ("Ω", "F", "H"):
        if t.endswith(unit):
            t = t[: -len(unit)].strip()
            break
    if not t:
        return None
    # Try a magnitude suffix (case-sensitive, longest-first).
    for suf, mult in _SPICE_SUFFIXES:
        if t.endswith(suf):
            num = t[: -len(suf)]
            try:
                return float(num) * mult
            except ValueError:
                continue  # 'suf' was actually part of the number/letter; try next
    try:
        return float(t)
    except ValueError:
        return None


def check_params_md():
    global checks
    with open(PARAMS_MD) as f:
        text = f.read()

    def expect(label, needle):
        global checks
        checks += 1
        if needle not in text:
            fail("circuit-params.md: %s - expected to find '%s'" % (label, needle))

    # --- Spot-check key derived values (unchanged) ---
    # Q1 Ve (sim) and pass window
    expect("Q1 Ve sim", "%g V" % P.Q1_VE_SIM)
    expect("Q1 Ve window", "%s – %s V" % (_g1(P.Q1_VE_WINDOW[0]), _g(P.Q1_VE_WINDOW[1])))
    # Recovery gain (sim + window)
    expect("recov_gain sim", "%g×" % P.RECOV_GAIN_SIM)
    expect("recov_gain window", "%g – %g×" % (P.RECOV_GAIN_WINDOW[0], P.RECOV_GAIN_WINDOW[1]))
    # HPF corner sim + design + window
    expect("hpf sim", "%g Hz" % P.HPF_CORNER_SIM)
    expect("hpf design", "%g Hz" % P.HPF_CORNER_DESIGN)
    expect("hpf window", "%g – %g Hz" % (P.HPF_CORNER_WINDOW[0], P.HPF_CORNER_WINDOW[1]))
    # Rails (regulated targets, written with one decimal)
    expect("rail_pos", "≈+%s V" % _g1(P.RAIL_POS))
    expect("rail_neg", "≈%s V" % _g1(P.RAIL_NEG))
    # Rail pass windows
    expect("rail_pos window", "%g – %g V" % (P.RAIL_POS_WINDOW[0], P.RAIL_POS_WINDOW[1]))

    # --- Per-row component check: EVERY R/C row value must match its constant ---
    # Parse "| <ref> | <value> | ..." rows out of the md tables and compare the
    # numeric value to circuit_params. The ref label in the md is sometimes
    # decorated (e.g. "C1 (= `C_drive`)"), so we map md-ref -> constant.
    md_to_const = {
        # resistors R1-R7 + fuses (md ref : circuit_params value string)
        "R1": P.R1, "R2": P.R2, "R3": P.R3, "R4": P.R4, "R5": P.R5,
        "R6": P.R6, "R7": P.R7, "RF2": P.RF2, "RF3": P.RF3,
        # key capacitors
        "C_in": P.C_IN, "C1 (= `C_drive`)": P.C_DRIVE, "C2": P.C2, "C3": P.C3,
        "C4": P.C4, "C11": P.C11, "C12": P.C12, "C13": P.C13, "C14": P.C14,
    }

    # Index md table rows by their (stripped) first column.
    rows = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        rows.setdefault(cells[0], cells[1])  # ref -> value cell

    for ref, const_str in md_to_const.items():
        checks += 1
        if ref not in rows:
            fail("circuit-params.md: component row for '%s' not found" % ref)
            continue
        md_val = _spice_to_float(rows[ref])
        want = _spice_to_float(const_str)
        if md_val is None or want is None:
            fail("circuit-params.md: %s - could not parse value (md=%r, const=%r)"
                 % (ref, rows[ref], const_str))
        elif abs(md_val - want) > abs(want) * 1e-9 + 1e-18:
            fail("circuit-params.md: %s value %r (=%g) != circuit_params %r (=%g)"
                 % (ref, rows[ref], md_val, const_str, want))


# ---------------------------------------------------------------------------
# 3. test-assertions.md: the pass-window numbers quoted there must match the
#    tolerance tuples in circuit_params.py.
# ---------------------------------------------------------------------------
def check_assertions_md():
    global checks
    with open(ASSERT_MD) as f:
        text = f.read()

    def expect(label, needle):
        global checks
        checks += 1
        if needle not in text:
            fail("test-assertions.md: %s - expected to find '%s'" % (label, needle))

    # off_u1/2/3: |val| <= 10 mV
    expect("offset window", "%g mV" % (P.OFFSET_WINDOW[1] * 1e3))
    # q1_ve: 1.0 - 1.4 V
    expect("q1_ve window", "%s – %s V" % (_g1(P.Q1_VE_WINDOW[0]), _g(P.Q1_VE_WINDOW[1])))
    # q1_ic: 10 - 26 mA
    expect("q1_ic window", "%g – %g mA" % (P.Q1_IC_WINDOW[0] * 1e3, P.Q1_IC_WINDOW[1] * 1e3))
    # q1_ic_err: < 10% (M3 - the cross-check bound that was a silent measurement)
    expect("q1_ic_err max", "< %g%%" % (P.Q1_IC_ERR_MAX * 100))
    # q1_vb: 1.65 – 2.05 V (loaded base voltage from R3b/R4 divider)
    expect("q1_vb window",
           "%g – %g V" % (P.Q1_VB_WINDOW[0], P.Q1_VB_WINDOW[1]))
    # Q1 forward-active (not saturated): Vce > min, Vcb >= 0, Vc window
    expect("q1_vce min", "> %g V" % P.Q1_VCE_MIN)
    expect("q1_vcb min", "≥ %g V" % P.Q1_VCB_MIN)
    expect("q1_vc window", "%g – %g V" % (P.Q1_VC_WINDOW[0], P.Q1_VC_WINDOW[1]))
    # u2_in_pos DC bias: |val| <= 10 mV
    expect("u2_inpos_bias window", "%g mV" % (P.U2_INPOS_BIAS_WINDOW[1] * 1e3))
    # U1 buffer unity gain: 0.9 - 1.05
    expect("u1_buf_gain window",
           "%g – %g" % (P.U1_BUF_GAIN_WINDOW[0], P.U1_BUF_GAIN_WINDOW[1]))
    # Unregulated-bus headroom: |bus| > 17 V
    expect("unreg headroom min", "> %g V" % P.UNREG_HEADROOM_MIN)
    # Unregulated-bus ripple trough (low mains): |bus trough| > 17 V
    expect("unreg trough min", "> %g V (trough)" % P.UNREG_TROUGH_MIN)
    # recov_gain: 205 - 225
    expect("recov_gain window", "%g – %g" % (P.RECOV_GAIN_WINDOW[0], P.RECOV_GAIN_WINDOW[1]))
    # hpf: 250 - 320 Hz
    expect("hpf window", "%g – %g Hz" % (P.HPF_CORNER_WINDOW[0], P.HPF_CORNER_WINDOW[1]))
    # vout_pk: < 14 V
    expect("vout_pk max", "< %g V" % P.VOUT_PK_MAX)
    # osc_ratio: < 1.05
    expect("osc_ratio max", "< %g" % P.OSC_RATIO_MAX)
    # rails: 14.85 - 15.15 V
    expect("rail_pos window", "%g – %g V" % (P.RAIL_POS_WINDOW[0], P.RAIL_POS_WINDOW[1]))
    # ripple: < 10 mVpp
    expect("ripple max", "< %g mVpp" % (P.RIPPLE_MAX_PP * 1e3))

    # ----- Stage 7 pot-position sweep windows (H1/H3): every window defined in
    # circuit_params.py MUST be enforced in test-assertions.md or it is a silent
    # test. These expect() calls fail if a Stage-7 row drops its numeric bound.
    # dwell_min_dry: 0.05 – 0.15 V
    expect("dwell_min_dry window",
           "%g – %g V" % (P.DWELL_MIN_DRY_WINDOW[0], P.DWELL_MIN_DRY_WINDOW[1]))
    # dwell_min_vout: 0.02 – 0.12 V (v_out dry-only at Dwell-CCW/Mix-noon)
    expect("dwell_min_vout window",
           "%g – %g V" % (P.DWELL_MIN_VOUT_WINDOW[0], P.DWELL_MIN_VOUT_WINDOW[1]))
    # dwell_max_wiper_pk: 0.03 – 0.15 V
    expect("dwell_max_wiper_pk window",
           "%g – %g V" % (P.DWELL_MAX_WIPER_PK_WINDOW[0], P.DWELL_MAX_WIPER_PK_WINDOW[1]))
    # dwell_max_u2_pk: < 13.5 V
    expect("dwell_max_u2_pk max", "< %g V" % P.DWELL_MAX_U2_PK_MAX)
    # worst_case_pk: ≤ 6.0 V (v_out at Dwell-max/Mix-CW; analytical ceiling 0.4×13.5=5.4V)
    expect("worst_case_pk max", "≤ %g V" % P.WORST_CASE_PK_MAX)
    # mix_ccw_vout_pk: 0.05 – 0.15 V
    expect("mix_ccw_vout window",
           "%g – %g V" % (P.MIX_CCW_VOUT_WINDOW[0], P.MIX_CCW_VOUT_WINDOW[1]))
    # mix_ccw_wet_ratio: 0.20 – 0.65 (V(mix_wet)/V(hpf_out) across the real RV3 divider)
    expect("mix_ccw_wet_ratio window",
           "%g – %g" % (P.MIX_CCW_WET_ARRIVAL_WINDOW[0], P.MIX_CCW_WET_ARRIVAL_WINDOW[1]))
    # mix_cw_vout_pk: > 0.20 V (baseline sim 1.16V; floor catches badly-attenuated wet path)
    expect("mix_cw_vout_pk min", "> %g V" % P.MIX_CW_VOUT_PK_MIN)
    # mix_cw_dry_attn: < 0.5
    expect("mix_cw_dry_attn max", "< %g" % P.MIX_CW_DRY_ATTN_MAX)
    # worst_case_settle: < 0.5
    expect("worst_case_settle max", "< %g V" % P.WORST_CASE_SETTLE_MAX)

    # ----- Stage 3 tank-interface AC bounds (the "drip"): tank_pk_f resonance
    # band + tank_drive_db level. These were documented but previously unenforced.
    # tank_pk_f: 1 – 5 kHz
    expect("tank_pk_f window",
           "%g – %g kHz" % (P.TANK_PKF_MIN / 1e3, P.TANK_PKF_MAX / 1e3))
    # tank_drive_db: > −60 dB
    expect("tank_drive_db min", "> %s dB" % _g(P.TANK_DRIVE_DB_MIN))

    # ----- Stage 4 input-protection idle + overload bounds: every measured
    # quantity must carry an enforced numeric bound (no silent .meas).
    # clamp_p_i: < 1 uA at idle (forward current = wrong orientation)
    expect("clamp_p_i max",
           "< %g µA" % (P.CLAMP_IDLE_MAX * 1e6))
    # clamp_n_i: > -1 uA (reverse-biased at idle)
    expect("clamp_n_i min",
           "> %s µA (reverse-biased)" % _g(P.CLAMP_N_IDLE_MIN * 1e6))
    # tvs_a_i / tvs_b_i: -1 uA - +1 uA at idle
    expect("tvs_a_i window",
           "%s µA – +%g µA (idle, not conducting)"
           % (_g(P.TVS_IDLE_WINDOW[0] * 1e6), P.TVS_IDLE_WINDOW[1] * 1e6))
    # vin_idle: -10 mV - +10 mV (0V DC)
    expect("vin_idle window",
           "%s mV – +%g mV (0 V DC)"
           % (_g(P.VIN_IDLE_WINDOW[0] * 1e3), P.VIN_IDLE_WINDOW[1] * 1e3))
    # Overload: u1pos_hi <= +16V, u1pos_lo >= -16V
    expect("u1pos_hi max", "≤ +%g V" % P.U1POS_CLAMP_WINDOW[1])
    expect("u1pos_lo min", "≥ %s V" % _g(P.U1POS_CLAMP_WINDOW[0]))
    # Overload: clamp diodes MUST conduct (clamp_p_pk > 0, clamp_n_pk < 0)
    expect("clamp_p_pk min", "> %g (clamp conducts)" % P.CLAMP_OVERLOAD_P_MIN)
    expect("clamp_n_pk max", "< %g (clamp conducts)" % P.CLAMP_OVERLOAD_N_MAX)

    # ----- Stage 2 dynamic driver bounds (tran variant): D3 idle + driver no-clip.
    expect("d3_pk max", "< %g mA" % (P.D3_IDLE_PEAK_MAX * 1e3))
    expect("drv_pk max", "< %g mA" % (P.DRV_PEAK_MAX * 1e3))
    expect("drv_rms max", "< %g mA" % (P.DRV_RMS_MAX * 1e3))

    # ----- Stage 8 stress-variant windows: every new pass criterion must be
    # documented in test-assertions.md or it is a silent test.
    # 3a low mains: the 0.90 scale factor (108V on 120V nominal). Same rail/ripple
    # windows apply; document the drive factor so the variant is traceable.
    expect("psu low-mains factor", "%g×" % P.PSU_LOW_MAINS_VFACTOR)
    # 3b U2 Vos output DC window: |val| <= 150 mV (214x * 500uV ~107mV, blocked by C4)
    expect("u2_out_dc_vos window",
           "%g mV" % (P.U2_VOS_OUT_WINDOW[1] * 1e3))
    # 3c BD139 low-beta corner: BF forced to the datasheet hFE minimum (40).
    expect("bd139 low-beta BF", "BF=%g" % P.BD139_LO_BETA_BF)


# ---------------------------------------------------------------------------
# 1l. Q1 BASE BIAS constants (FIX 5): Q1_VB_WINDOW must exist and the unloaded
#     divider voltage Q1_VB_UNLOADED (15 * R4/(R3b+R4)) must fall inside it. This
#     ties the builder-guide's bench bias numbers to a single source of truth.
# ---------------------------------------------------------------------------
def check_q1_vb():
    global checks
    checks += 1
    if not hasattr(P, "Q1_VB_WINDOW"):
        fail("Q1 base bias: circuit_params has no Q1_VB_WINDOW")
        return
    if not hasattr(P, "Q1_VB_UNLOADED"):
        fail("Q1 base bias: circuit_params has no Q1_VB_UNLOADED")
        return
    lo, hi = P.Q1_VB_WINDOW
    checks += 1
    if not (lo < hi):
        fail("Q1 base bias: Q1_VB_WINDOW not lo<hi: %r" % (P.Q1_VB_WINDOW,))
    checks += 1
    if not (lo <= P.Q1_VB_UNLOADED <= hi):
        fail("Q1 base bias: Q1_VB_UNLOADED %g outside Q1_VB_WINDOW %s"
             % (P.Q1_VB_UNLOADED, P.Q1_VB_WINDOW))


# ---------------------------------------------------------------------------
# 1m. FENCE vs NETLIST DRIFT: every .meas line shown in a ```spice fence in
#     test-assertions.md must have matching analysis type, form, AND probe
#     expression in at least one committed netlist. Catches M1-class bugs
#     (wrong analysis type / form) and M2-class bugs (wrong probe node or
#     wrong time window).
# ---------------------------------------------------------------------------
def _norm_probe(s):
    """Strip inline ; comments then collapse whitespace — for fence vs netlist comparison."""
    return " ".join(s.split(";")[0].split())


def check_fence_meas_forms():
    global checks
    with open(ASSERT_MD) as f:
        doc = f.read()

    # Collect (analysis, form, probe_expr) tuples from all committed .net files.
    # probe_expr is everything after the form keyword, normalized.
    netlist_meas = {}   # name -> set of (analysis, form, probe_expr)
    for fname in sorted(os.listdir(STAGES)):
        if not fname.endswith(".net"):
            continue
        try:
            lines = open(os.path.join(STAGES, fname)).read().splitlines()
        except IOError:
            continue
        for line in lines:
            m = re.match(r"\.meas\s+(\w+)\s+(\w+)\s+(\w+)\s*(.*)", line, re.I)
            if m:
                analysis = m.group(1).upper()
                name = m.group(2).lower()
                form = m.group(3).upper()
                probe = _norm_probe(m.group(4))
                netlist_meas.setdefault(name, set()).add((analysis, form, probe))

    # Extract .meas lines from ```spice fences.
    in_fence = False
    for line in doc.splitlines():
        stripped = line.strip()
        if stripped.startswith("```spice"):
            in_fence = True
            continue
        if in_fence and stripped == "```":
            in_fence = False
            continue
        if not in_fence:
            continue
        m = re.match(r"\.meas\s+(\w+)\s+(\w+)\s+(\w+)\s*(.*)", stripped, re.I)
        if not m:
            continue
        fence_analysis = m.group(1).upper()
        name = m.group(2).lower()
        fence_form = m.group(3).upper()
        fence_probe = _norm_probe(m.group(4))

        if name not in netlist_meas:
            continue  # intermediate PARAM / legacy example not in any netlist

        # Check 1: analysis type + form keyword match at least one netlist entry.
        checks += 1
        af_matches = [(a, f, p) for (a, f, p) in netlist_meas[name]
                      if a == fence_analysis and f == fence_form]
        if not af_matches:
            actual = sorted(netlist_meas[name])
            fail(
                "test-assertions.md fence shows '.meas %s %s %s ...', "
                "but no committed netlist has (%s, %s) for '%s' — "
                "actual: %s"
                % (fence_analysis, name, fence_form,
                   fence_analysis, fence_form, name, actual)
            )
            continue

        # Check 2: probe expression matches (catches wrong node, wrong window).
        checks += 1
        if (fence_analysis, fence_form, fence_probe) not in netlist_meas[name]:
            actual_probes = [p for (a, f, p) in netlist_meas[name]
                             if a == fence_analysis and f == fence_form]
            fail(
                "test-assertions.md fence '%s' probe mismatch — "
                "fence: %r  netlist: %r"
                % (name, fence_probe, actual_probes)
            )


def main():
    check_netlist()
    check_stage_netlists()
    check_mix_topology()
    check_hpf_wet_only()
    check_opamp_feedback()
    check_decoupling_caps()
    check_d3_flyback()
    check_rv1_topology()
    check_q1_vb()
    check_derived_transfer()
    check_variant_netlists()
    check_q1_ic_crosscheck()
    check_op_bias_guards()
    check_psu_unreg_meas()
    check_chain_gain_target()
    check_params_md()
    check_assertions_md()
    check_fence_meas_forms()

    if errors:
        print("VALIDATION FAILED (%d of %d checks):" % (len(errors), checks))
        for e in errors:
            print("  - " + e)
        print("\nFix circuit_params.py and run sync.py to regenerate.")
        return 1
    print("VALIDATION OK: %d checks passed; netlist + circuit-params.md + "
          "test-assertions.md all agree with circuit_params.py." % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
