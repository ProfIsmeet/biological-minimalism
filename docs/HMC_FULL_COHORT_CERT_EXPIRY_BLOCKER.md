# HMC Full-Cohort Download — Blocked by a Genuine PhysioNet TLS Certificate Expiry

**This is a fresh, real, external infrastructure event, verified directly
— not a local issue, not a permissions/access issue, and NOT bypassed.**

## What happened

The full 151-recording HMC download (`datasets/hmc-sleep-staging/
download_full_cohort.sh`, launched this sprint) succeeded for the first 8
recordings (SHA256-verified against PhysioNet's own `SHA256SUMS.txt`), then
began failing with `curl: (35) schannel: ... SEC_E_CERT_EXPIRED` on every
subsequent request.

## Independent verification (not assumed from the curl error alone)

```
$ echo | openssl s_client -connect physionet.org:443 -servername physionet.org | openssl x509 -noout -dates
notBefore=Jun 11 20:22:46 2026 GMT
notAfter=Sep  9 20:22:45 2026 GMT
```

`date -u` at the time of the first failure showed `Wed Sep 9 20:32:49 2026
UTC` — **10 minutes past the certificate's own `notAfter` date.**
PhysioNet's real TLS certificate for `physionet.org` genuinely expired
during this session (not a local clock skew — the session's own UTC clock
and the certificate's stated validity window were checked directly). A
recheck a few seconds later showed the same result — not yet rotated.

## What was NOT done

**No `-k`/`--insecure` flag or any other certificate-validation bypass was
used or considered a real option.** Disabling TLS verification to route
around an expired certificate is a security anti-pattern and is not an
acceptable workaround for a legitimate infrastructure issue, regardless of
how much it would "unblock" — this is treated the same as any other
access control that must not be bypassed.

## Real partial result available

**8 of 151 recordings** were downloaded and SHA256-verified before the
certificate expired (real files, real hashes, genuinely on disk:
`datasets/hmc-sleep-staging/raw/`, 867 MB). This is a smaller real subset
than the intended full cohort, and smaller even than Claude's earlier
12-recording pilot — it is used only for a further-bounded pipeline
diagnostic (see `results/hmc_bounded_diagnostic_n8.json` if produced this
sprint), never presented as the canonical full-151 HMC replication result.

## Status

`HMC_FULL_COHORT_BLOCKED_BY_EXTERNAL_CERT_EXPIRY` — genuinely blocked by an
external event, not a design, protocol, or data-access-permission issue.
Full-cohort download should be retried once PhysioNet's certificate is
rotated (typically hours to a few days for a routine Let's Encrypt/similar
renewal cycle, though the exact timeline is outside this project's
knowledge or control).
