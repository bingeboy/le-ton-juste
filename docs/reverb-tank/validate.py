#!/usr/bin/env python3
"""
validate.py - Consistency gate for the Ghost Spring parameter cascade.

Checks (WITHOUT regenerating anything) that the three downstream artifacts agree
with circuit_params.py (the single source of truth):

  1. stages/stage_06_full.net  - every R/C/L/K value matches the constant.
  1b. per-stage netlists       - driver stages carry R5=68; stage_05_psu places
                                 RF2/RF3 on the DC rails (not the AC secondary).
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
    "Rwet": P.RWET, "R7": P.R7, "Rload": P.RLOAD,
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
    # recov_gain: 200 - 228
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


def main():
    check_netlist()
    check_stage_netlists()
    check_params_md()
    check_assertions_md()

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
