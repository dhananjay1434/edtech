import pytest
from decimal import Decimal
from cde.grading_core import grade_submission

def test_grade_submission_all_correct():
    submission = {
        "identity_confirmed": True,
        "alignment_confirmed": True,
        "question_count": 2,
        "marking_policy": {
            "correct_marks": "1.000",
            "wrong_marks": "-0.250",
            "blank_marks": "0.000"
        },
        "answer_key": [
            {"question_number": 1, "correct_option": "A"},
            {"question_number": 2, "correct_option": "B"}
        ],
        "answers": [
            {"question_number": 1, "selected_option": "A", "finalized": True},
            {"question_number": 2, "selected_option": "B", "finalized": True}
        ]
    }
    
    grade = grade_submission(submission)
    assert grade.score == Decimal("2.000")
    assert grade.maximum == Decimal("2.000")
    assert grade.percentage == Decimal("100.000")

def test_grade_submission_mixed():
    submission = {
        "identity_confirmed": True,
        "alignment_confirmed": True,
        "question_count": 2,
        "marking_policy": {
            "correct_marks": "1.000",
            "wrong_marks": "-0.250",
            "blank_marks": "0.000"
        },
        "answer_key": [
            {"question_number": 1, "correct_option": "A"},
            {"question_number": 2, "correct_option": "B"}
        ],
        "answers": [
            {"question_number": 1, "selected_option": "A", "finalized": True},
            {"question_number": 2, "selected_option": "C", "finalized": True}
        ]
    }
    grade = grade_submission(submission)
    assert grade.score == Decimal("0.750")
    assert grade.percentage == Decimal("37.500")
    
def test_grade_submission_unfinalized_rejected():
    submission = {
        "identity_confirmed": True,
        "alignment_confirmed": True,
        "question_count": 2,
        "marking_policy": {
            "correct_marks": "1.000",
            "wrong_marks": "-0.250",
            "blank_marks": "0.000"
        },
        "answer_key": [
            {"question_number": 1, "correct_option": "A"},
            {"question_number": 2, "correct_option": "B"}
        ],
        "answers": [
            {"question_number": 1, "selected_option": "A", "finalized": True},
            {"question_number": 2, "selected_option": None, "finalized": False}
        ]
    }
    with pytest.raises(ValueError, match="is not finalized"):
        grade_submission(submission)
