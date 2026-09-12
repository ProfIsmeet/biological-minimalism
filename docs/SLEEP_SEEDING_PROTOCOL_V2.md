# Sleep-EDF Seeding Protocol V2 (Day 12, H1 Remediation)

## What was wrong

Every Sleep-EDF trainer (`ml/train_sleep_edf_eeg_eog_ablation.py`,
`ml/train_sleep_edf_shuffled_eog_control.py`,
`ml/train_sleep_edf_interaction_resp.py`) follows this order:

```python
model = SleepStageClassifier(in_channels=len(channels))   # (1) construct
history = train_one(model, train_x, train_y, ..., seed)   # (2) train_one() calls torch.manual_seed(seed) INSIDE, at its first line
```

`SleepStageClassifier.__init__` builds `Conv1d`/`Linear` layers whose
default PyTorch initialization draws from the **global torch RNG at
construction time** — step (1), before step (2) ever seeds anything. The
recorded `seed` therefore controls the DataLoader shuffle order (correct,
since that happens after `torch.manual_seed(seed)` inside `train_one`) but
does **not** control the model's initial weights.

Real, reproduced demonstration:
`ml/diagnostics/sleep_seed_initialization_probe.py` →
`results/sleep_seed_initialization_audit_day12.json`
(`overall_h1_confirmed: true`). Constructs the actual
`SleepStageClassifier`, shows the same recorded seed produces different
initial weights under the old order (depending on ambient RNG state) and
identical initial weights under the corrected order.

## What was NOT affected

- The EOG shuffle (`shuffle_eog_within_subject`) already uses a **local**
  `np.random.default_rng(seed)` instance, fully isolated from torch's
  global RNG and from model construction order. It was never affected by
  H1 - confirmed by every existing reproducibility check
  (`ml/verify_sleep_edf_shuffled_eog_reproducibility.py`,
  5/5 exact match, every time it has been run).
- DataLoader shuffle order, since `torch.manual_seed(seed)` inside
  `train_one` runs before the DataLoader is constructed.
- All existing checkpoints remain real, valid, historical trained models -
  H1 does not mean training didn't happen or the weights are invalid, only
  that the recorded seed does not fully identify the initialization that
  produced them.

## Corrected protocol (`ml/sleep_seed_utils.py`)

One run seed (42-46) derives **three independent sub-seeds**, each
controlling exactly one RNG role - not silently sharing one seed value
across unrelated roles:

| Sub-seed | Formula | Controls | Called |
|---|---|---|---|
| `model_init_seed` | `run_seed + 0` | Python `random`, NumPy, torch global RNG (CPU + CUDA if present) | **Before** `SleepStageClassifier(...)` is constructed |
| `data_order_seed` | `run_seed + 100_000` | torch global RNG for DataLoader `shuffle=True` order | **After** model construction, **before** the DataLoader is built |
| `control_shuffle_seed` | `run_seed + 200_000` | Reserved for a future control needing torch-driven shuffling. The existing EOG shuffle does NOT use this - it uses its own already-isolated `np.random.default_rng(seed)`, unchanged. |

```python
seeds = derive_sleep_run_seeds(run_seed)
seed_for_model_init(seeds)               # fixes H1
model = SleepStageClassifier(...)
seed_for_data_order(seeds)
# ... build DataLoader, optimizer, train ...
```

The offsets (0 / 100,000 / 200,000) are fixed and documented so no two
sub-seeds for any of this project's run seeds (42-46) ever collide, and
so a reader can recover which sub-seed produced which value without
guessing.

## Determinism caveats

- CPU-only training (this project's entire compute environment,
  `results/environment_manifest.json`) - `torch.manual_seed()` alone is
  sufficient for CPU determinism given fixed thread count
  (`torch.set_num_threads(4)`, already standard practice in every trainer
  in this project). No `torch.use_deterministic_algorithms()` call was
  added, since CPU Conv1d/Linear/BatchNorm1d forward+backward are already
  deterministic in PyTorch without it; this was not empirically
  stress-tested beyond the reproduction probe and the bounded retraining
  diagnostic in this sprint.
- If this project ever trains on CUDA, `seed_for_model_init` already calls
  `torch.cuda.manual_seed_all`, but full CUDA determinism additionally
  requires `torch.backends.cudnn.deterministic = True` - not added here
  since it's not applicable to the current CPU-only pipeline; flagged for
  whoever first trains on GPU.

## Historical scripts are UNCHANGED

`ml/train_sleep_edf_eeg_eog_ablation.py`,
`ml/train_sleep_edf_shuffled_eog_control.py`, and
`ml/train_sleep_edf_interaction_resp.py` are left exactly as they were -
they remain an accurate historical record of the actual (buggy) order
that produced every existing checkpoint. Editing them in place would
itself be a form of "rewriting old artifacts as if nothing happened,"
which this remediation explicitly avoids. The corrected protocol lives
only in the new `ml/sleep_seed_utils.py` module and any new
`*_seedfix_v2.py` script that uses it.

## What corrected training looks like

`ml/train_sleep_edf_primary_seedfix_v2.py` - the Day-12 bounded
retraining diagnostic for primary A/B (see
`results/sleep_scientific_remediation_day12.json` for the outcome). Any
future Sleep-EDF training should follow this same pattern (import
`ml/sleep_seed_utils.py`, seed before construction) rather than the old
scripts' order.
