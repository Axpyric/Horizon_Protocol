#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import json, hashlib
from pathlib import Path
from datetime import datetime

def _canonical_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def _sha256_hex(obj):
    return hashlib.sha256(_canonical_bytes(obj)).hexdigest()

def build_fingerprint_record(manifest_path: str, engine_version: str = "1.0.0"):
    mp = Path(manifest_path)
    manifest = json.loads(mp.read_text(encoding="utf-8"))
    manifest_bytes = mp.read_bytes()
    origin_manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    manifest_dir = mp.parent
    layers_out = {}
    composite_layers = {}
    layers = manifest.get("layers", {})
    for lname, linfo in sorted(layers.items()):
        layer_path = manifest_dir / linfo["path"]
        raw = json.loads(layer_path.read_text(encoding="utf-8"))
        version = raw.get("version", "1.0.0")
        data = raw.get("data", raw)
        layer_hash = hashlib.sha256(_canonical_bytes(data)).hexdigest()
        layers_out[lname] = {"version": str(version), "data": data, "hash": "sha256:" + layer_hash}
        composite_layers[lname] = {"version": str(version), "hash": "sha256:" + layer_hash}
    composite = {"schema":"hakumadi-fingerprint-record-1","engine_version":engine_version,"origin_manifest_hash":"sha256:"+origin_manifest_hash,"layers":composite_layers}
    record_hash = hashlib.sha256(_canonical_bytes(composite)).hexdigest()
    record_id = "sha256:" + record_hash
    deterministic_record = {"schema":"hakumadi-fingerprint-record-1","record_id":record_id,"origin_manifest": manifest.get("origin_manifest", str(manifest_path)),"engine_version":engine_version,"layers":layers_out,"runtime_state":{"computed_composite":None,"evaluation_flags":manifest.get("evaluation_flags",[])}}
    metadata = {"created_at": datetime.utcnow().isoformat() + "Z", "manifest_path": str(mp)}
    return deterministic_record, metadata
