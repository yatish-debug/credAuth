from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db, Base, engine
from app.core.security import get_password_hash
from app.models.domain import (
    User, Organization, Credential, VerificationRequest, 
    VerificationResult, FraudCase, ApiKey, Webhook, 
    WebhookDelivery, MonitoringSubscription, MonitoringAlert, AuditLog
)
from app.api import deps

router = APIRouter()

class ResetDatabaseRequest(BaseModel):
    confirm_reset: bool
    super_admin_email: str = "admin@ssbt.demo"
    super_admin_password: str = "admin123"
    super_admin_name: str = "CredAuth Root Super Admin"

@router.post("/reset-database")
def reset_database_to_zero(
    body: ResetDatabaseRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.require_role(["SUPER_ADMIN"]))
):
    """
    Wipes all demo data across all tables and resets the platform database to a 
    clean fresh state with ONLY ONE user (the root Super Admin).
    """
    if not body.confirm_reset:
        raise HTTPException(status_code=400, detail="Must explicitly set confirm_reset to true.")
        
    try:
        # Delete records in dependent order
        db.query(AuditLog).delete()
        db.query(MonitoringAlert).delete()
        db.query(MonitoringSubscription).delete()
        db.query(WebhookDelivery).delete()
        db.query(Webhook).delete()
        db.query(ApiKey).delete()
        db.query(FraudCase).delete()
        db.query(VerificationResult).delete()
        db.query(VerificationRequest).delete()
        db.query(Credential).delete()
        db.query(User).delete()
        db.query(Organization).delete()
        db.commit()
        
        # Create the single root Super Admin user
        super_admin = User(
            name=body.super_admin_name,
            email=body.super_admin_email.strip().lower(),
            password_hash=get_password_hash(body.super_admin_password),
            role="SUPER_ADMIN",
            institution_id=None,
            is_active=True
        )
        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)
        
        # Log clean reset
        deps.log_audit_trail(
            db=db,
            action="DATABASE_RESET_TO_ZERO",
            resource="SYSTEM_DATABASE",
            resource_id="0",
            user_id=super_admin.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            result="SUCCESS",
            metadata={
                "message": "Platform reset to 0. All demo organizations and credentials wiped.",
                "root_admin": super_admin.email
            }
        )
        
        return {
            "status": "CLEAN_DATABASE_RESET",
            "message": "All demo data has been wiped. Database reset to 0 with 1 Super Admin.",
            "super_admin": {
                "id": super_admin.id,
                "email": super_admin.email,
                "name": super_admin.name,
                "role": super_admin.role
            },
            "stats": {
                "organizations": 0,
                "credentials": 0,
                "verifications": 0,
                "fraud_cases": 0,
                "api_keys": 0,
                "webhooks": 0,
                "users": 1
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database reset error: {str(e)}")
