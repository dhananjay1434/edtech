def up(db):
    print("Running 001_core up()")
    # Create necessary unique indexes
    db.users.create_index("email", unique=True)
    db.uploads.create_index([("exam_id", 1), ("idempotency_key", 1)], unique=True, sparse=True)
    db.exams.create_index("title")

def down(db):
    print("Running 001_core down()")
    # Drop indexes
    db.users.drop_index("email_1")
    db.uploads.drop_index("exam_id_1_idempotency_key_1")
    db.exams.drop_index("title_1")
