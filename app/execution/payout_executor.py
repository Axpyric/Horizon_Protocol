#!/usr/bin/env python3
"""
app/execution/payout_executor.py

Internal-only payout executor that wraps settlement.adapters.adapter_mock.
This executor is intentionally NOT exposed over HTTP; it is invoked by the
WorkerManager in-process. It writes an execution receipt and records status
via settlement.ledger.append_transaction() for persistence.
"""
from typing import Dict, Any
import time
import json
import asyncio
from ..ledger import Ledger
from settlement.adapters.adapter_mock import execute_payout
from settlement.ledger import append_transaction, init_db, load_transaction


class PayoutExecutor:
    """
    Executor interface compatible with execution_router.ExecutorBase / SimpleExecutor style.
    run(task_id, file_uri, route, ledger) -> returns result dict
    """

    async def run(self, task_id: str, file_uri: str, route: str, ledger: Ledger) -> Dict[str, Any]:
        # For payout flow, task_id is expected to correspond to a settlement proposal_id
        # (or test harness can pass proposal_id in file_uri or meta). We'll attempt to
        # read proposal by task_id from settlement ledger first, fallback to file_uri.
        # This executor calls blocking IO in a thread to avoid blocking the event loop.
        proposal_id = task_id
        # load proposal from settlement DB if available
        try:
            tx = load_transaction(proposal_id)
        except Exception:
            tx = None

        if tx and tx.get("proposal"):
            proposal = tx["proposal"]
        else:
            # fallback: attempt to load JSON from file_uri
            try:
                with open(file_uri, "r", encoding="utf-8") as fh:
                    proposal = json.load(fh)
            except Exception:
                proposal = {"proposal_id": proposal_id, "asset_id": None, "allocations": {}}

        # Execute via mock adapter in a thread to avoid blocking event loop
        receipt = await asyncio.to_thread(execute_payout, proposal)

        # Persist execution result in settlement ledger (update status)
        init_db()
        append_transaction(proposal, status="EXECUTED")

        # Emit a RESULT-like dict for orchestrator ledger recording (manager will append RESULT events)
        result_meta = {"receipt": receipt, "executed_at": time.time()}
        return result_meta
