import os
import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.domain import Credential, User, Organization, CredentialStatusHistory, MonitoringSubscription, MonitoringAlert
from app.schemas.domain import CredentialCreate, CredentialUpdate, CredentialResponse
from app.api.deps import get_current_active_user, require_role, log_audit_trail
from app.qr.generator import generate_qr_code
from app.services.pdf_service import generate_certificate_pdf
from app.crypto.hashing import generate_file_hash
from app.crypto.signing import (
    generate_institution_keypair, 
    sign_certificate_payload, 
    verify_certificate_signature
)

router = APIRouter()

def generate_credential_id():
    suffix = uuid.uuid4().hex[:8].upper()
    return f"CV-2026-{suffix}"

def generate_qr_token():
    return uuid.uuid4().hex

def format_date_str(d) -> str:
    if hasattr(d, 'strftime'):
        return d.strftime("%Y-%m-%d")
    return str(d)[:10]

class ReasonRequest(BaseModel):
    reason: str

@router.post("", response_model=CredentialResponse)
@router.post("/", response_model=CredentialResponse)
def create_credential(
    cert_in: CredentialCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN", "CREDENTIAL_ISSUER", "ISSUER"]))
):
    inst_id = cert_in.organization_id or cert_in.institution_id or current_user.institution_id
    if not inst_id:
        first_inst = db.query(Organization).first()
        if not first_inst:
            raise HTTPException(status_code=400, detail="No organizations exist in the platform. Please create an organization first.")
        inst_id = first_inst.id
    
    institution = db.query(Organization).filter(Organization.id == inst_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    # Ensure institution has cryptographic keys
    if not institution.private_key or not institution.public_key:
        priv, pub, fp = generate_institution_keypair()
        institution.private_key = priv
        institution.public_key = pub
        institution.key_fingerprint = fp
        db.commit()
        db.refresh(institution)
        
    cert_id = generate_credential_id()
    qr_token = generate_qr_token()
    
    # 1. Generate QR Code
    qr_path = generate_qr_code(qr_token, cert_id)
    
    # 2. Generate PDF
    issue_date_display = cert_in.issue_date.strftime("%B %d, %Y") if hasattr(cert_in.issue_date, 'strftime') else str(cert_in.issue_date)
    pdf_path = generate_certificate_pdf(
        certificate_id=cert_id,
        holder_name=cert_in.holder_name,
        course_name=cert_in.course_name,
        institution_name=institution.name,
        issue_date=issue_date_display,
        qr_image_path=qr_path,
        category=cert_in.category or "ACADEMIC",
        student_id=cert_in.student_id,
        department=cert_in.department,
        academic_year=cert_in.academic_year,
        marks_obtained=cert_in.marks_obtained,
        total_marks=cert_in.total_marks,
        percentage=cert_in.percentage,
        cgpa=cert_in.cgpa,
        grade=cert_in.grade,
        remarks=cert_in.remarks,
        role_designation=cert_in.role_designation,
        organization_company=cert_in.organization_company,
        skills_acquired=cert_in.skills_acquired,
        employment_type=cert_in.employment_type,
        license_number=cert_in.license_number,
        score_or_rank=cert_in.score_or_rank
    )
    
    # 3. Generate SHA-256 Hash of PDF
    doc_hash = generate_file_hash(pdf_path)
    
    # 4. Cryptographically Sign the Canonical Payload
    canonical_payload = {
        "certificate_id": cert_id,
        "holder_name": cert_in.holder_name,
        "student_id": cert_in.student_id or "",
        "course_name": cert_in.course_name,
        "grade": cert_in.grade or "",
        "cgpa": str(cert_in.cgpa) if cert_in.cgpa is not None else "",
        "institution_code": institution.institution_code,
        "issue_date": format_date_str(cert_in.issue_date),
        "document_hash": doc_hash,
        "qr_token": qr_token
    }
    
    digital_signature = sign_certificate_payload(
        institution.private_key, 
        canonical_payload
    )
    
    dict_data = cert_in.model_dump(exclude={"extra_metadata", "organization_id", "institution_id"}) if hasattr(cert_in, 'model_dump') else cert_in.dict(exclude={"extra_metadata", "organization_id", "institution_id"})
    new_cert = Credential(
        **dict_data,
        certificate_id=cert_id,
        institution_id=inst_id,
        issuer_id=current_user.id,
        document_path=pdf_path,
        document_hash=doc_hash,
        qr_token=qr_token,
        status="ACTIVE",
        digital_signature=digital_signature,
        signature_algorithm="RSA-PSS-SHA256",
        signer_public_key_fingerprint=institution.key_fingerprint,
        metadata_json=json.dumps(cert_in.extra_metadata) if getattr(cert_in, 'extra_metadata', None) else None
    )
    
    db.add(new_cert)
    db.commit()
    db.refresh(new_cert)
    
    log_audit_trail(
        db=db,
        action="CREDENTIAL_ISSUED",
        resource="CREDENTIAL",
        resource_id=str(new_cert.id),
        user_id=current_user.id,
        organization_id=inst_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"credential_id": cert_id, "holder": cert_in.holder_name, "type": cert_in.certificate_type}
    )
    
    return new_cert

@router.get("/", response_model=List[CredentialResponse])
def get_credentials(
    skip: int = 0,
    limit: int = 200,
    status_filter: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Credential)
    
    # Tenant boundary
    if current_user.role != "SUPER_ADMIN":
        if current_user.institution_id:
            query = query.filter(Credential.institution_id == current_user.institution_id)
        else:
            raise HTTPException(status_code=403, detail="User has no assigned organization")
            
    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(Credential.status == status_filter.upper())
        
    if category and category.upper() != "ALL":
        query = query.filter(Credential.category == category.upper())
        
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (Credential.certificate_id.ilike(s)) |
            (Credential.holder_name.ilike(s)) |
            (Credential.course_name.ilike(s)) |
            (Credential.student_id.ilike(s))
        )
        
    return query.order_by(Credential.id.desc()).offset(skip).limit(limit).all()

@router.get("/{cert_id}", response_model=CredentialResponse)
def get_credential(
    cert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    cert = db.query(Credential).filter(Credential.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Credential not found")
        
    if current_user.role != "SUPER_ADMIN" and cert.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    return cert

@router.put("/{cert_id}", response_model=CredentialResponse)
def update_credential(
    cert_id: int,
    cert_in: CredentialUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN", "CREDENTIAL_ISSUER", "ISSUER"]))
):
    cert = db.query(Credential).filter(Credential.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Credential not found")
        
    if current_user.role != "SUPER_ADMIN" and cert.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    institution = db.query(Organization).filter(Organization.id == cert.institution_id).first()
    
    update_dict = cert_in.dict(exclude_unset=True, exclude={"metadata"})
    for field, value in update_dict.items():
        setattr(cert, field, value)
        
    if cert_in.metadata is not None:
        cert.metadata_json = json.dumps(cert_in.metadata)
        
    # Re-generate PDF with updated data
    issue_date_display = cert.issue_date.strftime("%B %d, %Y")
    qr_path = os.path.join("storage", "qr", f"{cert.qr_token}.png")
    if not os.path.exists(qr_path):
        qr_path = generate_qr_code(cert.qr_token, cert.certificate_id)
        
    pdf_path = generate_certificate_pdf(
        certificate_id=cert.certificate_id,
        holder_name=cert.holder_name,
        course_name=cert.course_name,
        institution_name=institution.name if institution else "Credential Registry",
        issue_date=issue_date_display,
        qr_image_path=qr_path,
        category=cert.category or "ACADEMIC",
        student_id=cert.student_id,
        department=cert.department,
        academic_year=cert.academic_year,
        marks_obtained=cert.marks_obtained,
        total_marks=cert.total_marks,
        percentage=cert.percentage,
        cgpa=cert.cgpa,
        grade=cert.grade,
        remarks=cert.remarks,
        role_designation=cert.role_designation,
        organization_company=cert.organization_company,
        skills_acquired=cert.skills_acquired,
        employment_type=cert.employment_type,
        license_number=cert.license_number,
        score_or_rank=cert.score_or_rank
    )
    
    doc_hash = generate_file_hash(pdf_path)
    cert.document_path = pdf_path
    cert.document_hash = doc_hash
    
    if institution and institution.private_key:
        canonical_payload = {
            "certificate_id": cert.certificate_id,
            "holder_name": cert.holder_name,
            "student_id": cert.student_id or "",
            "course_name": cert.course_name,
            "grade": cert.grade or "",
            "cgpa": str(cert.cgpa) if cert.cgpa is not None else "",
            "institution_code": institution.institution_code,
            "issue_date": format_date_str(cert.issue_date),
            "document_hash": doc_hash,
            "qr_token": cert.qr_token
        }
        cert.digital_signature = sign_certificate_payload(
            institution.private_key,
            canonical_payload
        )
        cert.signature_algorithm = "RSA-PSS-SHA256"
        cert.signer_public_key_fingerprint = institution.key_fingerprint
        
    cert.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(cert)
    
    log_audit_trail(
        db=db,
        action="CREDENTIAL_UPDATED",
        resource="CREDENTIAL",
        resource_id=str(cert.id),
        user_id=current_user.id,
        organization_id=cert.institution_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"credential_id": cert.certificate_id}
    )
    
    return cert

@router.post("/{cert_id}/revoke")
def revoke_credential(
    cert_id: int,
    req: ReasonRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    cert = db.query(Credential).filter(Credential.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Credential not found")
        
    if current_user.role != "SUPER_ADMIN" and cert.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    if cert.status == "REVOKED":
        raise HTTPException(status_code=400, detail="Credential is already revoked")
        
    prev_status = cert.status
    cert.status = "REVOKED"
    cert.suspicious_reason = None
    
    history = CredentialStatusHistory(
        certificate_id=cert.id,
        previous_status=prev_status,
        new_status="REVOKED",
        reason=req.reason,
        changed_by=current_user.id
    )
    db.add(history)
    
    # Trigger monitoring alert if active watches exist
    watches = db.query(MonitoringSubscription).filter(
        MonitoringSubscription.credential_id == cert.id,
        MonitoringSubscription.status == "ACTIVE"
    ).all()
    for watch in watches:
        alert = MonitoringAlert(
            subscription_id=watch.id,
            organization_id=cert.institution_id,
            credential_id=cert.id,
            previous_status=prev_status,
            new_status="REVOKED",
            alert_type="REVOKED",
            message=f"Credential {cert.certificate_id} for {cert.holder_name} was revoked. Reason: {req.reason}"
        )
        db.add(alert)
        watch.last_status = "REVOKED"
        
    db.commit()
    
    log_audit_trail(
        db=db,
        action="CREDENTIAL_REVOKED",
        resource="CREDENTIAL",
        resource_id=str(cert.id),
        user_id=current_user.id,
        organization_id=cert.institution_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"credential_id": cert.certificate_id, "reason": req.reason}
    )
    
    return {"status": "success", "message": "Credential revoked successfully"}

@router.post("/{cert_id}/reinstate")
def reinstate_credential(
    cert_id: int,
    req: ReasonRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    cert = db.query(Credential).filter(Credential.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Credential not found")
        
    if current_user.role != "SUPER_ADMIN" and cert.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    prev_status = cert.status
    cert.status = "ACTIVE"
    cert.suspicious_reason = None
    
    history = CredentialStatusHistory(
        certificate_id=cert.id,
        previous_status=prev_status,
        new_status="ACTIVE",
        reason=req.reason or "Reinstated to Active registry",
        changed_by=current_user.id
    )
    db.add(history)
    db.commit()
    
    log_audit_trail(
        db=db,
        action="CREDENTIAL_REINSTATED",
        resource="CREDENTIAL",
        resource_id=str(cert.id),
        user_id=current_user.id,
        organization_id=cert.institution_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"credential_id": cert.certificate_id}
    )
    return {"status": "success", "message": "Credential reinstated to ACTIVE status"}

@router.post("/{cert_id}/flag-suspicious")
def flag_credential_suspicious(
    cert_id: int,
    req: ReasonRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    cert = db.query(Credential).filter(Credential.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Credential not found")
        
    if current_user.role != "SUPER_ADMIN" and cert.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    prev_status = cert.status
    cert.status = "SUSPICIOUS"
    cert.suspicious_reason = req.reason
    
    history = CredentialStatusHistory(
        certificate_id=cert.id,
        previous_status=prev_status,
        new_status="SUSPICIOUS",
        reason=req.reason,
        changed_by=current_user.id
    )
    db.add(history)
    db.commit()
    
    log_audit_trail(
        db=db,
        action="CREDENTIAL_FLAGGED_SUSPICIOUS",
        resource="CREDENTIAL",
        resource_id=str(cert.id),
        user_id=current_user.id,
        organization_id=cert.institution_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"credential_id": cert.certificate_id, "reason": req.reason}
    )
    return {"status": "success", "message": "Credential flagged as SUSPICIOUS for investigation"}

@router.delete("/{cert_id}")
def delete_credential(
    cert_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    cert = db.query(Credential).filter(Credential.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Credential not found")
        
    if current_user.role != "SUPER_ADMIN" and cert.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    cert_code = cert.certificate_id
    if cert.document_path and os.path.exists(cert.document_path):
        try:
            os.remove(cert.document_path)
        except Exception:
            pass
            
    db.delete(cert)
    db.commit()
    
    log_audit_trail(
        db=db,
        action="CREDENTIAL_DELETED",
        resource="CREDENTIAL",
        resource_id=str(cert_id),
        user_id=current_user.id,
        organization_id=cert.institution_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"deleted_code": cert_code}
    )
    return {"status": "success", "message": "Credential deleted successfully"}

@router.get("/{cert_id}/crypto-proof")
def get_credential_crypto_proof(
    cert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    cert = db.query(Credential).filter(Credential.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Credential not found")
        
    institution = db.query(Organization).filter(Organization.id == cert.institution_id).first()
    
    canonical_payload = {
        "certificate_id": cert.certificate_id,
        "holder_name": cert.holder_name,
        "student_id": cert.student_id or "",
        "course_name": cert.course_name,
        "grade": cert.grade or "",
        "cgpa": str(cert.cgpa) if cert.cgpa is not None else "",
        "institution_code": institution.institution_code if institution else "",
        "issue_date": format_date_str(cert.issue_date),
        "document_hash": cert.document_hash,
        "qr_token": cert.qr_token
    }
    
    is_valid_signature = False
    if institution and institution.public_key and cert.digital_signature:
        is_valid_signature = verify_certificate_signature(
            institution.public_key,
            canonical_payload,
            cert.digital_signature
        )
        
    qr_url = f"/storage/qr/{cert.qr_token}.png" if cert.qr_token else None
    pdf_url = f"/api/v1/certificates/{cert.id}/download"
    
    return {
        "certificate_id": cert.certificate_id,
        "holder_name": cert.holder_name,
        "course_name": cert.course_name,
        "category": cert.category or "ACADEMIC",
        "status": cert.status,
        "institution_name": institution.name if institution else "Unknown",
        "institution_code": institution.institution_code if institution else "",
        "key_algorithm": institution.key_algorithm if institution else "RSA-2048",
        "key_fingerprint": cert.signer_public_key_fingerprint or (institution.key_fingerprint if institution else ""),
        "public_key_pem": institution.public_key if institution else "",
        "digital_signature": cert.digital_signature,
        "signature_algorithm": cert.signature_algorithm or "RSA-PSS-SHA256",
        "document_hash": cert.document_hash,
        "canonical_payload": canonical_payload,
        "cryptographic_verification": "VALID" if is_valid_signature else "UNVERIFIED",
        "qr_token": cert.qr_token,
        "qr_image_url": qr_url,
        "pdf_download_url": pdf_url
    }

@router.get("/{cert_id}/download")
def download_credential_pdf(
    cert_id: int,
    db: Session = Depends(get_db)
):
    from fastapi.responses import FileResponse
    cert = db.query(Credential).filter(Credential.id == cert_id).first()
    if not cert or not cert.document_path or not os.path.exists(cert.document_path):
        raise HTTPException(status_code=404, detail="Credential PDF not found on server")
        
    return FileResponse(
        cert.document_path,
        media_type="application/pdf",
        filename=f"{cert.certificate_id}_{cert.holder_name.replace(' ', '_')}.pdf"
    )

@router.get("/{cert_id}/qr")
def get_credential_qr_image(
    cert_id: int,
    db: Session = Depends(get_db)
):
    from fastapi.responses import FileResponse
    cert = db.query(Credential).filter(Credential.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Credential not found")
        
    qr_path = os.path.join("storage", "qr", f"{cert.qr_token}.png")
    if not os.path.exists(qr_path):
        qr_path = generate_qr_code(cert.qr_token, cert.certificate_id)
        
    return FileResponse(
        qr_path,
        media_type="image/png",
        filename=f"QR_{cert.certificate_id}.png"
    )
