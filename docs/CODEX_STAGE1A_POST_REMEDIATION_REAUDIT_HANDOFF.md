# Codex Stage 1A Post-Remediation Re-Audit Handoff (Day 12)

## Exact audited candidate

- **Branch:** `day12-post-remediation-integration`
- **Full SHA:** `4bcfd1a7b2c404e106c1d23c94fb9ebff0bcbf29`
- **Base:** `origin/day12-audit-remediation @ 45d99a4a521d0c97eab4273ed662a8ae8f9a37d3`
- **Merged in:** `origin/day12-sleep-scientific-remediation @ 0e03c63729ce7a1e374edd978ef55f9edd45f435` (clean `--no-ff` merge, zero file overlap, no manual conflict resolution)
- Working tree clean at handoff time; `main` untouched; branch not yet pushed (see integration report §29 for push status at the time you read this).

## Source lineage

```
169f99d  origin/day11-canonical-integration          (canonical base)
   └─ f2d895e  origin/day12-14-ismet-support-audit    (shared support tip)
        ├─ 45d99a4  origin/day12-audit-remediation    (Claude: H3/H4/H5/H7/M1-M12 fixes)
        └─ 0e03c63  origin/day12-sleep-scientific-remediation  (Ismet: H1/H2 fixes)
             └─ merge → 4bcfd1a  day12-post-remediation-integration  (this candidate)
```

Also present in the remote, **intentionally not merged**: `origin/stage1b-dataset-expansion-prep @ cd92836` — a parallel Stage 1B dataset-expansion track Emir confirmed is deliberately out of scope for this integration. Do not treat its absence as a gap.

## Finding matrix

| Finding | Status | Note |
|---|---|---|
| H1 (Sleep seed-init bug) | FIXED_WITH_LIMITATION | Corrected protocol + Primary A/B retraining done (10 checkpoints, 5 seeds each); C and interaction M_B/M_AB are `V2_PENDING_FOLLOWUP` by explicit design, not a silent gap |
| H2 (Resp native rate) | FIXED | Metadata-only, zero data/retraining impact, verified via EDF header + MNE source review |
| H3 (Reproduction default-PASS) | VERIFIED_IN_INTEGRATION | Pre-existing fix from `day12-audit-remediation`; unaffected by this merge (zero file overlap); reconfirmed green in the full backend suite (158 passed) |
| H4 (Engineering unknown→0) | VERIFIED_IN_INTEGRATION | Same as H3 — pre-existing fix, unaffected, reconfirmed |
| H5 (PPG marginal-value headline) | VERIFIED_IN_INTEGRATION | Pre-existing fix, unaffected by this merge; capacity-controlled headline (0.605 bpm, 5/5) confirmed live via API in this session |
| H6 | NOT_APPLICABLE | Not referenced by name in the governing prompt's completed-findings list for this stage; no H6-labeled artifact found in the repo |
| H7 (Power semantics) | VERIFIED_IN_INTEGRATION | Pre-existing fix, unaffected; "reference scenario, not guaranteed lower bound" wording confirmed present, no regression found in stale-string sweep |
| M1–M12 | VERIFIED_IN_INTEGRATION | Pre-existing fixes from `day12-audit-remediation`, unaffected by this merge (zero file overlap with Ismet's branch); backend/ML suites green |
| CLAIM-1 (lexical bypass) | DEFERRED_FOLLOWUP | Unchanged — still disclosed as a known limitation of the regex-based checker, not re-litigated this stage |
| New: Sleep V1/V2 version safety | FIXED | New `backend/app/research/sleep_version_guard.py` + `ComparisonRole` enum extension + `catalog._build_sleep_v1_v2_comparisons`; 13 new adversarial tests (Cases A–F from the governing prompt §36) all pass; live-API and live-browser confirmed |

## Highest-risk re-checks (attack these first)

1. **V2 B + V1 C mixed-protocol bug.** Try to find any code path that would combine `results/sleep_edf_primary_seedfix_v2.json` with `results/sleep_edf_eeg_eog_control_analysis.json` into one derived delta. Expected: none exists; `resolve_version_safe_comparison` in `sleep_version_guard.py` returns `available=False` for any V1/V2 mix. See `backend/tests/test_sleep_version_guard.py::test_case_c_mixed_v2_b_v1_c_is_blocked`.
2. **Reproduction default PASS.** `backend/app/research/catalog.py::_reproducibility` — confirm no code path returns PASS from missing/malformed evidence. Unaffected by this merge; re-verify anyway.
3. **Engineering unknown→zero.** `backend/app/research/engineering_readiness.py` — confirm missing values still resolve to `UNKNOWN`/`None`, never `0` or the old `48068` fallback.
4. **PPG old headline regression.** Grep the full repo for `9.0901`, `7.0317` (as a *pair* implying the old uncontrolled delta), `22.64`, `22.644` on active (non-historical, non-source-data) surfaces. This session's sweep found none; independently re-verify.
5. **Resp native-rate regression.** Grep for `native 100 ?Hz` or `matched native bandwidth` — none found this session on active surfaces.
6. **Checkpoint durability overstatement.** Grep for `70 externally archived` or `70/70`. None found. Cross-check `results/checkpoint_inventory_post_remediation_stage1a.json` against `results/final_checkpoint_inventory_day14.json` and `results/sleep_edf_primary_seedfix_v2.json::checkpoint_manifest`.
7. **Guaranteed-lower-bound wording.** Grep for `guaranteed lower bound` without a preceding `NOT` / `not a`. All occurrences found this session were correct negations.
8. **Cross-layer hash cascade.** Not touched by this integration (no contract/decision-inputs/freeze-manifest files were edited); `python -m app.research.decision_inputs` reproduces `results/pareto_decision_inputs.json` byte-identical (no git diff) — re-verify this still holds on your checkout.
9. **Archive/verifier exit-code behavior.** Unaffected by this merge (M9, pre-existing). Re-run `ml/tests/test_checkpoint_archive_guards.py`.
10. **Optional engineering panel failure isolation.** Unaffected by this merge (M12, pre-existing). Re-run `backend/tests/test_research_api.py` and inspect `frontend/src/store/researchStore.ts`.
11. **Claim traceability version mismatch.** `ml/check_claim_consistency.py` currently only validates artifact/field/route *existence*, not version-consistency between a claim's stated protocol and its resolved source. This is a genuine gap: nothing currently stops a future claim entry from citing `results/sleep_edf_primary_seedfix_v2.json` while describing it in V1 terms, or vice versa. Not fixed this stage (would require checker schema changes beyond the disclosed Sleep-versioning scope) — flag as a candidate M-finding for the next remediation round.
12. **Historical vs preferred Sleep result confusion.** Load `/research`, expand the Sleep-EDF card, confirm the `HEADLINE` badge is on the V2 comparison, `HISTORICAL — pre-seedfix (V1)` is dimmed/demoted, and the three `PENDING` comparisons show no numeric delta (should render "N/A").

## Commands (all confirmed runnable on this checkout at handoff time)

```bash
# Backend (158 passed, 0 failed)
cd backend && .venv/bin/python -m pytest -q

# ML (285 passed, 24 skipped -- dataset-dependent; mne/pandas/scikit-learn/tqdm/wfdb
# had to be installed into .venv-integration this sprint, see integration report §22)
.venv-integration/bin/python -m pytest ml/tests -q

# Claim consistency checker
.venv-integration/bin/python ml/check_claim_consistency.py

# Decision-inputs regeneration / drift check
cd backend && .venv/bin/python -m app.research.decision_inputs
git diff --stat results/pareto_decision_inputs.json   # expect: no output (byte-identical)

# Frontend
cd frontend && npx tsc --noEmit
cd frontend && npx eslint src/components/research/ResearchMode.tsx src/lib/types.ts
cd frontend && npm run build

# Sleep-specific adversarial tests (new this stage)
cd backend && .venv/bin/python -m pytest tests/test_sleep_version_guard.py -q

# Live API spot-check
cd backend && .venv/bin/uvicorn app.main:app --port 8000 &
curl -s http://127.0.0.1:8000/research/experiments/sleep-edf-eeg-eog-ablation | python3 -m json.tool
```

No archive/checkpoint-verifier CLI command is invoked in this handoff beyond the existing pytest suite (`ml/tests/test_checkpoint_archive_guards.py`) — Stage 1A did not build or publish a new external archive (per the governing prompt §12, prepare-inventory-only).
