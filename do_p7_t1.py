import os
import glob
import shutil

base_dir = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0"
files_to_delete = [
    "cde/workflows.py",
    "cde/activities.py",
    "cde/worker.py",
    "cde/dispatcher.py",
    "run_worker.py",
    "cde/omr.py",
    "cde/omr_adapter.py",
    "cde/routes/alpha.py",
    "cde/routes/gamma.py",
]

for f in files_to_delete:
    p = os.path.join(base_dir, f.replace('/', os.sep))
    if os.path.exists(p):
        os.remove(p)
        print(f"Deleted {p}")

teacher_dir = os.path.join(base_dir, "web", "src", "features", "teacher")
if os.path.exists(teacher_dir):
    shutil.rmtree(teacher_dir)
    print(f"Deleted {teacher_dir}")

# Scratch scripts
scratch_patterns = ["diag_*.py", "fix_*.py", "patch_v130.py", "eval_v130.py", "chk_gt.py", "zip_project.py", "run_batch*.py"]
for pat in scratch_patterns:
    for p in glob.glob(os.path.join(base_dir, pat)):
        os.remove(p)
        print(f"Deleted scratch script {p}")
