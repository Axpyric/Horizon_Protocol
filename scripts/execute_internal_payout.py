#!/usr/bin/env python3
"""
scripts/execute_internal_payout.py

Small CLI helper to enqueue an internal payout execution via the in-process WorkerManager.
This is for local testing/demo only (no HTTP exposure).

Usage:
  python -m scripts.execute_internal_payout <proposal_id> [--file <proposal_json_path>]

It reads the global app.worker_manager created by app.main on startup. If you run this
from a REPL where the app is already running, import app.main and call enqueue_sync.
"""
import sys
import asyncio
from pathlib import Path


def main(argv):
    if len(argv) < 2:
        print("Usage: execute_internal_payout <proposal_id> [file_uri]")
        return 2
    proposal_id = argv[1]
    file_uri = argv[2] if len(argv) > 2 else ""

    # Lazy import to avoid import-time side effects
    import app.main as am

    # Ensure worker_manager is started (if running as module)
    wm = getattr(am, "worker_manager", None)
    if wm is None:
        print("Worker manager not available. Run the app first (uvicorn app.main:app) or import and start manager.")
        return 2

    # Enqueue the payout execution
    # For our payout executor, we use task_id == proposal_id. file_uri optional.
    wm.enqueue_sync(proposal_id, file_uri or f"settlement/proposal-{proposal_id}.json", "payout", file_hash=proposal_id)
    print(f"Enqueued internal payout execution for {proposal_id}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
