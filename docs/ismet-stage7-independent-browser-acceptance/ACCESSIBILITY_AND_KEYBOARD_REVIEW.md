# Accessibility & Keyboard Review — Stage 7 Independent Browser Acceptance

`ACTUAL_SCREEN_READER_STATUS: DEFERRED_BY_OWNER_UNTIL_STAGE9`. Per this task's
explicit scope, macOS VoiceOver was **not run**, and no OS accessibility settings were
altered. This review covers browser accessibility-tree inspection, semantic-HTML
inspection, keyboard-only interaction, focus-order/visible-focus review, and
touch-target review — genuine DOM/keyboard testing, not a substitute for a real
screen-reader pass.

## Keyboard interaction — tested against the final corrected implementation

Confirmed via source read of `ConceptualTwinStage.tsx`'s `onStageKeyDown` handler and
`digitalTwinViewForKey()` (`digitalTwinPresentation.ts`, unmodified by this audit's
corrections) plus live browser interaction:

- `1`/`2`/`3`/`4` select Front/Back/Chest/Wrist respectively.
- `Escape`, `Home`, and `0` all return to Default.
- All 5 primary view controls (Default/Front/Back/Chest/Wrist) are keyboard-reachable
  in a logical tab order, matching their visual left-to-right presentation.
- Shortcuts do not trigger while typing in an editable control — confirmed no text
  input exists on this route that would need to suppress them, and the handler is
  scoped to the stage container, not `document`-global, which structurally prevents
  the shortcut-while-typing-elsewhere failure mode by construction.
- Space does not trigger unexpected page scroll when acting as the Pause/Resume
  rotation command — the control is a real `<button>`, so Space activates it via the
  browser's native button-activation semantics rather than a custom keydown handler
  that would need to separately call `preventDefault()`.
- No keyboard trap: Tab/Shift+Tab move through all controls and out of the region
  normally; confirmed by traversing the full control set without getting stuck.
- No pointer/scroll trap: mouse wheel and click interaction outside the 3D canvas
  behave normally (canvas is not `pointer-events: none`-hijacking navigation).

**Evidence:** `10-keyboard-focus-first-view-control.png` shows a visible focus ring on
the first control after Tab from page load.

## Accessible names, pressed/selected states

DOM inspection (`getAttribute("aria-pressed")`, `.textContent`) confirmed:
- The 5 primary view buttons expose `aria-pressed` reflecting the current selection,
  updating correctly on click and on keyboard shortcut activation.
- The 3 semantic-list module cards (Chest/Wrist/Frontal) expose accurate accessible
  names combining module label + modalities + focus-region state.
- Button labels change appropriately with state ("Pause rotation" ↔ "Resume rotation"
  ↔ "Rotation paused" when reduced motion is active and the control is disabled).

## Touch-target sizing

See `FINDING_LEDGER.md` — investigated and found **no defect**: the 3 semantic-list
module cards have `getBoundingClientRect().height` of 91.5px (well above the 44×44
WCAG minimum) due to their natural multi-line text content, despite a computed
`min-height: 0px` in the stylesheet. The 5 primary view buttons have an explicit 44px
`min-height`. No correction was needed or made.

## Semantic HTML / canvas-alternative

- The "Semantic architecture summary" (`aria-live="polite"`) block exposes current
  view, selected region, and per-modality descriptions in real DOM text — the canvas
  is not the sole carrier of this information.
- `ConceptualTwinFallback.tsx` (the WebGL-unsupported/context-lost fallback) is itself
  fully accessible: `role="img"` with `<title>`/`<desc>`, all 5 modality markers
  present as real DOM elements, current-view label, conditional Retry button —
  confirmed reachable and legible with WebGL genuinely disabled (see
  `WEBGL_RUNTIME_REVIEW.md` Gate C).
- No announcement storm observed: the `aria-live="polite"` region updates once per
  view change, not continuously — confirmed no ticking/continuously-changing value is
  placed inside it (this is also independently enforced by the pre-existing
  `verify-live-region-boundaries.mjs` structural guard, which passed).

## Accessibility-tree inspection — method note

`playwright-core`'s `page.accessibility.snapshot()` API was not exposed in the
installed version (`1.63.0`); accessibility-tree-equivalent facts (roles, names,
pressed/checked states, computed geometry) were instead verified via direct DOM/
`getComputedStyle`/`getBoundingClientRect` queries through `page.evaluate` — a valid
alternative that inspects the same underlying facts a real accessibility tree would
expose, though it is not a literal accessibility-tree dump. This is disclosed
explicitly rather than silently substituted.

## Summary

| Check | Method | Result |
|---|---|---|
| Keyboard shortcuts (1/2/3/4/Home/Escape/0) | Live keyboard interaction | PASS |
| Focus order / visible focus | Live Tab traversal, screenshot | PASS |
| No keyboard trap | Live Tab/Shift+Tab traversal | PASS |
| Accessible names / pressed states | DOM inspection | PASS |
| Touch targets ≥44×44 | `getBoundingClientRect()` | PASS (investigated a false alarm, no defect) |
| Canvas-alternative semantic HTML | DOM + live-region inspection | PASS |
| Screen reader (VoiceOver) | — | DEFERRED_BY_OWNER_UNTIL_STAGE9, not run, not claimed |

**KEYBOARD_ACCEPTANCE: PASS. ACCESSIBILITY_TREE_REVIEW: PASS** (DOM-equivalent method,
disclosed). Accessibility is **not** claimed as fully screen-reader-verified.
