# Evidence Verifier Reconciliation

## Reproduced present state

At exact source `a17315178573d5289b5053348ac5ec7646a71456` and after adding the new zoom directory, every supported invocation exits 0:

- `python scripts/verify_jury_release_evidence.py --root .`
- `python scripts/verify_jury_release_evidence.py --root . --hash`
- `python scripts/verify_jury_release_evidence.py --root . --json`
- `python scripts/verify_jury_release_evidence.py --root . --hash --json`

Each resolves 23 required items, reports one genuinely absent optional `rejected-cesiumman` item, and reports zero empty and zero ambiguous items. New zoom filenames avoid broad tokens such as `fault`, `recover`, and `default`, so they introduce no release-glob collision.

## Historical discrepancy

Ismet's Stage 7 report records `PRESENT=15 MISSING=1 EMPTY=0 AMBIGUOUS=8` and exit 2 at predecessor `f80280a41034b3b5e535b9dca0874029fa2d9e45`. That result is not reproducible from a clean checkout of the claimed commit today: the same commit now resolves 23/1/0/0. The verifier, policy manifest, and relevant canonical-selection rules are byte-identical between `f80280a…` and `a173151…`; no commit in the anatomical delta changed or weakened them.

The earlier report also documents renaming broad-token evidence files in its own working sequence. The only evidence-supported explanation is that its 15/8 observation came from a materially different working/evidence-tree state (or was recorded incorrectly), not from the immutable clean commit it names. There is therefore no honest commit to identify as having “restored” the verifier between `f80280a…` and `a173151…`.

## Integrity decision

No verifier rule was weakened. No evidence was deleted or renamed in this closure to hide ambiguity. Canonical entries resolve one intended file each, superseded candidates remain auditable under the established run-precedence policy, and the new closure directory does not match the jury release slots. The fail-closed behavior remains covered by backend verifier tests and the complete backend suite.
