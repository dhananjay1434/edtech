import pytest
from fastapi.testclient import TestClient

from cde.api import app
from cde.db import DatabaseAdapter, get_db_adapter
from cde.features import FEATURE_KEYS
from cde.routes.admin import verified_admin_claims
from cde.routes.student import current_student_id

TEST_DB = DatabaseAdapter("mongodb://localhost:27017", "cde_test")

app.dependency_overrides[get_db_adapter] = lambda: TEST_DB
app.dependency_overrides[current_student_id] = lambda: "std1"
app.dependency_overrides[verified_admin_claims] = lambda: {
    "sub": "admin1", "iss": "test-issuer", "realm_access": {"roles": ["admin"]}}

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    TEST_DB.db.entitlements.delete_many({})
    yield


def _enabled_map(features):
    return {f["key"]: f["enabled"] for f in features}


def test_student_features_all_disabled_by_default():
    r = client.get("/api/me/features")
    assert r.status_code == 200
    features = r.json()["features"]
    assert {f["key"] for f in features} == FEATURE_KEYS
    assert all(f["enabled"] is False for f in features)


def test_admin_put_enables_and_student_sees_it():
    r = client.put("/api/admin/features", json={"enabled": {"cognitive.growth": True}})
    assert r.status_code == 200
    assert _enabled_map(r.json()["features"])["cognitive.growth"] is True

    r = client.get("/api/me/features")
    assert _enabled_map(r.json()["features"])["cognitive.growth"] is True


def test_admin_put_unknown_key_422_and_writes_nothing():
    r = client.put("/api/admin/features", json={"enabled": {"bogus.key": True}})
    assert r.status_code == 422
    assert TEST_DB.db.entitlements.find_one({"_id": "institute"}) is None


def test_admin_put_is_partial_merge():
    client.put("/api/admin/features", json={"enabled": {"cognitive.growth": True}})
    client.put("/api/admin/features", json={"enabled": {"cognitive.patterns": True}})
    r = client.get("/api/admin/features")
    enabled = _enabled_map(r.json()["features"])
    assert enabled["cognitive.growth"] is True
    assert enabled["cognitive.patterns"] is True
