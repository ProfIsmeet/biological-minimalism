# Source Prototype Adjudication

## Reconciled Git truth

The prototype branch contains four commits after its actual base `7afe57114ad6f7537b73f17683f7ecd733606730`: `c4ff1b3`, `7895e97`, `7bc09b5`, and `4295f29`. Its own-base delta is exactly **34 added files and 1,996 insertions**. The comparison against the later accepted Stage 4–5 tip is 79 changed files because it also includes independent baseline work and apparent deletions; that comparison is not a valid “prototype file count.” The reported “26 new files” is incorrect.

## File-class adjudication

| Prototype area | Classification | Decision |
|---|---|---|
| Hidden research route | REJECT | Final product already has canonical `/digital-twin` and a navigation entry. No duplicate route. |
| View presets/camera concepts | PORT_WITH_REWRITE | Reimplemented as pure typed presets on the accepted orthographic camera/anatomical mesh. |
| Capsule mannequin | REJECT | Visually primitive and inferior to accepted `anatomicalHumanGeometry.ts`. |
| Prototype matte material/lighting | REPORT_ONLY | Accepted holographic volume and restrained lighting already meet the established visual system. |
| Canonical topology imports | PORT_WITH_REWRITE | Landmarks derive from existing canonical inventory/colors/coordinates. |
| Semantic DOM legend | PORT_WITH_REWRITE | Expanded into full module controls, current-view status, and sensor legend. |
| Static fallback | PORT_WITH_REWRITE | Rebuilt as an information-preserving anatomical SVG with retry only when possible. |
| WebGL lifecycle | PORT_AS_IS (baseline) | Accepted shared `WebglStage` already owns detection, error boundary, context-loss cleanup, and clean remount retry. |
| Prototype CSS | REJECT | Would create a divergent style island and smaller text. Tailwind/design tokens retained. |
| Prototype reports/screenshots | REPORT_ONLY | Useful provenance, never evidence for the integrated branch. |
| Prototype test script | REIMPLEMENT | Replaced with behavioral pure-function tests plus structural ownership/accessibility guards. |

No merge or cherry-pick from the prototype branch was performed.
