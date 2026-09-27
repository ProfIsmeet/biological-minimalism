# Stage 7 Digital Twin Prototype — Design Specification

## User questions this prototype answers

1. What would a more anatomically legible, less "ghost hologram" treatment of the existing procedural human figure look like?
2. Can sensor/module topology be understood without relying on small in-canvas text or ambient decorative rings?
3. Can region focus (frontal/chest/wrist) be shown clearly without losing anatomical context or implying a measured/affected condition?
4. Does deterministic view switching (front/three-quarter/left/right/back/reset) work better for jury inspection than free-orbit alone?
5. Can the WebGL failure and reduced-motion paths preserve full topology information, not just an inert fallback?

## Explicit non-goals

- No trained Digital Twin, no personalized physiology, no adaptation percentages, no confidence values, no clinical claims — enforced by construction (the prototype never reads or displays a number that isn't a static architecture fact from `lib/architecture.ts`).
- No new sensor modality, no new body region, no invented anchor position — the prototype imports `FINAL_SENSOR_INVENTORY` and `MODALITY_ANCHOR_POSITION` directly rather than redeclaring them.
- No production-route integration, no navigation entry, no shared-store writes, no backend calls.
- No new asset, no new dependency (see `ASSET_AND_LICENSE_AUDIT.md`).
- No replacement of the current `/digital-twin` or Mission Overview experience — this is a parallel, disposable exploration.

## Visual hierarchy

1. Body silhouette (readable at a glance, matte-lit, real shading — not translucent wireframe-only).
2. Depth/form cues (rim light + soft key light, reused color palette from `humanMaterials.ts`: `KEY_LIGHT_COLOR`, `RIM_LIGHT_COLOR`).
3. Region/module orientation (only surfaced on selection, never ambient).
4. Sensor anchors (small, consistent markers, always visible, labelled via an adjacent DOM legend, not in-canvas text).
5. Projector readability (high contrast against a dark neutral stage, no more than one accent color live at a time per selection).

## Human treatment

Reuses `humanGeometry.ts`'s `JOINTS`/`BODY_SEGMENTS`/`computeSegmentTransform` (imported, unmodified) to build the same capsule/sphere mannequin `HumanMannequin.tsx` already builds — the prototype does not reimplement this math, it reimplements only the **material and lighting** applied to it:

- A single opaque `MeshStandardMaterial` primary surface (moderate roughness, low metalness — matte, not glossy/plastic), color close to the existing `bodyMaterial` tone family but tuned slightly lighter for stronger separation against the stage background.
- An optional, low-opacity (≤0.08) surface lattice overlay — subordinate, never the dominant read, and completely omitted (not just dimmed) under the static/2D fallback.
- No emissive glow beyond a faint rim-light-driven edge, no pulsing, no color-cycling.

## Module and sensor encoding

Directly imports and never redeclares:
- `FINAL_SENSOR_INVENTORY`, `MODALITY_COLOR`, `FINAL_MODULES`, `FINAL_ARCHITECTURE_ID` from `@/lib/architecture`.
- `MODALITY_ANCHOR_POSITION`, `REGION_ORBITS` from `@/components/visualization/human/humanLayout`.
- `JOINTS`, `HEAD_RADIUS`, `computeSegmentTransform`, `BODY_SEGMENTS` from `@/components/visualization/human/humanGeometry`.

Each sensor anchor is a small sphere marker colored by its canonical `MODALITY_COLOR`. A DOM-based semantic list (outside the canvas) pairs every anchor with its label, module, and a static conceptual-role sentence sourced from `FINAL_SENSOR_INVENTORY[i].description` — never an invented sentence.

## Interaction model

- **Selection** (module or modality) is local React state only — never written to any shared store, never a network call. Selecting sets `PROTOTYPE SELECTION` labelling explicitly, per the master prompt's scientific-boundary requirement.
- Selecting a modality highlights its anchor and its parent region; selecting a region highlights all anchors belonging to it.
- Region focus draws a subtle outline sphere/box around the region plus a leader line to a DOM label positioned via a screen-space projection of the 3D anchor (a standard, deterministic technique — no physics, no random placement).

## View model

Six deterministic camera presets (front, three-quarter — the existing default angle from `ORTHO_VIEW`, left, right, back, reset-to-three-quarter), each an exact azimuth/elevation pair fed through the existing, imported `orthoCameraPosition()`/`computeOrthographicFit()` functions — no new framing math is invented. No free-drag orbit is implemented in this iteration (deterministic buttons only), which trivially satisfies the "avoid uncontrolled free-orbit" requirement without needing to also build and test a drag-rotate affordance.

## Camera model

Orthographic (parallel) projection, matching the existing system's own documented rationale (`humanLayout.ts`'s comment: deterministic on-screen size independent of distance, no perspective clipping surprises). Frustum computed by the existing, imported `computeOrthographicFit`, called with the prototype's own measured canvas aspect and a fixed height fraction tuned so head-to-feet is always inside frame with margin — verified by direct screenshot inspection, not just by trusting the math.

## Fallback model

Reuses the existing, imported `WebglStage` (unsupported/render-error/context-loss coverage, unmodified) exactly as `PhysiologyAvatar3D.tsx` and `ConceptualTwinStage.tsx` already do. The fallback content itself is new prototype-only code: a simplified flat 2D SVG body outline with the same 5 anchor markers at proportionally equivalent positions, paired with the identical semantic module/modality list the 3D mode shows — so a WebGL failure never removes topology information, only the volumetric rendering.

## Accessibility model

- The canvas gets an `aria-label` summarizing current view + selection state, updated only on genuine state changes (never per-frame).
- The semantic list is fully keyboard-operable (`<button>` elements, native focus, visible focus ring) and fully usable without ever touching the canvas.
- View buttons are native `<button>` elements; current view is indicated via `aria-pressed`, not color alone (also a filled/outlined visual state).
- No live region auto-announces rotation, since there is no autonomous rotation by default (see Reduced-motion model) — this sidesteps the entire class of defect Stage 2 A1 had to fix elsewhere in this repository.
- Real OS screen-reader testing is explicitly deferred per the master prompt's own instruction (`ACTUAL_SCREEN_READER_STATUS: DEFERRED_BY_OWNER_UNTIL_AFTER_STAGE7_INTEGRATION`) — keyboard-only testing is performed instead and is reported accurately.

## Reduced-motion model

Imports the existing shared `useReducedMotionPreference()` hook (unmodified) rather than deriving a private OS-only check. The prototype starts with **zero autonomous animation regardless of reduced-motion state** — there is no default auto-rotate to suppress in the first place, which trivially and robustly satisfies the reduced-motion requirement without needing a runtime toggle-and-verify test for a behavior that doesn't exist. An optional, explicit, user-triggered "auto-rotate preview" toggle (default off) is gated on the same shared hook and disabled entirely (not just paused) when reduced motion is active.

## Performance budget

Target: fewer rendered meshes than the existing `HumanMannequin` + `HumanScanRings` + `HumanSensorContacts` combination where practical, no per-frame geometry or material allocation, module-level singleton materials (mirroring `humanMaterials.ts`'s own pattern), `useMemo` for all static geometry derivations, `IntersectionObserver`-gated `frameloop` (`"always"` only while the canvas is in view, matching the existing `PhysiologyAvatar3D.tsx` pattern) since there is no autonomous animation requiring constant redraw. Exact measurements recorded in `PERFORMANCE_REPORT.md`.

## Asset decision

See `ASSET_AND_LICENSE_AUDIT.md` — no new asset, procedural geometry reused via import.

## Later integration boundaries

See `POST_STAGE45_INTEGRATION_PLAN.md` for the full port plan. In summary: the prototype's new material/lighting/interaction files are designed to be portable with light adaptation (swap Tailwind utility classes for the accepted shared design tokens once Stage 4-5 lands); the prototype never modifies or depends on unstable Stage 4-5-in-progress files, so it can be ported independently of that work's exact final state.
