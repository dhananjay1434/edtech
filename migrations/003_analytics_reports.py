def up(db):
    print("Running 003_analytics_reports up()")
    db.reports.create_index([("exam_id", 1), ("student_id", 1)])

def down(db):
    print("Running 003_analytics_reports down()")
    db.reports.drop_index("exam_id_1_student_id_1")
