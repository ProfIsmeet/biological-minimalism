# Cost and platform limitations

The owner declined paid compute and storage. The selected backend plan is Render Free at **$0/month**: 0.1 CPU, 512 MB RAM, 750 workspace-hours/month, and no persistent disk. Vercel Hobby and the private GitHub release bootstrap are also **$0** within their included allowances. No paid resource is selected.

Render documents that Free web services spin down after 15 minutes without inbound HTTP or WebSocket activity, take about a minute to wake, lose local filesystem changes on every spin-down/restart/redeploy, and may be restarted at any time. The backend therefore downloads two authenticated private assets on each cold start and verifies both hashes before accepting traffic. This is a free presentation deployment, not an always-on production SLA. A connected presentation WebSocket now counts as inbound activity and prevents idle spin-down while it remains active.

The exact-channel S14 bundle reduced the compressed bootstrap from 105 MB to 19,058,604 bytes while preserving every consumed sample bit-for-bit. Local warm runtime stayed under 512 MB, but macOS peak physical footprint briefly reported 567.9 MB; actual Render Free cold-start acceptance is therefore a hard production gate and any OOM remains a disclosed blocker rather than a fabricated pass.
