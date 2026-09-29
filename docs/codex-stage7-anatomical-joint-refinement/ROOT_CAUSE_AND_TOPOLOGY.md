# Root cause and topology

## Source identity

- Source branch: `origin/ismet/stage7-independent-browser-acceptance`
- Required and verified source tip: `f80280a41034b3b5e535b9dca0874029fa2d9e45`
- Isolated branch: `codex/stage7-anatomical-joint-refinement`
- Implementation checkpoint: `972cedd591320bf8a283cbf964160fd61b6f0d17`

## Inherited topology

The inherited `buildAnatomicalHuman()` built six independent families: a capped horizontal-ring torso, a separately lofted head/neck, two separately lofted arms, and two separately lofted legs. `mergeMeshArrays()` only offset and concatenated their arrays. It did not weld coincident coordinates, share boundary-loop indices, boolean-union volumes, or reconcile normals.

The torso used 22-vertex horizontal elliptical rings. It expanded from `rx=.060` at `y=1.525` to `rx=.180` at `y=1.460`, then narrowed through the chest. Each arm began at `x=±.158, y=1.470`, used a 14-vertex parallel-transport ring, and set `capStart: true`. The cap center and 14 fan triangles remained inside the shoulder volume.

The pelvis ended as one full-width ellipse at `y=.865`, `rx=.138`, `rz=.106` and had `capEnd: true`. Each thigh began at `x=±.098, y=.865`, radius `.080`, with `capStart: true`. The central ellipse therefore ended in a flat horizontal edge while the two capped thigh tubes began beneath it.

Normals were accumulated per independent part. Even after concatenation, the torso and limbs had unrelated vertex sets and unrelated normals. The transparent shell (`opacity=.54`, `depthWrite=false`), full triangle wireframe, and scaled back-face rim exposed the internal cap fans, intersecting surfaces, angular ring changes, and normal discontinuities from both sides.

## Selected correction

The final generator evaluates a deterministic smooth implicit field made from:

- a compact loft-profile torso core;
- a sloped clavicular capsule and ovoid deltoid on each side;
- mirrored variable-radius arm chains;
- separate iliac/gluteal lobes and mirrored thigh chains;
- preserved stylized head, hands, feet, knees, calves, stance, and wrist placement.

A `49 × 123 × 27` grid samples that field. Deterministic surface nets create one vertex per active cell and one indexed quad around every sign-changing grid edge. Adjacent quads reuse the same cell vertex. Finite-difference field gradients provide smooth outward unit normals independent of triangulation diagonals.

This removes the shoulder and thigh root caps entirely. The central torso, both arms, pelvis, and both legs are now one connected indexed outer surface. The crotch is produced by two withdrawing medial hip/thigh fields, not by suspending cylinders below a block.

## Topology truth statement

The final body is a single welded, indexed, closed procedural surface. Automated incidence analysis finds one connected component, every vertex referenced, every edge incident to exactly two faces, and zero boundary or non-manifold edges. It is not an imported model and has no internal root faces. This report does not make the stronger CAD/manufacturing claim that every possible self-intersection or volumetric tolerance has been certified.

## Rejected alternatives

- Radius/coordinate-only overlap: rejected because translucent layers would continue exposing caps and intersecting normals.
- Open limb roots plus raw wireframe: rejected because it leaves real boundaries and can expose bright rings under future material changes.
- Decorative patches, darker joints, extra glow, clothing, or camera concealment: rejected as concealment rather than geometry correction.
- Hand-authored pair-of-pants bridge patches: rejected because four local transition patches would be harder to keep symmetric, closed, and normal-continuous than one deterministic field.
- External anatomical asset: rejected by scope and provenance requirements.
