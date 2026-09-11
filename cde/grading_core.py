from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

THREE_PLACES = Decimal("0.001")

@dataclass
class AnswerAward:
    question_number: int
    state: str
    awarded_marks: Decimal
    selected_option: str | None = None
    finalized: bool = True

@dataclass
class Grade:
    awards: Tuple[AnswerAward, ...]
    score: Decimal
    maximum: Decimal
    percentage: Decimal

def grade_submission(submission: Dict[str, Any]) -> Grade:
    # Basic validation
    if not submission.get("identity_confirmed"):
        raise ValueError("Identity not confirmed")
    if not submission.get("alignment_confirmed"):
        raise ValueError("Alignment not confirmed")
    
    # Check if there are blocking reviews? 
    # State should not be awaiting_review if there are unfinalized answers.
    # We must reject unfinalized answers.
    answers = submission.get("answers", [])
    for ans in answers:
        if not ans.get("finalized"):
            raise ValueError(f"Answer for question {ans.get('question_number')} is not finalized.")
    
    policy = submission.get("marking_policy", {})
    correct_marks = Decimal(policy.get("correct_marks", "1.000"))
    wrong_marks = Decimal(policy.get("wrong_marks", "0.000"))
    blank_marks = Decimal(policy.get("blank_marks", "0.000"))
    multiple_marks = Decimal(policy.get("multiple_marks", "0.000"))

    if wrong_marks > 0 or blank_marks > 0 or multiple_marks > 0:
        raise ValueError("Wrong, blank and multiple marks must be non-positive.")
    if correct_marks <= 0:
        raise ValueError("Correct marks must be positive.")
        
    question_count = submission.get("question_count", 0)
    answer_key = {k["question_number"]: k for k in submission.get("answer_key", [])}
    
    # Check exact contiguous coverage
    expected_numbers = set(range(1, question_count + 1))
    actual_numbers = {a["question_number"] for a in answers}
    if actual_numbers != expected_numbers:
        raise ValueError("Missing or unexpected answers. Contiguous coverage required.")
    
    # Check duplicate answers
    if len(answers) != len(actual_numbers):
        raise ValueError("Duplicate answers detected.")
    
    awards = []
    
    for ans in answers:
        q_num = ans["question_number"]
        sel_opt = ans.get("selected_option")
        key_entry = answer_key[q_num]
        if key_entry.get("question_type") == "integer":
            key_opt = str(key_entry["correct_value"])
        else:
            key_opt = key_entry["correct_option"]

        if ans.get("state") == "invalid_multiple":
            state = "invalid_multiple"
            marks = multiple_marks
        elif sel_opt is None:
            state = "blank"
            marks = blank_marks
        elif sel_opt == key_opt:
            state = "correct"
            marks = correct_marks
        else:
            state = "incorrect"
            marks = wrong_marks
            
        awards.append(AnswerAward(
            question_number=q_num,
            state=state,
            awarded_marks=marks,
            selected_option=sel_opt,
            finalized=True
        ))
        
    score = sum((a.awarded_marks for a in awards), Decimal("0"))
    maximum = correct_marks * question_count
    percentage = (score * Decimal("100") / maximum).quantize(
        THREE_PLACES, rounding=ROUND_HALF_UP
    )
    
    return Grade(tuple(awards), score, maximum, percentage)
