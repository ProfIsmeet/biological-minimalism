# Prompt 4/4A Dossier — Accessibility Hardening Evidence

This dossier records the accessibility-hardening behavioral evidence
gathered in this session, closing the specific runtime gaps the prior
Codex independent audit (`docs/codex-reviews/STAGE2_3_INDEPENDENT_ACCEPTANCE.md`)
left open due to lacking media-feature emulation.

## Reduced-motion (Prompt 4A HIGH-1 lineage)

Full 14-scenario matrix executed with genuine `matchMedia` emulation
(injected via `navigate_page` `initScript`, executed before hydration —
functionally equivalent to `Emulation.setEmulatedMedia` from the page's own
point of view). Full detail and per-scenario results: `../AUDIT.md` section 5.

Headline results:
- Effective contract confirmed as `OS reduce OR app reduce` via a full
  truth table (00/01/10/11 combinations), including the specific invariant
  that removing one input cannot re-enable motion while the other remains
  active.
- Cross-tab sync confirmed with a genuine second browser tab and the
  native `storage` event (not simulated).
- User pause/play intent confirmed to survive reduced-motion toggles in
  both directions (regression guard for the prior M-02 defect).
- No full-motion hydration flash on reload with a persisted setting,
  confirmed both structurally (synchronous pre-hydration boot script in
  `app/layout.tsx`) and behaviorally (class + frozen angle present at first
  measurement).

## Modal dialog focus containment (Prompt 4 section 10 / 4A MEDIUM-1 lineage)

Both dialogs (`MobileNav`'s "More" sheet, `DemoControlDrawer`) re-verified
with real Tab/Shift+Tab/Escape key events and real accessibility-tree
snapshots: correct initial focus, correct forward/reverse wrap, correct
background `inert`+`aria-hidden`, correct scroll lock and its cleanup,
correct focus restoration to the trigger. Full detail: `../AUDIT.md`
section 6.

## WebGL failure fallback (Prompt A4 lineage)

Unsupported-path and context-loss/retry paths re-verified with a genuine
`getContext` override and a genuine `WEBGL_lose_context` extension call
(not source-string assertions). Confirmed the "recovery offered only when
technically possible" rule holds (no retry control on the hard-unsupported
path). Full detail: `../AUDIT.md` section 6.

## 200% zoom

Verified no horizontal overflow at `document.documentElement.style.zoom = 2`
on a 1280x800 viewport; screenshot in `../mission-overview-200-zoom-accessibility.png`.

## What this dossier does not claim

It does not claim actual screen-reader verification (explicitly deferred
this session, see `../AUDIT.md` section 9) and does not claim Docker or
real-S14 evidence (see Stage 3A/3B sections of `../AUDIT.md`).
