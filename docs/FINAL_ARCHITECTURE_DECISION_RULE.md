# Final Architecture Decision Rule — Frozen Day 6 Rule

## What this rule is (terminology)

This artifact is currently an **architecture decision gate**, not yet a final
selection rule. It decides *whether* the evidence on a component/target pair is
complete and comparable enough to authorize a formal target-specific trade-off —
and, when it is not, it returns **Future evidence required**. It deliberately does
**not** manufacture a tie-break operator or embed benefit thresholds to force a
decision.

- **Architecture decision gate** (this document, today): admissibility check on
  evidence completeness/comparability; can return Retain / Conditional /
  Deprioritize / Remove-from-named-target / Future-evidence-required.
- **Architecture decision policy** (future): a frozen downstream trade-off method
  over admissible candidates.
- **Final selection rule** (future): applies only once such a policy is frozen.

The filename is retained for backward compatibility with artifacts that reference
it. Behaving like a gate that often returns *Future evidence required* is the
intended, honest behavior — not a defect to be papered over with arbitrary
thresholds.

## Interaction-effect precondition

One-component-at-a-time marginal-value evidence does **not** prove a globally
minimal subset. Greedy accumulation of independent single-component results must
never be reported as a proof of global optimality. Formal target-specific Pareto
readiness therefore **cannot** become TRUE from independent one-sensor experiments
alone when interaction evidence is a decision-critical dimension; a dedicated
interaction design (e.g. baseline / +A / +B / +A+B within one dataset/target/
protocol) is future work, and `interaction_evidence` remains `unavailable`
(see `docs/SENSOR_MARGINAL_VALUE_METHODOLOGY.md` §14).

## Independence

This rule is frozen before any final component outcome is calculated. It does not encode a preferred winner and is unchanged by whether a scientific experiment is positive or negative.

## Unit of decision

Evaluate one component for one stated physiological target and deployment schedule. Never collapse targets, datasets, populations, or model families into a universal sensor score. Do not rank raw MAE/RMSE across datasets.

## Required evidence dimensions

1. Target-specific scientific marginal benefit, direction, uncertainty/heterogeneity, and claim boundary.
2. Incremental operational burden in original units: component and average power/energy, mass boundary, contact/sensing sites, module allocation, data, memory, and embedded latency.
3. Robustness and availability under a relevant, predeclared corruption protocol.
4. Traceable provenance and an explicit reference operating condition.
5. Shared-resource allocation that prohibits double counting.

Formal target-specific Pareto assessment requires comparable candidates with sufficiently complete evidence on every decision-critical dimension. Missing values remain missing; they are not imputed as zero or replaced by subjective weights.

## Possible outcomes

- **Retain:** sufficient target-specific value and no disqualifying operational/robustness burden.
- **Conditional or intermittent use:** value depends on context, event, session, or duty schedule.
- **Deprioritize:** evidence does not justify current integration priority, without claiming permanent irrelevance.
- **Remove from a named target architecture:** only when the target-specific evidence and burden are sufficiently complete and the rule's preconditions are met.
- **Future evidence required:** incomplete or non-comparable evidence prevents a decision.

## Prohibitions

No weighted universal scalar score, fabricated comfort number, inferred total wearable power, inferred finished mass, cross-dataset raw-error ranking, or predetermined architecture action is permitted. A structural observation may be reported descriptively but cannot be mislabeled a formal Pareto frontier.

## Day 6 application status

No final retain/remove outcome is applied. The readiness artifact determines that global and target-specific formal Pareto analysis are not authorized. The single limited structural observation about the second PPG site remains scoped to its frozen heart-rate experiment.
