# Hakumadi — Whitepaper (Concise)

Executive summary

Hakumadi is an open protocol for cryptographically verifiable creative provenance. It provides a minimal, interoperable set of schemas and flows so creators can publish manifests that describe creative assets, sign them cryptographically, and allow registries and third parties to compute trust and provenance.

The problem

Creators and downstream consumers (platforms, publishers, auditors) need reliable provenance for creative works. Current approaches are fragmented, ad-hoc, and often rely on centralized platforms that mix metadata and rights. A protocol-level approach enables interoperability and auditability.

Approach

- Define a compact, canonical manifest format.
- Define deterministic fingerprinting for manifests and layers.
- Use envelopes to carry payloads and signatures.
- Provide idempotent ingestion and a registry model to record canonical nodes.
- Provide reconciliation and trust scoring to detect divergence and provide deterministic, auditable interpretations.

Core protocol pieces (recap)

- Manifest v1 (schema)
- Fingerprint record v1
- Envelope v1 (payload + signatures)
- Registry upsert semantics
- Reconciliation & Trust Scoring

Roadmap (near term)

- v0.1: reference implementation and protocol docs (this release)
- v0.2: signature verification flows, key discovery, and attestation pooling
- v1.0: interop tests, reference implementations in multiple languages, governance baseline

Governance & openness

- Hakumadi is intended as an open protocol. Governance for schema changes should be lightweight at first (maintainers + steering), migrating to a more open process as the protocol matures.

Economics & tokens

- Not included in v0.1. The protocol is neutral to token models and can support optional economic overlays later.

Security and privacy

- Keys: support encrypted private keys and rotation. Provide revocation and key discovery mechanisms.
- Data minimization: registries should store only necessary fingerprints and metadata, not raw asset content unless explicitly requested.

Conclusion

Hakumadi is positioned as a minimal, pragmatic protocol to bootstrap cryptographic provenance for creative works. Start with a core set of stable semantics (manifests, fingerprints, envelopes), prove interoperability with reference implementations, and iterate on trust, attestation, and governance.

