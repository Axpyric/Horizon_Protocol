# Hakumadi — Architecture (execution model)

This document captures the event-driven execution model for Hakumadi v0.1.0. It intentionally mirrors the SPECIFICATION execution steps and restricts acceptance logic to deterministic validation and validator attestations.

Execution steps

1. CREATE — Producer emits manifest and produces asset blob
2. SIGN — Creator signs manifest (signature embedded)
3. SUBMIT — Envelope containing manifest is submitted to ingestion endpoint
4. VALIDATE — Deterministic checks (schema, signature, digest integrity)
5. ATTEST — Validator operators optionally produce attestations (signatures over manifest_hash)
6. CONSENSUS CHECK — If validator attestations >= configured threshold N, proceed
7. FINALIZE — Registry writes canonical record and returns acknowledgement
8. ARCHIVE — persist submitted envelope, attestations, and canonical record for audit

Consensus model (v0.1.0)
- Validator model: set of known validators (M)
- Threshold: N (1 <= N <= M) required attestations
- No economic incentives or slashing in v0.1.0

