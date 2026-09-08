#!/usr/bin/env python
"""Clean-state reproducibility check for the QDE V2 leg-BioZ result: rerun
the trainer from scratch and confirm the stored numbers reproduce exactly
(deterministic ridge regression + seeded derangement, no stochastic
training)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULT_PATH = REPO_ROOT / "results" / "qde_v2_leg_bioz_stage2.json"


def main() -> None:
    before = json.loads(RESULT_PATH.read_text())
    subprocess.run([sys.executable, str(REPO_ROOT / "ml" / "train_qde_v2_leg_bioz.py")], check=True, cwd=REPO_ROOT, stdout=subprocess.DEVNULL)
    after = json.loads(RESULT_PATH.read_text())
    exact_match = before == after
    print("EXACT_MATCH:", exact_match)
    out = {"exact_match": exact_match, "coverage": "FULL_CLEAN_STATE_RERUN (deterministic ridge regression, no stochastic training component)"}
    (REPO_ROOT / "results" / "qde_v2_leg_bioz_stage2_reproducibility.json").write_text(json.dumps(out, indent=2))
    if not exact_match:
        raise SystemExit("MISMATCH DETECTED")


if __name__ == "__main__":
    main()
