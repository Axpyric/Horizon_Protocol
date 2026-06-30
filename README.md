[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# Hakumadi — an open protocol for cryptographic creative provenance

Hakumadi is an open protocol for cryptographically verifiable creative provenance. This repository contains a reference implementation (demo) and the protocol documentation. The documentation lives in /docs — start with docs/SPECIFICATION.md.

Quick start (demo)
1. python -m venv .venv
2. source .venv/bin/activate
3. pip install -r requirements.txt
4. python signing/generate_key.py
5. python run_local_demo.py

Docs
- docs/SPECIFICATION.md — canonical protocol specification (required reading for implementers)
- docs/MANIFEST_V1.md — manifest schema and examples
- docs/ARCHITECTURE.md — architecture overview and deployment patterns
- docs/WHITEPAPER.md — concise whitepaper describing problem, approach, and roadmap

License: Apache-2.0 — see LICENSE file for full terms.
