# Accessibility ledger

## What is claimed, and what is not

**Claimed:** structural and source-level properties, each backed by an
assertion that fails the build.

**Not claimed:** VoiceOver acceptance. Genuine 200% zoom acceptance. Any
measured contrast ratio. Any real keyboard traversal. No browser was available
(see `RESPONSIVE_ACCEPTANCE_MATRIX.md`), so nothing requiring a rendered page
or a real interaction was verified. `min-h-11` in the source is evidence about
a hit target; it is not a measurement of one.

## Focus visibility

Before: focus was declared ad hoc in three different ways. ~20 controls
hard-coded `outline-[#A1D2CC]`. Four used `ring-final-accent`. About 40 more
interactive elements across the routes declared nothing and fell back to the
user-agent default ring, which on this dark canvas is both low-contrast and
visually unrelated to the rest of the system. A keyboard user's indicator
depended on which stage the control they happened to reach was written in.

After: one global `:focus-visible` rule gives every interactive element the
same ring.

Three details that make it correct rather than merely present:

1. **It introduces no new colour.** `#A1D2CC` is the value ~20 controls had
   already settled on. It is promoted to a named `focus-ring` token, the global
   rule reads it via `theme()`, and every call site now names the token. So the
   product has one focus colour with one definition — unifying did not create a
   second convention competing with the existing one.
2. **It is emitted inside `@layer base`,** so Tailwind utilities still win.
   `outline-none` on the three programmatically focused containers (the main
   landmark, the mobile sheet, the demo drawer) keeps suppressing the ring, and
   any component opting into a stronger treatment keeps it. Declared outside
   the layer, the rule would have overridden both and put a ring on every modal
   container opened by keyboard.
3. **`:focus-visible`, not `:focus`,** so a mouse press leaves no ring behind.

Focus **geometry** was deliberately left alone where a component chose it: the
round constellation and avatar-anchor targets keep their ring rather than an
outline, and `ConceptualTwinStage`'s canvas focus behaviour is Stage 7
protected, so only its hard-coded hex changed. Colour unified; behaviour
untouched.

## Hit targets

| Control | Before | After |
|---|---|---|
| Sidebar nav rows | 40px | 44px |
| `/settings` reduce-motion switch | 24px | 24px track inside a 44px button |
| Replay load / switch-to-synthetic | ~32px | 44px |
| Replay pause / step / resume | ~28px | 44px |
| Playback speed buttons | ~28px | 44px |
| Fault apply / clear | ~28px | 44px |
| Fault severity / seed inputs | ~30px | 44px |
| Source-strip retry | ~28px | 44px |
| `DataStateError` retry | ~28px | 44px |
| `ExplanationPanel` refresh | 44px | unchanged |

The reduce-motion switch is the case worth describing: rather than enlarging
the toggle and changing how the control looks, the 24px visual track now sits
inside a 44px focusable button. The accessible target meets the minimum with no
change to the control's visual weight.

Guarded: every `button`/`select`/`input`/`a`/`summary` in the five control
files that sets a short vertical padding must also set the 44px floor, so a new
control cannot be added at 28px. The guard was narrowed after it flagged eight
non-interactive elements — a badge is allowed to be short.

## Colour is never the only signal

Three places relied on colour alone and no longer do:

1. **Playback-speed selection** — active speed was border-and-text colour only,
   with no programmatic state either. Now carries `aria-pressed` plus a weight
   change.
2. **Sidebar active row** — was a background-colour difference. Now weight plus
   a 3px leading rule as well.
3. **`SensorConstellation` connection state** — was a small green/red word
   inside the hub. Now reads "Source connected" / "Source not connected" in the
   caption, so the state is in the words.

Timeline event origins were built this way from the start: each origin renders
its **word** (`Simulated control`, `Source-reported`, `Inference transition`,
`Transport`) as well as its colour.

## Semantics and structure

- **Exactly one `h1` per route**, asserted against delivered HTML for all 10
  routes. The two display heroes own theirs; the other eight use `RouteHeader`
  and declare none of their own.
- **`/mission-timeline` chronology is a real `<table>`** with `<caption>`,
  `scope="col"` headers, and `<tbody>` — not a div grid.
- **Decorative icons are `aria-hidden`**, so a screen reader reads each sidebar
  row once rather than announcing an icon name before it.
- **Modal dialogs** use the shared `useModalDialog()` primitive: Tab trap,
  Escape, scroll lock, background `inert`/`aria-hidden`, focus restoration.
  `MobileNav` and `DemoControlDrawer` both call it, proved by
  `verify-modal-dialog-primitives`. `MobileNav` was audited in full this stage
  and found already correct — `role="dialog"`, `aria-modal`,
  `aria-labelledby`, portalled to body, `min-h-11` targets, and an item order
  matching the desktop rail. Only its group-label contrast and tracking
  changed.
- **Disabled controls say why.** The `ExplanationPanel` refresh button was
  enabled during replay even though its loader early-returns there, so pressing
  it did nothing and explained nothing. It is now genuinely disabled, with the
  reason in both the accessible name and the `title`.
- **Live regions** — `verify-live-region-boundaries` continues to pass: no
  ticking value sits inside an `aria-live`/`role="status"` region, so assistive
  technology is not flooded.

## Reduced motion

Unchanged this stage and still verified by
`verify-reduced-motion-unification`: a single shared
`useReducedMotionPreference()` (persisted setting OR OS query) drives both the
CSS override and `MotionConfig reducedMotion="always"`, so Framer Motion's JS
animation engine is covered as well as CSS transitions. The only edit was to a
stale comment that named the deleted `DigitalTwinPanel` as an example consumer.

## Contrast

Not measured. Two changes should reduce risk and one should be checked:

- Sidebar group labels moved off `ink-disabled` onto `ink-muted`, and the
  subtitle onto `ink-secondary` — both lighter.
- "SIMULATED" moved off `ink-disabled` onto `jury-warning`.
- **To check:** the global focus ring `#A1D2CC` against `surface-3` and against
  the `#061A26` WebGL stage background, which are the darkest and the most
  saturated surfaces it will sit on.
