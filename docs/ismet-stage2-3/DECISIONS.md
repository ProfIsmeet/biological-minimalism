# DECISIONS

## D1 — Existing clone reused, not a second fresh clone

The master prompt asks for "a fresh clone on your own computer." This session already has a fully-fetched, clean working clone of the exact same remote at `C:\Users\Administrator\Desktop\biological-minimalism`. Rather than create a redundant second clone on disk (which risks confusing which copy is authoritative), I fetched `origin` fresh, verified the working tree was clean/uncontaminated, stashed one unrelated pending change from a prior unrelated task (see STATUS.md), and branched directly from the verified `origin/codex/stage1-scientific-data-integrity` SHA. This satisfies the intent (a clean, verified starting point at the exact required base) without the risk of a second untracked directory.

## D2 — Branch tracking

`git checkout -b ismet/frontend-stage2-3-hardening origin/codex/stage1-scientific-data-integrity` set the new branch's upstream to the Stage-1 branch by default. This will be corrected to track the new branch's own remote ref only if/when it is pushed (`git push -u origin ismet/frontend-stage2-3-hardening`), so a plain `git push` never accidentally targets the Stage-1 branch.
