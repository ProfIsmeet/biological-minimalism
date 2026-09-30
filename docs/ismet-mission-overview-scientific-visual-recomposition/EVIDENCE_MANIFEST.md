# Evidence Manifest — Mission Overview Scientific Visual Recomposition

Machine-readable manifest with full per-file metadata and SHA-256:
`frontend/qa-screenshots/ismet-mission-overview-scientific-visual-recomposition/EVIDENCE_MANIFEST.json`

- **29 screenshots**, all newly captured for this task against implementation
  checkpoint `9c20845a9559399eb1a58e73f476a811249116ba`. No screenshot was
  reused from an earlier task.
- **29 unique SHA-256 hashes** - verified no duplicates.
- Every file was opened and visually inspected at original resolution; the
  inspection directly produced findings MO-F02 (orbit centre overlapping the
  rings) and MO-F03 (IMU gutter reading 1.0/1.0 for a varying signal), both
  of which were fixed and the affected screenshots re-captured.

## Filename policy

Deliberately avoids the release-verifier collision tokens `fault`, `recover`
and `default` (noting `default` contains `fault`). Uses `adverse-onset`,
`adverse-sustained`, `rebuilding-window`, `restored-state`,
`adverse-response-timeline` and `first-viewport` instead. The release
evidence verifier was re-run after these files were added and returned
**exit 0 with AMBIGUOUS=0**, confirming no collision.

## Coverage against the required list

Captured: desktop first viewport and full page; ring close-up; radar
close-up; enlarged HR trend; signal ribbons; pipeline; adverse onset (PPG and
IMU); sustained adverse; rebuilding; restored; adverse-response timeline;
1366; 1280; tablet 1024x768 (first viewport + full page); tablet 768x1024;
mobile first viewport, ring+legend, HR trend, radar, signal lanes, pipeline,
full page, adverse state; source-establishing neutral state; keyboard focus;
reduced motion.

**Not captured, honestly:**
- *Genuine 200% zoom proof* and *zoom-restored proof* - the zoom itself is
  BLOCKED_EXTERNAL (see VERIFICATION_LEDGER.md). Zoom was never successfully
  changed from 100%, so there is nothing to restore and no proof to show.
  Two screenshots produced by a device-pixel-ratio change were **discarded**
  rather than presented as zoom evidence.
- *Genuine source-error state* - not reproduced, because forcing a real
  authoritative REST failure would require killing the backend mid-capture,
  which would also invalidate the surrounding replay session. The
  source-error path is instead covered behaviourally by regression tests
  asserting it is the only route to the red presentation and that it
  outranks a still-connecting socket.
