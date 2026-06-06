#!/usr/bin/env python3
"""
sync.py - One command to re-cascade the Ghost Spring parameters.

Runs the whole pipeline from circuit_params.py outward, in order:
  1. Regenerate every SPICE netlist  (gen_stage*.py, default analysis variant).
  2. Regenerate circuit-params.md     (gen_circuit_params_md.py).
  3. Run validate.py                  (the consistency gate).
Then prints a summary: what was regenerated, and any drift validate found.

Idempotent: running it twice produces identical files and the same result.
Path-independent: resolves everything from __file__, so it works from any cwd.

Usage: python docs/reverb-tank/sync.py
"""

import hashlib
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STAGES = os.path.join(HERE, "stages")
PY = sys.executable

# Each generator maps to a LIST of (analysis, output file) variants it must emit.
# Most stages ship only their default op netlist. Stages 5 and 6 additionally
# carry analysis-specific variants whose .meas assertions live in NO other file:
#   - stage 5: op (rail DC) + tran (ripple_pos/ripple_neg < 10mVpp)
#   - stage 6: op (bias) + ac (recov_gain / hpf_m3db / recov_gain_db) + tran
#              (vout_pk / osc_ratio)
# The FIRST variant in each list is the canonical default (matches the generator's
# own __main__ default and the bare filename); the rest get a _<analysis> suffix.
GENERATORS = [
    (os.path.join(STAGES, "gen_stage2_asc.py"),
     [("op", os.path.join(STAGES, "stage_02_driver.net"))]),
    (os.path.join(STAGES, "gen_stage3_asc.py"),
     [("ac", os.path.join(STAGES, "stage_03_transformer.net"))]),
    (os.path.join(STAGES, "gen_stage4_asc.py"),
     [("op", os.path.join(STAGES, "stage_04_input_protect.net"))]),
    (os.path.join(STAGES, "gen_stage5_psu.py"),
     [("op", os.path.join(STAGES, "stage_05_psu.net")),
      ("tran", os.path.join(STAGES, "stage_05_psu_tran.net"))]),
    (os.path.join(STAGES, "gen_stage6_full.py"),
     [("op", os.path.join(STAGES, "stage_06_full.net")),
      ("ac", os.path.join(STAGES, "stage_06_full_ac.net")),
      ("tran", os.path.join(STAGES, "stage_06_full_tran.net")),
      # Stage 7 pot-position sweep (GitHub issue #43): pot-extreme variants whose
      # .meas assertions live in NO other file. Each drives one pot to a travel
      # rail (the others held at noon) and gates the failure mode it exposes.
      ("dwell_min", os.path.join(STAGES, "stage_06_full_dwell_min.net")),
      ("dwell_max", os.path.join(STAGES, "stage_06_full_dwell_max.net")),
      ("mix_ccw", os.path.join(STAGES, "stage_06_full_mix_ccw.net")),
      ("mix_cw", os.path.join(STAGES, "stage_06_full_mix_cw.net")),
      ("dwell_max_mix_cw",
       os.path.join(STAGES, "stage_06_full_dwell_max_mix_cw.net"))]),
]
PARAMS_MD_GEN = os.path.join(STAGES, "gen_circuit_params_md.py")
PARAMS_MD = os.path.join(HERE, "circuit-params.md")
VALIDATE = os.path.join(HERE, "validate.py")


def _hash(path):
    if not os.path.exists(path):
        return None
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _run(script, analysis, out):
    """Generate ONE analysis variant of a generator into a SPECIFIC output path.

    The generators' __main__ hardcode a single default output filename, so we
    cannot select the analysis variant or the output file via argv. Instead we
    import the generator module (its `sys.path.insert(0, dirname(__file__))` makes
    `import circuit_params` resolve to the stages dir) and call build(analysis) +
    dump() with our own paths. Run in a subprocess so module/bytecode caches never
    leak between variants. Raises on failure so a broken generator branch is loud.
    """
    asc = os.path.splitext(out)[0] + ".asc"
    snippet = (
        "import importlib.util, os, sys\n"
        "stages = %r\n"
        "script = %r\n"
        "analysis = %r\n"
        "out = %r\n"
        "asc = %r\n"
        "sys.path.insert(0, stages)\n"
        "spec = importlib.util.spec_from_file_location('gen_mod', script)\n"
        "gen = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(gen)\n"
        "b = gen.build(analysis)\n"
        "b.dump(asc, out)\n"
    ) % (STAGES, script, analysis, out, asc)
    subprocess.run([PY, "-c", snippet], cwd=STAGES, check=True,
                   stdout=subprocess.DEVNULL)


def main():
    # Clear any stale bytecode so a fresh circuit_params.py is always re-read.
    shutil.rmtree(os.path.join(STAGES, "__pycache__"), ignore_errors=True)

    regenerated = []   # files whose content actually changed
    unchanged = []     # files re-emitted byte-identical (idempotent path)

    print("Ghost Spring sync - regenerating from circuit_params.py")
    print("-" * 60)
    # Every netlist variant (op/ac/tran) of every generator.
    for script, variants in GENERATORS:
        for analysis, out in variants:
            before = _hash(out)
            _run(script, analysis, out)
            after = _hash(out)
            rel = os.path.relpath(out, HERE)
            if before != after:
                regenerated.append(rel)
                print("  regenerated  %s" % rel)
            else:
                unchanged.append(rel)
                print("  unchanged    %s" % rel)

    # circuit-params.md (its generator writes its own fixed output path via argv).
    before = _hash(PARAMS_MD)
    subprocess.run([PY, PARAMS_MD_GEN], cwd=STAGES, check=True,
                   stdout=subprocess.DEVNULL)
    after = _hash(PARAMS_MD)
    rel = os.path.relpath(PARAMS_MD, HERE)
    if before != after:
        regenerated.append(rel)
        print("  regenerated  %s" % rel)
    else:
        unchanged.append(rel)
        print("  unchanged    %s" % rel)

    print("-" * 60)
    print("Validating consistency...")
    print("-" * 60)
    sys.stdout.flush()
    result = subprocess.run([PY, VALIDATE], capture_output=True, text=True)
    sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)

    print("-" * 60)
    print("Summary: %d file(s) changed, %d unchanged."
          % (len(regenerated), len(unchanged)))
    if regenerated:
        print("  Changed: " + ", ".join(regenerated))
    if result.returncode == 0:
        print("Drift: none - all artifacts agree with circuit_params.py.")
    else:
        print("Drift: validate.py reported mismatches (see above). "
              "This should not happen right after a sync - investigate.")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
