def up(db):
    print("Running 002_diagnostics up()")
    db.diagnostics.create_index([("submission_id", 1), ("question_number", 1)])

def down(db):
    print("Running 002_diagnostics down()")
    db.diagnostics.drop_index("submission_id_1_question_number_1")
