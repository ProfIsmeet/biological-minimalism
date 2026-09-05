# Final Architecture Decision Rule — Frozen Day 6 Rule

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
