from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_role_permissions
from app.core.config import settings
from app.models.domain import User, Organization
from app.schemas.auth import Token
from app.schemas.domain import UserResponse
from app.api import deps

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    request: Request,
    db: Session = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = db.query(User).filter(User.email == form_data.username.strip()).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        deps.log_audit_trail(
            db=db,
            action="LOGIN_FAILURE",
            resource="USER_AUTH",
            resource_id=form_data.username,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            result="FAILURE",
            metadata={"reason": "Invalid credentials"}
        )
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    if not user.is_active:
        deps.log_audit_trail(
            db=db,
            action="LOGIN_BLOCKED",
            resource="USER_AUTH",
            resource_id=str(user.id),
            user_id=user.id,
            organization_id=user.institution_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            result="DENIED",
            metadata={"reason": "Account disabled"}
        )
        raise HTTPException(status_code=400, detail="This account has been disabled. Please contact administrator.")
        
    perms = get_role_permissions(user.role)
    org_name = None
    if user.institution_id:
        org = db.query(Organization).filter(Organization.id == user.institution_id).first()
        org_name = org.name if org else None

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email,
        role=user.role,
        org_id=user.institution_id,
        permissions=perms,
        expires_delta=access_token_expires
    )
    
    deps.log_audit_trail(
        db=db,
        action="LOGIN_SUCCESS",
        resource="USER_AUTH",
        resource_id=str(user.id),
        user_id=user.id,
        organization_id=user.institution_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"role": user.role, "organization": org_name}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role,
        "organization_id": user.institution_id,
        "organization_name": org_name,
        "permissions": perms
    }

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(deps.get_current_active_user)):
    return current_user
