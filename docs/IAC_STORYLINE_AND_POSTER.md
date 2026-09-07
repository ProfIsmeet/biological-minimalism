# IAC 2026 Storyline & Poster / Presentation Structure

Recommended oral/poster narrative. Spaceflight is **motivation, not validation**. Every headline
number traces to a committed artifact.

## Recommended storyline (oral)

- **Problem** — dense physiological monitoring creates real sensing burden (mass, contacts, power, comfort), acute in spaceflight.
- **Research question** — which sensing components actually add *target-specific* value worth their human burden?
- **Method** — controlled marginal sensor evaluation: capacity control + negative control + heterogeneity + burden model + a refusal-capable decision gate.
- **Positive example** — IMU adds a small HR value *after* capacity control (5/5 seeds).
- **Negative/heterogeneous example** — a second PPG site does not consistently help HR (s2-sensitive).
- **Second target** — EOG shows a modest, preliminary sleep-stage value (controls pending).
- **Operational layer** — scientific value alone does not define minimalism; burden lives at the body region/module/contact.
- **Honest result** — the final architecture remains NOT_READY.
- **Contribution** — a reproducible method that refuses unjustified sensor selection.
- **Future** — converge toward a personalized Biological Digital Twin architecture.

## Poster / interactive presentation sequence

| # | Section | One-sentence takeaway | Key artifact-backed number | Claim boundary |
|---|---|---|---|---|
| 1 | Motivation | Sensing burden is a real operational cost. | — | motivation, not validation |
| 2 | Biological Minimalism principle | Justify each component per target vs burden. | — | principle, not a sensor count |
| 3 | Scientific pipeline | Control-anchored marginal evaluation. | 3 experiments, 5 seeds each | per-target only |
| 4 | HR case (IMU) | Small but replicated capacity-controlled benefit. | C→B ~0.776 bpm, 5/5 | not pure ~20.6% |
| 5 | Negative PTT case | Second site not consistently helpful. | 2/4 subjects better; Δ≈+1.46 | not global removal |
| 6 | Sleep control case | Modest EOG benefit; controls pending. | 0.7473→0.7693, 4/5 | preliminary, n=3 |
| 7 | Operational burden | Burden = body region/module/contact, not count. | 0 new modules for colocated IMU | unknowns remain |
| 8 | Decision gate | The method can say "not yet." | IMU CONDITIONAL / EOG FUTURE | no thresholds forced |
| 9 | Research Mode live demo | Evidence is inspectable end-to-end. | live `/research` | pending shown as pending |
| 10 | NOT_READY conclusion | Honesty over a fabricated frontier. | Pareto NOT_READY | no frontier computed |
| 11 | Future Digital Twin | Proposed deployment architecture. | 153,801 params (untrained) | architecture-only |

## Demo flow (2–3 min)

Open `/research` → Case 1 (IMU, show capacity + shuffled controls) → Case 2 (PTT heterogeneity,
s2 toggle narrative) → Case 3 (Sleep A/B frozen, shuffled/secondary shown as PENDING) →
Architecture status per case → Global Pareto NOT_READY with blocker breakdown → Digital Twin page
(clearly labeled synthetic/untrained).

---

## Day 8/9 Update — Sleep panel (stronger, still honest)

The sleep panel can now show three bars (EEG-only A / aligned-EOG B / shuffled-EOG C) for BOTH
evaluations, kept visually separate:

- **Primary (n=3):** B > C in 5/5 seeds; per-subject note "concentrated in SC4011".
- **Prospective secondary holdout (n=8):** B > A in 5/5 seeds; B > C in 5/5 seeds; 6/8 subjects
  B>A, 7/8 B>C; zero retraining.
- **Class-level (secondary):** REM large positive (+0.150), N3 regression (−0.043) shown, not hidden.

Poster caption (approved framing): *"Aligned EOG showed positive within-dataset marginal value
with matched-control and prospective secondary-holdout support."* Do NOT show a single pooled
score or an "n=11" test. Spaceflight remains motivation, not a validated claim; no astronaut
validation. Global architecture panel stays **UNRESOLVED / NOT_READY**.

---

## Day 11 Update — The burden half of minimalism

Storyline segment (one clean paragraph):

> Scientific value is only half of minimalism. We then ask what physical burden the candidate
> actually adds. A sensor with real marginal value but a new body-worn contact is not the same as
> one that rides along for free.

The narrative triangle (three concrete examples, deliberately *not* ranked into one score):

- **IMU:** small scientific gain, almost no new physical contact burden **if co-located** on the wrist
  (0 new region / module / contact; reference power ~0.018 mW). Attractive but CONDITIONAL.
- **EOG:** clearer sleep value (matched-control + secondary support), but **+2 ocular sensing
  contacts** and a new peri-ocular site. Value is real; burden is real. CONDITIONAL.
- **Second PPG:** heterogeneous/negative scientific value **plus** a new physical optical site
  (+1 site, +1 contact region, highest raw data-rate). DEPRIORITIZED for HR, not globally removed.

### Poster / slide engineering comparison panel

Single descriptive table — **no global ranking, no total score, no formal Pareto**:

| Candidate | Target | Scientific direction | New body region | New module | New contacts | Reference component power | Readiness |
|---|---|---|---|---|---|---|---|
| Wrist IMU | Heart rate | Modest positive (capacity-controlled) | 0 | 0 | 0 | ~0.018 mW (band 0.018–0.378) | CONDITIONAL |
| Horizontal EOG | Sleep stage | Positive w/ control + secondary | 0 or 1 | 0 (shared head) | +2 | Not ready (shared AFE) | CONDITIONAL |
| Second PPG site | Heart rate | Aggregate negative / heterogeneous | 1 | OPEN | +1 | Not ready (LED-dominated) | DEPRIORITIZE |

Panel footer (required): *System average power, system mass, and full BOM remain **Not ready**;
the raw data-rate figure (~48.068 kbps) is a partial lower bound, not radio bandwidth. Unknowns are
shown as "Not ready", never 0. Global architecture stays **UNRESOLVED**, formal Pareto **NOT_READY**.*
