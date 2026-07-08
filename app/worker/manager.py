#!/usr/bin/env python3
"""
Thin WorkerManager conductor (refactored to be a thin conductor).

Uses projection for O(1) lookups, schedules retries with backoff, supports graceful shutdown,
and dispatches to route-specific executors. Registers internal PayoutExecutor for route "payout".
"""
import asyncio
from typing import Dict, Any, Optional
from ..ledger import Ledger
from .decision_engine import decide_next_action, short_history
from .execution_router import ExecutorBase, SimpleExecutor
from .recovery_engine import handle_failure
from ..projection import Projection
import time

# Import local executor mapping
from ..execution.payout_executor import PayoutExecutor


class WorkerManager:
    def __init__(self, ledger: Ledger, executor: Optional[ExecutorBase] = None):
        self.ledger = ledger
        self.default_executor = executor or SimpleExecutor()
        # allow a mapping for route->executor
        self.executors: Dict[str, ExecutorBase] = {}
        self.executors["payout"] = PayoutExecutor()
        self.queue: asyncio.Queue = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._shutdown = False
        # attach a projection for O(1) lookups
        if getattr(self.ledger, "_projection", None) is None:
            self.projection = Projection(self.ledger)
            # full rebuild at startup
            self.projection.rebuild(self.ledger.read_all_raw())
            self.ledger.set_projection(self.projection)
        else:
            self.projection = getattr(self.ledger, "_projection")
        # track scheduled timers to cancel on shutdown
        self._scheduled_handles = set()

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self, drain_timeout: float = 5.0):
        # signal shutdown; stop accepting new items
        self._shutdown = True
        # wait for queue to be processed with timeout (graceful drain)
        try:
            await asyncio.wait_for(self.queue.join(), timeout=drain_timeout)
        except asyncio.TimeoutError:
            # timed out draining; cancel worker loop
            pass
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        # cancel any scheduled requeue handles
        for h in list(self._scheduled_handles):
            try:
                h.cancel()
            except Exception:
                pass
        self._scheduled_handles.clear()

    async def _loop(self):
        while self._running:
            try:
                item = await self.queue.get()
                task_id = item["task_id"]
                file_uri = item["file_uri"]
                route = item["route"]
                file_hash = item.get("file_hash", "")

                # Use projection (O(1)) instead of replaying entire ledger
                proj = self.projection.get(task_id)
                events = [e for e in self.ledger.read_all_raw() if e.get("task_id") == task_id]

                # Pure decision
                decision = decide_next_action(proj or {}, events)
                action = decision.get("action")

                if action == "drop" or action == "noop":
                    # nothing to do
                    self.queue.task_done()
                    continue
                if action == "execute":
                    try:
                        # select executor by route
                        exec_impl = self.executors.get(route, self.default_executor)
                        await exec_impl.run(task_id, file_uri, route, self.ledger)
                    except Exception as e:
                        # append an execution failed event
                        self.ledger.append({"event_type": "EXECUTION_FAILED", "task_id": task_id, "file_hash": file_hash, "file_uri": file_uri, "state": "FAILED", "timestamp": time.time(), "meta": {"error": str(e)}})
                        proj = self.projection.get(task_id)
                        last_event = self.ledger.last_event_for(task_id)
                        last_event_dict = last_event.dict() if last_event is not None else {}
                        # recovery_engine determines RETRY vs DLQ; pass schedule callback to schedule delayed enqueue
                        handle_failure(proj or {}, last_event_dict, self.ledger, self._schedule_requeue_callback)
                else:
                    # unknown action, noop
                    pass

                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception:
                # swallow loop-level exceptions; ledger records failures
                continue

    def _schedule_requeue_callback(self, task_id: str, file_uri: str, route: str, file_hash: str, delay: float = 0.0):
        """Recovery engine calls this to schedule a delayed requeue."""
        if self._shutdown:
            return
        if delay <= 0:
            # immediate requeue
            try:
                self.enqueue(task_id, file_uri, route, file_hash)
            except Exception:
                pass
            return
        loop = asyncio.get_event_loop()
        handle = loop.call_later(delay, lambda: self.enqueue(task_id, file_uri, route, file_hash))
        self._scheduled_handles.add(handle)
        # remove handle on execution
        def _cleanup(h=handle):
            try:
                self._scheduled_handles.discard(h)
            except Exception:
                pass
        # schedule a cleanup after delay + small margin
        loop.call_later(delay + 1.0, _cleanup)

    def enqueue(self, task_id: str, file_uri: str, route: str, file_hash: str):
        if self._shutdown:
            # reject new enqueues during shutdown
            return
        self.queue.put_nowait({"task_id": task_id, "file_uri": file_uri, "route": route, "file_hash": file_hash})

    def qsize(self) -> int:
        return self.queue.qsize()

    # Convenience synchronous wrapper for testing/CLI
    def enqueue_sync(self, task_id: str, file_uri: str, route: str, file_hash: str):
        self.enqueue(task_id, file_uri, route, file_hash)
