#!/usr/bin/env python3
"""
test_sync.py - End-to-end proof that the Ghost Spring parameter cascade works.

    circuit_params.py  ->  gen_stage*.py  ->  stage_0*.net
                       ->  gen_circuit_params_md.py -> circuit-params.md
                       ->  validate.py (gate)  /  sync.py (re-cascade)

These tests prove the cascade end-to-end: that circuit_params.py is the single
source of truth, that mutating it actually propagates into the generated
netlists, that validate.py catches drift, and that sync.py is idempotent.

They are pure Python-tooling tests: no LTspice, no Wine, no SPICE simulation is
required. Run from the repo root:

    pytest docs/reverb-tank/test_sync.py -v

Design notes
------------
* sync.py and validate.py have side effects (they write files / exit), so they
  are invoked via subprocess, never imported.
* The cascade test (Group 3) copies the whole stages/ dir into a tmp_path,
  mutates the COPY of circuit_params.py, runs the generator there via
  subprocess, and asserts against the COPY's netlist. The real tree is never
  touched and there is no module-cache contamination.
* validate.py drift tests (Group 4) corrupt a copy of stage_06_full.net in a
  tmp tree and point validate.py at it, again leaving the real file untouched.
"""

import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys

import pytest

# ---------------------------------------------------------------------------
# Paths (resolved from this file, so tests work from any cwd).
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
STAGES = os.path.join(HERE, "stages")
PARAMS_PY = os.path.join(STAGES, "circuit_params.py")
GEN_STAGE6 = os.path.join(STAGES, "gen_stage6_full.py")
NET6 = os.path.join(STAGES, "stage_06_full.net")
NET5 = os.path.join(STAGES, "stage_05_psu.net")
SYNC = os.path.join(HERE, "sync.py")
VALIDATE = os.path.join(HERE, "validate.py")
PY = sys.executable

# Generated artifacts that sync.py (re)writes, used by the idempotency test.
GENERATED_FILES = [
    os.path.join(STAGES, "stage_02_driver.net"),
    # Stage 2 dynamic driver tran variant (d3_pk / drv_pk / drv_rms).
    os.path.join(STAGES, "stage_02_driver_tran.net"),
    os.path.join(STAGES, "stage_03_transformer.net"),
    os.path.join(STAGES, "stage_04_input_protect.net"),
    # Stage 4 20Vpp clamp-window overload tran variant.
    os.path.join(STAGES, "stage_04_input_protect_overload.net"),
    os.path.join(STAGES, "stage_05_psu.net"),
    os.path.join(STAGES, "stage_05_psu_tran.net"),
    # Stage 8 stress variant (low mains).
    os.path.join(STAGES, "stage_05_psu_low_mains.net"),
    os.path.join(STAGES, "stage_06_full.net"),
    os.path.join(STAGES, "stage_06_full_ac.net"),
    os.path.join(STAGES, "stage_06_full_tran.net"),
    # Stage 7 pot-position sweep variants (GitHub issue #43).
    os.path.join(STAGES, "stage_06_full_dwell_min.net"),
    os.path.join(STAGES, "stage_06_full_dwell_max.net"),
    os.path.join(STAGES, "stage_06_full_mix_ccw.net"),
    os.path.join(STAGES, "stage_06_full_mix_cw.net"),
    os.path.join(STAGES, "stage_06_full_dwell_max_mix_cw.net"),
    # Stage 8 stress variants (U2 Vos injection, BD139 low-beta corner).
    os.path.join(STAGES, "stage_06_full_vos.net"),
    os.path.join(STAGES, "stage_06_full_lo_beta.net"),
    os.path.join(HERE, "circuit-params.md"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_circuit_params(path=PARAMS_PY, modname="cp_under_test"):
    """Import a circuit_params.py from an explicit path under a private module
    name, so the live one is never shadowed and the cache is never reused."""
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def run_stage6_generator(stages_dir, out_net):
    """Run gen_stage6_full.py's real build()+dump() against the circuit_params.py
    that lives in `stages_dir`, writing the netlist to `out_net`.

    The generator's __main__ hardcodes an absolute output path (the real tree),
    so we cannot just `subprocess.run([PY, "gen_stage6_full.py"])` and expect
    output in a copy. Instead we import the generator module FROM stages_dir
    (which makes its `sys.path.insert(0, dirname(__file__))` pick up that dir's
    circuit_params) and call build()/dump() with our own paths. Run in a
    subprocess so module/​bytecode caches never leak between tests.
    """
    snippet = (
        "import importlib.util, os, sys\n"
        "stages = %r\n"
        "out = %r\n"
        "sys.path.insert(0, stages)\n"
        "spec = importlib.util.spec_from_file_location("
        "'gen6', os.path.join(stages, 'gen_stage6_full.py'))\n"
        "gen = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(gen)\n"
        "b = gen.build('op')\n"
        "b.dump(out + '.asc', out)\n"
    ) % (str(stages_dir), str(out_net))
    subprocess.run([PY, "-c", snippet], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def run_generator(stages_dir, gen_filename, out_net, analysis="op"):
    """Generic version of run_stage6_generator: import any gen_stage*.py module
    FROM stages_dir (so its `import circuit_params` resolves to that dir's copy)
    and call build(analysis)/dump() with our own output paths. Subprocess so
    module/bytecode caches never leak between tests."""
    snippet = (
        "import importlib.util, os, sys\n"
        "stages = %r\n"
        "gen_file = %r\n"
        "out = %r\n"
        "analysis = %r\n"
        "sys.path.insert(0, stages)\n"
        "spec = importlib.util.spec_from_file_location("
        "'gen_mod', os.path.join(stages, gen_file))\n"
        "gen = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(gen)\n"
        "b = gen.build(analysis)\n"
        "b.dump(out + '.asc', out)\n"
    ) % (str(stages_dir), gen_filename, str(out_net), analysis)
    subprocess.run([PY, "-c", snippet], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def net_line(netlist_text, instance):
    """Return the netlist card whose first token == instance, or None.
    Skips comments (*) and directives (.)."""
    for raw in netlist_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("*") or line.startswith("."):
            continue
        if line.split()[0] == instance:
            return line
    return None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def P():
    """The live circuit_params module, freshly loaded from disk."""
    return load_circuit_params()


@pytest.fixture
def stages_copy(tmp_path):
    """An isolated copy of the entire stages/ directory in tmp_path.

    Generators do `sys.path.insert(0, os.path.dirname(__file__))` then
    `import circuit_params`, so a generator placed in this copy imports the
    COPY's circuit_params.py. Mutating that copy lets us prove propagation
    without touching the real tree.
    """
    dst = tmp_path / "stages"
    shutil.copytree(STAGES, dst, ignore=shutil.ignore_patterns("__pycache__"))
    return dst


# ===========================================================================
# Group 1: circuit_params is importable and complete
# ===========================================================================
def test_circuit_params_imports_cleanly():
    """import circuit_params succeeds with no errors."""
    P = load_circuit_params()
    assert P is not None
    assert hasattr(P, "R5")


@pytest.mark.parametrize(
    "name", ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "RF2", "RF3"]
)
def test_all_resistors_defined(P, name):
    """Required resistor constants are present, string-typed, and non-empty."""
    assert hasattr(P, name), "circuit_params is missing %s" % name
    val = getattr(P, name)
    assert isinstance(val, str), "%s should be a SPICE string, got %r" % (name, val)
    assert val.strip(), "%s is empty" % name


@pytest.mark.parametrize(
    "name", ["C_IN", "C_DRIVE", "C2", "C3", "C4", "C11", "C12", "C13", "C14"]
)
def test_all_caps_defined(P, name):
    """Key capacitor constants are present, string-typed, and non-empty.

    Note: BOM ref C1 == netlist C_DRIVE (see circuit_params header)."""
    assert hasattr(P, name), "circuit_params is missing %s" % name
    val = getattr(P, name)
    assert isinstance(val, str), "%s should be a SPICE string, got %r" % (name, val)
    assert val.strip(), "%s is empty" % name


def test_operating_point_targets_are_floats(P):
    """Operating-point targets / tolerances are numeric (so checks can compare)."""
    # Single-value targets.
    for name in ["Q1_VE_SIM", "Q1_IC_SIM", "RAIL_POS", "RAIL_NEG", "RIPPLE_MAX_PP"]:
        val = getattr(P, name)
        assert isinstance(val, (int, float)), "%s should be numeric, got %r" % (name, val)

    # Tolerance windows are numeric 2-tuples with lo < hi.
    for name in ["Q1_VE_WINDOW", "Q1_IC_WINDOW", "OFFSET_WINDOW",
                 "RAIL_POS_WINDOW", "RECOV_GAIN_WINDOW", "HPF_CORNER_WINDOW"]:
        win = getattr(P, name)
        assert isinstance(win, tuple) and len(win) == 2, "%s should be a 2-tuple" % name
        lo, hi = win
        assert isinstance(lo, (int, float)) and isinstance(hi, (int, float)), \
            "%s bounds should be numeric" % name
        assert lo < hi, "%s window is not lo<hi: %r" % (name, win)


def test_stage7_sweep_constants_are_numeric(P):
    """Stage 7 pot-sweep pass windows (H1/H3) are numeric so validate.py can
    enforce them. DWELL_MAX_Q1_VE_WINDOW was replaced by DWELL_MAX_WIPER_PK_WINDOW
    (H2: q1_e is Dwell-independent); the mix-sweep bounds got real numbers (H3)."""
    # The replaced constant must be gone.
    assert not hasattr(P, "DWELL_MAX_Q1_VE_WINDOW"), \
        "DWELL_MAX_Q1_VE_WINDOW should be replaced by DWELL_MAX_WIPER_PK_WINDOW"

    # 2-tuple windows: numeric, lo < hi.
    for name in ["DWELL_MIN_DRY_WINDOW", "DWELL_MAX_WIPER_PK_WINDOW",
                 "MIX_CCW_VOUT_WINDOW", "MIX_CCW_WET_BLEED_WINDOW"]:
        win = getattr(P, name)
        assert isinstance(win, tuple) and len(win) == 2, "%s should be a 2-tuple" % name
        lo, hi = win
        assert isinstance(lo, (int, float)) and isinstance(hi, (int, float)), \
            "%s bounds should be numeric" % name
        assert lo < hi, "%s window is not lo<hi: %r" % (name, win)

    # Single-bound scalars: numeric.
    for name in ["DWELL_MAX_U2_PK_MAX", "MIX_CW_VOUT_PK_MIN",
                 "MIX_CW_DRY_ATTN_MAX", "WORST_CASE_SETTLE_MAX"]:
        val = getattr(P, name)
        assert isinstance(val, (int, float)), "%s should be numeric, got %r" % (name, val)


# ===========================================================================
# Group 2: generators produce valid netlists
# ===========================================================================
def test_gen_stage6_produces_netlist(stages_copy):
    """Running gen_stage6_full.py writes a non-empty stage_06_full.net."""
    out = stages_copy / "stage_06_full.net"
    out.unlink(missing_ok=True)  # prove the generator (re)creates it
    run_stage6_generator(stages_copy, out)
    assert out.exists(), "generator did not produce stage_06_full.net"
    text = out.read_text()
    assert text.strip(), "generated netlist is empty"
    # A sanity floor: it should at least carry the analysis/end cards.
    assert ".end" in text
    assert text.startswith("*")  # header comment


def test_netlist_contains_r5(P):
    """The committed stage_06_full.net carries R5 with circuit_params.R5's value."""
    text = open(NET6).read()
    line = net_line(text, "R5")
    assert line is not None, "no R5 card in stage_06_full.net"
    # Card form: "R5 <n1> <n2> <value>"
    assert line.split()[3] == P.R5, \
        "R5 netlist value %r != circuit_params.R5 %r" % (line.split()[3], P.R5)


def test_netlist_polyfuse_on_dc_rails(P):
    """RF2/RF3 (F2/F3 polyfuses) sit on the regulated DC rails, NOT the AC
    secondary. This is the regression guard for the polyfuse-placement bug:
    a fuse on ac_pos/ac_neg would protect nothing useful and is wrong."""
    text = open(NET6).read()

    rf2 = net_line(text, "RF2")
    rf3 = net_line(text, "RF3")
    assert rf2 is not None and rf3 is not None, "RF2/RF3 missing from netlist"

    # Nodes are tokens 1 and 2; value is token 3.
    rf2_nodes = set(rf2.split()[1:3])
    rf3_nodes = set(rf3.split()[1:3])

    # Must touch the DC rail output side (reg_pos/reg_neg -> +15V/-15V bus).
    assert rf2_nodes == {"reg_pos", "+15V"}, \
        "RF2 should bridge reg_pos<->+15V (DC rail), got %s" % rf2_nodes
    assert rf3_nodes == {"reg_neg", "-15V"}, \
        "RF3 should bridge reg_neg<->-15V (DC rail), got %s" % rf3_nodes

    # And must NOT be on the AC secondary side.
    for ac_node in ("ac_pos", "ac_neg"):
        assert ac_node not in rf2_nodes, "RF2 wrongly on AC node %s" % ac_node
        assert ac_node not in rf3_nodes, "RF3 wrongly on AC node %s" % ac_node

    # Value matches the source of truth.
    assert rf2.split()[3] == P.RF2
    assert rf3.split()[3] == P.RF3


def test_stage5_netlist_polyfuse_on_dc_rails(P):
    """Same regression guard as Stage 6, but for the standalone PSU stage
    (stage_05_psu.net): RF2/RF3 must sit on the regulated DC rails
    (reg_pos->+15V, reg_neg->-15V), NOT on the AC secondary (ac_pos/ac_neg).
    Stage 5 originally placed them on the AC side, which is electrically wrong;
    this locks in the fix so Stage 5 and Stage 6 stay topologically identical."""
    text = open(NET5).read()

    rf2 = net_line(text, "RF2")
    rf3 = net_line(text, "RF3")
    assert rf2 is not None and rf3 is not None, "RF2/RF3 missing from stage_05_psu.net"

    rf2_nodes = set(rf2.split()[1:3])
    rf3_nodes = set(rf3.split()[1:3])

    assert rf2_nodes == {"reg_pos", "+15V"}, \
        "RF2 should bridge reg_pos<->+15V (DC rail), got %s" % rf2_nodes
    assert rf3_nodes == {"reg_neg", "-15V"}, \
        "RF3 should bridge reg_neg<->-15V (DC rail), got %s" % rf3_nodes

    for ac_node in ("ac_pos", "ac_neg"):
        assert ac_node not in rf2_nodes, "RF2 wrongly on AC node %s" % ac_node
        assert ac_node not in rf3_nodes, "RF3 wrongly on AC node %s" % ac_node

    assert rf2.split()[3] == P.RF2
    assert rf3.split()[3] == P.RF3


# ===========================================================================
# Group 3: the cascade -- mutate circuit_params -> regenerate -> propagate
# ===========================================================================
def test_cascade_r5_change_propagates(stages_copy, P):
    """THE core cascade test. Change R5 in a COPY of circuit_params.py to a
    sentinel value, run the stage-6 generator against that copy, and assert the
    sentinel appears as R5's value in the regenerated netlist. Proves editing
    the single source of truth actually re-flows into the netlist."""
    sentinel = "999"
    assert P.R5 != sentinel, "sentinel collides with real R5 value; pick another"

    params_copy = stages_copy / "circuit_params.py"
    src = params_copy.read_text()

    # Replace ONLY the R5 assignment line, robustly (keeps inline comment).
    new_src, n = re.subn(
        r'(?m)^(R5\s*=\s*)"[^"]*"',
        r'\g<1>"%s"' % sentinel,
        src,
    )
    assert n == 1, "expected exactly one R5 assignment to rewrite, found %d" % n
    params_copy.write_text(new_src)

    # Confirm the mutated copy actually reports the sentinel.
    mutated = load_circuit_params(str(params_copy), modname="cp_mutated")
    assert mutated.R5 == sentinel

    # Regenerate the netlist from the mutated copy.
    out = stages_copy / "stage_06_full.net"
    out.unlink(missing_ok=True)
    run_stage6_generator(stages_copy, out)

    # The R5 card must now carry the sentinel value.
    line = net_line(out.read_text(), "R5")
    assert line is not None, "R5 missing after regeneration"
    assert line.split()[3] == sentinel, \
        "cascade broken: R5 card = %r, expected value %r" % (line, sentinel)

    # And the original (untouched) tree must be unaffected.
    assert net_line(open(NET6).read(), "R5").split()[3] == P.R5


@pytest.mark.parametrize(
    "const_name, sentinel, gen_file, out_name, instance, analysis",
    [
        # resistor through the stage-6 generator
        ("R5", "999", "gen_stage6_full.py", "stage_06_full.net", "R5", "op"),
        # capacitor through the stage-6 generator
        ("C_IN", "777n", "gen_stage6_full.py", "stage_06_full.net", "C_in", "op"),
        ("C2", "888u", "gen_stage6_full.py", "stage_06_full.net", "C2", "op"),
        # PSU fuse constant through the stage-5 (PSU) generator
        ("RF2", "0.123", "gen_stage5_psu.py", "stage_05_psu.net", "RF2", "op"),
    ],
)
def test_cascade_constant_change_propagates(
    stages_copy, P, const_name, sentinel, gen_file, out_name, instance, analysis
):
    """Generalised cascade test (W1): mutate a single constant in a COPY of
    circuit_params.py, run the RELEVANT generator against that copy, and assert
    the sentinel value appears on the right netlist card. Covers a resistor
    (R5), capacitors (C_IN, C2), and a PSU fuse constant (RF2) through both the
    stage-6 and stage-5 generators -- proving the source of truth re-flows
    across multiple constant classes and generators, not just R5."""
    assert getattr(P, const_name) != sentinel, \
        "sentinel collides with real %s value; pick another" % const_name

    params_copy = stages_copy / "circuit_params.py"
    src = params_copy.read_text()
    new_src, n = re.subn(
        r'(?m)^(%s\s*=\s*)"[^"]*"' % re.escape(const_name),
        r'\g<1>"%s"' % sentinel,
        src,
    )
    assert n == 1, \
        "expected exactly one %s assignment to rewrite, found %d" % (const_name, n)
    params_copy.write_text(new_src)

    mutated = load_circuit_params(str(params_copy), modname="cp_mut_" + const_name)
    assert getattr(mutated, const_name) == sentinel

    out = stages_copy / out_name
    out.unlink(missing_ok=True)
    run_generator(stages_copy, gen_file, out, analysis=analysis)

    line = net_line(out.read_text(), instance)
    assert line is not None, "%s missing after regeneration" % instance
    assert line.split()[3] == sentinel, \
        "cascade broken: %s card = %r, expected value %r" % (instance, line, sentinel)


def test_cascade_does_not_touch_real_tree(stages_copy, P):
    """Sibling guard: regenerating inside the copy leaves the real
    circuit_params.py and stage_06_full.net byte-identical."""
    before_params = sha256(PARAMS_PY)
    before_net = sha256(NET6)
    out = stages_copy / "stage_06_full.net"
    run_stage6_generator(stages_copy, out)
    assert sha256(PARAMS_PY) == before_params
    assert sha256(NET6) == before_net


# ===========================================================================
# Group 4: validate.py catches drift
# ===========================================================================
def test_validate_passes_clean():
    """validate.py exits 0 against the committed, in-sync artifacts."""
    result = subprocess.run([PY, VALIDATE], capture_output=True, text=True)
    assert result.returncode == 0, \
        "validate.py failed on a clean tree:\n%s\n%s" % (result.stdout, result.stderr)
    assert "VALIDATION OK" in result.stdout


def test_validate_catches_netlist_drift(tmp_path):
    """Corrupt R5 in a COPY of the netlist, point validate.py at that copy, and
    assert it fails. This is the regression guard for hand-edited / drifted
    netlists. The real netlist is never modified.

    validate.py resolves NET = STAGES/stage_06_full.net from its own __file__,
    so we run a copy of the whole reverb-tank tree in tmp_path and corrupt the
    copy's netlist.
    """
    tree = tmp_path / "reverb-tank"
    shutil.copytree(HERE, tree, ignore=shutil.ignore_patterns("__pycache__"))
    bad_net = tree / "stages" / "stage_06_full.net"

    text = bad_net.read_text()
    P = load_circuit_params()
    good = net_line(text, "R5")
    assert good is not None
    wrong_val = "12345"  # definitely not R5's real value
    assert P.R5 != wrong_val
    corrupted_line = " ".join(good.split()[:3] + [wrong_val])
    text = text.replace(good, corrupted_line)
    bad_net.write_text(text)

    result = subprocess.run([PY, str(tree / "validate.py")],
                            capture_output=True, text=True)
    assert result.returncode != 0, \
        "validate.py did NOT catch the R5 netlist drift:\n%s" % result.stdout
    assert "R5" in result.stdout, \
        "validate.py failed but did not name R5:\n%s" % result.stdout


# ===========================================================================
# Group 5: sync.py is idempotent
# ===========================================================================
def test_sync_idempotent():
    """Run sync.py twice; the generated files must be byte-identical between
    runs (and sync must succeed both times). Proves the cascade settles to a
    fixed point and re-running is safe.

    sync.py rewrites files in the real tree, so we snapshot every generated
    file, run sync twice, compare hashes, and restore the originals to leave
    the working tree exactly as we found it.
    """
    backups = {f: open(f, "rb").read() for f in GENERATED_FILES if os.path.exists(f)}
    try:
        first = subprocess.run([PY, SYNC], capture_output=True, text=True)
        assert first.returncode == 0, \
            "first sync.py run failed:\n%s\n%s" % (first.stdout, first.stderr)
        hashes_1 = {f: sha256(f) for f in GENERATED_FILES if os.path.exists(f)}

        second = subprocess.run([PY, SYNC], capture_output=True, text=True)
        assert second.returncode == 0, \
            "second sync.py run failed:\n%s\n%s" % (second.stdout, second.stderr)
        hashes_2 = {f: sha256(f) for f in GENERATED_FILES if os.path.exists(f)}

        assert hashes_1 == hashes_2, "sync.py is NOT idempotent: %s" % (
            [os.path.basename(f) for f in hashes_1 if hashes_1[f] != hashes_2.get(f)]
        )
        # Idempotent run #2 should report no changes.
        assert "0 file(s) changed" in second.stdout, \
            "second sync reported changes:\n%s" % second.stdout
    finally:
        for f, data in backups.items():
            with open(f, "wb") as fh:
                fh.write(data)


# ===========================================================================
# Group 6: structural / topology guards on the COMMITTED stage_06_full.net
#
# These are the P1 functional-failure guards. Unlike the value checks above,
# they assert the WIRING (which node connects to which) so a topology fix that
# is correct value-wise but mis-wired cannot ship undetected -- the class of
# bug behind the Mix-pot short (dry shorted to -140 dB with every value right).
# ===========================================================================

# (gen script basename -> list of (analysis, committed .net basename)) for EVERY
# variant sync emits. Mirrors sync.py's GENERATORS. Stages 5 and 6 carry multiple
# analysis variants whose .meas assertions exist in NO other file, so the
# meta-guard must regenerate and diff EACH variant -- otherwise a broken ac/tran
# generator branch ships green (W2). The FIRST entry per generator is the
# canonical default (bare filename); others get the _<analysis> suffix.
GEN_TO_NETS = {
    "gen_stage2_asc.py": [("op", "stage_02_driver.net"),
                          ("tran", "stage_02_driver_tran.net")],
    "gen_stage3_asc.py": [("ac", "stage_03_transformer.net")],
    "gen_stage4_asc.py": [("op", "stage_04_input_protect.net"),
                          ("overload",
                           "stage_04_input_protect_overload.net")],
    "gen_stage5_psu.py": [("op", "stage_05_psu.net"),
                          ("tran", "stage_05_psu_tran.net"),
                          # Stage 8 stress: 108V (10%-low) mains variant.
                          ("psu_low_mains", "stage_05_psu_low_mains.net")],
    "gen_stage6_full.py": [("op", "stage_06_full.net"),
                           ("ac", "stage_06_full_ac.net"),
                           ("tran", "stage_06_full_tran.net"),
                           # Stage 7 pot-position sweep (GitHub issue #43): each
                           # pot-extreme variant's .meas assertions exist in NO
                           # other file, so the meta-guard must regenerate + diff
                           # EACH one or a broken sweep branch ships green.
                           ("dwell_min", "stage_06_full_dwell_min.net"),
                           ("dwell_max", "stage_06_full_dwell_max.net"),
                           ("mix_ccw", "stage_06_full_mix_ccw.net"),
                           ("mix_cw", "stage_06_full_mix_cw.net"),
                           ("dwell_max_mix_cw",
                            "stage_06_full_dwell_max_mix_cw.net"),
                           # Stage 8 stress: U2 Vos injection + BD139 low-beta.
                           ("stage6_vos", "stage_06_full_vos.net"),
                           ("lo_beta", "stage_06_full_lo_beta.net")],
}

# Flattened (gen_file, analysis, net_name) cases for the meta-guard parametrize:
# (stage2, op), (stage3, ac), (stage4, op), (stage5, op), (stage5, tran),
# (stage6, op), (stage6, ac), (stage6, tran).
GEN_NET_CASES = [
    (gen, analysis, net_name)
    for gen, variants in GEN_TO_NETS.items()
    for analysis, net_name in variants
]


def _strip_path_header(text):
    """Drop the leading '* <abspath>.asc' comment line that every generator
    writes first (it embeds the output path and so differs between the real
    tree and a tmp_path regeneration). Everything else must match exactly."""
    lines = text.splitlines()
    if lines and lines[0].startswith("* ") and lines[0].rstrip().endswith(".asc"):
        lines = lines[1:]
    return lines


def cards_of(netlist_text):
    """{instance: token-list} for every element card (skip *comments/.directives)."""
    out = {}
    for raw in netlist_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("*") or line.startswith("."):
            continue
        parts = line.split()
        out[parts[0]] = parts
    return out


# ---------------------------------------------------------------------------
# P1.1 -- committed netlist == generator output (the META-GUARD). Regenerate
# every stage into tmp_path and compare line-for-line (minus the path header)
# against the committed file. Catches a topology fix applied to a generator but
# never re-cascaded into the committed netlist (or a hand-edited netlist).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("gen_file, analysis, net_name", GEN_NET_CASES)
def test_committed_netlist_matches_generator(stages_copy, gen_file, analysis, net_name):
    out = stages_copy / ("regen_" + net_name)
    run_generator(stages_copy, gen_file, out, analysis=analysis)
    regenerated = _strip_path_header(out.read_text())
    committed = _strip_path_header(open(os.path.join(STAGES, net_name)).read())
    assert regenerated == committed, (
        "%s diverges from %s output -- a fix to the generator was not "
        "re-cascaded into the committed netlist (run sync.py). First diff:\n%s"
        % (net_name, gen_file,
           next(("  committed: %r\n  generated: %r" % (c, g)
                 for c, g in zip(committed + [None] * len(regenerated),
                                 regenerated + [None] * len(committed))
                 if c != g), "(length differs only)"))
    )


def test_meta_guard_detects_divergence(stages_copy):
    """Red-before-green for P1.1: if the committed netlist is hand-edited away
    from generator output, the meta-guard must notice. We regenerate, then
    corrupt a COPY of the committed file and confirm the line-for-line compare
    fails on it."""
    out = stages_copy / "regen_check.net"
    run_generator(stages_copy, "gen_stage6_full.py", out, analysis="op")
    regenerated = _strip_path_header(out.read_text())

    committed = open(NET6).read()
    # Hand-edit: bump R5's value, as if someone patched the netlist directly.
    tampered = committed.replace("R5 q1_e 0 68", "R5 q1_e 0 75", 1)
    assert tampered != committed, "anchor for tamper not found"
    tampered_lines = _strip_path_header(tampered)
    assert regenerated != tampered_lines, \
        "meta-guard would MISS a hand-edited netlist diverging from generator"


# ---------------------------------------------------------------------------
# P1.2 -- Mix topology structural check (the original-bug guard).
# ---------------------------------------------------------------------------
def test_mix_topology_structure():
    """stage_06_full.net wires RV2 as a 3-terminal passive blend, not a volume
    knob. Asserts the exact node wiring that the Rwet=0.001 short violated."""
    text = open(NET6).read()
    cards = cards_of(text)

    rdry = cards.get("Rdry")
    rv2a = cards.get("RV2a")
    rv2b = cards.get("RV2b")
    assert rdry and rv2a and rv2b, "Rdry/RV2a/RV2b missing from netlist"

    # Rdry: dry source u1_buf -> CCW end mix_dry.
    assert set(rdry[1:3]) == {"u1_buf", "mix_dry"}, \
        "Rdry must connect u1_buf<->mix_dry, got %s" % set(rdry[1:3])
    # RV2a: CCW half mix_dry -> wiper mix_node.
    assert set(rv2a[1:3]) == {"mix_dry", "mix_node"}, \
        "RV2a must connect mix_dry<->mix_node, got %s" % set(rv2a[1:3])
    # RV2b: CW half mix_node -> wet end mix_wet.
    assert set(rv2b[1:3]) == {"mix_node", "mix_wet"}, \
        "RV2b must connect mix_node<->mix_wet, got %s" % set(rv2b[1:3])

    # The wet signal reaches mix_wet (here via Rwet_wire from the Tone wiper).
    wet_on_mix_wet = any(
        "mix_wet" in set(p[1:3]) and ("rv3_wiper" in set(p[1:3]))
        for p in cards.values()
    )
    assert wet_on_mix_wet, \
        "wet signal (rv3_wiper / Tone output) must reach mix_wet"

    # mix_dry and mix_wet are DIFFERENT nodes.
    assert "mix_dry" != "mix_wet"
    dry_nodes = set(rdry[1:3])
    assert "mix_wet" not in dry_nodes, \
        "dry end (Rdry) must not land on mix_wet -- that collapses the blend"

    # No near-short (<=0.01) resistor ties both the dry node and the wet signal
    # to the same node (the Rwet=0.001 bug).
    def rval(tok):
        try:
            return float(tok)
        except ValueError:
            return None
    for name, p in cards.items():
        if name[0] not in ("R", "r") or len(p) < 4:
            continue
        v = rval(p[3])
        if v is not None and v <= 0.01:
            nodes = set(p[1:3])
            assert "mix_dry" not in nodes, \
                ("%s is a near-short (%s) on the dry node mix_dry -- the "
                 "Rwet short bug" % (name, p[3]))


def test_validate_catches_broken_mix_topology(tmp_path):
    """Red-before-green for P1.2: inject the volume-knob/short wiring into a COPY
    of the netlist and confirm validate.py's check_mix_topology() fails on it.
    The real netlist is never touched."""
    tree = tmp_path / "reverb-tank"
    shutil.copytree(HERE, tree, ignore=shutil.ignore_patterns("__pycache__"))
    bad_net = tree / "stages" / "stage_06_full.net"

    text = bad_net.read_text()
    # Re-wire RV2b so both pot halves share the SAME two nodes (volume-knob /
    # collapsed blend): RV2a and RV2b both span mix_dry<->mix_node.
    assert "RV2b mix_node mix_wet 50k" in text
    text = text.replace("RV2b mix_node mix_wet 50k",
                        "RV2b mix_dry mix_node 50k", 1)
    bad_net.write_text(text)

    result = subprocess.run([PY, str(tree / "validate.py")],
                            capture_output=True, text=True)
    assert result.returncode != 0, \
        "validate.py did NOT catch the broken mix topology:\n%s" % result.stdout
    assert "mix topology" in result.stdout, \
        "validate.py failed but not on mix topology:\n%s" % result.stdout


# ---------------------------------------------------------------------------
# P1.3 -- HPF on the wet path only; dry path DC-coupled.
# ---------------------------------------------------------------------------
def test_hpf_wet_path_only():
    """C4/R6 form the wet HPF (between U2 out and the Tone/Mix stage); the dry
    path u1_buf->mix_dry carries NO series capacitor (DC-coupled)."""
    text = open(NET6).read()
    cards = cards_of(text)

    c4, r6, rdry = cards.get("C4"), cards.get("R6"), cards.get("Rdry")
    assert c4 and r6 and rdry, "C4/R6/Rdry missing"

    # C4 + R6 are the wet HPF, both on wet-chain nodes (not dry).
    assert set(c4[1:3]) == {"u2_out", "hpf_out"}, \
        "C4 must couple u2_out<->hpf_out (wet), got %s" % set(c4[1:3])
    assert set(r6[1:3]) == {"hpf_out", "0"}, \
        "R6 must shunt hpf_out<->0 (wet HPF), got %s" % set(r6[1:3])

    # Dry path: Rdry connects u1_buf directly to mix_dry, purely resistive.
    assert set(rdry[1:3]) == {"u1_buf", "mix_dry"}, \
        "Rdry must connect u1_buf<->mix_dry directly, got %s" % set(rdry[1:3])
    assert rdry[0][0] in ("R", "r"), "dry coupler Rdry must be a resistor"

    # No capacitor sits on the dry source node u1_buf (a series coupling cap),
    # and no cap touches mix_dry except the legitimate C_bright pot bridge.
    for name, p in cards.items():
        if name[0] not in ("C", "c") or len(p) < 3:
            continue
        nodes = set(p[1:3])
        assert "u1_buf" not in nodes, \
            "cap %s on dry source node u1_buf -- dry path must be DC-coupled" % name
        if "mix_dry" in nodes:
            assert nodes == {"mix_dry", "mix_wet"}, \
                ("cap %s on mix_dry with other end %s -- only the C_bright "
                 "pot-bridge mix_dry<->mix_wet is allowed"
                 % (name, nodes - {"mix_dry"}))


def test_validate_catches_cap_in_dry_path(tmp_path):
    """Red-before-green for P1.3: insert a series cap into the dry path in a COPY
    of the netlist and confirm validate.py flags it."""
    tree = tmp_path / "reverb-tank"
    shutil.copytree(HERE, tree, ignore=shutil.ignore_patterns("__pycache__"))
    bad_net = tree / "stages" / "stage_06_full.net"

    text = bad_net.read_text()
    assert "Rdry u1_buf mix_dry 10k" in text
    # Drop a coupling cap onto the dry source node u1_buf.
    text = text.replace("Rdry u1_buf mix_dry 10k",
                        "Rdry u1_buf mix_dry 10k\nCdrybad u1_buf mix_dry 1u", 1)
    bad_net.write_text(text)

    result = subprocess.run([PY, str(tree / "validate.py")],
                            capture_output=True, text=True)
    assert result.returncode != 0, \
        "validate.py did NOT catch a cap in the dry path:\n%s" % result.stdout
    assert "hpf wet-only" in result.stdout, \
        "validate.py failed but not on the dry-path cap:\n%s" % result.stdout


# ---------------------------------------------------------------------------
# P1.5 -- decoupling caps present on the correct rails.
# ---------------------------------------------------------------------------
def test_decoupling_caps_on_rails():
    """C5/C7 bridge +15V->0 and C6/C8 bridge -15V->0; all four present."""
    cards = cards_of(open(NET6).read())
    for name, expect in (
        ("C5", {"+15V", "0"}), ("C7", {"+15V", "0"}),
        ("C6", {"-15V", "0"}), ("C8", {"-15V", "0"}),
    ):
        card = cards.get(name)
        assert card is not None, "%s (supply decoupling) missing from netlist" % name
        assert set(card[1:3]) == expect, \
            "%s must bridge %s, got %s" % (name, expect, set(card[1:3]))


def test_validate_catches_missing_decoupling(tmp_path):
    """Red-before-green for P1.5: delete a decoupling cap in a COPY of the
    netlist and confirm validate.py flags the missing supply bypass."""
    tree = tmp_path / "reverb-tank"
    shutil.copytree(HERE, tree, ignore=shutil.ignore_patterns("__pycache__"))
    bad_net = tree / "stages" / "stage_06_full.net"

    text = bad_net.read_text()
    assert "C7 +15V 0 100n\n" in text
    text = text.replace("C7 +15V 0 100n\n", "", 1)
    bad_net.write_text(text)

    result = subprocess.run([PY, str(tree / "validate.py")],
                            capture_output=True, text=True)
    assert result.returncode != 0, \
        "validate.py did NOT catch the missing decoupling cap:\n%s" % result.stdout
    assert "decoupling" in result.stdout or "C7" in result.stdout, \
        "validate.py failed but not on the missing decoupling cap:\n%s" % result.stdout


# ---------------------------------------------------------------------------
# P1.6 -- D3 flyback clamp present and correctly oriented.
# ---------------------------------------------------------------------------
def test_d3_flyback_present_and_oriented():
    """D3 clamps Q1's collector to the +15V rail: anode=q1_c, cathode=+15V.
    In SPICE the D card is 'D3 <anode> <cathode> <model>', so the line must be
    'D3 q1_c +15V ...'. A reversed/missing D3 would let the transformer flyback
    spike destroy Q1."""
    text = open(NET6).read()
    line = net_line(text, "D3")
    assert line is not None, "D3 flyback clamp missing from netlist"
    parts = line.split()
    assert parts[0] == "D3"
    assert parts[1] == "q1_c", \
        "D3 anode must be q1_c (collector), got %s" % parts[1]
    assert parts[2] == "+15V", \
        "D3 cathode must be +15V rail, got %s" % parts[2]


def test_d3_reversed_orientation_is_detectable():
    """Red-before-green for P1.6: confirm the orientation assertion is real --
    a swapped D3 (anode/cathode reversed) would NOT match the expected card.
    We synthesise the reversed line and check the same assertion logic rejects
    it (no file write needed; this exercises the guard's discriminating power)."""
    reversed_line = "D3 +15V q1_c 1N4148"
    parts = reversed_line.split()
    # The committed-netlist assertion requires anode=q1_c, cathode=+15V; the
    # reversed card has them swapped, so the guard must reject it.
    assert not (parts[1] == "q1_c" and parts[2] == "+15V"), \
        "a reversed D3 must NOT satisfy the orientation guard"


def test_validate_catches_reversed_d3(tmp_path):
    """Red-before-green for the validate.py D3 orientation guard: reverse D3 in a
    COPY of the netlist and confirm validate.py's check_d3_flyback() fails. A
    reversed D3 shorts Q1's collector to the rail and gives no flyback protection,
    so it MUST be caught statically -- not only by the test-suite presence check."""
    tree = tmp_path / "reverb-tank"
    shutil.copytree(HERE, tree, ignore=shutil.ignore_patterns("__pycache__"))
    bad_net = tree / "stages" / "stage_06_full.net"

    text = bad_net.read_text()
    assert "D3 q1_c +15V 1N4148" in text
    text = text.replace("D3 q1_c +15V 1N4148", "D3 +15V q1_c 1N4148", 1)
    bad_net.write_text(text)

    result = subprocess.run([PY, str(tree / "validate.py")],
                            capture_output=True, text=True)
    assert result.returncode != 0, \
        "validate.py did NOT catch the reversed D3:\n%s" % result.stdout
    assert "D3 flyback" in result.stdout, \
        "validate.py failed but not on the D3 orientation:\n%s" % result.stdout


def test_validate_catches_wrong_decoupling_value(tmp_path):
    """Red-before-green for the decoupling-VALUE guard: change a decoupling cap to
    a wrong value (100p) in a COPY of the netlist and confirm validate.py flags it.
    A present-but-wrong-valued bypass passes a presence check but bypasses nothing
    at audio HF -- the value must be gated too."""
    tree = tmp_path / "reverb-tank"
    shutil.copytree(HERE, tree, ignore=shutil.ignore_patterns("__pycache__"))
    bad_net = tree / "stages" / "stage_06_full.net"

    text = bad_net.read_text()
    assert "C7 +15V 0 100n" in text
    text = text.replace("C7 +15V 0 100n", "C7 +15V 0 100p", 1)
    bad_net.write_text(text)

    result = subprocess.run([PY, str(tree / "validate.py")],
                            capture_output=True, text=True)
    assert result.returncode != 0, \
        "validate.py did NOT catch the wrong decoupling value:\n%s" % result.stdout
    assert "decoupling" in result.stdout, \
        "validate.py failed but not on the decoupling value:\n%s" % result.stdout


def test_op_netlist_has_bias_guard_meas():
    """The committed op netlist carries the Q1 active-region + U2-input-bias
    measurements whose pass windows live in circuit_params. Without the .meas the
    window in test-assertions.md gates a number that is never computed."""
    names = _meas_names(open(NET6).read())
    for needed in ("q1_vc", "q1_vce", "q1_vcb", "u2_inpos_bias"):
        assert needed in names, \
            "stage_06_full.net (op) missing .meas %s (got %s)" \
            % (needed, sorted(names))


# ---------------------------------------------------------------------------
# Stage 4 input-overload variant (FIX 1): the 20Vpp clamp-window run carries the
# overload .meas that exist in NO other netlist, and drives V1 at 20Vpp.
# ---------------------------------------------------------------------------
def test_stage4_overload_variant_exists_and_meas():
    """stage_04_input_protect_overload.net exists, drives V1 with the 20Vpp
    overload stimulus, runs a tran, and carries the clamp-window + clamp-
    conduction measurements."""
    path = os.path.join(STAGES, "stage_04_input_protect_overload.net")
    assert os.path.exists(path), \
        "stage_04_input_protect_overload.net missing -- run sync.py"
    text = open(path).read()
    assert ".tran" in text, "overload variant must carry a .tran analysis"
    assert net_line(text, "V1").endswith("SINE(0 20 1k) AC 1"), \
        "overload variant must drive V1 with the 40Vpp SINE(0 20 1k) stimulus"
    names = _meas_names(text)
    for needed in ("u1pos_hi", "u1pos_lo", "clamp_p_pk", "clamp_n_pk"):
        assert needed in names, \
            "overload netlist missing .meas %s (got %s)" % (needed, sorted(names))


# ---------------------------------------------------------------------------
# Stage 2 dynamic driver variant (FIX 6): the driver-current/flyback .meas exist
# only in this tran variant, driven at the normal 100mVpk 1kHz level.
# ---------------------------------------------------------------------------
def test_stage2_driver_tran_variant_exists_and_meas():
    """stage_02_driver_tran.net exists, drives V1 at 100mVpk 1kHz, runs a tran,
    and carries the D3-idle / driver-no-clip measurements."""
    path = os.path.join(STAGES, "stage_02_driver_tran.net")
    assert os.path.exists(path), \
        "stage_02_driver_tran.net missing -- run sync.py"
    text = open(path).read()
    assert ".tran" in text, "stage2 tran variant must carry a .tran analysis"
    assert net_line(text, "V1").endswith("SINE(0 100m 1k) AC 1"), \
        "stage2 tran variant must drive V1 with the 100mVpk 1kHz stimulus"
    names = _meas_names(text)
    for needed in ("d3_pk", "drv_pk", "drv_rms"):
        assert needed in names, \
            "stage2 tran netlist missing .meas %s (got %s)" \
            % (needed, sorted(names))


# ---------------------------------------------------------------------------
# RV1 (Dwell pot) topology (FIX 3): every maintained stage netlist wires the
# Dwell pot the same way as stage_06_full + builder-guide.md.
# ---------------------------------------------------------------------------
RV1_BEARING_NETS = [
    "stage_02_driver.net", "stage_02_driver_tran.net",
    "stage_03_transformer.net",
    "stage_04_input_protect.net", "stage_04_input_protect_overload.net",
    "stage_06_full.net",
]


@pytest.mark.parametrize("net_name", RV1_BEARING_NETS)
def test_rv1_topology_consistent(net_name):
    """The Dwell pot is wired RV1a rv1_wiper 0 (wiper-to-GND half) and
    RV1b u1_buf rv1_wiper (signal-to-wiper half) in every maintained stage,
    matching builder-guide.md. The reverse wiring inverts the Dwell sense."""
    text = open(os.path.join(STAGES, net_name)).read()
    rv1a = net_line(text, "RV1a")
    rv1b = net_line(text, "RV1b")
    assert rv1a is not None and rv1b is not None, \
        "%s missing RV1a/RV1b" % net_name
    assert rv1a.split()[1:3] == ["rv1_wiper", "0"], \
        "%s RV1a must be 'rv1_wiper 0', got %s" % (net_name, rv1a)
    assert rv1b.split()[1:3] == ["u1_buf", "rv1_wiper"], \
        "%s RV1b must be 'u1_buf rv1_wiper', got %s" % (net_name, rv1b)


def test_validate_catches_reversed_rv1(tmp_path):
    """Red-before-green for validate.py check_rv1_topology(): reverse the Dwell
    pot in a COPY of a stage netlist and confirm validate.py flags it. A reversed
    RV1 inverts the Dwell control sense and diverges from the builder guide."""
    tree = tmp_path / "reverb-tank"
    shutil.copytree(HERE, tree, ignore=shutil.ignore_patterns("__pycache__"))
    bad_net = tree / "stages" / "stage_04_input_protect.net"

    text = bad_net.read_text()
    assert "RV1a rv1_wiper 0 5k" in text and "RV1b u1_buf rv1_wiper 5k" in text
    # Swap to the reversed (wrong) wiring.
    text = text.replace("RV1a rv1_wiper 0 5k", "RV1a u1_buf rv1_wiper 5k", 1)
    text = text.replace("RV1b u1_buf rv1_wiper 5k", "RV1b rv1_wiper 0 5k", 1)
    bad_net.write_text(text)

    result = subprocess.run([PY, str(tree / "validate.py")],
                            capture_output=True, text=True)
    assert result.returncode != 0, \
        "validate.py did NOT catch the reversed RV1:\n%s" % result.stdout
    assert "rv1 topology" in result.stdout, \
        "validate.py failed but not on the RV1 topology:\n%s" % result.stdout


def test_q1_vb_constants_consistent(P):
    """Q1 base bias: the unloaded divider voltage (15 * R4/(R3b+R4)) sits inside
    the loaded bench window, and both constants exist (FIX 5)."""
    assert hasattr(P, "Q1_VB_WINDOW"), "circuit_params missing Q1_VB_WINDOW"
    assert hasattr(P, "Q1_VB_UNLOADED"), "circuit_params missing Q1_VB_UNLOADED"
    lo, hi = P.Q1_VB_WINDOW
    assert lo < hi, "Q1_VB_WINDOW not lo<hi: %r" % (P.Q1_VB_WINDOW,)
    assert lo <= P.Q1_VB_UNLOADED <= hi, \
        "Q1_VB_UNLOADED %g outside Q1_VB_WINDOW %r" \
        % (P.Q1_VB_UNLOADED, P.Q1_VB_WINDOW)


def test_ac_netlist_has_u1_buffer_gain_meas():
    """The committed ac netlist carries the U1 unity-buffer gain measurement."""
    names = _meas_names(open(os.path.join(STAGES, "stage_06_full_ac.net")).read())
    assert "u1_buf_gain" in names, \
        "stage_06_full_ac.net missing .meas u1_buf_gain (got %s)" % sorted(names)


def test_q1_active_region_constants_are_consistent(P):
    """The Q1 active-region windows are numeric and self-consistent: the sim
    collector voltage sits inside Q1_VC_WINDOW, and the Vce/Vcb floors keep Q1
    out of saturation (Vce floor > Vce(sat) ~0.2V, Vcb floor >= 0)."""
    lo, hi = P.Q1_VC_WINDOW
    assert lo < hi, "Q1_VC_WINDOW not lo<hi: %r" % (P.Q1_VC_WINDOW,)
    assert lo <= P.Q1_VC_SIM <= hi, \
        "Q1_VC_SIM %g outside Q1_VC_WINDOW %r" % (P.Q1_VC_SIM, P.Q1_VC_WINDOW)
    assert P.Q1_VCE_MIN > 0.2, "Vce floor must clear Vce(sat) ~0.2V"
    assert P.Q1_VCB_MIN >= 0.0, "Vcb floor must keep the CBJ reverse-biased"


# ===========================================================================
# Group 7: Stage 7 pot-position sweep (GitHub issue #43)
#
# All baseline sims hardcode every pot at 50%. These tests guard the pot-extreme
# variants: that each variant netlist exists, carries the .meas assertions that
# gate its failure mode, and that the pot halves are actually driven to the rail
# (not left at the 50/50 baseline). The meta-guard above (Group 6, GEN_NET_CASES)
# already regenerates+diffs each variant; these add variant-specific coverage.
# ===========================================================================

# (variant -> committed .net basename) for every pot-sweep variant sync emits.
POT_SWEEP_NETS = {
    "dwell_min": "stage_06_full_dwell_min.net",
    "dwell_max": "stage_06_full_dwell_max.net",
    "mix_ccw": "stage_06_full_mix_ccw.net",
    "mix_cw": "stage_06_full_mix_cw.net",
    "dwell_max_mix_cw": "stage_06_full_dwell_max_mix_cw.net",
}


def _meas_names(netlist_text):
    """Set of .meas result names (the token after the analysis type)."""
    names = set()
    for raw in netlist_text.splitlines():
        line = raw.strip()
        if not line.lower().startswith(".meas"):
            continue
        parts = line.split()
        if len(parts) >= 3:
            names.add(parts[2])
    return names


@pytest.mark.parametrize("variant, net_name", sorted(POT_SWEEP_NETS.items()))
def test_pot_sweep_variant_exists(variant, net_name):
    """Every pot-position sweep variant netlist exists and carries a tran
    analysis with the 100mVpk 1kHz stimulus (the pot extremes are exercised
    under signal, not as a bare DC op)."""
    path = os.path.join(STAGES, net_name)
    assert os.path.exists(path), \
        "%s missing -- run sync.py to generate the pot-sweep variants" % net_name
    text = open(path).read()
    assert ".tran" in text, "%s must carry a .tran analysis" % net_name
    # 100mVpk 1kHz stimulus, identical to the baseline tran variant.
    assert net_line(text, "V1").endswith("SINE(0 100m 1k) AC 1"), \
        "%s must drive V1 with the 100mVpk 1kHz stimulus" % net_name


def test_mix_ccw_has_wet_bleed_meas():
    """mix_ccw (Mix full-CCW = full dry) carries both its output-level meas and
    the wet-bleed proxy that gates dry-only output (no wet leaking through)."""
    text = open(os.path.join(STAGES, "stage_06_full_mix_ccw.net")).read()
    names = _meas_names(text)
    for needed in ("mix_ccw_vout_pk", "mix_ccw_wet_bleed"):
        assert needed in names, \
            "mix_ccw netlist missing .meas %s (got %s)" % (needed, sorted(names))


def test_dwell_max_has_wiper_pk_meas():
    """dwell_max (Dwell full-CW = max wet drive) carries the U2-clip guard and
    the wiper-level meas (dwell_max_wiper_pk). The wiper level is what the Dwell
    position actually controls; the old dwell_max_q1_ve probed a Dwell-independent
    DC bias (C_drive blocks DC) and so could never catch a Dwell failure."""
    text = open(os.path.join(STAGES, "stage_06_full_dwell_max.net")).read()
    names = _meas_names(text)
    for needed in ("dwell_max_vout_pk", "dwell_max_wiper_pk"):
        assert needed in names, \
            "dwell_max netlist missing .meas %s (got %s)" % (needed, sorted(names))
    # The replaced assertion must be gone (it tested a Dwell-independent quantity).
    assert "dwell_max_q1_ve" not in names, \
        "dwell_max still carries the Dwell-independent dwell_max_q1_ve meas"


def test_dwell_max_mix_cw_has_worst_case_meas():
    """dwell_max_mix_cw (worst-case clip path) carries the worst-case peak and
    the post-clip DC-settle meas (U2 must not rail and must settle back to ~0)."""
    text = open(os.path.join(STAGES, "stage_06_full_dwell_max_mix_cw.net")).read()
    names = _meas_names(text)
    for needed in ("worst_case_pk", "worst_case_settle"):
        assert needed in names, \
            "dwell_max_mix_cw netlist missing .meas %s (got %s)" \
            % (needed, sorted(names))


def test_pot_split_drives_halves_to_rail():
    """The pot-extreme variants must actually move a pot off the 50/50 baseline:
    one half goes to the SPICE-singularity floor (0.001) and the other to the
    pot total. Reads the committed netlists (proves the generator emitted the
    swept values), not just the generator in isolation."""
    P = load_circuit_params()
    floor = P.POT_MIN_OHMS  # "0.001"

    # dwell_min: Dwell CCW -> RV1a≈0, RV1b = full 10k.
    dmin = open(os.path.join(STAGES, "stage_06_full_dwell_min.net")).read()
    assert net_line(dmin, "RV1a").split()[3] == floor, \
        "dwell_min must floor RV1a to %s (wiper at CCW)" % floor
    assert net_line(dmin, "RV1b").split()[3] == P.RV1_TOTAL, \
        "dwell_min must put the full %s on RV1b" % P.RV1_TOTAL

    # dwell_max: Dwell CW -> RV1a = full 10k, RV1b≈0.
    dmax = open(os.path.join(STAGES, "stage_06_full_dwell_max.net")).read()
    assert net_line(dmax, "RV1a").split()[3] == P.RV1_TOTAL
    assert net_line(dmax, "RV1b").split()[3] == floor

    # mix_ccw: Mix CCW -> RV2a≈0 (wiper at the dry end), RV2b = full 100k.
    mccw = open(os.path.join(STAGES, "stage_06_full_mix_ccw.net")).read()
    assert net_line(mccw, "RV2a").split()[3] == floor
    assert net_line(mccw, "RV2b").split()[3] == P.RV2_TOTAL

    # mix_cw: Mix CW -> RV2a = full 100k, RV2b≈0 (wiper at the wet end).
    mcw = open(os.path.join(STAGES, "stage_06_full_mix_cw.net")).read()
    assert net_line(mcw, "RV2a").split()[3] == P.RV2_TOTAL
    assert net_line(mcw, "RV2b").split()[3] == floor

    # Non-swept pots stay at noon (the 50/50 baseline halves).
    assert net_line(dmin, "RV2a").split()[3] == P.RV2A, \
        "dwell_min must leave the Mix pot at noon"
    assert net_line(mccw, "RV1a").split()[3] == P.RV1A, \
        "mix_ccw must leave the Dwell pot at noon"


# ===========================================================================
# Group 8: Stage 8 realistic-hardware stress variants
#
# Idealized sims use Vos=0, nominal mains, nominal BD139 beta. These guard the
# stress variants: that each exists, carries the .meas assertion gating its
# failure mode, and that the modelled deviation is actually applied (not the
# nominal). The meta-guard above (GEN_NET_CASES) already regenerates+diffs each.
# ===========================================================================
def test_psu_low_mains_variant_scales_secondary(P):
    """The low-mains variant scales the T1 secondary by PSU_LOW_MAINS_VFACTOR
    (0.90, = 108V on 120V nominal) and re-runs the SAME ripple/rail checks."""
    path = os.path.join(STAGES, "stage_05_psu_low_mains.net")
    assert os.path.exists(path), "stage_05_psu_low_mains.net missing -- run sync.py"
    text = open(path).read()
    # Same ripple checks as the nominal tran variant.
    names = _meas_names(text)
    for needed in ("ripple_pos", "ripple_neg", "rail_pos", "rail_neg",
                   "unreg_pos", "unreg_neg"):
        assert needed in names, \
            "low-mains variant missing .meas %s (got %s)" % (needed, sorted(names))
    # The secondary peak must be the nominal 21.2Vpk scaled by 0.90 = 19.08.
    vsec = net_line(text, "Vsec_p")
    assert vsec is not None, "Vsec_p missing from low-mains netlist"
    nominal_pk = 21.2  # P.VSEC_SINE peak
    expected_pk = nominal_pk * P.PSU_LOW_MAINS_VFACTOR
    assert ("%g" % expected_pk) in vsec, \
        "low-mains Vsec_p must carry the %gV-scaled peak %g, got %r" \
        % (P.PSU_LOW_MAINS_VFACTOR, expected_pk, vsec)
    # And must NOT be the nominal 21.2 peak.
    assert "21.2" not in vsec, \
        "low-mains variant still drives the NOMINAL 21.2Vpk secondary"


def test_vos_variant_injects_offset_at_u2(P):
    """The Vos-stress variant inserts a 500uV DC source in SERIES at U2's
    non-inverting input and reads the settled DC at u2_out (gain unaffected)."""
    path = os.path.join(STAGES, "stage_06_full_vos.net")
    assert os.path.exists(path), "stage_06_full_vos.net missing -- run sync.py"
    text = open(path).read()
    names = _meas_names(text)
    assert "u2_out_dc_vos" in names, \
        "vos variant missing .meas u2_out_dc_vos (got %s)" % sorted(names)
    # Vos_u2 sits between the network node (u2_in_pos_src) and U2(+) (u2_in_pos).
    vos = net_line(text, "Vos_u2")
    assert vos is not None, "Vos_u2 source missing from vos netlist"
    assert set(vos.split()[1:3]) == {"u2_in_pos", "u2_in_pos_src"}, \
        "Vos_u2 must be in series at U2(+); got %s" % set(vos.split()[1:3])
    assert vos.split()[3] == P.U2_VOS_INJECT, \
        "Vos_u2 value %r != U2_VOS_INJECT %r" % (vos.split()[3], P.U2_VOS_INJECT)
    # The C3/Rbias network now feeds the SOURCE node, not U2(+) directly.
    assert set(net_line(text, "C3").split()[1:3]) == {"tank_out", "u2_in_pos_src"}, \
        "C3 must feed u2_in_pos_src (network node) in the vos variant"
    assert set(net_line(text, "Rbias").split()[1:3]) == {"u2_in_pos_src", "0"}, \
        "Rbias must shunt u2_in_pos_src->0 in the vos variant"


def test_lo_beta_variant_forces_bf_40(P):
    """The low-beta corner overrides the BD139 model with BF=40 (datasheet hFE
    min) and re-runs the SAME q1_ve / q1_ic bias windows."""
    path = os.path.join(STAGES, "stage_06_full_lo_beta.net")
    assert os.path.exists(path), "stage_06_full_lo_beta.net missing -- run sync.py"
    text = open(path).read()
    names = _meas_names(text)
    for needed in ("q1_ve", "q1_ic"):
        assert needed in names, \
            "lo_beta variant missing .meas %s (got %s)" % (needed, sorted(names))
    # Q1 references the low-beta model.
    assert net_line(text, "Q1").split()[4] == "BD139_lo", \
        "Q1 must reference BD139_lo in the lo_beta variant"
    # The model card forces BF to the low-beta corner.
    assert ".model BD139_lo" in text, "lo_beta variant missing .model BD139_lo"
    assert "Bf=%d" % P.BD139_LO_BETA_BF in P.BD139_LO_BETA_MODEL, \
        "BD139_LO_BETA_MODEL must force Bf=%d" % P.BD139_LO_BETA_BF


def test_stress_variant_constants_are_consistent(P):
    """Stage 8 stress constants are well-formed and self-consistent."""
    # Low-mains factor is a fraction below 1 (a sag, not a boost).
    assert 0.0 < P.PSU_LOW_MAINS_VFACTOR < 1.0, \
        "PSU_LOW_MAINS_VFACTOR must be a sag fraction in (0,1)"
    # U2 Vos output window straddles 0 (either offset polarity) and covers the
    # 214x * 500uV ~ 107mV worst case.
    lo, hi = P.U2_VOS_OUT_WINDOW
    assert lo < 0 < hi, "U2_VOS_OUT_WINDOW must straddle 0: %r" % (P.U2_VOS_OUT_WINDOW,)
    assert hi >= 0.107, "U2_VOS_OUT_WINDOW must cover the ~107mV worst case"
    # Low-beta BF is the datasheet hFE minimum and below the nominal Bf=100.
    assert P.BD139_LO_BETA_BF == 40
    assert "Bf=100" in P.BD139_MODEL and "Bf=40" in P.BD139_LO_BETA_MODEL
