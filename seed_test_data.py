import os
from pymongo import MongoClient

# Connect to local MongoDB
uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
db_name = os.environ.get("MONGODB_DB_NAME", "cde_db")
client = MongoClient(uri)
db = client[db_name]

# 1. Create a dummy Exam
db.exams.update_one(
    {"_id": "test-exam-1"},
    {"$set": {
        "title": "Math 101 Midterm",
        "status": "published",
        "answer_key": [
            {"question_number": 1, "correct_option": "A", "question_text": "Solve: 2x + 4 = 10"},
            {"question_number": 2, "correct_option": "C", "question_text": "What is the derivative of x^2?"}
        ]
    }},
    upsert=True
)

# 2. Create a dummy Submission (with incorrect answers so Gemini triggers)
db.submissions.update_one(
    {"_id": "test-sub-1"},
    {"$set": {
        "exam_id": "test-exam-1",
        "student_id": "student-xyz",
        "state": "Graded (Draft)",
        "answers": [
            {"question_number": 1, "state": "incorrect", "selected_option": "B"},
            {"question_number": 2, "state": "incorrect", "selected_option": "D"}
        ]
    }},
    upsert=True
)

print("✅ Database seeded! You can now test with:")
print("   Exam ID: test-exam-1")
print("   Submission ID: test-sub-1")
