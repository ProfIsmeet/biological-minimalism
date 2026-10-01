# Scientific consistency matrix

Each §7 truth lock, how it is now enforced, and whether the enforcement is a
build-time guarantee or a one-time inspection. A one-time inspection is worth
less, and is marked as such.

## Architecture truth (§7.1)

| Lock | Enforcement | Kind |
|---|---|---|
| Final architecture is `CORE_PLUS_CONTEXT`: wrist PPG+IMU, chest ECG, frontal EEG+EOG — 3 regions, 5 modalities | `lib/architecture` constants, unchanged this stage; rendered copy asserted on `/system-brief` | guard + inspection |
| EOG is the **only** addition beyond `MINIMAL_CORE` | copy inspected on `/system-brief` and `/research/experimental` | inspection |
| IMU must never be described as newly added | tree-wide guard, negation-aware | **build-time** |
| BioZ/EIS is not in the final architecture | retained only as experimental evidence on `/research/experimental`; `ExperimentalBoundary` preserved | inspection |
| `CORE_PLUS_CONTEXT` is a conditional evidence–burden selection, not a unique optimum | tree-wide guard rejects "unique/mathematically optimal" phrasing | **build-time** |

## Data provenance (§7.2)

| Lock | Enforcement | Kind |
|---|---|---|
| S14 is recorded human research data, one participant — not astronaut telemetry, not population validation | `verify-rendered-routes` rejects "astronaut telemetry" and "population validated" in visible text on every route | **build-time** |
| HR is AI-estimated from PPG+IMU | `HrInferencePanel` and `ScopeProvenanceFooter` copy, unchanged | inspection |
| No reference ground-truth HR channel exists | tree-wide guard, negation-aware (the required disclaimers are permitted; an affirmative claim is not) | **build-time** |
| No invented confidence, reliability, certainty, accuracy, or clinical-normal status | `/ai-insights` rebuilt source-aware; synthetic output labelled synthetic | guard + inspection |
| Missing HR is unavailable, never `0 bpm` | tree-wide guard **and** rendered-route guard | **build-time (both layers)** |
| Frozen experiment metrics stay offline artifacts | not surfaced as live telemetry on any route | inspection |

## Digital Twin boundary (§7.4)

| Lock | Enforcement | Kind |
|---|---|---|
| `ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED` preserved | asserted rendered on `/digital-twin`; scope-language check reads **both** halves of the split route | **build-time** |
| Never described as adapted by a percentage | tree-wide guard on `overall_adaptation`, `% Adapted`, `Overall Adaptation`, `Adaptation Score`, `adaptationScore`; plus rendered-route visible-text guard | **build-time (both layers)** |
| Never personalized, trained, clinically or spaceflight validated, or predictive | tree-wide guard, negation-aware; rendered-route guard | **build-time** |
| No route may reintroduce `% Adapted`, overall adaptation scores, or success badges | the only carrier (`DigitalTwinPanel`) is deleted, with an existence guard | **build-time** |

## State semantics (§7.6)

`Missing != zero`, `unknown != false`, `unavailable != nominal`,
`pending != failed`, `historical != current`, `no-channel != flat waveform`.

Three concrete violations of the first rule were found and fixed this stage,
all of the same shape — an empty chart axis standing in for a quantity that
does not exist:

- `/ai-insights` confidence history during replay (H-3).
- `/mission-timeline` circadian trend during replay (M-10).
- A missing replay timestamp now renders as a session-clock offset that says
  so, never as a fabricated replay position; a non-finite timestamp is treated
  as missing rather than rendered as `NaN` (asserted directly).

`historical != current` is additionally enforced structurally on
`/mission-timeline`: the conceptual checkpoints sit behind a hard rule and a
"Not session data" badge, below the real session chronology rather than in
place of it.

## Event-origin integrity (§14)

A simulated operator action silently reclassified as source-reported would be
a scientific misstatement that still renders perfectly, so the mapping is
asserted behaviourally rather than by inspection. All 13 event kinds are
covered, and exhaustiveness is enforced by deriving the kind list from the
`Record` the compiler already forces to be total — a kind added to the union
cannot be left without an origin.

| Origin | Kinds |
|---|---|
| Simulated control | `fault_applied`, `fault_cleared` |
| Source-reported | `source_connected`, `source_changed`, `replay_loaded`, `replay_started`, `replay_paused` |
| Inference transition | `warmup_started`, `prediction_available`, `prediction_unavailable`, `prediction_recovered` |
| Transport | `disconnected`, `source_error` |

Every origin is rendered as a **word** as well as a colour, so the distinction
does not depend on colour perception.

## Time-basis integrity (§14)

This runtime genuinely has two clocks. Mixing them unlabelled is a scientific
error, not a cosmetic one. Enforced behaviourally: a row with a replay position
reads `t+N.Ns replay`; one without reads `+N.Ns session`, an offset from the
first event observed in this interface session. The caption states whether one
or both clocks appear. Nothing is fabricated.

## What is NOT enforced at build time

The following rest on inspection alone and would not fail a build if a future
change broke them. They are the honest weak points of this matrix:

- That `EOG` is the only addition beyond `MINIMAL_CORE` (the claim is prose, and
  a guard that parsed it would be guessing at meaning).
- That BioZ/EIS stays confined to experimental framing.
- That frozen experiment metrics are not re-presented as current-person values.
- That the architecture constants themselves remain correct — they were not
  modified this stage, and no test asserts their scientific content.
