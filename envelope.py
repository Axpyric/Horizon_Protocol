#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import json, base64
from typing import Any, Dict

def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

class Envelope:
    def __init__(self, record: Dict[str,Any], metadata: Dict[str,Any], schema: str = "hakumadi-envelope-1"):
        self.payload = {"schema": schema, "record": record, "metadata": metadata}
        self.signatures = []
    def canonical_bytes(self) -> bytes:
        return canonical_bytes(self.payload)
    def attach_signature(self, sig: Dict[str,Any]):
        self.signatures.append(sig)
    def to_dict(self) -> Dict[str,Any]:
        out = dict(self.payload)
        if self.signatures:
            out["signatures"] = list(self.signatures)
        return out
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, indent=2, ensure_ascii=False)
