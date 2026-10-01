# Merge recommendation

## Recommendation

**Merge after a browser pass. Do not merge before one.**

Every automated gate passes, the protected work shows no regression, and the
scientific truth locks are now enforced at build time rather than by
inspection. But this branch changed roughly 40 text sizes and roughly 26
control heights without a single rendered page being observed, and that is
precisely the class of change that a test suite cannot validate. The gap is not
a formality — see `RESPONSIVE_ACCEPTANCE_MATRIX.md` for the three specific
places most likely to have broken.

Ten minutes with a browser at 1024x768 and 1280x800 would close it.

## Why the risk is lower than the diff suggests

91 files changed, but the great majority of those lines are two mechanical
token migrations applied uniformly. The substantive behavioural changes are
few, and each is narrow:

| Change | Blast radius |
|---|---|
| `/settings` drops the duplicated source control and the `live-feed` tier | One route. Removes capability rather than adding it; the controls remain where they belong. |
| `/ai-insights` rebuilt source-aware | One route. The panels' own logic was already correct; the route's framing around them was not. |
| `/mission-timeline` gains a chronology | One route, read-only from an existing store. No new provider, socket, or watcher. |
| `/digital-twin` split for metadata | Structural only. The view moved file; its content is byte-identical apart from the export name. |
| Global `:focus-visible` rule | Product-wide, but additive and inside `@layer base`, so every existing opt-out and opt-in still wins. |
| `!important` typography override removed | Product-wide. The riskiest single line, mitigated by the fact that all ~400 affected call sites were rewritten to their real sizes first. |

Nothing in the backend, the ML layer, or the datasets was touched. No model
constant, scientific constant, evidence-selection rule, or dataset/checkpoint
path changed.

## Merge risks, honestly ranked

1. **Unobserved layout regression.** The real risk. Raising type and control
   sizes makes content wider and taller, and three surfaces are tight enough to
   care. Mitigation: look at them.
2. **Focus ring contrast on the darkest surfaces.** `#A1D2CC` was already in
   use on ~20 controls, so it is not a new colour — but it now also applies to
   the ~40 controls that previously showed the user-agent ring, including some
   on `surface-3` and over the `#061A26` WebGL stage. Unmeasured.
3. **`DigitalTwinPanel` deletion.** Low. It had no importers. If some future
   branch expected it, that branch wanted a `% Adapted` readout and should be
   stopped by the guard rather than accommodated.
4. **Guard false negatives.** Six findings were self-inflicted guard failures.
   The guards are stronger now, but "the suite is green" means less here than
   it would if no guard in it had ever reported clean over a real violation.
   `INDEPENDENT_REVIEW_ENTRYPOINT.md` explains how to test one.
5. **The six rewritten `C-01` assertions.** They previously asserted that a
   stylesheet papered over sub-12px classes; they now assert the classes do not
   exist. I consider that strictly stronger, but a reviewer who disagrees should
   look at that diff specifically, since it is the one place where existing
   assertions changed meaning rather than being added to.

## Conflict exposure

The branch is based directly on `dc2039d` with no merge or rebase, and does not
touch `main`, the source branch, or the Furkan presentation snapshot. Conflicts
would be expected only against another branch doing its own palette or
typography migration over the same component files — the mechanical changes are
wide, so a competing wide change would conflict heavily. The substantive files
(`RouteHeader`, `timelinePresentation`, `AIInsightsClient`, `DigitalTwinClient`,
`verify-rendered-routes`) are new and cannot conflict.

## Suggested sequence

1. Bring the stack up per `INDEPENDENT_REVIEW_ENTRYPOINT.md`.
2. Run the five gates. Expect clean, 1327/1327, 146/146.
3. Check the three high-risk surfaces at 1024x768 and 1280x800.
4. Confirm the protected Mission Overview and Stage 7 surfaces still look
   right, not merely assert right.
5. Tab through `/live-monitoring` and open both modals by keyboard.
6. Merge, or report the layout findings — which, if any exist, should be fixed
   by giving content room rather than by reverting a type size.

## What should not be merged as-is

Nothing in this branch is knowingly incomplete. The deliverable that is
genuinely missing is the screenshot evidence package, and it is missing because
no browser existed — not because it was skipped. If the receiving process
requires that package to exist before merge, this branch cannot satisfy that
requirement in this environment and someone with a browser must produce it.
