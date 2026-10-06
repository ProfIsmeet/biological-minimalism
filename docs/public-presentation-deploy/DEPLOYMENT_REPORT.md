# Deployment report

Status: **IN PROGRESS**

This report is finalized only after the public URLs, provider deployment identities, environment contract, and branch SHA are verified. The implementation starts from accepted closure SHA `36cc9d36a9c11c47374bd6be142761d93b7cdfb5` and changes only the new deployment branch.

## Intended public topology

- Browser → Vercel Next.js frontend over HTTPS
- Browser → Render FastAPI over HTTPS
- Browser → Render `/ws/live-feed` over WSS
- Render private persistent disk → hash-pinned S14 archive and checkpoint
- Backend → committed, hash-pinned Model B checkpoint

No provider token or credential is committed.
