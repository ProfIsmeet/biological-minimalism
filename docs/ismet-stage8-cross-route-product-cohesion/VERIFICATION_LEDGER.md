# Verification ledger

## Baseline, reproduced before any mutation

Verified at source SHA `dc2039d53773ebfad763e0716f51876fb8185058` before a
single file was touched, so every later number is a comparison and not a guess:

| Gate | Baseline |
|---|---|
| `npx tsc --noEmit` | clean |
| `npm run lint` | clean |
| `npm run build` | succeeds |
| `npm run verify:monitoring` | **1247/1247**, all 7 sub-verifiers pass |
| backend `pytest` | 351 passed, 4 skipped |
| evidence verifier | exit 0 |

The brief estimated "around 1247" monitoring checks; the reproduced count was
exactly 1247, which is what made the later deltas trustworthy.

## Final

| Gate | Final | Delta |
|---|---|---|
| `npx tsc --noEmit` | clean | — |
| `npm run lint` | clean | — |
| `npm run build` | succeeds, 12 routes prerendering | — |
| `npm run verify:monitoring` | **1327/1327** | +80 added, 0 removed |
| sub-verifiers | all 7 pass | — |
| `npm run verify:rendered` (new) | **146/146** | new gate |

The 1247 baseline assertions are all still present and still passing. Six
assertions were **rewritten in place** rather than removed — see below.

## Sub-verifier output, final run

```
verify-monitoring-state: 1327/1327 passed, 0 failed
verify-monitoring-consumers: checked 20 protected file(s) for raw missionStore.latest and missionStore.history reads.
verify-live-region-boundaries: checked 3 protected file(s) for ticking values inside aria-live/role="status" regions.
verify-reduced-motion-unification: checked shared hook, MotionConfig wiring, and 2 WebGL/Framer consumers for a single reduced-motion source of truth.
verify-modal-dialog-primitives: checked the shared useModalDialog() hook and its 2 known dialog consumers.
verify-webgl-fallback: checked WebglStage, WebglErrorBoundary, and 2 Canvas-rendering consumers for unsupported/error/context-loss coverage.
verify-stage7-digital-twin: checked production route, interaction controls, semantic fallback, reduced motion, and monitoring isolation.
```

## Assertions rewritten, not removed

Six `C-01 shared floor` checks previously asserted that `globals.css`
force-promoted `.text-[9px]` through `.text-[11px]` to 12px with `!important`.
That mechanism was removed this stage (finding M-4), which left two bad options
and one good one:

- Deleting them would have dropped real coverage, and the brief forbids
  lowering counts.
- Leaving them would have asserted a mechanism that no longer exists.
- **Chosen:** rewrite them in place to assert the invariant they always existed
  to protect — that no file sets any of those five sizes, anywhere. That is
  strictly stronger than asserting a stylesheet papers over them.

Same six assertions, same section, same count, checking the real property
instead of its workaround.

Separately, the `/settings` runtime-tier assertion changed from "is live-feed"
to "is static", and two assertions were added alongside it proving the route
opens no socket and mounts no monitoring session. That is also a
strengthening: the old assertion said the preferences page *did* open an
operational connection.

## Guards proved to discriminate, not merely pass

A guard that passes because its pattern never matches anything is worse than
no guard, because it reports safety. Two were explicitly tested against known
violations rather than trusted:

**The page-title ceiling guard** was run against five inputs before being
accepted. It matched the exact 34px title this stage removed, matched
`text-3xl`, matched the 56px display hero, and did **not** match the canonical
24/28 scale or a large non-title number.

**The palette and alpha guards** were validated by the fact that they found
528 real violations the previous, narrower version had passed over (finding
H-6), and the alpha pattern's trailing-word-boundary bug (L-2) was found by
noticing it returned zero while `grep` returned 41.

Four guards were corrected after producing false positives (L-1, L-3, L-4) —
each correction is recorded at the guard itself with the reason, so the next
reader does not reintroduce the looser form.

## What the automated gates cannot prove

Stated so the verdict is not read as broader than it is:

- Nothing requiring layout or paint: no overflow detection, no measured
  contrast ratio, no focus-ring visibility, no rendered hit-target geometry.
- Nothing requiring interaction: no keyboard traversal order, no focus-trap
  behaviour under real tabbing, no scroll locking.
- No genuine 200% zoom acceptance.
- No screen-reader acceptance. **VoiceOver acceptance is not claimed.**
- No Docker or container runtime acceptance. **Not claimed.**
- No real-device or real-browser rendering at any viewport — see
  `RESPONSIVE_ACCEPTANCE_MATRIX.md`.

The structural assertions are proxies for several of these: `min-h-11` in the
source is evidence about a hit target, but it is not a measurement. The
distinction is maintained throughout these reports.

## Reproducing this

```bash
# offline gates
cd frontend
npx tsc --noEmit
npm run lint
npm run build
npm run verify:monitoring

# rendered-route acceptance (needs a running server)
cd ../backend && ./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8137 &
cd ../frontend && NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8137 npx next dev -p 3147 &
npm run verify:rendered -- http://127.0.0.1:3147
```

Ports 8137 and 3147 were chosen as task-specific and unused; only the services
this task started were stopped afterwards.
