# Evidence Verifier Root Cause — Stage 6 Fresh-Session Audit & Closure

## The failure

`python scripts/verify_jury_release_evidence.py --root . --hash` at the
Stage 6 source tip (`82d136a`) exits `2`: `PRESENT=15 MISSING=1 EMPTY=0
AMBIGUOUS=8`, all 8 ambiguous slots reporting `issue=canonical SHA-256
does not match policy`.

## Isolating which commit introduced it

Created a throwaway detached worktree at the accepted Stage 7 parent
(`011a31683ce3444cd1b8f258c0308fb4c6997490` — before any Stage 6 commit
exists) and ran the identical command:

```
SUMMARY PRESENT=15 MISSING=1 EMPTY=0 AMBIGUOUS=8
```

**Identical result.** This proves conclusively that no Stage 6 commit
introduced this condition — it predates Stage 6 entirely, reproducing
exactly at the commit Stage 6 itself started from.

## Which slots, and why

All 8 ambiguous slots (`audit-main`, `audit-matrix`, `audit-recommendation`,
`prompt-3bc-human-visual`, `prompt-4-a11y-hardening`, `prompt-5-hostile-
dossier`, `presenter-script`, `recovery-card`) are `.md` text files.
`docs/JURY_RELEASE_EVIDENCE_POLICY.json` freezes an exact SHA-256 per slot.

For `audit-main`
(`frontend/qa-screenshots/claude-stage4-5-real-visual-implementation/AUDIT.md`):

```
actual file (as checked out):  f783016e...618798d
policy-frozen hash:            78838536...4676c0c7
LF-normalized file hash:       78838536...4676c0c7  <- matches policy exactly
```

Confirmed programmatically for all 8 files (a small script computing
`hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()` for every entry
in the policy and comparing to the frozen hash): **every single one**
matches its policy hash once CRLF is normalized to LF, and **none** of the
15 PNG/binary entries are affected (binary files are untouched by
line-ending conversion).

## Why this happens

`git config --get core.autocrlf` on this machine returns `true` — the
common Windows default. No `.gitattributes` file existed anywhere in the
repository before this audit. Without one, `core.autocrlf=true` silently
converts LF-stored text blobs to CRLF on checkout. The evidence policy's
hashes were computed against the LF bytes (as stored in the git object
database); the verifier reads the actual on-disk bytes, which — on this
checkout — are CRLF. The file's logical *content* is byte-for-byte
identical modulo the line-ending style; nothing about the evidence itself
is corrupted, duplicated, or missing.

## Ruling out the alternatives the master task asked to check

- **Filename collisions between required slots** (e.g. `default` containing
  `fault`): not the cause here — all 8 affected slots are the *same*
  canonical path before and after; no unregistered/duplicate file was
  found for any of them at the Stage 6 tip.
- **Genuinely absent evidence:** ruled out — all 8 files exist at their
  exact policy-specified canonical paths; only their checked-out bytes
  differ from the frozen hash.
- **Duplicate canonical files / generated evidence incorrectly marked
  canonical:** ruled out — no `superseded`/`unregistered` list was
  populated for any of the 8; the issue field is exclusively
  `canonical SHA-256 does not match policy`.
- **Manifest/index metadata disagreeing with files:** this *is* effectively
  what's happening, but the disagreement is caused by the checkout
  environment, not by a stale or incorrect policy entry — the policy's
  hash is correct (LF), only the working-tree bytes are wrong (CRLF).
- **Dirty working tree affecting the prior reported result:** ruled out —
  `git status` was clean at the exact source tip before any edit, and the
  detached-worktree reproduction at the Stage 7 parent (independent,
  freshly checked out) showed the identical result.

## The fix

Added `.gitattributes`:

```
frontend/qa-screenshots/**/*.md text eol=lf
frontend/qa-screenshots/**/*.json text eol=lf
frontend/qa-screenshots/**/*.png binary
```

This forces every future checkout of these evidence paths to produce LF
bytes regardless of the checking-out machine's `core.autocrlf` setting —
a root-cause fix, not a per-machine workaround. Then normalized the 8
currently-checked-out working-tree files to LF to match (git's own diff
machinery reported these normalizations as producing **zero net change**
relative to the already-committed blobs — confirming the git *object
store* already held the correct LF bytes all along; the bug was purely a
checkout-time conversion artifact, never a stored-content problem).

**Content verification:** `git diff -w` (ignore all whitespace) against
every affected file shows zero differences; a direct byte-level comparison
(`file bytes` vs. `git show HEAD:path` with CRLF stripped from both) also
confirms exact equality for a sampled file (`recovery-card.md`, 1930 bytes
before and after).

## Permitted-corrections compliance

- Weakened no required evidence — all 23 required slots remain required.
- Changed no required slot to optional.
- Ignored no ambiguity — every one was individually root-caused.
- Did not return exit 0 by hardcoding a pass — the script and policy file
  are both byte-for-byte unmodified; only the checkout mechanism for
  evidence text files was corrected.
- Deleted no unrelated historical evidence.
- Did not broadly exclude any directory — the `.gitattributes` scope is
  precise (`frontend/qa-screenshots/**/*.md` and `*.json`), not a blanket
  repo-wide line-ending policy.

## Result

```
python scripts/verify_jury_release_evidence.py --root . --hash
SUMMARY PRESENT=23 MISSING=1 EMPTY=0 AMBIGUOUS=0
F-07 status: EVIDENCE PRESENT (visual review separately recorded in policy)
exit code: 0
```

Reproduced identically across plain mode, `--hash` mode, and `--json --hash`
mode (`"complete": true`). This is exactly the originally-claimed Stage 7
baseline (23 present, 0 ambiguous, exit 0) — genuinely reproduced, not
merely re-asserted.
