/**
 * Stage 6 — shared, JSX-free visualization primitives (missing/non-finite
 * guards, evidence-class labels, tabular-numeral formatting). Kept pure so
 * scripts/verify-monitoring-state.ts can exercise every rule directly,
 * matching the existing convention in lib/monitoring/*.ts.
 *
 * These helpers exist to make one rule mechanically impossible to violate by
 * accident: a missing/non-finite value must never silently become 0, and a
 * finite 0 must never be treated as "missing". Every Stage 6 chart routes its
 * raw numbers through `classifyValue`/`formatMetric` rather than rendering
 * `value ?? 0` or `value || 0` directly.
 */

export type ValueClass = "finite" | "missing" | "non_finite";

/**
 * Classifies a raw numeric candidate without ever coercing missing/NaN/
 * Infinity into 0. `undefined`/`null` -> "missing" (genuinely absent).
 * `NaN`/`Infinity`/`-Infinity` -> "non_finite" (present but unusable).
 * Anything else, including a real 0, -> "finite".
 */
export function classifyValue(value: number | null | undefined): ValueClass {
  if (value === null || value === undefined) return "missing";
  if (!Number.isFinite(value)) return "non_finite";
  return "finite";
}

export interface FormattedMetric {
  class: ValueClass;
  /** Human-readable text for the value cell — never "0" for a missing/non-finite input. */
  text: string;
  /** The finite numeric value, only when class === "finite" — safe to plot. */
  plottable: number | null;
}

export interface FormatMetricOptions {
  unit?: string;
  digits?: number;
  missingText?: string;
  nonFiniteText?: string;
}

/** Format a raw metric for both display and plotting, honoring missing != 0. */
export function formatMetric(value: number | null | undefined, options: FormatMetricOptions = {}): FormattedMetric {
  const { unit = "", digits = 1, missingText = "Not measured", nonFiniteText = "Non-finite value" } = options;
  const cls = classifyValue(value);
  if (cls === "missing") return { class: cls, text: missingText, plottable: null };
  if (cls === "non_finite") return { class: cls, text: nonFiniteText, plottable: null };
  const num = value as number;
  const text = `${num.toFixed(digits)}${unit ? ` ${unit}` : ""}`;
  return { class: cls, text, plottable: num };
}

/** Tabular-numeral-safe fixed formatting for aligned quantitative columns. */
export function tabularNumber(value: number, digits = 1): string {
  return value.toFixed(digits);
}

export type Directionality = "lower_is_better" | "higher_is_better" | "not_directional";

export function directionalityLabel(direction: Directionality): string {
  switch (direction) {
    case "lower_is_better":
      return "Lower is better";
    case "higher_is_better":
      return "Higher is better";
    case "not_directional":
      return "No preferred direction";
  }
}

/**
 * The seven-term evidence-class vocabulary used across every Stage 6 research
 * visualization (family E/F/G) — mirrors the project's own TIER_A..TIER_P
 * scientific vocabulary (results/stage4_architecture_candidate_classes.json)
 * rather than inventing a new one.
 */
export type EvidenceClass =
  | "TIER_A_REPLICATED_SUPPORT"
  | "TIER_B_CONTROLLED_SUPPORT"
  | "TIER_C_BOUNDED_SUPPORT"
  | "TIER_D_MIXED_OR_FRAGILE"
  | "TIER_E_NEGATIVE_OR_DEPRIORITIZED"
  | "TIER_P_PENDING"
  | "ENGINEERING_ESTIMATE";

export const EVIDENCE_CLASS_LABEL: Record<EvidenceClass, string> = {
  TIER_A_REPLICATED_SUPPORT: "Tier A · replicated support",
  TIER_B_CONTROLLED_SUPPORT: "Tier B · controlled support (same-dataset)",
  TIER_C_BOUNDED_SUPPORT: "Tier C · bounded support (small-N / limited external)",
  TIER_D_MIXED_OR_FRAGILE: "Tier D · mixed / fragile evidence",
  TIER_E_NEGATIVE_OR_DEPRIORITIZED: "Tier E · negative / deprioritized",
  TIER_P_PENDING: "Pending — no governing result yet",
  ENGINEERING_ESTIMATE: "Engineering estimate — not measured hardware",
};

export type GoverningStatus = "GOVERNING" | "SUPERSEDED" | "HISTORICAL_NON_GOVERNING";

export const GOVERNING_STATUS_LABEL: Record<GoverningStatus, string> = {
  GOVERNING: "Governing",
  SUPERSEDED: "Superseded",
  HISTORICAL_NON_GOVERNING: "Historical — not governing",
};

/** Sample SD across seeds/subjects is descriptive variability, never a population CI. Label it honestly. */
export function uncertaintyLabel(kind: "seed_sd" | "subject_bootstrap" | "none"): string {
  switch (kind) {
    case "seed_sd":
      return "Sample SD across training seeds — not a population confidence interval";
    case "subject_bootstrap":
      return "Descriptive subject-level bootstrap — not a population confidence interval";
    case "none":
      return "No defensible interval at this sample size — individual points only";
  }
}
