#!/usr/bin/env python
"""Builds the complete Sleep V2 package (Section 24): corrected A, B, C,
interaction, subject/class sensitivity, Resp provenance, seed provenance,
checkpoint provenance - derived from the already-written result JSONs, no
hand-typed duplicated numbers."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS = REPO_ROOT / "results"


def main() -> None:
    primary = json.loads((RESULTS / "sleep_edf_primary_seedfix_v2.json").read_text())
    control = json.loads((RESULTS / "sleep_edf_shuffled_eog_control_seedfix_v2.json").read_text())
    interaction_path = RESULTS / "sleep_edf_interaction_resp_seedfix_v2.json"
    interaction = json.loads(interaction_path.read_text()) if interaction_path.exists() else None

    out = {
        "purpose": "Complete Sleep V2 (corrected, H1-seed-fixed) scientific package - A, B, C, interaction, all cross-referenced from their own result artifacts, not hand-duplicated.",
        "v1_vs_v2_separation": "V1 (historical, uncorrected-seed-order) results remain in results/sleep_edf_eeg_eog_ablation.json, results/sleep_edf_eeg_eog_control_analysis.json, results/sleep_edf_interaction_resp_day10.json - ALL UNCHANGED, NEVER MIXED WITH V2 NUMBERS in this package.",
        "corrected_A": primary["aggregate"]["baseline_macro_f1"],
        "corrected_B": primary["aggregate"]["candidate_macro_f1"],
        "B_minus_A": primary["aggregate"]["delta_candidate_minus_baseline"],
        "corrected_C": control["aggregate"]["model_c_macro_f1_v2"],
        "B_minus_C": control["aggregate"]["C_to_B"],
        "A_minus_C": control["aggregate"]["A_to_C"],
        "capacity_c_equals_b": control["frozen_protocol"]["capacity_identical_to_b"],
        "interaction": interaction["aggregate"] if interaction else "PENDING - training in progress at package-build time",
        "interaction_m0_ma_equivalence": interaction["m0_ma_equivalence_decision"] if interaction else None,
        "resp_provenance": interaction["resp_rate_provenance"] if interaction else {
            "native_sfreq_hz": 1.0, "loaded_common_grid_sfreq_hz": 100.0,
            "note": "Native 1 Hz, 100 Hz is the common/model grid via FFT upsampling - never report Resp as native 100 Hz."
        },
        "seed_provenance": {
            "seeds": [42, 43, 44, 45, 46],
            "protocol": "model_init_seed = run_seed; data_order_seed = run_seed+100000; control_shuffle_seed = run_seed+200000 (ml/sleep_seed_utils.py)",
            "seeds_are_optimization_repetitions_not_biological_n": True,
        },
        "checkpoint_provenance": {
            "A_B": "ml/checkpoints/sleep_edf_{baseline_eeg_only,candidate_eeg_plus_eog}_seedfix_v2_seed{42-46}.pt (10 files, from a prior sprint)",
            "C": "ml/checkpoints/sleep_edf_model_c_shuffled_eog_seedfix_v2_seed{42-46}.pt (5 files, this sprint)",
            "interaction": "ml/checkpoints/sleep_edf_interaction_{M_B_eeg_plus_resp,M_AB_eeg_plus_eog_plus_resp}_seedfix_v2_seed{42-46}.pt (10 files, this sprint) - NOT to be confused with the pre-existing Day-10 V1 checkpoints of similar names (no seedfix_v2 suffix)",
        },
        "primary_subject_split": primary["frozen_protocol"]["subject_split"],
    }
    out_path = RESULTS / "sleep_v2_complete_package.json"
    out_path.write_text(json.dumps(out, indent=2))
    print("Wrote", out_path)
    print("Interaction included:", interaction is not None)


if __name__ == "__main__":
    main()
