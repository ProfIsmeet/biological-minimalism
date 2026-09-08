# Hash Provenance Policy (audit M2 / §21–§22)

One shared, explicit policy for every SHA-256 used as provenance in this
repository. It exists because `core.autocrlf=true` means a Windows checkout of a
**text** file has CRLF line endings on disk while the frozen constants were
computed against LF-normalized content — hashing raw bytes produced false
mismatches on Windows for byte-identical content.

## The two hash classes

| Class | Applies to | Definition | Field name to prefer |
|---|---|---|---|
| **Binary raw hash** | model checkpoints (`.pt`), datasets (`.edf/.pkl/.npz`), any non-text artifact | `sha256(path.read_bytes())` — raw bytes, no normalization | `raw_sha256` |
| **Canonical text hash** | committed JSON/text artifacts used in provenance joins (contracts, decision-input catalogs, protocol/config text) | `sha256(path.read_bytes().replace(b"\r\n", b"\n"))` — LF-normalized | `canonical_text_sha256` |
| **Git blob id** (optional) | when cross-checking against git object identity | `git hash-object` (SHA-1 blob) | `git_blob_id` |

Rules:

1. **Binary artifacts are hashed raw.** They contain no `\r\n` sequences to
   normalize, so raw-byte hashing is stable across platforms. All checkpoint
   builders/verifiers and the dataset-fingerprint manifest use this.
2. **Canonical text artifacts are hashed LF-normalized.** This is the only
   platform-stable way to hash a `core.autocrlf` text file. Implemented
   identically in `ml/build_sensor_marginal_value_contract.py::_sha256` and
   `backend/app/research/decision_inputs.py::_sha256`.
3. **Never conflate the two under a bare `sha256` name in NEW fields.** Existing
   stored fields historically named `sha256` follow the per-layer convention
   above (checkpoint manifests = raw; contract/decision-input text joins =
   canonical text). Renaming those historical fields would cascade the frozen
   provenance SHA chain and is intentionally NOT done here; this document is the
   authoritative disambiguation for them. New provenance fields SHOULD use the
   typed names in the table.

## Verification

`ml/tests/test_hash_provenance_policy.py` proves:

- the canonical text hash is CRLF/LF-invariant (same digest for `\n` and
  `\r\n` content), while the raw hash is not;
- the two independent canonical-text implementations agree;
- a binary blob's raw hash is unaffected by (absent) CRLF handling.

## Do NOT

- Do not rebuild caches or re-freeze SHAs to "unify" field names — that breaks
  reproduction against externally archived checkpoints.
- Do not hash a text artifact raw in a new provenance path; use the canonical
  text hash so Windows and macOS/Linux agree.
