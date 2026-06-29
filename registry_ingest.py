#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
from registrar.registry import RegistryManager
from truth_reflector import TruthReflector
from scorer.ingest_and_score import score_from_reconciliation
from datetime import datetime

class RegistryIngestor:
    def __init__(self, registry_manager=None, reflector=None):
        self.registry = registry_manager or RegistryManager()
        self.reflector = reflector or TruthReflector()

    def ingest(self, fingerprint_record: dict, source: str="external"):
        asset_id = fingerprint_record["record_id"]
        internal = self.registry.get_node(asset_id)
        internal_fpr = internal.get("fingerprint_record") if internal else None
        drift_report = self.reflector.compare(internal_fpr, fingerprint_record, asset_id) if fingerprint_record else None

        # In the demo we still provide placeholder attribution_confidence & provenance_depth;
        # integration should supply evaluator-derived values in production.
        reconciliation_for_scoring = dict(drift_report)
        reconciliation_for_scoring["attribution_confidence"] = reconciliation_for_scoring.get("attribution_confidence", 0.8)
        reconciliation_for_scoring["provenance_depth"] = reconciliation_for_scoring.get("provenance_depth", 0.5)

        trust = score_from_reconciliation(asset_id, reconciliation_for_scoring)

        node = {
            "asset_id": asset_id,
            "origin_manifest": fingerprint_record.get("origin_manifest"),
            "engine_version": fingerprint_record.get("engine_version"),
            "fingerprint_record": fingerprint_record,
            "ingestion": {"source": source, "ingested_at": datetime.utcnow().isoformat()+"Z"},
            "reconciliation": drift_report,
            "trust": trust,
            "status": trust["interpretation"]
        }

        # Upsert into registry so re-ingest updates node rather than crashing
        stored = self.registry.upsert_node(node)
        return {"status":"ADMITTED", "asset_id": asset_id, "trust": trust, "stored": stored}
