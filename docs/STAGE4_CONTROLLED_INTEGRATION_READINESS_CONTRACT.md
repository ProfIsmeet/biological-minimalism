# Stage 4 Controlled-Integration Readiness Contract

Defines what must be true before controlled final-science integration begins.
This document does **not** execute that integration — it is the checklist
`PROJECT_COORDINATOR` (Emir) reviews before authorizing it. Nothing in this
Stage-4 sprint starts Stage 5.

## Preconditions (all must hold before controlled integration starts)

| # | Precondition | Current state |
|---|---|---|
| 1 | Parent science audit resolved | **NOT MET.** `INDEPENDENT_AUDITOR` (Codex) is independently auditing `stage2-4-science-owner-completion` at frozen SHA `ab798815882ac0723491dc489de2375f8bf5b774`. This sprint verified the SHA is frozen and unmodified but did not touch, read for integration purposes, or declare its audit passed. |
| 2 | Stage 3 science handoff complete | **NOT MET.** `SCIENCE_OWNER` (Ismet) is actively working beyond `next-science-expansion-sprint` at SHA `58e901174cc88fc79e1bc1d5c9bb4d7aa729a372` on GalaxyPPG broader grouped replication, LBNP, HMC retry, ds003838 full experiment. No completion signal was observed or waited for during this sprint. |
| 3 | Science branch/delta verified | **NOT MET** (cannot be, until #2). A delta review (exact files changed, exact new results/*.json artifacts, exact new checkpoints) must be performed against a specific frozen handoff SHA once one exists. |
| 4 | Exact authoritative artifacts identified | **PARTIALLY MET for Stage-4-owned engineering artifacts** (this sprint's `results/stage4_engineering_readiness.json` is unambiguous and frozen). **NOT MET for future science artifacts** — the typed ingestion contract (`app.schemas.experiment_manifest`, ported this sprint) is ready to receive them, but no manifest exists yet (`GET /research/future-science-manifest` reports `PENDING_SCIENCE_HANDOFF`). |
| 5 | Checkpoint states known | **NOT MET.** No new science checkpoints exist to enumerate; this sprint created none and imported none. |
| 6 | V1/V2 (and all mixed-protocol) guards intact | **MET.** `forbid_mixed_protocol_derivation()` (ported, tested) still fails closed on any dataset_version/protocol_version mismatch; re-verified by the full backend suite passing on this branch. |
| 7 | No quarantine result source | **MET.** `d97b4d5ea82ab039c6d79e095b0c2833ca82bb71` is confirmed absent from this branch's ancestry (`git merge-base --is-ancestor` check); see `docs/STAGE4_CLEAN_PORT_ADJUDICATION.md`. |
| 8 | No moving target | **NOT MET until #2 resolves.** Ismet's branch is actively running; this sprint deliberately did not read partial results from it. |
| 9 | Exact integration base selected | **NOT YET DECIDED — this is a `PROJECT_COORDINATOR` decision**, not something this sprint can or should select. Candidates once #1/#2 resolve: this Stage-4 branch (engineering-only, science-independent), or a fresh branch from whatever base Emir designates after reviewing both audits. |
| 10 | One future candidate SHA | **NOT APPLICABLE YET** — no science handoff SHA exists to name. |
| 11 | Independent final audit required | **STANDING REQUIREMENT, unchanged.** Any future integrated candidate requires its own independent Codex audit; this sprint's own hostile self-review does not substitute for it, per governing-prompt §3/§121. |

## What this Stage-4 sprint contributes toward readiness

- A clean, quarantine-free implementation branch (preconditions #6, #7).
- A typed, fail-closed future-science ingestion contract already wired end-to-end
  (backend validator → display projection → frontend card) so that when a real
  manifest arrives, ingesting it is "a mechanical validate-then-project operation
  rather than a hand-hardcoding exercise" (precondition #4, partially).
- A materially advanced, but explicitly non-final, engineering evidence package
  (power/mass/data-rate/BOM) that is entirely science-independent and therefore
  does not need to wait on preconditions #1-#3/#8/#10.

## What must happen next, in order

1. Emir reviews the Codex parent-science audit result for `ab798815...`.
2. Emir reviews Ismet's Stage-3 completion report once `next-science-expansion-sprint`
   (or its successor) reaches a frozen, handed-off state.
3. A delta review is performed comparing the frozen science-completion SHA
   against `next-science-expansion-sprint`'s current known state.
4. Emir selects the exact integration base (may or may not be this Stage-4 branch).
5. A new, explicitly-named integration branch is created from that exact base.
6. The future-science manifest (satisfying `app.schemas.experiment_manifest.ExperimentManifestFile`,
   schema_version `1.0.0`) is placed at `results/stage2_4_science_completion_manifest.json`
   and ingested through the existing fail-closed validator — not hand-written into
   `research_catalog` or any other canonical structure.
7. The resulting integrated candidate undergoes its own independent Codex audit.
8. Only after that audit passes does Stage 5 (final synthesis/freeze) begin.

## What this contract explicitly does NOT authorize

- It does not authorize reading Ismet's in-progress branch for any purpose.
- It does not authorize declaring the Codex parent audit passed or failed.
- It does not select a final integration base — that is `PROJECT_COORDINATOR` authority.
- It does not select a final architecture or compute a formal Pareto frontier.
- It does not begin Stage 5.
