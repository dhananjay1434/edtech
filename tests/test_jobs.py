import pytest
from datetime import datetime, timedelta
from cde.db import DatabaseAdapter
from cde.indexes import ensure_indexes
from cde.jobs.queue import claim_job, heartbeat, complete_job, fail_job


@pytest.fixture
def db():
    a = DatabaseAdapter("mongodb://localhost:27017", "cde_test")
    a.db.jobs.delete_many({})
    ensure_indexes(a.db)
    return a


def _job(db, jid="j1", **kw):
    doc = {"_id": jid, "kind": "read_sheet", "entity_id": "sh1", "status": "pending",
           "attempt_count": 0, "max_attempts": 3, "lease_owner": None,
           "lease_expires_at": None, "fencing_token": 0,
           "idempotency_key": f"k-{jid}", "created_at": datetime.utcnow()}
    doc.update(kw)
    db.db.jobs.insert_one(doc)
    return doc


def test_claim_returns_job(db):
    _job(db)
    j = claim_job(db.db, "read_sheet", "w1")
    assert j["_id"] == "j1" and j["lease_owner"] == "w1" and j["fencing_token"] == 1


def test_two_workers_cannot_claim_same_job(db):
    _job(db)
    a = claim_job(db.db, "read_sheet", "w1")
    b = claim_job(db.db, "read_sheet", "w2")
    assert a is not None and b is None, "Two workers claimed the same job"


def test_expired_lease_can_be_reclaimed(db):
    _job(db, status="running", lease_owner="dead",
         lease_expires_at=datetime.utcnow() - timedelta(minutes=10))
    j = claim_job(db.db, "read_sheet", "w2")
    assert j is not None and j["lease_owner"] == "w2"


def test_stale_worker_cannot_complete(db):
    """A worker that lost its lease must not be able to finish the job."""
    _job(db)
    first = claim_job(db.db, "read_sheet", "w1")
    db.db.jobs.update_one({"_id": "j1"},
                          {"$set": {"lease_expires_at": datetime.utcnow() - timedelta(minutes=1)}})
    second = claim_job(db.db, "read_sheet", "w2")
    assert not complete_job(db.db, "j1", "w1", first["fencing_token"]), \
        "Stale worker completed a job it no longer owned"
    assert complete_job(db.db, "j1", "w2", second["fencing_token"])


def test_heartbeat_fails_after_lease_lost(db):
    _job(db)
    j = claim_job(db.db, "read_sheet", "w1")
    db.db.jobs.update_one({"_id": "j1"}, {"$inc": {"fencing_token": 1}})
    assert heartbeat(db.db, "j1", "w1", j["fencing_token"]) is False


def test_retries_then_gives_up(db):
    _job(db, max_attempts=2)
    for _ in range(2):
        j = claim_job(db.db, "read_sheet", "w1")
        fail_job(db.db, "j1", "w1", j["fencing_token"], "boom")
    assert db.db.jobs.find_one({"_id": "j1"})["status"] == "failed"
    assert claim_job(db.db, "read_sheet", "w1") is None
