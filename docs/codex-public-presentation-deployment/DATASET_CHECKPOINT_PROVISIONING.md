# Dataset and checkpoint provisioning

## Provenance

- Dataset: PPG-DaLiA, UCI DOI `10.24432/C53890`, CC BY 4.0.
- Official 2.7 GB UCI archive SHA-256: `5772387956e34e2e2dc4c2ddbeb98cb70569d5112fa4c13ee98a17680b84a1f3`.
- Original `S14.pkl` SHA-256: `c192b9090ac3c0107000d8424c038ccd11292cded1f6c46c97e2cae85c725392`.
- Backend-only S14 deployment archive SHA-256: `3e4499a0ad6eb024dfd39b2ec53c5739f2d25bced51d22ac55da332271444c03`.
- Accepted Model B checkpoint SHA-256: `c53a34586d2d6baf68aae4441b6c15a0f5f623f0ea70c023c7371c2dbded0e77`.

The deployment archive is 105 MB compressed and contains the original synchronized S14 pickle plus CC BY attribution. Neither asset is tracked by Git or served publicly. After owner approval, both are uploaded through the authenticated Render backend shell to the private persistent disk and hashes are rechecked before startup.
