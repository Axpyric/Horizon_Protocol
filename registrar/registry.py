#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
registrar/registry.py

SQLite-backed RegistryManager to replace a flat registry.json.

DB: canon/haunted_hoard.db
Table: nodes
  - asset_id TEXT PRIMARY KEY
  - payload TEXT (JSON)
  - revision INTEGER
  - created_at TEXT
  - updated_at TEXT

APIs:
  - init_db()
  - add_node(node)        # insert-only; raises if exists
  - upsert_node(node)     # insert or update; preserves created_at, bumps revision
  - get_node(asset_id)
  - list_nodes(limit)
  - migrate_from_json(path)  # optional helper to import old registry.json
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

DB_PATH = Path("canon/haunted_hoard.db")

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = _connect()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS nodes (
        asset_id TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        revision INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

class RegistryManager:
    def __init__(self):
        init_db()

    def add_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert-only. Raises ValueError on duplicate asset_id.
        """
        asset_id = node.get("asset_id") or node.get("record_id") or node.get("fingerprint_record", {}).get("record_id")
        if not asset_id:
            raise ValueError("node missing asset_id")
        existing = self.get_node(asset_id)
        if existing:
            raise ValueError("asset already exists")
        now = datetime.utcnow().isoformat() + "Z"
        payload = json.dumps(node, sort_keys=True)
        conn = _connect()
        conn.execute(
            "INSERT INTO nodes (asset_id, payload, revision, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (asset_id, payload, 1, now, now)
        )
        conn.commit()
        conn.close()
        return node

    def upsert_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert or update node.
        - If new: revision = 1, created_at = now
        - If exists: revision = prev_revision + 1, created_at preserved
        Stores payload as JSON.
        Returns the stored node (as dict).
        """
        asset_id = node.get("asset_id") or node.get("record_id") or node.get("fingerprint_record", {}).get("record_id")
        if not asset_id:
            raise ValueError("node missing asset_id")
        conn = _connect()
        cur = conn.execute("SELECT payload, revision, created_at FROM nodes WHERE asset_id = ?", (asset_id,))
        row = cur.fetchone()
        now = datetime.utcnow().isoformat() + "Z"
        payload = json.dumps(node, sort_keys=True)
        if not row:
            revision = 1
            created_at = now
            conn.execute(
                "INSERT INTO nodes (asset_id, payload, revision, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (asset_id, payload, revision, created_at, now)
            )
        else:
            prev_payload, prev_rev, prev_created = row
            revision = int(prev_rev) + 1
            created_at = prev_created
            conn.execute(
                "UPDATE nodes SET payload = ?, revision = ?, updated_at = ? WHERE asset_id = ?",
                (payload, revision, now, asset_id)
            )
        conn.commit()
        conn.close()
        # return a copy of the stored node (attach revision/created_at/updated_at)
        stored = self.get_node(asset_id)
        return stored

    def get_node(self, asset_id: str) -> Optional[Dict[str, Any]]:
        conn = _connect()
        cur = conn.execute("SELECT payload, revision, created_at, updated_at FROM nodes WHERE asset_id = ?", (asset_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        payload_json, revision, created_at, updated_at = row
        try:
            payload = json.loads(payload_json)
        except Exception:
            payload = {"raw": payload_json}
        # attach revision/created_at/updated_at for convenience
        payload["_registry"] = {"revision": int(revision), "created_at": created_at, "updated_at": updated_at}
        return payload

    def list_nodes(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = _connect()
        cur = conn.execute("SELECT payload FROM nodes ORDER BY rowid DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        conn.close()
        out = []
        for (p,) in rows:
            try:
                out.append(json.loads(p))
            except Exception:
                out.append({"raw": p})
        return out

    def migrate_from_json(self, json_path: str):
        """
        Load old canon/registry.json and insert any nodes into the DB that are not present.
        """
        p = Path(json_path)
        if not p.exists():
            return 0
        data = json.loads(p.read_text(encoding="utf-8"))
        nodes = data.get("nodes", [])
        count = 0
        for n in nodes:
            asset_id = n.get("asset_id") or n.get("origin_manifest") or n.get("fingerprint_record", {}).get("record_id")
            if not asset_id:
                continue
            if not self.get_node(asset_id):
                # upsert will insert
                self.upsert_node(n)
                count += 1
        return count
