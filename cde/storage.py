"""
cde/storage.py — MongoDB GridFS Object-storage abstraction.

Replaced S3 with GridFS so no credit card or external cloud is needed.
Images are stored directly inside the MongoDB database.
"""
import logging
from typing import Optional
import gridfs
from bson.objectid import ObjectId
from cde.db import db_adapter

logger = logging.getLogger(__name__)

def upload(submission_id: str, data: bytes, content_type: str = "image/png") -> str:
    """
    Persist *data* in MongoDB GridFS and return a stable storage key.
    """
    db = db_adapter.db
    fs = gridfs.GridFS(db)
    
    # Put the file into GridFS
    file_id = fs.put(data, filename=f"{submission_id}.png", content_type=content_type)
    storage_key = f"gridfs:{file_id}"
    logger.info("Uploaded rough sheet to MongoDB GridFS with key: %s", storage_key)
    return storage_key

def upload_named(filename: str, data: bytes, content_type: str = "image/png") -> str:
    """
    Like `upload`, but lets the caller pick the GridFS filename directly
    instead of deriving it from a submission id. Used for per-question
    evidence crops (a submission can have many crops).

    Returns the bare GridFS ObjectId as a string (not prefixed with
    "gridfs:") — this is the id consumed by GET /api/evidence/{crop_id}
    and GET /api/images/{file_id}.
    """
    db = db_adapter.db
    fs = gridfs.GridFS(db)
    file_id = fs.put(data, filename=filename, content_type=content_type)
    logger.info("Uploaded evidence crop to MongoDB GridFS: %s (%s)", filename, file_id)
    return str(file_id)


def _download_bytes(storage_key: str) -> bytes:
    """Read a stored file back into memory.

    `upload()` returns keys prefixed "gridfs:<ObjectId>"; `upload_named()`
    returns the bare ObjectId string. Handle both.
    """
    db = db_adapter.db
    fs = gridfs.GridFS(db)
    key = storage_key.split("gridfs:", 1)[-1]
    return fs.get(ObjectId(key)).read()


def presign(storage_key: str, ttl_seconds: int = 3600) -> Optional[str]:
    """
    Return a relative URL that the frontend can use to download the image.
    """
    if not storage_key or not storage_key.startswith("gridfs:"):
        # Local mock fallback support if needed
        return None
    
    file_id = storage_key.split("gridfs:")[1]
    # Point to the FastAPI route in beta.py
    return f"/api/images/{file_id}"
