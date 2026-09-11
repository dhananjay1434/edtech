"""Database indexes. Safety rules depend on these — they are not optional."""
from pymongo import ASCENDING


def ensure_indexes(db) -> list[str]:
    created = []

    # A roll number is unique WITHIN a roster. The same number in another
    # class or year is a different student.
    db.students.create_index(
        [("roster_id", ASCENDING), ("roll_number_normalized", ASCENDING)],
        unique=True, name="uniq_roll_per_roster")
    created.append("uniq_roll_per_roster")

    # One Keycloak identity maps to exactly one student, permanently.
    db.account_links.create_index(
        [("issuer", ASCENDING), ("subject", ASCENDING)],
        unique=True, name="uniq_account_link")
    created.append("uniq_account_link")

    # Every page of a batch appears exactly once.
    db.sheets.create_index(
        [("batch_id", ASCENDING), ("page_number", ASCENDING)],
        unique=True, name="uniq_page_per_batch")
    created.append("uniq_page_per_batch")

    # A student may have at most one sheet per exam. Partial index so many
    # sheets may have student_id = None simultaneously.
    db.sheets.create_index(
        [("exam_id", ASCENDING), ("student_id", ASCENDING)],
        unique=True, name="uniq_sheet_per_student_exam",
        partialFilterExpression={"student_id": {"$type": "string"}})
    created.append("uniq_sheet_per_student_exam")

    # A job is never enqueued twice for the same work.
    db.jobs.create_index([("idempotency_key", ASCENDING)],
                         unique=True, name="uniq_job_idempotency")
    created.append("uniq_job_idempotency")

    # Worker claim query.
    db.jobs.create_index(
        [("kind", ASCENDING), ("status", ASCENDING), ("lease_expires_at", ASCENDING)],
        name="job_claim")
    created.append("job_claim")

    # One published report per student per exam per revision.
    db.report_revisions.create_index(
        [("exam_id", ASCENDING), ("student_id", ASCENDING), ("revision", ASCENDING)],
        unique=True, name="uniq_report_revision")
    created.append("uniq_report_revision")

    return created
