import os
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.domain import Organization, User, Credential
from app.schemas.domain import InstitutionCreate, InstitutionUpdate, InstitutionResponse
from app.api.deps import get_current_active_user, require_role
from app.crypto.signing import generate_institution_keypair

router = APIRouter()

def get_institution_admin_email(db: Session, institution_id: int) -> Optional[str]:
    admin = db.query(User).filter(
        User.institution_id == institution_id,
        User.role.in_(["INSTITUTION_ADMIN", "ORGANIZATION_ADMIN", "ORGANIZATION_OWNER"])
    ).first()
    return admin.email if admin else None

@router.get("/", response_model=List[InstitutionResponse])
def get_institutions(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Organization)
    if current_user.role != "SUPER_ADMIN":
        query = query.filter(Organization.id == current_user.institution_id)
        
    institutions = query.offset(skip).limit(limit).all()
    results = []
    for inst in institutions:
        admin_email = get_institution_admin_email(db, inst.id)
        cert_count = db.query(Credential).filter(Credential.institution_id == inst.id).count()
        
        if not inst.public_key or not inst.private_key:
            priv, pub, fp = generate_institution_keypair()
            inst.private_key = priv
            inst.public_key = pub
            inst.key_fingerprint = fp
            db.commit()
            db.refresh(inst)
            
        inst_dict = {
            "id": inst.id,
            "name": inst.name,
            "institution_code": inst.institution_code,
            "organization_type": inst.organization_type or "UNIVERSITY",
            "registration_number": inst.registration_number,
            "official_domain": inst.official_domain,
            "description": inst.description,
            "contact_email": inst.contact_email,
            "contact_phone": inst.contact_phone,
            "address": inst.address,
            "logo_url": inst.logo_url,
            "verification_status": inst.verification_status,
            "status": inst.status or "ACTIVE",
            "trust_score": inst.trust_score or 95.0,
            "key_algorithm": inst.key_algorithm or "RSA-2048",
            "key_fingerprint": inst.key_fingerprint,
            "public_key": inst.public_key,
            "features_config": inst.features_config,
            "admin_email": admin_email,
            "total_credentials": cert_count,
            "total_certificates": cert_count,
            "created_at": inst.created_at,
            "updated_at": inst.updated_at
        }
        results.append(inst_dict)
    return results

@router.post("/", response_model=InstitutionResponse)
def create_institution(
    institution_in: InstitutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN"]))
):
    existing = db.query(Organization).filter(Organization.institution_code == institution_in.institution_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Institution code already registered")
    
    private_key, public_key, fingerprint = generate_institution_keypair()
    
    features_json = None
    if institution_in.features:
        features_json = json.dumps(institution_in.features.dict())
    else:
        features_json = json.dumps({
            "suspicious_threshold": 0.5,
            "allow_revocation": True,
            "allow_reinstate": True,
            "require_revocation_reason": True,
            "qr_verification_enabled": True,
            "ocr_document_check_enabled": True,
            "digital_signatures_enabled": True,
            "signature_algorithm": "RSA-PSS-SHA256"
        })
    
    new_inst = Organization(
        name=institution_in.name,
        institution_code=institution_in.institution_code,
        organization_type=institution_in.organization_type or "UNIVERSITY",
        registration_number=institution_in.registration_number,
        official_domain=institution_in.official_domain,
        description=institution_in.description,
        contact_email=institution_in.contact_email,
        contact_phone=institution_in.contact_phone,
        address=institution_in.address,
        logo_url=institution_in.logo_url,
        verification_status=institution_in.verification_status or "VERIFIED",
        status=institution_in.status or "ACTIVE",
        trust_score=95.0,
        public_key=public_key,
        private_key=private_key,
        key_algorithm="RSA-2048",
        key_fingerprint=fingerprint,
        features_config=features_json
    )
    db.add(new_inst)
    db.commit()
    db.refresh(new_inst)
    
    if institution_in.admin_email and institution_in.admin_password:
        existing_user = db.query(User).filter(User.email == institution_in.admin_email).first()
        if existing_user:
            existing_user.institution_id = new_inst.id
            existing_user.role = "INSTITUTION_ADMIN"
            existing_user.password_hash = get_password_hash(institution_in.admin_password)
            if institution_in.admin_name:
                existing_user.name = institution_in.admin_name
        else:
            admin_user = User(
                name=institution_in.admin_name or f"{new_inst.name} Admin",
                email=institution_in.admin_email,
                password_hash=get_password_hash(institution_in.admin_password),
                role="INSTITUTION_ADMIN",
                institution_id=new_inst.id,
                is_active=True
            )
            db.add(admin_user)
        db.commit()
    
    return {
        "id": new_inst.id,
        "name": new_inst.name,
        "institution_code": new_inst.institution_code,
        "organization_type": new_inst.organization_type,
        "registration_number": new_inst.registration_number,
        "official_domain": new_inst.official_domain,
        "description": new_inst.description,
        "contact_email": new_inst.contact_email,
        "contact_phone": new_inst.contact_phone,
        "address": new_inst.address,
        "logo_url": new_inst.logo_url,
        "verification_status": new_inst.verification_status,
        "status": new_inst.status,
        "trust_score": new_inst.trust_score,
        "key_algorithm": new_inst.key_algorithm,
        "key_fingerprint": new_inst.key_fingerprint,
        "public_key": new_inst.public_key,
        "features_config": new_inst.features_config,
        "admin_email": institution_in.admin_email,
        "total_credentials": 0,
        "total_certificates": 0,
        "created_at": new_inst.created_at,
        "updated_at": new_inst.updated_at
    }

@router.get("/{institution_id}", response_model=InstitutionResponse)
def get_institution(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    inst = db.query(Organization).filter(Organization.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    if current_user.role != "SUPER_ADMIN" and current_user.institution_id != inst.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    admin_email = get_institution_admin_email(db, inst.id)
    cert_count = db.query(Credential).filter(Credential.institution_id == inst.id).count()
    
    return {
        "id": inst.id,
        "name": inst.name,
        "institution_code": inst.institution_code,
        "organization_type": inst.organization_type or "UNIVERSITY",
        "registration_number": inst.registration_number,
        "official_domain": inst.official_domain,
        "description": inst.description,
        "contact_email": inst.contact_email,
        "contact_phone": inst.contact_phone,
        "address": inst.address,
        "logo_url": inst.logo_url,
        "verification_status": inst.verification_status,
        "status": inst.status or "ACTIVE",
        "trust_score": inst.trust_score or 95.0,
        "key_algorithm": inst.key_algorithm or "RSA-2048",
        "key_fingerprint": inst.key_fingerprint,
        "public_key": inst.public_key,
        "features_config": inst.features_config,
        "admin_email": admin_email,
        "total_credentials": cert_count,
        "total_certificates": cert_count,
        "created_at": inst.created_at,
        "updated_at": inst.updated_at
    }

@router.put("/{institution_id}", response_model=InstitutionResponse)
def update_institution(
    institution_id: int,
    inst_in: InstitutionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN"]))
):
    inst = db.query(Organization).filter(Organization.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    for field, val in inst_in.dict(exclude_unset=True).items():
        if field == "features" and val:
            inst.features_config = json.dumps(val)
        elif hasattr(inst, field) and val is not None and field not in ["admin_email", "admin_name", "admin_password", "features"]:
            setattr(inst, field, val)
        
    if inst_in.admin_email:
        admin_user = db.query(User).filter(
            User.institution_id == inst.id,
            User.role.in_(["INSTITUTION_ADMIN", "ORGANIZATION_ADMIN"])
        ).first()
        
        if admin_user:
            admin_user.email = inst_in.admin_email
            if inst_in.admin_name:
                admin_user.name = inst_in.admin_name
            if inst_in.admin_password:
                admin_user.password_hash = get_password_hash(inst_in.admin_password)
        else:
            new_admin = User(
                name=inst_in.admin_name or f"{inst.name} Admin",
                email=inst_in.admin_email,
                password_hash=get_password_hash(inst_in.admin_password or "instadmin123"),
                role="INSTITUTION_ADMIN",
                institution_id=inst.id,
                is_active=True
            )
            db.add(new_admin)
            
    db.commit()
    db.refresh(inst)
    
    admin_email = get_institution_admin_email(db, inst.id)
    cert_count = db.query(Credential).filter(Credential.institution_id == inst.id).count()
    
    return {
        "id": inst.id,
        "name": inst.name,
        "institution_code": inst.institution_code,
        "organization_type": inst.organization_type or "UNIVERSITY",
        "registration_number": inst.registration_number,
        "official_domain": inst.official_domain,
        "description": inst.description,
        "contact_email": inst.contact_email,
        "contact_phone": inst.contact_phone,
        "address": inst.address,
        "logo_url": inst.logo_url,
        "verification_status": inst.verification_status,
        "status": inst.status or "ACTIVE",
        "trust_score": inst.trust_score or 95.0,
        "key_algorithm": inst.key_algorithm,
        "key_fingerprint": inst.key_fingerprint,
        "public_key": inst.public_key,
        "features_config": inst.features_config,
        "admin_email": admin_email,
        "total_credentials": cert_count,
        "total_certificates": cert_count,
        "created_at": inst.created_at,
        "updated_at": inst.updated_at
    }

@router.delete("/{institution_id}")
def delete_institution(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN"]))
):
    inst = db.query(Organization).filter(Organization.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
        
    db.delete(inst)
    db.commit()
    return {"status": "success", "message": f"Institution '{inst.name}' and all associated records deleted successfully"}

@router.post("/{institution_id}/regenerate-keys")
def regenerate_institution_keys(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN"]))
):
    inst = db.query(Organization).filter(Organization.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
        
    private_key, public_key, fingerprint = generate_institution_keypair()
    inst.private_key = private_key
    inst.public_key = public_key
    inst.key_fingerprint = fingerprint
    db.commit()
    db.refresh(inst)
    
    return {
        "status": "success",
        "key_algorithm": inst.key_algorithm,
        "key_fingerprint": inst.key_fingerprint,
        "public_key": inst.public_key
    }

@router.get("/{institution_id}/report/summary")
def get_institution_report_summary(
    institution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    inst = db.query(Organization).filter(Organization.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
        
    if current_user.role != "SUPER_ADMIN" and current_user.institution_id != inst.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    admin_email = get_institution_admin_email(db, inst.id)
    all_certs = db.query(Credential).filter(Credential.institution_id == inst.id).all()
    
    total = len(all_certs)
    active = sum(1 for c in all_certs if c.status == "ACTIVE")
    revoked = sum(1 for c in all_certs if c.status == "REVOKED")
    suspicious = sum(1 for c in all_certs if c.status == "SUSPICIOUS")
    expired = sum(1 for c in all_certs if c.status == "EXPIRED")

    categories = {
        "ACADEMIC": sum(1 for c in all_certs if (c.category or "ACADEMIC").upper() == "ACADEMIC"),
        "RECRUITMENT": sum(1 for c in all_certs if "RECRUIT" in (c.category or "").upper() or "EMPLOY" in (c.category or "").upper()),
        "TECHNICAL_COURSE": sum(1 for c in all_certs if "TECH" in (c.category or "").upper() or "COURSE" in (c.category or "").upper()),
        "ACHIEVEMENT": sum(1 for c in all_certs if "ACHIEVE" in (c.category or "").upper() or "AWARD" in (c.category or "").upper()),
    }

    return {
        "institution_id": inst.id,
        "name": inst.name,
        "institution_code": inst.institution_code,
        "official_domain": inst.official_domain,
        "contact_email": inst.contact_email,
        "verification_status": inst.verification_status,
        "admin_email": admin_email,
        "key_algorithm": inst.key_algorithm or "RSA-2048",
        "key_fingerprint": inst.key_fingerprint,
        "total_certificates": total,
        "active_certificates": active,
        "revoked_certificates": revoked,
        "suspicious_certificates": suspicious,
        "expired_certificates": expired,
        "categories_breakdown": categories
    }

@router.get("/{institution_id}/report/pdf")
def generate_and_download_institution_report_pdf(
    institution_id: int,
    status: Optional[str] = "ALL",
    category: Optional[str] = "ALL",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    from fastapi.responses import FileResponse
    from app.services.report_service import generate_institution_report_pdf

    inst = db.query(Organization).filter(Organization.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
        
    if current_user.role != "SUPER_ADMIN" and current_user.institution_id != inst.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    query = db.query(Credential).filter(Credential.institution_id == inst.id)
    if status and status.upper() != "ALL":
        query = query.filter(Credential.status == status.upper())
    if category and category.upper() != "ALL":
        query = query.filter(Credential.category == category.upper())
        
    certificates = query.order_by(Credential.id.asc()).all()

    admin_email = get_institution_admin_email(db, inst.id)
    setattr(inst, 'admin_email', admin_email)

    stats = {
        "total": len(certificates),
        "active": sum(1 for c in certificates if c.status == "ACTIVE"),
        "revoked": sum(1 for c in certificates if c.status == "REVOKED"),
        "suspicious": sum(1 for c in certificates if c.status == "SUSPICIOUS")
    }

    pdf_file_path = generate_institution_report_pdf(
        institution=inst,
        certificates=certificates,
        stats=stats,
        generated_by_user=current_user,
        status_filter=status,
        category_filter=category
    )

    if not os.path.exists(pdf_file_path):
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")

    safe_inst_code = (inst.institution_code or "INST").replace(" ", "_")
    download_name = f"CredAuth_Audit_Report_{safe_inst_code}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return FileResponse(
        pdf_file_path,
        media_type="application/pdf",
        filename=download_name
    )
