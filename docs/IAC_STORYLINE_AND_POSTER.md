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
