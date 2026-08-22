import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.api.endpoints import (
    auth, organizations, institutions, certificates, verify, 
    evidence, fraud, apikeys, webhooks, monitoring, audit, 
    issuers, dashboard, verifiers, users, admin
)

# Create storage directories
os.makedirs(os.path.join("storage", "certificates"), exist_ok=True)
os.makedirs(os.path.join("storage", "qr"), exist_ok=True)
os.makedirs(os.path.join("storage", "uploads"), exist_ok=True)
os.makedirs(os.path.join("storage", "temp"), exist_ok=True)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CredAuth — B2B Credential Trust & Fraud Intelligence Platform API",
    description="""
    Enterprise Credential Trust, Verification and Fraud Intelligence Layer.
    Enables multi-tenant organizations to issue, verify, risk-score, monitor, and audit digital credentials.
    
    ### Key Features:
    - **Multi-Tenancy & RBAC**: Tenant isolation across universities, enterprises, and certification bodies.
    - **Modular Trust Engine**: Mathematical Credential Trust Score (0-100) & Issuer Trust Score.
    - **AI Document Forensics**: OCR anomaly detection, metadata extraction, tampering triage.
    - **Cryptographic Security**: RSA-PSS 2048-bit digital signatures and SHA-256 integrity digests.
    - **Enterprise API & Webhooks**: Programmatic B2B integration with API key management and signed webhook events.
    - **Fraud Investigation Center**: Case management, incident notes, and fraud resolution workflows.
    - **Continuous Monitoring**: Automatic alert tracking for revocation and integrity updates.
    """,
    version="2.5.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for generated certificates and QR codes
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# API Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication & RBAC"])
app.include_router(organizations.router, prefix=f"{settings.API_V1_STR}/organizations", tags=["Organization Management (Multi-Tenant)"])
app.include_router(institutions.router, prefix=f"{settings.API_V1_STR}/institutions", tags=["Institutions (Backward Compatibility)"])
app.include_router(certificates.router, prefix=f"{settings.API_V1_STR}/certificates", tags=["Credentials & Certificates"])
app.include_router(certificates.router, prefix=f"{settings.API_V1_STR}/credentials", tags=["Credentials API"])
app.include_router(verify.router, prefix=f"{settings.API_V1_STR}/verify", tags=["Verification & Trust Engine"])
app.include_router(evidence.router, prefix=f"{settings.API_V1_STR}/evidence", tags=["Verification Evidence Dossiers"])
app.include_router(fraud.router, prefix=f"{settings.API_V1_STR}/fraud", tags=["Fraud Intelligence Center"])
app.include_router(apikeys.router, prefix=f"{settings.API_V1_STR}/api-keys", tags=["Developer & API Keys"])
app.include_router(webhooks.router, prefix=f"{settings.API_V1_STR}/webhooks", tags=["Enterprise Webhooks"])
app.include_router(monitoring.router, prefix=f"{settings.API_V1_STR}/monitoring", tags=["Continuous Credential Monitoring"])
app.include_router(audit.router, prefix=f"{settings.API_V1_STR}/audit", tags=["Audit Trail & Governance"])
app.include_router(issuers.router, prefix=f"{settings.API_V1_STR}/issuers", tags=["Issuer Directory & Trust Profiles"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["Dashboard & Analytics"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["User Management & RBAC"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["Platform Admin & Reset"])
app.include_router(verifiers.router, prefix=f"{settings.API_V1_STR}/verifiers", tags=["Verifiers (Legacy Support)"])

@app.get("/")
def root():
    return {
        "platform": "CredAuth — B2B Credential Trust & Fraud Intelligence Platform",
        "status": "OPERATIONAL",
        "version": "2.5.0",
        "docs_url": f"{settings.API_V1_STR}/docs",
        "tagline": "Trust Every Credential."
    }
