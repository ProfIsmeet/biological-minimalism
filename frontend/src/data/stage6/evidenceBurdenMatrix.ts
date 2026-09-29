/**
 * Stage 6 Visualization F — bundled, verbatim excerpt of
 * results/final_tables/table_d_negative_mixed_results.json (provenance:
 * results/final_claim_ledger.json). Keyed by the same candidate identifiers
 * used in results/final_wearable_architecture.json's exclusion_rationale so
 * CandidateDispositionMatrix.tsx (which already fetches that artifact live)
 * can join quantitative evidence onto its existing disposition rows without
 * a second network fetch or a duplicate component.
 */
export interface NegativeMixedEvidence {
  numericSupport: string;
  populationScope: string;
  limitation: string;
}

export const NEGATIVE_MIXED_EVIDENCE: Record<string, NegativeMixedEvidence> = {
  second_site_ppg: {
    numericSupport: "B_minus_A = +1.462 MAE (worse); n=4 held-out test subjects",
    populationScope: "n=4 held-out test subjects",
    limitation: "n=4 test subjects; sign-sensitive to exclusion (excluding subject s2 flips the aggregate sign)",
  },
  leg_bioz: {
    numericSupport: "A_minus_B = -0.052 (aggregate disfavors B); 7/10 subjects individually favor B",
    populationScope: "QDE V2, n=10 subjects",
    limitation: "n=10; single-outlier-dominated ambiguity",
  },
  thoracic_bioz_eis: {
    numericSupport: "A_minus_B = -0.452 (sign-reverses without subject 9); C_minus_B = -1.293 (shrinks substantially without subject 9); classification COMPLETE_MIXED",
    populationScope: "LBNP corrected protocol-compliant cohort: n=12/16 eligible subjects",
    limitation: "n=12; only thoracic site and LBNP-stage target tested; both comparisons subject-9-sensitive",
  },
  wrist_temperature_light: {
    numericSupport: "Not measured — no governing experiment currently exists",
    populationScope: "Not applicable",
    limitation: "TIER_P_PENDING — complete absence of governing evidence, not a negative result",
  },
};
