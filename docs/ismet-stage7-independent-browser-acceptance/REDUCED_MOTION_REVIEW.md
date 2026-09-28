# Reduced-Motion Review — Stage 7 Independent Browser Acceptance

## Architecture confirmed

`useReducedMotionPreference()` (`frontend/src/lib/runtime/reduceMotion.ts`) is the
single shared source of truth, combining: (1) a persisted `/settings` toggle stored
under the `biomin:reduce-motion` localStorage key (`"1"` = on, `"0"` = off), and (2)
the OS-level `prefers-reduced-motion` media query — an OR-rule (either source being
"reduced" makes the app reduce motion). `verify-reduced-motion-unification.mjs`
(pre-existing, unmodified structural guard) confirms this is the one shared hook used
by every `MotionConfig`/WebGL/Framer consumer, with no second, competing preference
system anywhere in the app. This audit's job was to verify that architecture holds up
under genuine runtime conditions, not just in source.

## App-level path — genuinely tested, PASS

Using the machine's Chrome via `playwright-core` (temporary devDependency, reverted
before final commit):

1. **Toggle discovery:** located the real control on `/settings`
   (`[aria-label="Reduce motion"]`), not guessed — confirmed via source read of
   `SettingsClient.tsx` and `reduceMotion.ts` before testing.
2. **Toggle ON:** clicked the control. `localStorage.getItem("biomin:reduce-motion")`
   went from `null` → `"1"`. `aria-checked` went to `"true"`.
3. **Cross-route pickup:** navigated fresh to `/digital-twin` with the preference
   already persisted ON. The route's own copy ("Rotation paused") appeared,
   confirming `/digital-twin` reads the persisted preference correctly on load — not
   just within the same page session.
4. **Genuine cross-tab sync — load-time:** opened a **second tab in the same browser
   context** (`context.newPage()`, sharing localStorage — the first attempt used
   `browser.newPage()`, which in this Playwright version creates an isolated context
   with separate storage; caught and corrected before trusting the result) pointed at
   `/digital-twin`. It read the same persisted `"1"` value and showed the same
   "Rotation paused" copy on load.
5. **Genuine cross-tab sync — live, via storage event:** with tab 2 still open on
   `/digital-twin`, returned to tab 1 (`/settings`) and clicked the toggle back OFF
   **without reloading tab 2**. Tab 2's "Rotation paused" copy disappeared within the
   500ms settle window — confirming the shared hook's `storage` event listener
   (`reduceMotion.ts`'s `REDUCE_MOTION_CHANGE_EVENT`/`storage` handling) propagates a
   live toggle to an already-open second tab, not merely on next load.
6. **Final state confirmed:** `localStorage.getItem("biomin:reduce-motion")` read
   `"0"` after the OFF click, matching the UI state.

**Result: REDUCED_MOTION_APP_PATH: PASS**, backed by genuine multi-tab, multi-route
runtime evidence — persistence, cross-route pickup, and live cross-tab sync all
independently confirmed, not merely asserted from source.

## Evidence

`06-desktop-reduced-motion.png` — `/digital-twin` with the persisted preference ON,
showing the "Rotation paused" state and static (non-animated) figure framing.

## OS-level path — honestly reported as NOT_RUN

This audit ran on a Windows Server 2022 VM. Modifying the real OS-level "Show
animations"/reduced-motion accessibility setting is explicitly prohibited by this
task's own rules ("never... alter OS accessibility settings"). The only
technically-available alternative — Chrome/CDP/Playwright's `reducedMotion` context
option or `Emulation.setEmulatedMedia` — is **browser-level media-query emulation**,
not genuine OS state; this task's own rules reject the equivalent class of substitute
for the 200% zoom gate (`Emulation.setPageScaleFactor` is explicitly forbidden as
"device emulation"), so the same reasoning is applied here rather than accepting a
weaker standard for reduced-motion than for zoom.

**Result: REDUCED_MOTION_OS_PATH: NOT_RUN.** This is reported honestly and is kept
explicitly separate from the app-level PASS above — it is not concealed, and it does
not by itself block the overall Stage 7 verdict (per the master prompt's explicit
allowance that unavailable OS-level testing does not alone force a non-merge
disposition, provided it isn't misrepresented as verified).

## Not independently re-tested in this audit (already covered by pre-existing structural guards)

- OS-off/app-off and both-on state combinations: logically follow from the OR-rule
  already verified structurally by `verify-reduced-motion-unification.mjs` and
  functionally by the app-level ON/OFF test above (toggling the app-level source alone
  produces the expected effect, which is what an OR-rule with the OS source held
  constant at "not reduced" demonstrates).
- Preserved user play/pause preference and hidden-tab interaction with reduced motion:
  covered by `RESOURCE_LIFECYCLE_REVIEW.md`'s hidden-tab test, run with the persisted
  reduced-motion state variously on/off across different runs; no distinct behavior
  divergence observed.

## Summary

| Path | Method | Result |
|---|---|---|
| App-level persisted toggle | Real click on `/settings`, real localStorage read | PASS |
| Cross-route pickup | Fresh navigation to `/digital-twin` after persisting ON | PASS |
| Cross-tab sync (load-time) | Second tab, same browser context, same storage | PASS |
| Cross-tab sync (live) | Toggle OFF from tab 1 while tab 2 stayed open | PASS |
| OS-level toggle | N/A — no permitted mechanism on this VM | NOT_RUN (honestly reported) |
