# Stage 4 Architecture / Pareto Status

**Status: `NOT_READY`, unchanged.**

This sprint did not run any additional architecture/Pareto analysis and is
not authorized to (Section 71, Section 93). The reasons `NOT_READY` remains
correct, independently re-confirmed given this sprint's own new evidence:

1. Metrics across this sprint's experiments are non-comparable by
   construction (MAE in bpm, MAE in kg, macro-F1, MAE in mmHg) — no unified
   score exists or was computed (Section 67).
2. Two of four Stage 2–3 experiments (GalaxyPPG, LBNP) produced no result at
   all this sprint (blocked by access) — a Pareto analysis needs completed
   evidence for its candidate sensors, not placeholders.
3. QDE V2's completed result is negative-leaning for its specific
   candidate (leg BioZ) — this is evidence AGAINST including that sensor at
   its measured burden cost, not evidence for a Pareto frontier position.
4. ds003838's central minimalism question is unresolved (bounded diagnostic
   only) — the one experiment in this sprint most directly relevant to
   "how minimal can a sensor be" produced no usable evidence yet.
5. Engineering-burden quantification for LBNP's thoracic EIS module and any
   architecture combining it with existing modules has not been attempted
   here — architecture decisions require Claude's engineering-burden line,
   which this branch does not contain (Section 6).

`results/architecture_evidence_handoff_stage4.json`'s
`final_architecture_status` field is set to `"UNRESOLVED"` accordingly.
