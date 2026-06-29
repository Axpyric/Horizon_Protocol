#!/usr/bin/env python3
import yaml
from scorer.core import TrustScorer
def load_ruleset(path="scorer/ruleset_v1.yml"):
    return yaml.safe_load(open(path, "r", encoding="utf-8"))
def score_from_reconciliation(asset_id: str, reconciliation: dict):
    ruleset = load_ruleset()
    engine = TrustScorer(ruleset)
    return engine.score(asset_id, reconciliation)
