import os

path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\cde\routes\beta.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

if "from cde.auth import get_current_user" not in text:
    text = text.replace("from cde.db import get_db, get_db_adapter, DatabaseAdapter", 
                       "from cde.db import get_db, get_db_adapter, DatabaseAdapter\nfrom cde.auth import get_current_user")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
