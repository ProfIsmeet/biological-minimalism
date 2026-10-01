# Typography and visual system audit

## The §9.1 scale, and where it now lives

| Role | Required | Owner |
|---|---|---|
| Essential text floor | never below 12px | tree-wide guard (build-time) |
| Navigation | 14px | `Sidebar`, `MobileNav` |
| Page title | 24-30px | shared `RouteHeader` (24px, 28px at `sm`) |
| Section title | 20-24px | per route, `text-xl` |
| Component title | 16-18px | shared `Panel` |
| Body | 13-15px | `text-sm` |
| Table body | >= 12px | `text-xs` minimum |
| Status pill | >= 12px | `text-xs` minimum |
| Axis labels | >= 12px | `ChartFrame`, chart components |
| Captions | >= 12px | `text-xs` minimum |

## The floor: what was actually wrong

This needs stating precisely, because my own first description of it was wrong.

`globals.css` contained a Stage 4 rule that force-mapped `.text-[9px]`,
`.text-[9.5px]`, `.text-[10px]`, `.text-[10.5px]` and `.text-[11px]` to
`font-size: 0.75rem !important`. So the ~400 sub-12px classes in the source
were **already rendering at 12px**. The rendered floor was not broken.

What was broken was the mechanism:

- the source said 9px and rendered 12px, so no reviewer reading the JSX could
  tell what would actually appear;
- any newly added sub-12px class was swallowed silently, so the problem could
  keep growing invisibly and no one would see it;
- `!important` meant a component that legitimately needed a different size
  could not have one.

Both halves were therefore done: every call site now states its real size, and
the override is gone. The floor is enforced by a guard that walks the whole
tree and **fails the build**, naming the offending file. A build-time failure
beats a silent runtime patch.

Counts: ~367 classes rewritten in the first pass, 33 more in the Mission
Overview operations components and Stage 7 avatar overlays (initially excluded
as protected areas, then included once it was clear that a font size changes no
plotted value, ring sweep, radar semantic, or anatomical joint).

Two sites needed more than a size change, because §9.1 forbids shrinking text
to resolve overflow and the converse is to give the text room:

- **`SensorConstellation` hub** — two all-caps labels at 9px and 10px in a 56px
  circle. Both cannot fit at 12px. The hub keeps the source kind in sentence
  case; the connection state moved to the caption, gaining full panel width and
  a word-plus-colour treatment. Circle geometry untouched.
- **`FaultRecoveryTimeline` "SIMULATED"** — 10px on `ink-disabled`, the
  smallest and lowest-contrast text in the row, despite being the fact that
  decides how the row may be read. Now at the floor on the warning token.

## Palette: two passes, and why the first was incomplete

**Pass 1** retired `slate-*` and `space-*`: 470 occurrences. `tailwind.config.ts`
had documented these as coexisting with the semantic tokens pending migration;
Stage 8 finished it.

**Pass 2** was only run because a guard failure elsewhere exposed that pass 1
had stopped too early. 528 further occurrences of the **raw default Tailwind
palette** survived — `cyan`, `amber`, `emerald`, `rose`, `violet`, and alpha
layered over `white`/`black` — across 20 files, concentrated in
`components/research/*` (the archive tree reachable through the collapsed
disclosure on `/research/experimental`) and `DataSourceControl`. These bypass
the token system exactly as `slate-*` did: the same meaning expressed two ways,
so a token change still could not be trusted to propagate.

My own guard had reported clean throughout, because it checked for exactly the
two families pass 1 had handled. That is recorded as finding H-6.

Migration was by **meaning**, not nearest hue:

| Legacy family | Token | Why |
|---|---|---|
| `cyan`, `teal` | `final-accent` | cyan was the pre-token accent |
| `emerald`, `green`, `lime` | `jury-success` | success/nominal |
| `amber`, `yellow`, `orange` | `jury-warning` | warning/caution |
| `rose`, `red`, `pink`, `fuchsia` | `jury-fault` | fault |
| `violet`, `indigo`, `purple`, `blue`, `sky` | `information` | informational |
| `gray`, `zinc`, `neutral`, `stone` | `ink-*` / surface / border | neutral |
| `bg-white/α` | `surface-2` | the surface it stood in for |
| `border-white/α` | `jury-border-subtle` (α<=0.12) or `-strong` | hairline vs. heavier |

Zero raw-palette utilities remain. The guard now covers the whole default
palette plus the alpha forms.

## Visual system

**Glassmorphism removed from the shared Panel.** `.mission-panel` layered a
translucent fill, a backdrop blur and a drop shadow — the reason legacy routes
read as a stack of floating cards rather than one authored document. It is now
a flat `surface-1` with a real `jury-border-subtle` border and a 10px radius.
Because every Panel consumer inherits this, one change de-glassed the whole
product.

**`.text-shadow-glow` deleted** — zero consumers.

**Focus ring unified.** See `ACCESSIBILITY_LEDGER.md`; the typography-relevant
part is that `#A1D2CC` was promoted from a hex repeated at ~20 call sites to a
named `focus-ring` token, so the product has one focus colour with one
definition.

## Page titles

Five routes used three different scales with no rule distinguishing them, two
of them reaching 34px — outside the band. The shared `RouteHeader` now owns
eyebrow, title, lede, an optional quieter caveat, and an optional boundary
badge, with the eyebrow tone chosen by what the route *is* (`accent` for
operational, `information` for system reference, `experimental` for
experimental evidence) rather than for variety.

**Two display heroes were deliberately left out.** `JuryHero`
(`/system-brief`, 38px rising to 56px) and `ExperimentalHero`
(`/research/experimental`, 34px rising to 44px) are presentation openings for a
walkthrough, not page headers for a workspace: they carry their own display
type, their own scope labels, and in `JuryHero`'s case a numeric identity
block. §17 asks for shared primitives where they remove real inconsistency and
warns against flattening real distinctions — forcing the heroes in would have
done the latter, and would have shrunk the submission's opening statement from
56px to 28px for no legibility gain. The exclusion is named explicitly in
`RouteHeader.tsx` and in the guard, not left implicit.

The ceiling guard was tested against known violations before being accepted:
it matches the exact 34px title this stage removed, matches `text-3xl`, matches
the 56px hero, and does not match the canonical 24/28 scale or a large
non-title number.

## Unverified

No rendered measurement of any kind was possible — no measured contrast ratio,
no detected overflow, no confirmation that a raised size did not wrap badly.
See `RESPONSIVE_ACCEPTANCE_MATRIX.md` for the three changes most likely to have
caused a layout regression.
