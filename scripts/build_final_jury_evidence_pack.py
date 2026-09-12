"""Stage 5 Final Synthesis: final jury evidence pack (master prompt Part VI,
Sections 32-34).

Every answer cites claim_id(s) from results/final_claim_ledger.json; the
script resolves each citation into its governing_evidence/numeric_support at
build time (fail-closed if a citation doesn't exist) so the pack can never
silently drift from the claim ledger it must trace to.

Covers the required questions from master prompt Section 33 plus the
Day7-11 jury Q&A already accepted in docs/JURY_DEFENSE_MASTER.md (not
duplicated here - that file remains authoritative for its own Q1-Q40; this
pack adds the Stage-5-specific final-architecture questions that postdate it).
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "presentation" / "final_jury_evidence_pack.json"
LEDGER_PATH = "results/final_claim_ledger.json"


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


QUESTIONS = [
    {
        "question": "Why these sensors?",
        "answer_15s": "We selected CORE_PLUS_CONTEXT - wrist PPG+IMU, chest ECG, frontal EEG+EOG - because every included modality has a measured incremental-value result or a foundational role under controlled testing, not intuition.",
        "answer_45s": "Each included modality traces to a specific governing experiment: wrist IMU shows a capacity-controlled, externally-replicated (with heterogeneity) HR benefit; EOG shows same-dataset controlled sleep-staging benefit at near-zero marginal burden; ECG and frontal EEG are foundational reference/monitoring signals. A formal Pareto analysis over 4 candidate classes found CORE_PLUS_CONTEXT and MINIMAL_CORE both non-dominated; the Coordinator selected CORE_PLUS_CONTEXT for the EOG capability at low burden, accepting bounded engineering uncertainty (Gate D CONDITIONALLY_READY).",
        "evidence_claim_ids": ["sensor_minimalism_framing", "final_architecture", "ppg_plus_imu", "eog_incremental_value"],
        "forbidden_overclaim": "'Four sensors are proven sufficient.'",
    },
    {
        "question": "Why remove BioZ?",
        "answer_15s": "Thoracic BioZ (EIS) showed a COMPLETE_MIXED, negative-leaning result on the corrected LBNP protocol (n=12) that sign-reverses without a single subject - we excluded it rather than force a weak result into the architecture.",
        "answer_45s": "Under the frozen 0-60 mmHg protocol, thoracic EIS added no stable aggregate benefit over ECG+pleth (A-B = -0.452 mmHg MAE, 3/12 subjects favor it, and the aggregate sign reverses if subject 9 is removed). Leg BioZ (QDE V2) was separately excluded for the same reason: aggregate-negative (n=10) but heterogeneous (7/10 subjects individually favor it). Neither result proves BioZ is useless - both remain visible as mixed/heterogeneous evidence, not erased.",
        "evidence_claim_ids": ["thoracic_eis", "leg_bioz"],
        "forbidden_overclaim": "'BioZ is proven useless'; any claim that this disproves microgravity fluid-shift monitoring.",
    },
    {
        "question": "Why retain EOG?",
        "answer_15s": "EOG showed controlled, same-dataset incremental sleep-staging value (B-A = +0.028 macro-F1, 4/5 seeds) at near-zero marginal burden (+0.375 mW, +0.4 g, +2 contacts) by sharing EEG infrastructure.",
        "answer_45s": "The primary Sleep-EDF result, its shuffled-EOG control, and a prospective n=8 secondary holdout (zero retraining) all support EOG's same-dataset value, though REM gains strongly while N3 regresses in the secondary cohort - disclosed, not smoothed over. External validity is only bounded (HMC n=7 diagnostic, not a full-cohort replication), so Gate E froze EOG inclusion CONDITIONALLY with an explicit revision trigger tied to the HMC full-cohort result.",
        "evidence_claim_ids": ["eog_incremental_value", "hmc"],
        "forbidden_overclaim": "'EOG is externally validated on an independent cohort.'",
    },
    {
        "question": "Why not wait for HMC?",
        "answer_15s": "HMC access works (59/151 subjects downloaded, 52 SHA256-verified) but training the full 151-subject cohort is a compute/time-budget constraint, not an access blocker - so Gate E freezes EOG conditionally with a predefined revision trigger instead of waiting indefinitely.",
        "answer_45s": "A bounded n=7 diagnostic already exists and does not itself establish external replication in either direction (B-A = -0.031 macro-F1, 2/5 seeds favor B). Rather than block the whole architecture decision on an open-ended full-cohort run, the Coordinator made an explicit, disclosed FREEZE_CONDITIONALLY decision: EOG stays in the architecture now, and a stable, majority-consistent negative full-cohort HMC result would reopen that inclusion.",
        "evidence_claim_ids": ["hmc"],
        "forbidden_overclaim": "'HMC replicates or fails to replicate Sleep-EDF' (n=7 is not sufficient to claim either).",
    },
    {
        "question": "Why sparse EEG?",
        "answer_15s": "The final architecture keeps the same sparse frontal-channel EEG already used in the accepted Sleep-EDF result; a bounded n=3 ds003838 diagnostic only proves the loader/pipeline works, not that sparse channels are validated.",
        "answer_45s": "ds003838's n=3 diagnostic (sub-032/033/034) is chance-level and driven by 2 of 3 subjects - far too small to justify a channel-count decision either way. Sparse-vs-full-montage EEG is therefore frozen CONDITIONALLY under Gate E, with the ds003838 full cohort (requiring ~93GB additional download, not yet attempted) as the predefined revision trigger.",
        "evidence_claim_ids": ["ds003838"],
        "forbidden_overclaim": "'Sparse EEG is population validated.'",
    },
    {
        "question": "What does GalaxyPPG prove?",
        "answer_15s": "GalaxyPPG (corrected cohort) is external-cohort corroboration, not identical replication: aligned wrist IMU adds a modest aggregate HR benefit with real participant heterogeneity - 12/18 and 13/18 (of two comparisons) participants favor it, after excluding 6/24 for a reference-signal defect.",
        "answer_45s": "An earlier GalaxyPPG analysis was invalidated after discovering a reference-ECG signal-quality defect in 6 of 24 subjects; the corrected 18-subject analysis is the only current governing result. It is qualitatively consistent with the PPG-DaLiA finding (A_cap->B +0.834 bpm, C->B +0.916 bpm) but is not framed as proving PPG-DaLiA's exact effect size replicates, and it is not spaceflight or astronaut data.",
        "evidence_claim_ids": ["galaxy_replication"],
        "forbidden_overclaim": "'GalaxyPPG replicates PPG-DaLiA exactly'; '24/24 subject cohort'; 'astronaut validation.'",
    },
    {
        "question": "Why is the old ~23% IMU number not your headline?",
        "answer_15s": "That number compared models of very different capacity (8,065 vs ~29,000 parameters); once capacity is matched, about 68% of the apparent gap disappears. The governing number is the capacity-controlled A_cap->B ~0.605 bpm (5/5 seeds).",
        "answer_45s": "The historical ~20.6%/23%/1.879 bpm figure is capacity-confounded and is explicitly marked HISTORICAL_ONLY in the claim ledger - it must never be cited as a clean IMU effect. The current, governing, capacity-controlled result (PPG-DaLiA A_cap->B +0.605 bpm; GalaxyPPG A_cap->B +0.834 bpm) is smaller but real, and is the number this project defends.",
        "evidence_claim_ids": ["old_ppg_imu_headline_20_6_23_percent", "ppg_plus_imu"],
        "forbidden_overclaim": "Citing 20.6%/23%/1.879 bpm as a current or clean IMU effect.",
    },
    {
        "question": "Why are negative results valuable?",
        "answer_15s": "Negative/mixed results (second-site PPG, leg BioZ, thoracic EIS) tell us where not to spend physical burden budget just as clearly as positive results tell us where to spend it.",
        "answer_45s": "If this project only reported positive findings, the minimalism claim would be unfalsifiable - anyone could add sensors without evidence and call it 'evidence-driven.' Publishing NOT_READY, mixed, and negative results (second-site PPG worse on aggregate and subject-fragile; leg BioZ aggregate-negative but heterogeneous; thoracic EIS mixed and sign-reversing) is what makes the positive claims (PPG+IMU, EOG) credible by contrast.",
        "evidence_claim_ids": ["second_site_ppg", "leg_bioz", "thoracic_eis", "sensor_minimalism_framing"],
        "forbidden_overclaim": "Omitting negative/mixed results from the final presentation to present a cleaner story.",
    },
    {
        "question": "Is this validated in astronauts?",
        "answer_15s": "No. Every governing dataset in this project is terrestrial (healthy or patient populations); LBNP is a terrestrial protocol-analog for hypovolemic stress, not a spaceflight experiment.",
        "answer_45s": "Spaceflight and microgravity are the motivation for this project, not a validation population it has access to. Terrestrial evidence, physiological plausibility, and spaceflight validation are kept as three explicitly separate tiers throughout the claim ledger, and are never collapsed into one another.",
        "evidence_claim_ids": ["astronaut_microgravity_applicability"],
        "forbidden_overclaim": "'Astronaut-validated'; 'proves microgravity fluid-shift monitoring works/doesn't work.'",
    },
    {
        "question": "Is the Digital Twin real?",
        "answer_15s": "It's a conceptual, synthetic architecture proposal - a 153,801-parameter untrained reference network - not a trained or longitudinally validated personalized model.",
        "answer_45s": "The Digital Twin architecture (per-modality encoders + fusion Transformer + 9 regression heads) exists as untrained reference code with an explicit ARCHITECTURE_ONLY_UNTRAINED_UNVALIDATED status. No trained checkpoint, no validated multi-target performance, and no runtime/energy/latency measurement is claimed. A synthetic demo exists and is labeled synthetic wherever shown.",
        "evidence_claim_ids": ["digital_twin"],
        "forbidden_overclaim": "'The Digital Twin learns the astronaut's baseline' (present-tense accomplished capability); presenting it as validated or trained.",
    },
    {
        "question": "What does 'minimalism' mean scientifically?",
        "answer_15s": "Evaluating whether each modality provides measurable incremental value after controlling for model capacity, temporal correspondence, subject separation, heterogeneity, and physical burden - not counting down to the fewest possible sensors for its own sake.",
        "answer_45s": "Minimalism here is a methodology, not a target sensor count. Every candidate modality is tested the same way: does it add value beyond a capacity-matched, temporally-aligned baseline, on held-out subjects, accounting for how heterogeneous that value is across subjects, weighed against the physical burden it adds? Some modalities pass this test, some are mixed, some fail it outright - the sensor count is an output of that process, not an input goal.",
        "evidence_claim_ids": ["sensor_minimalism_framing"],
        "forbidden_overclaim": "'We proved four sensors are enough.'",
    },
    {
        "question": "Why CORE_PLUS_CONTEXT instead of MINIMAL_CORE?",
        "answer_15s": "A formal Pareto analysis found MINIMAL_CORE and CORE_PLUS_CONTEXT both non-dominated - MINIMAL_CORE is strictly lower burden, but CORE_PLUS_CONTEXT adds a capability (sleep staging via EOG) MINIMAL_CORE structurally lacks. The Coordinator chose CORE_PLUS_CONTEXT as a judgment call within that set, not because it's mathematically superior.",
        "answer_45s": "Formal dominance requires being weakly better on every axis; because the two classes disagree (MINIMAL_CORE wins on burden, CORE_PLUS_CONTEXT wins on science breadth via a capability the other lacks entirely), the comparison is a partial order, not a total ranking - both remain Pareto-relevant, and no_unique_pareto_winner=true is recorded explicitly. The Coordinator's selection rationale: EOG adds controlled sleep-staging evidence at low incremental physical burden without adding a new body region or full module, while accepting conditional external-validation uncertainty.",
        "evidence_claim_ids": ["pareto", "final_architecture"],
        "forbidden_overclaim": "'CORE_PLUS_CONTEXT mathematically dominates MINIMAL_CORE.'",
    },
    {
        "question": "Why not EVIDENCE_EXTENDED?",
        "answer_15s": "EVIDENCE_EXTENDED remains only POTENTIALLY_DOMINATED (burden-superior candidates block it from formal dominance), and it would add modalities (BioZ, second-site PPG) whose own evidence is negative, mixed, or pending.",
        "answer_45s": "The formal Pareto analysis places EVIDENCE_EXTENDED and EXPERIMENTAL_EXTENDED in a separate potentially_dominated_set - not formally proven dominated (the methodology deliberately under-claims dominance rather than over-claims it), but not selected from the Pareto-relevant set either. Their constituent modalities are exactly the ones this project's own evidence disfavors or has not yet cleared for inclusion.",
        "evidence_claim_ids": ["pareto", "thoracic_eis", "leg_bioz", "second_site_ppg"],
        "forbidden_overclaim": "Presenting EVIDENCE_EXTENDED as formally proven dominated (the methodology only supports 'potentially dominated').",
    },
    {
        "question": "What would cause you to revise the architecture?",
        "answer_15s": "A stable, majority-consistent NEGATIVE full-cohort HMC result would reopen EOG's inclusion; a full-cohort ds003838 result could reopen the sparse-vs-full EEG channel-count decision - both are explicit, predefined Gate E revision triggers.",
        "answer_45s": "These are not ad hoc - they were defined at the same time as the conditional freeze itself (results/stage4_gate_e_coordinator_decisions.json revision_triggers), so the criteria for reopening the decision were fixed before seeing the outcome. Both HMC full-cohort and ds003838 full-cohort remain LOWER_PRIORITY_EXTERNAL_WORK_PENDING - real future work, not required for this release.",
        "evidence_claim_ids": ["hmc", "ds003838", "final_architecture"],
        "forbidden_overclaim": "Implying the architecture is immutable or unconditionally final.",
    },
]


def build() -> dict:
    ledger = _load(LEDGER_PATH)
    claims_by_id = {c["claim_id"]: c for c in ledger["claims"]}

    entries = []
    for q in QUESTIONS:
        resolved_evidence = []
        for cid in q["evidence_claim_ids"]:
            if cid not in claims_by_id:
                raise SystemExit(f"REFUSING TO WRITE: jury pack cites unknown claim_id {cid!r} - not in {LEDGER_PATH}.")
            c = claims_by_id[cid]
            resolved_evidence.append(
                {
                    "claim_id": cid,
                    "numeric_support": c["numeric_support"],
                    "governing_evidence": c["governing_evidence"],
                }
            )
        entries.append(
            {
                "question": q["question"],
                "answer_15s": q["answer_15s"],
                "answer_45s": q["answer_45s"],
                "evidence": resolved_evidence,
                "limitation": "; ".join(claims_by_id[cid]["limitation"] for cid in q["evidence_claim_ids"][:1]),
                "forbidden_overclaim": q["forbidden_overclaim"],
            }
        )

    return {
        "artifact_id": "biological-minimalism-stage5-final-jury-evidence-pack-v1",
        "schema_version": "1.0.0",
        "sprint": "STAGE5_FINAL_SYNTHESIS_AND_RELEASE",
        "generated_role": "FINAL_SYNTHESIS_AND_RELEASE_OWNER",
        "purpose": (
            "Jury/defense evidence pack for the Stage-5-specific final-architecture questions (postdate "
            "docs/JURY_DEFENSE_MASTER.md's Day7-11 Q1-Q40, which remains authoritative for its own scope and is "
            "not duplicated here). Every answer's evidence field is resolved programmatically from "
            f"{LEDGER_PATH} at build time - fail-closed if a cited claim_id does not exist."
        ),
        "related_pack": "docs/JURY_DEFENSE_MASTER.md",
        "questions": entries,
        "question_count": len(entries),
        "status": "STAGE5_JURY_EVIDENCE_PACK_REPORTED_COMPLETE_PENDING_INDEPENDENT_AUDIT",
    }


if __name__ == "__main__":
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output = build()
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({len(output['questions'])} questions)")
