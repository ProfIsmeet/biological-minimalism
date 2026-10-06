# Production verification report

Status: **PASS — PUBLIC PRODUCTION VERIFIED 2026-10-06**

Closure evidence:

- Frontend: `https://biological-minimalism-iac.vercel.app`
- Backend: `https://biological-minimalism-api.onrender.com`
- Source commit: `08481f69649892c56cd5cf38aed2dad47d02ec37`
- Render deploy `dep-db2ekbcs728c73c5vgj0`: `Deploy succeeded | Live` on the Free plan.
- Vercel production deployment: `Ready` on the Hobby plan; canonical domain assigned.
- Public `/health`: HTTP 200 with `source_type=dataset_replay` and `public_read_only=true`.
- Public `/data-source/state`: HTTP 200; dataset `PPG-DaLiA`, subject `S14`, playback
  `playing` at `5.0x`; wrist BVP, wrist ACC, chest ECG, and wrist temperature present.
- Mutation control: `POST /data-source/replay/pause` returned HTTP 403 with
  `Public presentation is read-only.`
- Browser WSS/CORS/mixed-content integration: PASS from the exact Vercel origin.
  Mission Overview displayed `CONNECTED`, `PPG-DaLiA · S14`, `PUBLIC READ-ONLY`,
  fresh signal plots, and canonical Model B HR output.
- Browser endurance: PASS for 621 seconds in one uninterrupted page/WebSocket
  session. Replay markers advanced monotonically from approximately `4157s` to
  `7262s`; connection, S14 identity, read-only state, and model output remained
  present at final sampling.
- Provider logs: startup completed, Uvicorn bound to port 10000, repeated health
  checks returned 200, and no secret value or private local path was emitted.

The earlier CLI WSS runner could not complete its handshake through the local
command-line proxy, so production WSS closure is based on the real browser client
that the deployment serves. That client sustained the required ten-minute session.
