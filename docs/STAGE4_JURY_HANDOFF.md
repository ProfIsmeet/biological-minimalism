# Stage 4 Jury Handoff — Expansion Science

Evidence-backed answers to likely IAC reviewer questions, scoped to what
this expansion-science branch (Stage 1B–4) actually established. Every
answer names its evidence and its limitation.

**Why more datasets?** To test whether marginal-sensor-value findings from
this project's original datasets (PPG-DaLiA, Sleep-EDF, QDE) generalize
beyond a single device/subject/protocol family — a standard external-
validity check, not dataset accumulation for its own sake. Two of five
attempts (GalaxyPPG, LBNP) are currently blocked by data access, not
completed — see the access-attempt artifacts.

**Did the IMU result replicate?** Unresolved. The independent-family
attempt (GalaxyPPG) is blocked by a reproducible Zenodo access failure this
session; the frozen protocol is ready to execute the moment access is
available. We do not claim replication we have not run.

**Why BioZ?** Bio-impedance is this project's real candidate for a
non-invasive fluid-status proxy. QDE V2 tested whether adding leg
segments improves a body-mass-change estimate over arm+trunk alone; the
answer, honestly, is a negative-leaning, single-subject-dominated result
(see QDE V2 row below) — not evidence BioZ is worthless, but not evidence
leg BioZ specifically earns its burden cost either.

**Why leg BioZ specifically?** Because upper-body-only BioZ was already in
this project's inherited work; legs were the natural next marginal-value
question, and QDE's own file already contains real leg impedance
measurements — no new dataset was needed to ask this question.

**Does QDE prove fluid shift?** No. QDE is a terrestrial, exercise-induced
dehydration protocol — not microgravity fluid shift, not TBW, not
astronaut-validated. See `docs/STAGE1B_EXPANSION_FORBIDDEN_CLAIMS.md`.

**Why LBNP?** It is the closest terrestrial analog this project could find
for centrally-redistributed hypovolemic stress, using a real, peer-reviewed,
open dataset with an externally-imposed (not device-derived) pressure
target. It remains untrained this sprint (data access blocked).

**Is LBNP microgravity?** No — it is a ground-based lower-body negative
pressure chamber protocol. It never establishes microgravity fluid shift or
astronaut validation, even if a future run shows a positive result.

**Why only four EEG channels?** The four (AF7/AF8/TP9/TP10) were frozen
*before* seeing any results because they match a real, currently-shipping
consumer EEG headband's exact electrode geometry — tying the "wearable
minimalism" framing to a physical product, not an arbitrary guess. Whether
they actually retain enough information for this specific task is an open
question this sprint could only begin to probe (a small bounded diagnostic,
not the full cohort).

**What if full EEG wins?** Then the honest finding is that this specific
task's information is spatially distributed beyond a 4-electrode frontal/
mastoid subset — a real, reportable negative-for-minimalism result, not
something to be redesigned away.

**What if sparse EEG wins (or ties)?** Then it is reported as a genuinely
useful minimalism finding for *this task, this cohort, this frozen channel
subset, this model* — never generalized to "four electrodes capture
cognition."

**Which sensors are actually justified?** Wrist PPG+IMU has the strongest
inherited evidence (PPG-DaLiA, unreplicated-yet on an independent dataset).
Sleep EEG+EOG has been reconfirmed under corrected seeding. Everything else
in this sprint (leg BioZ, thoracic EIS, sparse EEG) is either negative-
leaning, blocked, or too bounded to conclude — stated plainly, not
minimized.

**Why is architecture still unresolved?** Because `architecture_evidence_
handoff_stage4.json`'s `final_architecture_status` is explicitly
`UNRESOLVED` — this branch is authorized only to gather and organize
evidence, not to select a final sensor architecture (Section 70, Section
93). That decision requires the integrated Claude+Ismet line and an
independent audit this branch cannot perform alone (Section 6).

**Which results were negative?** QDE V2 leg-BioZ (single-subject-dominated,
aggregate mean unfavorable). ds003838's bounded diagnostic cannot yet
support any conclusion either way.

**Which experiment is weakest?** The ds003838 bounded diagnostic by a wide
margin — at most 2-3 subjects, orders of magnitude short of the frozen
n=65 cohort, included only to prove the access/loader pipeline works, not
as scientific evidence.

**Which result depends most on one subject?** QDE V2 — subject 2's
A-minus-B delta (−0.71 kg) is roughly 9× the typical subject's magnitude and
flips the aggregate sign relative to the 7-of-10-subject majority
direction. Disclosed explicitly, not averaged away.

**Are different metrics comparable?** No, and this branch does not combine
them — MAE (bpm), MAE (kg), macro-F1, and MAE (mmHg) are reported
separately per experiment with no unified score (Section 67).

**Why should an IAC reviewer care?** Because this branch demonstrates the
project's methodology holds up under its own scrutiny even when results are
inconvenient: a real negative result was published rather than hidden, two
real access failures were disclosed rather than silently worked around, and
a small partial-cohort diagnostic was clearly separated from a frozen full-
cohort claim rather than blurred together.
