path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\cde\auth.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    '        except jwt.PyJWTError as e:\n            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")',
    '        except Exception as e:\n            print(f"JWT ERROR: {str(e)}", flush=True)\n            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")'
)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
