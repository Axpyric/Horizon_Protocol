# Hakumadi Protocol — Specification (v1)

This document is the canonical specification for the Hakumadi protocol. It is intended to be machine- and implementer-friendly: a reference that implementers, integrators, and auditors can rely on.

1. What Hakumadi is

Hakumadi is an open protocol for cryptographically verifiable creative provenance. It defines how creators publish machine-readable "manifests" that describe assets, how those manifests are deterministically fingerprinted, how manifests are signed and attested, and how a registry records canonical assertions about assets so that consumers and tooling can evaluate provenance and trust.

2. Design goals

- Creator ownership: creators retain control of provenance claims they make. 
- Cryptographic verification: metadata and provenance are signed and verifiable.
- Interoperability: the protocol defines stable schemas and clear semantics so multiple implementations can interoperate.
- Minimal trusted infrastructure: the registry is an auditable ledger (pluggable backends) and attestation/consensus layers are modular.
- Privacy by design: sensitive data is kept out of public records unless explicitly published.
- Tool neutrality: records may describe toolchains but the protocol does not enforce tool behaviour.

3. Manifest schema (overview)

- Manifest: a JSON document describing an asset and its associated layers. Each manifest MUST include at minimum:
  - manifest_version (string)
  - origin_manifest (string): canonical pointer or human-readable origin
  - manifest_id (string): deterministically derived identifier (e.g., sha256 of canonicalized manifest)
  - layers (object): keyed collection of layer descriptors, each with a path and optional metadata
  - created_at (timestamp)
  - author (object) {id, name, contact?}
  - evaluation_flags (optional array)

Deterministic canonicalization: manifest bytes MUST be canonicalized using JSON canonical form: sorted keys, separators=(',',':'), UTF-8, no trailing whitespace.

4. Cryptographic primitives

- Signing: Ed25519 is the default signing algorithm. Signatures are produced over the canonicalized manifest/envelope bytes.
- Key storage: protocol recommends encrypted private keys for local signing (scrypt + AES-GCM envelope example provided in reference implementation).
- Signatures are expressed as JSON objects: { method, keyid, value (base64), created_at }

5. Identity model

- Identity in Hakumadi is decentralized. An identity is an opaque identifier (e.g., DID, an email-hash, or a public-key-derived keyid).
- The protocol requires a keyid to be included in signatures and recommends including a verifiable public key in discoverable registries or keyservers for cross-checking.

6. Registry model

- The registry stores nodes keyed by asset_id. Each node contains the latest admitted fingerprint record, provenance metadata, revision metadata (revision number, created_at, updated_at), reconciliation reports, trust scores, and ingestion provenance.
- Upsert semantics: ingest operations MUST be idempotent. Implementations SHOULD use upsert with revision incrementing to prevent duplicate insertion errors.
- Backend agnostic: registry may be implemented using SQLite (demo), PostgreSQL, or an append-only ledger.

7. Attestation model

- Attestations are signed envelopes that carry fingerprint records and optional metadata. Envelopes include payload (record + metadata) and signatures array.
- Submitters sign enveloped canonical bytes and publish envelopes to an ingestion endpoint or shared attestation pool.

8. Consensus & canonicalization

- The protocol does not mandate a single consensus mechanism; it allows multiple approaches depending on deployment needs (centralized registry, federated attestation pools, or blockchain-based canonical ledgers).
- Implementations MUST document how canonical records are chosen when multiple attestations conflict (e.g., highest trust score, quorum attestations, operator policy).

9. Versioning

- The protocol must use explicit schema version strings for manifests, fingerprint records, and envelope formats (e.g., manifest_v1, fingerprint_record_1, envelope_v1).
- Implementations MUST refuse or validate variations from unknown schema versions until compatibility mappings exist.

10. Security assumptions & threat model

- Private keys may be compromised; therefore, ridge controls (key rotation, revocation lists, and re-issuance) MUST be supported by implementations.
- The registry is trusted to provide availability and accountable integrity; if ledger tampering is possible, higher trust assumptions must be used (append-only ledger, signed checkpoints, external auditors).

Appendix A: References and canonical forms
- JSON canonicalization: sorted keys, separators=(',',':'), ensure_ascii=false, UTF-8
- Recommended signature scheme: Ed25519
- Recommended KDF + encryption for private keys: scrypt + AES-GCM

---

Design Principles

1. Creator ownership
2. Cryptographic verification
3. Transparency
4. Interoperability
5. Privacy by design
6. Tool neutrality
7. Minimal centralization
