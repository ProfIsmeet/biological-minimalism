# Stage 7 Digital Twin Prototype — Performance Report

## Asset transfer

**Zero GLB/binary asset** — the prototype uses only procedural geometry (see `ASSET_AND_LICENSE_AUDIT.md`), so there is no model transfer cost of any kind. Total new source added: 68 KB across `frontend/src/prototypes/stage7-digital-twin/` (13 files, 1073 lines) + 4 KB for the route page — this ships as ordinary JS/CSS, not a binary payload.

## Geometry / mesh counts (per render, fixed, non-animated)

| Element | Count | Source |
|---|---|---|
| Head sphere | 1 | `Stage7HumanModel.tsx`, reusing `HEAD_RADIUS`/`JOINTS.head` |
| Body capsule segments | 16 | `BODY_SEGMENTS` (imported, unmodified, from `humanGeometry.ts`) |
| Joint spheres | 8 | `JOINT_SPHERES` (mirrors the product's own `HumanMannequin.tsx` list) |
| Sensor anchor markers | 5 | one per `FINAL_SENSOR_INVENTORY` entry (always rendered) |
| Selection-highlight ring | 0 or 1 | only while a modality is selected |
| Region-focus outline torus | 0 or 1 | only while a region is focused |
| **Total meshes (typical, one selection active)** | **~32** | |

This is comparable to (not larger than) the product's own operational avatar (`HumanMannequin` + `HumanScanRings` + `HumanSensorContacts`), which the prototype's design deliberately did not exceed — no additional decorative geometry (no free-floating ambient scan rings, no particle systems) was added.

## Material count

5 module-level singleton materials (`stage7BodyMaterial`, `stage7JointMaterial`, `stage7LatticeMaterial`, `stage7RegionFocusMaterial`, plus a small per-modality-color cache of up to 5 anchor materials created once and reused — never recreated per render or per frame). Verified by code review: every material in `stage7PrototypeMaterials.ts` is a module-level `const`, not constructed inside a component body or a `useMemo` callback that could re-run.

## Draw-call estimate

Roughly one draw call per mesh under Three.js's default (non-instanced) rendering path — approximately 32 draw calls for the typical one-selection-active scene. No instancing was used since the segment/joint/anchor counts are small and fixed; this was judged not worth the added complexity for a 32-mesh scene.

## Rendering strategy

`frameloop: "demand"` — the Canvas renders **zero frames** when nothing has changed (no `useFrame` call exists anywhere in the prototype; confirmed structurally by `verify-stage7-digital-twin-prototype.mjs` check #6). A frame is only produced by an explicit `invalidate()` call (on mount, on scene-background set, and on camera/view change) or by React/R3F's own automatic invalidation when a tracked prop changes (e.g. selection state changing which meshes render highlighted). This is a stronger performance posture than the product's own `PhysiologyAvatar3D.tsx` (which uses `frameloop: "always"` gated only by an `IntersectionObserver`), since the prototype has no continuous animation to justify `"always"` in the first place.

## First render time (observed, this environment)

Not precisely benchmarked with instrumentation (no performance-timing code was added, per the "no per-route measurement dependency" scope), but observed directly during browser verification: initial WebGL context creation and first paint took approximately 5-10 seconds in this environment's software-rendered VM (VMware SVGA 3D, no hardware GPU — see `RUN_STATE.md`). This is materially slower than a real GPU would produce and should not be read as representative of end-user hardware; it is reported honestly as an environment characteristic encountered during verification, not as the prototype's real-world performance profile.

## Resize stability

`ResizeObserver` on the canvas container (`Stage7PrototypeCanvas.tsx`) recomputes `aspect` and feeds it to `stage7ComputeFrustum` on every resize — this is the same pattern the product's own `PhysiologyAvatar3D.tsx` already uses. Not independently re-verified via an actual browser resize event in this session (the browser's window could not be resized in this environment — see `RUN_STATE.md`'s network/environment note) — this is a known, honestly-reported gap, not a claimed pass.

## Resource cleanup

- `ResizeObserver.disconnect()` is called in every effect's cleanup function (`Stage7PrototypeCanvas.tsx`) — verified by code review.
- `WebglStage`'s own `webglcontextlost` listener cleanup (imported, unmodified from the product) is reused as-is; the prototype adds no additional DOM listeners that would need separate cleanup.
- No `setInterval`/`setTimeout` of any kind exists anywhere in the prototype (confirmed by grep) — there is nothing to leak on that front.
- Materials/geometries are module-level singletons (see above) — there is no per-mount allocation to dispose of a per-unmount `dispose()` call would otherwise need to reclaim; disposal is not required for objects that live for the module's lifetime, matching the same convention `humanMaterials.ts` already established.

## Per-frame allocation check (structural, code-reviewed)

No component allocates a new `THREE.Color`, `THREE.Material`, or geometry inside a render body, a `useFrame` callback (there are none), or an unmemoized position computed on every render — `Stage7HumanModel.tsx`'s segment transforms are wrapped in `useMemo([])` (static, computed once), and all materials are imported module-level singletons. `PER_FRAME_GEOMETRY_ALLOCATION_PRESENT: NO`, `PER_FRAME_MATERIAL_ALLOCATION_PRESENT: NO`.
