path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\web\src\main.tsx"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Add index redirects for admin and student portals
text = text.replace(
    "children: [\n            { path: 'setup', element: <AdminConsole /> },",
    "children: [\n            { index: true, element: <Navigate to=\"setup\" replace /> },\n            { path: 'setup', element: <AdminConsole /> },"
)

text = text.replace(
    "children: [\n            { path: 'exams', element: <Navigate to=\"/student/exams/test-exam\" replace /> },",
    "children: [\n            { index: true, element: <Navigate to=\"exams\" replace /> },\n            { path: 'exams', element: <Navigate to=\"/student/exams/test-exam\" replace /> },"
)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
