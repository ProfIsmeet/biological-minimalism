# Corrective implementation ledger

| Finding | Files | Correction | Regression coverage |
|---|---|---|---|
| H-01 | `backend/app/ml/explainability.py` | Independent locks serialize each mutable SHAP explainer without coupling confidence and fatigue calls. | `backend/tests/test_explainability_concurrency.py` (2 tests, 16 parallel calls per target) |
| M-01 | `AffectedRegionSummary.tsx` | Replay/synthetic wording follows authoritative source identity. | monitoring verifier source-aware assertions |
| M-02 | `MissionOverviewExperience.tsx`, `PipelineStateStrip.tsx` | Content-safe 1280px and 1180px breakpoints. | monitoring breakpoint assertions plus 1024/768 browser retest |
| M-03 | `OperationalAvatarOverlay.tsx`, `DemoControlDrawer.tsx`, `SensorConstellation.tsx`, `JuryHero.tsx`, `ExperimentalBoundary.tsx` | 44px minimum target geometry. | monitoring assertions plus real bounding-box measurements |

No accepted Stage 7 geometry, Stage 6 chart algorithm, telemetry ownership, data-isolation logic, or dataset/checkpoint content was changed.
