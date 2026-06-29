#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import json, hashlib

def _canonical_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def _sha(obj):
    return hashlib.sha256(_canonical_bytes(obj)).hexdigest()

class TrustScorer:
    def __init__(self, ruleset):
        self.ruleset = ruleset
        self.w = ruleset["weights"]
        self.t = ruleset["thresholds"]
    def score(self, asset_id, reconciliation):
        variance = max(0.0, min(1.0, float(reconciliation["comparison"]["variance_score"])))
        attribution = max(0.0, min(1.0, float(reconciliation.get("attribution_confidence", 0.5))))
        provenance = max(0.0, min(1.0, float(reconciliation.get("provenance_depth", 0.5))))
        v = 1 - variance
        score_float = self.w["variance_score"]*v + self.w["attribution_confidence"]*attribution + self.w["provenance_depth"]*provenance
        score_float = max(0.0, min(1.0, score_float))
        score_str = f"{score_float:.8f}"
        interpretation = self._interpret(score_float)
        explanation = {"variance_contribution": self.w["variance_score"]*v, "attribution_contribution": self.w["attribution_confidence"]*attribution, "provenance_contribution": self.w["provenance_depth"]*provenance}
        score_id = _sha({"asset_id": asset_id, "score": score_str, "ruleset": self.ruleset})
        return {"schema":"hakumadi-trust-score-1","score_id":score_id,"asset_id":asset_id,"ruleset_version":self.ruleset["version"],"score":score_str,"interpretation":interpretation,"computed_components":{"variance_score":variance,"attribution_confidence":attribution,"provenance_depth":provenance},"explanation_vector":explanation,"signals":reconciliation["comparison"].get("signals",[])}
    def _interpret(self, score):
        if score >= self.t["canonical"]: return "CANONICAL"
        if score >= self.t["trusted"]: return "TRUSTED"
        if score >= self.t["stable"]: return "STABLE"
        if score >= self.t["review"]: return "REVIEW"
        return "SUSPICIOUS"
