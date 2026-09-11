import re

path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\web\src\main.tsx"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Remove the import
text = re.sub(r"import\s*\{\s*TeacherUploadBay\s*\}\s*from\s*['\"]./features/teacher/TeacherUploadBay['\"];\n?", "", text)

# Remove the teacher route block
# We'll use a regex that looks for the exact teacher route block
teacher_route = r"""      \{
        path: 'teacher',
        element: <RequirePortal role="teacher" />,
        children: \[
            \{ path: 'exams', element: <Navigate to="/teacher/exams/test-exam/upload" replace /> \},
            \{ path: 'exams/:examId/upload', element: <TeacherUploadBay examId="test-exam" maxFileBytes=\{50000000\} /> \}
        \]
      \},
"""

text = text.replace(teacher_route, "")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
