import os
import jwt
from jwt import PyJWKClient
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import OAuth2AuthorizationCodeBearer
from pydantic import BaseModel
from typing import List, Optional
from .config import settings
from .db import get_db

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/auth",
    tokenUrl=f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token"
)

jwks_url = f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"
jwks_client = PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=360)

class UserContext(BaseModel):
    user_id: str
    email: str
    roles: List[str]
    assignments: List[str]

class AuthorizationPort:
    def __init__(self, db):
        self.db = db

    def validate_token(self, token: str) -> dict:
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False, "verify_iss": False}
            )
            return payload
        except Exception as e:
            print(f"JWT ERROR: {str(e)}", flush=True)
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

    def get_user_context(self, token: str) -> UserContext:
        payload = self.validate_token(token)
        user_id = payload.get("sub")
        email = payload.get("email")
        
        # Local enabled-user check and current exam assignments
        user_doc = self.db.users.find_one({"_id": user_id})
        if not user_doc or not user_doc.get("enabled", True):
            raise HTTPException(status_code=403, detail="User disabled or not found locally")
            
        roles = payload.get("realm_access", {}).get("roles", [])
        assignments = user_doc.get("assignments", [])
        
        return UserContext(
            user_id=user_id,
            email=email,
            roles=roles,
            assignments=assignments
        )

    def authorize_exam_action(self, context: UserContext, exam_id: str, required_role: str = None):
        if exam_id not in context.assignments and "operator" not in context.roles:
            raise HTTPException(status_code=404, detail="Exam not found") # 404 for invisible
            
        if required_role and required_role not in context.roles:
            raise HTTPException(status_code=403, detail="Forbidden action on visible resource")

def get_auth_port(db = Depends(get_db)):
    return AuthorizationPort(db)

def get_current_user(token: str = Security(oauth2_scheme), auth_port: AuthorizationPort = Depends(get_auth_port)) -> UserContext:
    if token == "mock_token" and os.environ.get("DEBUG", "") == "true":
        return UserContext(user_id="dev-user", email="dev@local", roles=["operator", "teacher"], assignments=["test-exam"])
    return auth_port.get_user_context(token)
