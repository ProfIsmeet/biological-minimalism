# Finding Ledger — Stage 7 Independent Browser Acceptance

All findings from the independent audit of Stage 7 (`origin/codex/stage7-digital-twin-integration`
@ `c01f66f43a76c953996d811f3e846f3ac7d9a09c`), performed on branch
`ismet/stage7-independent-browser-acceptance`. Every CRITICAL/HIGH/MEDIUM finding was
corrected in this branch. No LOW/INFORMATIONAL finding required a code change.

---

## S7-AUDIT-02 — HIGH — Chest/Wrist camera focus silently fails to render under `demand` frameloop

**Claim challenged:** "Chest focus = ECG sensor location only; Wrist focus = PPG+IMU
sensor locations only" (implies a working close-up camera transition on selection).

**Evidence:** Visual inspection of an early capture of `04-desktop-chest-focus.png`
showed `aria-pressed="true"` and a correct selection ring, but the figure remained at
full-body scale — no visible zoom. Independently reimplemented the frustum math in a
standalone script (`mathcheck.mjs`, not committed) and confirmed chest's
`viewHeight: 0.74` should produce a view ~2.95× tighter than the full-body baseline
(~2.18) — ruling out "the preset value just isn't visually different enough." Ruled
out test-script timing/selector bugs (generous 2s/3s/8s waits, exact-match selectors,
`aria-pressed` reliably `"true"`), dev-server/HMR cache corruption (bug reproduced
identically after a full `rm -rf .next` + restart), and "just needs more time"
(8-second wait still stuck). A newly-added `frontal` preset (see S7-AUDIT-01, tighter
`viewHeight: 0.42`) zoomed correctly on first click while Chest/Wrist did not — this
asymmetry pointed at the camera-mutation code path itself, not the frustum math.
Added a temporary diagnostic (`window.__AUDIT_LOG`, later fully removed) logging
`camera.top`/`camera.bottom`/`projectionMatrix.elements` inside `ViewRig`'s effect and
ran a sequential chest→frontal→wrist click test: the camera object's own data was
**always correct** (chest: viewHeight 0.74 confirmed via projection-matrix scale
factor 1.719 vs. default's 0.583; frontal: 0.42/3.029; wrist: 0.58/2.194 — all
mathematically consistent) — proving the bug was not in the frustum math or the
camera-mutation code, but purely in whether the canvas ever repainted to reflect it.

**Root cause:** `ConceptualTwinStage.tsx`'s `ViewRig` sub-component mutates
`camera.left/right/top/bottom/position` imperatively inside a plain `useEffect`. Under
this route's `"demand"` frameloop — active whenever motion is paused, i.e. for every
non-default view, since selecting Chest/Wrist/Frontal pauses rotation — React Three
Fiber only schedules a repaint on an explicit `invalidate()` call or a JSX-prop diff
visible to its own reconciler. A direct, non-reconciler-visible mutation of a Three.js
object's properties is invisible to that mechanism, so the canvas kept presenting its
last-painted full-body frame indefinitely, even though the underlying camera state was
fully correct.

**Affected files:** `frontend/src/components/visualization/human/ConceptualTwinStage.tsx`
(`ViewRig` function).

**Correction:** Added `const invalidate = useThree((state) => state.invalidate);` and
called `invalidate()` at the end of `ViewRig`'s effect (with `invalidate` added to the
dependency array), forcing the next repaint to happen regardless of frameloop mode.

**Regression test:** `verify-monitoring-state.ts` — two new source-guard checks
confirming `ViewRig` calls the real R3F `invalidate` (`useThree((state) => state.invalidate)`)
and actually invokes it after the camera mutation. These are explicitly documented in
the test file as *supplementary* to the real runtime evidence below — a source check
alone cannot prove the browser actually repaints.

**Browser retest:** Re-ran the exact same sequential-click diagnostic post-fix:
`seq-1-chest.png` now shows a correct, dramatic torso close-up with the ECG landmark
large and clear; `seq-3-wrist.png` shows a correct close-up of the wrist/hand with
PPG/IMU landmarks large and clear; `seq-2-back-to-default.png` confirms the Default
full-body view is unaffected by the fix. Re-ran the full capture suite against a
freshly restarted, cache-cleared dev server; `04-desktop-chest-focus.png` and
`05-desktop-wrist-focus.png` (final evidence) show the correct close-up framing, with
file sizes (345KB/304KB) notably larger than the pre-fix captures (246KB/246KB each)
as independent corroborating evidence of genuinely different rendered content.

**Final disposition:** **FIXED and verified.** This is the single highest-value finding
of this audit — the original implementer's structural-only verification
(`verify-stage7-digital-twin.mjs`'s source-string checks) could not have caught it,
since the source code looked entirely correct; only genuine runtime browser testing
could reveal it.

---

## S7-AUDIT-01 — MEDIUM — "Frontal module" semantic-list card was reachable but never actually selectable

**Claim challenged:** Semantic architecture summary offers Focus-region/Selected-region
affordances for every module, including Frontal (EEG/EOG).

**Evidence:** Code review of `ConceptualTwinStage.tsx`'s semantic-list module-card
`onClick` handler:
```tsx
onClick={() => selectView(module.id === "chest" ? "chest" : module.id === "wrist" ? "wrist" : "front")}
```
The `"Frontal module"` card (an actual card in the list, exposing the same
"Focus region"/description affordance as Chest and Wrist) fell into the `"front"`
branch — the plain Front full-body orientation, which sets `activeRegion: null`. The
card was reachable and clickable, but clicking it could never reach a "Selected
region" state, and EEG/EOG (2 of 5 canonical modalities) had no dedicated close-up
camera framing at all, unlike Chest (ECG) and Wrist (PPG+IMU).

**Root cause:** `digitalTwinPresentation.ts`'s `DIGITAL_TWIN_VIEW_PRESETS` never
defined a `"frontal"` view preset — only `default`/`front`/`back`/`chest`/`wrist`
existed — so there was no dedicated target for the card to select even if wired
correctly.

**Affected files:** `frontend/src/lib/visualization/digitalTwinPresentation.ts` (new
`frontal` preset), `frontend/src/components/visualization/human/ConceptualTwinStage.tsx`
(module-card `onClick` rewire).

**Correction:** Added a `frontal` entry to `DIGITAL_TWIN_VIEW_PRESETS` —
`activeRegion: "Frontal"`, `target: [0, 1.68, 0]` (`H_JOINTS.headCenter.y`, imported
unmodified from `holographicGeometry.ts`), `viewHeight: 0.42` (tighter than chest's
0.74/wrist's 0.58, appropriate for a head/neck close-up) — and rewired the module-card
`onClick` to route to `"frontal"` instead of `"front"` for the Frontal module
specifically. Deliberately did **not** add a new keyboard shortcut for `frontal`
(kept the existing `1`/`2`/`3`/`4`/`Escape`/`Home`/`0` contract exactly as-is) — the
preset is reachable only via the semantic-list card, matching the existing pattern
that not every view needs a dedicated hotkey. `ArchitectureSensorContacts.tsx` was
confirmed (read, unmodified) to already support arbitrary `activeRegion` values
including `"Frontal"` via `REGION_ORBITS` (imported from `humanLayout.ts`, unmodified)
— so only the UI-reachability was broken, not the underlying rendering capability.

**Regression test:** `verify-monitoring-state.ts` — asserts `DIGITAL_TWIN_VIEW_PRESETS.frontal.activeRegion === "Frontal"`,
`.viewHeight === 0.42`, a finite-frustum check via `computeDigitalTwinFrustum`, and a
source-string guard confirming the module-card wiring routes to `"frontal"` not
`"front"`.

**Browser retest:** `09-desktop-frontal-focus.png` (supplemental evidence) shows a
correct close-up of the head/neck region with EEG/EOG landmarks large and clear,
selection ring active, "Selected region: Frontal" reflected in the semantic summary.

**Final disposition:** **FIXED and verified.**

---

## Touch-target sizing on semantic-list module cards — investigated, no defect found

**Claim challenged:** none directly (self-initiated check under the accessibility
audit's touch-target requirement, ≥44×44).

**Evidence:** A DOM computed-style check (`getComputedStyle(...).minHeight`) showed
the 3 semantic-list module-card `<button>` elements had `min-height: 0px`, unlike the
5 primary view buttons' explicit `44px`. Before treating this as a defect, ran a
follow-up check using `getBoundingClientRect().height` and found the **actual
rendered height is 91.5px** — well above the 44px WCAG minimum — because the button's
multi-line text content (module label, modalities, description, focus-region tag)
naturally pushes it well past that floor regardless of the `min-height` CSS property.

**Final disposition:** **NO DEFECT — false alarm, correctly not corrected.** Adding an
unnecessary `min-height` CSS rule for a problem that does not actually exist would
have violated this task's explicit "do not manufacture code changes to appear
productive" rule.

---

## Pre-existing conditions identified and explicitly NOT corrected (out of Stage 7 scope)

### Evidence-verifier AMBIGUOUS-count discrepancy (8 required AMBIGUOUS entries, exit code 2)

Not a Stage 7 defect. `git log -- scripts/verify_jury_release_evidence.py` shows the
script was last touched at `b9ec0a8` ("docs(audit): record independent stage 4 and 5
verdict"), before the Stage 7 diff (`dec1546`/`c688d54`/`c01f66f`) began.
`git ls-tree -r --name-only 7b077a4 -- frontend/qa-screenshots` confirms 54
pre-existing evidence files already existed at the accepted Stage 4-5 base, and the
AMBIGUOUS entries trace to canonical-selection-policy vs. actual-file-SHA mismatches
among those pre-existing files, unrelated to anything Stage 7 touched. See
`ROUTE_COUNT_RECONCILIATION.md` for the full historical trace. **Out of this audit's
corrective scope** — correcting it would mean rewriting canonical-evidence policy for
unrelated Stage 2-3/4-5 artifacts, which this task's rules do not authorize.

### React hydration-mismatch warning (`className="dark"` → `"dark reduce-motion"`)

Not a Stage 7 regression. Caused by a pre-hydration boot `<script>` in the shared root
`app/layout.tsx` that synchronously mutates `document.documentElement.className`
before React hydrates. Independently reproduced identically on `/mission-overview`
(a route Stage 7 never touched) and `/settings`, confirming it is a pre-existing,
cross-route architectural tradeoff, not something introduced by the Stage 7 diff.
**Out of corrective scope** — fixing it would mean redesigning the shared reduced-motion
boot script used by every route in the app, well beyond Stage 7's boundary.

### `THREE.Clock` deprecation warning

Investigated and confirmed to originate from the pinned `three`/`@react-three/fiber`
dependency versions, not project code (`git grep` found no `THREE.Clock` reference in
`frontend/src`). Does not affect correctness. No dependency upgrade was performed
(risk of destabilizing the accepted Stage 4-5 baseline for a cosmetic warning is not
justified by this task's scope). **Accepted as a low-severity upstream limitation.**

---

## Summary

| Severity | Count | Disposition |
|---|---|---|
| CRITICAL | 0 | — |
| HIGH | 1 (S7-AUDIT-02) | Fixed, regression-tested, browser-retested |
| MEDIUM | 1 (S7-AUDIT-01) | Fixed, regression-tested, browser-retested |
| LOW | 0 | — |
| INFORMATIONAL | 3 (touch-target false-alarm, evidence-verifier pre-existing, hydration-warning pre-existing) | No code change — either no defect, or genuinely out of scope |

No finding remains unfixed that was within this audit's authority to fix. No test was
weakened and no acceptance criterion was redefined to obtain a pass.
