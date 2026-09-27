# Prompt 3B/3C Dossier — Human Figure Visual Evidence

## Asset provenance

The holographic human figure rendered in the Digital Twin Reference and
Operational Physiology views is an **original, procedurally generated
mesh** (`frontend/src/components/visualization/human/anatomicalHumanGeometry.ts`
+ `HolographicHumanFigure.tsx`) — lofted elliptical cross-section rings for
torso/limbs/head, assembled in-code from geometric primitives. It is **not**
a downloaded, scanned, or licensed 3D human asset. Confirmed by source
inspection: no `useGLTF`, no `.glb`/`.gltf` import, no reference to any
external model file anywhere in the component. No CesiumMan or other
third-party rigged-human asset is loaded by this build.

## Privacy review

No real person's likeness, scan, photograph, or biometric data is used or
implied by this figure. It is an abstract teal/cyan wireframe-and-shell
holographic silhouette with no facial features, no identifying
characteristics, and no text or personal data rendered on the body. Safe to
distribute publicly.

## Evidence captured this session

All three captured against the real production build (`localhost:3003`),
Chrome DevTools MCP, desktop 1280x800 viewport, `/digital-twin` route,
synthetic-demo backend (`127.0.0.1:8003`), architecture-only/untrained/
unvalidated boundary badge visible in every shot:

| File | Approx. angle | Real/Synthetic/Controlled |
|---|---|---|
| `../human-front-holographic-figure.png` | ~350 degrees (front) | Real production UI, synthetic demo backend |
| `../human-three-quarter-holographic-figure.png` | ~35 degrees (three-quarter) | Real production UI, synthetic demo backend |
| `../human-side-holographic-figure.png` | ~103 degrees (side) | Real production UI, synthetic demo backend |

Angles were reached using the real "Rotate left"/"Rotate right" controls
(22.5 degrees per press) after pausing auto-rotation, then verified against
the sr-only rotation-angle text before each capture. All three were
visually reviewed: correct boundary copy, correct silhouette, no invented
confidence/adaptation values, no rendering artifacts.
