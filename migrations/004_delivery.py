def up(db):
    print("Running 004_delivery up()")
    db.deliveries.create_index("submission_id", unique=True)

def down(db):
    print("Running 004_delivery down()")
    db.deliveries.drop_index("submission_id_1")
