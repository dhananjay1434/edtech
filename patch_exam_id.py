path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\web\src\main.tsx"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace('examId="test-exam"', 'examId="test-exam-1"')
text = text.replace('to="/student/exams/test-exam"', 'to="/student/exams/test-exam-1"')

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
