# Sensor Interaction Limitation — Formal Documentation (Day 7)

**Master-review finding (Reviews A and C):** one-at-a-time marginal sensor
experiments do NOT prove a globally minimal sensor subset when sensor
interactions may be non-additive. This document formally records that
limitation as a permanent property of this project's methodology, not
something one more experiment will resolve.

## The limitation, precisely

Every marginal-value experiment this project has run (PPG-DaLiA IMU,
PTT second PPG site, Sleep-EDF EOG) measures:

```
Value(baseline + component X) - Value(baseline)
```

for one specific baseline. It does **not** measure:

```
Value(baseline + X + Y) - Value(baseline + X) - Value(baseline + Y)
```

for any pair of components X, Y. **The additive assumption
`Value(A+B) ≈ Value(A) + Value(B)` is unsupported by any experiment this
project has run.** Two components could interact in either direction:

- **Redundancy/negative interaction**: components carry overlapping
  information, so their combined value is less than the sum of their
  individual values (e.g. two PPG sites at different locations might
  partially duplicate the same pulse-wave information).
- **Synergy/positive interaction**: components are individually weak but
  jointly informative (e.g. IMU alone predicts nothing about HR, but IMU +
  PPG together lets the model separate motion artifact from real pulse
  signal — arguably part of why PPG+IMU ever showed a real, capacity-
  controlled benefit in this project's own PPG-DaLiA result).

## Consequence: greedy sensor-by-sensor selection cannot guarantee a global optimum

Even if every single-component marginal-value experiment in this
project's evidence base were unambiguously positive, **summing or
ranking those isolated positive results and picking the top N does not
guarantee the best N-sensor combination**, because interaction effects
are neither measured nor assumed to be zero. This is a standard
limitation of any greedy/marginal feature-selection procedure applied to
a system with unknown interaction structure, and it applies to this
project's entire methodology, not to any single experiment's flaws.

## What current evidence does NOT establish

- A globally minimal multimodal sensor architecture for any target.
- That the sensors validated as individually positive (e.g. synchronized
  wrist IMU for HR, after the Day 7 capacity correction) would remain
  equally valuable, more valuable, or less valuable in combination with
  any other candidate component this project has evaluated or might
  evaluate later.
- That two independently negative-marginal-value components are jointly
  useless — the two might only show value together (synergy case, not
  contradicted by either single-component negative result).

## How interaction evidence COULD later be measured (future work, not started)

A full factorial design, under one shared dataset/target/protocol:

```
baseline
baseline + A
baseline + B
baseline + A + B
```

evaluated with the same subject-disjoint split, same seeds, same
capacity-fairness discipline this project now applies (post Day 7
capacity-confound repair) to every pairwise cell. The `baseline+A+B` cell
directly measures the interaction term:
`interaction = Value(A+B) - Value(A) - Value(B) + Value(baseline)`.

This is **future work**, not started in this sprint. It requires a
dataset with at least two independently-added candidate components
recorded simultaneously with a shared baseline and target — none of this
project's current three experiments (PPG-DaLiA: only IMU; PTT: only a
second PPG site; Sleep-EDF: only EOG) has two independently-addable
components available in the same dataset, so a genuine interaction
experiment would require identifying a fourth dataset with that property,
which has not been attempted in this sprint (no time was spent on this -
it was explicitly out of scope per the Day 7 master prompt's own
instruction not to start a combinatorial experiment suite this sprint).

## Binding constraint on all future sensor-selection claims

Any future document, contract, or handoff that proposes a specific
multi-sensor architecture **must cite this limitation explicitly** and
must not claim the selection is provably optimal from marginal-value
evidence alone. Operational-cost and Pareto work (owned by Emir/Claude,
not this track) must treat this the same way: a Pareto frontier built
from one-at-a-time marginal values is a reasonable engineering heuristic,
not a proof of global optimality.
