# Stage 7 Prototype — Asset and License Audit

## Finding

The master prompt assumes an existing CesiumMan-derived GLB asset with provenance/license documentation. Exhaustive search of `origin/claude/stage4-5-visual-command-deck` @ `7afe57114ad6f7537b73f17683f7ecd733606730` found **no such asset, no `public/models/` directory, and no provenance/license documents anywhere in the repository**. The entire human figure on this branch — both the operational avatar and the Digital Twin stage — is built from procedural capsule/sphere geometry (`humanGeometry.ts`, `holographicGeometry.ts`), not an imported mesh.

## Decision: no new binary asset committed

Per the master prompt's own rule ("do not commit a new binary unless it is demonstrably necessary, optimized, licensed, and materially superior") and the git-safety instruction to add no dependency, the Stage 7 prototype **reuses the existing procedural geometry system exclusively** — imported from `humanGeometry.ts` (read-only import, not modified) — rather than sourcing, downloading, or committing any new GLB/FBX/OBJ file.

Rationale:
1. Procedural geometry has zero licensing risk, zero binary weight, and is already proven to work in this exact rendering pipeline (Three.js `capsuleGeometry`/`sphereGeometry`, no loader dependency).
2. The audited weaknesses (F1-F4 in `CURRENT_SYSTEM_AUDIT.md`) are presentation defects — material/lighting/decoration/framing choices — not defects inherent to procedural geometry. A scanned/sculpted mesh would not fix any of them and would introduce a licensing and file-size burden with no offsetting benefit for this prototype's actual goals.
3. Sourcing a new external asset (per the master prompt's own asset-research process: URL, author, license, hash, rights) was considered and explicitly rejected for this iteration — it would require legal/licensing due diligence disproportionate to what a "clearer human figure treatment" needs, when the existing procedural mesh already has an anatomically coherent capsule/sphere topology (confirmed by reading `humanGeometry.ts`'s `JOINTS`/`BODY_SEGMENTS` tables — proportioned head/torso/limb ratios with a documented rationale in the file's own header comment).

## What the prototype changes instead

Only the **material, lighting, and decoration treatment** applied to the existing procedural geometry — never the geometry itself, never a new mesh, never a new dependency. This is documented in full in `PROTOTYPE_DESIGN_SPEC.md`.

## Compliance confirmation

- `NEW_UNVERIFIED_ASSET_COMMITTED: NO` — no binary asset of any kind was added by this branch.
- No dependency was added; `package.json`/`package-lock.json` are untouched (verified via `git diff --stat` in `CHANGE_LEDGER.md`).
- `three`, `@react-three/fiber`, `@react-three/drei` are used at their existing pinned versions only.
