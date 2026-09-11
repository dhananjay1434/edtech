from datetime import datetime, timezone
from uuid import UUID
from typing import Dict, Any

from cde.grading_core import grade_submission
from cde.beta.ports import UnitOfWork, SubmissionReadPort, AnswerMutationPort, OutboxPort

class GradingService:
    def __init__(
        self,
        submission_read_port: SubmissionReadPort,
        answer_mutation_port: AnswerMutationPort,
        outbox_port: OutboxPort,
        clock: Any = None
    ):
        self.submission_read_port = submission_read_port
        self.answer_mutation_port = answer_mutation_port
        self.outbox_port = outbox_port
        self.clock = clock or datetime

    async def run_grading(self, uow: UnitOfWork, submission_id: UUID) -> Dict[str, Any]:
        submission = await self.submission_read_port.get_submission(uow, submission_id)
        
        if submission.get("answers_locked_at") is not None:
            # Already graded, return the stored grade
            return {
                "score": submission.get("score"),
                "percentage": submission.get("percentage")
            }

        grade = grade_submission(submission)
        
        answers_to_save = []
        for award in grade.awards:
            answers_to_save.append({
                "question_number": award.question_number,
                "selected_option": award.selected_option,
                "finalized": award.finalized,
                "state": award.state,
                "awarded_marks": str(award.awarded_marks)
            })

        await self.answer_mutation_port.save_answers(uow, submission_id, answers_to_save)
        
        locked_at = self.clock.now(timezone.utc)
        await self.answer_mutation_port.lock_answers(uow, submission_id, locked_at)
        
        await self.outbox_port.append_event(
            uow,
            "submission_graded",
            {
                "submission_id": str(submission_id),
                "score": str(grade.score),
                "percentage": str(grade.percentage)
            }
        )
        
        return {
            "score": str(grade.score),
            "percentage": str(grade.percentage)
        }
