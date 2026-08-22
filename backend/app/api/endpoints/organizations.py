import os
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.domain import Organization, User, Credential, ApiKey, Webhook, FraudCase
from app.schemas.domain import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse, 
    UserResponse, UserCreate
)
from app.api.deps import get_current_active_user, require_role, log_audit_trail
from app.crypto.signing import generate_institution_keypair

router = APIRouter()

def get_org_admin_email(db: Session, org_id: int) -> Optional[str]:
    admin = db.query(User).filter(
        User.institution_id == org_id,
        User.role.in_(["ORGANIZATION_OWNER", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"])
    ).first()
    return admin.email if admin else None

@router.get("/", response_model=List[OrganizationResponse])
def get_organizations(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    org_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List organizations. Super admins see all; organization admins see their own.
    """
    query = db.query(Organization)
    if current_user.role != "SUPER_ADMIN":
        query = query.filter(Organization.id == current_user.institution_id)
    if status_filter:
        query = query.filter(Organization.status == status_filter.upper())
    if org_type:
        query = query.filter(Organization.organization_type == org_type.upper())
        
    orgs = query.order_by(Organization.id.desc()).offset(skip).limit(limit).all()
    results = []
    for org in orgs:
        admin_email = get_org_admin_email(db, org.id)
        cert_count = db.query(Credential).filter(Credential.institution_id == org.id).count()
        
        # Ensure org has keys
        if not org.public_key or not org.private_key:
            priv, pub, fp = generate_institution_keypair()
            org.private_key = priv
            org.public_key = pub
            org.key_fingerprint = fp
            db.commit()
            db.refresh(org)
            
        org_dict = {
            "id": org.id,
            "name": org.name,
            "institution_code": org.institution_code,
            "organization_type": org.organization_type or "UNIVERSITY",
            "registration_number": org.registration_number,
            "official_domain": org.official_domain,
            "description": org.description,
            "contact_email": org.contact_email,
            "contact_phone": org.contact_phone,
            "address": org.address,
            "logo_url": org.logo_url,
            "verification_status": org.verification_status,
            "status": org.status or "ACTIVE",
            "trust_score": org.trust_score or 95.0,
            "key_algorithm": org.key_algorithm or "RSA-2048",
            "key_fingerprint": org.key_fingerprint,
            "public_key": org.public_key,
            "features_config": org.features_config,
            "admin_email": admin_email,
            "total_credentials": cert_count,
            "total_certificates": cert_count,
            "created_at": org.created_at,
            "updated_at": org.updated_at
        }
        results.append(org_dict)
    return results

@router.post("/", response_model=OrganizationResponse)
def create_organization(
    org_in: OrganizationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN"]))
):
    """
    Platform Super Admin creates a new B2B Organization/Tenant.
    """
    existing = db.query(Organization).filter(Organization.institution_code == org_in.institution_code.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Organization code already registered")
        
    private_key, public_key, fingerprint = generate_institution_keypair()
    
    features_json = json.dumps(org_in.features.dict()) if org_in.features else json.dumps({
        "suspicious_threshold": 0.5,
        "allow_revocation": True,
        "allow_reinstate": True,
        "require_revocation_reason": True,
        "qr_verification_enabled": True,
        "ocr_document_check_enabled": True,
        "digital_signatures_enabled": True,
        "signature_algorithm": "RSA-PSS-SHA256"
    })
    
    new_org = Organization(
        name=org_in.name,
        institution_code=org_in.institution_code.strip(),
        organization_type=org_in.organization_type or "UNIVERSITY",
        registration_number=org_in.registration_number,
        official_domain=org_in.official_domain,
        description=org_in.description,
        contact_email=org_in.contact_email,
        contact_phone=org_in.contact_phone,
        address=org_in.address,
        logo_url=org_in.logo_url,
        verification_status=org_in.verification_status or "VERIFIED",
        status=org_in.status or "ACTIVE",
        trust_score=95.0,
        public_key=public_key,
        private_key=private_key,
        key_algorithm="RSA-2048",
        key_fingerprint=fingerprint,
        features_config=features_json
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    
    # Assign Organization Owner / Admin if credentials provided
    if org_in.admin_email and org_in.admin_password:
        admin_user = db.query(User).filter(User.email == org_in.admin_email.strip()).first()
        if admin_user:
            admin_user.institution_id = new_org.id
            admin_user.role = "ORGANIZATION_ADMIN"
            admin_user.password_hash = get_password_hash(org_in.admin_password)
            if org_in.admin_name:
                admin_user.name = org_in.admin_name
        else:
            admin_user = User(
                name=org_in.admin_name or f"{new_org.name} Administrator",
                email=org_in.admin_email.strip(),
                password_hash=get_password_hash(org_in.admin_password),
                role="ORGANIZATION_ADMIN",
                institution_id=new_org.id,
                is_active=True
            )
            db.add(admin_user)
        db.commit()

    log_audit_trail(
        db=db,
        action="ORGANIZATION_CREATED",
        resource="ORGANIZATION",
        resource_id=str(new_org.id),
        user_id=current_user.id,
        organization_id=new_org.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"org_code": new_org.institution_code, "name": new_org.name}
    )
    
    return {
        "id": new_org.id,
        "name": new_org.name,
        "institution_code": new_org.institution_code,
        "organization_type": new_org.organization_type,
        "registration_number": new_org.registration_number,
        "official_domain": new_org.official_domain,
        "description": new_org.description,
        "contact_email": new_org.contact_email,
        "contact_phone": new_org.contact_phone,
        "address": new_org.address,
        "logo_url": new_org.logo_url,
        "verification_status": new_org.verification_status,
        "status": new_org.status,
        "trust_score": new_org.trust_score,
        "key_algorithm": new_org.key_algorithm,
        "key_fingerprint": new_org.key_fingerprint,
        "public_key": new_org.public_key,
        "features_config": new_org.features_config,
        "admin_email": org_in.admin_email,
        "total_credentials": 0,
        "total_certificates": 0,
        "created_at": new_org.created_at,
        "updated_at": new_org.updated_at
    }

@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "SUPER_ADMIN" and current_user.institution_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied to tenant organization")
        
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    admin_email = get_org_admin_email(db, org.id)
    cert_count = db.query(Credential).filter(Credential.institution_id == org.id).count()
    
    return {
        "id": org.id,
        "name": org.name,
        "institution_code": org.institution_code,
        "organization_type": org.organization_type or "UNIVERSITY",
        "registration_number": org.registration_number,
        "official_domain": org.official_domain,
        "description": org.description,
        "contact_email": org.contact_email,
        "contact_phone": org.contact_phone,
        "address": org.address,
        "logo_url": org.logo_url,
        "verification_status": org.verification_status,
        "status": org.status or "ACTIVE",
        "trust_score": org.trust_score or 95.0,
        "key_algorithm": org.key_algorithm or "RSA-2048",
        "key_fingerprint": org.key_fingerprint,
        "public_key": org.public_key,
        "features_config": org.features_config,
        "admin_email": admin_email,
        "total_credentials": cert_count,
        "total_certificates": cert_count,
        "created_at": org.created_at,
        "updated_at": org.updated_at
    }

@router.put("/{org_id}", response_model=OrganizationResponse)
def update_organization(
    org_id: int,
    org_in: OrganizationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    if current_user.role != "SUPER_ADMIN" and current_user.institution_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied to tenant organization")
        
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    for field, val in org_in.dict(exclude_unset=True).items():
        if field == "features" and val:
            org.features_config = json.dumps(val)
        elif hasattr(org, field) and val is not None and field not in ["admin_email", "admin_name", "admin_password", "features"]:
            setattr(org, field, val)
            
    if org_in.admin_email:
        admin_user = db.query(User).filter(
            User.institution_id == org.id,
            User.role.in_(["ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"])
        ).first()
        if admin_user:
            admin_user.email = org_in.admin_email
            if org_in.admin_name:
                admin_user.name = org_in.admin_name
            if org_in.admin_password:
                admin_user.password_hash = get_password_hash(org_in.admin_password)
        else:
            new_admin = User(
                name=org_in.admin_name or f"{org.name} Admin",
                email=org_in.admin_email,
                password_hash=get_password_hash(org_in.admin_password or "orgadmin123"),
                role="ORGANIZATION_ADMIN",
                institution_id=org.id,
                is_active=True
            )
            db.add(new_admin)
            
    org.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(org)
    
    log_audit_trail(
        db=db,
        action="ORGANIZATION_UPDATED",
        resource="ORGANIZATION",
        resource_id=str(org.id),
        user_id=current_user.id,
        organization_id=org.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"name": org.name}
    )
    
    admin_email = get_org_admin_email(db, org.id)
    cert_count = db.query(Credential).filter(Credential.institution_id == org.id).count()
    
    return {
        "id": org.id,
        "name": org.name,
        "institution_code": org.institution_code,
        "organization_type": org.organization_type,
        "registration_number": org.registration_number,
        "official_domain": org.official_domain,
        "description": org.description,
        "contact_email": org.contact_email,
        "contact_phone": org.contact_phone,
        "address": org.address,
        "logo_url": org.logo_url,
        "verification_status": org.verification_status,
        "status": org.status,
        "trust_score": org.trust_score,
        "key_algorithm": org.key_algorithm,
        "key_fingerprint": org.key_fingerprint,
        "public_key": org.public_key,
        "features_config": org.features_config,
        "admin_email": admin_email,
        "total_credentials": cert_count,
        "total_certificates": cert_count,
        "created_at": org.created_at,
        "updated_at": org.updated_at
    }

@router.post("/{org_id}/suspend")
def suspend_organization(
    org_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN"]))
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    org.status = "SUSPENDED"
    org.verification_status = "SUSPENDED"
    db.commit()
    
    log_audit_trail(
        db=db,
        action="ORGANIZATION_SUSPENDED",
        resource="ORGANIZATION",
        resource_id=str(org.id),
        user_id=current_user.id,
        organization_id=org.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS"
    )
    return {"status": "success", "message": f"Organization '{org.name}' has been suspended"}

@router.post("/{org_id}/activate")
def activate_organization(
    org_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN"]))
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    org.status = "ACTIVE"
    org.verification_status = "VERIFIED"
    db.commit()
    
    log_audit_trail(
        db=db,
        action="ORGANIZATION_ACTIVATED",
        resource="ORGANIZATION",
        resource_id=str(org.id),
        user_id=current_user.id,
        organization_id=org.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS"
    )
    return {"status": "success", "message": f"Organization '{org.name}' is now active"}

@router.get("/{org_id}/users", response_model=List[UserResponse])
def get_organization_users(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "SUPER_ADMIN" and current_user.institution_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    return db.query(User).filter(User.institution_id == org_id).order_by(User.id.asc()).all()

@router.post("/{org_id}/users", response_model=UserResponse)
def create_organization_user(
    org_id: int,
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    if current_user.role != "SUPER_ADMIN" and current_user.institution_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    existing = db.query(User).filter(User.email == user_in.email.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
        
    new_user = User(
        name=user_in.name,
        email=user_in.email.strip(),
        password_hash=get_password_hash(user_in.password),
        role=user_in.role or "CREDENTIAL_ISSUER",
        organization=user_in.organization,
        institution_id=org_id,
        permissions=json.dumps(user_in.permissions) if user_in.permissions else None,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log_audit_trail(
        db=db,
        action="USER_CREATED",
        resource="USER",
        resource_id=str(new_user.id),
        user_id=current_user.id,
        organization_id=org_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"created_email": new_user.email, "role": new_user.role}
    )
    return new_user

@router.delete("/{org_id}")
def delete_organization(
    org_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN"]))
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    org_name = org.name
    db.delete(org)
    db.commit()
    
    log_audit_trail(
        db=db,
        action="ORGANIZATION_DELETED",
        resource="ORGANIZATION",
        resource_id=str(org_id),
        user_id=current_user.id,
        organization_id=org_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"deleted_name": org_name}
    )
    return {"status": "success", "message": f"Organization '{org_name}' deleted successfully"}
