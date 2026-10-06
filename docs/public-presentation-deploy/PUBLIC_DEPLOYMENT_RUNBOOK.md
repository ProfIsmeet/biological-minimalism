# Public presentation deployment runbook

## Immutable source

- Git source: `origin/codex/stage8-final-evidence-closure`
- Accepted source SHA: `36cc9d36a9c11c47374bd6be142761d93b7cdfb5`
- Deployment branch: `codex/public-presentation-deploy`
- Frontend: Vercel, root directory `frontend`
- Backend and WebSocket: Render Blueprint `render.yaml`

Do not merge or rewrite the protected Stage 6, Stage 7, Stage 8, Mission Overview, audit, or closure refs for this deployment.

## Runtime contract

The public backend starts only when all of the following hold:

1. `BIOMIN_PUBLIC_PRESENTATION_MODE=true`.
2. `BIOMIN_PPG_DALIA_PATH` names a local zip file, or the file can be obtained from the HTTPS-only `BIOMIN_PRESENTATION_DATASET_URL`.
3. `BIOMIN_PRESENTATION_DATASET_SHA256` matches the complete downloaded S14-only archive.
4. The archive contains the original, internally identified `PPG_FieldStudy/S14/S14.pkl` recording.
5. The committed PPG+IMU checkpoint passes the model bridge's pinned SHA and metadata contract.
6. S14 loads, replay speed is accepted, and playback starts.

The public runtime blocks every non-GET/HEAD/OPTIONS HTTP request with 403, rejects missing or unapproved WebSocket origins before acceptance (ASGI policy close 1008; HTTP 403 at the network handshake), and loops replay after the recorded end. Local development remains mutable because public mode defaults to false.

## Render environment

Set these non-secret values in the Render service:

- `BIOMIN_ALLOWED_ORIGINS=["https://<exact-vercel-production-host>"]`
- `BIOMIN_PRESENTATION_DATASET_SHA256=<sha256>`

The Blueprint supplies the remaining presentation values. No API token, asset credential, or admin bypass belongs in source control. For the $0 deployment, both URLs identify authenticated private release assets. Set `BIOMIN_PRESENTATION_ASSET_BEARER_TOKEN` to a least-privilege read-only credential in Render's secret field. The backend strips that credential before any cross-host signed redirect, verifies both complete hashes, and fails closed. The URLs and credential must never appear in the frontend or public access guide.

Render Free has no persistent disk. Every spin-down, restart, or redeploy removes the local copies and forces a new authenticated bootstrap. Expect roughly one minute or more for a cold start, and validate the 512 MB memory limit on the deployed Linux instance before presentation use.

## Vercel environment

Production build variables:

- `NEXT_PUBLIC_API_BASE_URL=https://<render-host>`
- `NEXT_PUBLIC_WS_URL=wss://<render-host>/ws/live-feed`
- `NEXT_PUBLIC_PRESENTATION_MODE=true`

All three are public browser configuration, not secrets. Production Branch must be exactly `codex/public-presentation-deploy`.

## Data license and provenance

The deployed recording is PPG-DaLiA subject S14, redistributed under CC BY 4.0. Dataset citation: Reiss, A., Indlekofer, I., & Schmidt, P. (2019), PPG-DaLiA, UCI Machine Learning Repository, DOI `10.24432/C53890`. The application continues to label S14 as a single-participant robustness demonstration, not population validation and not live astronaut monitoring.

## Rollback

Rollback only to a known-good deployment of this branch. Do not promote `main` or any protected evidence branch by accident. After rollback, re-check `/health`, `/data-source/state`, WSS origin enforcement, and both primary routes before declaring recovery.

## Repeatable endurance check

Run from the repository root after deployment:

```bash
backend/.venv/bin/python backend/scripts/verify_public_endurance.py \
  --api-url https://<render-host> \
  --ws-url wss://<render-host>/ws/live-feed \
  --origin https://<vercel-production-host> \
  --duration 600 --clients 3
```

The check requires continuous fresh S14 timestamps, an available AI HR prediction after warmup, a 403 mutation boundary, and successful concurrent WebSocket delivery for the full interval.
