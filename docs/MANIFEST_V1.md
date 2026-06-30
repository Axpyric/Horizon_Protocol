# Manifest v1 — Field Specification

This document defines the Manifest v1 schema and semantics. Implementations should validate manifests against this schema and follow the canonicalization rules described in SPECIFICATION.md.

Top-level fields

- manifest_version (string) — e.g. "manifest_v1"
- manifest_id (string) — deterministic identifier (sha256:... of canonical manifest bytes)
- origin_manifest (string) — human or machine pointer to the canonical origin (URI, path)
- created_at (string, RFC3339 UTC)
- author (object)
  - id (string) — opaque identity (pref: key-derived id or DID)
  - name (string) — human readable
  - contact (string, optional)
- description (string, optional)
- layers (object) — map of layer_key -> layer_descriptor

Layer descriptor

Each layer descriptor is an object with fields:
- path (string) — relative path to layer file referenced by the manifest
- version (string, optional)
- metadata (object, optional)

Example manifest

{
  "manifest_version": "manifest_v1",
  "manifest_id": "sha256:...",
  "origin_manifest": "vault/fingerprints/asset-alpha/manifest.json",
  "created_at": "2026-06-30T12:00:00Z",
  "author": { "id": "axpyric:pk:...", "name": "Eric Wesley Axelton" },
  "layers": {
    "cadence": { "path": "layers/cadence.json", "version":"1.0.0" },
    "structure": { "path": "layers/structure.json" }
  }
}

Semantics

- manifest_id MUST be computed by canonicalizing the manifest JSON and hashing with sha256. Consumers MUST verify manifest_id corresponds to the canonical hash.
- Layers referenced by path MUST be included or published together with the manifest to enable fingerprinting.
- Tool disclosures SHOULD be included in layer metadata when third-party tools contributed to generation.

