import os
import re

path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\cde\routes\beta.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Remove the upload_omr_sheet function
# We will just find the @beta_router.post("/api/omr/upload") and strip until the next route
import ast

# Alternatively, I can just use a regex
match = re.search(r"@beta_router\.post\(\"/api/omr/upload\"\).*?(?=@beta_router)", text, re.DOTALL)
if match:
    text = text.replace(match.group(0), "")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
