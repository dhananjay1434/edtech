import os
import re

path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\cde\routes\beta.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Add get_current_user to imports if not there
if "get_current_user" not in text:
    text = text.replace("from cde.auth import get_auth_port", "from cde.auth import get_auth_port, get_current_user")

# Replace the get_image_from_gridfs signature
old_sig = "async def get_image_from_gridfs(file_id: str, db_adapter: DatabaseAdapter = Depends(get_db_adapter)):"
new_sig = "async def get_image_from_gridfs(file_id: str, db_adapter: DatabaseAdapter = Depends(get_db_adapter), user=Depends(get_current_user)):"
text = text.replace(old_sig, new_sig)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
