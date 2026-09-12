"""Stage 5 Final Synthesis: paper abstract fact sheet (master prompt Part V,
Section 27).

Every quantitative statement fit for an abstract, each with its source
claim_id (resolved fail-closed against results/final_claim_ledger.json),
metric, and exact safe wording. No unsupported number may enter the
abstract - this script only emits numbers that already exist in the claim
ledger's numeric_support fields.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "paper" / "final" / "abstract_fact_sheet.json"
LEDGER_PATH = "results/final_claim_ledger.json"

# Each entry: claim_id (must exist in the ledger) + the specific metric this
# abstract statement draws from that claim's numeric_support.
ABSTRACT_STATEMENTS = [
    {"claim_id": "sensor_minimalism_framing", "metric": "central scientific message / methodology"},
    {"claim_id": "ppg_plus_imu", "metric": "capacity-controlled wrist IMU HR benefit"},
    {"claim_id": "galaxy_replication", "metric": "external corroboration of wrist IMU HR benefit"},
    {"claim_id": "eog_incremental_value", "metric": "controlled sleep-staging benefit of EOG"},
    {"claim_id": "second_site_ppg", "metric": "negative second-site PPG result"},
    {"claim_id": "leg_bioz", "metric": "aggregate-negative, heterogeneous leg BioZ result"},
    {"claim_id": "thoracic_eis", "metric": "mixed, sign-reversing thoracic EIS result"},
    {"claim_id": "final_architecture", "metric": "selected final architecture"},
    {"claim_id": "pareto", "metric": "formal Pareto analysis outcome"},
    {"claim_id": "engineering_burden", "metric": "bounded engineering burden estimate"},
]


def build() -> dict:
    ledger = json.loads((REPO_ROOT / LEDGER_PATH).read_text(encoding="utf-8"))
    claims_by_id = {c["claim_id"]: c for c in ledger["claims"]}

    statements = []
    for entry in ABSTRACT_STATEMENTS:
        cid = entry["claim_id"]
        if cid not in claims_by_id:
            raise SystemExit(f"REFUSING TO WRITE: abstract fact sheet cites unknown claim_id {cid!r} - not in {LEDGER_PATH}.")
        c = claims_by_id[cid]
        statements.append(
            {
                "claim_id": cid,
                "metric": entry["metric"],
                "exact_safe_wording": c["exact_final_safe_wording"],
                "numeric_support": c["numeric_support"],
                "limitation": c["limitation"],
                "governing_evidence": c["governing_evidence"],
                "prohibited_stronger_wording": c["prohibited_stronger_wording"],
            }
        )

    return {
        "artifact_id": "biological-minimalism-stage5-abstract-fact-sheet-v1",
        "schema_version": "1.0.0",
        "sprint": "STAGE5_FINAL_SYNTHESIS_AND_RELEASE",
        "generated_role": "FINAL_SYNTHESIS_AND_RELEASE_OWNER",
        "purpose": (
            "Every quantitative/qualitative statement fit for the IAC paper abstract, each resolved fail-closed "
            "against results/final_claim_ledger.json at build time. No unsupported number may enter the abstract."
        ),
        "central_scientific_message": ledger["central_scientific_message"],
        "statements": statements,
        "statement_count": len(statements),
        "source": LEDGER_PATH,
        "status": "STAGE5_ABSTRACT_FACT_SHEET_REPORTED_COMPLETE_PENDING_INDEPENDENT_AUDIT",
    }


if __name__ == "__main__":
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output = build()
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({len(output['statements'])} statements)")
