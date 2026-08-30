# BIOLOGICAL MINIMALISM — TECHNICAL HANDOFF v2

## IAC 2026 | System Architecture, Sensor Decisions, Data Fusion, Repository Status, and Next Research Steps

**Purpose of this document:**
This file is a self-contained technical handoff for any AI or team member working on
the Biological Minimalism project. It reflects the latest sensor/system decisions, the
two internal technical guides, the accepted abstract, and a direct inspection of the
current GitHub repository.

**Important status rule:**
Do not treat the dashboard demo as the scientific validation. The dashboard is a
demonstrator. Scientific claims must come from real, labeled data, properly designed
experiments, ablation, robustness tests, and clearly stated limitations.

> **Provenance note (added by the assistant integrating this document, not part of the
> original handoff):** This file is reproduced as received from the team. Section 16
> ("Current GitHub Repository — Verified Status") is the reviewer's own independent
> inspection and is substantially accurate; two of its sharpest claims were
> re-independently confirmed by reading the live code before this document was
> committed (`TorchInferenceEngine` not calling `self.model(...)`, and the
> `fused.mean(dim=1)` masking gap). One claim (§16.9, a duplicate `backend/frontend/`
> folder) was checked against the current repository and found **not present** —
> likely a stale snapshot on the reviewer's side; no action was taken on it. See
> `docs/PDD_Biological_Minimalism_IAC2026.md` Section 20 and
> `Biological_Minimalism_IAC2026_Master_Project_Plan.md`'s Phase 13 block for how this
> document's priorities are being tracked against actual repo changes.

---

# 1. PROJECT IN ONE SENTENCE

**Biological Minimalism asks: what is the smallest practical wearable sensing
architecture that can preserve useful astronaut-health inference performance when AI,
signal quality control, sensor fusion, personalization, and analytical redundancy are
used intelligently?**

The central research contribution should **not** be "we chose 4 sensors."

The stronger contribution is:

> **We evaluate the marginal information value of candidate sensing channels against
> operational cost and derive a Pareto-efficient architecture empirically.**

Operational cost should include more than raw sensor count:
- number of skin-contact regions,
- number of wearable modules,
- power,
- mass,
- computational cost,
- wearing/maintenance burden,
- robustness cost.

A chest patch containing ECG + BioZ + IMU is not equivalent, operationally, to three
separate wearable devices.

---

# 2. ACCEPTED ABSTRACT — ORIGINAL BASELINE

The accepted abstract currently describes a minimal suite of:

- EEG
- PPG
- peripheral thermistor
- bio-impedance

and claims inference of:
- autonomic balance,
- cognitive workload,
- fatigue,
- circadian stability,
- cardiovascular dynamics,
- cuffless blood pressure,
- respiration,
- fluid-shift risk.

The project has evolved technically after the abstract. Small architecture changes are
therefore being considered, but the final paper must clearly distinguish:
1. what the abstract originally proposed,
2. what was modified during engineering,
3. what was actually implemented and validated.

Do **not** preserve an old sensor list merely because it was in the abstract if the
later engineering analysis shows that another architecture is more defensible.

---

# 3. LATEST SENSOR / CHANNEL DECISIONS

## 3.1 ECG — ADD, if cardiovascular targets remain

**Decision: YES.**

Reason:
- reliable HR/HRV timing,
- ECG + PPG enables PAT,
- BioZ/ICG + ECG can support cardiac timing features,
- analytical redundancy for heart-rate-related outputs,
- potentially improves experimental cuffless-BP trend estimation.

Important correction:

> ECG is **not "free"** just because a chest patch already exists.

It may avoid opening a new wearable region, but still requires electronics, analogue
front-end design, protection/isolation, validation, and interference management with
BioZ.

### Scientific language
Do not claim:
> "ECG makes cuffless blood pressure solved."

Prefer:
> "ECG enables physically meaningful cardiac timing features such as PAT;
> blood-pressure output remains an experimental, personalized trend estimate requiring
> calibration and reference validation."

---

## 3.2 IMU — ADD, but classify it correctly

**Decision: YES.**

IMU is primarily:
- motion-artifact reference,
- activity/context channel,
- signal-quality support,
- sleep/activity timing support.

A wrist IMU is especially valuable for PPG because motion can create false optical
pulsations. A chest IMU can help evaluate ECG/BioZ signal quality and physical
activity.

### Important design distinction

IMU should not automatically be counted as an additional "physiological modality" in
the Biological Minimalism claim.

Better taxonomy:

**Physiological sensing channels**
- EEG
- ECG
- PPG
- BioZ
- skin temperature

**Context / artifact-reference channels**
- IMU
- light
- cabin CO₂
- ambient temperature/humidity

This distinction matters for the paper and for Pareto analysis.

---

## 3.3 Light sensor — ADD if circadian target remains

**Decision: YES, as a context channel.**

Circadian inference without actual light exposure is weaker because light is a major
external driver of circadian phase.

Light is attractive because it has:
- low mass,
- low power,
- no new skin-contact region,
- high contextual information value.

Do not necessarily make "light" a full CNN/Transformer physiological token. It may be
better represented as a low-frequency context feature.

---

## 3.4 Temperature — KEEP single skin-temperature channel for v1

**Decision: DO NOT claim validated core temperature in v1.**

Single thermistor:
- useful for skin temperature,
- useful for personal thermal trend,
- not equivalent to core-body temperature.

A true dual-heat-flux/core-temperature design requires:
- controlled thermal geometry,
- known thermal resistance,
- ambient measurement,
- reference validation.

Therefore:

**v1:** skin temperature / personal thermal trend
**future:** validated core-temperature estimation if a proper dual-heat-flux system is
built.

---

## 3.5 Leg BioZ — EXPERIMENTAL / ABLATION CANDIDATE

Fluid shift is a redistribution phenomenon. Regional comparison can be more
informative than a single thoracic measurement.

However a leg BioZ module:
- opens another contact region,
- increases operational burden,
- must therefore earn its place through measurable marginal information.

Recommended status:
> Experimental candidate used in analog/literature-based analysis or ablation;
> promoted into the final architecture only if the added information justifies the
> extra contact region.

Do not present a universal `leg/chest BioZ ratio` as a clinically validated
fluid-shift index unless independently validated.

---

## 3.6 EEG — IMPORTANT, but continuous use is a design choice

EEG preserves the project's cognitive dimension:
- workload,
- vigilance,
- fatigue,
- selected sleep-state information.

However continuous EEG may impose:
- contact burden,
- motion artifacts,
- power burden,
- comfort issues.

Possible architecture:
- continuous only if continuous cognitive monitoring is essential,
- otherwise scheduled/intermittent EEG during critical tasks, cognitive tests, fatigue
  suspicion, or selected sleep periods.

This should be treated as an optimization variable rather than an unquestioned
assumption.

---

# 4. CANDIDATE PHYSICAL ARCHITECTURE

## Module A — Chest patch
Possible channels:
- ECG
- thoracic BioZ / ICG
- IMU

Primary outputs/features:
- HR,
- HRV,
- respiration-related features,
- thoracic impedance trend,
- ECG timing reference,
- selected ICG/PEP features if signal quality permits.

## Module B — Wrist / finger
Possible channels:
- red / infrared PPG
- IMU
- skin temperature
- light exposure

Primary outputs/features:
- pulse waveform,
- perfusion features,
- SpO₂ if hardware/data support it,
- PAT together with ECG,
- motion context,
- thermal trend,
- light exposure.

## Module C — Frontal headband
Possible channels:
- low-channel EEG
- local signal-quality/contact information
- optional local IMU

Primary outputs:
- workload,
- vigilance,
- fatigue,
- selected sleep/cognitive sessions.

## Optional Module D — Leg
- segmental BioZ
- experimental fluid-redistribution validation

## Cabin context
Possible channels:
- CO₂
- ambient temperature
- humidity
- light

These should be reported separately from the wearable "biological sensor" burden.

---

# 5. DATA FUSION — SIMPLE DEFINITION

Data fusion is **not** "concatenate every sensor file and train one giant model."

Correct conceptual pipeline:

```text
Sensor / replay source
        ↓
Timestamped data
        ↓
Synchronization
        ↓
Modality-specific preprocessing
        ↓
Signal-quality score q_i(t)
        ↓
Windowing / physiological features / embeddings
        ↓
Target-appropriate fusion
        ↓
Temporal / personalized model
        ↓
Prediction + uncertainty
        ↓
Digital-twin deviation / warning logic
```

Each sensor has its own sampling rate and noise characteristics. They do not need to
be forced into one identical raw sampling rate, but their time relationship must be
known.

This is especially critical for ECG–PPG timing measurements such as PAT.

---

# 6. QUALITY-AWARE FUSION

Each channel should produce a dynamic quality score:

`q_i(t) ∈ [0,1]`

Conceptually:

```text
q_i(t) = Quality(
    SNR,
    contact,
    motion,
    saturation,
    waveform morphology,
    missing samples,
    timing integrity
)
```

A degraded PPG channel should not be trusted equally with a clean ECG channel.

Possible intermediate-fusion form:

`e_fused = Σ α_i e_i`

with fusion weight influenced by both:
- learned target relevance,
- current signal quality.

**Important:** attention weight is not proof of causality or physiological
importance.

---

# 7. RECOMMENDED MODEL STRATEGY

Do not use "CNN + RNN + Transformer" simply because the accepted abstract named them.

The later engineering review correctly warns that a large chain may be unnecessary and
may overfit small heterogeneous datasets.

Recommended progression:

### Baseline 1 — explainable physiological features
Examples:
- ECG R–R intervals / HRV,
- PPG pulse timing and morphology,
- EEG band powers,
- BioZ baseline/trend,
- IMU motion energy,
- temperature/light trends.

### Baseline 2 — conventional ML
Depending on target:
- linear / regularized regression,
- random forest / gradient boosting,
- logistic classifier,
- simple MLP.

### Temporal model
If data support it:
- Kalman/state-space model,
- small GRU/LSTM.

### Transformer
Use as a **comparison or final fusion architecture only if enough truly synchronized
multimodal data exist** and subject-level validation is possible.

A more complex model is not automatically a better scientific result.

---

# 8. ABSOLUTE RULE FOR DATASETS

## DO NOT fabricate multimodal subjects.

Forbidden operation:

```text
EEG from Subject A / Dataset A
+
PPG from Subject B / Dataset B
+
BioZ from Subject C / Dataset C
=
fake multimodal "astronaut"
```

That is not valid sensor fusion.

Different datasets can be used to validate **different target-specific subproblems**,
but absent channels must not be invented.

### Valid uses of separate datasets
- pretrain an EEG encoder on an EEG dataset,
- validate PPG+IMU motion robustness on a synchronized PPG+IMU dataset,
- validate ECG+PPG timing/BP-related features on a synchronized ECG+PPG/reference
  dataset,
- validate BioZ fluid-status sensitivity on a BioZ dataset.

### What is still required for a real fusion claim
At least some experiments must contain the relevant modalities **simultaneously in
the same subject/session**.

A Transformer trained only on disjoint single-modality datasets cannot demonstrate
learned cross-modal relationships.

---

# 9. TARGET-FIRST DATASET STRATEGY

Search by **target and ground truth**, not just by sensor name.

For every candidate dataset record:

```text
Dataset name:
Subjects:
Population:
Signals:
Which signals are simultaneous:
Sampling rates:
Ground-truth labels:
Target(s) we can honestly evaluate:
Subject-level split possible:
License/access:
Space relevance:
Known domain gap:
Which ablation can this dataset support:
```

## High-priority roles already identified

### PPG-DaLiA
Priority role:
- PPG + IMU,
- motion-artifact / heart-rate robustness,
- IMU ablation.

Why it matters: BIDMC is useful for PPG→HR/respiration, but does not provide the
motion context needed to prove the "IMU helps motion-corrupted PPG" claim.

### BIDMC
Useful for:
- PPG heart-rate estimation,
- PPG respiration experiment.

Not sufficient for:
- PPG motion-artifact correction / IMU ablation.

### Sleep-EDF
Useful for:
- EEG pathway / sleep-stage-related proof-of-concept.

Not sufficient by itself for:
- full multimodal cognitive fusion.

### QDE
Useful for:
- real BioZ + temperature fluid-status-related analysis.

Limitation:
- dehydration ≠ microgravity fluid redistribution.

### PulseDB / other synchronized ECG+PPG+BP datasets
Potentially useful for:
- ECG+PPG timing,
- blood-pressure-related experiments,
- cardiovascular ablation.

Loader and access must be verified before relying on it.

### WESAD
Potentially valuable because it includes synchronized wearable channels and stress
labels.

Current repository loader is not implemented. Access/source must be re-verified.

---

# 10. ABLATION — PRIMARY RESEARCH RESULT

Ablation means:

> Remove one channel or channel group, repeat evaluation, and measure how much
> performance / uncertainty / robustness changes.

For each target:

`ΔPerformance(sensor_i) = Performance(full) − Performance(without sensor_i)`

But do not reduce the project to a single accuracy number.

Measure:
- MAE/RMSE for regression,
- F1/AUROC/calibration for classification,
- uncertainty increase,
- failure robustness,
- compute cost,
- power estimate/measurement,
- contact-region cost,
- mass,
- maintenance burden.

The final output should be a **target × channel marginal-contribution matrix**.

Example structure:

| Candidate channel | HR | BP trend | Workload | Fatigue | Circadian | Fluid |
|---|---:|---:|---:|---:|---:|---:|
| ECG | | | | | | |
| PPG | | | | | | |
| BioZ | | | | | | |
| EEG | | | | | | |
| Skin Temp | | | | | | |
| IMU/context | | | | | | |
| Light/context | | | | | | |

**Important:** IMU and light may be reported separately as context/artifact channels
rather than equivalent physiological sensors.

---

# 11. PARETO SENSOR SELECTION

Do not pre-announce a final sensor number.

For candidate set `S`, conceptually optimize:

`Utility(S) = Performance(S) − λP·Power(S) − λM·Mass(S) − λC·Contact(S) − λR·Risk(S)`

Better still, report a Pareto frontier rather than hiding the trade-off inside one
arbitrary weighting.

A sensor combination is Pareto efficient if no other combination is:
- more accurate/robust,
- while simultaneously cheaper/lighter/less burdensome.

The final architecture should emerge from this analysis.

---

# 12. FAULT-INJECTION / ROBUSTNESS MATRIX

The current demo only has coarse states such as nominal/degraded/offline.

Research-grade tests should include:

- complete channel dropout,
- temporary packet loss,
- frozen signal,
- random noise,
- motion artifact,
- saturation/clipping,
- delayed packet bursts,
- timestamp offset,
- clock drift between modules,
- sensor recovery after failure,
- inconsistent redundant channels.

Expected system behavior:

1. quality score drops,
2. unreliable channel is down-weighted or masked,
3. uncertainty increases,
4. remaining channels carry the estimate if possible,
5. if confidence becomes unacceptable, output **"reliable measurement unavailable"**
   instead of inventing certainty.

A robust system should not keep the same confidence when a critical sensor
disappears.

---

# 13. RECORDED-DATA LIVE REPLAY

Recommended software architecture:

```text
DataSource
 ├─ SyntheticSource        (current demo)
 ├─ DatasetReplaySource    (next)
 └─ RealSensorSource       (future)
          ↓
 same preprocessing/fusion/API/dashboard path
```

Dataset replay should preserve timestamps and feed recorded real data as if samples
were arriving live.

This allows demonstration of:
- streaming,
- packet loss,
- delay,
- sensor dropout,
- recovery,
- real-time dashboard behavior,

without falsely claiming a real wearable prototype exists.

Replay validates software logic, not full real-time hardware timing.

---

# 14. DIGITAL TWIN — WHAT COUNTS

A true project-level "digital twin" should not be merely a fixed Day-1-to-Day-30
animation.

Minimum defensible formulation:

1. establish a personal baseline,
2. track current state relative to that baseline,
3. update slowly during stable periods,
4. track uncertainty / data quality,
5. detect multivariate deviations.

Single-variable standardized deviation:

`z_i(t) = [x_i(t) − μ_i] / σ_i`

Adaptive baseline:

`μ_t = (1−λ)μ_(t−1) + λx_t`

For multiple correlated features, Mahalanobis distance can be used.

Do not allow an acute abnormal event to be instantly absorbed into the "new normal."

---

# 15. SPACE / MICROGRAVITY SIMULATION — ALLOWED CLAIM

Literature-based physiological perturbations can be introduced as a
**sensitivity-analysis layer**.

Correct claim:

> "We characterized how model performance changes under literature-informed or
> parameter-swept spaceflight-analog perturbations."

Incorrect claim:

> "We generated microgravity data ourselves and therefore proved the system works in
> space."

Do not validate a model using only the same synthetic transformation rules that
created its test data and then call that independent spaceflight validation.

Use two categories:

### Literature-grounded perturbations
Parameters with defensible published ranges.

### Uncertain perturbations
Unknown effects represented as parameter sweeps.

Output:
- performance vs perturbation magnitude,
- uncertainty vs perturbation,
- which sensor pathways fail first,
- which sensor configurations are most robust.

---

# 16. CURRENT GITHUB REPOSITORY — VERIFIED STATUS

Repository inspected: `ProfIsmeet/biological-minimalism`

## 16.1 Dashboard / backend
Strongly developed:
- Next.js frontend,
- FastAPI backend,
- WebSocket live feed,
- mission-mode demo,
- sensor-failure demo,
- digital-twin visualization,
- SHAP machinery,
- Docker setup.

The dashboard is a useful demonstrator.

## 16.2 Dashboard data is synthetic
`backend/app/engine/mock_data_engine.py` generates synthetic telemetry.

`backend/app/engine/physiology.py` uses hand-specified, literature-inspired demo
formulas.

Current base sensor weights are manually specified:

```python
ppg = 0.41
eeg = 0.35
temperature = 0.14
bioimpedance = 0.10
```

These are **not empirical ablation results**.

Therefore the dashboard's current sensor-contribution visualization is demonstrator
logic, not a scientific discovery.

## 16.3 Current SHAP interpretation
The SHAP computation may be mathematically genuine, but it currently explains the
transparent rule-based demo function.

It does **not** explain a trained multimodal neural network.

Important correction: Simply replacing the four static weights with ablation-derived
values would reduce one arbitrary part of the demo, but would **not by itself
transform the rule engine into a learned physiological model**.

Ablation contributions are also:
- target-specific,
- dataset-specific,
- sometimes context-specific,
- not necessarily valid as one global static weight vector.

## 16.4 ML code is not "empty," but the core fusion result is unfinished
Implemented:
- `bidmc_ppg.py`
- `sleep_edf.py`
- `qde_bioimpedance.py`
- `train_ppg.py`
- `train_sleep_edf.py`
- `train_bioimpedance.py`
- CNN encoders
- Transformer fusion architecture

Still scaffold / incomplete:
- `ml/ablation.py` raises `NotImplementedError`
- `wesad.py` raises `NotImplementedError`
- `stew.py` raises `NotImplementedError`
- `pulsedb.py` raises `NotImplementedError`
- `osdr.py` raises `NotImplementedError`
- full multimodal `BiologicalDigitalTwinNet` has not been jointly trained
- no full-network checkpoint is present in the repository.

The repository documentation reports previous real per-modality experiments:
- EEG/Sleep-EDF: 72.6% held-out sleep-stage accuracy in the documented run,
- PPG/BIDMC: HR MAE 8.72 bpm in the documented run; respiration result worse than
  naive baseline,
- BioZ/temp/QDE: 0.454 L MAE vs 0.414 L naive baseline, a null/slightly negative
  result.

Those are **per-modality proof-of-concept experiments**, not a validated multimodal
fusion result.

## 16.5 Documentation contradiction
The PDD contains both:
- a section stating three per-modality paths were trained,
- a limitations bullet stating "No model has been trained."

This must be rewritten.

Correct wording should be approximately:

> "Several per-modality proof-of-concept models were trained on real public datasets;
> however, the complete multimodal fusion network has not yet been jointly trained or
> validated."

## 16.6 Torch inference is not actually wired to model forward
`TorchInferenceEngine` loads a checkpoint, but its current
`confidence_and_contribution()` method does not run `self.model(...)` over real
buffered sensor windows. It falls back to the current dashboard snapshot.

Therefore:

> checkpoint loading exists, but real trained-model → live-dashboard inference
> integration is incomplete.

## 16.7 Modality masking has a pooling problem
The Transformer uses a key-padding mask, but after encoding the code currently
performs:

```python
fused.mean(dim=1)
```

over all modality-token positions.

For rigorous missing-modality ablation, use:
- masked mean pooling,
- or a dedicated fusion/CLS token,
- or another pooling strategy that excludes missing-token positions.

This should be fixed before trusting modality-dropout results.

## 16.8 Current code is still on the old architecture
Current `MODALITIES`:

```python
("eeg", "ppg", "temperature", "bioimpedance")
```

The latest design decisions (ECG, IMU, light/context) have not been integrated.

But **do not simply add every new channel to `MODALITIES` blindly**.

First decide software roles:

### Core physiological modality tokens
Possible:
- EEG
- ECG
- PPG
- BioZ
- temperature

### Context / quality inputs
Possible:
- IMU
- light
- CO₂
- ambient conditions

Some context channels may enter through a context encoder or feature vector instead
of one equal Transformer token.

## 16.9 Duplicate frontend
`backend/frontend/` and root `frontend/` are byte-for-byte identical in the inspected
ZIP.

Keep one source of truth and remove/archive the duplicate after confirming deployment
configuration.

---

# 17. RECONCILIATION OF TWO REPO REVIEWS

## Statement: "There are two separate projects: dashboard and research."
**Mostly correct.**

The dashboard and ML research path are currently weakly integrated. However the ML
side is not merely empty scaffolding: several real data loaders/training scripts and
documented per-modality experiments exist.

Better summary:

> **The demonstrator is mature; per-modality research has begun; the central
> multimodal fusion + ablation + empirical architecture-selection result is still
> incomplete.**

## Statement: "Every dashboard number is made up."
**Essentially correct for the live demo outputs**, but use precise wording:

> They are synthetic/demo outputs generated from stochastic signals and
> hand-specified equations, not empirical subject measurements.

## Statement: "SHAP is circular."
**Correct concern, with nuance.**

SHAP is genuinely computing attributions, but currently explains a manually designed
rule engine. It does not independently discover the scientific importance of
PPG/EEG/etc.

## Statement: "Replace the 0.41/0.35/etc. weights with ablation contributions and SHAP
## becomes scientific."
**Too strong.**

Better:
- empirical ablation can replace arbitrary contribution priors,
- but SHAP remains an explanation of whatever model/function it is applied to,
- marginal sensor importance should be target-specific and should not automatically
  become one universal global weight vector.

## Statement: "Do not spend another day on the dashboard."
**Directionally correct, but too absolute.**

Do not spend time on cosmetic redesign.

Do spend engineering time on:
- real dataset replay,
- model/API integration,
- research-grade fault injection,
- uncertainty display,
- experiment controls,
- results visualization.

The dashboard should become a **research instrument**, not merely a prettier
interface.

## Statement: "Add ECG and IMU to MODALITIES immediately."
**Needs refinement.**

ECG should likely become a physiological modality if relevant targets remain.

IMU should definitely enter the software pipeline, but primarily as context/artifact
reference.

Light should enter if circadian inference remains, but likely as context rather than
equal physiological modality.

Architecture should be decided before changing the tuple.

## Statement: "PPG-DaLiA should be the first new dataset."
**Strong recommendation for the PPG motion-artifact/IMU question.**

It is a much better experimental fit than BIDMC for:
- motion corruption,
- PPG+IMU synchronization,
- IMU ablation.

Source/access and exact protocol should still be verified before paper use.

---

# 18. IMMEDIATE PRIORITIES

## Priority 0 — Freeze terminology and sensor taxonomy
Before changing code, decide:
- physiological modality,
- context channel,
- contact region,
- wearable module,
- experimental channel.

This prevents "7 sensors vs 4 sensors" confusion.

## Priority 1 — Dataset research
Build a verified target-first dataset table.

Highest-value missing experiments:
1. PPG + IMU under movement.
2. ECG + PPG (+ reference BP/cardiac timing if available).
3. synchronized multimodal cognitive/stress dataset.
4. BioZ fluid-status / analog evidence.
5. circadian/light/actigraphy evidence if that target is retained.

## Priority 2 — First real ablation result
Start with one clean question:

> **How much does synchronized IMU improve PPG-derived heart-rate estimation under
> motion?**

This is narrow, measurable, and directly supports one architecture decision.

## Priority 3 — Implement research-grade ablation framework
Not only "sensor present/absent."

Support:
- target-specific metrics,
- missing modality,
- noise,
- motion artifact,
- delay,
- clock drift,
- uncertainty delta.

## Priority 4 — Refactor real-time data source
Create:

```text
SyntheticSource
DatasetReplaySource
FutureRealSensorSource
```

all behind one common interface.

## Priority 5 — Fix model masking / pooling
Do this before interpreting sensor-dropout results.

## Priority 6 — Real inference adapter
`TorchInferenceEngine` must eventually:
- maintain/receive synchronized raw windows,
- preprocess them,
- create modality/context inputs,
- run `model.forward`,
- return predictions + uncertainty,
- expose them to the dashboard.

## Priority 7 — Pareto analysis
Only after real target-specific experimental results exist.

---

# 19. TEAM OWNERSHIP — SUGGESTED

## Furkan
- physiology,
- spaceflight adaptation literature,
- target definitions,
- sensor biological justification,
- paper physiology/space sections.

## İsmet
- ML models,
- model training,
- evaluation,
- encoder/fusion architecture,
- checkpoint production,
- uncertainty/calibration implementation.

## Emir
- dataset scouting and provenance,
- data-source architecture,
- dataset replay,
- fault injection,
- experiment orchestration,
- ablation reporting pipeline,
- model ↔ backend integration,
- digital-twin software logic,
- dashboard research mode,
- Pareto/result visualization.

This gives Emir a substantial technical role without duplicating İsmet's training
work.

---

# 20. CLAIMS THE PAPER MAY / MAY NOT MAKE

## Defensible after proper experiments
- "We evaluated candidate sensor/channel contributions on real labeled public
  datasets."
- "We quantified performance degradation under specific missing-sensor/noise
  scenarios."
- "We derived a Pareto-efficient candidate architecture under stated cost
  assumptions."
- "We implemented a replayable real-time software architecture."
- "We characterized sensitivity to literature-informed spaceflight-analog
  perturbations."
- "We developed a personalized baseline/deviation framework."

## Do NOT say without evidence
- "The system is ready for spaceflight."
- "The model is clinically validated."
- "The dashboard proves medical accuracy."
- "Our synthetic microgravity data proves performance in microgravity."
- "One global SHAP weight proves sensor importance."
- "Four/six sensors are objectively optimal" before a real Pareto analysis.
- "90% power reduction" unless supported by a transparent measured/calculated power
  budget.

---

# 21. NEXT DECISION GATE

Before major code changes, answer these questions with verified dataset research:

1. Which final health targets remain in the paper?
2. For each target, what is the ground truth?
3. Which synchronized modalities are actually available in public data?
4. Which architecture decisions can be experimentally tested in two weeks?
5. Which decisions will remain literature/design proposals rather than validated
   results?
6. Which context channels (IMU/light/CO₂) should affect quality/fusion but not be
   counted as core physiological modalities?
7. What is the smallest set of experiments that can produce a defensible
   ablation/Pareto result?

**Recommended next action:** perform a focused public-dataset + literature search
before rewriting the fusion architecture.

---

# 22. ONE-SENTENCE TECHNICAL NORTH STAR

> **Do not optimize the dashboard for looking like a finished medical product;
> optimize the system for producing traceable, reproducible evidence about which
> synchronized sensing channels add information, when they fail, and what minimal
> architecture survives the accuracy–robustness–burden trade-off.**
