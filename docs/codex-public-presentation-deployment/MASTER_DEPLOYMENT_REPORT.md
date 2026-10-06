# Master deployment report

## Purpose

Publish the accepted Stage 8 application as a Vercel frontend plus Render FastAPI/WSS backend, pinned to a dedicated branch, with real PPG-DaLiA S14 replay and no viewer installation.

## Current verdict

Production is complete and verified. The owner selected Render Free plus an authenticated, hash-pinned private release bootstrap. The earlier pre-authorization status was accurate at the time; provider authorization was later completed without rewriting history. No protected branch was modified.

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

PASS on 2026-10-06. Frontend: `https://biological-minimalism-iac.vercel.app`; backend: `https://biological-minimalism-api.onrender.com`; deployed source `08481f69649892c56cd5cf38aed2dad47d02ec37`. Real S14, public read-only enforcement, browser WSS, and 621 seconds of uninterrupted browser endurance passed. Render Free cold starts remain an operational limitation, not an acceptance failure.
