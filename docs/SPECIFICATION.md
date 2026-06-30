# Hakumadi Protocol — Specification (v1.0)

Status: v0.1.0 (protocol spine — locked)

This document is the canonical specification for Hakumadi v0.1.0. It encodes the protocol-level decisions and deterministic schemas required for interoperable implementations. v0.1.0 is intentionally narrow: it defines how manifests are created, signed, validated, attested, and finalized into canonical registry records.

1. Canonical Terms (single source of truth)

- Registry: system of record — the authoritative store of canonical records. (Not a blockchain; an operationally run system-of-record that may be backed by append-only storage.)
- Manifest: a signed creative metadata object produced by a creator describing an asset and its layers.
- Envelope: submitted payload carrying a manifest (and optional attachments) prior to validation.
- Attestation: a validator signature over a manifest_hash used as evidence for acceptance.
- Canonical Record: the finalized, accepted registry entry derived from a validated manifest and its attestations.
- Consensus: a rule-based acceptance threshold (e.g., N-of-M attestations) used to determine canonicalization.

2. Design principles (immutable for v0.1.0)

- Creator ownership
- Cryptographic verification
- Deterministic schemas
- Minimal trusted infrastructure
- Privacy-by-design
- Tool neutrality
- No economic or staking primitives in core

3. Manifest v1.0 — locked schema (summary)

Every Manifest v1.0 MUST be a UTF-8 JSON object canonicalized with sorted keys and separators (",", ":"). The required fields are explicitly enumerated below.

Top-level required fields

- protocol_version: "1.0" (string)
- manifest_hash: "sha256:<hex>" — SHA-256 of the canonicalized manifest JSON bytes
- asset_id: "sha256:<hex>" — SHA-256 of the asset binary or canonical asset blob
- creator_id: base64-encoded Ed25519 public key (or other explicit key identifier)
- creative_blueprint: object
- revision_chain: array of revision objects
- tool_disclosure: array of strings
- human_contribution_summary: object
- asset_hash: "sha256:<hex>" — same as asset_id or explicit asset digest
- signature: base64-encoded Ed25519 signature over manifest_hash

Creative blueprint (required)
- genre_tags: array of strings
- structure: array (ordered structural descriptors)
- toolchain: array of objects (tool name, version)
- ai_assistance: object { used: boolean, tools: [ { name, version, params? } ] }

Revision object (each entry in revision_chain)
- revision_id: uuid
- timestamp: iso8601 UTC
- change_type: enum { composition, mix, edit, arrangement }
- description: string

Human contribution summary
- percentage_estimate: number | null
- notes: string

Signature
- signature is required and MUST be an Ed25519 signature over the canonicalized manifest JSON bytes or the manifest_hash as an implementation choice (both are acceptable if documented). The signature field MUST include the key id or support deriving the key (creator_id).

4. Canonicalization rules

- JSON canonicalization: sort object keys lexicographically; use separators=(',',':'); do not emit insignificant whitespace; ensure UTF-8; ensure predictable numeric formatting.
- Where binary assets are referenced (asset_id / asset_hash), the digest MUST be computed over the canonical asset blob (platform must document what constitutes the canonical asset blob — e.g., raw PCM, normalized file, or an exported container).

5. Signing & identity

- Default signing algorithm: Ed25519. Implementations MAY support other algorithms but must label them in metadata.
- creator_id: SHOULD be the base64-encoded public key or a resolvable key identifier (DID or similar). For v0.1.0, the simplest interoperable form is the public key.
- Key rotation & revocation: out of scope for v0.1.0 but MUST be considered in v0.2 (revocation list, cross-references).

6. Execution model (event-driven state transitions)

1. CREATE — creator produces manifest and asset
2. SIGN — creator signs the manifest (signature included in manifest)
3. SUBMIT — an Envelope containing the manifest is submitted to the Registry ingestion endpoint
4. VALIDATE — deterministic checks are run:
   - schema validation (manifest v1.0)
   - signature verification (creator signature)
   - manifest_hash and asset_hash integrity checks
5. ATTEST — validators (operators) may produce attestations (validator signatures over manifest_hash)
6. CONSENSUS CHECK — Registry applies the configured consensus rule (e.g., N-of-M validator attestations) to determine acceptance
7. FINALIZE — once consensus satisfied, create Canonical Record and persist (with revision metadata)
8. ARCHIVE — retain immutable history of envelopes, attestations, and canonical records

Important: Trust scoring, heuristics, or AI-derived signals MAY be produced by auxiliary services but MUST NOT determine canonical acceptance in v0.1.0.

7. Consensus rule (v0.1.0)

- Acceptance rule: canonicalization occurs when a manifest receives >= N valid validator attestations. N is an operator-configured threshold. No staking, slashing, or economic primitives are defined in v0.1.0.

8. Registry model

- Upsert semantics: ingest MUST be idempotent. The Registry stores nodes keyed by asset_id and includes revision numbers, created_at, updated_at.
- Canonical Record fields: asset_id, manifest_hash, creator_id, attestations[], canonicalized_payload, revision, created_at, updated_at

9. Security & threat model (concise)

- Assume private keys can be compromised; provide clear rotation and reissuance paths in later versions.
- The Registry is a system-of-record; tamper-evidence (signed checkpoints, append-only storage) is recommended for deployments requiring auditability.

10. Versioning & extensibility

- All core schemas include explicit version strings.
- Backwards-incompatible changes require a new manifest protocol_version and a documented migration plan.

Appendix A — What is out of scope for v0.1.0
- Token economics, staking, slashing, reputation-based canonicalization, and ML-driven acceptance decisions.

Appendix B — Reference encodings
- Digests: sha256:<hex>
- Signatures: base64
- Public keys: base64-encoded raw Ed25519 public key


