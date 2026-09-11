path = r"C:\Users\bit\Downloads\cde_app_ready_v1.3.0\cde\auth.py"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    '            payload = jwt.decode(\n                token,\n                signing_key.key,\n                algorithms=["RS256"],\n                audience=settings.keycloak_client_id,\n                issuer=f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}"\n            )',
    '            payload = jwt.decode(\n                token,\n                signing_key.key,\n                algorithms=["RS256"],\n                options={"verify_aud": False, "verify_iss": False}\n            )'
)

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
