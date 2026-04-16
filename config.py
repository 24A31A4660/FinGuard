import os
from pydantic_settings import BaseSettings, SettingsConfigDict

# Detect Vercel serverless (read-only filesystem — use /tmp for DB)
_IS_VERCEL = os.environ.get("VERCEL", "") == "1"
_DEFAULT_DB = "sqlite:////tmp/ai_finance.db" if _IS_VERCEL else "sqlite:///./ai_finance.db"

class Settings(BaseSettings):
    """
    Production-ready settings management using Environmental Variables.
    Defaults allow zero-config execution.
    """
    
    # Flask Settings
    flask_env: str = "development"
    debug: bool = not _IS_VERCEL
    port: int = 5000
    secret_key: str = "dev-key-default-replace-me-in-prod"
    jwt_secret_key: str = "jwt-secret-key-replace-me"
    jwt_access_token_expires: int = 86400  # 1 day in seconds
    google_client_id: str = "" # Optional, set from ENV
    
    # Database
    database_url: str = _DEFAULT_DB
    
    # ML Engine Thresholds
    contamination_rate: float = 0.05
    risk_threshold_block: float = 85.0
    risk_threshold_otp: float = 60.0
    
    # Alerting
    alert_provider: str = "console"
    alert_email_recipient: str = "alerts@finguard.internal"
    
    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Singleton settings instance
settings = Settings()

# Ensure database directory exists if using SQLite
if settings.database_url.startswith("sqlite:///"):
    db_path = settings.database_url.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
