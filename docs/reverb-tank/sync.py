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

# (script path, output file it writes with the DEFAULT analysis variant)
GENERATORS = [
    (os.path.join(STAGES, "gen_stage2_asc.py"), os.path.join(STAGES, "stage_02_driver.net")),
    (os.path.join(STAGES, "gen_stage3_asc.py"), os.path.join(STAGES, "stage_03_transformer.net")),
    (os.path.join(STAGES, "gen_stage4_asc.py"), os.path.join(STAGES, "stage_04_input_protect.net")),
    (os.path.join(STAGES, "gen_stage5_psu.py"), os.path.join(STAGES, "stage_05_psu.net")),
    (os.path.join(STAGES, "gen_stage6_full.py"), os.path.join(STAGES, "stage_06_full.net")),
]
PARAMS_MD_GEN = os.path.join(STAGES, "gen_circuit_params_md.py")
PARAMS_MD = os.path.join(HERE, "circuit-params.md")
VALIDATE = os.path.join(HERE, "validate.py")


def _hash(path):
    if not os.path.exists(path):
        return None
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _run(script):
    """Run a generator script; raise on failure so a broken generator is loud."""
    subprocess.run([PY, script], cwd=STAGES, check=True,
                   stdout=subprocess.DEVNULL)


def main():
    # Clear any stale bytecode so a fresh circuit_params.py is always re-read.
    shutil.rmtree(os.path.join(STAGES, "__pycache__"), ignore_errors=True)

    regenerated = []   # files whose content actually changed
    unchanged = []     # files re-emitted byte-identical (idempotent path)

    targets = [(g, out) for g, out in GENERATORS]
    targets.append((PARAMS_MD_GEN, PARAMS_MD))

    print("Ghost Spring sync - regenerating from circuit_params.py")
    print("-" * 60)
    for script, out in targets:
        before = _hash(out)
        _run(script)
        after = _hash(out)
        rel = os.path.relpath(out, HERE)
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
