# Adversarial Finding Ledger

| ID | Severity | Evidence/root cause | Correction | Verification | Disposition |
|---|---|---|---|---|---|
| S7-01 | High | Prototype uses disconnected capsule/sphere mannequin and is based on stale Stage 4–5 base. | Rejected model; integrated on accepted anatomical geometry. | Visual review at required desktop/tablet/mobile sizes. | Fixed |
| S7-02 | High | Prototype is hidden-route-only. | Canonical production `/digital-twin`; existing sidebar/mobile navigation retained. | Route tree and real navigation. | Fixed |
| S7-03 | High | Live-looking Digital Twin could imply trained/personalized physiology. | Static runtime tier; persistent boundary; no store/network/model inputs. | Structural ownership guard and source review. | Fixed |
| S7-04 | Medium | Accepted production route lacked chest/wrist/back deterministic focus. | Added typed presets and keyboard mappings. | Pure behavioral tests and real keyboard QA. | Fixed |
| S7-05 | Medium | Old fallback preserved copy but not topology. | Added accessible SVG silhouette/landmarks/current view. | Structural fallback guard and typecheck. | Fixed |
| S7-06 | Medium | Render loop did not explicitly stop on hidden page. | Added `visibilitychange` state and cleanup; demand frameloop. | Structural guard; source review. | Fixed |
| S7-07 | Medium | Reduced-motion disabled control label could say “Pause rotation.” | Label becomes “Rotation paused” while preference is active. | Accessibility-tree review. | Fixed |
| S7-08 | Low | Upstream React Three Fiber emits `THREE.Clock` deprecation once per mount. | Not suppressed; dependency-level limitation documented. | Runtime console inspection. | Open low |
| S7-09 | Verification | Browser screenshots cannot be persisted by available controlled browser. | None safe in this environment. | Tool capability inspection. | Blocked external |
| S7-10 | Verification | Genuine 200% page zoom unavailable in controlled browser. | No viewport-emulation substitution. | Native shortcut attempt had no zoom effect. | Blocked external |
| S7-11 | Verification | Controlled browser cannot disable/lose WebGL through exposed capabilities. | Structural lifecycle checks retained. | `verify-webgl-fallback` pass. | Blocked external |
| S7-12 | Medium | Initial screenshot-directory `AUDIT.md` collided with the fail-closed canonical audit slot. | Renamed the informational note to `README.md`; no policy weakening. | Evidence verifier returned to exit 0. | Fixed |

This self-review does not replace independent review. High remaining: 0. Medium remaining: 0. Mandatory verification gaps remain.
