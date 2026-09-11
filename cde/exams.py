from fastapi import HTTPException
from typing import List, Dict, Any
from .db import DatabaseAdapter
from .auth import UserContext, AuthorizationPort

class ExamsService:
    def __init__(self, db_adapter: DatabaseAdapter):
        self.db_adapter = db_adapter
        self.db = db_adapter.db

    def list_exams(self, user: UserContext) -> List[Dict[str, Any]]:
        if "operator" in user.roles:
            exams = list(self.db.exams.find({}))
        else:
            exams = list(self.db.exams.find({"_id": {"$in": user.assignments}}))
            
        for exam in exams:
            exam["id"] = exam.pop("_id")
        return exams

    def get_exam(self, exam_id: str, user: UserContext, auth_port: AuthorizationPort) -> Dict[str, Any]:
        auth_port.authorize_exam_action(user, exam_id)
        exam = self.db.exams.find_one({"_id": exam_id})
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        exam["id"] = exam.pop("_id")
        return exam

    def publish_exam(self, exam_id: str, user: UserContext, auth_port: AuthorizationPort):
        auth_port.authorize_exam_action(user, exam_id, required_role="publisher")
        
        with self.db_adapter.unit_of_work() as session:
            exam = self.db.exams.find_one({"_id": exam_id}, session=session)
            if not exam:
                raise HTTPException(status_code=404, detail="Exam not found")
                
            if exam.get("status") == "published":
                raise HTTPException(status_code=400, detail="Exam already published")
                
            self.db.exams.update_one(
                {"_id": exam_id},
                {"$set": {"status": "published"}},
                session=session
            )
            return {"status": "published"}
