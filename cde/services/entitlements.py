from datetime import datetime
from typing import Callable, Dict

from fastapi import Depends, HTTPException

from cde.db import DatabaseAdapter, get_db_adapter
from cde.features import ENTITLEMENTS_DOC_ID, effective_enabled, get_feature, validate_toggles


def read_enabled(db_adapter: DatabaseAdapter) -> Dict[str, bool]:
    doc = db_adapter.db.entitlements.find_one({"_id": ENTITLEMENTS_DOC_ID})
    return effective_enabled(doc)


def set_enabled(db_adapter: DatabaseAdapter, toggles: Dict[str, bool], actor_id: str) -> Dict[str, bool]:
    toggles = validate_toggles(toggles)
    with db_adapter.unit_of_work() as s:
        update = {f"enabled.{k}": v for k, v in toggles.items()}
        update["updated_at"] = datetime.utcnow()
        update["updated_by"] = actor_id
        db_adapter.db.entitlements.update_one(
            {"_id": ENTITLEMENTS_DOC_ID}, {"$set": update}, upsert=True, session=s)
    return read_enabled(db_adapter)


def require_feature(key: str) -> Callable[..., None]:
    """FastAPI dependency: 404s a route when `key` is not enabled.

    A gated resource is invisible, never forbidden — 404, not 403 — so nothing
    tells an unentitled caller that the feature exists at all.
    """
    get_feature(key)  # fail fast at import time if key is unknown

    def dependency(db_adapter: DatabaseAdapter = Depends(get_db_adapter)) -> None:
        if not read_enabled(db_adapter).get(key):
            raise HTTPException(status_code=404, detail="Not found")

    return dependency
