# Independent Full-Repository Audit (Day 12–14)

Performed as a completely independent, adversarial reviewer of the entire
repository — including this session's own support work. Structured
findings live in `results/full_repository_audit_day14.json`; this
document narrates the audit process and conclusions.

## Scope actually covered (time-boxed, not padded)

Git forensics (chronology spot-check), scientific pipeline re-verification
(PPG/PTT/Sleep/interaction arithmetic and splits — already exhaustively
verified in the Day 10 and Day 11–14 sprints, spot-re-checked here rather
than fully redone), statistics artifacts, reproducibility (true
recomputation vs. self-consistency), checkpoint/archival state, CRLF
hashing, builder determinism, hand-maintained-artifact risk, engineering
arithmetic (independently recomputed from scratch), architecture-gate and
Pareto status consistency, claim-checker adversarial testing, dead
code/security/repo-hygiene scan, and a cross-layer consistency matrix.

Not independently re-derived from zero: the underlying PPG/PTT/Sleep
scientific results themselves (already reproduced exactly, multiple
times, across Day 9/10/11–14 sprints with checkpoint-based, byte-exact
verification — re-litigating that from scratch here would not find
anything the existing chain of reproduction artifacts hasn't already
proven or disproven). This audit instead spent its budget where prior
sprints had NOT already looked: the engineering-evidence rendering code,
the claim checker's actual robustness, and cross-layer consistency.

## True recomputation vs. artifact self-consistency

This is an important distinction the audit explicitly tracked:

- **TRUE RECOMPUTATION** (independently reloads a frozen checkpoint,
  regenerates predictions, and compares to a stored number): every
  `ml/verify_*_reproducibility.py` script, the Day-10
  `day10_scientific_reproduction.json` pipeline, and the Day 12–14
  clean-clone test. These are the strongest evidence in the project.
- **ARTIFACT SELF-CONSISTENCY** (checks that one JSON's derived fields are
  arithmetically consistent with its own or another JSON's *already-
  computed* fields, without touching a model): `ml/build_*_contract.py`,
  `ml/check_claim_consistency.py`, and this audit's own
  `independent_engineering_arithmetic_check_day12.json`. These are real
  and valuable but weaker — they cannot catch a shared upstream error
  present in both the source and the derived artifact.

Both categories exist in this project and are correctly *not* conflated
in any document reviewed. This audit's engineering-arithmetic check is
explicitly the second kind (self-consistency against source values), and
is labeled as such in its own artifact.

## Findings

See `results/full_repository_audit_day14.json` for the full structured
list. Summary: **3 HIGH, 3 MEDIUM, 1 LOW, 0 BLOCKER** (2 HIGH + 1 MEDIUM
already fixed this session — see below).

**Fixed this session (REPRO-1, REPRO-2):** running the full backend test
suite for the first time in this audit lineage (it was not run during the
ML-focused Day 10/11–14 sprints) surfaced 7 failures + 12 cascading
fixture errors. All traced to the same CRLF/autocrlf root cause already
found and fixed in the ML track — but here it was **more serious**: the
live `decision_inputs.artifact()` function (backing a research API
endpoint) was actually computing `ResearchAvailability.UNAVAILABLE` on
this Windows machine, not just failing a test assertion. A second,
distinct bug (missing `encoding="utf-8"` on several test `.read_text()`
calls, confined to test files — production code was already correct) was
found alongside it. Both were fixed with the identical, already-reviewed
normalize-before-hash / explicit-encoding pattern, verified via the same
git-blob-content-equality method as the original ML-track fix, and
committed separately with zero scientific or engineering value changed.
Full backend suite: 128/128 passing after the fix (was 7 failed + 12
errors before).

The third HIGH finding (REPRO-1) is described above, already fixed. The
remaining two (currently open, not fixed this session):
1. **SOFT-1**: `engineering_readiness.py` defaults two candidate fields
   (`incremental_sensing_contacts`, `raw_data_rate_increment_bps`) to `0`
   if missing, contradicting the module's own stated "never render
   unknown as zero" invariant — no current misfire (all present data is
   correctly populated), but untested and unenforced for a future missing
   value.
2. **CLAIM-1**: the claim-consistency checker
   (`ml/check_claim_consistency.py`) is a regex/lexical pattern list.
   Five hand-written semantic paraphrases of forbidden claims (e.g. "our
   complete wearable consumes 45 milliwatts" instead of "system power =
   45mW") were tested against its actual `FORBIDDEN` pattern list and
   **all five bypassed it with zero matches**. The checker currently
   reports "OK" because no live document happens to phrase an overclaim
   that way — this is not evidence it would catch one in the future.

Two MEDIUM and one LOW finding are lower-severity variants of the same
"unknown-folded-into-a-default" pattern (SOFT-2, SOFT-3) and a
presentation-clarity risk in the 48.068 kbps headline figure (HW-1: it
includes the deprioritized second-PPG evaluation branch's 59% share).

## Positive findings (also load-bearing for the verdict)

- Every independently recomputed power and data-rate arithmetic value
  (15 individual checks) matched the canonical figure **exactly**, with
  zero discrepancy — see `results/independent_engineering_arithmetic_check_day12.json`.
- Architecture-gate decisions and Pareto/power/mass NOT_READY states are
  consistent across the decision matrix, backend, and tests — no
  contradiction found anywhere checked.
- `ml/build_sensor_marginal_value_contract.py` reconfirmed
  byte-identical-deterministic across two independent reruns in this
  session.
- Git commit timestamps for the Sleep secondary-holdout cohort freeze
  (16:58:20) vs. its evaluation results (17:38:14) independently
  corroborate the predeclaration-before-evaluation claim from outside the
  documents' own self-reporting.
- No secrets, credentials, absolute personal paths, or raw/binary data
  found in tracked files.
- Digital Twin remains conceptual/untrained/unvalidated everywhere
  checked.
- The 10 Day-10 interaction checkpoints (found not externally durable in
  the immediately-prior sprint) are confirmed fixed and externally
  archived (60/60, 0 gaps) in this session's inventory.

## Cross-layer contradictions

`results/cross_layer_consistency_audit_day14.json` checked 11 major
facts (subject counts, checkpoint count, architecture-gate statuses,
Pareto/power status, the 48.068 kbps figure, interaction classification,
Digital Twin status) across code, result artifacts, the architecture
matrix, backend tests, and paper docs. **Zero active contradictions
found.** One fact (the 48.068 kbps fallback constant) is flagged fragile-
but-currently-consistent (see SOFT-2).

## Red-team answers (selected, evidence-based)

- **Could reproducibility PASS be artifact self-consistency?** For the
  checkpoint-based reproduction claims (PPG/PTT/Sleep primary/secondary,
  robustness), no — these are true recomputation from reloaded
  checkpoints, verified in this audit's TRUE RECOMPUTATION vs.
  SELF-CONSISTENCY breakdown above. For the sensor marginal-value
  contract and claim checker, yes — they are self-consistency checks,
  correctly not represented as anything stronger anywhere reviewed.
- **Are all checkpoints externally reproducible?** Yes as of this
  session — 60/60, verified via `results/final_checkpoint_inventory_day14.json`.
- **Could unknown burden become zero?** Yes, in two specific,
  now-documented code locations (SOFT-1, SOFT-3) — not currently active,
  but a real latent gap.
- **Is power arithmetic correct?** Yes, exactly, independently
  reconfirmed (see `results/independent_engineering_arithmetic_check_day12.json`).
- **Is 48 kbps correct?** Yes exactly, with one presentation-clarity
  caveat (HW-1) about what it includes.
- **Could a clean clone reproduce without the original developers?**
  Largely yes for code/environment/checkpoints (Day 12–13 test); raw
  dataset acquisition still requires either network access or a
  verified-hash file copy, disclosed as such, not hidden.
- **What would an IAC reviewer attack first?** Almost certainly the PTT
  n=4/s2-fragility (already disclosed as the project's weakest result)
  and the claim checker's actual robustness if they inspected it closely
  enough to construct a paraphrase — which this audit did.

## What is safe to freeze

All scientific results and their reproduction chain (PPG, PTT, Sleep
primary/secondary, robustness, interaction) — no discrepancy found in
this audit beyond what prior sprints already disclosed. The architecture
decision matrix and Pareto/power/mass NOT_READY states. The scientific
freeze candidate status (`SCIENTIFIC_FREEZE_CANDIDATE_READY_WITH_LIMITATIONS`)
remains valid — this audit found nothing that should downgrade it.

## What is NOT safe to freeze

The engineering-evidence rendering code paths identified in SOFT-1/2/3
should be fixed (or at minimum test-covered for the missing-value case)
before any "final" engineering evidence freeze. The claim checker's
actual semantic coverage should not be over-represented in jury/paper
materials as a strong guarantee.
