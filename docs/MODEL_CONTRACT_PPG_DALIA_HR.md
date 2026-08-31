# Model Contract — PPG-DaLiA Heart-Rate Model (Priority 2)

**Purpose:** everything an integration engineer (Emir) needs to run the
trained Priority 2 model against a live/replayed PPG+IMU stream, without
reading or reverse-engineering the training code. Every value below is taken
directly from the actual code and saved artifacts — nothing here is inferred
or estimated.

**Source of truth this document was built from:**
- `ml/train_ppg_dalia_imu_ablation.py` (model classes, forward signatures)
- `backend/app/ml/models.py` (`Conv1DEncoder`, `ModalityFusionTransformer`)
- `ml/datasets/ppg_dalia.py` (windowing/synchronization/preprocessing constants)
- `ml/experiments/ppg_dalia_imu_ablation/{config.json,subject_split.json,results.json}`
- `results/ppg_dalia_imu_ablation.json` (the full machine-readable record)
- Commit `d257f196f736e281a671fcc117781331034db1eb`

---

## 1. Model identity

**Recommended model for integration: Model B — PPG + synchronized IMU.**
This is the model that was actually validated to help (Section 2's result);
Model A (PPG-only) and Model C (shuffled-IMU negative control) are the
scientific comparison points, not integration targets.

| Field | Value |
|---|---|
| Model class | `PPGPlusIMUHRModel` (`ml/train_ppg_dalia_imu_ablation.py`) |
| Checkpoint path (local, gitignored) | `ml/checkpoints/model_b_ppg_plus_imu_ppg_dalia.pt` |
| Checkpoint format | `torch.save(model.state_dict(), path)` — a raw `state_dict`, **not** a full pickled model object. Loading requires reconstructing `PPGPlusIMUHRModel(embedding_dim=32)` first, then `model.load_state_dict(torch.load(path, map_location="cpu"))`. |
| Regenerate the checkpoint | `python ml/train_ppg_dalia_imu_ablation.py --save-checkpoints` (requires `ml/preprocess_ppg_dalia.py` to have been run first — see `datasets/ppg-dalia/README.md`) |
| Experiment/config file | `ml/experiments/ppg_dalia_imu_ablation/config.json` |
| Subject split file | `ml/experiments/ppg_dalia_imu_ablation/subject_split.json` |
| Producing commit | `d257f196f736e281a671fcc117781331034db1eb` |
| Framework | PyTorch `2.6.0+cpu`, Python `3.13.0` |
| DLL note (Windows) | Import `app.ml._torch_bootstrap.ensure_torch_dll_path()` **before** `import torch` — see that module's docstring for why. |

### Exact model definition (verbatim from `ml/train_ppg_dalia_imu_ablation.py`)

```python
class PPGPlusIMUHRModel(nn.Module):
    def __init__(self, embedding_dim: int) -> None:
        super().__init__()
        self.ppg_encoder = Conv1DEncoder(in_channels=1, embedding_dim=embedding_dim)
        self.imu_encoder = Conv1DEncoder(in_channels=3, embedding_dim=embedding_dim)
        self.fusion = ModalityFusionTransformer(embedding_dim=embedding_dim, n_heads=4, n_layers=1, n_modalities=2)
        self.head = nn.Linear(embedding_dim, 1)

    def forward(self, ppg: torch.Tensor, acc: torch.Tensor) -> torch.Tensor:
        ppg_emb = self.ppg_encoder(ppg)
        imu_emb = self.imu_encoder(acc)
        tokens = torch.stack([ppg_emb, imu_emb], dim=1)   # (batch, 2, dim)
        mask = torch.ones(ppg.shape[0], 2, dtype=torch.bool, device=ppg.device)
        fused = self.fusion(tokens, modality_mask=mask)
        return self.head(fused).squeeze(-1)
```

`embedding_dim = 32` (from `config.json`). `Conv1DEncoder` and
`ModalityFusionTransformer` are imported unmodified from
`backend/app/ml/models.py` — the same classes the dashboard's own
`BiologicalDigitalTwinNet` uses. **Note:** `ModalityFusionTransformer` was
generalized during this experiment to accept an explicit `n_modalities`
parameter (previously hard-coupled to the dashboard's global 4-modality
tuple); this is backward-compatible and does not affect any existing
dashboard code path (`backend/tests/test_models.py` covers both).

---

## 2. PPG input

| Field | Value |
|---|---|
| Dataset source channel | PPG-DaLiA `data['signal']['wrist']['BVP']` (Empatica E4 wrist device) |
| Original sample rate | 64 Hz |
| Model sample rate | 64 Hz (**no resampling** — the model consumes the native rate directly) |
| Window duration | 8.0 seconds |
| Samples per window | 512 |
| Tensor shape (single window) | `(1, 512)` — `(in_channels=1, sequence_length=512)` |
| Tensor shape (batch) | `(batch, 1, 512)` |
| dtype | `float32` |
| Channel ordering | Single channel — no ordering ambiguity |
| Required preprocessing before `forward()` | **Per-window z-score**: `(window - window.mean()) / window.std()`, computed fresh from the window itself (no stored training-set statistic to reuse for this input — see §5) |
| Expected numerical range after preprocessing | Approximately zero-mean, unit-variance (a standard-normal-shaped window); windows where the raw signal is flat (`std < 1e-8`) were **dropped** during training, not fed to the model — a live pipeline should apply the same rule (treat a flat/dead PPG window as "no valid input" rather than z-scoring noise) |

---

## 3. IMU input

| Field | Value |
|---|---|
| Dataset source | PPG-DaLiA `data['signal']['wrist']['ACC']` (Empatica E4 wrist accelerometer, same device as PPG) |
| Axes used | All 3 (x, y, z) — raw accelerometer axes, **not** a magnitude or engineered feature |
| Original sample rate | 32 Hz |
| Model sample rate | 32 Hz (no resampling) |
| Window duration | 8.0 seconds (same window as PPG — see §4) |
| Samples per window | 256 |
| Tensor shape (single window) | `(3, 256)` — `(in_channels=3, sequence_length=256)` |
| Tensor shape (batch) | `(batch, 3, 256)` |
| dtype | `float32` |
| Axis ordering | Whatever order PPG-DaLiA's own `ACC` array uses (x, y, z as distributed) — this project does not reorder or relabel axes |
| Required preprocessing before `forward()` | **Per-axis, per-window z-score**: each of the 3 axes independently mean-zeroed and unit-variance *within its own window* — `(seg[axis] - seg[axis].mean()) / seg[axis].std()` per axis, computed fresh from the window (no stored training statistic) |

---

## 4. Synchronization (read this section carefully — it is the part most likely to break silently)

**Rule:** for window index `i` (0-based), the absolute start time is:

```
t0 = i * step_seconds = i * 2.0 seconds  (from the start of the subject's recording)
```

Both PPG and IMU windows are **left-aligned at the same `t0`**, each sliced at
its own native sample rate for a duration of 8.0 seconds — there is no
resampling to a shared rate and no interpolation:

```python
ppg_start = round(t0 * 64.0);  ppg_end = ppg_start + 512
acc_start = round(t0 * 32.0);  acc_end = acc_start + 256
```

The real ground-truth HR label at the **same window index `i`** (from
PPG-DaLiA's own pre-computed `data['label']` array) is used as that window's
target — this project trusts PPG-DaLiA's own windowing convention for the
label rather than re-deriving it, and verified it directly against real data
before relying on it: for subject S1, `(recording_duration_s − 8) / 2 + 1 ==
len(label)` exactly (9212 s duration → 4603 labels, confirmed).

**What a live/replay pipeline must reproduce exactly:**
1. Advance the window index at a fixed 2.0-second step.
2. For each window, take exactly 512 PPG samples and exactly 256 IMU samples
   starting from the *same* elapsed-time offset `t0` — do not let PPG and IMU
   drift relative to each other (e.g. by buffering them independently on
   different timers without a shared clock).
3. Do not carry over the previous window's normalization — normalization is
   recomputed **fresh per window** (see §2, §3), so a window is a
   self-contained unit; the model has no hidden state between windows.
4. A window with a genuinely flat/dead PPG segment should be treated as "no
   prediction this window," matching the training-time drop rule, not fed
   into the model with degenerate (NaN or divide-by-zero) normalization.

**Boundary behavior:** during preprocessing, any window whose PPG or IMU
slice would run past the end of the available recording is dropped, not
padded. A live pipeline should do the same at the end of a session (do not
zero-pad a partial final window).

---

## 5. Preprocessing summary table

| Transformation | What | When | Parameters | Source of statistics |
|---|---|---|---|---|
| PPG z-score | Per-window normalization | Immediately before `forward()`, per window | mean/std of that window | **The window itself** (not training data) |
| IMU z-score | Per-axis, per-window normalization | Immediately before `forward()`, per window, per axis | mean/std of that window's own axis | **The window itself** (not training data) |
| HR target normalization | z-score of the model's *output* | Applied only when de-normalizing the model's output back to bpm (never applied to model *input*) | `mean=86.34466552734375`, `std=21.048254013061523` | **Training-set subjects only** (`S1,S10,S11,S12,S15,S3,S4,S6,S7,S8`) — never derived from validation or test subjects, per the project's own hard rule against evaluation leakage |

No filtering, clipping, detrending, or hand-engineered feature extraction is
applied anywhere in this pipeline — the model consumes (normalized) raw PPG
and IMU waveforms directly.

---

## 6. Output

| Field | Value |
|---|---|
| Raw `forward()` output shape | `(batch,)` — one scalar per window (already squeezed) |
| Raw output meaning | **Normalized** heart rate: `(true_hr_bpm − 86.34466552734375) / 21.048254013061523` |
| Converting to real bpm | `hr_bpm = raw_output * 21.048254013061523 + 86.34466552734375` |
| Output clipping | **None** — the model can output values outside a physiologically plausible range if given out-of-distribution input; no clamping is applied anywhere in the pipeline. An integration layer that wants a safety clamp must add it itself and should treat it as a UI/safety concern, not a property of the trained model. |
| One prediction per window? | Yes — exactly one HR estimate per 8-second/2-second-step window, no temporal smoothing across windows is applied by the model itself |

---

## 7. Confidence / uncertainty

**CURRENT MODEL DOES NOT PROVIDE VALIDATED PREDICTIVE UNCERTAINTY.**

`PPGPlusIMUHRModel.forward()` returns a single scalar per window. There is no
variance head, no ensemble, no dropout-at-inference, no calibrated confidence
score anywhere in this model or this experiment. Any "confidence" or
"uncertainty" shown in the dashboard for this model's predictions must not be
sourced from the model itself unless and until a real uncertainty mechanism
is implemented and validated — do not synthesize a plausible-looking
confidence percentage from e.g. per-subject or per-activity historical MAE
and present it as the model's own uncertainty for a specific live prediction.

---

## 8. Minimal inference example (real API, not pseudocode)

```python
import sys
from pathlib import Path

REPO_ROOT = Path("path/to/biological-minimalism")
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT))

from app.ml._torch_bootstrap import ensure_torch_dll_path
ensure_torch_dll_path()  # Windows DLL fix - must run before `import torch`

import numpy as np
import torch

from ml.train_ppg_dalia_imu_ablation import PPGPlusIMUHRModel

HR_MEAN = 86.34466552734375
HR_STD = 21.048254013061523

model = PPGPlusIMUHRModel(embedding_dim=32)
state_dict = torch.load(REPO_ROOT / "ml/checkpoints/model_b_ppg_plus_imu_ppg_dalia.pt", map_location="cpu")
model.load_state_dict(state_dict)
model.eval()


def preprocess_ppg(window_512_samples: np.ndarray) -> torch.Tensor:
    std = window_512_samples.std()
    if std < 1e-8:
        raise ValueError("flat/dead PPG window - do not feed to the model")
    normalized = (window_512_samples - window_512_samples.mean()) / std
    return torch.from_numpy(normalized.astype(np.float32)).view(1, 1, 512)  # (batch=1, ch=1, seq=512)


def preprocess_imu(window_3x256_samples: np.ndarray) -> torch.Tensor:
    # window_3x256_samples: shape (3, 256), axes = whatever order the source stream provides
    mean = window_3x256_samples.mean(axis=1, keepdims=True)
    std = window_3x256_samples.std(axis=1, keepdims=True)
    std[std < 1e-8] = 1.0
    normalized = (window_3x256_samples - mean) / std
    return torch.from_numpy(normalized.astype(np.float32)).view(1, 3, 256)  # (batch=1, ch=3, seq=256)


@torch.no_grad()
def predict_hr_bpm(ppg_window: np.ndarray, imu_window: np.ndarray) -> float:
    """ppg_window: 512 raw PPG samples @ 64 Hz, starting at the same t0 as imu_window.
    imu_window: (3, 256) raw accelerometer samples @ 32 Hz, same t0."""
    ppg_t = preprocess_ppg(ppg_window)
    imu_t = preprocess_imu(imu_window)
    raw_output = model(ppg_t, imu_t)  # normalized, shape (1,)
    return float(raw_output.item() * HR_STD + HR_MEAN)
```

---

## 9. Known limitations

- Trained and evaluated on PPG-DaLiA (terrestrial, free-living daily
  activities) — no astronaut or microgravity data or validation.
- Not clinically validated.
- Held-out test set is 3 subjects (`S14`, `S2`, `S9`) out of 15 total, from
  one seeded split (`seed=42`) — a different split could shift exact numbers,
  though the direction of the effect (IMU helps) held for all 3 test
  subjects individually.
- IMU's benefit did **not** monotonically increase with motion severity in
  this run (largest absolute gain was in the *lowest*-motion quartile) — do
  not build downstream logic that assumes "more motion → more IMU benefit."
- Per-activity results include one real negative case: during `table_soccer`
  activity, Model B (PPG+IMU) performed *worse* than Model A (PPG-only) —
  full breakdown in `results/ppg_dalia_imu_ablation.json`.
- No validated predictive uncertainty (§7) — do not present a fabricated
  confidence value alongside this model's predictions.
- This model estimates heart rate only. It says nothing about stress,
  fatigue, cognitive load, or any other target — do not reuse its output as
  a proxy for those without a separate, dedicated validation.
