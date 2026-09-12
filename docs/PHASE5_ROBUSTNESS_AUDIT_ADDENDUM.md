# Phase 5 robustness audit addendum

**Status:** Post-hoc interpretation and audit note. This document is not part of the frozen Phase 5 protocol and does not amend its configuration, condition definitions, result values, or hashes. The experiment was not rerun for this addendum.

## IMU fault-amplitude calibration

The implemented IMU additive-noise and saturation faults calibrate their scale from the first affected S14 replay batch. That initial interval is low-motion/rest-like. A read-only diagnostic found first-batch per-axis IMU standard deviations of approximately `[0.0075, 0.0093, 0.0080]`, while median values across typical later windows were approximately `[0.122, 0.144, 0.101]`. Nominal additive-noise severity `1.0` therefore represented only about 6–8% of typical movement-scale variation on those axes for many windows.

The reported result remains valid for this implemented, first-batch-calibrated perturbation. Severity is a dimensionless experiment setting, not a universal physical corruption magnitude. The near-zero aggregate HR degradation must not be described as robustness to universally severe IMU noise.

## IMU dependence diagnostic

An independent, read-only diagnostic found that zeroing or freezing IMU changed model output and increased MAE by approximately `+0.95 bpm`. The committed frozen-sensor condition similarly shows degradation relative to clean replay. The model therefore does use IMU; the small effect of the tested additive-noise grid is not evidence that IMU is irrelevant.

A plausible interpretation combines under-scaling from first-batch calibration, attenuation of present-but-noisy perturbations by per-window z-scoring, and some genuine tolerance within the tested range. This is an interpretation, not a validated causal decomposition.

## Packet loss is primarily an availability result

The canonical inference path requires complete, contiguous native-rate windows. If an independently dropped required sample leaves a window incomplete, that window is rejected before ordinary model evaluation. The packet-loss conditions therefore characterize fail-closed pipeline availability much more than continuous neural-network error degradation. The few surviving windows remained approximately clean, but they are small selected subsets and do not support a broad accuracy claim.

Undefined MAE/RMSE for zero-survivor conditions must remain `N/A`; rejection must not be converted into a fabricated large error. Continued output in other conditions is not evidence that the model detected the fault.

## Reproducibility and replay display semantics

The verified environment used approximately PyTorch `2.6.0`. The frozen golden-integration contract uses a `0.001 bpm` tolerance. Exact bitwise equality across arbitrary PyTorch, BLAS, hardware, or operating-system versions is not guaranteed; the tolerance is the relevant parity contract.

Replay inference completes on 8-second windows at a 2-second stride. Between completed inference strides, the interface may retain the latest valid AI HR. A displayed value can therefore be the most recently completed model-window estimate rather than a continuously recomputed instantaneous HR.

## Claim boundaries

This audit explicitly prohibits claims that Phase 5 demonstrates:

- robustness to universally severe IMU corruption;
- generic IMU irrelevance;
- automatic neural-network fault detection;
- predictive confidence or calibrated uncertainty;
- fault tolerance;
- population-level robustness;
- astronaut or microgravity robustness.

The defensible statement is narrower: under the implemented first-batch-calibrated IMU perturbation, aggregate held-out S14 HR error changed very little; zero/frozen IMU diagnostics confirm model dependence; and independent native-sample loss primarily caused the current contiguous-window pipeline to fail closed.
