# Furkan AI — Dashboard Presentation Master Handoff

## 0. Purpose and authority

This document is the single presentation handoff for Furkan and Furkan's AI.
Its purpose is to turn the accepted Biological Minimalism dashboard into an
accurate, visually coherent interactive presentation without requiring the
presentation team to reconstruct the project from commit history or old chat
summaries.

Use this document to:

1. check out the correct dashboard version;
2. select or recapture screenshots;
3. understand what each visualization means;
4. construct the slide narrative;
5. write captions and speaker notes;
6. avoid scientifically unsafe claims.

Do not treat older presentation scripts as current authority when they
conflict with this file. In particular, the old synthetic-only presenter
script predates the accepted real-S14 path and the final Mission Overview
recomposition.

## 1. Immutable dashboard version

The accepted product-code checkpoint for presentation work is:

| Field | Value |
|---|---|
| Repository | `ProfIsmeet/biological-minimalism` |
| Presentation handoff branch | `codex/furkan-dashboard-presentation-handoff` |
| Accepted dashboard parent branch | `codex/mission-overview-independent-visual-audit` |
| Accepted dashboard SHA | `dc2039d53773ebfad763e0716f51876fb8185058` |
| Monitoring verification | `1247/1247 passed` |
| Backend verification | `351 passed, 4 skipped` |
| Production build | `14/14` routes |

The handoff branch contains the accepted dashboard at `dc2039d…` plus this
documentation-only presentation handoff. It intentionally does not merge the
dashboard into `main`.

Furkan must not prepare screenshots from `main`, an older Stage 6 branch, or
the unaudited Ismet source branch. Those versions do not contain all accepted
Mission Overview corrections.

Future Stage 8–10 work will continue independently. The handoff branch is a
stable presentation snapshot so Furkan's deck work can continue without being
invalidated by ongoing frontend development.

## 2. Checkout instructions for Furkan's AI

After cloning the GitHub repository:

```bash
git fetch origin
git switch --track origin/codex/furkan-dashboard-presentation-handoff
git rev-parse HEAD
```

The resolved commit must descend from the accepted dashboard SHA
`dc2039d53773ebfad763e0716f51876fb8185058`.

If the remote handoff branch is not visible, fetch again. Do not silently fall
back to `main`.

## 3. Thirty-second project explanation

Biological Minimalism is a mission-systems demonstrator for a selected
five-modality physiological sensing architecture:

- wrist: PPG + IMU;
- chest: ECG;
- frontal/head module: EEG + EOG.

The dashboard separates three different things that must never be conflated:

1. the selected final sensor architecture;
2. the channels actually available in the active data source;
3. the smaller PPG + IMU pipeline currently used to demonstrate AI-estimated
   heart rate.

The operational demonstration can replay recorded PPG-DaLiA participant S14,
inject controlled sensor faults, withhold invalid output, rebuild the
inference window, and show a fresh recovery. It is not live astronaut
monitoring, not a clinical device, and not proof of population-level
performance.

## 4. One-sentence presentation thesis

> We selected a minimal multimodal sensing architecture, made the limits of
> the available evidence explicit, and built an operational demonstrator that
> fails closed instead of inventing physiological certainty when its source or
> inference pipeline becomes unreliable.

## 5. Scientific truth locks

Every slide, caption, diagram, animation, and spoken sentence must respect the
following rules.

### 5.1 Final architecture

- Final architecture name: `CORE_PLUS_CONTEXT`.
- Wrist module: PPG + IMU.
- Chest module: ECG.
- Head/frontal module: EEG + EOG.
- Total: three body regions/modules and five sensing modalities.
- `MINIMAL_CORE` already includes PPG, IMU, ECG, and frontal EEG.
- EOG is the only modality added by `CORE_PLUS_CONTEXT` beyond
  `MINIMAL_CORE`.
- `CORE_PLUS_CONTEXT` is a conditional evidence–burden selection, not a
  unique mathematical optimum.
- BioZ/EIS is not part of the final architecture. It belongs to Experimental
  Research.

### 5.2 S14 replay and HR inference

- PPG-DaLiA S14 is recorded human research data.
- It is not astronaut telemetry.
- It is one participant, not population validation.
- Current demonstrated HR inference consumes PPG + IMU.
- HR is an AI estimate, not a reference or clinical measurement.
- The current runtime has no simultaneous reference-ground-truth HR channel.
- Do not claim live accuracy, live confidence, medical reliability, or
  clinical validity.
- During a fault or rebuilding interval the current HR output is withheld.
- A missing output is not `0 bpm`.

### 5.3 EEG and EOG

- EEG and EOG remain in the selected final architecture.
- The S14 replay does not provide live EEG/EOG channels to this dashboard.
- Do not describe either as “50% reliable,” partially active, or measured in
  the current replay.
- Do not create flat EEG/EOG waveforms.

### 5.4 Digital Twin

- Status: `ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED`.
- It is a conceptual architecture reference.
- It is not personalized.
- It is not trained or clinically validated.
- It is not spaceflight validated.
- The human figure shows intended sensor regions and interaction structure,
  not a live anatomical simulation.

### 5.5 Faults

- Dashboard faults are explicitly simulated control events.
- They demonstrate fail-closed behavior and recovery choreography.
- They are not hardware failure probabilities.
- They are not proof of autonomous fault detection or clinical safety.

## 6. Current route map

| Route | Presentation role | Recommended use |
|---|---|---|
| Mission Overview | Primary operational story | Main source of screenshots and live demo |
| Live Signals | Detailed signal/source view | Optional technical appendix or backup demo |
| System Brief | Architecture and project explanation | Architecture slide support |
| Experimental Research | Historical/offline scientific evidence | Evidence slide; keep separate from live telemetry |
| Digital Twin Reference | Conceptual sensor-location reference | Digital Twin boundary slide |
| AI Insights | Source-aware AI presentation | Optional; never imply replay confidence exists |
| Mission Timeline | Session events and chronology | Optional appendix |
| Settings | Reduced motion and user preferences | Accessibility/demo-preparation appendix |

The deck should be centered on Mission Overview. Avoid making every route a
separate equal-weight slide.

## 7. Mission Overview: how to explain the page

Mission Overview is a five-part operational narrative.

### 7.1 Command Deck

Answers:

- Which source/session is active?
- Is the source authoritative?
- Is a simulated fault active?
- Which body region is affected?
- Is current HR output available?

The opening viewport contains:

- stable session/source/status fields;
- the accepted human sensor-location figure;
- four concentric inference-integrity rings;
- the recent HR estimate trend.

The old fluctuating “Last confirmed frame” display has been removed. Stable
categorical phase language is used instead.

### 7.2 Signal Geometry

Answers:

- Which channels are part of the selected architecture?
- Which channels are provided by the current source?
- What do the real PPG, IMU, and ECG signals look like?

The radar is binary coverage, not performance. Lime represents static
architecture membership. Cyan represents channel provision by the confirmed
source. Exact usability/fault state is stated in the table beside it.

### 7.3 Inference Integrity

Answers:

- In what order does HR become valid?
- At which stage is output blocked?

The chain is:

`Source → PPG + IMU → Window assembly → HR model → HR output`

### 7.4 Fault & Recovery

Answers:

- When did a simulated adverse event occur?
- When was HR withheld?
- How long did rebuilding take?
- When did a new output return?

The timeline contains genuine gaps for withheld output. It must not be
described as continuous HR through the fault.

### 7.5 Operational Boundary

Answers:

- Which dataset, subject, channels, and model produced the displayed output?
- What does the demonstrator explicitly not claim?

This final section is essential for scientific trust and should not be cropped
out of every presentation artifact.

## 8. What the visualizations mean

### 8.1 Four concentric rings

Outside to inside:

1. Source authority
2. PPG input
3. IMU input
4. HR output

All rings always use the same fixed 300-degree sweep. Arc length is decorative
structure and does not encode a number.

The rings do not represent:

- percentage;
- confidence;
- probability;
- accuracy;
- reliability;
- readiness score.

Use the phrase:

> “Four categorical gates in the inference path.”

Do not use the phrase:

> “The rings show how confident the AI is.”

### 8.2 Architecture radar

Axes:

- PPG
- IMU
- ECG
- EEG
- EOG

Lime polygon:

- static membership in the selected final architecture.

Cyan polygon:

- channel provision by the current confirmed source.

The radar uses binary 0/1 semantics. It is not a score and does not compare
five different physiological units.

During a PPG/IMU fault the channel can remain source-provided while its exact
current usability is reported separately as faulted or rebuilding. This
distinction was added during independent review to prevent “present but
temporarily unusable” from being confused with “absent from the source.”

### 8.3 HR trend

- Shows recent AI-estimated HR in bpm.
- Uses linear segments rather than decorative smoothing.
- Gaps mean output was unavailable or withheld.
- No confidence band is shown because the runtime does not provide genuine
  predictive uncertainty.
- No clinical-normal range is claimed.

### 8.4 Signal ribbons

- PPG, IMU, and ECG retain separate scales.
- Their unlike units are not combined.
- EEG/EOG are shown as unavailable in the current source rather than as flat
  zero-valued signals.

### 8.5 Fault/recovery timeline

- X-axis: replay time.
- Y-axis: HR estimate in bpm.
- Fault and rebuilding intervals are marked.
- HR remains absent until a new, fresh output is produced.

## 9. Recommended twelve-slide presentation

Furkan's AI may adapt the visual style and wording, but it must preserve this
narrative and the scientific constraints.

### Slide 1 — Biological Minimalism

**Purpose:** Establish the project and final thesis.

**Headline:** `Biological Minimalism`

**Subheadline:** `A fail-closed multimodal physiological monitoring demonstrator`

**Visual:** Clean title composition using a subtle crop of the accepted human
figure or the nominal Mission Overview hero.

**Spoken line:**

> “Our objective was not to maximize sensor count. It was to identify a
> defensible minimal architecture and demonstrate how its operational state
> can be communicated without inventing certainty.”

### Slide 2 — The problem

**Purpose:** Explain why minimalism matters.

**Content:**

- Long-duration monitoring has evidence, wearability, power, and integration
  constraints.
- More sensors do not automatically mean a more defensible system.
- The interface must distinguish architecture intent from currently observed
  data.

**Visual:** A simple three-part tension diagram: evidence, physiological
coverage, operational burden.

Do not use arbitrary numerical percentages.

### Slide 3 — Selected architecture

**Purpose:** Present the final five-modality configuration.

**Visual:** Digital Twin front view or System Brief architecture map.

**Labels:**

- Wrist — PPG + IMU
- Chest — ECG
- Frontal — EEG + EOG

**Caption:**

> “CORE_PLUS_CONTEXT: five modalities across three wearable regions.”

**Required note:** EOG is the only addition beyond MINIMAL_CORE.

### Slide 4 — Operational command deck

**Purpose:** Show the dashboard as a finished product surface.

**Primary screenshot:**

`frontend/qa-screenshots/codex-mission-overview-independent-visual-audit/01-1440-nominal-first-viewport.png`

**Secondary/full-page option:**

`frontend/qa-screenshots/codex-mission-overview-independent-visual-audit/02-1440-nominal-full-page.png`

**Callouts:**

- Confirmed source/session identity
- Anatomical sensor regions
- Four categorical inference gates
- Current AI-estimated HR
- Recent HR trend

**Spoken line:**

> “This is the operational summary: what source is active, which inputs are
> available, whether the inference chain is intact, and whether a current HR
> estimate can honestly be shown.”

### Slide 5 — Integrity without invented confidence

**Purpose:** Explain the concentric ring graphic.

**Screenshot:**

`frontend/qa-screenshots/codex-mission-overview-independent-visual-audit/03-ring-nominal.png`

**Labels:** Source authority, PPG input, IMU input, HR output.

**Caption:**

> “Categorical pipeline integrity — not an AI-confidence percentage.”

The slide must explicitly state that every ring uses a fixed 300-degree sweep.

### Slide 6 — Architecture versus current source

**Purpose:** Explain why five selected modalities do not mean five live replay
channels.

**Screenshot:**

`frontend/qa-screenshots/codex-mission-overview-independent-visual-audit/04-radar-nominal.png`

**Supporting screenshot:**

`frontend/qa-screenshots/codex-mission-overview-independent-visual-audit/06-signal-ribbons-desktop.png`

**Caption:**

> “Lime shows selected architecture membership; cyan shows channels provided
> by the current confirmed source.”

**Required note:** EEG and EOG remain architecture members but are not supplied
by the S14 replay.

### Slide 7 — From signal to HR estimate

**Purpose:** Explain the demonstrated inference path.

**Screenshot:**

`frontend/qa-screenshots/codex-mission-overview-independent-visual-audit/07-pipeline-available.png`

**Supporting screenshot:**

`frontend/qa-screenshots/codex-mission-overview-independent-visual-audit/05-hr-trend-nominal.png`

**Flow:**

`PPG + IMU → synchronized window → trained HR model → AI-estimated HR`

**Required boundary:** No reference-ground-truth HR channel is present in this
runtime.

### Slide 8 — Fail closed under a simulated fault

**Purpose:** Demonstrate operational honesty.

**Primary screenshot:**

`frontend/qa-screenshots/codex-mission-overview-independent-visual-audit/18-ppg-fault-first-viewport.png`

**Detail screenshots:**

- `19-ring-fault.png`
- `20-radar-ppg-fault.png`
- `21-hr-fault-gap.png`
- `22-pipeline-blocked.png`

All detail files are in the same evidence directory.

**Spoken line:**

> “When a required input is deliberately corrupted, the interface localizes
> the fault and withholds the current HR output instead of preserving an old
> number or displaying a fake zero.”

### Slide 9 — Rebuilding and fresh recovery

**Purpose:** Show that clearing a fault does not instantly make stale data
valid.

**Screenshots:**

- `frontend/qa-screenshots/codex-mission-overview-independent-visual-audit/23-ring-rebuilding.png`
- `frontend/qa-screenshots/codex-mission-overview-independent-visual-audit/24-ring-recovered.png`
- `frontend/qa-screenshots/codex-mission-overview-independent-visual-audit/25-hr-recovered.png`
- `frontend/qa-screenshots/codex-mission-overview-independent-visual-audit/08-fault-recovery-timeline.png`

**Narrative:**

1. Fault is cleared.
2. HR remains unavailable while a synchronized window rebuilds.
3. A fresh model output arrives.
4. Only then does the dashboard report recovery.

### Slide 10 — Digital Twin boundary

**Purpose:** Present the human figure without overstating maturity.

**Recommended screenshots:**

- `frontend/qa-screenshots/codex-stage7-final-acceptance-closure/zoom100-reference-page.png`
- `frontend/qa-screenshots/codex-stage7-final-acceptance-closure/zoom200-wrist-focus.png`
- `frontend/qa-screenshots/codex-stage7-final-acceptance-closure/zoom200-chest-focus.png`
- `frontend/qa-screenshots/codex-stage7-final-acceptance-closure/zoom200-frontal-focus.png`

**Caption:**

> “Architecture-only digital human reference — untrained, unvalidated, and
> not personalized.”

Do not call it a patient-specific digital twin.

### Slide 11 — Evidence and engineering decision

**Purpose:** Connect the dashboard to the project’s scientific and engineering
selection process.

**Recommended screenshots:**

- `frontend/qa-screenshots/ismet-stage6-final-audit-closure/15-architecture-delta-matrix.png`
- `frontend/qa-screenshots/ismet-stage6-final-audit-closure/16-evidence-burden-matrix.png`
- `frontend/qa-screenshots/ismet-stage6-final-audit-closure/17-ppg-dalia-ptt-small-multiples.png`
- `frontend/qa-screenshots/ismet-stage6-final-audit-closure/18-sleep-and-ppgdalia-subject-small-multiples.png`

**Narrative:**

- Evidence is multi-source and modality-specific.
- Scientific results are frozen offline artifacts.
- The live dashboard does not generate the paper’s results.
- The final architecture balances evidence against operational burden.

### Slide 12 — What is proven and what remains

**Purpose:** Close with credibility rather than inflated certainty.

**Demonstrated:**

- selected five-modality architecture;
- real recorded S14 replay;
- PPG + IMU HR inference;
- source-aware visualization;
- simulated fault, withheld output, rebuilding, and fresh recovery;
- explicit scientific boundaries.

**Not claimed:**

- live astronaut monitoring;
- clinical validation;
- flight qualification;
- population validation from S14;
- personalized Digital Twin;
- live predictive confidence;
- autonomous hardware fault diagnosis.

**Closing line:**

> “The contribution is not a claim of flight readiness; it is a defensible
> architecture and an operational demonstrator whose interface remains honest
> when the evidence becomes incomplete.”

## 10. Recommended screenshot policy

### 10.1 Fast path

The repository already contains independently inspected PNGs. Furkan may use
these immediately for draft slides. This avoids waiting for a local backend,
dataset, checkpoint, or replay cycle.

### 10.2 Fresh-capture path

Use a fresh local capture when:

- the presentation requires a different crop or resolution;
- labels must be larger for projection;
- a live pointer/callout will be added;
- a later accepted frontend branch intentionally changes the screen.

When recapturing:

- preserve the screenshot’s aspect ratio;
- do not stretch UI screenshots;
- avoid browser chrome unless proving a browser setting;
- do not crop away the source/session identity when discussing real S14;
- do not crop away disclaimers when discussing scientific validity;
- do not composite nominal HR over a fault-state screenshot;
- do not recolor state indicators;
- do not add invented percentage labels.

### 10.3 Presentation-safe cropping

- Hero screenshot: crop to the status, human, orbit, and HR plot.
- Orbit detail: keep the full legend and the “not confidence” statement.
- Radar detail: keep both series legend and binary-coverage disclaimer.
- Signal view: include channel names, sample rates, and no-channel EEG/EOG rows.
- Fault screenshot: include the full fault description and unavailable HR.
- Recovery slide: show rebuilding and recovered screenshots as a sequence,
  not as an unlabeled before/after collage.

## 11. Optional interactive elements for the deck

The presentation may be interactive, but animations must clarify state rather
than decorate it.

Recommended interactions:

- Click through architecture regions: Wrist → Chest → Frontal.
- Reveal the five radar axes one by one.
- Animate the inference chain in causal order.
- Use a three-frame fault sequence: Nominal → Fault/withheld → Recovered.
- Allow a “scientific boundaries” panel to expand on demand.

Avoid:

- rotating charts;
- animated fake waveforms;
- continuously pulsing status indicators;
- ring animations that look like percentages filling up;
- particles, excessive glow, or generic science-fiction decoration;
- animations that continue under a reduced-motion presentation mode.

## 12. Visual direction for Furkan's AI

The slide deck should inherit the dashboard’s accepted visual language:

- near-black/navy canvas;
- controlled cyan and teal for observed/operational data;
- lime only for selected architecture or final-output emphasis;
- blue for IMU/contextual comparison;
- amber for awaiting/rebuilding;
- coral for simulated fault;
- pale neutral primary text;
- restrained grid lines and borders;
- large scientific graphics rather than grids of small cards.

Typography:

- titles must remain projector-readable;
- avoid uppercase microtext;
- use tabular numerals for measurements;
- use one sentence per key visual rather than dense paragraphs;
- never shrink scientific caveats into unreadable footnotes.

Do not paste full dashboard screenshots onto every slide. Alternate between:

- full interface establishing shots;
- focused visual crops;
- simplified architecture diagrams;
- short scientific-boundary slides.

## 13. Claims Furkan's AI may safely make

- “The selected architecture contains five modalities across three wearable
  regions.”
- “The S14 demonstration uses recorded human research data.”
- “The demonstrated HR pipeline consumes PPG and IMU.”
- “The dashboard distinguishes selected architecture from current-source
  coverage.”
- “A simulated required-input fault causes the current HR output to be
  withheld.”
- “Recovery requires a newly assembled synchronized window and a fresh model
  output.”
- “Missing data is shown as unavailable rather than zero or nominal.”
- “The Digital Twin route is explicitly architecture-only and unvalidated.”
- “The interface is a mission-systems demonstrator.”

## 14. Claims Furkan's AI must not make

- “This monitors astronauts live.”
- “The system is flight ready/flight qualified.”
- “The system is clinically validated.”
- “S14 validates the model across a population.”
- “The dashboard proves medical reliability.”
- “The rings show AI confidence.”
- “EEG is 50% reliable.”
- “The radar compares sensor quality.”
- “The model detects every sensor failure automatically.”
- “The model remains accurate during missing required samples.”
- “The Digital Twin is personalized or trained.”
- “The displayed HR is ground truth.”
- “The five modalities all feed the current HR model.”

## 15. Suggested live-demo choreography

If Furkan also needs a short live-dashboard sequence:

1. Open Mission Overview.
2. Confirm Presenter Preflight.
3. Use `Load canonical demo` to select recorded PPG-DaLiA S14.
4. Start replay.
5. Point out source identity, PPG/IMU/ECG provision, and absent EEG/EOG.
6. Explain the four categorical rings.
7. Show the PPG + IMU inference pipeline.
8. Apply one simulated PPG fault.
9. Show HR becoming unavailable and the pipeline blocking.
10. Clear the fault.
11. Explain the rebuilding interval while HR remains unavailable.
12. Wait for a fresh recovered output.
13. End on Operational Boundary or the Digital Twin boundary.

Never click controls rapidly to skip the rebuilding period. The delay is part
of the scientific story.

## 16. Demo recovery guidance

If the interface reports unavailable, disconnected, rebuilding, or source
error, do not hide the message. The system is designed to fail closed.

Recovery order:

1. Stop clicking controls.
2. Read the exact status.
3. Check Presenter Preflight.
4. Retry `Load canonical demo` once if a named partial/transient step failed.
5. Refresh once for a disconnected frontend.
6. If the same infrastructure error repeats, stop the live interaction and
   continue with the committed evidence screenshots.

The presentation must have the nominal, fault, rebuilding, and recovery PNGs
available locally before the jury session.

## 17. Known limitations to disclose internally

- Actual OS VoiceOver acceptance remains deferred.
- Genuine automated browser 200% page-zoom verification remained externally
  blocked in the final Mission Overview audit; no DPI substitute was accepted.
- Docker/container runtime verification remains an integration-stage item.
- The current snapshot is not yet merged to `main` because Stage 8–10 work is
  continuing.

These limitations do not invalidate the committed screenshots or the accepted
Mission Overview behavior, but they must not be silently reported as passed.

## 18. Required output from Furkan's AI

Furkan's AI should deliver:

1. An editable interactive presentation.
2. A PDF export.
3. A slide-by-slide source/evidence ledger.
4. Speaker notes for every slide.
5. A list of every screenshot used with repository-relative path.
6. A list of any visual redrawing or annotation performed.
7. Confirmation that no metric or percentage was invented.
8. Confirmation that all scientific non-claims remain visible or spoken.
9. A short presenter recovery appendix.
10. A final 3–5 minute timed narration.

Before declaring the presentation complete, Furkan's AI must independently
check every slide against Sections 5, 13, and 14 of this document.

## 19. Final handoff summary

The stable presentation snapshot is the GitHub branch
`codex/furkan-dashboard-presentation-handoff`, descended from accepted
dashboard SHA `dc2039d53773ebfad763e0716f51876fb8185058`.

Use the committed independent-audit screenshots for immediate slide creation.
Use Mission Overview as the central product narrative. Treat System Brief,
Experimental Research, Digital Twin Reference, and Live Signals as supporting
routes. Preserve the distinction between selected architecture, observed
channels, demonstrated inference, offline evidence, and future conceptual
work.

The presentation succeeds when the audience understands both what the system
demonstrates and where its evidence boundary ends.
