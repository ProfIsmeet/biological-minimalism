# Stage 8 independent browser audit and corrective review

## Mission and provenance

This review independently tested Stage 8 cross-route cohesion, responsive behavior, accessibility, scientific truth, runtime stability, and preservation of accepted Mission Overview, Stage 6, and Stage 7 behavior. It began from exact source `origin/ismet/stage8-cross-route-product-cohesion@208c1b44c7c99d7b9a41e7e1807e5a0e67650645` in a clean isolated worktree and review branch `codex/stage8-independent-browser-audit`.

## Independent verdict

**PARTIAL.** Ismet's implementation was not accepted unchanged. One high and three medium defects were reproduced and corrected in `5c2fcf6f2f26925ce0207c446c15d9e55414ee10`; the browser/evidence adjudication is `2e6a999faeaf18f3d0b6248ba301061b0d52a53b`. No known critical/high/medium product defect remains, but complete acceptance is barred by missing durable final screenshot files and unavailable verifiable genuine zoom. Real S14, OS motion emulation, and actual screen-reader acceptance are also blocked/deferred.

## What Stage 8 changed

The incoming 106-file diff modernized eight user routes and the shared shell, unified typography/status/panel language, introduced source-scoped AI and timeline pages, made Settings static, refined Live Monitoring composition, and strengthened structural verification. The classification and risks are in `CHANGE_SCOPE_AUDIT.md`.

## Findings and corrections

- H-01: mutable singleton SHAP explainers raced across FastAPI worker threads and intermittently returned 500. Independent locks and real concurrent regression tests now serialize each explainer.
- M-01: synthetic channels were called replay inputs. Copy now follows authoritative source identity.
- M-02: Mission Overview clipped at 1024/768 due premature desktop breakpoints. Layout transitions now wait for safe content widths.
- M-03: key targets were 36–42px. Operational, drawer, constellation, and System Brief actions now meet 44px.

See `FINDING_LEDGER.md` and `CORRECTIVE_IMPLEMENTATION_LEDGER.md` for exact files and proof.

## Automated verification

Baseline: clean lockfile install; TypeScript/lint/build PASS; monitoring `1327/1327`; seven sub-verifiers PASS; rendered routes `146/146`; backend `351 passed, 4 skipped`; evidence verifier exit 0 with `23 PRESENT / 1 optional MISSING / 0 EMPTY / 0 AMBIGUOUS`; `git diff --check` PASS.

Final: TypeScript/lint/build PASS; monitoring `1341/1341`; seven sub-verifiers PASS; rendered routes `146/146`; backend `353 passed, 4 skipped`; evidence verifier unchanged and PASS; `git diff --check` PASS. No dependency version was changed.

## Runtime and browser environment

FastAPI ran on `127.0.0.1:8138`; the Next production server ran on `127.0.0.1:3148`; exact CORS origin was `http://127.0.0.1:3148`. REST preflights and requests returned 200, WebSocket connected, and expected replay subject discovery returned 409 because no real source was configured. Normal startup stabilized as connected synthetic without a false source error.

Every rendered route was opened directly, reloaded, clicked through the shell, and inspected at desktop/tablet/mobile sizes. Mission Overview and Live Monitoring received the full six-size matrix. All final document widths matched viewport widths. Tables that exceed mobile width either use local scrollers or mobile cards.

## Scientific integrity

Synthetic output remained explicitly synthetic and disclaimed. Missing HR remained unavailable; absent modalities remained absent; categorical graphics did not become probabilities; historical evidence stayed separate from live state; no EEG/EOG channel was fabricated; source/session/dataset isolation verifiers passed. The review did not alter accepted Stage 7 human geometry or Stage 6 visualization algorithms.

## Accessibility and motion

Keyboard testing verified the skip link, visible focus, shell links, Enter activation, Escape dismissal, focus traps, and focus restoration for both overlays. Representative accessibility trees had one H1, landmarks, names, dialog/table semantics, and chart alternatives. Actual screen-reader use was explicitly deferred.

The Reduce Motion preference synchronized live across two tabs and back. Structural consumers pass. OS media-query emulation was unavailable, so reduced-motion acceptance is partial. The browser did not expose verifiable page zoom: Meta-plus attempts left CSS viewport and DPR unchanged; genuine 200% zoom is `BLOCKED_EXTERNAL`.

## Evidence adjudication

The in-app browser displayed more than 30 fresh screenshots and final layouts were visually reviewed. Its security boundary prevented writing screenshot bytes to the worktree. Twelve representative transient hashes are recorded, but all have null paths and are not called canonical evidence. Repository-backed Stage 8 evidence count is zero, forcing the partial verdict. See `EVIDENCE_ADJUDICATION.md` and `EVIDENCE_MANIFEST.json`.

## Merge, rollback, and Stage 9

The product corrections are technically ready for owner review, but the branch should not be merged under complete-acceptance rules until durable evidence and genuine zoom are supplied. Stage 9 is not authorized by this verdict. Rollback can revert the corrective and report commits; retaining H-01 is strongly recommended because it prevents real 500 responses.

## Report index

This directory contains the executive verdict, source state, change audit, finding/correction/test ledgers, automated and browser matrices, accessibility, motion, scientific integrity, evidence adjudication and manifest, merge recommendation, and review entrypoint required by the audit contract.
