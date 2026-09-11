import os
import re

path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\cde\api.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace('allow_origins=["*"]', 'allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"]')

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
