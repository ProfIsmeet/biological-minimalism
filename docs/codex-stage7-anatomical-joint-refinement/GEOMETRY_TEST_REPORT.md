# Geometry test report

Implementation checkpoint: `972cedd591320bf8a283cbf964160fd61b6f0d17`

## Measured geometry

| Metric | Inherited | Refined |
|---|---:|---:|
| Vertices | 1,102 | 10,080 |
| Indices | 6,168 | 60,468 |
| Triangles | 2,056 | 20,156 |
| Minimum triangle area | `1.833e-5` | `3.051e-7` |
| X bounds | `±.347991` | `±.345878` |
| Y bounds | `.007736…1.768000` | `-.005023…1.791667` |
| Z bounds | `-.122840….175389` | `-.129193….205829` |

Vertex growth is `9.147×`, below the explicit `10×` regression ceiling and absolute 12,000-vertex ceiling. The body is constructed once under the existing `useMemo`, uploaded once, shared by the shell/lattice/rim, and disposed on unmount. No per-frame geometry construction was added.

## Added behavioral checks

The monitoring harness increased from `1091/1091` to `1116/1116`. The 25 added checks calculate from generated buffers or the same implicit field used to generate them:

- finite positions/normals/indices and unit nonzero normals;
- minimum triangle area above `1e-7`;
- every edge has exactly two incident faces;
- every vertex is referenced and the mesh has one connected component;
- exact mirrored positions within `.1 mm` and mirrored normals within `1e-4`;
- camera envelope, crown scale, depth, and ground alignment bounds;
- vertex-growth and absolute-count budgets;
- bilateral clavicle-to-deltoid continuity probes;
- bilateral hip-to-thigh continuity probes;
- arm roots clear the neck;
- arm/rib negative space remains open while both arms remain present;
- crotch center remains exterior while both thighs remain present;
- 95th-percentile adjacent-normal continuity thresholds at shoulders and pelvis.

Thresholds are scale-relative and intentionally stricter than the visible pixel scale. The shoulder normal gate requires at least 95% of local adjacent normals to differ by less than 20°. The concave pelvis permits 39° at the 95th percentile because a real crotch cleft necessarily turns more sharply than a convex shoulder.

## Result

`npm run verify:monitoring` → `1116/1116 passed, 0 failed`, followed by all seven structural/ownership verifiers passing.
