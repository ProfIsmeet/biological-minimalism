# Evidence Manifest (companion) — Stage 6 Fresh-Session Audit & Closure

Authoritative, machine-readable manifest:
`frontend/qa-screenshots/ismet-stage6-final-audit-closure/EVIDENCE_MANIFEST.json`.

## Identity

- Implementation checkpoint: `bb56853bc3392a3db63a924149ebb2cd83e751ab`.
- Source: `origin/ismet/stage6-scientific-visualization-redesign` @ `82d136ab104211bd3d854e096faca123e95be225`.

## Canonical-selection rule

Every file is unique, captured once against the implementation checkpoint
above. No competing/older evidence set exists in this directory, so every
listed file is CANONICAL; none is SUPERSEDED. Future-collision rule:
latest capture timestamp wins (CANONICAL), older becomes SUPERSEDED; an
unresolvable timestamp collision is AMBIGUOUS and withheld until human
adjudication — mirroring the repository's own evidence-verifier policy.

## What makes this evidence set different from the Stage 6 source's own

The Stage 6 source's evidence directory (`ismet-stage6-scientific-
visualization-redesign`) captured only the **empty state** of the fault/
recovery timeline — genuinely, honestly, because no dataset was available
in that session. This audit's evidence directory captures the **genuinely
populated** state: a real fault applied, sustained, cleared, and recovered
against real S14 replay data and a real trained checkpoint, with the two
CRITICAL defects that made this impossible to render correctly (S6A-FIND-
01, S6A-FIND-02) found and fixed first.

## Coverage vs. the master task's 30-item suggested list

25 files captured. Not captured: `26/27` (200%-zoom-affected route
screenshots — zoom itself is `BLOCKED_EXTERNAL`), `28/29` (native-zoom
proof / zoom-restored-to-100% proof — not applicable since zoom was never
changed from 100%), item `21` (a duplicate of item 20 in the suggested
list numbering — not separately captured). All omissions are disclosed
honestly, none fabricated.

## Filename collisions found and corrected

Two of this audit's own filenames (`*nominal*.png`, `*rebuild*.png`)
collided with pre-existing evidence-verifier glob patterns for unrelated
Stage 2-5 slots. Renamed before commit (content/hash unchanged) — see
`EVIDENCE_VERIFIER_ROOT_CAUSE.md` and the JSON manifest's own
`filename_collision_note` for full detail.

## File index

See the JSON manifest for the full per-file route/viewport/state/SHA-256
table (25 entries). Summary by category:

- **Populated fault/recovery cycle** (7 files): 01–07, culminating in the
  canonical closeup `06-adverse-response-timeline-populated-closeup.png`.
- **Coverage + pipeline** (3 files): 08, 09, 10.
- **HR trend + waveforms** (4 files): 11–14.
- **Research route** (6 files): 15–20.
- **Accessibility/responsive/navigation** (5 files): 22–25, 30.

All 25 SHA-256 hashed (mutually distinct) and visually inspected via
direct image review before commit.
