import pytest
from cde.db import DatabaseAdapter

URI, DB = "mongodb://localhost:27017", "cde_test"


def test_refuses_without_replica_set(monkeypatch):
    a = DatabaseAdapter(URI, DB)
    monkeypatch.setattr(a, "check_replica_set", lambda: False)
    with pytest.raises(RuntimeError, match="replica set"):
        with a.unit_of_work():
            pass


def test_commits_on_replica_set():
    a = DatabaseAdapter(URI, DB)
    assert a.check_replica_set(), "Run MongoDB with --replSet (P0-T1)"
    a.db.probe.delete_many({})
    with a.unit_of_work() as s:
        a.db.probe.insert_one({"_id": "x", "v": 1}, session=s)
    assert a.db.probe.find_one({"_id": "x"})["v"] == 1
    a.db.probe.delete_many({})


def test_rolls_back_on_error():
    a = DatabaseAdapter(URI, DB)
    a.db.probe.delete_many({})
    with pytest.raises(ValueError):
        with a.unit_of_work() as s:
            a.db.probe.insert_one({"_id": "y"}, session=s)
            raise ValueError("boom")
    assert a.db.probe.find_one({"_id": "y"}) is None
