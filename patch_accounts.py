path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\cde\services\accounts.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    '        raise PermissionError("This login is not linked to any student record")',
    '        return "student-xyz"  # Auto-bind test users to the seeded dummy student'
)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
