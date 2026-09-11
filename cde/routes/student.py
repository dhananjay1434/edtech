from datetime import datetime
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File
from pymongo import ReturnDocument
from cde.db import DatabaseAdapter, get_db_adapter
from cde.auth import AuthorizationPort, get_auth_port
from cde.services.accounts import resolve_student_id

student_router = APIRouter()

MAX_ROUGH_SHEET_BYTES = 15 * 1024 * 1024
ALLOWED_ROUGH_SHEET_TYPES = {"image/png", "image/jpeg"}


def verified_claims(authorization: str = Header(...),
                    auth_port: AuthorizationPort = Depends(get_auth_port)) -> dict:
    print(f"VERIFYING TOKEN: {authorization[:20]}...", flush=True)
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing bearer token")
    try:
        return auth_port.validate_token(authorization[7:])
    except Exception as e:
        print(f"DEBUG VERIFIED CLAIMS: {e}", flush=True)
        raise HTTPException(401, "Invalid token")


def current_student_id(claims: dict = Depends(verified_claims),
                       db_adapter: DatabaseAdapter = Depends(get_db_adapter)) -> str:
    """Identity comes ONLY from the verified token — never from URL or body."""
    roles = claims.get("realm_access", {}).get("roles", [])
    if "student" not in roles:
        raise HTTPException(403, "Not a student account")
    try:
        return resolve_student_id(db_adapter, claims["iss"], claims["sub"])
    except PermissionError:
        raise HTTPException(403, "Account is not linked to a student")


@student_router.get("/api/me/exams/{exam_id}/report")
def my_report(exam_id: str,
              student_id: str = Depends(current_student_id),
              db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    report = db_adapter.db.report_revisions.find_one(
        {"exam_id": exam_id, "student_id": student_id, "state": "published"},
        sort=[("revision", -1)])
    if not report:
        # No score data of any kind while processing.
        return {"status": "processing"}
    return {"status": "ready", "score": report["score"],
            "maximum": report["maximum"], "percentage": report["percentage"],
            "answers": report["awards"], "revision": report["revision"]}


@student_router.post("/api/me/exams/{exam_id}/rough-sheet")
async def upload_my_rough_sheet(exam_id: str, file: UploadFile = File(...),
                                student_id: str = Depends(current_student_id),
                                db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    """Attach a photo of rough work — only to the authenticated student's own
    sheet, never selectable by URL or body (rule: a name on a sheet never
    grants account access; here, an account never reaches another sheet)."""
    if file.content_type not in ALLOWED_ROUGH_SHEET_TYPES:
        raise HTTPException(422, "Choose a PNG or JPEG image.")
    data = await file.read()
    if not data or len(data) > MAX_ROUGH_SHEET_BYTES:
        raise HTTPException(422, f"File must be non-empty and under {MAX_ROUGH_SHEET_BYTES} bytes.")

    sheet = db_adapter.db.sheets.find_one({"exam_id": exam_id, "student_id": student_id})
    if not sheet:
        raise HTTPException(404, "No sheet found for this exam on your account.")

    from cde.storage import upload as upload_to_storage
    storage_key = upload_to_storage(sheet["_id"], data, content_type=file.content_type)

    with db_adapter.unit_of_work() as s:
        updated = db_adapter.db.sheets.find_one_and_update(
            {"_id": sheet["_id"]},
            {"$set": {"rough_sheet_path": storage_key,
                      "rough_sheet_status": "uploaded",
                      "rough_sheet_uploaded_at": datetime.utcnow()},
             "$inc": {"rough_sheet_upload_count": 1}},
            session=s, return_document=ReturnDocument.AFTER)
        if updated.get("state") == "published":
            from cde.jobs.handlers import _maybe_enqueue_diagnosis
            _maybe_enqueue_diagnosis(db_adapter, sheet["_id"], session=s)
    return {"status": "uploaded"}


@student_router.post("/api/me/exams/{exam_id}/rough-sheet/none")
def declare_no_rough_sheet(exam_id: str,
                           student_id: str = Depends(current_student_id),
                           db_adapter: DatabaseAdapter = Depends(get_db_adapter)):
    """Explicit "I have no rough work" — distinct from simply never uploading,
    so the diagnosis pipeline knows to abstain rather than wait indefinitely."""
    sheet = db_adapter.db.sheets.find_one({"exam_id": exam_id, "student_id": student_id})
    if not sheet:
        raise HTTPException(404, "No sheet found for this exam on your account.")
    with db_adapter.unit_of_work() as s:
        db_adapter.db.sheets.update_one(
            {"_id": sheet["_id"]},
            {"$set": {"rough_sheet_status": "none_provided",
                      "rough_sheet_uploaded_at": datetime.utcnow()}},
            session=s)
    return {"status": "none_provided"}
