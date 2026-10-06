# Cost and platform limitations

Render Free and `0.5c-512mb` both provide only 512 MB RAM. Local real-S14 warmup showed approximately 138 MB resident plus 355 MB swapped/dirty pressure in macOS `vmmap`, leaving no safe Linux headroom at 512 MB. The smallest plausibly safe tier is Render `1c-2g` (1 CPU, 2 GB), currently displayed at **$25/month**. A 1 GB encrypted persistent disk is **$0.25/GB/month**. Proposed region: **Frankfurt, Germany**. Proposed total: **$25.25/month**, excluding bandwidth beyond the Hobby allowance; compute is prorated per Render's billing terms.

This paid configuration is not selected until the owner explicitly approves. With it, the service is always-on and avoids free-tier sleep/cold-start. The private disk prevents repeated asset downloads and keeps raw participant data out of public artifacts. Vercel cost is expected to be $0 on the applicable free account unless its dashboard shows otherwise.
