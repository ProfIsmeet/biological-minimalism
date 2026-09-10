# HMC Full-Cohort Access — Certificate Renewed, Download Resumed

**Real, positive finding this sprint**: PhysioNet's TLS certificate has
been rotated since the prior sprint's blocker.

```
$ echo | openssl s_client -connect physionet.org:443 -servername physionet.org | openssl x509 -noout -dates
notBefore=Sep 10 00:51:10 2026 GMT
notAfter=Dec  9 00:51:09 2026 GMT
```

Real HTTP 200 confirmed against a real HMC file. **Status upgraded from
`HMC_FULL_COHORT_EXTERNAL_ACCESS_BLOCKED` to `HMC_FULL_COHORT_ACCESS_RESTORED`.**

The full 151-recording download (`datasets/hmc-sleep-staging/
download_full_cohort.sh`, same script used in the prior sprint, which
skips the 8 recordings already downloaded and SHA256-verified before the
prior expiry) was resumed this sprint. See
`results/hmc_full_cohort_download_progress_stage3.json` (written once the
download completes or this sprint's session time runs out) for the exact
achieved count.
