import os
from pymongo import MongoClient

uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
db_name = os.environ.get("MONGODB_DB_NAME", "cde_db")
client = MongoClient(uri)
db = client[db_name]

db.report_revisions.update_one(
    {"_id": "report:test-sub-1:r1"},
    {"$set": {
        "exam_id": "test-exam-1",
        "student_id": "student-xyz",
        "state": "published",
        "revision": 1,
        "score": 0,
        "maximum": 8,
        "percentage": 0.0,
        "awards": [
            {"question_number": 1, "state": "incorrect", "awarded_marks": -1},
            {"question_number": 2, "state": "incorrect", "awarded_marks": -1}
        ]
    }},
    upsert=True
)
print("Report seeded!")
