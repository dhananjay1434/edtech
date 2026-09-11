import uuid
from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel, Field


class RosterRow(BaseModel):
    roll_number: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)


class RosterImport(BaseModel):
    exam_class: str = Field(min_length=1, max_length=64)
    rows: List[RosterRow] = Field(min_length=1, max_length=500)


def normalize_roll(roll: str) -> str:
    """Normalize for MATCHING only. The original is always stored unchanged.
    Do NOT strip leading zeros — '007' and '7' may be different students."""
    return roll.strip().upper()


def import_roster(db_adapter, payload: RosterImport, actor_id: str) -> Dict:
    seen: Dict[str, str] = {}
    for row in payload.rows:
        k = normalize_roll(row.roll_number)
        if k in seen:
            raise ValueError(
                f"Duplicate roll number '{row.roll_number}' (also '{seen[k]}'). "
                "Fix the roster before importing.")
        seen[k] = row.name

    roster_id = f"roster_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow()
    with db_adapter.unit_of_work() as s:
        db_adapter.db.rosters.insert_one({
            "_id": roster_id, "exam_class": payload.exam_class,
            "revision": 1, "created_at": now, "created_by": actor_id}, session=s)
        db_adapter.db.students.insert_many([{
            "_id": f"std_{uuid.uuid4().hex[:12]}",
            "roster_id": roster_id,
            "exam_class": payload.exam_class,
            "roll_number": r.roll_number,
            "roll_number_normalized": normalize_roll(r.roll_number),
            "name": r.name,
            "created_at": now,
        } for r in payload.rows], session=s)
        db_adapter.db.audit_events.insert_one({
            "kind": "roster_imported", "roster_id": roster_id,
            "student_count": len(payload.rows), "actor": actor_id, "at": now}, session=s)
    return {"roster_id": roster_id, "student_count": len(payload.rows)}
