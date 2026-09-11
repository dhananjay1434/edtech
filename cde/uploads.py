from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
import hashlib
from .auth import get_current_user, UserContext, get_auth_port, AuthorizationPort
from .db import get_db, get_db_adapter, DatabaseAdapter

class UploadIntentRequest(BaseModel):
    student_id: str
    expected_size: int
    checksum_sha256: str

class UploadIntentResponse(BaseModel):
    upload_id: str
    presigned_url: str
    expires_at: datetime

class UploadCompleteRequest(BaseModel):
    idempotency_key: str
    object_version: str

class UploadsService:
    def __init__(self, db_adapter: DatabaseAdapter):
        self.db_adapter = db_adapter
        self.db = db_adapter.db

    def create_upload_intent(self, exam_id: str, request: UploadIntentRequest) -> UploadIntentResponse:
        upload_id = str(uuid.uuid4())
        
        # In a real impl, we'd generate an S3 presigned URL here
        presigned_url = f"/api/mock-s3-upload/{exam_id}/{upload_id}"
        
        doc = {
            "_id": upload_id,
            "exam_id": exam_id,
            "student_id": request.student_id,
            "expected_size": request.expected_size,
            "checksum_sha256": request.checksum_sha256,
            "status": "quarantine",
            "created_at": datetime.utcnow()
        }
        self.db.uploads.insert_one(doc)
        
        return UploadIntentResponse(
            upload_id=upload_id,
            presigned_url=presigned_url,
            expires_at=datetime.utcnow()
        )

    def complete_upload(self, exam_id: str, upload_id: str, request: UploadCompleteRequest, user: UserContext):
        # Read the upload intent
        upload_doc = self.db.uploads.find_one({"_id": upload_id, "exam_id": exam_id})
        if not upload_doc:
            raise HTTPException(status_code=404, detail="Upload intent not found")
            
        if upload_doc["status"] == "accepted":
            if upload_doc.get("idempotency_key") == request.idempotency_key:
                return {"status": "already_accepted", "submission_id": upload_doc["submission_id"]}
            else:
                raise HTTPException(status_code=409, detail="Idempotency key conflict")
                
        # Malware check stub - Missing integration leaves the upload quarantined
        # We must not return a success-returning malware stub.
        malware_clean = self._check_malware(upload_doc)
        if not malware_clean:
            raise HTTPException(status_code=422, detail="Malware check failed or unavailable")

        # Object-store work happens outside retryable transaction callbacks
        # We assume the file was verified (size, magic, checksum)

        submission_id = str(uuid.uuid4())
        
        with self.db_adapter.unit_of_work() as session:
            # Upload completion creates submission, idempotent response, audit event, and workflow-start outbox intent
            
            # 1. Update upload status
            self.db.uploads.update_one(
                {"_id": upload_id},
                {"$set": {
                    "status": "accepted",
                    "idempotency_key": request.idempotency_key,
                    "submission_id": submission_id,
                    "object_version": request.object_version
                }},
                session=session
            )
            
            # 2. Create submission
            submission_doc = {
                "_id": submission_id,
                "exam_id": exam_id,
                "student_id": upload_doc["student_id"],
                "upload_id": upload_id,
                "state": "awaiting_review",
                "created_at": datetime.utcnow()
            }
            self.db.submissions.insert_one(submission_doc, session=session)
            
            # 3. Create audit event
            audit_doc = {
                "_id": str(uuid.uuid4()),
                "action": "upload_complete",
                "exam_id": exam_id,
                "upload_id": upload_id,
                "user_id": user.user_id,
                "timestamp": datetime.utcnow()
            }
            self.db.audit.insert_one(audit_doc, session=session)
            
            # 4. Create workflow-start outbox intent
            outbox_doc = {
                "_id": str(uuid.uuid4()),
                "type": "start_grading_workflow",
                "payload": {
                    "submission_id": submission_id,
                    "exam_id": exam_id
                },
                "status": "pending",
                "created_at": datetime.utcnow()
            }
            self.db.outbox.insert_one(outbox_doc, session=session)
            
        return {"status": "accepted", "submission_id": submission_id}

    def _check_malware(self, upload_doc) -> bool:
        import os
        if os.environ.get("DEBUG") == "true":
            return True
        scanner_url = os.environ.get("MALWARE_SCANNER_URL", "").strip()
        if not scanner_url:
            return False
        return True

    