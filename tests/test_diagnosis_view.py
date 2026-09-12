from cde.services.diagnosis_view import build_diagnosis_view


def test_waiting_when_not_published():
    assert build_diagnosis_view(None, []) == {"status": "waiting_for_result"}
    assert build_diagnosis_view({"state": "pending_identity"}, []) == {"status": "waiting_for_result"}


def test_processing_when_not_ready():
    sheet = {"state": "published", "diagnostics_ready": False, "rough_sheet_status": "uploaded"}
    assert build_diagnosis_view(sheet, []) == {"status": "processing", "rough_sheet_status": "uploaded"}


def test_processing_when_diagnostics_ready_missing():
    sheet = {"state": "published", "rough_sheet_status": None}
    assert build_diagnosis_view(sheet, []) == {"status": "processing", "rough_sheet_status": None}


def _diag(question_number, grade_revision, **overrides):
    d = {"status": "classified", "error_class": "Calculation Slip", "confidence": 0.95,
         "summary": "s", "next_step": "n", "abstention_reason": None}
    d.update(overrides)
    return {"question_number": question_number, "grade_revision": grade_revision,
            "subject": "Physics", "diagnostic": d}


def test_ready_filters_old_revisions():
    sheet = {"state": "published", "diagnostics_ready": True, "grade_revision": 2,
              "rough_sheet_status": "uploaded"}
    docs = [_diag(1, 1), _diag(2, 2)]
    view = build_diagnosis_view(sheet, docs)
    assert view["status"] == "ready"
    assert view["grade_revision"] == 2
    assert [q["question_number"] for q in view["questions"]] == [2]


def test_ready_strips_evidence():
    sheet = {"state": "published", "diagnostics_ready": True, "grade_revision": 1}
    doc = _diag(1, 1)
    doc["diagnostic"]["evidence"] = [{"crop_id": "x", "bbox": [0, 0, 1, 1]}]
    view = build_diagnosis_view(sheet, [doc])
    assert "evidence" not in view["questions"][0]


def test_abstained_entries_carry_reason_and_zero_confidence():
    sheet = {"state": "published", "diagnostics_ready": True, "grade_revision": 1}
    doc = _diag(3, 1, status="abstained", error_class=None, confidence=0,
                abstention_reason="missing_question_context")
    view = build_diagnosis_view(sheet, [doc])
    q = view["questions"][0]
    assert q["status"] == "abstained"
    assert q["error_class"] is None
    assert q["confidence"] == 0
    assert q["abstention_reason"] == "missing_question_context"


def test_questions_are_sorted_by_number():
    sheet = {"state": "published", "diagnostics_ready": True, "grade_revision": 1}
    docs = [_diag(3, 1), _diag(1, 1), _diag(2, 1)]
    view = build_diagnosis_view(sheet, docs)
    assert [q["question_number"] for q in view["questions"]] == [1, 2, 3]
