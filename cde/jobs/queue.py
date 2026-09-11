from datetime import datetime, timedelta
from typing import Optional, Dict
from pymongo import ASCENDING, ReturnDocument

DEFAULT_LEASE_SECONDS = 300


def claim_job(db, kind: str, owner: str,
              lease_seconds: int = DEFAULT_LEASE_SECONDS) -> Optional[Dict]:
    """Atomically claim one pending job, or a job whose lease has expired."""
    now = datetime.utcnow()
    return db.jobs.find_one_and_update(
        {"kind": kind,
         "status": {"$in": ["pending", "running"]},
         "$or": [{"lease_expires_at": None}, {"lease_expires_at": {"$lt": now}}],
         "$expr": {"$lt": ["$attempt_count", "$max_attempts"]}},
        {"$set": {"status": "running", "lease_owner": owner,
                  "lease_expires_at": now + timedelta(seconds=lease_seconds),
                  "updated_at": now},
         "$inc": {"attempt_count": 1, "fencing_token": 1}},
        sort=[("created_at", ASCENDING)],
        return_document=ReturnDocument.AFTER)


def heartbeat(db, job_id: str, owner: str, fencing_token: int,
              lease_seconds: int = DEFAULT_LEASE_SECONDS) -> bool:
    """Extend the lease. False means the lease was lost — STOP WORKING."""
    now = datetime.utcnow()
    r = db.jobs.update_one(
        {"_id": job_id, "lease_owner": owner, "fencing_token": fencing_token},
        {"$set": {"lease_expires_at": now + timedelta(seconds=lease_seconds)}})
    return r.matched_count == 1


def complete_job(db, job_id: str, owner: str, fencing_token: int, session=None) -> bool:
    """Mark succeeded, only if this worker still holds the lease."""
    r = db.jobs.update_one(
        {"_id": job_id, "lease_owner": owner, "fencing_token": fencing_token},
        {"$set": {"status": "succeeded", "lease_owner": None,
                  "lease_expires_at": None, "updated_at": datetime.utcnow()}},
        session=session)
    return r.matched_count == 1


def fail_job(db, job_id: str, owner: str, fencing_token: int, error: str) -> None:
    job = db.jobs.find_one({"_id": job_id})
    exhausted = job and job["attempt_count"] >= job["max_attempts"]
    db.jobs.update_one(
        {"_id": job_id, "lease_owner": owner, "fencing_token": fencing_token},
        {"$set": {"status": "failed" if exhausted else "pending",
                  "last_error": error[:500], "lease_owner": None,
                  "lease_expires_at": None, "updated_at": datetime.utcnow()}})
