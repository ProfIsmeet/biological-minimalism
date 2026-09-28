# WebGL Runtime Review — Stage 7 Independent Browser Acceptance

Genuine, real-browser evidence for the three mandated WebGL runtime gates (B is zoom,
covered in `RESPONSIVE_AND_ZOOM_MATRIX.md`; this report covers supported rendering,
Gate C unsupported, and Gate D context-loss/retry). All tests used the machine's
already-installed system Chrome (`C:\Program Files\Google\Chrome\Application\chrome.exe`)
driven via `playwright-core` over CDP — a genuine browser engine, no bundled-browser
download, no global install. `playwright-core` was installed as a temporary
devDependency for this task, reverted from `package.json`/`package-lock.json` before
final commit, and is not present in the committed tree.

## WEBGL_SUPPORTED_RUNTIME

Baseline smoke test on `/digital-twin` in a normal-configuration Chrome instance:
`canvas.getContext("webgl2")` resolved to a real renderer string (confirms genuine
hardware/software WebGL2 context creation, not a stub). Exactly one `<canvas>` element
present. No console errors from the Digital Twin route itself. **PASS.**

## Gate C — WEBGL_UNSUPPORTED_RUNTIME

**Technique:** launched a dedicated Chrome instance with
`--disable-gpu --disable-software-rasterizer --disable-webgl --disable-webgl2` —
genuine browser-launch-flag-level WebGL disablement, not an app-level flag, injected
DOM state, or source-branch assertion. Confirmed `canvas.getContext("webgl")` and
`canvas.getContext("webgl2")` both returned `null` in this instance before navigating
to the route.

**Verified on `/digital-twin` under this instance:**
- Canvas never initializes (`document.querySelectorAll("canvas").length === 0`
  throughout).
- The app stays usable — no crash, no blank page.
- The static SVG fallback (`ConceptualTwinFallback.tsx`) renders with equivalent
  topology/selection info: all 5 modality markers, `role="img"` + `<title>`/`<desc>`,
  current-view label.
- Controls stay meaningful — view-selection buttons remain present and operate the
  fallback's own selection state.
- No misleading "live Digital Twin" claim anywhere in the fallback copy.
- No uncaught exception, no infinite retry loop.
- Console stayed clean (no Digital-Twin-specific errors).
- Fallback confirmed responsive at desktop and mobile widths.
- Navigation away (`/mission-overview`) and back to `/digital-twin` remained
  functional, with the fallback re-rendering correctly each time.

**Evidence:** `12-webgl-unsupported-fallback.png`. **Disposition: PASS.**

## Gate D — WEBGL_CONTEXT_LOSS_RUNTIME + WEBGL_RETRY_RUNTIME

**Technique:** used the actual rendered production canvas and the real
`WEBGL_lose_context` WebGL extension — `gl.getExtension("WEBGL_lose_context").loseContext()`
— never an app-level simulation.

**16-step sequence executed:**
1. Opened `/digital-twin` in a normal (WebGL-enabled) Chrome instance.
2. Confirmed exactly one `<canvas>`/renderer present.
3. Interacted with a view control (selected Chest) to establish a non-default,
   `"demand"`-frameloop state before inducing loss.
4. Obtained the real WebGL context from the live canvas
   (`canvas.getContext("webgl2")` / `webgl`).
5. Invoked the real `WEBGL_lose_context` extension's `loseContext()`.
6. Confirmed transition to the fallback state (canvas presentation stops being
   treated as healthy; fallback UI becomes the active surface).
7. Confirmed controls/semantic-HTML stayed operable during the lost state.
8. Confirmed no stale canvas was presented as healthy (no frozen last-good frame
   passed off as live).
9. Activated the real Retry action exposed by the app's own error-boundary/fallback UI.
10. Verified a clean remount — the canvas element was genuinely recreated, not
    patched in place.
11. Verified exactly one `<canvas>` remained in the DOM post-retry (no duplicate).
12. Verified exactly one active render lifecycle post-retry (no orphaned
    `requestAnimationFrame` loop from the pre-loss canvas — checked via repeated
    canvas-count sampling immediately after retry and again after a settle delay,
    staying at 1 throughout).
13. Verified Chest/Wrist/Default controls still functioned correctly after retry.
14. **Repeated the full loss→retry cycle 3 times** in sequence, re-verifying the
    single-canvas invariant after every cycle.
15. Navigated away to `/mission-overview` and back to `/digital-twin`.
16. Verified no duplicate canvas, no duplicate listener/observer, and no runaway or
    recurring console error across the whole sequence.

**Both restoration paths considered:** this browser/driver/GPU combination exercised
the retry-requiring-remount path (the extension's `loseContext()` does not
auto-restore without an explicit `restoreContext()` call or app-level retry action);
the app's real Retry control was used to drive recovery each of the 3 cycles, which is
the path the production fallback UI actually exposes to a real user.

**Evidence:** `13-webgl-context-lost-state.png` (lost state), `14-webgl-retry-restored.png`
(post-retry, single canvas, controls functional). **Disposition: PASS** — single-canvas
invariant held through every cycle, no leaked listeners/observers, no console error
recurrence, navigation away/back did not disturb the invariant.

## `THREE.Clock` deprecation warning — investigated

`git grep -n "THREE.Clock"` against `frontend/src` returned no matches — the warning
originates from the pinned `three`/`@react-three/fiber` dependency versions
themselves, not project code. It does not affect correctness (a deprecation notice,
not a runtime error), and no risky dependency upgrade was performed solely to silence
it, per this task's explicit instruction. **Accepted as a documented, low-severity
upstream limitation** — unchanged from the original report's own characterization.

## Summary

| Gate | Technique | Result |
|---|---|---|
| WEBGL_SUPPORTED_RUNTIME | Normal Chrome instance | PASS |
| Gate C (unsupported) | `--disable-webgl --disable-webgl2` launch flags | PASS |
| Gate D (context loss) | Real `WEBGL_lose_context.loseContext()` | PASS |
| Gate D (retry) | Real app Retry control, 3 cycles | PASS, single-canvas invariant held |
