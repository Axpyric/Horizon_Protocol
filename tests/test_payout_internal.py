import tempfile
import json
import asyncio
from pathlib import Path

from app.ledger import Ledger
from app.projection import Projection
from app.worker.manager import WorkerManager
from app.execution.payout_executor import PayoutExecutor
from settlement.core import compute_settlement_proposal
from settlement.ledger import init_db, append_transaction, load_transaction


def test_payout_executor_roundtrip(tmp_path):
    # create deterministic proposal
    attr = {"attribution_id": "attr-x", "payout_map": {"alice": "1.0"}, "result_node_id": "node-x"}
    trust = {"score_id": "s-x", "interpretation": "TRUSTED"}
    ruleset = {"version": "1.0.0", "eligibility": {"allowed_interpretations": ["TRUSTED", "CANONICAL", "STABLE"]}}
    proposal, meta = compute_settlement_proposal(attr, trust, ruleset, {"USD": "10.00"}, "period-test")
    # persist into settlement ledger DB
    init_db()
    append_transaction(proposal, status="PROPOSED")
    pid = proposal["proposal_id"]

    # prepare orchestrator ledger and manager
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = Ledger(ledger_path)
    proj = Projection(ledger)
    proj.rebuild([])
    ledger.set_projection(proj)

    manager = WorkerManager(ledger=ledger)

    # start manager loop in background
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _run():
        await manager.start()
        # enqueue payout: task_id == proposal_id; route 'payout' selects PayoutExecutor
        manager.enqueue(pid, "", "payout", pid)
        # wait a bit for queue processing
        await asyncio.sleep(0.5)
        # stop manager
        await manager.stop(drain_timeout=1.0)

    loop.run_until_complete(_run())
    # verify settlement DB updated to EXECUTED
    tx = load_transaction(pid)
    assert tx is not None
    assert tx["status"] == "EXECUTED"

    # ensure an execution receipt file exists in settlement/out
    out_dir = Path("settlement/out")
    found = list(out_dir.glob("execution-*.json"))
    assert len(found) >= 1

    # cleanup loop
    loop.close()
