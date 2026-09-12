# Stage 5 Paper Production Package

This package is structured material for IAC paper production, not a drafted
paper. Every claim below cites a `claim_id` from
[`results/final_claim_ledger.json`](../../results/final_claim_ledger.json) —
that file, not this prose, is the source of truth. If this document and the
ledger ever disagree, the ledger wins and this document is stale.

## Contents

- [`abstract_fact_sheet.json`](abstract_fact_sheet.json) — every quantitative statement fit for the abstract, source-resolved (Part 27).
- [`INTRODUCTION_CLAIMS.md`](INTRODUCTION_CLAIMS.md) — structured material for the Introduction (Part 26).
- [`METHODS_CONTRACT.md`](METHODS_CONTRACT.md) — datasets, splits, controls, seeds, external replication, burden methodology (Part 28).
- [`RESULTS_CONTRACT.md`](RESULTS_CONTRACT.md) — positive/replicated/mixed/negative/pending, not cherry-picked (Part 29).
- [`DISCUSSION_CONTRACT.md`](DISCUSSION_CONTRACT.md) — heterogeneity, evidence-driven selection, negative-evidence value, terrestrial limits (Part 30).
- [`LIMITATIONS.md`](LIMITATIONS.md) — explicit limitations list (Part 31).

## Governing artifacts (read these, not just this package)

- `results/final_claim_ledger.json` — the claim contract.
- `results/final_tables/table_a_modality_evidence.json` … `table_f_engineering_burden.json` — Tables A-F.
- `results/final_figure_manifest.json` — figure-data catalog with provenance.
- `results/final_reproduction_manifest.json` — per-experiment reproducibility class.
- `docs/STAGE4_FINAL_ARCHITECTURE_CLOSURE.md` — architecture closure narrative.
- `docs/FURKAN_PAPER_HANDOFF_DAY11.md` and `docs/FURKAN_PAPER_HANDOFF_CANONICAL_DAY9.md` — prior accepted paper-handoff material this package extends, not replaces.

## Central scientific message (frozen, do not replace)

> Biological Minimalism evaluates whether sensing modalities provide measurable incremental value after controlling for model capacity, temporal correspondence, subject separation, heterogeneity, and physical burden. Some modalities retain value under stronger controls and external replication, while others become mixed, negative, fragile, or deprioritized.

Prohibited replacement: *"We proved four sensors are enough."*
