# Manifest v1 — Locked Structure and JSON Schema mapping

This document defines Manifest v1 fields, their types, and strict validation expectations. Implementers MUST validate incoming manifests against the provided JSON Schema (schemas/manifest_v1.schema.json).

Key invariants
- manifest_hash MUST match the canonicalized manifest bytes
- asset_id/asset_hash MUST be provided and be a sha256 digest
- signature MUST verify against creator_id

See schemas/manifest_v1.schema.json for machine-readable schema.
