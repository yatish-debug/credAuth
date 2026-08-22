import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.domain import ApiKey, User, Organization
from app.schemas.domain import ApiKeyCreate, ApiKeyResponse, ApiKeySecretResponse
from app.api.deps import get_current_active_user, require_role, log_audit_trail
from app.core.security import generate_api_key

router = APIRouter()

@router.get("/", response_model=List[ApiKeyResponse])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(ApiKey)
    if current_user.role != "SUPER_ADMIN":
        query = query.filter(ApiKey.organization_id == current_user.institution_id)
        
    keys = query.order_by(ApiKey.id.desc()).all()
    results = []
    for k in keys:
        perms = []
        if k.permissions_json:
            try:
                perms = json.loads(k.permissions_json)
            except Exception:
                pass
        results.append({
            "id": k.id,
            "key_id": k.key_id,
            "name": k.name,
            "environment": k.environment or "TEST",
            "prefix": k.prefix or "ssbt_...",
            "permissions": perms,
            "rate_limit_per_minute": k.rate_limit_per_minute or 120,
            "last_used_at": k.last_used_at,
            "expires_at": k.expires_at,
            "status": k.status or "ACTIVE",
            "created_at": k.created_at
        })
    return results

@router.post("/", response_model=ApiKeySecretResponse)
def create_api_key(
    key_in: ApiKeyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    org_id = current_user.institution_id
    if not org_id:
        first_org = db.query(Organization).first()
        org_id = first_org.id if first_org else 1
        
    raw_key, hashed_secret, key_id, prefix = generate_api_key(key_in.environment)
    
    new_key = ApiKey(
        key_id=key_id,
        organization_id=org_id,
        name=key_in.name,
        environment=key_in.environment.upper(),
        hashed_secret=hashed_secret,
        prefix=prefix,
        permissions_json=json.dumps(key_in.permissions or ["credential:read", "credential:verify"]),
        rate_limit_per_minute=key_in.rate_limit_per_minute or 120,
        status="ACTIVE"
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    
    log_audit_trail(
        db=db,
        action="API_KEY_CREATED",
        resource="API_KEY",
        resource_id=key_id,
        user_id=current_user.id,
        organization_id=org_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"name": key_in.name, "env": key_in.environment}
    )
    
    return {
        "id": new_key.id,
        "key_id": new_key.key_id,
        "name": new_key.name,
        "environment": new_key.environment,
        "raw_api_key": raw_key, # Transmitted once
        "prefix": new_key.prefix,
        "permissions": key_in.permissions or [],
        "rate_limit_per_minute": new_key.rate_limit_per_minute,
        "created_at": new_key.created_at
    }

@router.post("/{key_id}/rotate", response_model=ApiKeySecretResponse)
def rotate_api_key(
    key_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    key_rec = db.query(ApiKey).filter(
        (ApiKey.key_id == key_id) | (ApiKey.id == (int(key_id) if key_id.isdigit() else -1))
    ).first()
    if not key_rec:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    if current_user.role != "SUPER_ADMIN" and key_rec.organization_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    raw_key, hashed_secret, new_key_id, prefix = generate_api_key(key_rec.environment)
    key_rec.hashed_secret = hashed_secret
    key_rec.prefix = prefix
    key_rec.created_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(key_rec)
    
    log_audit_trail(
        db=db,
        action="API_KEY_ROTATED",
        resource="API_KEY",
        resource_id=key_rec.key_id,
        user_id=current_user.id,
        organization_id=key_rec.organization_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS"
    )
    
    perms = []
    if key_rec.permissions_json:
        try:
            perms = json.loads(key_rec.permissions_json)
        except Exception:
            pass
            
    return {
        "id": key_rec.id,
        "key_id": key_rec.key_id,
        "name": key_rec.name,
        "environment": key_rec.environment,
        "raw_api_key": raw_key,
        "prefix": key_rec.prefix,
        "permissions": perms,
        "rate_limit_per_minute": key_rec.rate_limit_per_minute,
        "created_at": key_rec.created_at
    }

@router.delete("/{key_id}")
def revoke_api_key(
    key_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    key_rec = db.query(ApiKey).filter(
        (ApiKey.key_id == key_id) | (ApiKey.id == (int(key_id) if key_id.isdigit() else -1))
    ).first()
    if not key_rec:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    if current_user.role != "SUPER_ADMIN" and key_rec.organization_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    key_rec.status = "REVOKED"
    db.commit()
    
    log_audit_trail(
        db=db,
        action="API_KEY_REVOKED",
        resource="API_KEY",
        resource_id=key_rec.key_id,
        user_id=current_user.id,
        organization_id=key_rec.organization_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS"
    )
    return {"status": "success", "message": "API key revoked successfully"}
