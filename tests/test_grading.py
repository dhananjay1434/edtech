import pytest
from decimal import Decimal
from cde.grading_core import grade_submission

POLICY = {"correct_marks": "4.000", "wrong_marks": "-1.000",
          "blank_marks": "0.000", "multiple_marks": "-1.000"}


def sub(answers, n):
    return {"identity_confirmed": True, "alignment_confirmed": True,
            "question_count": n, "marking_policy": POLICY,
            "answer_key": [{"question_number": i, "correct_option": "A"}
                           for i in range(1, n + 1)],
            "answers": answers}


def ans(q, opt, state=None, finalized=True):
    d = {"question_number": q, "selected_option": opt, "finalized": finalized}
    if state:
        d["state"] = state
    return d


def test_correct_wrong_blank():
    g = grade_submission(sub([ans(1,"A"), ans(2,"A"), ans(3,"A"),
                              ans(4,"B"), ans(5,None)], 5))
    assert g.score == Decimal("11.000")      # 12 - 1 + 0
    assert g.maximum == Decimal("20.000")


def test_multiple_scores_minus_one_not_zero():
    g = grade_submission(sub([ans(1,"A"), ans(2,None,state="invalid_multiple")], 2))
    assert g.score == Decimal("3.000"), "invalid_multiple scored as blank, not wrong"


def test_guesser_scores_below_blank_leaver():
    guess = [ans(i,"A") for i in range(1,11)] + [ans(i,"B") for i in range(11,21)]
    blank = [ans(i,"A") for i in range(1,11)] + [ans(i,None) for i in range(11,21)]
    assert grade_submission(sub(guess,20)).score == Decimal("30.000")
    assert grade_submission(sub(blank,20)).score == Decimal("40.000")


def test_full_paper_maximum_is_300():
    g = grade_submission(sub([ans(i,"A") for i in range(1,76)], 75))
    assert g.maximum == Decimal("300.000")
    assert g.score == Decimal("300.000")


def test_positive_penalty_rejected():
    b = sub([ans(1,"A")], 1); b["marking_policy"] = {**POLICY, "wrong_marks": "1.000"}
    with pytest.raises(ValueError, match="non-positive"):
        grade_submission(b)


def test_unfinalized_blocks_grading():
    with pytest.raises(ValueError, match="not finalized"):
        grade_submission(sub([ans(1,"A",finalized=False)], 1))


def test_integer_question_scored_by_exact_value_match():
    sub = {"identity_confirmed": True, "alignment_confirmed": True,
           "question_count": 2, "marking_policy": POLICY,
           "answer_key": [
               {"question_number": 1, "question_type": "mcq", "correct_option": "A"},
               {"question_number": 2, "question_type": "integer", "correct_value": 42},
           ],
           "answers": [
               ans(1, "A"),
               {"question_number": 2, "selected_option": "42", "finalized": True},
           ]}
    g = grade_submission(sub)
    assert g.score == Decimal("8.000")       # both correct: 4 + 4
    assert g.awards[1].state == "correct"


def test_integer_question_wrong_value():
    sub = {"identity_confirmed": True, "alignment_confirmed": True,
           "question_count": 1, "marking_policy": POLICY,
           "answer_key": [{"question_number": 1, "question_type": "integer", "correct_value": 42}],
           "answers": [{"question_number": 1, "selected_option": "7", "finalized": True}]}
    g = grade_submission(sub)
    assert g.score == Decimal("-1.000")
    assert g.awards[0].state == "incorrect"


def test_integer_question_blank():
    sub = {"identity_confirmed": True, "alignment_confirmed": True,
           "question_count": 1, "marking_policy": POLICY,
           "answer_key": [{"question_number": 1, "question_type": "integer", "correct_value": 42}],
           "answers": [{"question_number": 1, "selected_option": None, "finalized": True}]}
    g = grade_submission(sub)
    assert g.score == Decimal("0.000")
    assert g.awards[0].state == "blank"


def test_unconfirmed_identity_blocks_grading():
    b = sub([ans(1,"A")], 1); b["identity_confirmed"] = False
    with pytest.raises(ValueError, match="Identity"):
        grade_submission(b)


from dataclasses import dataclass
from cde.services.grading import (scope_answers_to_exam, find_stray_marks_outside_exam,
                                   build_answer_docs)


@dataclass
class FakeQ:
    question_number: int
    selected_option: str | None
    state: str
    needs_review: bool = False


def test_scoping_drops_unused_rows():
    qs = [FakeQ(i, "A", "filled") for i in range(1, 181)]
    scoped = scope_answers_to_exam(qs, 75)
    assert len(scoped) == 75 and max(q.question_number for q in scoped) == 75


def test_stray_mark_in_unused_row_is_reported():
    qs = [FakeQ(i, None, "blank") for i in range(1, 181)]
    qs[119] = FakeQ(120, "C", "filled")
    assert find_stray_marks_outside_exam(qs, 75) == [120]


def test_clean_unused_rows_are_fine():
    qs = [FakeQ(i, "A" if i <= 75 else None,
                "filled" if i <= 75 else "blank") for i in range(1, 181)]
    assert find_stray_marks_outside_exam(qs, 75) == []


def test_multiple_is_not_blank():
    d = build_answer_docs([FakeQ(1, None, "multiple")])[0]
    assert d["state"] == "invalid_multiple" and d["finalized"] is True


def test_needs_review_not_finalized():
    d = build_answer_docs([FakeQ(1, None, "ambiguous", needs_review=True)])[0]
    assert d["finalized"] is False


def test_integer_question_never_trusts_omr_reading():
    """Even if the OMR engine confidently read something in that row (it
    has no calibration for a digit grid, so any reading there is noise),
    an integer-type question must always be routed to a human, unfinalized."""
    from cde.services.grading import integer_question_numbers
    q = FakeQ(5, "C", "filled", needs_review=False)   # OMR is "confident"
    d = build_answer_docs([q], integer_questions={5})[0]
    assert d["state"] == "pending_integer_entry"
    assert d["finalized"] is False
    assert d["selected_option"] is None


def test_integer_question_numbers_reads_exam_answer_key():
    from cde.services.grading import integer_question_numbers
    exam = {"answer_key": [
        {"question_number": 1, "question_type": "mcq", "correct_option": "A"},
        {"question_number": 2, "question_type": "integer", "correct_value": 7},
    ]}
    assert integer_question_numbers(exam) == {2}
