import re

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from cde.db import get_db_adapter
from cde.features import (
    CATALOG, DENYLIST, FEATURE_KEYS, catalog_view, effective_enabled, get_feature,
    validate_toggles,
)
from cde.services.entitlements import require_feature


def test_catalog_keys_unique_and_namespaced():
    keys = [f.key for f in CATALOG]
    assert len(keys) == len(set(keys))
    assert set(keys) == FEATURE_KEYS
    for k in keys:
        assert re.fullmatch(r"(cognitive|learning)\.[a-z_]+", k), k


def test_catalog_entries_are_well_formed():
    for f in CATALOG:
        assert f.tier in (2, 3)
        assert f.status in ("available", "preview")
        assert f.title.strip() and f.description.strip()


def test_effective_enabled_defaults_false_and_ignores_unknown():
    assert effective_enabled(None) == {k: False for k in FEATURE_KEYS}
    doc = {"enabled": {"cognitive.growth": True, "bogus.key": True}}
    enabled = effective_enabled(doc)
    assert enabled["cognitive.growth"] is True
    assert "bogus.key" not in enabled
    assert set(enabled) == FEATURE_KEYS


def test_validate_toggles_rejects_unknown_key():
    with pytest.raises(ValueError, match="bogus.key"):
        validate_toggles({"cognitive.growth": True, "bogus.key": False})


def test_validate_toggles_rejects_non_bool():
    with pytest.raises(ValueError, match="cognitive.growth"):
        validate_toggles({"cognitive.growth": "yes"})


def test_catalog_copy_passes_denylist():
    for f in CATALOG:
        hit = DENYLIST.search(f"{f.title} {f.description}")
        assert hit is None, f"{f.key}: {hit.group(0)!r}"


def test_denylist_does_not_trip_on_taxonomy_keys():
    assert DENYLIST.search("careless_slip") is None
    assert DENYLIST.search("a careless mistake") is not None


def test_catalog_view_carries_enabled_flag():
    view = catalog_view({**{k: False for k in FEATURE_KEYS}, "cognitive.growth": True})
    by_key = {v["key"]: v for v in view}
    assert by_key["cognitive.growth"]["enabled"] is True
    assert by_key["cognitive.patterns"]["enabled"] is False
    assert set(by_key["cognitive.growth"]) == {"key", "title", "description", "tier", "status", "enabled"}


def test_get_feature_unknown_raises():
    with pytest.raises(KeyError):
        get_feature("nope.nope")


class _FakeCollection:
    def __init__(self, doc):
        self.doc = doc

    def find_one(self, *_args, **_kwargs):
        return self.doc


class _FakeAdapter:
    def __init__(self, doc):
        self.db = type("Db", (), {"entitlements": _FakeCollection(doc)})()


def _gated_app(doc):
    app = FastAPI()

    @app.get("/gated", dependencies=[Depends(require_feature("cognitive.growth"))])
    def gated():
        return {"ok": True}

    app.dependency_overrides[get_db_adapter] = lambda: _FakeAdapter(doc)
    return TestClient(app)


def test_require_feature_returns_404_when_disabled():
    r = _gated_app(None).get("/gated")
    assert r.status_code == 404
    assert r.json() == {"detail": "Not found"}


def test_require_feature_passes_when_enabled():
    r = _gated_app({"_id": "institute", "enabled": {"cognitive.growth": True}}).get("/gated")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_require_feature_unknown_key_fails_at_definition():
    with pytest.raises(KeyError):
        require_feature("nope.nope")
