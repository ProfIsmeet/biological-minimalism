# Post-Stage2-4 Handoff to Integration Owner and Emir

Branch: `next-science-expansion-sprint`. **Not canonical.**
`PARALLEL_SCIENCE_EXPANSION_PENDING_PARENT_AUDIT` — the parent audit
target (`ab798815882ac0723491dc489de2375f8bf5b774`) has not yet completed
independent review.

## What's new and real this sprint

1. **Checkpoint durability**: 15 Sleep V2 checkpoints (C + interaction)
   from the prior sprint now externally archived and independently
   verified (GitHub Release `sleep-v2-corrected-c-interaction-checkpoint-archive-v1`).
2. **GalaxyPPG**: real, full A_cap/B/C training on a bounded single fold
   (4 test subjects of 24 eligible). Result: `EXTERNAL_REPLICATION_MIXED`
   — a real, genuinely mixed finding, not forced toward agreement or
   disagreement with PPG-DaLiA. 15 checkpoints externally archived and
   verified.
3. **LBNP**: real structural verification only (n=16 confirmed 3 ways,
   real EIS/target field structure). No training.
4. **HMC**: one controlled recheck, still blocked by the same external
   PhysioNet certificate expiry.

## What Integration Owner should NOT do with this

- Do not surface GalaxyPPG's mixed result as either a positive or negative
  headline finding — it is genuinely inconclusive at this bounded scale.
- Do not treat this branch as canonical or ready for final integration —
  it is pending both the parent audit (`ab798815...`) and this sprint's
  own eventual review.
- Do not select final architecture or compute a formal Pareto frontier
  from this data.

## Recommendation for Emir

1. Route the parent audit target (`ab798815882ac0723491dc489de2375f8bf5b774`)
   to the Independent Auditor as originally planned.
2. If/when a full 6-fold GalaxyPPG CV and a full LBNP A/B/C run become
   priorities, budget them as dedicated multi-hour sessions (GalaxyPPG's
   single fold alone took the bulk of this sprint's compute time; LBNP's
   remaining implementation work — time alignment + training — is
   comparable in scope).
3. Retry the HMC full-151 download once PhysioNet's certificate is
   rotated (check via `openssl s_client -connect physionet.org:443
   -servername physionet.org | openssl x509 -noout -dates`).
4. This branch's science is ready for Integration Owner's later,
   controlled integration once Emir accepts this sprint's completion —
   not automatically, and not before the parent audit's disposition is
   known.
