#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from datetime import datetime
import hashlib, json

def _sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

class TruthReflector:
    def __init__(self, reconciliation_version="1.0.0"):
        self.reconciliation_version = reconciliation_version

    def compare(self, internal_fingerprint: dict, external_fingerprint: dict, asset_id: str) -> dict:
        report_id = _sha({"asset_id": asset_id, "internal": (internal_fingerprint or {}).get("record_id"), "external": external_fingerprint.get("record_id"), "version": self.reconciliation_version})
        internal_layers = (internal_fingerprint or {}).get("layers", {})
        external_layers = external_fingerprint.get("layers", {})
        def _layer_delta(a,b,layer):
            la = a.get(layer,{}).get("hash","")
            lb = b.get(layer,{}).get("hash","")
            if not la or not lb: return 1.0
            return 0.0 if la==lb else 0.5
        cadence_delta = _layer_delta(internal_layers, external_layers, "cadence")
        structure_delta = _layer_delta(internal_layers, external_layers, "structure")
        timbre_delta = None
        variance_score = (cadence_delta + structure_delta)/2
        signals = []
        if cadence_delta>0: signals.append("CADENCE_DIVERGENCE")
        if structure_delta>0: signals.append("STRUCTURE_DIVERGENCE")
        if cadence_delta==0 and structure_delta==0: signals.append("FULL_MATCH")
        status = "CANONICAL" if variance_score<0.01 else ("STABLE" if variance_score<0.1 else ("DRIFTING" if variance_score<0.3 else "DIVERGENT"))
        return {
            "schema": "hakumadi-reconciliation-report-1",
            "report_id": report_id,
            "asset_id": asset_id,
            "reconciliation_version": self.reconciliation_version,
            "generated_at": datetime.utcnow().isoformat()+"Z",
            "source": {"internal_fingerprint": (internal_fingerprint or {}).get("record_id"), "external_fingerprint": external_fingerprint.get("record_id")},
            "comparison": {"variance_score": variance_score, "signals": signals, "layer_breakdown": {"cadence_delta": cadence_delta, "structure_delta": structure_delta, "timbre_delta": timbre_delta}},
            "interpretation": {"status": status, "notes": "Phase A passive audit"}
        }
