# Five-Stage Completeness Matrix

Source of truth for what is genuinely complete as of this audit
(`claude/stage2-3-final-acceptance`, base `779c265ca4f3d9f24c15994b8d301e68fc02ea3c`).
Status vocabulary: `COMPLETE`, `PARTIAL`, `BLOCKED_EXTERNAL`, `NOT_STARTED`.

| Stage | Status | Basis |
|---|---|---|
| Stage 1 — Scientific data integrity | COMPLETE (inherited, unchanged) | Base SHA carries Stage 1 protections unmodified; not in scope for edits this session; baseline gate reproduced identically |
| Stage 2 — Accessibility / runtime safety | **PARTIAL** | See breakdown below — everything except the actual OS screen reader is COMPLETE |
| Stage 3A — Deployment/Docker | **PARTIAL (COMPLETE_STATIC_ONLY)** | Everything verifiable without a Docker daemon is COMPLETE; container-runtime gates are BLOCKED_EXTERNAL (Docker not installed on host) |
| Stage 3B — Canonical jury demo / real S14 | **PARTIAL (CONDITIONALLY_ACCEPTED)** | Missing-prerequisite fail-closed path COMPLETE against the real backend; real S14 success BLOCKED_EXTERNAL (dataset/checkpoint absent) |
| Stage 4 | NOT_STARTED | Explicitly out of scope for this task; not touched |

## Stage 2 breakdown

| Item | Status | Evidence |
|---|---|---|
| Live-region / announcement boundaries | COMPLETE | Inherited from Ismet's A1 fix + prior Codex browser DOM verification; reconfirmed via 1021/1021 suite this session |
| Reduced-motion full 14-point matrix | **COMPLETE** | AUDIT.md §5 — this session's primary contribution; genuine `matchMedia` emulation, all 14 scenarios PASS |
| Mobile dialog / focus trap | COMPLETE | AUDIT.md §6 — reconfirmed with real keyboard events this session |
| WebGL fallback (unsupported / error / context-loss) | COMPLETE | AUDIT.md §6 — reconfirmed with real `getContext` override and real `WEBGL_lose_context` this session |
| 200% zoom | COMPLETE | AUDIT.md §6 |
| **Actual OS screen reader** | **NOT_RUN / DEFERRED** | Explicitly deferred by the repository owner for this task (AUDIT.md §9); not claimed as passed |

Stage 2 overall verdict is `PARTIAL` **only** because the actual-screen-reader
gate is a hard requirement for `COMPLETE` per the acceptance rules, and it
was deliberately not exercised this session at the owner's direction.

## Stage 3A breakdown

| Item | Status | Evidence |
|---|---|---|
| `docker-compose.yml` structural validity | COMPLETE (YAML-parse substitute) | AUDIT.md §7 |
| Frontend Dockerfile uses `npm ci`, not `npm install` | COMPLETE | AUDIT.md §7 |
| Lockfile unchanged | COMPLETE | SHA-256 matches prior audit exactly |
| API/WS build-time configuration correctness | COMPLETE | Dockerfile ARGs and compose args and `config.ts` all agree |
| No private backend env leak into jury UI | COMPLETE | `verify_jury_environment.py` PASS |
| Image builds | BLOCKED_EXTERNAL | Docker not installed |
| Container start / health / REST / WS / CORS-in-container / recovery / shutdown | BLOCKED_EXTERNAL | Docker not installed |

## Stage 3B breakdown

| Item | Status | Evidence |
|---|---|---|
| Missing-prerequisite fail-closed path (real backend) | COMPLETE | AUDIT.md §8 — exact message, 3x-repeat idempotent, no stale identity |
| Real S14 canonical success | BLOCKED_EXTERNAL | Dataset/checkpoint absent; not fabricated |
| Hostile-state convergence with real S14 | BLOCKED_EXTERNAL | Same reason |
| Supersession / idempotency logic (generic, dataset-independent) | COMPLETE (inherited) | 1021-check suite, corrective-review fix (`outcome: "superseded"`) reconfirmed in baseline gate |

## What would need to change for `READY_FOR_STAGE4: YES`

1. A qualified operator runs the actual-screen-reader matrix (already
   drafted, see `docs/ismet-stage2-3/MANUAL_ACCEPTANCE_CHECKLIST.md` and
   AUDIT.md §9) with VoiceOver/NVDA/Narrator and records real transcripts.
2. Docker Engine becomes available on a build/test host and the full
   Stage 3A container-runtime matrix (compose up, health, REST, WS, CORS,
   restart, shutdown) is executed for real.
3. An approved local PPG-DaLiA distribution and validated HR checkpoint are
   configured, and the real S14 canonical-success + hostile-state +
   idempotency scenarios are run against the real backend.
4. Codex (or another independent reviewer) performs the final independent
   review this task's rules require before any merge recommendation.

None of these four items were skipped by choice within this task's control;
each is either an explicit external environment gap (Docker, dataset) or an
explicit owner-directed deferral (screen reader), both honestly recorded
rather than worked around.
