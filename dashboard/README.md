# Dashboard

The Biological Minimalism dashboard is not a separate application living in this
folder — it's the combination of [`../frontend/`](../frontend/) (the Next.js 15
Mission Control UI) and [`../backend/`](../backend/) (the FastAPI + WebSocket API
and mock telemetry engine). This folder exists to satisfy the project's documented
top-level layout and to hold dashboard-specific notes that don't belong in either
the frontend or backend package itself.

For run instructions, see the [root README](../README.md#quickstart). For the
architecture and design rationale, see the PDD's **Dashboard Architecture** and
**API Design** sections:
[`../docs/PDD_Biological_Minimalism_IAC2026.md`](../docs/PDD_Biological_Minimalism_IAC2026.md).

## At a glance

| Layer | Location | Responsibility |
|---|---|---|
| UI | `../frontend/src/app/*` | 6 pages (Mission Overview, Live Monitoring, Digital Twin, AI Insights, Mission Timeline, Settings) |
| State | `../frontend/src/store/missionStore.ts` | Zustand store fed by the WebSocket feed |
| Data fetch | `../frontend/src/lib/api.ts`, `useLiveFeed.ts` | REST + WebSocket clients |
| API | `../backend/app/api/` | REST routes + `/ws/live-feed` |
| Simulation | `../backend/app/engine/mock_data_engine.py` | Synthetic telemetry, mission modes, sensor-failure injection |
| Physiology model | `../backend/app/engine/physiology.py` | Transparent scoring formulas (the thing SHAP explains) |
| Explainability | `../backend/app/ml/explainability.py` | Real SHAP over the physiology model |
| Future ML | `../backend/app/ml/models.py`, `../ml/` | Real PyTorch architecture + training scaffolding, not active by default |

## Screenshots / demo video

Not included in this repository. For the IAC 2026 presentation, capture a short
screen recording of the three demos (Sensor Failure Simulation, Solar Storm Mode,
Digital Twin Evolution) running against `docker compose up` — see the root
README's [demo walkthrough](../README.md#the-three-required-demos).
