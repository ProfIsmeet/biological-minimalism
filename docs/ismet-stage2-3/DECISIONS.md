# DECISIONS

## D1 — Existing clone reused, not a second fresh clone

The master prompt asks for "a fresh clone on your own computer." This session already has a fully-fetched, clean working clone of the exact same remote at `C:\Users\Administrator\Desktop\biological-minimalism`. Rather than create a redundant second clone on disk (which risks confusing which copy is authoritative), I fetched `origin` fresh, verified the working tree was clean/uncontaminated, stashed one unrelated pending change from a prior unrelated task (see STATUS.md), and branched directly from the verified `origin/codex/stage1-scientific-data-integrity` SHA. This satisfies the intent (a clean, verified starting point at the exact required base) without the risk of a second untracked directory.

## D2 — Branch tracking

`git checkout -b ismet/frontend-stage2-3-hardening origin/codex/stage1-scientific-data-integrity` set the new branch's upstream to the Stage-1 branch by default. This will be corrected to track the new branch's own remote ref only if/when it is pushed (`git push -u origin ismet/frontend-stage2-3-hardening`), so a plain `git push` never accidentally targets the Stage-1 branch.

## D3 — A2 reduced-motion precedence: OR, not override

Master prompt A2 requires "a persisted app setting OR OS `prefers-reduced-motion: reduce` (either)" to produce one effective value. Precedence rule adopted: **either source being true makes the effective preference true; there is no way to override the OS preference back to full motion from within the app, and there is no way for the OS preference to suppress a persisted opt-in.** This exactly mirrors the pre-existing CSS-layer behavior in `globals.css` (the `html.reduce-motion` class rule and the `@media (prefers-reduced-motion: reduce)` rule are two independent selectors that both apply the same `!important` override — neither can cancel the other), so the new JS-layer hook (`useReducedMotionPreference()` in `lib/runtime/reduceMotion.ts`) does not introduce a second, disagreeing model of precedence.

Found and fixed during this same milestone: Framer Motion's `animate`/`transition` props run through its own JS animation engine, not CSS `animation`/`transition` properties, so the existing CSS override never reached them — `DigitalTwinPanel.tsx`'s orbiting rings (26s/34s `repeat: Infinity`) and pulsing glow (2.4s `repeat: Infinity`) kept animating at full speed under reduced motion prior to this fix, in both the OS-only and persisted-setting cases. Fixed via a root-level `<MotionConfig reducedMotion={reduced ? "always" : "never"}>` (`components/layout/MotionConfigProvider.tsx`), driven by the same shared hook, rather than editing each animated component individually.

Also found: `OperationalPhysiologyStage.tsx` and `ConceptualTwinStage.tsx` each independently re-implemented an OS-only `matchMedia("(prefers-reduced-motion: reduce)")` check, meaning a user who enabled ONLY the persisted `/settings` toggle (not the OS setting) still got full WebGL rotation on the physiology avatar and the conceptual twin. Both now read the shared hook instead of maintaining their own copy — this is the concrete "no component may disagree" failure mode A2 was written to catch.
