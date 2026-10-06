# Dataset and checkpoint provisioning

## Provenance

- Dataset: PPG-DaLiA, UCI DOI `10.24432/C53890`, CC BY 4.0.
- Official 2.7 GB UCI archive SHA-256: `5772387956e34e2e2dc4c2ddbeb98cb70569d5112fa4c13ee98a17680b84a1f3`.
- Original `S14.pkl` SHA-256: `c192b9090ac3c0107000d8424c038ccd11292cded1f6c46c97e2cae85c725392`.
- Initial original-pickle S14 deployment archive SHA-256: `3e4499a0ad6eb024dfd39b2ec53c5739f2d25bced51d22ac55da332271444c03`.
- Free-tier exact-channel S14 bundle SHA-256: `e5f4fc0cb0722f98d1c86e499d1c0f49e7bfa4048a909f017df65978842821a5` (19,058,604 bytes).
- Accepted Model B checkpoint SHA-256: `c53a34586d2d6baf68aae4441b6c15a0f5f623f0ea70c023c7371c2dbded0e77`.

The free-tier bundle retains the exact BVP, wrist ACC, chest ECG, and wrist temperature arrays consumed by the accepted application. It performs no resampling, filtering, conversion, or value change. Its embedded derivation manifest records the official source-pickle hash plus every selected array's path, shape, dtype, and SHA-256; CC BY attribution is embedded alongside it.

Neither asset is tracked by Git or served publicly. Both are stored as release assets in a separately access-controlled private GitHub repository. Render receives only a server-side read credential and private API URLs. On every cold start, the ephemeral backend downloads each asset over HTTPS, strips the credential before any cross-host signed redirect, verifies the complete SHA-256, and fails closed before accepting traffic if any step disagrees.
