import uuid
from datetime import datetime
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class AnswerKeyEntry(BaseModel):
    """`question_type="integer"` is for JEE Main Section B numerical-answer
    questions. The OMR engine has no calibration for a digit grid and never
    attempts to read these — they always go to a human, who views the sheet
    image and types the value in. `question_type="mcq"` is the normal
    four-option bubble question, read automatically."""
    question_number: int = Field(ge=1)
    question_type: Literal["mcq", "integer"] = "mcq"
    correct_option: Optional[str] = Field(default=None, pattern="^[A-D]$")
    correct_value: Optional[int] = Field(default=None, ge=0, le=9999)
    # Optional: needed for Release-B AI diagnosis (cde/diagnostics.py refuses
    # to diagnose a question with no question_text). Not required for
    # Release-A scoring, which only needs correct_option/correct_value.
    question_text: Optional[str] = Field(default=None, max_length=4000)
    options: Optional[Dict[str, str]] = None

    @model_validator(mode="after")
    def fields_match_type(self):
        if self.question_type == "mcq":
            if self.correct_option is None:
                raise ValueError(f"Q{self.question_number}: mcq questions need correct_option")
            if self.correct_value is not None:
                raise ValueError(f"Q{self.question_number}: mcq questions must not set correct_value")
        else:
            if self.correct_value is None:
                raise ValueError(f"Q{self.question_number}: integer questions need correct_value")
            if self.correct_option is not None:
                raise ValueError(f"Q{self.question_number}: integer questions must not set correct_option")
        return self


class SubjectRange(BaseModel):
    subject: str = Field(min_length=1, max_length=40)
    first_question: int = Field(ge=1)
    last_question: int = Field(ge=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.last_question < self.first_question:
            raise ValueError("last_question must be >= first_question")
        return self


class MarkingPolicy(BaseModel):
    correct_marks: str = "4.000"
    wrong_marks: str = "-1.000"
    blank_marks: str = "0.000"
    multiple_marks: str = "-1.000"


class ExamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    roster_id: str
    question_count: int = Field(ge=1, le=180)
    marking_policy: MarkingPolicy = MarkingPolicy()
    answer_key: List[AnswerKeyEntry]
    subject_ranges: List[SubjectRange] = []

    @model_validator(mode="after")
    def key_covers_every_question(self):
        nums = sorted(e.question_number for e in self.answer_key)
        if nums != list(range(1, self.question_count + 1)):
            raise ValueError(
                f"Answer key must cover questions 1..{self.question_count} exactly once"
            )
        return self

    @model_validator(mode="after")
    def subjects_do_not_overlap(self):
        seen = set()
        for r in self.subject_ranges:
            rng = set(range(r.first_question, r.last_question + 1))
            if rng & seen:
                raise ValueError(f"Subject ranges overlap at {sorted(rng & seen)}")
            if r.last_question > self.question_count:
                raise ValueError("Subject range exceeds question_count")
            seen |= rng
        return self


def create_exam(db_adapter, payload: ExamCreate, actor_id: str) -> Dict:
    exam_id = f"exam_{uuid.uuid4().hex[:12]}"
    with db_adapter.unit_of_work() as s:
        if not db_adapter.db.rosters.find_one({"_id": payload.roster_id}, session=s):
            raise ValueError(f"Roster {payload.roster_id} not found")
        db_adapter.db.exams.insert_one({
            "_id": exam_id,
            "name": payload.name,
            "roster_id": payload.roster_id,
            "question_count": payload.question_count,
            "marking_policy": payload.marking_policy.model_dump(),
            "answer_key": [e.model_dump() for e in payload.answer_key],
            "subject_ranges": [r.model_dump() for r in payload.subject_ranges],
            "report_policy_revision": "score_only",
            "created_at": datetime.utcnow(),
            "created_by": actor_id,
        }, session=s)
    return {"exam_id": exam_id, "question_count": payload.question_count}


def subject_for_question(exam: Dict, question_number: int) -> str | None:
    for r in exam.get("subject_ranges", []):
        if r["first_question"] <= question_number <= r["last_question"]:
            return r["subject"]
    return None
