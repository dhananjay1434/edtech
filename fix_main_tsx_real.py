path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\web\src\main.tsx"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

import re
# Correctly use regex to remove the teacher block
text = re.sub(r"\s*\{\s*path:\s*'teacher'[\s\S]*?\},", "", text)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
