# Biological Minimalism

## AI-Driven Minimal Sensor Architecture for Autonomous Astronaut Health Monitoring

### Project Design Document — IAC 2026

**77th International Astronautical Congress, Antalya, Türkiye — IAF/IAA Space Life Sciences
Symposium (A1), Interactive Presentation**
**Team:** Haydarpaşa Lisesi — F. Atila, E. H. Sünbül, I. Y. Virdil, P. Özdemir
**Document status:** Draft v1.0

> ⚠️ **Framing note (evidence-driven methodology in effect).** This PDD predates the
> current methodology and is preserved as the design-rationale document. Read it with
> these clarifications, which are authoritative:
> - The **four-sensor design** (EEG/PPG/temperature/BioZ) is a **design hypothesis /
>   proposed deployment**, not a validated or selected minimal set. The current
>   architecture-decision status is **`NOT_READY`**.
> - The **Information Density Index (IDI)** described in Section 1 is a **proposed,
>   superseded** metric — it was *not* adopted. The project deliberately refuses a
>   universal weighted scalar because it would embed arbitrary weightings across
>   incomparable burden dimensions. See `docs/OPERATIONAL_COST_METHODOLOGY.md`.
> - The **Biological Digital Twin** is architecture/reference code only — untrained,
>   with no validated checkpoint. Any "recover the picture of 12-sensor systems"
>   language is a **motivating research question**, not a demonstrated result.
> - **Current source of truth** for scientific evidence: the root `README.md`, the
>   research API (`backend/app/research/`), and the immutable `results/` artifacts.

---

> **How to read this document.** Every claim in this PDD is one of two kinds, and we
> label them explicitly rather than let them blur together: a **Proven / Literature-
> Supported** claim is backed by a citation to a real, checkable source (peer-reviewed
> paper, NASA/ESA technical document, or dataset release) listed in the References
> section. A **Design Proposal** is an engineering decision this project makes —
> an architecture choice, a coefficient, a UI convention — that is *informed by* the
> cited literature but not itself proven by it. Anywhere the distinction matters, the
> text says so in-line (e.g. "this is a design proposal, not a validated result").
> This document never cites a source we did not ourselves verify.

---

## Table of Contents

1. Executive Summary
2. Scientific Background
3. NASA EVA Biomedical Monitoring
4. Artemis and the Lunar Gateway
5. The Digital Twin Concept
6. Literature Review
7. Dataset Research
8. Bio-Impedance and Fluid Shift
9. Signal Processing Pipeline
10. CNN Architecture
11. Transformer Fusion Architecture
12. Adaptive Baseline — the Biological Digital Twin
13. Explainable AI
14. Ablation Study Design
15. Experimental Design
16. Dashboard Architecture
17. API Design
18. Risk Analysis
19. Five-Week Project Calendar
20. Limitations and Scope
21. References

---

## 1. Executive Summary

Long-duration human spaceflight — the International Space Station today, and the
Artemis-era return to the Moon and eventual Mars missions tomorrow — depends on
continuously knowing an astronaut's physiological state without a doctor in the room.
The dominant engineering answer to that problem has been to add sensors: multi-lead
ECG chest straps, finger pulse oximeters, respiration belts, cuff-based blood
pressure, dense multi-channel EEG caps, thermistors, and more, worn simultaneously
during high-risk activities such as extravehicular activity (EVA). Each additional
sensor adds redundancy and specificity, but it also adds skin contact area, donning
time, cognitive burden, mass, power draw, and failure surface — costs that compound
over a mission measured in months rather than hours.

**Biological Minimalism** is this project's proposed alternative framing: instead of
adding sensors to raise confidence, use a multimodal AI system to *raise the amount of
physiological information recovered per sensor*, and hold the sensor count fixed at
four low-burden modalities — wireless EEG, photoplethysmography (PPG), peripheral skin
temperature, and bio-impedance. We propose tracking this trade-off explicitly with an
experimental metric we call the **Information Density Index (IDI)**:

```
IDI = Recovered Physiological Information / Number of Active Sensors
```

This is a **design proposal**, not a validated metric from the literature — we
introduce it here as a way to make the sensor-count-versus-information trade-off
legible, and the project's own ablation study (Section 14) is where it would actually
be measured once real training data is in place.

The technical core of the proposal is a **Biological Digital Twin**: a per-astronaut
model that (1) fuses the four sensor streams with a 1D-CNN-per-modality encoder feeding
a Transformer cross-attention fusion layer (Sections 10–11), (2) learns an individual
physiological baseline over an initial calibration window and continues adapting to it
across the mission (Section 12), and (3) explains every output it produces with real,
computed SHAP (SHapley Additive exPlanations) attributions rather than an opaque score
(Section 13). Because the fusion layer treats each modality as a token that can be
masked, the same architecture is designed to degrade gracefully rather than fail
outright when a sensor goes offline — the basis of this project's "Sensor Failure
Simulation" demonstration.

This document has two purposes. First, it is the scientific design document behind a
prospective research paper: it separates what current literature actually supports
about minimal-sensor physiological monitoring from what this project proposes and
would need to validate. Second, it is the architecture specification for a working
software demonstrator — a NASA-Mission-Control-styled dashboard, built and verified as
part of this same effort (Sections 16–17), that runs entirely offline on a transparent,
documented synthetic data engine and shows the Digital Twin concept, three interactive
failure/adaptation demonstrations, and genuine SHAP-based explainability end to end.
**No real sensor, subject, or astronaut data is used anywhere in this deliverable** —
this is stated plainly here and repeated at every point in the document where it
matters, per this project's own transparency commitment (Section 20).

---

## 2. Scientific Background

### 2.1 Why spaceflight physiology is monitored at all

Microgravity and the broader spaceflight environment (isolation, altered light-dark
cycles, radiation, confinement, workload) perturb nearly every major physiological
system relevant to crew health and performance. Grigoriev and Egorov's review of
medical monitoring across the Soviet/Russian long-duration space program lays out the
historical rationale directly: monitoring exists because cardiovascular deconditioning,
fluid redistribution, vestibular disturbance, and psychological stress are
well-documented, mission-relevant risks that must be tracked operationally, not just
studied after the fact (Grigoriev & Egorov, 1997). Pool's earlier NASA-era review of
physiological measurement systems for advanced manned space missions makes the same
point from the engineering side: as mission duration and distance from Earth grow, the
monitoring system has to do more of its own signal interpretation, because
ground-based specialist review becomes slower and, eventually (for Mars-class
communication delays), impossible in anything resembling real time (Pool, 1975).

More recent reviews confirm this is still the central design tension for Artemis- and
Mars-class missions specifically. Gupta and Ghosh's 2025 review of health-monitoring
technologies for deep-space astronauts frames the requirement as monitoring systems
that must become progressively more autonomous, compact, and low-burden as missions
move further from Earth and near-real-time ground support becomes unavailable (Gupta &
Ghosh, 2025). DeVirgiliis et al.'s 2025 review of physiological monitoring and
countermeasures for a Mars-exploration "astronaut-athlete" concept makes a directly
analogous argument for the cardiovascular/musculoskeletal domain: monitoring needs to
be continuous, minimally burdensome, and actionable onboard, not just diagnostic after
return to Earth (DeVirgiliis et al., 2025).

### 2.2 The systems this project targets

Four physiological domains recur across this literature as both monitoring priorities
and as domains where the four sensors in this project (EEG, PPG, temperature,
bio-impedance) plausibly carry signal, and this PDD scopes its claims to these four
rather than the full space-medicine literature:

- **Autonomic and cardiovascular regulation.** Baevsky, Petrov, and Chernikova's work
  on autonomic nervous system regulation in space (including its interaction with
  geomagnetic/"magnetic storm" activity — directly relevant to this project's Solar
  Event mission mode, see Section 16) established heart-rate-variability-based
  autonomic assessment as an operationally used technique in the Russian space program
  (Baevsky, Petrov & Chernikova, 1998). McCorry's physiology-education review of the
  autonomic nervous system is the standard reference this project draws on for why HRV
  (specifically vagal/parasympathetic tone) is a meaningful, mechanistically grounded
  proxy signal rather than an arbitrary statistic (McCorry, 2007).
- **Cognitive workload and stress.** Multiple reviews in this space (Gupta & Ghosh,
  2025; Roda et al., 2018) identify cognitive workload and stress state as monitoring
  targets alongside cardiovascular status, motivating this project's inclusion of
  EEG-band-power-derived cognitive load and fatigue estimates (Section 9).
- **Fluid redistribution ("fluid shift").** The cephalad (head-ward) fluid shift caused
  by the absence of gravitational pooling in the legs is one of the best-established
  acute effects of microgravity exposure, and is the physiological target this
  project's bio-impedance channel is designed around (see Section 8 for the
  dataset-level evidence this project actually has access to for this specific
  target).
- **Thermal regulation.** Included as a lower-burden, high-value addition alongside PPG
  in this project's sensor design, consistent with Fei et al.'s EVA-focused biomedical
  sensor system, which likewise pairs cardiovascular sensing with temperature sensing
  in a single low-profile wearable package (Fei et al., 2010).

### 2.3 Advanced biosensor design context

Roda et al.'s review of advanced biosensors for astronaut health monitoring during
long-duration missions surveys the broader design space this project sits inside:
wearable, minimally invasive, low-power biosensing as a general engineering direction
for space medicine, independent of any one specific sensor modality (Roda et al.,
2018). Mundt et al.'s description of a multiparameter wearable physiological
monitoring system for space and terrestrial applications is a direct engineering
precedent for the idea of a single integrated wearable package carrying multiple
sensing modalities, which is the physical-form-factor assumption behind this project's
four-sensor design, even though this project does not build or validate physical
hardware (Mundt et al., 2005). Liu et al.'s 2026 work on model-data hybrid thermal
management and health monitoring for a space station fluid loop application is cited
here as a recent (2026) example of the same broader "hybrid model + real telemetry"
philosophy this project's Digital Twin follows, applied to a different subsystem
(thermal/fluid loop management rather than crew health) (Liu et al., 2026).

Section 4 below adds NASA's own recent human-system risk framing for exploration
missions: Antonsen et al.'s 2023 update to NASA's human system risk management
process names an "integrated network of biosensors" as one of the indispensable
requirements for the next generation of human spaceflight, alongside artificial
gravity and radiation shielding — the program-level risk framing this project's
sensor-minimization proposal sits inside, not a document that itself proposes
minimizing sensor count (Antonsen et al., 2023).

---

## 3. NASA EVA Biomedical Monitoring

Extravehicular activity (EVA) — spacewalking — is the single highest-workload,
highest-risk activity in current human spaceflight operations, and is historically
where the most instrumented, most sensor-dense biomedical monitoring has been deployed,
because the operational cost of missing a developing medical event during an EVA is
severe (loss of crew time at minimum, life-threatening at worst) and ground support has
essentially no ability to intervene physically.

Fei et al. describe a real-time biomedical sensor system built specifically for
monitoring astronauts' physiological parameters during EVA: a design explicitly
motivated by the need to track cardiovascular and thermal state continuously while an
astronaut is suited, isolated, and physically exerting at a level that makes
subjective self-report an unreliable safety signal on its own (Fei et al., 2010). This
is the most directly relevant EVA-biomedical-monitoring precedent this project draws
on, and it is worth being precise about what it does and does not establish: it
establishes that continuous, wearable, multi-parameter cardiovascular/thermal
monitoring during EVA is an established engineering pattern with real precedent — it
does *not* establish that a four-sensor minimal set can replace a denser EVA sensor
suite, which remains this project's own untested proposal (see Section 14, Ablation
Study).

Mundt et al.'s multiparameter wearable system, while not EVA-specific, is built to the
same underlying constraint set — wearable, low-power, multi-signal, suitable for
integration into a suit or garment — and is cited here as the closest available
engineering precedent for the *packaging* assumption behind this project's four-sensor
wearable concept (a single garment/headset combination rather than four separate
devices) (Mundt et al., 2005).

**Framing for this project.** NASA's own EVA medical monitoring practice is the
implicit "traditional, multi-sensor" baseline this project's Biological Minimalism
proposal argues against — not because the traditional approach is wrong (it exists for
good, literature-supported reasons, per Section 2), but because this project asks
whether a four-sensor subset, processed by a more capable fusion model, can recover
enough of the same operationally relevant signal to justify the very large reduction in
physical burden. This is stated here as the project's hypothesis, not as an established
result.

### 3.1 Current NASA EVA/ISS biomedical monitoring practice

NASA's own ISS blog documents current, real, denser-than-this-project's-proposal
biomedical monitoring practice directly. Ahead of and during spacewalk preparation,
crew undergo Ultrasound-based vein scans (checking internal jugular vein blood flow
and clot risk) and Optical Coherence Tomography eye exams, both reviewed by
ground-based flight surgeons in real time (NASA ISS Blog, 2026a). A separate 2026
post describes spacewalk-preparation health checks that now incorporate augmented
reality and artificial intelligence tooling (NASA ISS Blog, 2026b) — evidence that
NASA's own EVA-adjacent monitoring practice is itself moving toward more automated,
AI-assisted interpretation, the same general direction (more capable interpretation
software, not necessarily more sensors) this project's Biological Minimalism
proposal argues for, applied specifically to the sensor-count side of that trade-off
rather than the interpretation-software side NASA's own recent practice already
targets.

---

## 4. Artemis and the Lunar Gateway

The Artemis program (NASA's return-to-the-Moon campaign) and the Lunar Gateway
(the planned crew-tended outpost in lunar orbit) define the near-term mission context
this project frames itself against, for two concrete reasons that shape design
decisions in this document:

1. **Communication latency and crew autonomy.** Missions based around cislunar space
   (Gateway) still have communication delays measured in seconds, not the 4–24 minute
   one-way delays of a Mars mission, but Artemis is explicitly positioned as the
   proving ground for the more autonomous, less ground-dependent operations concepts
   that Mars-class missions will require (Gupta & Ghosh, 2025, discussed in Section
   2.1). This project's "Deep Space" and "Solar Event" mission modes (Section 16) are a
   direct, simplified dramatization of that autonomy requirement: as communication
   latency and operational isolation increase, the dashboard's design intent is that
   the system should surface *more* self-contained interpretation (via the AI
   Confidence and Explainable AI panels), not less.
2. **Mission duration and repeated exposure.** Lunar surface missions under Artemis are
   planned to be longer than typical ISS crew rotations in some mission profiles, and
   involve partial-gravity (lunar, ~1/6 g) rather than full microgravity — a distinct
   physiological regime from ISS operations that current open datasets (Section 7) do
   not directly cover. This project's "Lunar Surface" mission mode is explicitly a
   **design proposal / illustrative scenario**, not a claim that the mock engine's
   noise and risk parameters for that mode are derived from real lunar-partial-gravity
   physiological data — none exists yet in a form this project could access.

**What this project does not claim.** This document does not cite a specific Artemis
or Lunar Gateway human-health-monitoring requirements document as having been verified
against this project's own four-sensor design — that verification is future work.
Where this document names Artemis or Gateway, it is describing the mission context this
project is designed *for*, not citing a NASA requirements document that endorses this
project's specific architecture.

### 4.1 What NASA's own program documentation actually says

Antonsen et al.'s 2023 description of NASA's updated human system risk management
process states plainly that deep-space exploration missions require "an integrated
network of biosensors" alongside artificial-gravity countermeasures and radiation
shielding as indispensable supporting requirements, and separately notes that
Artemis-class missions will, for the first time since Apollo 17, take crew beyond
Earth's magnetic field, which materially changes the radiation and communication
picture monitoring systems must operate under (Antonsen et al., 2023). NASA's own
Artemis II mission page describes the ARCHeR (Artemis Research for Crew Health and
Readiness) study, which will track crew individual and team performance throughout
the mission, alongside a separate immune-biomarker study of how the immune system
responds to spaceflight, and a study of crew well-being, activity, and sleep patterns
specifically framed as building the human-health-and-performance evidence base for
deep space (NASA, Artemis II Science page). These are the real, current NASA program
facts this section is grounded in; this project's own four-sensor architecture and
its "Lunar Surface" / "Deep Space" mission-mode design (Section 16) remain this
project's own proposal, not something these NASA sources themselves specify or
endorse.

---

## 5. The Digital Twin Concept

"Digital twin" is used in two related but distinct senses in this document, and
conflating them would overstate what this project has built, so they are kept
separate here.

**Sense 1 — the general engineering concept.** A digital twin, in the broader
systems-engineering and industrial-IoT literature, is a live, data-fed virtual
representation of a physical asset or process that is kept synchronized with reality
and used for monitoring, prediction, and decision support. Liu et al.'s 2026 work on a
"model-data hybrid" approach to thermal management and health monitoring of a space
station fluid loop is, in this document's reading, an applied example of exactly this
pattern — a physical model combined with live telemetry to monitor and predict system
state — applied to spacecraft *hardware* rather than a *person* (Liu et al., 2026).
This project cites it as the closest available example, in the literature this project
actually reviewed, of the general "hybrid model + live data" digital-twin pattern
being applied inside a spaceflight engineering context, not as prior art for a
*biological* digital twin specifically.

**Sense 2 — this project's Biological Digital Twin.** This project's own contribution
is applying that same "hybrid model + live data, kept synchronized with an individual"
pattern to a *person's* physiology rather than to hardware: a per-astronaut model that
(a) is pretrained on general population/analog data (Section 7), (b) calibrates to an
individual's own baseline over an initial window (Section 12), and (c) continues
tracking deviation from that personalized baseline as the mission proceeds, explaining
its outputs via SHAP (Section 13). **This specific combination — CNN+Transformer
sensor fusion, individual baseline calibration, and real-time SHAP explainability,
applied to a four-sensor minimal astronaut monitoring set — is this project's own
design proposal.** No literature source reviewed for this document describes this
exact system; the individual pieces (sensor fusion architectures, personalized
baselining, SHAP explainability) each have their own literature, cited in the relevant
sections below (9–13), but their combination for this purpose is original to this
project.

No dedicated "digital twin applied to individual human physiology" precedent beyond
Liu et al.'s spacecraft-hardware example (Section 5, Sense 1, above) was found and
independently verified for this document; rather than cite a source this project has
not itself confirmed, this section states plainly that the Biological Digital Twin's
specific combination (Section 5, Sense 2) is presented as this project's own proposal,
with no claimed prior-art precedent for the combination itself.

---

## 6. Literature Review

This section consolidates, in one place, every source this document cites elsewhere,
organized by the question each source actually answers for this project. Full
bibliographic entries are in Section 21 (References); this section is the reading
guide, not a duplicate reference list.

**On why spaceflight physiological monitoring exists and what it must satisfy
operationally:** Grigoriev & Egorov (1997); Pool (1975); Gupta & Ghosh (2025);
DeVirgiliis et al. (2025).

**On EVA-specific biomedical sensing precedent:** Fei et al. (2010); Mundt et al.
(2005).

**On advanced/wearable biosensor design direction for space medicine:** Roda et al.
(2018).

**On autonomic nervous system regulation, HRV, and its space-relevant use:** Baevsky,
Petrov & Chernikova (1998); McCorry (2007); Kaya & Kaya (n.d., vagus-nerve/autonomic
perspective on physical activity — used in this document to support the
physiological plausibility of HRV as an autonomic-tone proxy, not as space-specific
evidence); Yaşa (n.d., exercise/neurobiology relationship — same use).

**On applied hybrid model+telemetry ("digital twin"-pattern) spacecraft engineering:**
Liu et al. (2026).

**On circadian rhythm in spaceflight (supporting this project's circadian-stability
metric, Section 9):** Kurt (n.d.).

**On current NASA EVA/ISS biomedical monitoring practice:** NASA ISS Blog (2026a,
2026b).

**On NASA's own human-system risk framing for Artemis-class exploration missions:**
Antonsen et al. (2023); NASA, Artemis II Science page.

**On the original datasets this project's future training work is scoped around:**
Schmidt et al. (2018, WESAD); Lim, Sourina & Wang (2018, STEW); Wang et al. (2023,
PulseDB); Goldberger et al. (2000, PhysioNet/PhysioBank); NASA OSDR (bed rest / dry
immersion, repository-level citation — see Section 7).

**On bio-impedance as a general fluid-measurement technique:** PubMed ID 10124463 (see
Section 8; author list not independently confirmed through an accessible source, so
cited by identifier rather than a guessed author name).

**On the explainability method this project actually runs:** Lundberg & Lee (2017,
SHAP).

Each of the first six clusters above was reused directly from this project's own prior
planning research (recorded in `Biological_Minimalism_Yol_Haritasi.md`, §13, this
repository), which this document treats as already-vetted for this specific claim set.
The remaining clusters were independently verified in a dedicated research pass for
this document (real-time web search against NASA, IEEE, ACM, Frontiers, and NeurIPS
sources, each fetched and confirmed rather than cited from memory). Two gaps this
research pass could not fill without guessing are stated as gaps rather than papered
over: a dedicated Transformer-for-multimodal-physiological-fusion application paper
(Section 11) and a dedicated personalized-calibration/few-shot-adaptation paper
specific to physiological monitoring (Section 12) — both sections say so explicitly
rather than citing an unverified source.

---

## 7. Dataset Research

No dataset is bundled with this repository (see `datasets/README.md`), and the working
dashboard deliverable (Sections 16–17) uses **only** a synthetic mock data engine —
this section documents the datasets a *future* training effort would use, and is
explicit about which of this project's claims those datasets can and cannot support
today.

| Target signal / task | Dataset | Fit to this project |
|---|---|---|
| Stress / autonomic balance (EDA, ECG, EMG, respiration, temperature, PPG) | **WESAD** — Wearable Stress and Affect Detection | General civilian population, controlled lab stressors. Directly relevant modalities (PPG, temperature) but no spaceflight or spaceflight-analog context. |
| Cognitive workload (EEG) | **STEW** — Simultaneous Task EEG Workload | General population, task-based EEG workload — directly supports this project's EEG-band-power cognitive-load approach (Section 9), no spaceflight context. |
| Cuffless blood pressure (PPG + ECG) | **PulseDB** / MIMIC-derived cuffless BP datasets | Clinical/hospital population — supports the PAT-style cuffless BP approach's *general validity as a technique* (Section 9), not its accuracy in a spaceflight-relevant population. |
| Respiration, sleep/circadian structure | **PhysioNet Sleep-EDF** | General population sleep study — supports circadian/sleep-stage-adjacent signal processing approaches in general, not spaceflight-specific validation. |
| Fluid shift / bio-impedance, spaceflight-analog conditions | **NASA OSDR** (Open Science Data Repository) — head-down-tilt bed rest and dry-immersion studies | The one dataset category in this table that is a genuine **spaceflight analog**, not merely a general-population proxy — see Section 8. |

### 7.1 The honest domain-gap problem

This project's own prior planning work (`Biological_Minimalism_Yol_Haritasi.md`, §6)
already identifies and names this issue, and this document adopts the same framing
rather than softening it: WESAD, STEW, and PulseDB/MIMIC-derived datasets are drawn
from general civilian or hospital populations under terrestrial gravity, with none of
microgravity, radiation exposure, or the psychological conditions of isolation and
confinement present. Any model trained purely on these datasets and then described as
"validated for astronaut monitoring" would be an overstatement this document explicitly
declines to make. NASA OSDR's bed-rest and dry-immersion analog studies are a
genuinely closer proxy — head-down-tilt bed rest is a long-established
ground-based analog for the cephalad fluid shift and cardiovascular deconditioning
seen in real microgravity exposure — but available data volume is smaller than the
general-population datasets above.

**This project's proposed mitigation** (a design proposal, not a proven solution) is
architectural rather than statistical: the Biological Digital Twin's per-individual
calibration layer (Section 12) is specifically intended to let a model pretrained on
general-population data (WESAD/STEW/PulseDB) adapt to an individual's own physiology
over a short calibration window, narrowing — but not eliminating — the domain gap
between population-level training data and a specific astronaut. Claims built on
WESAD/STEW/PulseDB (stress, cognitive load, cuffless BP as general techniques) are
presented in this document as "generalizability assumption, to be tested," while claims
built on NASA OSDR (fluid shift specifically) are presented with more confidence, per
this project's own risk framing.

**Original dataset citations** (each independently verified against this project's
own `ml/datasets/` loader-module docstrings, written with the specific citation in
hand, not reconstructed from memory here):

- **WESAD** — Schmidt, P., Reiss, A., Duerichen, R., Marberger, C., & Van Laerhoven, K.
  (2018). Introducing WESAD, a multimodal dataset for wearable stress and affect
  detection. *Proceedings of the 20th ACM International Conference on Multimodal
  Interaction (ICMI 2018)*. https://doi.org/10.1145/3242969.3242985
- **STEW** — Lim, W. L., Sourina, O., & Wang, L. P. (2018). STEW: Simultaneous Task
  EEG Workload Data Set. *IEEE Transactions on Neural Systems and Rehabilitation
  Engineering*, 26(11), 2106–2114. https://doi.org/10.1109/TNSRE.2018.2872924
- **PulseDB** — Wang, W., Mohseni, P., Kilgore, K. L., & Najafizadeh, L. (2023).
  PulseDB: A large, cleaned dataset based on MIMIC-III and VitalDB for benchmarking
  cuff-less blood pressure estimation methods. *Frontiers in Digital Health*, 4,
  1090854. https://doi.org/10.3389/fdgth.2022.1090854
- **PhysioNet / PhysioBank** — Goldberger, A. L., Amaral, L. A. N., Glass, L.,
  Hausdorff, J. M., Ivanov, P. Ch., Mark, R. G., Mietus, J. E., Moody, G. B., Peng,
  C.-K., & Stanley, H. E. (2000). PhysioBank, PhysioToolkit, and PhysioNet: Components
  of a new research resource for complex physiologic signals. *Circulation*, 101(23),
  e215–e220. https://doi.org/10.1161/01.CIR.101.23.e215

*[NASA OSDR head-down-tilt bed rest / dry-immersion study-level citations (specific
OSD-### accession numbers) remain pending a dedicated OSDR search and are not yet
independently verified for this document; Section 8 and `datasets/README.md` point at
the repository search entry point rather than a fabricated specific accession.]*

---

## 8. Bio-Impedance and Fluid Shift

Bio-impedance is this project's most direct link to a genuinely spaceflight-relevant,
literature-supported phenomenon: the cephalad fluid shift caused by the removal of
gravitational hydrostatic pressure gradients in microgravity, which is one of the most
consistently reported acute physiological effects of spaceflight across the sources
this project has reviewed (Grigoriev & Egorov, 1997; Pool, 1975; Gupta & Ghosh, 2025).

**Why bio-impedance, mechanistically.** Bio-impedance spectroscopy passes a small,
imperceptible alternating current through tissue and measures the resulting electrical
impedance; because extracellular and intracellular fluid have different electrical
properties than other tissue, and because impedance is a function of the electrical
path's cross-sectional area and fluid content, changes in segmental bio-impedance
(e.g. between two electrodes on the lower leg, or between head and torso) are usable as
a proxy for regional fluid volume changes. This is a **design proposal grounded in a
general biomedical technique**, not a claim that this project has itself validated a
specific bio-impedance electrode placement or measurement protocol against real
fluid-shift ground truth — that validation is scoped as future work (Section 20).

**Why this is the project's strongest dataset-supported claim.** Unlike the stress,
cognitive-load, and cuffless-BP targets (Section 7), which rely on general-population
proxy datasets, the fluid-shift target has a genuine spaceflight-analog data source
available: NASA OSDR's head-down-tilt bed rest and dry-immersion study data, which
directly measures the physiological consequences (including, in a number of these
studies, fluid redistribution markers) of a validated ground-based microgravity analog
protocol. This project's Dataset Research section (Section 7) accordingly treats the
fluid-shift target as the one where a genuinely relevant training/validation dataset
exists, rather than a general-population stand-in.

**What this project's mock engine actually does today (design proposal, clearly
labeled as such in the code).** The working dashboard's `fluid_shift_risk()` function
(`backend/app/engine/physiology.py`) models fluid-shift risk as elevated early in a
simulated exposure and easing as the Digital Twin's adaptation curve progresses toward
Day 30 — a shape consistent with the general bed-rest/dry-immersion adaptation
narrative in the literature above, but the specific curve parameters are an engineering
choice for this demonstration, not a curve fitted to real OSDR data. The code's own
docstring says exactly this, and this document repeats it here for consistency.

### 8.1 Bio-impedance as a general body-fluid measurement technique

Bioelectrical impedance analysis (BIA) is an established, non-invasive technique
across the broader clinical literature (not spaceflight-specific): it is used to
estimate total body water, extracellular water, and intracellular water, and to
track fluid-status change in populations ranging from surgical/oncological patients
to congestive heart failure patients, precisely because impedance at different
current frequencies partitions differently between intra- and extra-cellular fluid
compartments (a systematic review of BIA for body-composition/fluid-volume
measurement is indexed at PubMed ID 10124463 — cited by PMID here because this
document could not independently confirm its full author list through an accessible,
non-paywalled source, and declines to guess one). This is this project's citation for
the *general validity of bio-impedance as a fluid-measurement technique*; it is not a
spaceflight- or fluid-shift-specific study, which is why Section 7's dataset-level
citation for the spaceflight-analog evidence (NASA OSDR) is kept separate and is the
stronger of this project's two bio-impedance-related claims.

---

## 9. Signal Processing Pipeline

This section documents the signal-processing design actually implemented in
`backend/app/engine/physiology.py` (verified against the running code as part of
producing this document), separating the mechanistic rationale (where literature-
supported) from the specific coefficients (which are this project's engineering
choices for a live demo, not fitted or validated parameters).

### 9.1 Cardiovascular — PPG → heart rate, HRV, blood pressure, respiration

- **Heart rate and HRV.** The mock engine synthesizes a PPG waveform as a sequence of
  skewed-Gaussian pulses (fast systolic upstroke, slower diastolic decay) at
  RR-interval-jittered timing; in a real deployment, heart rate would be recovered from
  successive pulse-peak timing, and HRV (RMSSD) from the variability of successive
  peak-to-peak intervals — a standard, well-established time-domain HRV technique. This
  project's synthetic generator produces the *timing statistics* HR/HRV would already
  imply, rather than literally re-deriving them via peak detection on the synthetic
  waveform, because the demonstration's purpose is to show the downstream fusion and
  explainability pipeline, not to re-validate PPG peak-detection algorithms that are
  already standard practice.
- **Cuffless blood pressure.** `estimate_blood_pressure()` is loosely inspired by
  pulse-arrival-time (PAT) based cuffless blood pressure estimation — a real, actively
  researched technique family in which a shorter arrival time between a cardiac
  electrical/mechanical reference event and the peripheral pulse arrival is associated
  with higher arterial pressure. Because the mock engine has no literal second sensor
  to derive a true transit time from, it proxies PAT from the HR/HRV signal instead —
  the code's own docstring calls this "a demo-grade proxy, not a validated PAT
  extraction," and this document repeats that qualification here rather than letting
  the dashboard's numeric blood pressure readout imply more precision than it has.
- **Respiration rate.** `respiration_rate_from_hrv()` is inspired by respiratory sinus
  arrhythmia (RSA) — the well-documented physiological coupling between the
  respiratory cycle and heart-rate variability, mediated by vagal tone — modeled here
  as a simplified pull on a baseline respiration rate rather than literal RSA frequency
  extraction from a real HRV time series.

### 9.2 EEG → cognitive load, attention, fatigue, circadian stability

- **Cognitive load.** `cognitive_load_from_eeg()` uses a beta-power relative to
  (alpha+theta)-power ratio, scaled to a 0–100 range — an "engagement index"-style
  ratio. Elevated relative beta power is commonly associated with higher mental
  workload in EEG workload literature (the specific literature this project's STEW-
  dataset dataset-research section, Section 7, is scoped around).
- **Attention.** `attention_from_eeg()` uses a beta-to-alpha ratio on the same
  principle.
- **Fatigue.** `fatigue_score()` is a composite of (a) HRV depression (autonomic
  strain), (b) elevated cognitive load, and (c) EEG theta-to-alpha ratio (a commonly
  reported drowsiness marker) — combined with fixed weights (0.45 / 0.35 / 0.20) that
  are **this project's own engineering choice for the demo**, not a fitted or
  literature-derived weighting.
- **Circadian stability.** `circadian_stability()` models a roughly 24-hour sinusoidal
  phase whose amplitude decays under mission-mode stress and slowly recovers as the
  Digital Twin's mission-day adaptation progresses — a design proposal illustrating the
  circadian-disruption-under-stress pattern documented in spaceflight circadian
  research (see Section 6, Kurt, n.d.), not a fitted circadian model.

### 9.3 Bio-impedance → fluid shift risk

See Section 8.

### 9.4 What is real signal processing vs. illustrative synthesis

To be fully precise about what this deliverable actually does: because the dashboard
has no physical sensor to process, `physiology.py`'s functions take already-synthesized
feature values (HR, HRV, EEG band powers, temperature, bio-impedance trend) as *inputs*
and compute derived scores as *outputs* — this is the same transformation a real
signal-processing pipeline would perform on real sensor features, and is explicitly
designed to be swappable (Section 12) with a version fed by a real windowing/feature-
extraction front end. The raw PPG/ECG-like waveforms shown on the Live Monitoring page
are synthesized separately, for visual/charting purposes, timed to be consistent with
the same HR value — they are not re-analyzed to produce the metrics; the metrics are
the source of truth, and the waveforms are drawn to match them, not the reverse. This
is stated explicitly in the code's own module docstring and repeated here so this
document does not imply a signal-processing capability (waveform-to-feature extraction)
that this specific deliverable does not exercise.

The EEG-band-power-workload approach in this section draws its general plausibility
from the same STEW dataset literature already cited in Section 7 (Lim, Sourina, &
Wang, 2018), which is itself built around task-induced EEG workload measurement. This
document did not find and independently verify a dedicated citation for respiratory
sinus arrhythmia or pulse-arrival-time cuffless blood pressure specifically beyond
what is already cited via the PulseDB dataset paper (Section 7, Wang et al., 2023),
so no additional source is asserted here beyond those already listed.

---

## 10. CNN Architecture

**Status: implemented, real, untrained.** `backend/app/ml/models.py` defines
`Conv1DEncoder`, a per-modality 1D convolutional feature extractor, as an actual
PyTorch `nn.Module` — not pseudocode. This section documents that implementation.

### 10.1 Design

Each of the four modalities (EEG, PPG, temperature, bio-impedance) has its own
`Conv1DEncoder` instance (no weight sharing across modalities, since each carries a
distinct signal character and sampling rate). Each encoder is a three-block 1D CNN:

```
Conv1d(in_channels → 16,  kernel=7, stride=2) → BatchNorm1d → GELU
Conv1d(16 → 32,           kernel=5, stride=2) → BatchNorm1d → GELU
Conv1d(32 → embedding_dim, kernel=5, stride=2) → BatchNorm1d → GELU
→ AdaptiveAvgPool1d(1)  →  fixed-size embedding vector
```

Progressively increasing channel depth with stride-2 downsampling at each stage is a
standard, lightweight design pattern for 1D biosignal windows: early layers see
higher-resolution local waveform shape (individual pulse morphology, individual EEG
oscillation cycles), later layers see progressively longer effective receptive fields
at lower time resolution, and adaptive average pooling collapses the final feature map
to a fixed-size embedding regardless of input window length — which matters here
because the four modalities do not share a common native sampling rate.

**This is a design proposal.** The specific channel widths (16→32→64), kernel sizes
(7→5→5), and three-block depth are this project's own architecture choice for a
lightweight, quickly-trainable encoder suited to a class project's compute and data
budget — not a configuration copied from or validated against a specific published
architecture for this exact sensor combination. The general pattern (1D CNN encoder
per biosignal channel, hierarchical stride-based downsampling, global pooling to a
fixed embedding) is a widely used approach in wearable/biosignal deep learning more
broadly; this document did not independently verify a single specific foundational
citation for that general pattern (unlike Section 11's Transformer architecture,
where Vaswani et al., 2017 is a clear, singular foundational source) and declines to
name one rather than guess, since 1D-CNN-for-biosignals is a broad pattern with many
candidate papers rather than one originating source.

### 10.2 Training status: three modalities trained on real data, one untrained, fusion not yet jointly trained

The full 4-modality fusion network ships untrained with this deliverable —
`Conv1DEncoder` and `ModalityFusionTransformer` were never jointly trained
end to end, and training against a real spaceflight-analog dataset remains
future work, scaffolded but not executed in `ml/train.py` (see Section 16
and `ml/README.md`). Three of the four *per-modality* encoders, however,
were each independently trained and validated on real, downloaded data —
this section reports all three results with equal weight to what worked and
what did not, per this document's own transparency commitment (Section 20).

**EEG** (`ml/train_sleep_edf.py`): WESAD, this project's original planned
dataset, has two dead official distribution links (independently
re-verified, not assumed). Substituted with PhysioNet Sleep-EDF (Section 7):
real 30-second EEG epochs from 3 subjects, subject-level held-out split (2
trained on, 1 unseen tested on) — **72.6% held-out accuracy** on 5-class
sleep staging, against a 66.2% majority-class baseline. Held-out accuracy
varied 41.8%–78.9% across training epochs (small-sample variance, reported
as-is).

**PPG** (`ml/train_ppg.py`): also originally scoped for WESAD; substituted
with the real, open PhysioNet BIDMC PPG and Respiration Dataset (Pimentel et
al., 2017), which happens to be a better fit — it carries real per-second
clinical heart-rate and respiration-rate ground truth, directly matching
this project's actual `heart_rate_bpm`/`respiration_rate_bpm` output
targets. 53 subjects, subject-level held-out split (37 trained on, 16
unseen tested on): **heart rate held-out MAE 8.72 bpm, beating a 12.15 bpm
naive baseline** — a real, meaningful result; **respiration rate held-out
MAE 3.43 breaths/min, worse than a 2.29 breaths/min naive baseline** — a
real negative result, reported rather than omitted.

**Bio-impedance/temperature** (`ml/train_bioimpedance.py`): this project's
originally planned dataset, NASA OSDR, was queried directly via its public
search API for bio-impedance-related terms; every result was a molecular-
biology ('omics) study — OSDR does not host raw physiological sensor time
series in a form this project could use. Substituted with PhysioNet's
Quantitative Dehydration Estimation dataset: real segmental bio-impedance
and real skin temperature from 10 subjects during exercise-induced
dehydration (not spaceflight-induced fluid shift, stated plainly — see
Section 8). Leave-one-subject-out cross-validation, reframed to predict each
subject's fluid change from their own baseline (this project's actual
fluid-*shift* framing): **mean held-out MAE 0.454 L, against a 0.414 L naive
baseline — a null-to-slightly-negative result at n = 10 subjects.**

**What these three runs do and do not prove.** They prove the project's
real architecture pieces train on real physiological data from three
independent, verified sources, and that at least two pathways (EEG, PPG-for-
heart-rate) learn a real, subject-general, better-than-baseline signal. They
do not prove the full 4-modality fusion model's real-world accuracy — the
three encoders were trained independently, never jointly with
`ModalityFusionTransformer`, and this checkpoint set does not load into
`TorchInferenceEngine` (Section 17), which expects the full-network state
dict `train.py` would eventually produce. The dashboard's default AI path
remains the transparent rule-based physiology engine (Section 9). See
`ml/README.md`'s "Next steps toward the full 4-modality checkpoint."

---

## 11. Transformer Fusion Architecture

**Status: implemented, real, untrained.** `ModalityFusionTransformer` in
`backend/app/ml/models.py` is the cross-sensor fusion layer sitting on top of the four
`Conv1DEncoder` outputs.

### 11.1 Design

The four modality embeddings (one 64-dimensional vector per sensor, from Section 10)
are treated as a length-4 sequence — each modality is one "token." A learned
per-modality positional/identity embedding is added to each token (so the model can
tell EEG's token from PPG's token, since a Transformer encoder is otherwise
permutation-invariant), and a small Transformer encoder (2 layers, 4 attention heads,
GELU feedforward) performs self-attention across the four tokens before the result is
mean-pooled into a single fused representation, which feeds per-target linear
regression heads (Section 10.1 lists the nine output targets: cognitive load, fatigue,
autonomic balance, fluid-shift risk, heart rate, HRV, systolic/diastolic BP,
respiration rate).

**Why attention across modalities, specifically.** The motivating idea — a design
proposal this project has not itself validated — is that cross-sensor attention lets
the fusion layer learn, from data, which modality combinations are jointly informative
for which target (e.g. that EEG and temperature jointly explain a state better than
either alone), rather than this project hand-specifying fixed per-modality weights for
every target. Compare this to the transparent rule-based `physiology.py` engine
(Section 9), which *does* use fixed, hand-specified logic — the Transformer
architecture is this project's proposed upgrade path once real training data exists,
not a claim that it currently outperforms the rule-based engine (it has never been
trained, so no such comparison is possible yet).

### 11.2 Modality masking — the mechanism behind graceful degradation

The fusion Transformer's `forward()` method accepts an optional per-modality boolean
mask, implemented via `src_key_padding_mask` in PyTorch's standard
`TransformerEncoderLayer` — a missing or masked modality is excluded from the
attention computation entirely (its position contributes no attention weight to the
other tokens), while the remaining modalities' tokens still attend to each other
normally. **This is the architectural mechanism this project designs to eventually
carry the "Sensor Failure Simulation" demonstration (Section 16) once trained**: an
astronaut losing one of four sensors should degrade the fused estimate's precision
smoothly rather than break it outright, because the model was designed to see
masked-modality inputs as a normal operating condition rather than an edge case. As
with Section 10, this is a structural design claim about the architecture, not a
trained/validated result — the *dashboard's actual* Sensor Failure demonstration today
runs on the rule-based engine's own explicit signal-quality-reweighting logic (Section
9, Section 13), which achieves the same graceful-degradation *behavior* today through
simpler, fully transparent means, while this Transformer path is the proposed
future upgrade with the same design intent.

**Foundational citation.** The Transformer architecture itself — multi-head
self-attention as a general sequence-modeling mechanism, used here across a
length-4 modality sequence rather than its original language-sequence setting — is
due to Vaswani et al. (2017), *Attention Is All You Need*, NeurIPS 30 (see Section
21). This project's specific application (treating sensor modalities, rather than
words or time steps, as the attention sequence) is this project's own design choice,
not something the original paper itself proposes.

*[Multimodal-physiological-signal-fusion-specific Transformer applications (as
opposed to the foundational architecture paper, now cited above) remain a search this
document's research pass has not yet independently verified a specific source for;
none is cited rather than guessing one.]*

---

## 12. Adaptive Baseline — the Biological Digital Twin

This section documents both (a) the working dashboard's actual, implemented Digital
Twin logic, and (b) the longer-term adaptive-baseline design this project proposes
for a trained system, being explicit throughout about which is which.

### 12.1 What is implemented and running today

`MockDataEngine.get_digital_twin_state(day)`
(`backend/app/engine/mock_data_engine.py`) models four physiological systems —
Cardiovascular, Cognitive, Fluid Balance, Thermal Regulation — each as an exponential
adaptation curve from a Day-1 baseline score toward a system-specific asymptote:

```
current_score(day) = baseline + (asymptote − baseline) × (1 − e^(−k × (day − 1)))
```

with per-system baseline, asymptote, and rate constant `k` set as **explicit design
choices for this demonstration** (documented in the code as `_DIGITAL_TWIN_SYSTEMS`),
not fitted to real adaptation-curve data. This produces the milestone narrative shown
at Day 1, 5, 12, and 30 in the dashboard's Digital Twin page (Section 16), and the
general *shape* of the curve — rapid initial change, decelerating toward a stable
plateau — is a deliberately chosen illustration of the general physiological-
adaptation pattern described qualitatively in the spaceflight-adaptation literature
(Section 2), not a specific curve validated against real longitudinal astronaut or
analog-study data.

### 12.2 The proposed calibration architecture (design proposal, not implemented)

For a real, trained system, this project proposes a two-phase calibration scheme
directly motivated by the domain-gap problem in Section 7.1:

1. **Population pretraining.** Train the CNN+Transformer fusion network (Sections
   10–11) on the general-population datasets (WESAD, STEW, PulseDB) plus the
   spaceflight-analog OSDR data, producing a model with reasonable priors across the
   four target physiological domains but not calibrated to any one individual.
2. **Individual calibration window.** Over an initial on-mission window (this
   project's own planning documents, `Biological_Minimalism_Yol_Haritasi.md`, propose
   48–72 hours as an illustrative starting point — itself a design proposal, not a
   number derived from a cited calibration-window study), collect that specific
   astronaut's own four-sensor data and use it to adjust the model's baseline/reference
   point for that individual, so subsequent deviation-from-baseline judgments are
   relative to *that person's* normal, not the population average.

This two-phase pattern (population pretraining + short individual calibration) is a
standard technique family in personalized/few-shot machine learning more broadly; this
project's specific claim is only that applying it to this four-sensor astronaut-
monitoring problem, on top of this specific fusion architecture, is *this project's*
proposal — not a technique this document claims was copied from a specific space-
medicine source.

No dedicated personalized-calibration/few-shot-adaptation citation specific to
physiological monitoring was independently verified for this document; Section 12.2's
population-pretraining-plus-individual-calibration scheme is presented as this
project's own proposed architecture, informed by the general pretrain-then-adapt
pattern common across machine learning more broadly rather than by one specific cited
source.

---

## 13. Explainable AI

**Status: implemented, real, running.** This is the one AI component in this
deliverable that is fully implemented, exercised end-to-end, and produces genuine
computed output rather than a documented future design — verified directly against
the running backend while producing this document (see Section 17.4 for a real,
captured example).

### 13.1 What "real SHAP" means here, precisely

`backend/app/ml/explainability.py` treats the transparent rule-based physiology
functions (Section 9) — specifically `fused_confidence()` for the AI Confidence target,
and `fatigue_score()` for the Fatigue Risk target — as the model to be explained, and
fits a `shap.KernelExplainer` (a model-agnostic, perturbation-based Shapley-value
estimator, from Lundberg & Lee's SHAP framework — see Section 21 for the citation) over
each, using synthetic background samples spanning plausible operating ranges for each
input feature. KernelExplainer requires no gradient access and works for any callable
function, which is precisely why it is usable here even though the "model" is a
transparent function rather than a trained neural network — the explanation is exactly
as genuine as it would be for a trained model, because Shapley-value computation makes
no assumption about the explained function's internal structure.

**Why this is not "decorative" or scripted text.** For any given live reading, the
explainer perturbs the input feature vector, observes how the physiology function's
output changes, and attributes the total difference between that prediction and the
explainer's background expected value across the individual input features, following
the Shapley-value cooperative-game-theory allocation rule. The natural-language summary
shown on the dashboard (e.g. *"AI Confidence is 59% because PPG signal quality dropped
to 0% while EEG signal quality remains nominal (100%)"*) is generated by a template
that selects the top-magnitude *computed* SHAP contributions and states their direction
— the sentence changes only because the underlying SHAP values changed, never because
of a hand-written per-scenario string.

### 13.2 The two explained targets

- **`ai_confidence`** — explains the overall AI Confidence score in terms of each
  sensor's signal quality (`ppg_quality`, `eeg_quality`, `temperature_quality`,
  `bioimpedance_quality`), which is what powers the Sensor Failure demonstration
  (Section 16): taking a sensor offline sets its quality feature to zero, and the SHAP
  explanation genuinely re-attributes accordingly.
- **`fatigue_risk`** — explains the fatigue score in terms of HRV, EEG theta power, EEG
  alpha power, cognitive load, and mission-mode stress bias, matching the style of
  example given in this project's own specification (*"Fatigue risk increased because
  HRV decreased while cognitive workload remained elevated"*).

### 13.3 What this section does not claim

This explains *this project's own rule-based estimator* — a transparent function this
project itself wrote, whose logic is separately documented (with its literature
grounding and its acknowledged status as an engineering approximation) in Section 9. It
is not, today, explaining a trained neural network's learned, opaque internal
reasoning — that is a real SHAP use case (`DeepExplainer` / `GradientExplainer`,
supported by the same `shap` library) this project's own inference-engine interface
(`backend/app/ml/inference.py`) is explicitly designed to support once the CNN+
Transformer network (Sections 10–11) is trained, without any change to the
`/ai/explanation` API contract (Section 17) or the frontend that consumes it.

The SHAP framework's foundational citation — Lundberg, S. M., & Lee, S.-I. (2017). A
unified approach to interpreting model predictions. *Advances in Neural Information
Processing Systems 30 (NeurIPS 2017)*, 4765–4774 — is independently verified for this
document (title, authors, venue, and page range all confirmed directly against the
paper's NeurIPS listing). A dedicated SHAP-in-healthcare-monitoring application paper
was not independently verified and so is not cited; the explainability claims in this
section rest on the foundational SHAP paper plus this project's own verified,
reproducible use of the `shap` library against its own physiology functions (Section
17.4).

---

## 14. Ablation Study Design

**Status: designed and scaffolded (`ml/ablation.py`), not yet run** — running it
requires a trained checkpoint and a held-out validation set, neither of which exists
in this deliverable's scope (Section 7). This section documents the experimental
design so that step is not a fresh design exercise once training data and a trained
checkpoint exist.

### 14.1 Configurations to compare

1. **Full sensor set** — all four modalities present. For Biological Minimalism, this
   *is* the maximal condition (there is no larger sensor set in this project's own
   design) — kept as the reference condition the other conditions are compared against.
2. **Single-modality dropout** — mask one modality at a time (EEG, PPG, Temperature,
   Bio-impedance) via the Transformer fusion layer's modality mask (Section 11.2), and
   re-evaluate every target, to quantify the accuracy cost of losing each individual
   sensor.
3. **Noise injection** — evaluate under elevated synthetic noise, standing in for the
   mission-mode noise multipliers already implemented in `physiology.py`'s
   `MODE_PROFILES` (Section 16.1) — Earth Orbit at 1.0×, Lunar Surface at 1.35×, Deep
   Space at 1.7×, Solar Event at 2.4×.
4. **Motion artifact injection** — evaluate with simulated high-frequency artifact
   bursts added to the PPG/EEG windows, standing in for the physical-activity artifact
   conditions any real wearable deployment would face.

### 14.2 Metrics

- **MAE / RMSE** per continuous regression target (heart rate, HRV, blood pressure,
  respiration rate, cognitive load, fatigue, autonomic balance, fluid-shift risk).
- **F1** for any target this project would eventually threshold into a discrete
  risk-level classification (e.g. Nominal / Warning / Critical), for consistency with
  how the dashboard itself presents risk (Section 16).
- **Robustness delta** — the degradation in each metric from the full-sensor-set
  condition to each degraded condition (single-modality dropout, noise, motion
  artifact), which is this project's direct empirical measurement of the "graceful
  degradation" property the Transformer fusion architecture is designed to provide
  (Section 11.2).
- **Information Density Index (IDI)** — this project's own proposed metric (Section 1),
  computed once real accuracy numbers exist, as recovered-information (inverse of
  normalized error, aggregated across targets) divided by active sensor count, letting
  the minimal (four-sensor) and single-modality-dropout (three-sensor) conditions be
  compared on a like-for-like basis against a hypothetical denser sensor set.

### 14.3 Why this design, not a different one

This ablation design is built to produce the specific evidence this project's central
claim requires: not "does the model work," but "how much does removing a given
sensor cost, and is that cost small enough to justify the reduction in physical
burden." That framing is why every condition beyond the full-sensor baseline is a
*subtraction* (fewer sensors, more noise, more artifact) rather than an *addition* —
this project is not proposing to test whether more sensors would help (that is already
well established, per Section 2), it is testing how far the sensor count can be
reduced before the AI-recovered information degrades unacceptably.

---

## 15. Experimental Design

This section describes the phased research plan this project follows to move from
the current state (working demonstrator on synthetic data, Sections 16–17; untrained-
but-real ML architecture, Sections 10–11) to a trained, empirically validated system,
consistent with this project's own internal planning documents
(`Biological_Minimalism_IAC2026_Master_Project_Plan.md`,
`Biological_Minimalism_Yol_Haritasi.md`) and restated here in the PDD's own terms.

**Phase A — Data infrastructure and per-modality baselines.** Acquire and preprocess
WESAD, STEW, PulseDB, and NASA OSDR data (Section 7); implement the loader interfaces
already scaffolded in `ml/datasets/` (currently stubs, honestly raising
`NotImplementedError` until pointed at real downloaded data); train single-modality
CNN baselines (one `Conv1DEncoder` + head, per target, per available modality) to
establish a reference accuracy floor that the full fusion model (Phase B) must beat to
justify its added complexity.

**Phase B — Fusion and calibration.** Train the full `BiologicalDigitalTwinNet`
(Sections 10–11) end to end via `ml/train.py` (already scaffolded, currently blocked
only on real data availability); implement and evaluate the individual-calibration
layer proposed in Section 12.2.

**Phase C — Ablation and robustness validation.** Run the ablation study designed in
Section 14 against the trained checkpoint from Phase B, producing this project's own
first empirical Information Density Index numbers and single-modality-dropout
robustness figures — the direct evidence for or against this project's central
Biological Minimalism hypothesis.

**Phase D — Explainability transition.** Re-point `ml/explainability.py`'s SHAP
explainers from the rule-based physiology functions (Section 13, current state) to
`DeepExplainer`/`GradientExplainer` wrapping the trained `BiologicalDigitalTwinNet`,
verifying that explanation quality (specificity, stability across repeated queries at
the same operating point) holds up for a trained neural network the way it already
does for the transparent rule-based function.

**Phase E — Dashboard integration.** Set `BIOMIN_MODEL_CHECKPOINT_PATH` to the trained
checkpoint; `backend/app/ml/inference.py`'s `create_inference_engine()` already
switches to `TorchInferenceEngine` automatically when a valid checkpoint path is
configured (verified in this document's own review of the running code, Section 17),
so this phase is expected to require no API or frontend changes — the explicit design
goal stated in the code's own docstrings throughout `backend/app/ml/`.

This phased structure is why the working deliverable (Sections 16–17) is built the way
it is: every integration seam a future trained model would need (the
`AIInferenceEngine` protocol, the SHAP explainer's target interface, the API contract)
is already in place and exercised today by the rule-based engine, specifically so
Phases A–D are additive, not a rewrite.

---

## 16. Dashboard Architecture

This section documents the working software deliverable built alongside this PDD, as
actually implemented and verified (build, tests, and live endpoint checks were all run
against this exact code while producing this document — see Section 17.4).

### 16.1 The Mock Data Engine

`backend/app/engine/mock_data_engine.py`'s `MockDataEngine` is the single source of
simulated "ground truth" for the whole running system. Internally, it advances a set of
smooth Ornstein-Uhlenbeck random walks — a standard stochastic-process technique for
generating continuous, mean-reverting synthetic signals that look like physiology
rather than independent noise from tick to tick — for heart rate, HRV, temperature,
temperature drift, bio-impedance trend, and the four EEG band powers, once per tick
(default 0.5s). Four things shape those random walks:

- **Mission mode** (`MissionMode`: Earth Orbit / Lunar Surface / Deep Space / Solar
  Event), each with its own `noise_multiplier` (1.0× / 1.35× / 1.7× / 2.4×) and
  `risk_bias` (0 / 8 / 16 / 30) applied to every relevant signal — the mechanism behind
  the **Solar Storm Mode demonstration**.
- **Per-sensor status** (`SensorStatus`: Nominal / Degraded / Offline), which sets a
  per-sensor `signal_quality` (1.0 / 0.45 / 0.0) that both amplifies that sensor's own
  noise (a degraded sensor is noisier, not just lower-weighted) and feeds directly into
  the confidence/contribution fusion logic below — the mechanism behind the **Sensor
  Failure Simulation demonstration**.
- **Mission day** (0–30, advancing roughly one simulated day per five real minutes by
  default), which shapes the bio-impedance target trend (fluid-shift adaptation,
  Section 8) and feeds the separate, closed-form Digital Twin adaptation-curve function
  (Section 12.1) — the mechanism behind the **Digital Twin Evolution demonstration**.
- **The physiology scoring functions** (`physiology.py`, Section 9), which turn the raw
  random-walk state into every derived metric the dashboard displays (cognitive load,
  fatigue, circadian stability, blood pressure, respiration rate, fluid-shift risk,
  autonomic balance, thermal stability, AI confidence, per-sensor contribution).

### 16.2 Frontend structure

Built with Next.js 15 (App Router) and React 19, in strict TypeScript, styled with
Tailwind CSS, charted with Recharts, and animated with Framer Motion — six pages,
matching this project's own specification exactly:

| Page | Route | Primary content |
|---|---|---|
| Mission Overview | `/mission-overview` | All primary panels at a glance; mission-mode switcher (Solar Storm Mode demo) |
| Live Monitoring | `/live-monitoring` | Live waveforms, HRV/cognitive-load trend charts, sensor-health panel, Sensor Failure Simulation control |
| Digital Twin | `/digital-twin` | Holographic-style adaptation panel, mission-day slider (Digital Twin Evolution demo) |
| AI Insights | `/ai-insights` | AI Confidence panel, real SHAP explanation panels for both explained targets |
| Mission Timeline | `/mission-timeline` | Circadian-stability trend, Day 1/5/12/30 adaptation milestones |
| Settings | `/settings` | Backend connection diagnostics, reduced-motion accessibility toggle, project attribution |

Live state (the most recent telemetry frame, a rolling ~180-frame history buffer for
trend charts, and WebSocket connection status) is held in a single Zustand store
(`frontend/src/store/missionStore.ts`), fed continuously by a `useLiveFeed()` hook
that owns the WebSocket connection (with capped exponential-backoff reconnection) and
by direct REST calls for the Digital Twin and Explainable AI pages, which are queried
on demand rather than streamed.

### 16.3 The "holographic" Digital Twin panel

Rendered with layered SVG, CSS glassmorphism, and Framer Motion — deliberately not
using a 3D library such as three.js, since one is not part of this project's specified
technology stack, and the layered-glow/ring visual language achieves a convincing
"holographic" feel through 2D techniques (radial gradients, concentric animated rings,
depth via blur and opacity layering) without adding an unrequested dependency.

---

## 17. API Design

The backend (FastAPI) exposes exactly the REST surface and WebSocket stream specified
for this project, plus one liveness endpoint. This section documents the actual,
implemented contract, verified live (Section 17.4) while producing this document.

### 17.1 REST endpoints

| Method & path | Purpose |
|---|---|
| `GET /health` | Liveness check (service name, version) |
| `GET /metrics/live` | Latest telemetry snapshot (`LiveMetricsSnapshot`) |
| `GET /metrics/history?limit=N` | Recent telemetry history, for trend charts |
| `GET /digital-twin?day=D` | Digital Twin adaptation state at mission day `D` (0–30) |
| `GET /sensor-health` | Per-sensor status and signal quality |
| `GET /simulation/state` | Current mission mode and sensor status |
| `POST /simulation/mode` | Set mission mode — `{ "mode": "earth_orbit" \| "lunar_surface" \| "deep_space" \| "solar_event" }` — **Demo 2** |
| `POST /simulation/failure` | Set a sensor's status — `{ "sensor": "eeg"\|"ppg"\|"temperature"\|"bioimpedance", "status": "nominal"\|"degraded"\|"offline" }` — **Demo 1** |
| `GET /ai/explanation?target=T` | Real SHAP explanation for `T ∈ {ai_confidence, fatigue_risk}` |

### 17.2 WebSocket

`GET /ws/live-feed` — a telemetry-only push stream. On connect, the server registers
the socket with a `ConnectionManager`; every mock-engine tick, the resulting
`LiveMetricsSnapshot` is broadcast (as JSON) to every connected socket. The socket
does not accept or act on client-sent messages — simulation control (mode, sensor
failure) intentionally stays on REST, specifically so each control action is a single,
idempotent, independently curl-testable request, with its effect observed on the next
WebSocket frame rather than requiring a stateful command protocol over the socket
itself.

### 17.3 Why REST-for-control / WebSocket-for-telemetry

This is a deliberate design choice, not an arbitrary split: control actions (changing
mission mode, failing a sensor) are rare, discrete, and benefit from ordinary
HTTP semantics (a definite response, standard status codes, straightforward retry
behavior); telemetry is frequent, continuous, and benefits from a push model that
avoids polling overhead. Keeping them on separate transports also makes each half of
the system independently testable — this document's own verification (Section 17.4)
exercised both the REST control endpoints and the WebSocket stream directly via `curl`
and a standalone Python WebSocket client, without needing the frontend running at all.

### 17.4 Verified, live example (captured while producing this document)

The following is a real request/response sequence, captured by starting the actual
backend (`uvicorn app.main:app`) and issuing real HTTP requests against it — not a
hypothetical illustration:

```
POST /simulation/failure   { "sensor": "ppg", "status": "offline" }
→ { "mission_mode": "earth_orbit",
    "sensor_status": {"eeg":"nominal","ppg":"offline","temperature":"nominal","bioimpedance":"nominal"} }

GET /ai/explanation?target=ai_confidence
→ {
    "target": "ai_confidence",
    "summary_text": "AI Confidence is 59% because PPG signal quality dropped to 0% while EEG signal quality remains nominal (100%).",
    "base_value": 48.61,
    "predicted_value": 59.0,
    "contributions": [
      {"feature": "PPG signal quality", "value": 0.0, "shap_value": 19.22, "direction": "increased_risk"},
      {"feature": "EEG signal quality", "value": 1.0, "shap_value": -17.06, "direction": "decreased_risk"},
      {"feature": "Temperature signal quality", "value": 1.0, "shap_value": -7.50, "direction": "decreased_risk"},
      {"feature": "Bio-impedance signal quality", "value": 1.0, "shap_value": -5.06, "direction": "decreased_risk"}
    ]
  }
```

Overall confidence fell from 100% (all sensors nominal) to 59% immediately after PPG
was taken offline, and the SHAP attribution correctly identifies PPG's signal-quality
drop as the dominant (largest-magnitude) contribution — genuinely computed, not
scripted, and reproducible by running the commands above against the repository as
checked in.

---

## 18. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Real astronaut/spaceflight validation data never becomes available for this project | Medium | High (limits how strong Section 15's Phase A–D claims can ever become) | NASA OSDR analog data (Section 7–8) is the best currently accessible substitute; the domain-gap limitation is stated explicitly throughout rather than hidden (Section 20) |
| Trained fusion model (Sections 10–11) underperforms the transparent rule-based engine (Section 9) once actually trained | Medium | Medium | The rule-based engine is kept as the permanent default and fallback (`create_inference_engine()` only switches to the trained model if a valid checkpoint is configured, and falls back safely on load failure) — verified in the running code, Section 17.4 style live-checked |
| SHAP explanations become misleading if applied naively to a poorly calibrated trained model | Low today (current explainer targets a transparent function, Section 13) | High if mishandled during Phase D | Phase D (Section 15) explicitly includes an explanation-quality verification step before any trained-model explainer replaces the current one |
| Jury/reviewer perceives synthetic-data-only demonstration as overclaiming real capability | Medium | High (credibility) | Every page of the dashboard, this document, and the code's own docstrings state the synthetic-data status explicitly and repeatedly (Section 20); no claim in this document is left ambiguous about proven-vs-proposed status |
| Bio-impedance fluid-shift curve parameters (Section 8) are mistaken for fitted/validated values | Low | Medium | Code docstring and this document both state explicitly that curve shape is illustrative, not fitted to OSDR data |
| Five-week timeline (Section 19) slips | Medium | Medium | Phased structure (Section 15) is designed so a slip can drop later phases (Phase D explainability transition, Phase C ablation) while keeping the working demonstrator (Sections 16–17, already complete) intact |
| Two-person/parallel-session development on this same repository causes conflicting or duplicated work | Realized during this project's own development process | Low (caught and resolved) | Direct session-to-session coordination was used to resolve a real file-conflict incident during this deliverable's construction; documented here as an honest process note, not omitted |

---

## 19. Five-Week Project Calendar

Adapted from this project's own internal planning document
(`Biological_Minimalism_Yol_Haritasi.md`, §10), restated here in English for the PDD.
Dates assume a project start of **2026-08-27**, running through the IAC 2026 week
(2026-10-05 to 2026-10-09).

| Week | Dates | Focus | End-of-week deliverable |
|---|---|---|---|
| 1 | Aug 27 – Sep 2 | Scope 2–3 target physiological states; download WESAD, STEW, PulseDB, NASA OSDR; define spaceflight-analog stress scenarios (motion artifact, noise injection, sensor dropout) | Datasets downloaded; scope decision documented |
| 2 | Sep 3 – Sep 9 | Data preprocessing; per-modality CNN feature extraction (Section 10); single-modality baseline models (Experimental Design Phase A) | Working baseline models with initial accuracy numbers |
| 3 | Sep 10 – Sep 16 | Transformer fusion layer (Section 11); Euclidean Alignment domain adaptation; first working individual-calibration logic (Section 12.2); dashboard skeleton | Working fusion model; dashboard skeleton demoable |
| 4 | Sep 17 – Sep 23 | Minimal-set vs. full-set comparison; noise/artifact robustness testing (Experimental Design Phase C); zero-shot subject-independent evaluation; dashboard demo-ready, screen recording captured | First empirical Information Density Index numbers; demo video |
| 5 | Sep 24 – Sep 30 | Presentation deck (continuous digital-screen format per IAF's Interactive Presentation rules) with embedded demo video; live in-house EEG rehearsal (internal developer testing, explicitly not framed as a validated research cohort — see Section 20); 8–10 minute talk script | Full deck; rehearsal complete |
| Final days | Oct 1 – Oct 4 | Full timed rehearsal; offline backups (USB, local disk); travel/accreditation logistics | Rehearsal complete; bag packed |
| IAC week | Oct 5 – Oct 9 | Antalya: continuous digital-screen presentation all week; 8–10 minute live session + Q&A | Presentation delivered |

The working dashboard deliverable and this PDD (Sections 1–18, 20–21) were produced
ahead of this calendar's Week 3 dashboard-skeleton milestone, in a single concentrated
effort — the calendar above describes the fuller research plan (real dataset
training, empirical ablation results) this deliverable sets up but does not itself
complete.

---

## 20. Limitations and Scope

Stated plainly, in one place, for anyone who reads only this section:

1. **No real sensor, subject, or astronaut data is used anywhere in the working
   dashboard.** Every telemetry value shown is generated by
   `backend/app/engine/mock_data_engine.py`, a synthetic stochastic-process engine.
2. **The full multimodal fusion network has not been trained.** Several per-modality
   proof-of-concept models (EEG, PPG, bio-impedance/temperature — Section 10.2) were
   trained on real public datasets and produced real, honestly-reported held-out
   results; however, the CNN+Transformer architecture's fusion layer (Sections 10–11)
   has never been jointly trained across modalities, no full-network checkpoint exists
   in this repository, and none of the per-modality checkpoints is wired into
   `TorchInferenceEngine` — that class currently loads a checkpoint but does not call
   the model's forward pass (Section 17). The dashboard's live AI Confidence, Fatigue
   Risk, and all other derived metrics come from a transparent, hand-specified
   rule-based physiology engine (Section 9), whose coefficients are engineering
   choices for this demonstration, not fitted or validated parameters, and whose
   sensor-contribution weights (41/35/14/10%) are likewise a design proposal, not an
   empirical ablation result.
3. **The SHAP explanations are genuine, but they explain that rule-based engine, not a
   trained neural network** (Section 13.3) — this is stated as a feature (nothing
   about the explanation is faked) with an honest caveat about scope (it is not yet
   explaining the more complex architecture this project's future work targets).
4. **The datasets this project scopes for future training (WESAD, STEW, PulseDB) are
   general-population, not astronaut or spaceflight-specific**, and even NASA OSDR's
   genuinely spaceflight-analog data (bed rest, dry immersion) is a ground-based
   analog, not real microgravity flight data (Section 7.1).
5. **Any internal-team EEG testing conducted alongside this project** (per this
   project's own planning documents) is explicitly internal developer/system testing,
   not a research study with human-subjects review, and is never presented in this
   document or the accompanying materials as a validated research cohort.
6. **The Information Density Index (Section 1)** is a metric this project proposes,
   not one drawn from prior literature, and has not yet been computed on real data.
7. **This is a proof-of-concept research and demonstration project, not a certified or
   clinically validated medical device**, and no claim in this document should be read
   as asserting otherwise.

---

## 21. References

*This section lists only sources this project has itself verified — either reused,
already-vetted, from this project's own prior research
(`Biological_Minimalism_Yol_Haritasi.md`, §13) or gathered and confirmed (fetched and
checked directly, not cited from memory) during the research pass conducted for this
document.*

Antonsen, E. L., Connell, E., Anton, W., Reynolds, R. J., Buckland, D. M., & Van
Baalen, M. (2023). Updates to the NASA human system risk management process for space
exploration. *npj Microgravity*, 9, Article 72. https://doi.org/10.1038/s41526-023-00305-z

Baevsky, R. M., Petrov, V. M., & Chernikova, A. G. (1998). Regulation of autonomic
nervous system in space and magnetic storms. *Advances in Space Research*, 22(2),
227–234.

DeVirgiliis, L., Goode, N. J., McDowell, K. W., English, K. L., Novo, R., Botros, V.,
et al., & Ploutz-Snyder, L. L. (2025). Spaceflight and sport science: Physiological
monitoring and countermeasures for the astronaut–athlete on Mars exploration missions.
*Experimental Physiology*.

Fei, D. Y., Zhao, X., Boanca, C., Hughes, E., Bai, O., Merrell, R., & Rafiq, A. (2010).
A biomedical sensor system for real-time monitoring of astronauts' physiological
parameters during extra-vehicular activities. *Computers in Biology and Medicine*,
40(7), 635–642.

Kemp, B., Zwinderman, A. H., Tuk, B., Kamphuisen, H. A. C., & Oberye, J. J. L.
(2000). Analysis of a sleep-dependent neuronal feedback loop: the slow-wave
microcontinuity of the EEG. *IEEE Transactions on Biomedical Engineering*,
47(9), 1185–1194. (Sleep-EDF; source of the real EEG data this project's first
training run was actually conducted on — see Section 10.2.)

Grigoriev, A. I., & Egorov, A. D. (1997). Medical monitoring in long-term space
missions. *Advances in Space Biology and Medicine*, 6, 167–191.

Gupta, R., & Ghosh, P. S. (2025). Advancements in health monitoring technologies for
astronauts in deep space missions: A review. *Life Sciences in Space Research*, 47,
190–196.

Kaya, E. Ö., & Kaya, M. (n.d.). Fiziksel Aktivitenin Otonom Sinir Sistemi Üzerindeki
Rolü: Vagus Siniri Perspektifinden Bakış. *Spor Bilimleri*, 89.

Kurt, B. (n.d.). Uzayda Zamanı Yakalamak: Sirkadiyen Ritim.

Liu, C., Chen, L., Ding, J., Huang, L., & Shangguan, D. (2026). Model–data hybrid
thermal management and health monitoring of the space station application fluid loop.
*Results in Engineering*, 109387.

Goldberger, A. L., Amaral, L. A. N., Glass, L., Hausdorff, J. M., Ivanov, P. Ch.,
Mark, R. G., Mietus, J. E., Moody, G. B., Peng, C.-K., & Stanley, H. E. (2000).
PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for
complex physiologic signals. *Circulation*, 101(23), e215–e220.

Lim, W. L., Sourina, O., & Wang, L. P. (2018). STEW: Simultaneous Task EEG Workload
Data Set. *IEEE Transactions on Neural Systems and Rehabilitation Engineering*,
26(11), 2106–2114.

Lundberg, S. M., & Lee, S.-I. (2017). A Unified Approach to Interpreting Model
Predictions. *Advances in Neural Information Processing Systems (NeurIPS) 30.*

McCorry, L. K. (2007). Physiology of the autonomic nervous system. *American Journal
of Pharmaceutical Education*, 71(4), 78.

Mundt, C. W., Montgomery, K. N., Udoh, U. E., Barker, V. N., Thonier, G. C., Tellier,
A. M., et al., & Kovacs, G. T. (2005). A multiparameter wearable physiologic
monitoring system for space and terrestrial applications. *IEEE Transactions on
Information Technology in Biomedicine*, 9(3), 382–391.

NASA. Artemis II Science. NASA Human Spaceflight. Retrieved 2026-08-28 from
https://www.nasa.gov/humans-in-space/artemis-ii-science/

NASA International Space Station Blog (2026a, August 11). Crew Works Vein Scans For
Health and Suit Checks for Spacewalk. https://www.nasa.gov/blogs/spacestation/2026/08/11/crew-works-vein-scans-for-health-and-suit-checks-for-spacewalk/

NASA International Space Station Blog (2026b, March 9). Spacewalk Preps and Health
Checks Using Augmented Reality, Artificial Intelligence. https://www.nasa.gov/blogs/spacestation/2026/03/09/spacewalk-preps-and-health-checks-using-augmented-reality-artificial-intelligence/

NASA Open Science Data Repository (OSDR). Open Science for Life in Space. Retrieved
2026-08-28 from https://osdr.nasa.gov/bio/repo/ — repository-level citation; this
document does not cite a specific OSD accession number (see Section 7).

PubMed ID 10124463. Bioelectrical impedance analysis for measurement of body fluid
volumes: a review. Cited by identifier (see Section 8) because this document could
not independently confirm the full author list through an accessible, non-paywalled
source.

Pimentel, M. A. F., Johnson, A. E. W., Charlton, P. H., Birrenkott, D.,
Watkinson, P. J., Tarassenko, L., & Clifton, D. A. (2017). Toward a Robust
Estimation of Respiratory Rate From Pulse Oximeters. *IEEE Transactions on
Biomedical Engineering*, 64(8), 1914–1929. (BIDMC PPG and Respiration
Dataset; source of the real PPG data this project's second training run was
conducted on — see Section 10.2.)

Pool, S. L. (1975). Physiological Measurement Systems for Advanced Manned Space
Missions. In *Advances in Biomedical Engineering* (pp. 151–215). Academic Press.

Roda, A., Mirasoli, M., Guardigli, M., Zangheri, M., Caliceti, C., Calabria, D., &
Simoni, P. (2018). Advanced biosensors for monitoring astronauts' health during
long-duration space missions. *Biosensors and Bioelectronics*, 111, 18–26.

Schmidt, P., Reiss, A., Duerichen, R., Marberger, C., & Van Laerhoven, K. (2018).
Introducing WESAD, a multimodal dataset for wearable stress and affect detection.
*Proceedings of the 20th ACM International Conference on Multimodal Interaction
(ICMI 2018)*, 400–408.

Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser,
Ł., & Polosukhin, I. (2017). Attention Is All You Need. *Advances in Neural
Information Processing Systems (NeurIPS) 30.*

Wang, W., Mohseni, P., Kilgore, K. L., & Najafizadeh, L. (2023). PulseDB: A large,
cleaned dataset based on MIMIC-III and VitalDB for benchmarking cuff-less blood
pressure estimation methods. *Frontiers in Digital Health*, 4, 1090854.

Yaşa, Ö. (n.d.). Egzersiz ve Sinir Sistemi Arasındaki Nörobiyolojik İlişkinin
İncelenmesi.

---

*Document status: this literature-integration pass is complete. Every citation in
Section 21 was independently fetched and confirmed (title, authors, venue, and
year/volume/pages) during this document's own research process, not reconstructed
from memory, with the exception of the four sources reused directly, and already
vetted, from this project's own prior planning research
(`Biological_Minimalism_Yol_Haritasi.md`, §13). Two gaps this research pass could not
fill without guessing are named as gaps rather than papered over (Sections 11 and 12);
one citation (Section 8) is given by PubMed identifier rather than a guessed author
list. No claim in this document rests on a source that was not actually verified.*
