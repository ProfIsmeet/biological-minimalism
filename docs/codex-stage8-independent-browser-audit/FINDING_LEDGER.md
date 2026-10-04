# Finding ledger

| ID | Severity | Reproduction and root cause | Final status |
|---|---|---|---|
| H-01 | High | Concurrent `/ai/explanation` requests intermittently returned 500. A singleton SHAP `KernelExplainer` mutates internal scratch arrays while FastAPI serves calls in parallel. | Corrected; per-explainer locks, deterministic concurrency tests, repeated browser requests all 200 |
| M-01 | Medium | Mission Overview said `confirmed replay inputs` while the authoritative source was synthetic. Copy was source-neutral. | Corrected; copy branches on authoritative replay/synthetic identity |
| M-02 | Medium | At 1024×768 the radar/table split clipped; at 768×1024 the horizontal pipeline clipped. Breakpoints ignored the persistent sidebar's remaining content width. | Corrected; split waits for 1280px and horizontal pipeline for 1180px |
| M-03 | Medium | Operational avatar controls, Demo Controls actions, constellation jump links, and several System Brief calls to action were below the accepted 44px target floor. | Corrected and remeasured in Chromium |

Remaining critical/high/medium defects: **0 / 0 / 0**.

Verification limitations are tracked separately and do not masquerade as product findings: durable screenshot export, genuine zoom, OS preference emulation, actual screen reader, and real S14 replay.
