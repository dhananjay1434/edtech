from typing import Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from cde.beta.ports import UnitOfWork, StagePort, OutboxPort

class StageService:
    def __init__(self, stage_port: StagePort, clock: Any = None):
        self.stage_port = stage_port
        self.clock = clock or datetime

    async def acquire(self, uow: UnitOfWork, submission_id: UUID, stage: str, input_fingerprint: str, owner: str, lease_seconds: int = 120) -> Dict[str, Any]:
        return await self.stage_port.acquire_stage(uow, submission_id, stage, input_fingerprint, owner, lease_seconds)

    async def commit(self, uow: UnitOfWork, submission_id: UUID, stage: str, input_fingerprint: str, owner: str, fence: int, result: Dict[str, Any]) -> None:
        await self.stage_port.commit_stage(uow, submission_id, stage, input_fingerprint, owner, fence, result)
