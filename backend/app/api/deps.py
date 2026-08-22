import json
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.config import settings
from app.core.database import get_db
from app.models.domain import User, Organization, ApiKey, AuditLog
from app.schemas.auth import TokenData
from app.core.security import ROLE_PERMISSIONS, get_role_permissions, hash_api_key_secret

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(roles: List[str]):
    """
    Enforces that the current user has one of the required RBAC roles.
    Includes backward-compatibility synonyms.
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_role = (current_user.role or "").upper()
        if user_role == "SUPER_ADMIN":
            return current_user
            
        synonyms = {
            "INSTITUTION_ADMIN": ["ORGANIZATION_ADMIN", "ORGANIZATION_OWNER"],
            "ORGANIZATION_ADMIN": ["INSTITUTION_ADMIN", "ORGANIZATION_OWNER"],
            "ORGANIZATION_OWNER": ["INSTITUTION_ADMIN", "ORGANIZATION_ADMIN"],
            "ISSUER": ["CREDENTIAL_ISSUER"],
            "CREDENTIAL_ISSUER": ["ISSUER"],
            "VERIFIER": ["VERIFICATION_OFFICER"],
            "VERIFICATION_OFFICER": ["VERIFIER"],
        }
        
        for required_role in roles:
            if user_role == required_role or user_role in synonyms.get(required_role, []):
                return current_user
                
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Access denied: Required role [{', '.join(roles)}], your role is [{user_role}]"
        )
    return role_checker

def require_permission(permission: str):
    """
    Enforces granular backend RBAC permission.
    """
    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role == "SUPER_ADMIN":
            return current_user
            
        user_perms = get_role_permissions(current_user.role)
        
        if current_user.permissions:
            try:
                custom_p = json.loads(current_user.permissions)
                if isinstance(custom_p, list):
                    user_perms = list(set(user_perms + custom_p))
            except Exception:
                pass
                
        if permission in user_perms:
            return current_user
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Missing required permission '{permission}'"
        )
    return permission_checker

def get_api_key_identity(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Optional[ApiKey]:
    if not x_api_key:
        return None
        
    hashed = hash_api_key_secret(x_api_key.strip())
    api_key_rec = db.query(ApiKey).filter(
        ApiKey.hashed_secret == hashed,
        ApiKey.status == "ACTIVE"
    ).first()
    
    if not api_key_rec:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or revoked API Key")
        
    return api_key_rec

def get_tenant_context(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> dict:
    """
    Resolves the authenticated identity (either JWT Bearer token or API Key header).
    """
    if x_api_key:
        hashed = hash_api_key_secret(x_api_key.strip())
        api_key_rec = db.query(ApiKey).filter(
            ApiKey.hashed_secret == hashed,
            ApiKey.status == "ACTIVE"
        ).first()
        if not api_key_rec:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or revoked API Key")
            
        from datetime import datetime, timezone
        api_key_rec.last_used_at = datetime.now(timezone.utc)
        db.commit()
        
        return {
            "type": "API_KEY",
            "user": None,
            "api_key": api_key_rec,
            "organization_id": api_key_rec.organization_id,
            "is_super_admin": False,
            "name": f"API Client ({api_key_rec.name})",
            "email": None
        }
        
    if token:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            email: str = payload.get("sub")
            if email:
                user = db.query(User).filter(User.email == email).first()
                if user and user.is_active:
                    return {
                        "type": "USER",
                        "user": user,
                        "api_key": None,
                        "organization_id": user.institution_id,
                        "is_super_admin": user.role == "SUPER_ADMIN",
                        "name": user.name,
                        "email": user.email
                    }
        except Exception:
            pass
            
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (Bearer JWT token or X-API-Key header)",
        headers={"WWW-Authenticate": "Bearer"}
    )

def get_optional_tenant_context(
    request: Request,
    db: Session = Depends(get_db),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> dict:
    """
    Optional tenant resolver for public verification endpoints.
    Allows seamless public guest queries while recording full caller identities if provided.
    """
    if x_api_key:
        hashed = hash_api_key_secret(x_api_key.strip())
        api_key_rec = db.query(ApiKey).filter(
            ApiKey.hashed_secret == hashed,
            ApiKey.status == "ACTIVE"
        ).first()
        if api_key_rec:
            from datetime import datetime, timezone
            api_key_rec.last_used_at = datetime.now(timezone.utc)
            db.commit()
            return {
                "type": "API_KEY",
                "user": None,
                "api_key": api_key_rec,
                "organization_id": api_key_rec.organization_id,
                "is_super_admin": False,
                "name": f"API Client ({api_key_rec.name})",
                "email": None
            }

    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ")[1].strip()
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            email: str = payload.get("sub")
            if email:
                user = db.query(User).filter(User.email == email).first()
                if user and user.is_active:
                    return {
                        "type": "USER",
                        "user": user,
                        "api_key": None,
                        "organization_id": user.institution_id,
                        "is_super_admin": user.role == "SUPER_ADMIN",
                        "name": user.name,
                        "email": user.email
                    }
        except Exception:
            pass

    return {
        "type": "PUBLIC_GUEST",
        "user": None,
        "api_key": None,
        "organization_id": None,
        "is_super_admin": False,
        "name": "Public Recruiter / Verifier",
        "email": None
    }

def log_audit_trail(
    db: Session,
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    user_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    result: str = "SUCCESS",
    metadata: Optional[dict] = None
):
    try:
        entry = AuditLog(
            user_id=user_id,
            organization_id=organization_id,
            action=action,
            resource=resource,
            resource_id=str(resource_id) if resource_id is not None else None,
            ip_address=ip_address,
            user_agent=user_agent,
            result=result,
            metadata_json=json.dumps(metadata) if metadata else None
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        print(f"Audit log recording error: {e}")
