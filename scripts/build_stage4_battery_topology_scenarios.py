"""Stage 4 Gate-D closure: battery topology scenarios (INTEGRATION_OWNER,
master prompt Part II).

Models BOTH plausible battery architectures without selecting one, per
the second of Gate D's 4 governing remediation items in
results/stage4_gate_d_burden_completeness.json ("Freeze the module-
boundary decision... OR publish a bounded interval"). This script takes
the "publish a bounded interval" path - final battery/topology selection
remains an explicit future decision, not made here.

NEW DISCLOSED GAP (checked, confirmed absent): no artifact anywhere in
this project states a target battery operating duration/runtime
requirement - results/reference_shared_electronics_day11.json explicitly
says "used_to_compute_runtime": false / "No runtime computed". Without a
runtime target, battery CAPACITY cannot be sized from an energy
requirement; this script therefore holds the already-frozen 150 mAh /
3.7 V / 190 Wh/kg reference-class UNIT constant across both scenarios
(never re-deriving a "better" capacity) and compares only the STRUCTURAL
mass/power delta the two topologies impose on top of that fixed unit.

Writes results/stage4_battery_topology_scenarios.json.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "results" / "stage4_battery_topology_scenarios.json"

readiness = json.loads((REPO_ROOT / "results/stage4_engineering_readiness.json").read_text())
candidate_classes = json.loads((REPO_ROOT / "results/stage4_architecture_candidate_classes.json").read_text())

PER_MODULE_BATTERY_G = readiness["mass"]["allowances_used"]["battery_reference"]["computed_mass_g"]  # 2.921 g
REGULATOR_EFFICIENCY = readiness["power"]["regulator"]["efficiency"]["value"]  # 0.85

# Modules required per candidate class, matching results/stage4_candidate_class_burden_comparison.json's
# modules_required lists (cited, not re-derived).
CLASS_MODULES = {
    "MINIMAL_CORE": ["wrist_module", "chest_module", "head_module"],
    "CORE_PLUS_CONTEXT": ["wrist_module", "chest_module", "head_module"],
    "EVIDENCE_EXTENDED": ["wrist_module", "chest_module", "head_module", "leg_module"],
    "EXPERIMENTAL_EXTENDED": ["wrist_module", "chest_module", "head_module", "leg_module", "optical_site_evaluation_branch"],
}

# Bounded engineering estimate for cross-body wiring harness per remote-module
# hub connection (NOT modeled anywhere else in this project - a shared hub
# requires routing power from one location to each other worn module, unlike
# the already-modeled PER-MODULE local interconnect which stays within one
# module). Based on thin flexible 2-4 conductor low-current cable,
# ~1-2 g/meter, over realistic wrist-to-torso / torso-to-head / torso-to-leg
# body-segment run lengths (0.3-0.7 m).
CROSS_BODY_WIRING_PER_CONNECTION_G = {"min": 0.3, "max": 1.5, "most_likely": 0.8}

SCENARIOS = {
    "SHARED_HUB": {
        "description": "One central battery pack (worn at a single hub location, e.g. chest/torso) supplies power via wiring to every other worn module.",
        "battery_count": 1,
        "battery_sizing_basis": (
            "No project-wide runtime/operating-duration requirement exists (checked: "
            "results/reference_shared_electronics_day11.json explicitly states used_to_compute_runtime=false, "
            "'No runtime computed - system average power is NOT_READY'). Without a stated energy requirement, "
            "this scenario cannot independently derive a 'right-sized' hub capacity - it holds total required "
            "capacity at N x 150 mAh (N = module count), i.e. the SAME total energy as N per-module reference "
            "batteries, consolidated into 1 pack. This is the only defensible basis absent a runtime target; "
            "it is NOT evidence that 1 pack could be made smaller than N x 150 mAh."
        ),
        "battery_mass_basis": (
            "Held IDENTICAL to Scenario B's per-cell reference (190 Wh/kg) - no project-specific figure exists "
            "for battery-pack economies of scale (larger single cells commonly have somewhat better effective "
            "Wh/kg than several small cells due to proportionally lower packaging/protection-circuit overhead, "
            "but this project has never measured or assumed such a figure, so assuming better density here would "
            "be inventing precision). Total cell mass is therefore mass-neutral vs. Scenario B at this project's "
            "current evidence level - real-world consolidation could plausibly IMPROVE it, but that is not assumed."
        ),
        "additional_burden": {
            "cross_body_wiring_harness_g_per_remote_module": CROSS_BODY_WIRING_PER_CONNECTION_G,
            "regulator_stage_note": (
                "If the hub pre-regulates before distribution and each remote module ALSO locally regulates "
                "(two stages), combined efficiency degrades from the already-frozen single-stage 0.85 down to "
                f"approximately {round(REGULATOR_EFFICIENCY * REGULATOR_EFFICIENCY, 4)} (0.85 x 0.85, i.e. two "
                "compounded conversion stages) - a real possible power penalty, not assumed by default. If the hub "
                "distributes raw battery voltage with only ONE regulation stage at each remote module (as today), "
                "efficiency is unchanged at 0.85. Which applies depends on a distribution-voltage design choice "
                "not yet made - bounded as [0.7225, 0.85], not asserted as a single value."
            ),
            "single_point_of_failure_note": "Qualitative risk, not a mass/power quantity: a single hub-battery failure disables every module simultaneously, vs. Scenario B where one module's battery failure is isolated.",
        },
        "reduced_burden": {
            "note": "Per-cell protective-circuit/connector overhead for (N-1) cells is plausibly reduced by consolidation, but is not separately broken out anywhere in results/reference_mass_readiness_day11_part2.json's battery allowance (bundled into the flat 190 Wh/kg figure) - this saving cannot be quantified without fabricating a new per-cell-overhead figure this project has never established. Not claimed as a quantified saving.",
        },
    },
    "DISTRIBUTED_PER_MODULE": {
        "description": "Separate battery per physical module/body region - the assumption already used throughout results/stage4_engineering_readiness.json.",
        "battery_sizing_basis": "Unchanged from the already-frozen per-module reference: 150 mAh / 3.7 V / 190 Wh/kg per module instance.",
        "battery_mass_basis": f"{PER_MODULE_BATTERY_G} g per module instance (unchanged, already-published figure).",
        "additional_burden": {
            "charging_circuitry_note": "If each module charges independently (vs. a single hub charge point), N separate charge-management ICs/connectors may be required - not currently modeled as a separate BOM line in reference_bom_readiness_day11_part2.json (folded, if at all, into the generic per-module PCB allowance).",
            "connector_burden_note": "N separate charging/maintenance access points instead of 1 - a real usability/connector-count burden, not quantified in mass here (connector_burden dimension is already flagged MISSING in results/stage4_gate_d_burden_completeness.json).",
        },
        "reduced_burden": {
            "note": "No cross-body wiring harness required - each module is self-contained (already reflected in the existing per-module wiring_mass_g allowance, which only covers LOCAL interconnect).",
        },
    },
}

class_comparisons = []
for class_id, modules in CLASS_MODULES.items():
    module_count = len(modules)
    remote_connections = module_count - 1  # hub is one of the modules; every other module needs a wiring run
    distributed_battery_total_g = round(module_count * PER_MODULE_BATTERY_G, 3)
    shared_hub_battery_total_g = distributed_battery_total_g  # mass-neutral cell assumption, see SCENARIOS note
    wiring_delta = {
        "min": round(remote_connections * CROSS_BODY_WIRING_PER_CONNECTION_G["min"], 3),
        "max": round(remote_connections * CROSS_BODY_WIRING_PER_CONNECTION_G["max"], 3),
        "most_likely": round(remote_connections * CROSS_BODY_WIRING_PER_CONNECTION_G["most_likely"], 3),
    }
    class_comparisons.append({
        "class_id": class_id,
        "modules": modules,
        "module_count": module_count,
        "distributed_per_module_total_battery_g": distributed_battery_total_g,
        "shared_hub_total_battery_g": shared_hub_battery_total_g,
        "battery_mass_delta_g": 0.0,
        "shared_hub_additional_wiring_g": wiring_delta,
        "net_mass_delta_shared_hub_minus_distributed_g": {
            "min": wiring_delta["min"],
            "max": wiring_delta["max"],
            "most_likely": wiring_delta["most_likely"],
            "interpretation": "Shared hub is mass-NEUTRAL-to-WORSE than distributed under this project's current evidence (no economies-of-scale figure exists to credit the hub with a battery-mass saving, but the hub does add a real, currently-unmodeled wiring harness).",
        },
        "regulator_efficiency_range": {"min": round(REGULATOR_EFFICIENCY * REGULATOR_EFFICIENCY, 4), "max": REGULATOR_EFFICIENCY, "note": "Shared hub may or may not add a second regulation stage; distributed keeps the already-frozen single-stage 0.85."},
    })

does_ranking_depend_on_topology = {
    "verdict": "NO for relative candidate ORDERING, YES for absolute burden magnitude of multi-module classes",
    "reasoning": (
        "Under this project's current evidence (no battery-pack economies-of-scale figure, no runtime "
        "requirement to size a hub differently), the shared-hub scenario is never mass-BETTER than distributed - "
        "it is mass-neutral at best (battery cells) and mass-WORSE at worst (added wiring, possible extra "
        "regulation loss). Since every candidate class's relative mass ORDERING (MINIMAL_CORE < CORE_PLUS_CONTEXT "
        "<= EVIDENCE_EXTENDED <= EXPERIMENTAL_EXTENDED by module count) is preserved under EITHER scenario "
        "(distributed always <= shared-hub in this project's evidence), topology choice does not reverse "
        "candidate-class ORDERING. However, the ABSOLUTE burden magnitude for multi-module classes "
        "(EVIDENCE_EXTENDED, EXPERIMENTAL_EXTENDED) does shift by the wiring-harness delta (up to "
        "~1.5 g x remote-module-count), which is a real, currently-unbounded-in-the-base-model addition that "
        "the existing results/stage4_engineering_readiness.json system totals do not include under either topology."
    ),
}

output = {
    "artifact_id": "biological-minimalism-stage4-battery-topology-scenarios-v1",
    "schema_version": "1.0.0",
    "sprint": "STAGE4_GATE_D_BURDEN_CLOSURE",
    "generated_role": "INTEGRATION_OWNER",
    "purpose": "Model both plausible battery architectures (shared-hub vs. distributed/per-module) without selecting one, answering whether final architecture ranking depends materially on the choice.",
    "operating_duration_requirement_status": {
        "status": "ABSENT",
        "evidence": "results/reference_shared_electronics_day11.json battery.used_to_compute_runtime=false, runtime_note='No runtime computed - system average power is NOT_READY.' No other project artifact states a target operating duration.",
        "consequence": "Battery capacity cannot be independently sized in either scenario from an energy requirement - both scenarios hold the already-frozen 150 mAh/module reference class constant rather than inventing a duration-derived capacity.",
        "surfaced_as_decision_variable": "A target single-charge operating duration (hours/days) is a genuine open Coordinator/engineering decision variable, not resolved by this script.",
    },
    "per_module_battery_reference": {
        "capacity_mah": 150.0,
        "voltage_v": 3.7,
        "energy_density_wh_per_kg": 190.0,
        "mass_g": PER_MODULE_BATTERY_G,
        "source": "results/stage4_engineering_readiness.json mass.allowances_used.battery_reference (unchanged, already-published).",
    },
    "scenarios": SCENARIOS,
    "candidate_class_comparison": class_comparisons,
    "does_ranking_depend_on_topology": does_ranking_depend_on_topology,
    "not_a_final_battery_selection": True,
    "final_architecture_status": "UNRESOLVED",
    "formal_pareto_status": "NOT_READY",
}

OUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Wrote {OUT_PATH}")
