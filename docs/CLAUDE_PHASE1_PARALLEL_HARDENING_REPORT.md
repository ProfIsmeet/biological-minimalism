# Claude Phase 1 — Parallel Integration-Prep Hardening Report

**Branch:** `stage2-4-claude-integration-prep`
**Base / starting SHA:** `d97b4d5ea82ab039c6d79e095b0c2833ca82bb71` (`origin/stage2-4-sleep-canonical`, verified)
**Canonical Stage-1A ancestor:** `52bd2eca1ef89b0460a4a3dd3648118176ad6610` (`origin/day12-post-remediation-integration`) — confirmed ancestor via `git merge-base --is-ancestor`
**Scope:** Software/engineering audit + hardening only. No model training, no new science, no science value changes.

---

## 1. Repository state at start

- Branch at session start: `stage2-4-sleep-canonical` @ `d97b4d5` (matches expected).
- Working tree: 5 untracked, repo-foreign items present at session start (kept untouched, see §9).
- Local `main` = `d257f19` (1 commit behind `origin/main` = `b02c6db`; local `main` was never mutated, reflog shows only "Created from origin/main"). No divergence risk — local is strictly behind, not ahead.
- Created `stage2-4-claude-integration-prep` from verified `d97b4d5` per governing prompt §5; all subsequent work happened on this branch only.

## 2. Active canonical state reconstructed (read from source, not just docs)

- Live backend (`uvicorn`, port scratch-tested) confirms, byte-for-byte matching the schemas:
  - `system_average_power_status = SYSTEM_AVERAGE_POWER_NOT_READY`
  - `system_mass_status = SYSTEM_MASS_NOT_READY`
  - `bom_status = PARTIAL`
  - `formal_pareto_status = FORMAL_PARETO_NOT_READY`
  - `final_architecture_status = UNRESOLVED`
- `/research/experiments/sleep-edf-eeg-eog-ablation` live payload confirms the V2 seed-corrected headline is live (`seed_corrected_v2_primary_ab`), with V1 historical preserved and three legs (`C`, `M_B`, `M_AB`) explicitly `SEED_CORRECTION_PENDING_FOLLOWUP` with `delta: null` — no fabricated numbers.
- `/digital-twin` API returns a scripted mission-narrative payload (mock, no ML forward pass); the frontend `/digital-twin` page explicitly labels it "synthetic, conceptual... untrained and not validated."
- The most recent commit (`d97b4d5`) is purely additive (10 new files, 0 modified, 0 deleted) — new Stage-2 candidate trainers/handoff docs for Ismet. Independently confirmed **zero** canonical backend/`ml` code path imports or references any of these new files (`claude_noncanonical_sleep_edf_primary_seedfix_v2_reproduction.json`, `claude_to_ismet_science_transfer_manifest.json`, `hmc_split_stage2.json`, the 4 new `ml/*.py` trainers) — full isolation confirmed.

## 3. H3/H4/H5/H7 (+M1/M5/M7/M10, Sleep V1/V2 guard, Digital Twin) regression audit

Independently re-verified by direct source reading (not by trusting prior docs), cross-checked against a dedicated re-verification pass:

| # | Item | Verdict |
|---|---|---|
| H3 | Reproduction API never defaults to PASS | **INTACT** — `catalog.py::_reproducibility`/`_overall_from_components` computes worst-of over typed `ReproComponentStatus` (PASS/PARTIAL/FAIL/UNAVAILABLE/MALFORMED); 12 adversarial tests in `test_reproducibility_panel.py` pass. |
| H4 | Engineering unknown never becomes 0 | **INTACT** — `engineering_readiness.py::_quantity` returns `UNKNOWN(value=None)` for missing/non-numeric; the old `48068` fallback appears only in comments explicitly warning against it. |
| H5 | Old uncontrolled PPG headline retired | **INTACT** — live headline is the capacity-controlled `A_cap→B` (~0.605 bpm); old numbers (9.0901/7.0317/22.64) exist only in frozen source-data JSON and test fixtures, never as a live/current headline. |
| H7 | Power wording — reference scenario, not guaranteed lower bound | **INTACT** — all 14 repo-wide "guaranteed lower bound" hits are negated or meta-references; zero unqualified assertions. |
| M1 | Metric direction explicit | **INTACT** — `MetricDirectionality` enum, per-record, no universal "lower wins" leak (verified in `catalog.py` and `ResearchMode.tsx`). |
| M5 | EOG/Resp native vs model rate | **INTACT, H2 has progressed** — H2 is now `H2_CLOSED_METADATA_ONLY` on Ismet's merged branch (disclosed correction, no silent edit); no Resp modality claimed in the data-rate budget. |
| M7 | Cache provenance | **DOCUMENTED LIMITATION CONFIRMED UNCHANGED** — PPG-DaLiA cache is stamped (`ppg_dalia.py`); PTT cache (`pulse_transit_time_ppg.py`) is still unstamped/legacy exactly as disclosed — no silent regression either direction. |
| M10 | TorchInferenceEngine / Digital Twin honesty | **INTACT** — `runs_real_inference = False`, name `torch_v1_mock_passthrough`, docstring/tests assert no forward pass; `/digital-twin` full page explicitly discloses synthetic/untrained. |
| — | Sleep-EDF V1/V2 version-mixing guard | **INTACT** — `sleep_version_guard.py::resolve_version_safe_comparison` blocks any mixed-version pair (`available=False, BLOCKED_MIXED_PROTOCOL_VERSION`); 13 adversarial tests pass; consuming code in `catalog.py` independently reinforces this by never reusing V1 values for pending V2 legs. |
| — | Digital Twin preview widget (Mission Overview) | **GAP FOUND AND FIXED** — see §6. |

## 4. Fallback/default audit (repository-wide sweep)

Two independent sweeps (a hostile grep-and-classify pass, plus my own targeted checks) covered: the six Day-12 named regression strings, `or 0` / `?? 0` / `|| 0` patterns, broad `except` blocks masking failure as success, hardcoded science constants in application code, and `dict.get(..., "PASS")`-style defaults.

**Result: zero regressions of any of the six Day-12 named findings. Zero new BUG-classified findings from either sweep — with one exception found and fixed during this session (see §6).**

Classified findings:
- **HISTORICAL:** 9 (old numbers present only in frozen source JSON, coincidental numeric collisions verified as unrelated, environment-manifest Windows/Python-3.13 snapshot explicitly labeled "Day 8, captured as-is, not upgraded/altered").
- **TEST_FIXTURE:** 7 (assertions against frozen historical values, not live claims).
- **DEAD_CODE:** 1 (`catalog.py:367` `.n or 0` — unreachable because the upstream `_require()` call already raises on a missing key; not a live bug, left as-is per "fix only genuine defects").
- **NEEDS_REVIEW (informational, no fix required this phase):**
  - `inference.py::create_inference_engine` swallows a Torch-checkpoint-load exception without logging — both fallback paths are already labeled non-real mocks, so this is not a science-masking regression, just a missing log line.
  - Several `catalog.py`/`engineering_readiness.py`/`day6.py` locations hand-duplicate artifact-derived numbers into human-readable narrative prose (currently accurate, but would go stale silently if the source artifact were regenerated with different numbers) — same failure *shape* as the already-fixed `48068` constant, but not itself a defect today. Flagged for a future remediation pass, out of Phase-1 scope to rewrite every narrative string.
  - `ml/train_hmc_sleep_a_b_c.py` and `ml/datasets/hmc_sleep.py` (new, never-executed Stage-2 candidate files from `d97b4d5`) reference `results/hmc_protocol_stage1b.json`, which does not exist on this branch (it lives only on the separate, intentionally-unmerged `stage1b-dataset-expansion-prep` branch). These files are documented as never-run handoff candidates, so this is an inert cross-branch dependency, not a live defect.

## 5. Version-mixing risks

- The Sleep-EDF V1/V2 guard (`sleep_version_guard.py`) is the single choke point for any V1/V2 comparison and is proven adversarially (13 tests) to block mixed-protocol pairs. No code path was found anywhere in `catalog.py` that bypasses it to construct a mixed delta.
- HMC/ds003838/GalaxyPPG/LBNP data from the historical `stage2-4-expansion-science` lineage (merged into this branch's ancestry, e.g. `fe32384`, `ba9d605`, `ce59871`) remains present only as historical/intermediate evidence; none of it is wired into any canonical API/builder path, and no code in this session promotes it to "final" status, consistent with governing-prompt §7.
- The new Stage-2 candidate files added in `d97b4d5` (HMC A/B/C trainer, corrected shuffled-EOG/interaction trainers, noncanonical A/B reproduction JSON) are confirmed fully isolated from every canonical backend/`ml` import path (§2).

## 6. Bugs found and fixed this session

**Finding 1:** `backend/app/research/catalog.py:1309` (function `_build_sleep_supplementary_breakdowns`) computed the Sleep-EDF secondary-holdout per-class `"regresses"` flag as `(rec.get("B_minus_A") or 0) < 0`. If a future regeneration of `results/sleep_edf_secondary_holdout_evaluation.json` ever omitted a sleep stage class, the missing value would silently render as `"regresses": False` ("does not regress") instead of unknown — the exact "missing → fabricated value" failure shape the Day-12 audit already fixed once for the `48068` engineering constant (H4). Currently dormant (today's artifact has all 5 classes), flagged `NEEDS_REVIEW` by the fallback-pattern sweep.

**Fix applied:** `"regresses": (rec.get("B_minus_A") < 0) if rec.get("B_minus_A") is not None else None`. No schema change needed — `ResearchBreakdownEntry.dimensions` (`backend/app/schemas/research.py:174`) already types values as `str | float | int | bool | None`.

**Test added:** `backend/tests/test_research_api.py::test_secondary_class_level_missing_class_is_unknown_not_false` — constructs a synthetic artifact missing 3 of 5 classes and asserts `regresses is None` for each missing class, `False`/`True` correctly for present classes.

**Blast radius verified before editing:** confirmed no other module imports this private function except the new test; confirmed this breakdown (`secondary_class_level` / `b_minus_a` / `regresses`) is not yet consumed by key name anywhere in the frontend, so the fix has zero visible UI impact today and is a pure backend-contract correctness fix.

**Finding 2:** `frontend/src/components/panels/DigitalTwinPreview.tsx` (rendered on `/mission-overview`, a primary dashboard page) showed the Digital Twin adaptation gauge with no inline synthetic/untrained disclaimer — unlike the full `/digital-twin` page (which explicitly says "synthetic, conceptual... untrained and not validated") and unlike sibling panels (e.g. `SensorHealthPanel` says "synthetic demo"). A viewer who only sees the Mission Overview card, without clicking through, could misread the percentage as a real/validated metric — directly relevant to governing-prompt §52's hostile-review question "Does Digital Twin look trained?"

**Fix applied:** added a one-line caption below the gauge: "Synthetic, untrained illustration — not a validated prediction." The existing milestone-label subtitle was preserved unchanged.

## 7. Engineering readiness (re-verified live, not just from docs)

Confirmed live via the running API (not just static JSON): `system_average_power_status`, `system_mass_status`, `bom_status`, `formal_pareto_status`, `final_architecture_status` are all independent typed fields — a component-level power figure (e.g. "~0.018 mW (band 0.018–0.378), accel-only") cannot structurally collide with or overwrite the system-level `NOT_READY` status; the API's own caveat text says so explicitly ("component power is not system power, and system mass is NOT_READY"). `pareto_readiness_blockers.json` confirms `pareto_status: NOT_READY` with an explicit blocker list (cross-dataset incomparability = BLOCKER; power/mass = HIGH).

## 8. Architecture / Pareto state

- `architecture_decision_matrix.json`: per-(target, candidate) decisions only, explicit `decision_vocabulary` with no global-ranking verb; `interaction_evidence_status: partial` disclosed.
- Live API: `final_architecture_status = UNRESOLVED`, `formal_pareto_status = FORMAL_PARETO_NOT_READY`. No code path found that auto-computes a Pareto frontier or auto-selects an architecture from the current evidence.

## 9. Synthetic/real isolation & repository hygiene

- `git ls-files` sweep confirms nothing under `.work/`, `.codex_tmp/`, `outputs/`, `archival/`, `node_modules/`, `__pycache__` is accidentally tracked — hygiene is clean.
- **Foreign, unrelated files present at session start (left untouched, not part of this repo's work):** `edit_haydarpasa.mjs`, `help_table_rows.mjs`, `inspect_basliksiz.mjs`, `inspect_haydarpasa.mjs` — confirmed by content inspection to be scratch scripts manipulating an Excel file in `~/Downloads` via `@oai/artifact-tool`, unrelated to Biological Minimalism. `node_modules` at repo root is a symlink to a Codex CLI runtime cache directory, not this project's dependencies (frontend's real `node_modules` lives under `frontend/`). None of these were staged, committed, or referenced by any change in this session. **Recommendation:** the user should move or delete these four files and the stray symlink from the repo root, since a broad `git add -A` (never used by this session) would otherwise sweep them in.
- Digital Twin/mock-inference boundary confirmed genuinely isolated: `AIInferenceEngine`/`TorchInferenceEngine` explicitly documented as mock-only; `/digital-twin` mission-narrative endpoint is a scripted engine (`mock_data_engine.py`), not backed by any trained checkpoint.

## 10. Bugs found

1. `catalog.py:1309` — missing sleep-class value could render as fabricated `"regresses": False` instead of unknown. **BUG — FIXED** (§6).
2. `DigitalTwinPreview.tsx` — Mission Overview Digital Twin card had no inline synthetic/untrained disclaimer. **BUG (representation) — FIXED** (§6).
3. One dead cross-branch file reference in never-executed Stage-2 candidate code (`hmc_protocol_stage1b.json`). **NEEDS_REVIEW, not fixed** — inert, would only surface if someone runs the pending trainer before Stage 1B is merged; out of scope to fix without touching the isolated stage1b branch.

No other genuine implementation defects found across two independent full-repository sweeps.

## 11. Bugs fixed

- §6, Finding 1 (backend, `catalog.py` + new test).
- §6, Finding 2 (frontend, `DigitalTwinPreview.tsx`).

## 12. BLOCKER

None.

## 13. HIGH

None found this phase (all previously-identified HIGH findings from Day-12, H1–H7, remain FIXED/DEFERRED-with-disclosure as documented; H1/H2 have since progressed further on Ismet's side, out of this phase's scope to re-litigate).

## 14. MEDIUM

- The Digital Twin preview-widget disclosure gap (§6, Finding 2) — treated as MEDIUM (visible on a primary dashboard page) and fixed this session.

## 15. LOW

- Dead cross-branch file reference in never-run Stage-2 candidate trainers (§10, item 3) — informational only.
- Narrative-prose duplication of artifact-derived numbers in `catalog.py`/`engineering_readiness.py`/`day6.py` (§4) — currently accurate, disclosed as a drift risk for a future pass, not fixed this phase (broad rewrite, out of proportion to Phase-1 scope).
- `inference.py::create_inference_engine` swallows a checkpoint-load exception without logging (§4) — both fallback paths are already labeled mocks; no science-masking risk, just missing observability.
- The four foreign `.mjs` files + stray `node_modules` symlink at repo root (§9) — not committed, but recommended for user cleanup.

## 16. Tests (exact counts)

| Suite | Command | Result |
|---|---|---|
| Backend (full) | `cd backend && .venv/bin/python -m pytest -q` | **159 passed**, 0 failed (158 baseline + 1 new regression test) |
| ML (non-training) | `.venv-integration/bin/python -m pytest ml/tests -q` | **290 passed, 19 skipped**, 0 failed (all skips are legitimate dataset/checkpoint-absence guards, verified individually — none silently masks a genuine issue) |
| Claim consistency | `.venv-integration/bin/python ml/check_claim_consistency.py` | `STRUCTURED_TRACEABILITY_AND_FORBIDDEN_PATTERN_CHECK_PASS`, exit 0 |
| Decision-inputs determinism | `cd backend && .venv/bin/python -m app.research.decision_inputs` then `git diff results/pareto_decision_inputs.json` | byte-identical, no diff, no other file touched (checked before and after code edits) |
| Frontend typecheck | `cd frontend && npx tsc --noEmit` | clean, 0 errors |
| Frontend lint | `cd frontend && npx eslint .` (full) + targeted re-run on edited file | clean, 0 warnings/errors |
| Frontend build | `cd frontend && npm run build` | succeeds, all 12 static routes generated, re-run after the `DigitalTwinPreview.tsx` fix — still clean |

## 17. Files changed

- `backend/app/research/catalog.py` (1 line → 3 lines; bug fix, §6)
- `backend/tests/test_research_api.py` (+1 import, +23 lines new test)
- `frontend/src/components/panels/DigitalTwinPreview.tsx` (+5 lines disclaimer)
- `docs/CLAUDE_PHASE1_PARALLEL_HARDENING_REPORT.md` (this report, new)

No `results/*.json` file was modified (decision-inputs regeneration confirmed byte-identical both before and after all edits). No science file touched.

## 18. Commit / SHA / push state

Committed on `stage2-4-claude-integration-prep` (branched from `d97b4d5`); pushed to `origin/stage2-4-claude-integration-prep` with upstream tracking set. Local and remote verified equal after push (see commands executed as part of this phase's close-out, logged in the session).

## 19. Main protection

- Local `main` untouched throughout (`git reflog main` shows only its original creation from `origin/main`, no new entries).
- No checkout onto `main`, no merge, no push to `main` performed at any point.
- Local `main` (`d257f19`) remains 1 commit behind `origin/main` (`b02c6db`) — unchanged from session start, purely informational, not touched by this phase.

## 20. Phase verdict

**PHASE1_COMPLETE**

All six Day-12 named regressions re-verified with zero recurrence. All previously-documented H3/H4/H5/H7/M1/M5/M7/M10 fixes and the Sleep V1/V2 version guard independently re-confirmed intact by direct source reading (not by trusting prior audit docs). Two real, narrowly-scoped defects were found by hostile sweep and fixed with regression coverage and full test/build re-verification. No blockers. No science touched. Main untouched. Ready for Phase 2 on explicit "DEVAM".
