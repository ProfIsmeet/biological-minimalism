# PPG-DaLiA S14 fault-robustness characterization

This is a controlled single-subject result for official held-out S14, not a population-level robustness claim.

Post-hoc interpretation note: see `docs/PHASE5_ROBUSTNESS_AUDIT_ADDENDUM.md` for the first-batch IMU calibration caveat, IMU-dependence diagnostic, packet-loss availability interpretation, and reproducibility limits. The addendum does not change this frozen experiment or its numerical results.

## Clean baseline

- Eligible/valid windows: 4476/4476
- Availability: 1.000000
- MAE: 5.083854 bpm
- RMSE: 7.492855 bpm
- Canonical and golden parity gates: PASS

## Full concrete condition table

MAE/RMSE are valid-prediction-only; failure counts retain every eligible window.

| Condition | Fault | Target | Severity | Seed | Valid/eligible | Availability | MAE | RMSE | Unavailable | Invalid | Error |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| clean | clean | — | N/A | N/A | 4476/4476 | 1.000000 | 5.0839 | 7.4929 | 0 | 0 | 0 |
| modality_dropout__ppg__severity_1 | modality_dropout | ppg | 1.00 | N/A | 0/4476 | 0.000000 | N/A | N/A | 4476 | 0 | 0 |
| modality_dropout__imu__severity_1 | modality_dropout | imu | 1.00 | N/A | 0/4476 | 0.000000 | N/A | N/A | 4476 | 0 | 0 |
| modality_dropout__both__severity_1 | modality_dropout | both | 1.00 | N/A | 0/4476 | 0.000000 | N/A | N/A | 4476 | 0 | 0 |
| frozen_sensor__ppg__severity_1 | frozen_sensor | ppg | 1.00 | N/A | 0/4476 | 0.000000 | N/A | N/A | 0 | 4476 | 0 |
| frozen_sensor__imu__severity_1 | frozen_sensor | imu | 1.00 | N/A | 4476/4476 | 1.000000 | 6.1313 | 9.3240 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p1__seed_2026 | additive_noise | ppg | 0.10 | 2026 | 4476/4476 | 1.000000 | 5.4851 | 7.9692 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p1__seed_2027 | additive_noise | ppg | 0.10 | 2027 | 4476/4476 | 1.000000 | 5.4497 | 7.9245 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p1__seed_2028 | additive_noise | ppg | 0.10 | 2028 | 4476/4476 | 1.000000 | 5.5117 | 8.0123 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p1__seed_2029 | additive_noise | ppg | 0.10 | 2029 | 4476/4476 | 1.000000 | 5.4564 | 7.9104 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p1__seed_2030 | additive_noise | ppg | 0.10 | 2030 | 4476/4476 | 1.000000 | 5.4426 | 7.8861 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p25__seed_2026 | additive_noise | ppg | 0.25 | 2026 | 4476/4476 | 1.000000 | 9.5996 | 13.4014 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p25__seed_2027 | additive_noise | ppg | 0.25 | 2027 | 4476/4476 | 1.000000 | 9.5440 | 13.2211 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p25__seed_2028 | additive_noise | ppg | 0.25 | 2028 | 4476/4476 | 1.000000 | 9.8874 | 13.7015 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p25__seed_2029 | additive_noise | ppg | 0.25 | 2029 | 4476/4476 | 1.000000 | 9.6718 | 13.4045 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p25__seed_2030 | additive_noise | ppg | 0.25 | 2030 | 4476/4476 | 1.000000 | 9.5023 | 13.2733 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p5__seed_2026 | additive_noise | ppg | 0.50 | 2026 | 4476/4476 | 1.000000 | 12.4772 | 16.4237 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p5__seed_2027 | additive_noise | ppg | 0.50 | 2027 | 4476/4476 | 1.000000 | 12.4100 | 16.0627 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p5__seed_2028 | additive_noise | ppg | 0.50 | 2028 | 4476/4476 | 1.000000 | 12.7848 | 16.6629 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p5__seed_2029 | additive_noise | ppg | 0.50 | 2029 | 4476/4476 | 1.000000 | 12.5717 | 16.4153 | 0 | 0 | 0 |
| additive_noise__ppg__severity_0p5__seed_2030 | additive_noise | ppg | 0.50 | 2030 | 4476/4476 | 1.000000 | 12.3586 | 16.2435 | 0 | 0 | 0 |
| additive_noise__ppg__severity_1__seed_2026 | additive_noise | ppg | 1.00 | 2026 | 4476/4476 | 1.000000 | 13.6766 | 17.8066 | 0 | 0 | 0 |
| additive_noise__ppg__severity_1__seed_2027 | additive_noise | ppg | 1.00 | 2027 | 4476/4476 | 1.000000 | 13.4993 | 17.3393 | 0 | 0 | 0 |
| additive_noise__ppg__severity_1__seed_2028 | additive_noise | ppg | 1.00 | 2028 | 4476/4476 | 1.000000 | 13.7784 | 17.7134 | 0 | 0 | 0 |
| additive_noise__ppg__severity_1__seed_2029 | additive_noise | ppg | 1.00 | 2029 | 4476/4476 | 1.000000 | 13.6758 | 17.6654 | 0 | 0 | 0 |
| additive_noise__ppg__severity_1__seed_2030 | additive_noise | ppg | 1.00 | 2030 | 4476/4476 | 1.000000 | 13.5034 | 17.5350 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p1__seed_2026 | additive_noise | imu | 0.10 | 2026 | 4476/4476 | 1.000000 | 5.0977 | 7.5033 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p1__seed_2027 | additive_noise | imu | 0.10 | 2027 | 4476/4476 | 1.000000 | 5.0879 | 7.4901 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p1__seed_2028 | additive_noise | imu | 0.10 | 2028 | 4476/4476 | 1.000000 | 5.1038 | 7.5021 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p1__seed_2029 | additive_noise | imu | 0.10 | 2029 | 4476/4476 | 1.000000 | 5.0897 | 7.4955 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p1__seed_2030 | additive_noise | imu | 0.10 | 2030 | 4476/4476 | 1.000000 | 5.0973 | 7.4994 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p25__seed_2026 | additive_noise | imu | 0.25 | 2026 | 4476/4476 | 1.000000 | 5.0956 | 7.5100 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p25__seed_2027 | additive_noise | imu | 0.25 | 2027 | 4476/4476 | 1.000000 | 5.0783 | 7.4817 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p25__seed_2028 | additive_noise | imu | 0.25 | 2028 | 4476/4476 | 1.000000 | 5.0995 | 7.4994 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p25__seed_2029 | additive_noise | imu | 0.25 | 2029 | 4476/4476 | 1.000000 | 5.0844 | 7.4956 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p25__seed_2030 | additive_noise | imu | 0.25 | 2030 | 4476/4476 | 1.000000 | 5.0912 | 7.4966 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p5__seed_2026 | additive_noise | imu | 0.50 | 2026 | 4476/4476 | 1.000000 | 5.0992 | 7.5214 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p5__seed_2027 | additive_noise | imu | 0.50 | 2027 | 4476/4476 | 1.000000 | 5.0755 | 7.4761 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p5__seed_2028 | additive_noise | imu | 0.50 | 2028 | 4476/4476 | 1.000000 | 5.0943 | 7.4932 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p5__seed_2029 | additive_noise | imu | 0.50 | 2029 | 4476/4476 | 1.000000 | 5.0840 | 7.5029 | 0 | 0 | 0 |
| additive_noise__imu__severity_0p5__seed_2030 | additive_noise | imu | 0.50 | 2030 | 4476/4476 | 1.000000 | 5.0862 | 7.4884 | 0 | 0 | 0 |
| additive_noise__imu__severity_1__seed_2026 | additive_noise | imu | 1.00 | 2026 | 4476/4476 | 1.000000 | 5.1069 | 7.5368 | 0 | 0 | 0 |
| additive_noise__imu__severity_1__seed_2027 | additive_noise | imu | 1.00 | 2027 | 4476/4476 | 1.000000 | 5.0724 | 7.4601 | 0 | 0 | 0 |
| additive_noise__imu__severity_1__seed_2028 | additive_noise | imu | 1.00 | 2028 | 4476/4476 | 1.000000 | 5.0934 | 7.4904 | 0 | 0 | 0 |
| additive_noise__imu__severity_1__seed_2029 | additive_noise | imu | 1.00 | 2029 | 4476/4476 | 1.000000 | 5.0915 | 7.5002 | 0 | 0 | 0 |
| additive_noise__imu__severity_1__seed_2030 | additive_noise | imu | 1.00 | 2030 | 4476/4476 | 1.000000 | 5.0814 | 7.4802 | 0 | 0 | 0 |
| saturation__ppg__severity_0p1 | saturation | ppg | 0.10 | N/A | 4476/4476 | 1.000000 | 7.0341 | 11.3064 | 0 | 0 | 0 |
| saturation__ppg__severity_0p25 | saturation | ppg | 0.25 | N/A | 4476/4476 | 1.000000 | 7.4223 | 11.9401 | 0 | 0 | 0 |
| saturation__ppg__severity_0p5 | saturation | ppg | 0.50 | N/A | 4476/4476 | 1.000000 | 8.1830 | 12.9571 | 0 | 0 | 0 |
| saturation__ppg__severity_1 | saturation | ppg | 1.00 | N/A | 0/4476 | 0.000000 | N/A | N/A | 0 | 4476 | 0 |
| saturation__imu__severity_0p1 | saturation | imu | 0.10 | N/A | 4476/4476 | 1.000000 | 6.1661 | 9.9817 | 0 | 0 | 0 |
| saturation__imu__severity_0p25 | saturation | imu | 0.25 | N/A | 4476/4476 | 1.000000 | 6.1621 | 9.9661 | 0 | 0 | 0 |
| saturation__imu__severity_0p5 | saturation | imu | 0.50 | N/A | 4476/4476 | 1.000000 | 6.1475 | 9.9182 | 0 | 0 | 0 |
| saturation__imu__severity_1 | saturation | imu | 1.00 | N/A | 4476/4476 | 1.000000 | 6.1313 | 9.3240 | 0 | 0 | 0 |
| packet_loss__ppg__severity_0p01__seed_2026 | packet_loss | ppg | 0.01 | 2026 | 30/4476 | 0.006702 | 4.9161 | 7.0796 | 0 | 0 | 4446 |
| packet_loss__ppg__severity_0p01__seed_2027 | packet_loss | ppg | 0.01 | 2027 | 31/4476 | 0.006926 | 7.1908 | 9.3925 | 0 | 0 | 4445 |
| packet_loss__ppg__severity_0p01__seed_2028 | packet_loss | ppg | 0.01 | 2028 | 12/4476 | 0.002681 | 5.2176 | 6.9197 | 0 | 0 | 4464 |
| packet_loss__ppg__severity_0p01__seed_2029 | packet_loss | ppg | 0.01 | 2029 | 23/4476 | 0.005139 | 4.4414 | 6.8783 | 0 | 0 | 4453 |
| packet_loss__ppg__severity_0p01__seed_2030 | packet_loss | ppg | 0.01 | 2030 | 25/4476 | 0.005585 | 5.9833 | 8.6136 | 0 | 0 | 4451 |
| packet_loss__ppg__severity_0p05__seed_2026 | packet_loss | ppg | 0.05 | 2026 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__ppg__severity_0p05__seed_2027 | packet_loss | ppg | 0.05 | 2027 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__ppg__severity_0p05__seed_2028 | packet_loss | ppg | 0.05 | 2028 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__ppg__severity_0p05__seed_2029 | packet_loss | ppg | 0.05 | 2029 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__ppg__severity_0p05__seed_2030 | packet_loss | ppg | 0.05 | 2030 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__ppg__severity_0p1__seed_2026 | packet_loss | ppg | 0.10 | 2026 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__ppg__severity_0p1__seed_2027 | packet_loss | ppg | 0.10 | 2027 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__ppg__severity_0p1__seed_2028 | packet_loss | ppg | 0.10 | 2028 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__ppg__severity_0p1__seed_2029 | packet_loss | ppg | 0.10 | 2029 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__ppg__severity_0p1__seed_2030 | packet_loss | ppg | 0.10 | 2030 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__ppg__severity_0p2__seed_2026 | packet_loss | ppg | 0.20 | 2026 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__ppg__severity_0p2__seed_2027 | packet_loss | ppg | 0.20 | 2027 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__ppg__severity_0p2__seed_2028 | packet_loss | ppg | 0.20 | 2028 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__ppg__severity_0p2__seed_2029 | packet_loss | ppg | 0.20 | 2029 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__ppg__severity_0p2__seed_2030 | packet_loss | ppg | 0.20 | 2030 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__imu__severity_0p01__seed_2026 | packet_loss | imu | 0.01 | 2026 | 337/4476 | 0.075290 | 5.1284 | 7.0609 | 0 | 0 | 4139 |
| packet_loss__imu__severity_0p01__seed_2027 | packet_loss | imu | 0.01 | 2027 | 315/4476 | 0.070375 | 4.9533 | 7.2278 | 0 | 0 | 4161 |
| packet_loss__imu__severity_0p01__seed_2028 | packet_loss | imu | 0.01 | 2028 | 386/4476 | 0.086238 | 5.0465 | 7.4553 | 0 | 0 | 4090 |
| packet_loss__imu__severity_0p01__seed_2029 | packet_loss | imu | 0.01 | 2029 | 289/4476 | 0.064567 | 5.1079 | 7.5941 | 0 | 0 | 4187 |
| packet_loss__imu__severity_0p01__seed_2030 | packet_loss | imu | 0.01 | 2030 | 294/4476 | 0.065684 | 5.4065 | 8.0496 | 0 | 0 | 4182 |
| packet_loss__imu__severity_0p05__seed_2026 | packet_loss | imu | 0.05 | 2026 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__imu__severity_0p05__seed_2027 | packet_loss | imu | 0.05 | 2027 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__imu__severity_0p05__seed_2028 | packet_loss | imu | 0.05 | 2028 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__imu__severity_0p05__seed_2029 | packet_loss | imu | 0.05 | 2029 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__imu__severity_0p05__seed_2030 | packet_loss | imu | 0.05 | 2030 | 1/4476 | 0.000223 | 2.1158 | 2.1158 | 0 | 0 | 4475 |
| packet_loss__imu__severity_0p1__seed_2026 | packet_loss | imu | 0.10 | 2026 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__imu__severity_0p1__seed_2027 | packet_loss | imu | 0.10 | 2027 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__imu__severity_0p1__seed_2028 | packet_loss | imu | 0.10 | 2028 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__imu__severity_0p1__seed_2029 | packet_loss | imu | 0.10 | 2029 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__imu__severity_0p1__seed_2030 | packet_loss | imu | 0.10 | 2030 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__imu__severity_0p2__seed_2026 | packet_loss | imu | 0.20 | 2026 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__imu__severity_0p2__seed_2027 | packet_loss | imu | 0.20 | 2027 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__imu__severity_0p2__seed_2028 | packet_loss | imu | 0.20 | 2028 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__imu__severity_0p2__seed_2029 | packet_loss | imu | 0.20 | 2029 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__imu__severity_0p2__seed_2030 | packet_loss | imu | 0.20 | 2030 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p01__seed_2026 | packet_loss | both | 0.01 | 2026 | 4/4476 | 0.000894 | 3.8603 | 4.8437 | 0 | 0 | 4472 |
| packet_loss__both__severity_0p01__seed_2027 | packet_loss | both | 0.01 | 2027 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p01__seed_2028 | packet_loss | both | 0.01 | 2028 | 1/4476 | 0.000223 | 1.8675 | 1.8675 | 0 | 0 | 4475 |
| packet_loss__both__severity_0p01__seed_2029 | packet_loss | both | 0.01 | 2029 | 1/4476 | 0.000223 | 0.0863 | 0.0863 | 0 | 0 | 4475 |
| packet_loss__both__severity_0p01__seed_2030 | packet_loss | both | 0.01 | 2030 | 1/4476 | 0.000223 | 1.3719 | 1.3719 | 0 | 0 | 4475 |
| packet_loss__both__severity_0p05__seed_2026 | packet_loss | both | 0.05 | 2026 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p05__seed_2027 | packet_loss | both | 0.05 | 2027 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p05__seed_2028 | packet_loss | both | 0.05 | 2028 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p05__seed_2029 | packet_loss | both | 0.05 | 2029 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p05__seed_2030 | packet_loss | both | 0.05 | 2030 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p1__seed_2026 | packet_loss | both | 0.10 | 2026 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p1__seed_2027 | packet_loss | both | 0.10 | 2027 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p1__seed_2028 | packet_loss | both | 0.10 | 2028 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p1__seed_2029 | packet_loss | both | 0.10 | 2029 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p1__seed_2030 | packet_loss | both | 0.10 | 2030 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p2__seed_2026 | packet_loss | both | 0.20 | 2026 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p2__seed_2027 | packet_loss | both | 0.20 | 2027 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p2__seed_2028 | packet_loss | both | 0.20 | 2028 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p2__seed_2029 | packet_loss | both | 0.20 | 2029 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |
| packet_loss__both__severity_0p2__seed_2030 | packet_loss | both | 0.20 | 2030 | 0/4476 | 0.000000 | N/A | N/A | 0 | 0 | 4476 |

## Stochastic five-seed aggregates

Values are mean ± population standard deviation across seeds 2026-2030. N/A means the metric was undefined for at least one seed because no valid prediction existed.

| Group | Availability | MAE bpm | RMSE bpm | Valid count |
|---|---:|---:|---:|---:|
| additive_noise__ppg__severity_0p1 | 1.0000 ± 0.0000 | 5.4691 ± 0.0257 | 7.9405 ± 0.0450 | 4476.0000 ± 0.0000 |
| additive_noise__ppg__severity_0p25 | 1.0000 ± 0.0000 | 9.6410 ± 0.1357 | 13.4004 ± 0.1667 | 4476.0000 ± 0.0000 |
| additive_noise__ppg__severity_0p5 | 1.0000 ± 0.0000 | 12.5205 ± 0.1502 | 16.3616 ± 0.2004 | 4476.0000 ± 0.0000 |
| additive_noise__ppg__severity_1 | 1.0000 ± 0.0000 | 13.6267 ± 0.1089 | 17.6120 ± 0.1620 | 4476.0000 ± 0.0000 |
| additive_noise__imu__severity_0p1 | 1.0000 ± 0.0000 | 5.0953 ± 0.0058 | 7.4981 ± 0.0048 | 4476.0000 ± 0.0000 |
| additive_noise__imu__severity_0p25 | 1.0000 ± 0.0000 | 5.0898 ± 0.0076 | 7.4967 ± 0.0091 | 4476.0000 ± 0.0000 |
| additive_noise__imu__severity_0p5 | 1.0000 ± 0.0000 | 5.0878 ± 0.0083 | 7.4964 ± 0.0152 | 4476.0000 ± 0.0000 |
| additive_noise__imu__severity_1 | 1.0000 ± 0.0000 | 5.0891 ± 0.0117 | 7.4935 ± 0.0254 | 4476.0000 ± 0.0000 |
| packet_loss__ppg__severity_0p01 | 0.0054 ± 0.0015 | 5.5498 ± 0.9614 | 7.7767 ± 1.0333 | 24.2000 ± 6.7941 |
| packet_loss__ppg__severity_0p05 | 0.0000 ± 0.0000 | N/A (0/5 defined) | N/A (0/5 defined) | 0.0000 ± 0.0000 |
| packet_loss__ppg__severity_0p1 | 0.0000 ± 0.0000 | N/A (0/5 defined) | N/A (0/5 defined) | 0.0000 ± 0.0000 |
| packet_loss__ppg__severity_0p2 | 0.0000 ± 0.0000 | N/A (0/5 defined) | N/A (0/5 defined) | 0.0000 ± 0.0000 |
| packet_loss__imu__severity_0p01 | 0.0724 ± 0.0079 | 5.1285 ± 0.1517 | 7.4775 ± 0.3398 | 324.2000 ± 35.2670 |
| packet_loss__imu__severity_0p05 | 0.0000 ± 0.0001 | N/A (1/5 defined) | N/A (1/5 defined) | 0.2000 ± 0.4000 |
| packet_loss__imu__severity_0p1 | 0.0000 ± 0.0000 | N/A (0/5 defined) | N/A (0/5 defined) | 0.0000 ± 0.0000 |
| packet_loss__imu__severity_0p2 | 0.0000 ± 0.0000 | N/A (0/5 defined) | N/A (0/5 defined) | 0.0000 ± 0.0000 |
| packet_loss__both__severity_0p01 | 0.0003 ± 0.0003 | N/A (4/5 defined) | N/A (4/5 defined) | 1.4000 ± 1.3565 |
| packet_loss__both__severity_0p05 | 0.0000 ± 0.0000 | N/A (0/5 defined) | N/A (0/5 defined) | 0.0000 ± 0.0000 |
| packet_loss__both__severity_0p1 | 0.0000 ± 0.0000 | N/A (0/5 defined) | N/A (0/5 defined) | 0.0000 ± 0.0000 |
| packet_loss__both__severity_0p2 | 0.0000 ± 0.0000 | N/A (0/5 defined) | N/A (0/5 defined) | 0.0000 ± 0.0000 |

## Interpretation limits

Accuracy changes and availability collapse are reported separately. Explicit rejection is not called an accuracy failure, and continued output is not evidence of fault detection. No retraining, output clipping, interpolation, missing-modality fill, fallback HR, or predictive uncertainty was introduced.

These results support only an observation of this frozen pipeline on official held-out S14 under the pre-registered corruptions. They do not establish population-level robustness, fault tolerance, calibrated uncertainty, microgravity performance, or astronaut readiness.
