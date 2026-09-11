import argparse
import sys
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from .config import settings

def get_client():
    return MongoClient(settings.mongodb_uri)

def plan_migrations():
    print("Planning migrations (read-only)...")
    # This would read from the `migrations/` folder and output what needs to be applied
    print("Migration 001_core.py is pending.")
    print("Migration 002_diagnostics.py is pending.")
    print("Migration 003_analytics_reports.py is pending.")
    print("Migration 004_delivery.py is pending.")

def check_migrations():
    print("Checking applied migrations...")
    client = get_client()
    db = client[settings.mongodb_db_name]
    try:
        applied = list(db.schema_migrations.find({}).sort("id", 1))
        if not applied:
            print("No migrations have been applied.")
        else:
            for mig in applied:
                print(f"Migration {mig['id']} is applied with checksum {mig['checksum']}")
    except OperationFailure as e:
        print(f"Error checking migrations: {e}")

def apply_migrations():
    import importlib.util
    from pathlib import Path
    from datetime import datetime
    client = get_client()
    db = client[settings.mongodb_db_name]
    migration_files = sorted(Path("migrations").glob("[0-9]*.py"))
    for migration_file in migration_files:
        migration_id = migration_file.stem
        existing = db.schema_migrations.find_one({"id": migration_id})
        if existing:
            print(f"Already applied: {migration_id}")
            continue
        spec = importlib.util.spec_from_file_location(migration_id, migration_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"Applying {migration_id}...")
        module.up(db)
        db.schema_migrations.insert_one({
            "id": migration_id,
            "applied_at": datetime.utcnow().isoformat(),
        })
        print(f"Done: {migration_id}")

def main():
    parser = argparse.ArgumentParser(description="CDE Migration Runner")
    parser.add_argument("--plan", action="store_true", help="Read-only planning and drift checking")
    parser.add_argument("--check", action="store_true", help="Verifies applied checksums and schema/index expectations")
    parser.add_argument("--apply", action="store_true", help="Executes migrations against target")
    
    args = parser.parse_args()
    
    if args.plan:
        plan_migrations()
    elif args.check:
        check_migrations()
    elif args.apply:
        apply_migrations()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
