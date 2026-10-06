# Deployment report

Status: **DEPLOYED — FREE-TIER PRODUCTION VERIFIED**

This report is finalized only after the public URLs, provider deployment identities, environment contract, and branch SHA are verified. The implementation starts from accepted closure SHA `36cc9d36a9c11c47374bd6be142761d93b7cdfb5` and changes only the new deployment branch.

## Intended public topology

- Browser → Vercel Next.js frontend over HTTPS
- Browser → Render FastAPI over HTTPS
- Browser → Render `/ws/live-feed` over WSS
- Render ephemeral startup → authenticated private, hash-pinned S14 bundle and checkpoint
- Backend → committed, hash-pinned Model B checkpoint

No provider token or credential is committed.

## Production identities

- Frontend: `https://biological-minimalism-iac.vercel.app`
- Backend: `https://biological-minimalism-api.onrender.com`
- Backend WebSocket: `wss://biological-minimalism-api.onrender.com/ws/live-feed`
- Source branch: `codex/public-presentation-deploy`
- Deployed source commit: `08481f69649892c56cd5cf38aed2dad47d02ec37`
- Render deploy: `dep-db2ekbcs728c73c5vgj0`
- Vercel project: `biological-minimalism-iac` (Hobby)
- Render service: `biological-minimalism-api` (Free)

The production asset bootstrap uses a private GitHub Release, a repository-scoped
read-only token, SHA-256 pinning, and a pickle-free selected-channel NPZ bundle.
The original repository anchor remains untouched and no main-branch merge was
performed.
