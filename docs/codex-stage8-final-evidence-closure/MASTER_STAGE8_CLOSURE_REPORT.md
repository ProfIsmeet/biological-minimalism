# Master Stage 8 closure report

## Independent verdict

`COMPLETE_ACCEPTED_AFTER_CORRECTIONS`

The source audit's `PARTIAL` verdict was correct when issued: it had accepted product corrections but lacked durable post-fix browser files, locally verified real-S14 runtime evidence, standards-based reduced-motion execution, and defensible genuine page-zoom proof. This continuation reproduced only those open gates and preserved the earlier reports as historical records.

No new critical, high, or medium product defect was reproduced. A preliminary full-page automation image suggested clipping at 200%, but independent native browser-window capture showed that the apparent defect was a capture-scaling artifact. It was not promoted to a finding and no product code was changed.

## Source and scope

- Authoritative source: `origin/codex/stage8-independent-browser-audit` at `035549d57748f5efb763cb1da550a115a58a36c0`.
- Closure branch: `codex/stage8-final-evidence-closure`.
- Durable-evidence implementation checkpoint: `9e0e55c04479f95fd7c4462dbd1bda57734bee19`.
- The expected source SHA was verified before editing and is an ancestor of the closure branch.
- No merge, rebase, reset, stash, clean, amend, or force-push was used.
- Product source, dependency manifests, dataset assets, and checkpoint assets were not changed.

## Closure evidence

- 40 canonical PNG files, 20,015,640 total bytes; largest file 1,189,542 bytes.
- Required responsive matrix: Mission Overview 6/6, Live Monitoring 6/6, six remaining principal routes at desktop and mobile 12/12.
- Real S14 sequence: 6/6 states—nominal, active fault, output withheld, rebuilding, recovered, and fresh recovered HR.
- Genuine zoom: 100% and 200% native browser-window PNGs for all four required routes, 8/8.
- Motion: normal and standards-emulated reduced-motion PNGs, 2/2.
- Manifest verifier: 565 pass, 0 fail, 40 required coverage slots, 0 ambiguous.
- Capture/runtime checks: 159/159 with zero page or console errors.
- Genuine zoom checks: 66/66.
- Chrome accessibility-tree and keyboard checks: 51/51 over all eight principal routes.

## Real S14 result

The owner-provided local PPG-DaLiA archive and owner-provided local Model B checkpoint were present, readable, and used through the supported backend environment contract without being copied into the repository. The checkpoint loaded as `PPGDaliaHRPredictor`; application identity SHA-256 was `c53a34586d2d6baf68aae4441b6c15a0f5f623f0ea70c023c7371c2dbded0e77`.

The connected source identified `PPG-DaLiA`, subject `S14`, channels `wrist_bvp`, `wrist_acc`, `chest_ecg`, and `wrist_temp`, and model `PPGDaliaHRModelB:PPGPlusIMUHRModel`. Nominal HR was 68.25598977283755 bpm at window 0. A full-severity PPG modality dropout made inference `input_unavailable` and the prediction `null`. Clearing the condition produced a genuine `warming_up` interval with a null prediction. Recovery produced 73.8207543101579 bpm at window 23, start 46 seconds. Because the recovered window index advanced from 0 to 23 after fault clearance, the recovered value is fresh rather than stale.

## Zoom and motion

Zoom used installed Chrome's browser-supported `chrome.tabs.setZoom` API, not viewport substitution or device emulation. At a fixed 1440×809 outer window, all required routes changed from CSS inner 1440×722, DPR 2 at 100% to 720×361, DPR 4 at 200%; `visualViewport` changed identically and the browser API returned 1 then 2. Horizontal overflow remained 0. Native Retina PNGs were 2880×1618. Reset restored 100% measurements.

Reduced motion used Playwright/CDP browser media emulation for `prefers-reduced-motion: reduce`. All 14 scenarios passed: initial media state, OS-or-app effective contract, live transitions, cross-tab synchronization, persisted route behavior, preserved play/pause control, dialog behavior, readable charts and Digital Twin content, and restoration to normal.

## Final verification

The final run preserved 1341/1341 monitoring checks, all seven monitoring sub-verifiers, 146/146 rendered-route checks, 353 backend passes with 4 skips, and 2/2 targeted SHAP concurrency tests. TypeScript, ESLint, the 14-page production build, release-evidence verification, closure-evidence verification, and `git diff --check` passed. The release verifier remained unweakened at PRESENT 23, optional MISSING 1, EMPTY 0, AMBIGUOUS 0.

## Acceptance boundary

Keyboard navigation, focus visibility, dialog focus trap, Escape, focus restoration, skip link, navigation, expandable content, chart alternatives, headings, landmarks, tables, button names, and status semantics were inspected in Chrome. Actual VoiceOver execution remains `DEFERRED_BY_OWNER`, not pass or fail, and is outside this Stage 8 closure.

Recommendation: owner merge is supported. Stage 8 is closed; Stage 9 is not started by this work.
