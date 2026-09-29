/**
 * Stage 6 Visualization G — bundled, faithfully-copied excerpts of the
 * governing figure-source artifacts (results/final_figure_manifest.json,
 * status STAGE5_FIGURE_MANIFEST_REPORTED_COMPLETE_PENDING_INDEPENDENT_AUDIT).
 * These are frozen, versioned scientific results (not live telemetry), so
 * they are copied at build time rather than fetched — the same pattern the
 * project already uses for lib/architecture.ts's static architecture facts.
 *
 * Every number below is copied VERBATIM from its cited results/ file — no
 * transformation beyond "extract this field" has been applied. Governing
 * status, exact source path, and claim_boundary/uncertainty_meaning text are
 * carried forward unedited so no chart can silently drift from what the
 * source artifact actually licenses it to claim.
 */

export type SensitivityDirection = "lower_is_better" | "higher_is_better";

export interface SeedSeries {
  label: string;
  values: Record<string, number>; // seed id -> value
}

export interface PpgDaliaCapacityControl {
  title: string;
  metric: string;
  unit: "bpm";
  direction: SensitivityDirection;
  sampleUnit: string;
  series: SeedSeries[];
  uncertaintyMeaning: string;
  claimBoundary: string;
  provenance: string[];
  governingStatus: "GOVERNING";
}

export const PPG_DALIA_CAPACITY_CONTROL: PpgDaliaCapacityControl = {
  title: "PPG-DaLiA: capacity-controlled IMU marginal value",
  metric: "MAE (bpm)",
  unit: "bpm",
  direction: "lower_is_better",
  sampleUnit: "training seed (n=5); each point is one independently-initialized model on the same held-out subjects",
  series: [
    { label: "A_cap (capacity-matched PPG-only)", values: { seed42: 7.558364391326904, seed43: 7.838508129119873, seed44: 7.554868698120117, seed45: 7.574195861816406, seed46: 8.538811683654785 } },
    { label: "B (PPG+IMU)", values: { seed42: 7.0128560066223145, seed43: 7.109114646911621, seed44: 7.282139778137207, seed45: 7.1660990715026855, seed46: 7.46796178817749 } },
    { label: "C (PPG+shuffled IMU)", values: { seed42: 7.882018566131592, seed43: 8.215158462524414, seed44: 8.142921447753906, seed45: 7.641919136047363, seed46: 8.03761100769043 } },
  ],
  uncertaintyMeaning: "Error bars = sample SD (ddof=1) across the 5 seeds, NOT a population confidence interval.",
  claimBoundary: "A_cap vs B is the capacity-fair comparison; the original uncontrolled A vs B gap is not the headline.",
  provenance: ["results/ppg_dalia_capacity_control.json", "results/ppg_dalia_imu_multiseed_replication.json"],
  governingStatus: "GOVERNING",
};

export interface PpgDaliaSubjectHeterogeneity {
  title: string;
  metric: string;
  direction: SensitivityDirection;
  sampleUnit: string;
  perSubjectDelta: Record<string, number>; // positive = candidate (B) better
  uncertaintyMeaning: string;
  claimBoundary: string;
  provenance: string[];
  governingStatus: "GOVERNING";
}

export const PPG_DALIA_SUBJECT_HETEROGENEITY: PpgDaliaSubjectHeterogeneity = {
  title: "PPG-DaLiA: per-subject A_cap -> B delta",
  metric: "delta MAE (bpm), positive = candidate (B) better",
  direction: "higher_is_better",
  sampleUnit: "held-out subject (n=3)",
  perSubjectDelta: { S14: 0.7420694351196289, S2: -0.07595510482788086, S9: 1.1151174545288085 },
  uncertaintyMeaning: "No error bars at n=3 subjects — individual subject points only, not a bar+CI.",
  claimBoundary: "n=3 subjects only for the capacity-matched comparison.",
  provenance: ["results/ppg_dalia_sensitivity_day11.json"],
  governingStatus: "GOVERNING",
};

export interface PttSubjectHeterogeneity {
  title: string;
  metric: string;
  direction: SensitivityDirection;
  sampleUnit: string;
  perSubjectDelta: Record<string, number>; // positive = candidate (B, two-site) WORSE
  aggregateWithS2: { modelAMae: number; modelBMae: number; deltaBMinusA: number; direction: "B_WORSE" | "B_BETTER" };
  aggregateWithoutS2: { modelAMae: number; modelBMae: number; deltaBMinusA: number; direction: "B_WORSE" | "B_BETTER" };
  signFlipsWhenS2Excluded: true;
  uncertaintyMeaning: string;
  claimBoundary: string;
  provenance: string[];
  governingStatus: "GOVERNING";
}

export const PTT_SUBJECT_HETEROGENEITY: PttSubjectHeterogeneity = {
  title: "PTT: per-subject B-A delta and s2 sensitivity",
  metric: "delta MAE (bpm), positive = candidate (B, two-site) worse",
  direction: "lower_is_better",
  sampleUnit: "held-out subject (n=4)",
  perSubjectDelta: { s14: 1.2935703277587898, s2: 7.265168762207029, s20: -1.4176908493041998, s9: -1.3268955230712898 },
  aggregateWithS2: { modelAMae: 17.540314802629062, modelBMae: 19.002724690622927, deltaBMinusA: 1.4624098879938643, direction: "B_WORSE" },
  aggregateWithoutS2: { modelAMae: 12.811820910452917, modelBMae: 12.328411470341265, deltaBMinusA: -0.483409440111652, direction: "B_BETTER" },
  signFlipsWhenS2Excluded: true,
  uncertaintyMeaning: "No defensible population CI at n=4 — show all 4 subject points individually, never a mean+CI bar.",
  claimBoundary: "Excluding s2 flips the aggregate sign; s2 is retained in the frozen primary result (this is a descriptive sensitivity finding, not a re-run excluding s2).",
  provenance: ["results/ptt_sensitivity_day11.json"],
  governingStatus: "GOVERNING",
};

export interface SleepEdfPrimaryAbc {
  title: string;
  metric: string;
  unit: "macro_f1";
  direction: SensitivityDirection;
  sampleUnit: string;
  series: SeedSeries[]; // macro_f1 per seed, per arm
  uncertaintyMeaning: string;
  claimBoundary: string;
  provenance: string[];
  governingStatus: "GOVERNING";
}

export const SLEEP_EDF_PRIMARY_ABC: SleepEdfPrimaryAbc = {
  title: "Sleep-EDF primary: A/B/C macro-F1",
  metric: "macro-F1",
  unit: "macro_f1",
  direction: "higher_is_better",
  sampleUnit: "training seed (n=5), held-out test subjects n=3",
  series: [
    { label: "A (EEG only)", values: { seed42: 0.7086057747793477, seed43: 0.7748928568718149, seed44: 0.7541404087394364, seed45: 0.7436336267999948, seed46: 0.7549900001130317 } },
    { label: "B (EEG+aligned EOG)", values: { seed42: 0.7608289499707233, seed43: 0.7717015866525443, seed44: 0.7913724827694598, seed45: 0.7623310681847801, seed46: 0.7600656094411762 } },
    { label: "C (EEG+shuffled EOG)", values: { seed42: 0.7454106020492566, seed43: 0.7594724073814922, seed44: 0.7342621761970922, seed45: 0.7233308126046032, seed46: 0.7476306179053609 } },
  ],
  uncertaintyMeaning: "Error bars = sample SD (ddof=1) across seeds, NOT a population confidence interval.",
  claimBoundary: "n=3 test subjects; primary effect is concentrated in a single subject (SC4011) — must be read alongside subject-level heterogeneity, not as a uniform population effect.",
  provenance: ["results/sleep_edf_eeg_eog_ablation.json", "results/sleep_edf_eeg_eog_control_analysis.json"],
  governingStatus: "GOVERNING",
};

/** Mean +/- sample SD helper for the small-multiple aggregate diamond. Never a population CI. */
export function seriesMeanSd(values: Record<string, number>): { mean: number; sd: number; n: number } {
  const nums = Object.values(values);
  const n = nums.length;
  const mean = nums.reduce((a, b) => a + b, 0) / n;
  const variance = n > 1 ? nums.reduce((a, b) => a + (b - mean) ** 2, 0) / (n - 1) : 0;
  return { mean, sd: Math.sqrt(variance), n };
}
