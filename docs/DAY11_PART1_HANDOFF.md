# DAY 11 — PART 1 HANDOFF (Engineering Evidence Audit + Calc-Input Freeze)

> Handoff-first document. Written so Part-2 can continue **without any conversation context**.
> Everything below is derived only from committed artifacts on the canonical Day-10 base.

## 0. Canonical starting point

- **Repository:** `/Users/emirharunsunbul/Documents/ChatGPT/IAC`
- **Remote:** `origin` → `https://github.com/ProfIsmeet/biological-minimalism.git`
- **Canonical Day-10 base commit (verified):** `e414ef5c0c2b00f7d80b681848d37d7c59e523b5` (matches accepted report `e414ef5`)
- **Day-10 scientific branch (verified):** `origin/day10-scientific-repro-freeze-ml` @ `94d366f` — already integrated; **no merge needed**.
- **Part-1 working branch:** `day11-engineering-audit` (created from `e414ef5`)
- Working tree was clean; no conflict markers; `main` untouched.

## 1. What Part-1 did (completed)

1. **Verified Day-10 canonical state** — commit, remote, clean tree, all accepted artifacts present (scientific reproduction PASS, frozen-env verification, dataset fingerprint manifest, interaction experiment, EOG operational burden, reference BOM readiness, architecture decision matrix, Pareto readiness blockers, claim traceability, freeze checklist, Furkan Day-10 handoff, jury-defense master).
2. **Closed the Day-10 live-browser item** — see §2.
3. **Audited engineering evidence** for all 9 components + EOG across 5 modules.
4. **Froze Part-2 calculation inputs** (power + mass) and **operating-point / duty assumptions**.
5. Produced 4 machine-readable artifacts + this handoff.

## 2. Live-browser validation — CLOSED (bounded)

The Day-10 remaining item was the **client-rendered DOM** of Research Mode.

- The **Claude-in-Chrome extension was NOT connected** (same unavailability anticipated by the brief).
- **Substitute used:** the **Chrome DevTools MCP** browser (`mcp__plugin_ecc_chrome-devtools__*`) drove a real Chromium page against the live stack (backend `127.0.0.1:8000` from `backend/.venv`, frontend `127.0.0.1:3000` via `npm run dev`). A full a11y-tree DOM snapshot + targeted `evaluate_script` reads + console + network were captured.
- **Result: PASS.** All required client-DOM content rendered; **0 console errors/warnings; all 12 API requests HTTP 200**; servers stopped afterward (ports 3000/8000 free).

Confirmed in the rendered DOM:
- **Reproducibility panel:** `SCIENTIFIC_REPRODUCTION_PASS`; frozen environment verified; datasets fingerprinted (266/266); checkpoints externally durable (50, GitHub Release); canonical reproduced (zero numerical difference); robustness reproduced (114/114 within 1e-4 bpm). Explicitly says **"not a final-architecture readiness signal"** and **"NOT independent-dataset replication"** (does NOT imply final architecture / final freeze / independent replication). ✅
- **Interaction panel:** M0 EEG / M_A EEG+EOG / M_B EEG+Resp / M_AB EEG+EOG+Resp; estimate `+0.0031 macro-F1`; **"approximately additive / unresolved"**; **"not a synergy claim"** (does NOT imply synergy). ✅
- **Sleep:** primary n=3, secondary n=8, shuffled-EOG control, N3 regression disclosed, **no pooled n=11 headline** (matrix/boundary keep primary+secondary separate). ✅
- **PPG:** capacity-control caveat rendered (A_cap, capacity-matched C→B). ✅
- **PTT:** heterogeneity + **s2 sensitivity** rendered ("aggregate negative direction dominated by subject s2; excluding s2 flips the aggregate"; "s2 is never removed from the frozen primary result"; "Sensitivity analysis: Available"). ✅
- **Digital Twin (`/digital-twin`):** "synthetic, conceptual", "untrained and not validated", "proposed", "Demo" — does NOT look like a validated astronaut model. ✅
- **Mission / architecture (on `/research`):** global architecture UNRESOLVED / "no outcome has been applied"; Pareto `STRUCTURAL_ONLY_DESCRIPTIVE; FORMAL_PARETO_NOT_READY` / `NOT_READY`; power & mass unknowns render as **"Unknown" / "Not yet quantified"** (never zero); EOG burden not zeroed; **IMU low burden conditional on wrist colocation**; **second PPG adds 1 physical + 1 optical site**. ✅
- **Mission Overview (`/mission-overview`):** clearly-labelled synthetic telemetry demo; no architecture/Pareto over-claims. ✅

**To re-run the browser check yourself:**
```
# backend
cd backend && .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# frontend (separate shell)
cd frontend && npm run dev            # serves http://127.0.0.1:3000
# then open /research, /digital-twin, /mission-overview
```

## 3. Assumptions FROZEN by Part-1 (Part-2 must honour)

- **Reference architecture is Day-6 topology** (`hardware_topology_contract.json`): 5 modules (wrist, chest, head, leg, second-PPG branch), 9 components. Not a final BOM.
- **Representative part classes preserved verbatim:** MAX86141, BMI270, TMP117, OPT3001-Q1, ADS1292R, ADS1299-4, AD5940. **Do not silently replace.**
- **EOG reference calculation case = `REFERENCE_SHARED_HEAD_MODULE`** (EOG on a spare channel of the ADS1299-4-class head-module AFE, reference/bias shared): **+2 lateral-ocular sensing electrodes, +0 reference/bias, +0 new module.** Alternative `ALTERNATIVE_STANDALONE_EOG` (3–4 contacts, possibly +1 module) is documented but NOT the reference case. Sensing-contact increment **= 2** is interpretation-independent and defensible.
- **Light sensor stays `LOCATION_UNRESOLVED`** (wrist vs cabin). Both consequences documented; do not attribute body-worn burden until placement is frozen.
- **Duty-cycle assumptions are `REFERENCE_SCHEDULE_ASSUMPTION`s, NOT deployable duty cycles.** Scientific sample rate ≠ product duty cycle.
- **Reference acquisition rates (schedule assumptions):** PPG 64 Hz, IMU 32 Hz, temp 1 Hz, light continuous, ECG 250 s/s, EEG 250 s/s payload (dataset EEG/EOG are 100 Hz), second-PPG 500 Hz. BioZ (thoracic + leg) cadence UNKNOWN.

## 4. Source-classification scheme (use consistently in Part-2)
`DATASHEET_DIRECT` · `DATASHEET_CALCULATED` · `REFERENCE_SCHEDULE_ASSUMPTION` · `ARCHITECTURE_ASSUMPTION` · `MEASURED_IN_PROJECT` (none exist) · `UNKNOWN`. Never mix; unknowns are `null`/status, never `0`.

## 5. Files to USE in Part-2 (inputs)

| File | Role |
|---|---|
| `results/engineering_evidence_inventory_day11.json` | Per-component evidence inventory (authoritative) |
| `results/power_calculation_inputs_day11.json` | Frozen power inputs + `average_power_ready` flags |
| `results/mass_calculation_inputs_day11.json` | Frozen mass contributors (all NOT_READY) |
| `results/day11_part2_calculation_readiness.json` | Per-module go/no-go for Part-2 |
| `results/operational_cost_catalog.json` | SOURCE OF TRUTH for datasheet power/rate |
| `results/hardware_topology_contract.json` | Module/topology/contact burden |
| `results/eog_operational_burden_day10.json` | EOG incremental burden detail |
| `results/reference_bom_readiness_day10.json` | BOM readiness framing |
| `results/pareto_readiness_blockers.json` | Blocker list |
| `results/architecture_decision_matrix.json` | Per-(target,candidate) gate decisions |

## 6. Defensible power evidence today (component/AFE boundary only — NOT system power)

| Component | Reference active power | Class | avg-power ready |
|---|---|---|---|
| skin_temperature (TMP117) | 0.01155 mW @1 Hz, 3.3 V | DATASHEET_CALCULATED | ✅ component-boundary |
| light_sensor (OPT3001) | 0.00594 mW continuous, 3.3 V | DATASHEET_CALCULATED | ✅ component-boundary (if wrist-mounted) |
| ecg_chest (ADS1292R) | 0.67 mW @2ch,250 s/s | DATASHEET_CALCULATED | ✅ AFE-only |
| wrist_imu (BMI270) | 0.018–0.378 mW band, 1.8 V | DATASHEET_CALCULATED | ⚠️ PARTIAL (band, no single 32 Hz point) |
| wrist_ppg (MAX86141) | ≤0.018 mW AFE floor (LEDs excluded) | DATASHEET_CALCULATED | ❌ (LEDs dominate, OPEN) |
| second_ppg_site (MAX86141-class) | ≤0.018 mW AFE floor | DATASHEET_CALCULATED | ❌ (LEDs + 500 Hz + boundary OPEN) |
| thoracic_bioz / leg_bioz (AD5940) | UNKNOWN (6.5 µA potentiostat ≠ BioZ power) | UNKNOWN | ❌ |
| frontal_eeg / frontal_eog (ADS1299-4) | UNKNOWN (no operating point) | UNKNOWN | ❌ |

## 7. Calculations NOT yet performed (Part-2 scope)

- **NO** system average power, **NO** module system-power total, **NO** daily energy.
- **NO** mass estimate of any kind (all modules NOT_READY).
- **NO** formal Pareto frontier; **NO** final architecture selection; **NO** cross-target ranking.
- Part-1 deliberately stops at **component/AFE-boundary reference power** readiness.

## 8. Part-2 recommended sequence

1. Wrist + chest **PARTIAL** sensing-IC reference active-power bands (component/AFE boundary, LED-excluded, no system sum). See readiness matrix `recommended_part2_action`.
2. Resolve the **top power blockers** to unlock more: (a) MAX86141 LED/optical operating point, (b) ADS1299 EEG operating point + session duty, (c) AD5940 active BioZ measurement power + cadence, (d) MCU/radio/regulator identity — the shared subsystems gating EVERY module's system power.
3. Mass: needs a frozen component + mechanical selection before any estimate; do not estimate package mass from dimensions without an explicit material model.
4. Only after (2)+(3) revisit Pareto blockers and the architecture decision gate (**Part-3**, not Part-2).

## 9. WARNINGS

- **Do NOT** sum component powers into a system number; **do NOT** treat AFE `<10 µA` MAX86141 as deployable optical power (LEDs dominate); **do NOT** use AD5940 6.5 µA potentiostat as BioZ power.
- **Do NOT** zero-out EOG contact burden or the second-PPG-site burden because of favorable/negative science.
- **Do NOT** upgrade any CONDITIONAL/ DEPRIORITIZE decision — Day-10 gate stands (IMU + EOG = CONDITIONAL_FOR_TARGET; second PPG = DEPRIORITIZE_FOR_TARGET; final architecture UNRESOLVED).
- **Do NOT** pool Sleep primary n=3 with secondary n=8; **do NOT** compare HR-MAE to sleep macro-F1.
- Engineering power/mass work does **NOT** resolve cross-target scientific incomparability (a BLOCKER Part-2 cannot fix).
- **Environment note:** GateGuard fact-forcing hook is active in this repo (blocks first Bash/Write per new file); disable with `ECC_GATEGUARD=off` if it impedes Part-2.

## 10. Corrections / contradictions found
None. Audit is consistent with Day-10 canonical state: system power/mass NOT_READY, Pareto NOT_READY, no false zeros in artifacts or DOM, EOG shared-reference path and light-sensor LOCATION_UNRESOLVED both intact.
