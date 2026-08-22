from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    PROJECT_NAME: str = "CredAuth Credential Trust & Fraud Intelligence Platform"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "production"
    
    # Security & Authentication
    JWT_SECRET: str = "SUPER_SECRET_ENTERPRISE_KEY_CHANGE_IN_PRODUCTION_9823471092384"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/credverify.db"
    
    # File Uploads & Storage
    UPLOAD_DIRECTORY: str = "storage/uploads"
    STORAGE_PDF_DIRECTORY: str = "storage/certificates"
    STORAGE_QR_DIRECTORY: str = "storage/qr"
    MAX_UPLOAD_SIZE: int = 10485760 # 10 MB
    
    # Webhooks
    WEBHOOK_DEFAULT_TIMEOUT_SECONDS: int = 10
    WEBHOOK_RETRY_LIMIT: int = 3

    # Frontend & CORS
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: Optional[List[str]] = None

    # AI & Forensics
    OCR_ENGINE: str = "TESSERACT"
    OCR_CONFIDENCE_THRESHOLD: float = 0.85

    # Trust Engine Weights
    WEIGHT_ISSUER_AUTHENTICITY: float = 0.25
    WEIGHT_CRYPTO_SIGNATURE: float = 0.20
    WEIGHT_REGISTRY_MATCH: float = 0.20
    WEIGHT_QR_VALIDATION: float = 0.15
    WEIGHT_DOCUMENT_FORENSICS: float = 0.10
    WEIGHT_METADATA_CONSISTENCY: float = 0.10

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
