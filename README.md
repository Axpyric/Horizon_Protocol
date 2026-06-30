[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# Hakumadi Phase A+B+C2 demo

This branch contains the demo-ready prototype for the Hakumadi system:
- Deterministic fingerprint engine
- Envelopes + local Ed25519 signing
- Truth Reflector (reconciliation)
- Registry ingestion with SQLite-backed registry (haunted_hoard.db)
- Trust scorer (deterministic)
- run_local_demo.py to orchestrate the flow for local testing

Quick start:
1. python -m venv .venv
2. source .venv/bin/activate
3. pip install -r requirements.txt
4. python signing/generate_key.py
5. python run_local_demo.py

License: Apache-2.0 — see LICENSE file for full terms.
