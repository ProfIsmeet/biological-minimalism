# Visual Acceptance Matrix

| Case | Result | Observed |
|---|---|---|
| 1920×1080 | PASS (interactive review) | Dominant full-body viewer, readable right boundary rail, no horizontal overflow. |
| 1440×900 | PASS (interactive review) | Full-body stage remains primary; chest and wrist focus inspected. |
| 1024×768 | PASS (interactive review) | Single-column content, large model, no horizontal overflow. |
| 390×844 | PASS (interactive review) | Intentional mobile stack, two-column preset controls, 44 px controls, semantic modules below model, `scrollWidth=innerWidth=390`. |
| Genuine 200% browser zoom | BLOCKED_EXTERNAL | Controlled in-app browser did not expose native zoom; viewport emulation was not substituted. |
| Default | PASS | Unified anatomical figure and all five canonical landmarks. |
| Front/back | PASS by behavior/source | Deterministic 0°/180° camera presets; back runtime image not persisted. |
| Chest | PASS | Torso remains in context; ECG landmark plus explicit selection ring. |
| Wrist | PASS | Wrist/hand and torso context visible; PPG and IMU colocated and individually marked. |
| Reduced motion | PASS | Static front/three-quarter figure, presets remain usable. |
| Focus state | PASS | High-contrast cyan outline visible around focused viewer. |
| WebGL fallback/loss/retry | BLOCKED_EXTERNAL runtime | Static fallback and lifecycle structurally verified. |

Browser images were visually inspected inline during the run. They are not canonical repository evidence because the browser tool could not export them to a repository path.
