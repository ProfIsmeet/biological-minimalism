# Real S14 runtime evidence

## Asset adjudication

The owner-provided local PPG-DaLiA archive and owner-provided local Model B checkpoint both existed and were readable. The archive exposed subject S14. The checkpoint passed the application's loading and identity checks, loaded as `PPGDaliaHRPredictor`, and reported SHA-256 `c53a34586d2d6baf68aae4441b6c15a0f5f623f0ea70c023c7371c2dbded0e77`.

Assets were supplied only through the existing backend environment variables. Neither asset nor its private discovery path is present in the commit.

## Runtime identity

- Dataset: `PPG-DaLiA`
- Subject: `S14`
- Source type: `dataset_replay`
- Channels: `wrist_bvp`, `wrist_acc`, `chest_ecg`, `wrist_temp`
- Model: `PPGDaliaHRModelB:PPGPlusIMUHRModel`
- Replay speed: 5×
- Transport: REST control and metrics plus frontend WebSocket-connected status

## State sequence

| State | Inference/output | Freshness proof | Artifact |
|---|---|---|---|
| Nominal connected | 68.25598977283755 bpm, window 0 | Baseline | `s14-01-nom.png` |
| Active simulated fault | PPG modality dropout, severity 1 | Fault banner and source identity retained | `s14-02-active-condition.png` |
| Output withheld | `input_unavailable`, prediction `null` | Fail-closed; no zero or stale HR substituted | `s14-03-output-withheld.png` |
| Rebuilding | `warming_up`, prediction `null`; clear position 28.41853104007896 s | Genuine post-clear window accumulation | `s14-04-warmup-window.png` |
| Recovered | 73.8207543101579 bpm, window 23, start 46 s | Window advanced after fault clear | `s14-05-postcondition.png` |
| Fresh recovered HR | Same captured recovery sample, nominal index 0 → recovered index 23 | Explicit `fresh_after_fault: true` | `s14-06-fresh-hr.png` |

The application did not present missing data as zero, did not relabel synthetic data as recorded data, and did not reuse the pre-fault HR after recovery. All six PNGs are canonical entries in the manifest.
