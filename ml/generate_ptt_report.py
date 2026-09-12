#!/usr/bin/env python
"""Generates the human-readable REPORT.md, paper-ready CSV tables, and
result figures from results/ptt_ppg_site_ablation.json. Run only after
ml/train_ptt_ppg_site_ablation.py's main() has produced that file.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

RESULTS_PATH = REPO_ROOT / "results" / "ptt_ppg_site_ablation.json"
EXPERIMENT_DIR = REPO_ROOT / "ml" / "experiments" / "ptt_ppg_site_ablation"
FIGURES_DIR = EXPERIMENT_DIR / "figures"


def seed_aggregated_per_subject(results: dict, model_key: str) -> dict:
    """Average per-subject MAE/RMSE across the 5 training seeds."""
    seeds = list(results["runs"][model_key].keys())
    subjects = list(results["runs"][model_key][seeds[0]]["per_subject"].keys())
    out = {}
    for s in subjects:
        maes = [results["runs"][model_key][sk]["per_subject"][s]["mae"] for sk in seeds]
        rmses = [results["runs"][model_key][sk]["per_subject"][s]["rmse"] for sk in seeds]
        n = results["runs"][model_key][seeds[0]]["per_subject"][s]["n_windows"]
        out[s] = {"mean_mae": sum(maes) / len(maes), "mean_rmse": sum(rmses) / len(rmses), "n_windows": n}
    return out


def seed_aggregated_per_activity(results: dict, model_key: str) -> dict:
    seeds = list(results["runs"][model_key].keys())
    activities = list(results["runs"][model_key][seeds[0]]["per_activity"].keys())
    out = {}
    for a in activities:
        maes = [results["runs"][model_key][sk]["per_activity"][a]["mae"] for sk in seeds]
        rmses = [results["runs"][model_key][sk]["per_activity"][a]["rmse"] for sk in seeds]
        n = results["runs"][model_key][seeds[0]]["per_activity"][a]["n_windows"]
        out[a] = {"mean_mae": sum(maes) / len(maes), "mean_rmse": sum(rmses) / len(rmses), "n_windows": n}
    return out


def write_tables(results: dict) -> tuple[dict, dict]:
    EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)

    agg = results["aggregate"]

    # Table A - overall
    with open(EXPERIMENT_DIR / "table_a_overall.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "mean_mae_bpm", "sd_mae_bpm", "mean_rmse_bpm", "sd_rmse_bpm"])
        w.writerow(["A (single-site)", agg["model_a"]["mean_mae"], agg["model_a"]["sd_mae"], agg["model_a"]["mean_rmse"], agg["model_a"]["sd_rmse"]])
        w.writerow(["B (two-site)", agg["model_b"]["mean_mae"], agg["model_b"]["sd_mae"], agg["model_b"]["mean_rmse"], agg["model_b"]["sd_rmse"]])
        w.writerow(["Paired delta (B-A)", agg["paired_delta_mae_b_minus_a"]["mean"], agg["paired_delta_mae_b_minus_a"]["sd"], agg["paired_delta_rmse_b_minus_a"]["mean"], agg["paired_delta_rmse_b_minus_a"]["sd"]])

    # Table B - per-subject (seed-aggregated)
    per_subject_a = seed_aggregated_per_subject(results, "a")
    per_subject_b = seed_aggregated_per_subject(results, "b")
    with open(EXPERIMENT_DIR / "table_b_per_subject.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["subject", "a_mae", "b_mae", "delta_mae", "a_rmse", "b_rmse", "delta_rmse", "n_windows"])
        for s in sorted(per_subject_a):
            a, b = per_subject_a[s], per_subject_b[s]
            w.writerow([s, a["mean_mae"], b["mean_mae"], b["mean_mae"] - a["mean_mae"], a["mean_rmse"], b["mean_rmse"], b["mean_rmse"] - a["mean_rmse"], a["n_windows"]])

    # Table C - per-activity (seed-aggregated)
    per_activity_a = seed_aggregated_per_activity(results, "a")
    per_activity_b = seed_aggregated_per_activity(results, "b")
    with open(EXPERIMENT_DIR / "table_c_per_activity.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["activity", "a_mae", "b_mae", "delta_mae", "a_rmse", "b_rmse", "delta_rmse", "n_windows"])
        for act in ("sit", "walk", "run"):
            if act not in per_activity_a:
                continue
            a, b = per_activity_a[act], per_activity_b[act]
            w.writerow([act, a["mean_mae"], b["mean_mae"], b["mean_mae"] - a["mean_mae"], a["mean_rmse"], b["mean_rmse"], b["mean_rmse"] - a["mean_rmse"], a["n_windows"]])

    # Table D - per-seed variability
    with open(EXPERIMENT_DIR / "table_d_seed_variability.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seed", "a_mae", "b_mae", "delta_mae", "a_rmse", "b_rmse", "delta_rmse"])
        for seed_key in results["runs"]["a"]:
            a = results["runs"]["a"][seed_key]["overall"]
            b = results["runs"]["b"][seed_key]["overall"]
            w.writerow([seed_key, a["mae"], b["mae"], b["mae"] - a["mae"], a["rmse"], b["rmse"], b["rmse"] - a["rmse"]])

    return per_subject_a, per_subject_b, per_activity_a, per_activity_b  # type: ignore[return-value]


def write_figures(results: dict, per_subject_a: dict, per_subject_b: dict, per_activity_a: dict, per_activity_b: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    agg = results["aggregate"]

    # Figure 1: Model A vs B overall MAE (with SD error bars)
    fig, ax = plt.subplots(figsize=(5, 4))
    models = ["Model A\n(single-site)", "Model B\n(two-site)"]
    means = [agg["model_a"]["mean_mae"], agg["model_b"]["mean_mae"]]
    sds = [agg["model_a"]["sd_mae"], agg["model_b"]["sd_mae"]]
    ax.bar(models, means, yerr=sds, capsize=5, color=["#4C72B0", "#DD8452"])
    ax.set_ylabel("Held-out MAE (bpm)")
    ax.set_title("PTT PPG site ablation: overall held-out MAE (mean +/- SD over 5 seeds)")
    for i, (m, s) in enumerate(zip(means, sds)):
        ax.annotate(f"{m:.3f}", (i, m + s + 0.05), ha="center")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure1_overall_mae.png", dpi=150)
    plt.close(fig)

    # Figure 2: per-subject delta MAE
    subjects = sorted(per_subject_a.keys())
    deltas = [per_subject_b[s]["mean_mae"] - per_subject_a[s]["mean_mae"] for s in subjects]
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = ["#55A868" if d < 0 else "#C44E52" for d in deltas]
    ax.bar(subjects, deltas, color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Delta MAE, bpm (B - A); negative = two-site better")
    ax.set_title("Per-subject marginal effect of the second PPG site")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure2_per_subject_delta.png", dpi=150)
    plt.close(fig)

    # Figure 3: per-activity delta MAE
    activities = [a for a in ("sit", "walk", "run") if a in per_activity_a]
    deltas_act = [per_activity_b[a]["mean_mae"] - per_activity_a[a]["mean_mae"] for a in activities]
    fig, ax = plt.subplots(figsize=(5, 4))
    colors = ["#55A868" if d < 0 else "#C44E52" for d in deltas_act]
    ax.bar(activities, deltas_act, color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Delta MAE, bpm (B - A); negative = two-site better")
    ax.set_title("Per-activity marginal effect of the second PPG site")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure3_per_activity_delta.png", dpi=150)
    plt.close(fig)

    # Figure 4: learning curves (seed 42 for both models, as a representative example)
    fig, ax = plt.subplots(figsize=(6, 4))
    for model_key, label, color in (("a", "Model A", "#4C72B0"), ("b", "Model B", "#DD8452")):
        history = results["runs"][model_key]["seed42"]["train_history"]
        epochs = [h["epoch"] for h in history]
        val_mae = [h["val_mae"] for h in history]
        ax.plot(epochs, val_mae, marker="o", label=f"{label} (seed 42)", color=color)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Validation MAE (bpm)")
    ax.set_title("Learning curves (seed 42, representative)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "figure4_learning_curves_seed42.png", dpi=150)
    plt.close(fig)

    print("Wrote figures to", FIGURES_DIR)


def write_report(results: dict, per_subject_a: dict, per_subject_b: dict, per_activity_a: dict, per_activity_b: dict) -> None:
    agg = results["aggregate"]
    subjects = sorted(per_subject_a.keys())
    n_improved = sum(1 for s in subjects if per_subject_b[s]["mean_mae"] < per_subject_a[s]["mean_mae"])
    n_worsened = sum(1 for s in subjects if per_subject_b[s]["mean_mae"] > per_subject_a[s]["mean_mae"])
    strongest_improve = min(subjects, key=lambda s: per_subject_b[s]["mean_mae"] - per_subject_a[s]["mean_mae"])
    strongest_regress = max(subjects, key=lambda s: per_subject_b[s]["mean_mae"] - per_subject_a[s]["mean_mae"])

    activities = [a for a in ("sit", "walk", "run") if a in per_activity_a]
    act_deltas = {a: per_activity_b[a]["mean_mae"] - per_activity_a[a]["mean_mae"] for a in activities}
    monotonic = activities == ["sit", "walk", "run"] and act_deltas["run"] < act_deltas["walk"] < act_deltas["sit"]

    lines = []
    lines.append("# PTT PPG Site-Value HR Ablation — Full Result Report\n")
    lines.append("## 1. Question\n")
    lines.append("Does a second physical PPG sensor site (proximal phalanx, in addition to the "
                  "distal phalanx) provide measurable value for heart-rate estimation from PPG "
                  "alone, evaluated across sitting, walking, and running?\n")

    lines.append("## 2. Frozen design\n")
    lines.append(f"- Window: {results['config']['window_seconds']}s, stride {results['config']['step_seconds']}s\n"
                  f"- Ground truth: ECG R-peak-derived mean HR (>= {results['config']['min_rpeaks_in_window']} peaks/window required)\n"
                  f"- Preprocessing: per-channel per-window z-score, identical for both models\n"
                  f"- Model A channels: {results['config']['model_a_channels']}\n"
                  f"- Model B channels: {results['config']['model_b_channels']}\n")

    lines.append("## 3. Dataset\n")
    lines.append("PhysioNet Pulse Transit Time PPG Dataset v1.1.0, 22 subjects, 66 records "
                  "(sit/walk/run), verified against real downloaded WFDB files "
                  "(see datasets/PTT_DATASET_AUDIT_DAY3.md and the full-dataset audit).\n")

    lines.append("## 4. Split\n")
    split = results["subject_split"]
    lines.append(f"- Train ({len(split['train'])}): {split['train']}\n"
                  f"- Val ({len(split['val'])}): {split['val']}\n"
                  f"- Test ({len(split['test'])}, held-out): {split['test']}\n"
                  f"- Window counts: train={results['window_counts']['train']}, val={results['window_counts']['val']}, test={results['window_counts']['test']}\n")

    lines.append("## 5. Model definitions\n")
    lines.append("`PPGSiteHRModel`: one `Conv1DEncoder(in_channels)` + `Linear(embedding_dim, 1)` "
                  f"head. Model A: in_channels=3. Model B: in_channels=6. embedding_dim={results['training_hyperparameters']['embedding_dim']} for both.\n")

    lines.append("## 6. Training protocol\n")
    hp = results["training_hyperparameters"]
    for k, v in hp.items():
        lines.append(f"- {k}: {v}\n")

    lines.append("\n## 7. Primary results (overall held-out, mean +/- SD over 5 seeds)\n")
    lines.append(f"- Model A: MAE {agg['model_a']['mean_mae']:.3f} +/- {agg['model_a']['sd_mae']:.3f} bpm, "
                  f"RMSE {agg['model_a']['mean_rmse']:.3f} +/- {agg['model_a']['sd_rmse']:.3f} bpm\n")
    lines.append(f"- Model B: MAE {agg['model_b']['mean_mae']:.3f} +/- {agg['model_b']['sd_mae']:.3f} bpm, "
                  f"RMSE {agg['model_b']['mean_rmse']:.3f} +/- {agg['model_b']['sd_rmse']:.3f} bpm\n")
    lines.append(f"- Paired delta MAE (B-A): {agg['paired_delta_mae_b_minus_a']['mean']:.3f} +/- {agg['paired_delta_mae_b_minus_a']['sd']:.3f} bpm "
                  "(negative = two-site model better)\n")
    lines.append(f"- Paired delta RMSE (B-A): {agg['paired_delta_rmse_b_minus_a']['mean']:.3f} +/- {agg['paired_delta_rmse_b_minus_a']['sd']:.3f} bpm\n")

    lines.append("\n## 8. Per-subject results (seed-aggregated)\n")
    lines.append("| Subject | A MAE | B MAE | Delta MAE | A RMSE | B RMSE | Delta RMSE |\n|---|---|---|---|---|---|---|\n")
    for s in subjects:
        a, b = per_subject_a[s], per_subject_b[s]
        lines.append(f"| {s} | {a['mean_mae']:.3f} | {b['mean_mae']:.3f} | {b['mean_mae']-a['mean_mae']:+.3f} | {a['mean_rmse']:.3f} | {b['mean_rmse']:.3f} | {b['mean_rmse']-a['mean_rmse']:+.3f} |\n")
    lines.append(f"\n{n_improved}/{len(subjects)} held-out subjects improved (lower MAE) with Model B; {n_worsened}/{len(subjects)} worsened.\n")
    lines.append(f"Strongest improvement: {strongest_improve}. Strongest regression: {strongest_regress}.\n")

    lines.append("\n## 9. Per-activity results (seed-aggregated)\n")
    lines.append("| Activity | A MAE | B MAE | Delta MAE | A RMSE | B RMSE | Delta RMSE |\n|---|---|---|---|---|---|---|\n")
    for a in activities:
        pa, pb = per_activity_a[a], per_activity_b[a]
        lines.append(f"| {a} | {pa['mean_mae']:.3f} | {pb['mean_mae']:.3f} | {pb['mean_mae']-pa['mean_mae']:+.3f} | {pa['mean_rmse']:.3f} | {pb['mean_rmse']:.3f} | {pb['mean_rmse']-pa['mean_rmse']:+.3f} |\n")
    lines.append(f"\nBenefit monotonic with motion (sit < walk < run improvement magnitude): {monotonic}. "
                  "This was NOT assumed in advance and is reported as observed.\n")

    lines.append("\n## 10. Paired per-seed results\n")
    lines.append("| Seed | A MAE | B MAE | Delta MAE | A RMSE | B RMSE | Delta RMSE |\n|---|---|---|---|---|---|---|\n")
    for seed_key in results["runs"]["a"]:
        a = results["runs"]["a"][seed_key]["overall"]
        b = results["runs"]["b"][seed_key]["overall"]
        lines.append(f"| {seed_key} | {a['mae']:.3f} | {b['mae']:.3f} | {b['mae']-a['mae']:+.3f} | {a['rmse']:.3f} | {b['rmse']:.3f} | {b['rmse']-a['rmse']:+.3f} |\n")

    lines.append("\n## 11. Negative/unexpected results\n")
    lines.append(f"See §8-9 above for exact subject/activity-level negatives; {n_worsened} of {len(subjects)} "
                  "subjects worsened under Model B and any activity with a positive delta above is a case "
                  "where the second site did not help under this frozen design. Reported as-is.\n")

    lines.append("\n## 12. Limitations\n")
    lines.append("- Model B has strictly more input channels than Model A by construction - the "
                  "site-value and channel-count effects are not perfectly separable from PPG "
                  "channel count alone (disclosed in docs/MODEL_CONTRACT_PTT_HR.md).\n"
                  "- Only 4 held-out test subjects; per-subject estimates carry real sampling "
                  "uncertainty from a small population.\n"
                  "- 22 terrestrial healthy subjects; no astronaut/microgravity data.\n"
                  "- Windows within a subject/activity are not independent samples - see §16 of the "
                  "master prompt; no window-level significance testing was performed for this reason.\n"
                  "- s13's ECG-noise caveat (flagged by the original dataset authors) applies to the "
                  "train split in this frozen assignment; retained per the pre-registered split.\n"
                  "- Held-out subject s2 has a real, verified-from-raw-data HR distribution far outside "
                  "the training population's range (sit ~121 bpm, run ~140 bpm mean, vs. a train-set mean "
                  "of ~85 bpm) - a genuine out-of-distribution held-out subject, not a data or leakage "
                  "issue, but it dominates the small (N=4) held-out aggregate MAE for both models.\n")

    lines.append("\n## 13. Permitted claims\n")
    lines.append("- A quantified, subject/activity-level marginal comparison of one vs. two PPG "
                  "sites for ECG-referenced HR estimation on this dataset/split.\n"
                  "- Whether the observed effect (if any) is consistent, seed-stable, and its "
                  "direction and magnitude, exactly as measured.\n")

    lines.append("\n## 14. Prohibited claims\n")
    lines.append("- No claim of universal superiority of multi-site PPG, no astronaut/microgravity "
                  "generalization, no cuffless BP/PTT-as-BP claim, no claim that six channels are "
                  "globally optimal, no treating seed SD as predictive uncertainty.\n")

    lines.append("\n## 15. Relationship to Biological Minimalism\n")
    if agg["paired_delta_mae_b_minus_a"]["mean"] < 0:
        lines.append("Under this frozen experiment, the second physical PPG site showed a measurable "
                      f"mean marginal MAE improvement ({agg['paired_delta_mae_b_minus_a']['mean']:.3f} bpm). "
                      "Whether this improvement justifies the additional physical sensing region's "
                      "hardware/contact/power/complexity cost is a separate, later Pareto question - "
                      "not answered here.\n")
    else:
        lines.append("Under this frozen experiment, the second physical PPG site did not show a clear "
                      "mean marginal MAE improvement for ECG-referenced HR estimation "
                      f"(paired delta {agg['paired_delta_mae_b_minus_a']['mean']:+.3f} bpm). This is a "
                      "legitimate, useful negative sensor-value result consistent with the Biological "
                      "Minimalism hypothesis for this specific target - it does not generalize beyond "
                      "HR or beyond this dataset.\n")

    (EXPERIMENT_DIR / "REPORT.md").write_text("".join(lines), encoding="utf-8")
    print("Wrote", EXPERIMENT_DIR / "REPORT.md")


def main() -> None:
    results = json.loads(RESULTS_PATH.read_text())
    per_subject_a, per_subject_b, per_activity_a, per_activity_b = write_tables(results)
    write_figures(results, per_subject_a, per_subject_b, per_activity_a, per_activity_b)
    write_report(results, per_subject_a, per_subject_b, per_activity_a, per_activity_b)


if __name__ == "__main__":
    main()
