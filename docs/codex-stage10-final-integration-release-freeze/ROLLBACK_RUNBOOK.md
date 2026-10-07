# Rollback Runbook

No rollback action is currently required.

If the candidate is merged and fails independent/post-merge checks:

1. Stop promotion; do not alter the stable public branch.
2. Record the failing candidate SHA and evidence.
3. Revert the Stage 10 merge commit on a new `codex/` repair branch; do not rewrite history.
4. Restore source behavior to rollback base `9ea9ef4b8f0f4a9d58344a29541faeb065037665` only through a reviewed revert/fast-forward decision.
5. Keep public deployment on `1e2fb5b913d5ae7d5bd93a4c180f28603e1ec5fc` until a replacement passes smoke.
6. Re-run source, clean-clone, scientific, evidence, public-contract, and privacy gates.

External dataset/checkpoint assets and provider secrets are never part of Git rollback.
