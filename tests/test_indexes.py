from cde.db import DatabaseAdapter
from cde.indexes import ensure_indexes


def test_indexes_are_created():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    names = ensure_indexes(a.db)
    for coll, idx in [("students", "uniq_roll_per_roster"),
                      ("sheets", "uniq_page_per_batch"),
                      ("sheets", "uniq_sheet_per_student_exam"),
                      ("jobs", "uniq_job_idempotency"),
                      ("account_links", "uniq_account_link")]:
        assert idx in a.db[coll].index_information(), f"{coll}.{idx} missing"


def test_duplicate_sheet_per_student_is_blocked_by_index():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    ensure_indexes(a.db)
    a.db.sheets.delete_many({})
    a.db.sheets.insert_one({"_id": "s1", "exam_id": "e1", "student_id": "std1",
                            "batch_id": "b1", "page_number": 1})
    import pymongo
    try:
        a.db.sheets.insert_one({"_id": "s2", "exam_id": "e1", "student_id": "std1",
                                "batch_id": "b1", "page_number": 2})
        assert False, "Index did not prevent two sheets for one student"
    except pymongo.errors.DuplicateKeyError:
        pass
    a.db.sheets.delete_many({})
