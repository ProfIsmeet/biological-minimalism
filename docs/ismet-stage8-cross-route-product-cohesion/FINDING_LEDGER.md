# Finding ledger

Every finding, with severity, how it was found, and its disposition. Findings
marked **self-inflicted** were introduced by my own earlier Stage 8 work and
caught by my own later checks. They are listed with the rest rather than
quietly corrected, because a reviewer needs to know which guards have already
proven they can fail.

## Critical

None found.

## High

**H-1 — `/settings` could mutate the confirmed source from a preferences page.**
Settings mounted the operational data-source control: synthetic/replay source
switching plus subject selection, duplicating the Demo controls drawer the
operational routes own. Two independent owners of the confirmed source, one of
which displayed none of the resulting state. *Found:* §15 route audit.
*Fixed:* control removed, not restyled. The route dropped from the `live-feed`
runtime tier to `static`.

**H-2 — dead `DigitalTwinPanel` was a ready-to-mount §7.4 violation.**
It rendered `overall_adaptation` as a large "% Overall Adaptation" readout plus
per-system percentage scores. *Found:* adaptation-score sweep. *Fixed:*
deleted, with a guard asserting the file does not return.

**H-3 — `/ai-insights` drew an empty 0-100% confidence axis during replay.**
An empty axis reads as a measured zero, not as "this quantity does not exist
for this source". *Found:* §13 audit under replay. *Fixed:* explanatory prose
replaces the chart; titles are source-conditional; synthetic output is labelled
synthetic.

**H-4 — `/mission-timeline` showed no chronology at all.** A route named for a
timeline displayed only four conceptual day markers, which a reader could
reasonably take for recorded mission events. *Found:* §14 audit. *Fixed:* a
real session event chronology, with every event declaring its origin and every
timestamp declaring which clock it is measured on.

**H-5 — four routes had no metadata of their own.** `/digital-twin` exported
none at all (a client component cannot export `metadata`), and
`/mission-overview`, `/mission-timeline` and `/settings` had a title but no
description. All four silently inherited the layout's generic defaults.
*Found:* `verify-rendered-routes.mjs`, after every source-level check had
missed them. *Fixed:* `/digital-twin` split into a server shell plus client;
descriptions added to the other three.

**H-6 (self-inflicted) — my own palette guard reported clean while 528
violations remained.** The first Stage 8 pass retired `slate-*` and `space-*`,
and the guard checked for exactly those two families — so it passed while cyan,
amber, emerald, rose, violet and alpha-over-white survived across 20 files,
concentrated in the research archive tree. *Found:* inspecting control
classNames for an unrelated reason. *Fixed:* all 528 migrated on meaning; the
guard broadened to the whole default palette.

## Medium

**M-1 — the operational demo controls were the smallest targets in the
product.** Replay load/pause/step, fault apply/clear, source switch, playback
speed, and the severity/seed number inputs: all roughly 28-32px tall at 12px
text. These are the controls a presenter drives live. *Fixed:* 44px minimum,
14px text, padding preserved.

**M-2 — playback-speed selection was indicated by colour alone**, with no
non-colour signal and no programmatic selected state. *Fixed:* `aria-pressed`
plus a weight change.

**M-3 — focus indication had no single definition.** Roughly 20 controls
hard-coded `outline-[#A1D2CC]`, four used `ring-final-accent`, and about 40
more declared nothing and fell back to the user-agent ring, which on this dark
canvas is low-contrast and unrelated to the rest of the system. A keyboard
user's indicator depended on which stage the control they reached was written
in. *Fixed:* one global `:focus-visible` rule in `@layer base`, reading a new
`focus-ring` token set to the value already in use — so unifying introduced no
second focus colour.

**M-4 — an `!important` rule made the source lie about type sizes.**
`globals.css` force-mapped `.text-[9px]` through `.text-[11px]` to 12px. It
held the floor at runtime, but a component said 9px and rendered 12px, every
newly added sub-12px class was swallowed silently, and `!important` blocked any
legitimate exception. *Fixed:* override removed; the floor is now held in the
source and enforced by a tree-wide guard that fails the build.

**M-5 — the `/settings` reduce-motion switch was a 24px hit target.** *Fixed:*
the 24px track now sits inside a 44px focusable button, so the accessible
target meets the minimum with no change to the control's visual weight.

**M-6 — the `SensorConstellation` hub held two all-caps labels at 9px and
10px** inside a 56px circle. Both cannot fit at 12px, and §9.1 forbids
shrinking text to fit. *Fixed:* the hub keeps the source kind in sentence case
(narrower than all-caps at the same size); the connection state moved to the
caption below, where it has the full panel width and now names itself in words
as well as colour. The circle's size and position are unchanged, so the orbit
geometry is untouched.

**M-7 — `FaultRecoveryTimeline` rendered "SIMULATED" at 10px on
`ink-disabled`** — the smallest, lowest-contrast text in the row, despite being
the fact that decides how the row may be read. *Fixed:* at the floor, on the
warning token: a qualifier rather than de-emphasis.

**M-8 — `/settings` rendered a live CONNECTED/CONNECTING transport badge**,
claiming a connection state on a page that shows no telemetry. *Fixed:* a
static APPLICATION PREFERENCES scope badge.

**M-9 — the `ExplanationPanel` refresh button was enabled during replay**
though `load()` early-returns for that source, so pressing it did nothing and
said nothing. *Fixed:* genuinely disabled, with the reason in both the
accessible name and the tooltip.

**M-10 — a synthetic-only circadian `TrendPanel` on `/mission-timeline`** drew
an empty 0-100 chart in replay: the same missing-reads-as-zero defect as H-3.
*Fixed:* removed from that route.

**M-11 — five routes used three different page-title scales**, two of them
reaching 34px, outside the §9.1 24-30px band, with no rule distinguishing them.
*Fixed:* shared `RouteHeader`.

**M-12 — `Sidebar` rendered its first-read text in the least legible treatment
available:** 10-11px all-caps at wide tracking, with group labels on
`ink-disabled`. Nav rows were 40px. The brand block carried a `max-h-[72px]`
clamp that truncated the wordmark once its text grew. *Fixed:* 12px sentence
case, 44px rows, the active row distinguished by weight plus a 3px leading rule
rather than a background difference alone, clamp removed, decorative icons
`aria-hidden` so a screen reader reads each row once.

## Low

**L-1 (self-inflicted)** — a private-path guard pattern matched the word run
"PageDown/Space/Home/End" inside a keyboard-handling comment. Anchored to a
real path shape.

**L-2 (self-inflicted)** — an alpha-palette pattern ended in a word boundary
after `]`, which can never match, so every `bg-white/[0.02]` slipped through
silently. Fixed, with the reason recorded at the guard.

**L-3 (self-inflicted)** — the copy-level §7 guards were not negation-aware and
flagged five of the disclaimers §7 *requires*, such as "There is no
reference/ground-truth HR channel". Made negation-aware over a plus-or-minus
one line window, because wrapped comments and JSX routinely split a sentence
across lines.

**L-4 (self-inflicted)** — the hit-target guard flagged eight non-interactive
elements: a status paragraph, badge spans, layout divs. Narrowed to require an
interactive opening tag within six lines of the className.

**L-5** — `.text-shadow-glow` had zero consumers. Removed.

**L-6** — the shared Panel was glassmorphic (translucent fill, backdrop blur,
drop shadow), which is why legacy routes read as a stack of floating cards
rather than one authored document. Flattened onto surface tokens with a real
border.

## Correction to my own earlier claim

An earlier commit message on this branch (`88f32a4`) described the sub-12px
codemod as fixing text that was rendering "below the essential-text floor".
That was wrong. The `!important` rule in `globals.css` was already promoting
those classes to 12px at runtime, so the rendered sizes were already at the
floor. The codemod's real value was making the source state what it actually
rendered; removing the override is what turned the floor into a build-time
guarantee instead of a silent runtime patch. The correction is recorded in
commit `4a8a629` and here, rather than left standing.
