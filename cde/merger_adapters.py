from __future__ import annotations

import asyncio
import copy
import math
import os
import queue
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable
from uuid import UUID

import pymongo
from pymongo.client_session import ClientSession
from pymongo.errors import OperationFailure

from cde.db import db_adapter, get_db
from cde.beta.ports import (
    UnitOfWork,
    SubmissionReadPort,
    AnswerMutationPort,
    StagePort,
    OutboxPort,
    ReviewPort,
)

def _seconds(name: str, default: float, maximum: float) -> float:
    value = float(os.environ.get(name, str(default)))
    if not math.isfinite(value) or not 0 < value <= maximum:
        raise ValueError(f"Invalid {name}")
    return value

WORKERS = int(os.environ.get("CDE_MONGO_TRANSACTION_WORKERS", "32"))
if not 1 <= WORKERS <= 64:
    raise ValueError("CDE_MONGO_TRANSACTION_WORKERS must be between 1 and 64")

OP_SECONDS = _seconds("CDE_MONGO_OPERATION_SECONDS", 3.0, 10.0)
TX_SECONDS = _seconds("CDE_MONGO_TRANSACTION_SECONDS", 15.0, 20.0)
CLEANUP_SECONDS = _seconds("CDE_MONGO_CLEANUP_SECONDS", 3.0, 5.0)

_EXECUTOR = ThreadPoolExecutor(
    max_workers=WORKERS, thread_name_prefix="cde-mongo-transaction"
)
_SLOTS = threading.BoundedSemaphore(WORKERS)

class _RollbackRequested(Exception):
    """Internal context-manager exit signal, not a failed user operation."""

@dataclass(frozen=True)
class _Command:
    kind: str
    action: Callable[[Any, ClientSession], Any] | None = None
    reply: Future | None = None

def _settle(future: Future, value: Any = None,
            error: BaseException | None = None) -> None:
    if not future.done():
        if error is None:
            future.set_result(value)
        else:
            future.set_exception(error)

def _observe_async_future(future: asyncio.Future) -> None:
    # A cancelled waiter must not leave an eventual worker exception unobserved.
    if not future.cancelled():
        future.exception()

class RealUnitOfWork(UnitOfWork):
    """One synchronous transaction actor; never share a session with callers.

    Use only inside an activity/service, not inside Temporal workflow code.
    execute() callbacks must perform finite synchronous MongoDB work and return
    materialized results. No HTTP calls, sleeps, cursors, or external side effects.
    """

    def __init__(self) -> None:
        self._commands: queue.Queue[_Command] = queue.Queue(maxsize=1)
        self._cancel = threading.Event()
        self._ready: Future = Future()
        self._closed: Future = Future()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._used = False
        self._busy = False
        self._closing = False
        self._deadline = 0.0

    def _check_loop(self) -> None:
        if self._loop is None or asyncio.get_running_loop() is not self._loop:
            raise OperationFailure("Unit of work used outside its owning event loop")

    async def _wait(self, future: Future, seconds: float) -> Any:
        wrapped = asyncio.wrap_future(future)
        wrapped.add_done_callback(_observe_async_future)
        try:
            return await asyncio.wait_for(
                asyncio.shield(wrapped), timeout=max(0.001, seconds)
            )
        except asyncio.TimeoutError as exc:
            self._cancel.set()
            raise OperationFailure("MongoDB adapter deadline exceeded", code=50) from exc
        except asyncio.CancelledError:
            self._cancel.set()
            raise

    async def __aenter__(self) -> "RealUnitOfWork":
        if self._used:
            raise OperationFailure("Unit of work cannot be reused")
        self._used = True
        self._loop = asyncio.get_running_loop()
        if not _SLOTS.acquire(blocking=False):
            raise OperationFailure("MongoDB transaction capacity exhausted")
        self._deadline = time.monotonic() + TX_SECONDS
        try:
            job = _EXECUTOR.submit(self._worker)
        except BaseException:
            _SLOTS.release()
            raise
        # A cancelled asyncio waiter cannot free capacity while its actor runs.
        job.add_done_callback(lambda _: _SLOTS.release())
        try:
            await self._wait(self._ready, OP_SECONDS + CLEANUP_SECONDS + 1.0)
        except BaseException:
            self._cancel.set()
            raise
        return self

    async def execute(self, action: Callable[[Any, ClientSession], Any]) -> Any:
        self._check_loop()
        if self._closing or self._closed.done() or self._cancel.is_set():
            raise OperationFailure("Unit of work is closed or aborting")
        if self._busy:
            raise OperationFailure("Concurrent operations on one unit of work are forbidden")
        if time.monotonic() >= self._deadline:
            self._cancel.set()
            raise OperationFailure("Transaction deadline exceeded", code=50)
        self._busy = True
        reply: Future = Future()
        try:
            self._commands.put_nowait(_Command("call", action, reply))
            return await self._wait(
                reply, min(OP_SECONDS, self._deadline - time.monotonic())
                + CLEANUP_SECONDS + 1.0
            )
        except queue.Full as exc:
            self._cancel.set()
            raise OperationFailure("Transaction mailbox is full") from exc
        finally:
            self._busy = False

    async def _finish(self, kind: str) -> None:
        self._check_loop()
        if self._closed.done():
            await self._wait(self._closed, 0.1)
            return
        if not self._closing:
            if self._busy:
                self._cancel.set()
                raise OperationFailure("Cannot finish a transaction with an operation in flight")
            self._closing = True
            try:
                self._commands.put_nowait(_Command(kind))
            except queue.Full as exc:
                self._cancel.set()
                raise OperationFailure("Transaction mailbox is full") from exc
        await self._wait(
            self._closed,
            max(0.0, self._deadline - time.monotonic()) + CLEANUP_SECONDS + 1.0,
        )

    async def commit(self) -> None:
        await self._finish("commit")

    async def rollback(self) -> None:
        await self._finish("rollback")

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._check_loop()
        if exc_type is None:
            try:
                await self.commit()
            except BaseException:
                self._cancel.set()
                raise
            return

        self._closing = True
        self._cancel.set()
        try:
            await self._wait(self._closed, OP_SECONDS + CLEANUP_SECONDS + 1.0)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Preserve the exception from the async-with body. Cleanup stays
            # owned by the actor even if this bounded wait expires.
            pass

    def _worker(self) -> None:
        ctx = None
        entered = False
        failure: BaseException | None = None
        rollback = False
        active: _Command | None = None
        try:
            if self._cancel.is_set():
                raise OperationFailure("Transaction cancelled before start")
            db = get_db()
            ctx = db_adapter.unit_of_work()
            with pymongo.timeout(OP_SECONDS):
                session = ctx.__enter__()
                entered = True
            _settle(self._ready)

            while True:
                if self._cancel.is_set():
                    raise OperationFailure("Transaction cancelled")
                remaining = self._deadline - time.monotonic()
                if remaining <= 0:
                    raise OperationFailure("Transaction deadline exceeded", code=50)
                try:
                    active = self._commands.get(timeout=min(0.05, remaining))
                except queue.Empty:
                    continue
                if self._cancel.is_set():
                    raise OperationFailure("Transaction cancelled")
                if active.kind in {"commit", "rollback"}:
                    rollback = active.kind == "rollback"
                    active = None
                    break
                if active.kind != "call" or active.action is None:
                    raise OperationFailure("Invalid transaction command")
                remaining = self._deadline - time.monotonic()
                if remaining <= 0:
                    raise OperationFailure("Transaction deadline exceeded", code=50)
                with pymongo.timeout(min(OP_SECONDS, remaining)):
                    value = active.action(db, session)
                if self._cancel.is_set():
                    raise OperationFailure("Transaction cancelled during operation")
                if time.monotonic() >= self._deadline:
                    raise OperationFailure("Transaction deadline exceeded", code=50)
                assert active.reply is not None
                _settle(active.reply, value=value)
                active = None
        except BaseException as exc:
            failure = exc
        finally:
            if entered and ctx is not None:
                if self._cancel.is_set() and failure is None:
                    failure = OperationFailure("Transaction cancelled before completion")
                reason = failure or (_RollbackRequested() if rollback else None)
                try:
                    # The context was entered on this same worker. Its exit
                    # performs commit/abort and end_session on that worker too.
                    with pymongo.timeout(CLEANUP_SECONDS):
                        ctx.__exit__(
                            type(reason) if reason is not None else None,
                            reason,
                            reason.__traceback__ if reason is not None else None,
                        )
                except BaseException as cleanup_error:
                    if failure is None:
                        failure = cleanup_error
                    else:
                        failure.add_note(
                            "Transaction cleanup also failed: "
                            + type(cleanup_error).__name__
                        )
            terminal_error = failure or OperationFailure("Unit of work has ended")
            if not self._ready.done():
                _settle(self._ready, error=terminal_error)
            if active is not None and active.reply is not None:
                _settle(active.reply, error=terminal_error)
            while True:
                try:
                    pending = self._commands.get_nowait()
                except queue.Empty:
                    break
                if pending.reply is not None:
                    _settle(pending.reply, error=terminal_error)
            _settle(self._closed, error=failure)

class RealSubmissionReadPort(SubmissionReadPort):
    async def get_submission(
        self, uow: RealUnitOfWork, submission_id: UUID
    ) -> dict[str, Any]:
        def read(db, session):
            document = db.submissions.find_one(
                {"_id": str(submission_id)}, session=session
            )
            if document is None:
                raise OperationFailure("Submission not found")
            return document
        return await uow.execute(read)

class RealAnswerMutationPort(AnswerMutationPort):
    async def save_answers(
        self, uow: RealUnitOfWork, submission_id: UUID,
        answers: list[dict[str, Any]],
    ) -> None:
        payload = copy.deepcopy(answers)

        def save(db, session):
            result = db.submissions.update_one(
                {"_id": str(submission_id), "answers_locked_at": None},
                {"$set": {"answers": payload}}, session=session,
            )
            if result.matched_count != 1:
                raise OperationFailure("Submission is missing or answers are locked")
        await uow.execute(save)

    async def lock_answers(
        self, uow: RealUnitOfWork, submission_id: UUID, locked_at: datetime
    ) -> None:
        if locked_at.tzinfo is None or locked_at.utcoffset() is None:
            raise ValueError("locked_at must be timezone-aware")

        def lock(db, session):
            result = db.submissions.update_one(
                {"_id": str(submission_id), "answers_locked_at": None},
                {"$set": {"answers_locked_at": locked_at}}, session=session,
            )
            if result.matched_count != 1:
                raise OperationFailure("Submission is missing or answers are already locked")
        await uow.execute(lock)

def shutdown_merger_executor() -> None:
    """Call after stopping new activity admission during graceful shutdown."""
    _EXECUTOR.shutdown(wait=True, cancel_futures=False)

import uuid as _uuid
import copy
from datetime import datetime as _datetime
from cde.beta.ports import OutboxPort

class RealOutboxPort(OutboxPort):
    async def append_event(
        self, uow, event_type: str, payload: dict
    ) -> str:
        event_id = str(_uuid.uuid4())
        payload_copy = copy.deepcopy(payload)
        def write(db, session):
            db.outbox.insert_one({
                "_id": event_id,
                "type": event_type,
                "payload": payload_copy,
                "status": "pending",
                "created_at": _datetime.utcnow(),
            }, session=session)
            return event_id
        return await uow.execute(write)

    async def acknowledge_event(self, event_id: str, owner: str, fence: int) -> None:
        from cde.db import get_db_adapter
        db_adapter = get_db_adapter()
        db_adapter.db.outbox.update_one(
            {"_id": event_id},
            {"$set": {
                "status": "acknowledged",
                "acknowledged_by": owner,
                "fence": fence,
                "acknowledged_at": _datetime.utcnow(),
            }},
        )
