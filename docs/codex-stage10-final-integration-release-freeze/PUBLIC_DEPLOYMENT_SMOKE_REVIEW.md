# Public Deployment Smoke Review

PASS without redeploy or provider changes.

- Frontend: `https://biological-minimalism-iac.vercel.app`
- API: `https://biological-minimalism-api.onrender.com`
- Public page displayed `PUBLIC · READ-ONLY`, connected PPG-DaLiA S14, and finite HR.
- Health/state asserted public read-only mode and S14 playing.
- Mutation request returned 403.
- Two WSS clients each received 108 monotonic frames and predictions over 60 seconds with identical first/last timestamps.
- Fresh screenshot visually passed; no provider/account page or private path was captured.

This is the prior stable public deployment at `1e2fb5b913d5ae7d5bd93a4c180f28603e1ec5fc`, not the Stage 10 candidate.
