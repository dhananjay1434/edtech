from datetime import datetime


def link_account(db_adapter, issuer: str, subject: str, student_id: str) -> dict:
    """Bind a Keycloak identity to a roster student. Immutable once created."""
    with db_adapter.unit_of_work() as s:
        existing = db_adapter.db.account_links.find_one(
            {"issuer": issuer, "subject": subject}, session=s)
        if existing:
            if existing["student_id"] != student_id:
                raise ValueError("This login is already linked to a different student.")
            return existing
        if not db_adapter.db.students.find_one({"_id": student_id}, session=s):
            raise ValueError("Cannot link a login to a non-roster student")
        link = {"_id": f"{issuer}|{subject}", "issuer": issuer, "subject": subject,
                "student_id": student_id, "created_at": datetime.utcnow()}
        db_adapter.db.account_links.insert_one(link, session=s)
    return link


def resolve_student_id(db_adapter, issuer: str, subject: str) -> str:
    link = db_adapter.db.account_links.find_one({"issuer": issuer, "subject": subject})
    if not link:
        raise PermissionError("This login is not linked to a roster student.")
    return link["student_id"]
