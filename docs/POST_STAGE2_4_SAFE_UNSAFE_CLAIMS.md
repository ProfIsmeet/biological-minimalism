# Post-Stage2-4 Safe / Unsafe Claims

## GalaxyPPG (new this sprint)

**Safe**: "Under a capacity-controlled, real-ECG-referenced protocol on an
independent device/subject family (GalaxyPPG, single bounded fold, n=4
test subjects), the previously observed PPG-DaLiA IMU benefit showed a
weak, seed- and subject-inconsistent signal (A→B +0.251 bpm, 3/5 seeds;
per-subject sign reversal: P01/P04 favor B, P09/P21 favor A_cap) —
classified `EXTERNAL_REPLICATION_MIXED`."

**Unsafe**: "IMU always improves HR estimation." "GalaxyPPG
replicates/confirms PPG-DaLiA." "GalaxyPPG refutes PPG-DaLiA." Any claim
extending beyond the 4 bounded test subjects to the full 24-subject
cohort (full 6-fold CV not performed this sprint).

## LBNP (structural verification only, new this sprint)

**Safe**: "LBNP's real n=16 cohort, 3-site EIS structure, and 100-point
excitation-frequency axis are independently confirmed from raw MATLAB
file content (three separate structures agree exactly on n=16)."

**Unsafe**: Any sensor-value claim (no training was run). "LBNP validates
astronaut hypovolemia monitoring" or any spaceflight/microgravity
equivalence (unchanged prohibition from the prior sprint).

## HMC (unchanged, one recheck only)

**Safe**: "HMC's full-151-recording external access remains blocked by a
genuine external PhysioNet TLS certificate expiry, independently
reverified this sprint; the n=7 bounded diagnostic from the prior sprint
is preserved unchanged as the best currently-available evidence."

**Unsafe**: "HMC replicates or fails to replicate Sleep-EDF" (n=7/1-test-
recording is too small for either claim, unchanged from the prior
sprint's determination).

## Checkpoint durability (new this sprint)

**Safe**: "All 15 Sleep V2 (C + interaction) and all 15 GalaxyPPG (A_cap/
B/C) checkpoints from this sprint's work are externally archived on
GitHub Releases and independently verified via fresh redownload + SHA256
recomputation (30/30 exact match)."

## HeartCycle

**Safe**: "HeartCycle's feasibility was thoroughly audited in an earlier
sprint (`datasets/HEARTCYCLE_AUDIT.md`) and found PARTIALLY suitable (only
4/17 subjects have PPG); unchanged this sprint, not re-audited or
re-prioritized given GalaxyPPG/LBNP/HMC's higher priority ranking."

## Carried-forward unsafe claims (unchanged, still governing)

All unsafe claims from `docs/STAGE1B_EXPANSION_FORBIDDEN_CLAIMS.md` and
`docs/STAGE2_4_SAFE_UNSAFE_CLAIMS.md` remain in force: no final four-sensor
architecture, no formal global Pareto, no astronaut/microgravity validation
from any terrestrial dataset, no fake global sensor score, no EOG/IMU
declared strictly necessary.
