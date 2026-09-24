# ISMET Frontend Stage 2-3 Hardening — Plan

## Scope (this document's own numbering, per the master prompt)

- Stage 2: accessibility, reduced-motion, resilient fallback correction.
- Stage 3A: deployment/reproducibility hardening integration (port from `origin/claude/deployment-hardening`).
- Stage 3B: canonical jury-demo bootstrap + honest release-evidence packaging.
- Stage 4 (visual art direction): explicitly out of scope, forbidden.

## Gate results (recorded before any edit)

- `origin/codex/stage1-scientific-data-integrity` exists: YES, SHA `cfd4935ee264cdeb3953c8b437c3936cd9e2f0ae`.
- `origin/claude/deployment-hardening` exists: YES, SHA `ef747182353560d6355931310a08bcce5d3a949d` (exact match to the expected commit named in the master prompt).
- Baseline gate: `verify:monitoring` 932/932, lint clean, `tsc --noEmit` clean, build 14/14 pages, `git diff --check` clean. **PASSED** — proceeding.

## Environment

- Node v24.19.0, npm 11.17.0, Python 3.13.0.
- Docker: **not available** (`docker: command not found`). All Docker-gated work will be reported `NOT_RUN_DOCKER_UNAVAILABLE`.
- Browser automation: Claude-in-Chrome extension not connected in this environment (confirmed unavailable in a prior session on this same machine). Browser-runtime claims will be marked accordingly.

## Milestone order

1. Milestone A (Stage 2): accessibility findings A1-A4, verification checkpoint, commit.
2. Milestone B (Stage 3A): inspect `origin/claude/deployment-hardening` diff, port valid changes only, commit.
3. Milestone C (Stage 3B): canonical jury bootstrap action + tests, commit.
4. Milestone D: release/jury evidence package.
5. Final adversarial review (two passes) + final verification + final report.

## Effort/scope honesty note

This is an extremely large assignment (accessibility audit across ~5 subsystems, a full branch-diff port, a new stateful bootstrap flow with 15+ required test cases, and a full evidence package). Given real time/context constraints in this session, work will proceed milestone-by-milestone with real verification at each checkpoint, and the run will stop and report PARTIAL honestly at whatever point further milestones cannot be completed with genuine verification, per Section 12 of the master prompt. STATUS.md is updated after every milestone so work is resumable without chat history.
