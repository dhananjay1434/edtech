from typing import Dict, Any, Callable, Awaitable
from uuid import UUID
from datetime import datetime

from cde.beta.ports import UnitOfWork, ReviewPort, OutboxPort

# Typed handler registry for review tasks
ReviewHandler = Callable[[UnitOfWork, UUID, Dict[str, Any], Dict[str, Any]], Awaitable[None]]

class ReviewRegistry:
    def __init__(self):
        self._handlers: Dict[str, ReviewHandler] = {}

    def register(self, kind: str, handler: ReviewHandler):
        self._handlers[kind] = handler

    def get_handler(self, kind: str) -> ReviewHandler:
        if kind not in self._handlers:
            raise ValueError(f"No handler registered for review kind: {kind}")
        return self._handlers[kind]

registry = ReviewRegistry()

class ReviewService:
    def __init__(self, review_port: ReviewPort, outbox_port: OutboxPort, registry: ReviewRegistry):
        self.review_port = review_port
        self.outbox_port = outbox_port
        self.registry = registry

    async def claim_task(self, uow: UnitOfWork, task_id: UUID, claimant: str, lease_seconds: int) -> Dict[str, Any]:
        return await self.review_port.claim_task(uow, task_id, claimant, lease_seconds)

    async def resolve_task(
        self,
        uow: UnitOfWork,
        task_id: UUID,
        task_kind: str,
        expected_version: int,
        resolution: Dict[str, Any],
        idempotency_key: str
    ) -> None:
        # 1. Resolve task
        await self.review_port.resolve_task(uow, task_id, expected_version, resolution)
        
        # 2. Dispatch to typed handler
        handler = self.registry.get_handler(task_kind)
        await handler(uow, task_id, resolution, {"idempotency_key": idempotency_key})
        
        # 3. Persist audit and resume outbox event
        await self.outbox_port.append_event(
            uow,
            "review_resolved",
            {
                "task_id": str(task_id),
                "resolution": resolution,
                "idempotency_key": idempotency_key
            }
        )

# Example Bubble handler
async def handle_bubble_review(uow: UnitOfWork, task_id: UUID, resolution: Dict[str, Any], context: Dict[str, Any]) -> None:
    # Update answers through AnswerMutationPort
    # (Implementation would require answer_mutation_port injection)
    pass

registry.register("bubble", handle_bubble_review)

def make_bubble_handler(answer_mutation_port):
    async def handle_bubble_review(
        uow, task_id, resolution, context
    ) -> None:
        import uuid
        await answer_mutation_port.save_answers(
            uow,
            uuid.UUID(resolution["submission_id"]),
            [{
                "question_number": resolution["question_number"],
                "selected_option": resolution["selected_option"],
                "finalized": True,
                "source": "human_review",
            }]
        )
    return handle_bubble_review
