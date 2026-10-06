# Master deployment report

## Purpose

Publish the accepted Stage 8 application as a Vercel frontend plus Render FastAPI/WSS backend, pinned to a dedicated branch, with real PPG-DaLiA S14 replay and no viewer installation.

## Current verdict

Local public-mode implementation and real-S14 acceptance are complete. The owner declined paid Render compute/storage, so the deployment uses Render Free plus an authenticated, hash-pinned private release bootstrap. Render email verification and a least-privilege private-asset read credential remain required before production creation. No protected branch was modified and Stage 9 was not started.

## Deployment-only changes

- opt-in backend public presentation settings;
- fail-fast dataset/checkpoint hash validation and S14 autoplay;
- replay reset/loop without retained history;
- global HTTP mutation rejection and exact HTTP/WebSocket Origin enforcement;
- conservative public request, WebSocket, and explanation concurrency limits;
- frontend public read-only indicator and removal of unusable mutation controls;
- Render Blueprint and repeatable endurance verifier.
- reproducible exact-channel S14 bundler and credential-safe private cold-start bootstrap.

Scientific calculations, checkpoint behavior, thresholds, telemetry authority, missing-data semantics, charts, and accepted responsive composition are unchanged.

## Local result

The official UCI distribution was downloaded and verified. A deployment-only S14 archive containing the original `S14.pkl` plus attribution was created outside Git. The backend loaded it, validated the accepted Model B checkpoint, auto-started replay at 5x, delivered fresh HR predictions to multiple clients, rejected mutation, and drove the production frontend through all eight principal routes at 1440×900, 1024×768, and 390×844 without horizontal overflow or private-path exposure.

## Production result

Pending Render email verification and private-asset credential entry. No paid-resource approval is required. Public URLs and deployment identities must not be claimed until the production acceptance report is complete.
