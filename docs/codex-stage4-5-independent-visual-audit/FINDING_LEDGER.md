# Finding Ledger

SOURCE_SHA: `979836ff704c2d6df43152e4d733d48703d12848`
IMPLEMENTATION_CHECKPOINT_SHA: `6d169c4abe6d68a7758f515bad5df39b8d851727`
REPORT_COMMIT: this commit; resolve with `git rev-parse HEAD`
Target: `codex/stage4-5-independent-visual-audit`

| ID | Severity | Reproduction and impact | Adjudication | Protection |
|---|---|---|---|---|
| F-01 | Medium | 1024×768 omitted the compact trend; 1280 began at the fold. Tablet users could not answer the required trend question. | Confirmed; corrected with a tablet HR/trend row and 1366px wide split. | Structural layout guard plus browser inspection at 1024/1280. |
| F-02 | Medium | During fault and real `warming_up`, the trend header retained a historical numeric bpm while the HR core said unavailable. | Confirmed; current trend summary now depends on prediction availability and labels retained history. | Behavioral helper cases for unavailable/not-applicable/available. |
| F-03 | Medium | “No affected region — Wrist, Chest confirmed” could imply whole-body or medical normality. | Confirmed; wording now limits the claim to no active simulated-fault region and separately names confirmed replay inputs. | Monitoring copy assertion and browser state matrix. |
| F-04 | Medium | Recharts axes and inference SVG labels used 10/11px despite a claimed 12px operational floor. | Confirmed; raised to 12px and added a runtime CSS floor for legacy micro-utilities. | Expanded typography verifier covers SVG/tick tokens and page composition. |
| F-05 | Medium | Global `CANONICAL_RUN_ORDER` silently subordinated unknown future runs and could not express per-slot policy. | Confirmed; replaced by exact per-entry path, digest, visual approval, superseded, and audit-only policy. | 13 verifier tests including future-run, hash-drift, unreviewed, same-slot, and per-entry selection. |
| F-06 | Medium | Critical rebuilding checks were source-string assertions only. | Confirmed; pure operational-presentation behavior is exercised with real values. | 1,059 monitoring assertions; source guards retained as supplementary wiring checks. |
| F-07 | Low | Segmented ring could read as confidence/progress. | Confirmed; proximate visible copy says four independent availability checks and “not confidence.” | Copy assertion and visual inspection. |
| F-08 | Medium | Reduce-motion switch lacked an accessible name/focus style and its visual state was stale cross-tab. | Confirmed; named/focus-visible switch and storage/custom-event subscription added. | Two-tab real-browser test: `false,false → true,true`; classes synchronized. |
| F-09 | Low | Comments described obsolete breakpoint/sizing behavior. | Confirmed; corrected comments. | Diff review. |
| S-01 | — | Fault text might truncate. | Disproved: full `PPG · packet loss · severity 0.9` was visible and present in the accessibility tree. | Existing full-string guard retained. |
| S-02 | — | Shared Panel typography might regress consumers. | Disproved after importer review and material-route inspection; defensive `min-w-0`, wrapping, and nonshrinking actions were added. | Lint/build plus route screenshots. |

No high- or medium-severity finding remains open.
