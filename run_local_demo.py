#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import os, json
from signing.ed25519_local import Ed25519LocalProvider
from fingerprint_engine import build_fingerprint_record
from envelope import Envelope
from registrar.registry import RegistryManager
from registry_ingest import RegistryIngestor
from pathlib import Path

def ensure_examples():
    Path("examples/layers").mkdir(parents=True, exist_ok=True)
    if not Path("examples/layers/cadence.json").exists():
        Path("examples/layers/cadence.json").write_text(json.dumps({"version":"1.0.0","data":{"bpm":92,"key":"F_minor"}}))
    if not Path("examples/layers/structure.json").exists():
        Path("examples/layers/structure.json").write_text(json.dumps({"version":"1.0.0","data":{"sections":["intro","verse","chorus"]}}))
    if not Path("examples/manifest.json").exists():
        Path("examples/manifest.json").write_text(json.dumps({"origin_manifest":"vault/fingerprints/asset-alpha/manifest.json","layers":{"cadence":{"path":"examples/layers/cadence.json"},"structure":{"path":"examples/layers/structure.json"}}}))
    Path("daemon/out").mkdir(parents=True, exist_ok=True)
    Path("canon").mkdir(parents=True, exist_ok=True)

def main():
    ensure_examples()
    print("Make sure you've created an encrypted key with: python signing/generate_key.py")
    key_path = "keys/private_ed25519.enc"
    if not Path(key_path).exists():
        raise SystemExit("Encrypted key not found; run signing/generate_key.py first.")
    provider = Ed25519LocalProvider(key_path)
    print("Provider created; will prompt to unlock on first use.")

    deterministic_record, meta = build_fingerprint_record("examples/manifest.json", engine_version="1.0.0")
    asset_id = deterministic_record["record_id"]

    # Build envelope and sign with provider (simulate external submitter)
    env = Envelope(record=deterministic_record, metadata=meta)
    sig = provider.sign(env.canonical_bytes())
    env.attach_signature(sig)
    outp = Path("daemon/out") / f"external-{asset_id.replace('sha256:','')[:8]}.json"
    outp.write_text(env.to_json(), encoding="utf-8")
    print("Wrote signed envelope to", outp)

    rm = RegistryManager()
    ingestor = RegistryIngestor(registry_manager=rm)

    # Try to ingest via the safe upsert path
    try:
        result = ingestor.ingest(deterministic_record, source="external-demo")
        print("Ingest result:", json.dumps(result, indent=2))
    except Exception as e:
        print("Ingest raised an exception:", str(e))
        # Defensive fallback: try to upsert directly into registry
        try:
            stored = rm.upsert_node({
                "asset_id": asset_id,
                "origin_manifest": deterministic_record.get("origin_manifest"),
                "engine_version": deterministic_record.get("engine_version"),
                "fingerprint_record": deterministic_record,
                "ingestion": {"source": "external-demo-retry", "ingested_at": __import__("datetime").datetime.utcnow().isoformat()+"Z"}
            })
            print("Upserted node as fallback. Registry updated.")
            print(json.dumps({"asset_id": asset_id, "_registry": stored.get("_registry")}, indent=2))
        except Exception as e2:
            print("Fallback upsert failed:", str(e2))

    node = rm.get_node(asset_id)
    if node:
        print("Stored node summary (trust/status):")
        print(json.dumps({"asset_id": node.get("asset_id"), "status": node.get("status"), "trust_score": node.get("trust", {}).get("score")}, indent=2))
    else:
        print("No node found after ingest attempt.")

if __name__ == "__main__":
    main()
