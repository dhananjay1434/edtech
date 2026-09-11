path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\cde\routes\student.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    'def verified_claims(authorization: str = Header(...),\n                    auth_port: AuthorizationPort = Depends(get_auth_port)) -> dict:\n    if not authorization.startswith("Bearer "):',
    'def verified_claims(authorization: str = Header(...),\n                    auth_port: AuthorizationPort = Depends(get_auth_port)) -> dict:\n    print(f"VERIFYING TOKEN: {authorization[:20]}...", flush=True)\n    if not authorization.startswith("Bearer "):'
)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
