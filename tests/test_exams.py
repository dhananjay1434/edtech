import pytest
from cde.db import DatabaseAdapter
from cde.services.exams import ExamCreate, AnswerKeyEntry, create_exam, subject_for_question


@pytest.fixture
def db():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    a.db.exams.delete_many({}); a.db.rosters.delete_many({})
    a.db.rosters.insert_one({"_id": "r1", "exam_class": "12A"})
    return a


def _key(n):
    return [{"question_number": i, "correct_option": "A"} for i in range(1, n + 1)]


def test_create_exam(db):
    p = ExamCreate(name="Mock 1", roster_id="r1", question_count=75, answer_key=_key(75))
    r = create_exam(db, p, "admin1")
    assert r["question_count"] == 75
    assert db.db.exams.find_one({"_id": r["exam_id"]})["marking_policy"]["wrong_marks"] == "-1.000"


def test_incomplete_answer_key_rejected():
    with pytest.raises(ValueError, match="1..75"):
        ExamCreate(name="x", roster_id="r1", question_count=75, answer_key=_key(70))


def test_overlapping_subjects_rejected():
    with pytest.raises(ValueError, match="overlap"):
        ExamCreate(name="x", roster_id="r1", question_count=75, answer_key=_key(75),
                   subject_ranges=[{"subject": "Physics", "first_question": 1, "last_question": 25},
                                   {"subject": "Chemistry", "first_question": 20, "last_question": 50}])


def test_integer_question_accepted():
    key = _key(2)
    key[1] = {"question_number": 2, "question_type": "integer", "correct_value": 42}
    p = ExamCreate(name="x", roster_id="r1", question_count=2, answer_key=key)
    assert p.answer_key[1].question_type == "integer"
    assert p.answer_key[1].correct_value == 42


def test_integer_question_rejects_correct_option():
    with pytest.raises(ValueError, match="must not set correct_option"):
        AnswerKeyEntry(question_number=1, question_type="integer",
                       correct_value=5, correct_option="A")


def test_integer_question_requires_correct_value():
    with pytest.raises(ValueError, match="need correct_value"):
        AnswerKeyEntry(question_number=1, question_type="integer")


def test_mcq_question_rejects_correct_value():
    with pytest.raises(ValueError, match="must not set correct_value"):
        AnswerKeyEntry(question_number=1, question_type="mcq",
                       correct_option="A", correct_value=5)


def test_subject_lookup():
    exam = {"subject_ranges": [
        {"subject": "Physics", "first_question": 1, "last_question": 25},
        {"subject": "Chemistry", "first_question": 26, "last_question": 50},
        {"subject": "Mathematics", "first_question": 51, "last_question": 75}]}
    assert subject_for_question(exam, 10) == "Physics"
    assert subject_for_question(exam, 40) == "Chemistry"
    assert subject_for_question(exam, 75) == "Mathematics"
    assert subject_for_question(exam, 120) is None
