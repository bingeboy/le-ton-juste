#!/usr/bin/env python3
"""
validate.py - Consistency gate for the Ghost Spring parameter cascade.

Checks (WITHOUT regenerating anything) that the three downstream artifacts agree
with circuit_params.py (the single source of truth):

  1. stages/stage_06_full.net  - every R/C/L/K value matches the constant.
  2. circuit-params.md         - spot-check key values (Ve, gain, HPF, rails).
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


# ---------------------------------------------------------------------------
# 2. circuit-params.md: spot-check key derived values appear with the right
#    numbers. We look for the value text anywhere in the file (regex), which is
#    robust to table formatting without a full markdown parser.
# ---------------------------------------------------------------------------
def check_params_md():
    global checks
    with open(PARAMS_MD) as f:
        text = f.read()

    def expect(label, needle):
        global checks
        checks += 1
        if needle not in text:
            fail("circuit-params.md: %s - expected to find '%s'" % (label, needle))

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
    # Key resistor values present in the table
    expect("Rf value", "%sk" % P.RF[:-1] if P.RF.endswith("k") else P.RF)
    expect("R5 value", "| R5 | %s |" % P.R5)


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
