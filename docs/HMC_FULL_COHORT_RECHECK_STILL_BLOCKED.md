# HMC Full-Cohort Access — One Controlled Recheck, Still Blocked

Per Section 101 (one controlled recheck, do not burn the sprint retrying),
a single recheck was performed this sprint:

```
$ echo | openssl s_client -connect physionet.org:443 -servername physionet.org | openssl x509 -noout -dates
notBefore=Jun 11 20:22:46 2026 GMT
notAfter=Sep  9 20:22:45 2026 GMT
```

Same expired certificate as the prior sprint — PhysioNet has not yet
rotated it. `curl` to a real HMC file still fails with
`SEC_E_CERT_EXPIRED`. **No TLS bypass was used.**

**Status: `HMC_FULL_COHORT_EXTERNAL_ACCESS_BLOCKED`** (unchanged from the
prior sprint). The n=7 bounded diagnostic
(`results/hmc_sleep_external_replication_stage3_bounded_n7.json`) is
preserved unchanged as the best currently-available real evidence, and
this sprint moves on to GalaxyPPG/LBNP per the priority ordering.
