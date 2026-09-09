# GalaxyPPG Split Strategy — Deviation from Full Grouped CV (versioned before training)

**Frozen Stage 1B protocol** (`results/galaxyppg_protocol_stage1b.json`)
specifies grouped subject-wise outer CV, "all 24 subjects held out
exactly once."

**Problem**: full CV at 6 folds × 5 seeds × 3 conditions (A_cap/B/C) = 90
full training runs on real, ~1,800-epoch-per-subject window sets — not
feasible within this sprint's realistic compute/time budget (this is on
top of the same sprint's Sleep V2 and HMC training already completed).

**New protocol (versioned here, BEFORE any training)**: a single fixed
train/val/test split over all 24 real, eligible subjects (all 24 passed
the real eligibility check — `results/galaxyppg_eligibility_stage2.json`),
chosen by the identical neutral-shuffle rule already used for HMC's
full-cohort split this session (`random.Random(42).shuffle()` over the
sorted participant list), 16/4/4 train/val/test.

**Exact split** (`results/galaxyppg_split_stage2_single_fold.json`):
- Train (16): P02, P03, P06, P07, P10, P11, P12, P13, P14, P15, P16, P17, P18, P19, P22, P24
- Val (4): P05, P08, P20, P23
- Test (4): P01, P04, P09, P21

**Disposition**: `BOUNDED_TO_SINGLE_FOLD` — this is a real, genuine
subject-held-out evaluation (4 test subjects never seen during training),
but it is NOT the full "every subject held out once" grouped-CV result the
frozen protocol specifies. A future full-CV run (5 more folds) remains the
canonical completion of this experiment.

**Whether any outcome was already inspected**: No. This split was
constructed using only the eligibility table (data-quality facts: file
presence, sync overlap duration) — no HR/model outcome of any kind existed
when this split was frozen.
