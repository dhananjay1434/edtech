path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\cde\routes\student.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    '    except Exception:\n        raise HTTPException(401, "Invalid token")',
    '    except Exception as e:\n        print(f"DEBUG VERIFIED CLAIMS: {e}", flush=True)\n        raise HTTPException(401, "Invalid token")'
)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
