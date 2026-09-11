from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "cde_db"
    
    keycloak_server_url: str = "http://localhost:8080"
    keycloak_realm: str = "cde"
    keycloak_client_id: str = "cde-app"
    keycloak_web_client_id: str = "cde-web"

    cde_verified_storage_root: str = "./verified_storage"

    # Read directly via os.environ by cde/diagnostics.py — declared here too
    # so pydantic-settings (extra="forbid" by default) doesn't reject a real
    # .env file that sets them.
    gemini_api_key: str = ""
    gemini_diagnostic_model: str = ""
    cde_verified_crop_root: str = "./verified_storage"
    cde_diagnostic_timeout_seconds: str = "45"

    s3_endpoint_url: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_bucket_name: str = "cde-uploads"
    
    temporal_target: str = "localhost:7233"
    
    class Config:
        env_file = ".env"

settings = Settings()
