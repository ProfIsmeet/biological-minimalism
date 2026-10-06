# Rollback runbook

1. In Vercel, promote the last known-good production deployment from this deployment branch; never switch Production Branch to `main` or a Stage 9/10 branch.
2. In Render, roll back to the recorded last known-good backend deployment.
3. Recheck `/health`, `/data-source/state`, allowed-origin REST, disallowed-origin REST/WSS, and fresh S14 HR.
4. To disable presentation behavior, set `BIOMIN_PUBLIC_PRESENTATION_MODE=false` and redeploy; this is an operator action, not a browser override.
5. To take the site offline, pause/maintenance the Render service and remove/promote away the Vercel domain as appropriate.
6. Rotate a private bootstrap credential only in provider secret fields. No such credential is present in Git.
7. The accepted Stage 8 source remains recoverable at `36cc9d36a9c11c47374bd6be142761d93b7cdfb5`.

Accepted production identities: frontend `https://biological-minimalism-iac.vercel.app`, backend `https://biological-minimalism-api.onrender.com`, source commit `08481f69649892c56cd5cf38aed2dad47d02ec37`, Render deploy `dep-db2ekbcs728c73c5vgj0`. These facts were appended after the original pre-authorization run.
