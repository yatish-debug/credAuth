import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.domain import VerificationResult, VerificationRequest, Credential, Organization, User
from app.schemas.domain import EvidenceResponse
from app.api.deps import get_current_active_user, get_tenant_context, get_optional_tenant_context

router = APIRouter()

@router.get("/{verification_id}")
def get_verification_evidence_dossier(
    verification_id: str,
    db: Session = Depends(get_db),
    tenant_ctx: dict = Depends(get_optional_tenant_context)
):
    """
    Retrieve an immutable Verification Evidence Dossier by Verification ID.
    Used by compliance, recruiters, and background verification teams for audits.
    """
    # Look up by verification_id (e.g. VER-2026-000918) or integer ID
    res = db.query(VerificationResult).filter(VerificationResult.verification_id == verification_id.strip()).first()
    if not res:
        try:
            int_id = int(verification_id)
            res = db.query(VerificationResult).filter(VerificationResult.id == int_id).first()
        except ValueError:
            pass
            
    if not res:
        raise HTTPException(status_code=404, detail="Verification evidence record not found")
        
    org = db.query(Organization).filter(Organization.id == res.organization_id).first() if res.organization_id else None
    cert = db.query(Credential).filter(Credential.id == res.credential_id).first() if res.credential_id else None
    req = db.query(VerificationRequest).filter(VerificationRequest.id == res.verification_request_id).first() if res.verification_request_id else None
    
    trust_breakdown = {}
    if res.trust_breakdown_json:
        try:
            trust_breakdown = json.loads(res.trust_breakdown_json)
        except Exception:
            pass
            
    evidence_meta = {}
    if res.evidence_metadata_json:
        try:
            evidence_meta = json.loads(res.evidence_metadata_json)
        except Exception:
            pass

    verified_rec = None
    if cert:
        verified_rec = {
            "credential_id": cert.certificate_id,
            "holder_name": cert.holder_name,
            "holder_identifier": cert.student_id,
            "course_name": cert.course_name,
            "category": cert.category,
            "credential_type": cert.certificate_type,
            "grade": cert.grade,
            "cgpa": cert.cgpa,
            "marks_obtained": cert.marks_obtained,
            "total_marks": cert.total_marks,
            "percentage": cert.percentage,
            "role_designation": cert.role_designation,
            "organization_company": cert.organization_company,
            "skills_acquired": cert.skills_acquired,
            "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
            "expiry_date": cert.expiry_date.isoformat() if cert.expiry_date else None,
            "document_hash": cert.document_hash,
            "signature_algorithm": cert.signature_algorithm,
            "key_fingerprint": cert.signer_public_key_fingerprint or (org.key_fingerprint if org else None),
            "status": cert.status
        }
        
    return {
        "verification_id": res.verification_id or f"VER-2026-{res.id:06d}",
        "credential_id": cert.certificate_id if cert else (req.searched_certificate_id if req else "UNKNOWN"),
        "organization_name": org.name if org else "Institutional Registry",
        "organization_code": org.institution_code if org else "N/A",
        "verification_method": req.verification_method if req else "SYSTEM",
        "timestamp": res.timestamp,
        "registry_check": res.registry_check,
        "qr_check": res.qr_check or "VALID",
        "hash_check": res.hash_check or "VALID",
        "signature_check": res.signature_check or "VALID",
        "issuer_check": res.issuer_check,
        "document_analysis": res.document_analysis or "CLEAN",
        "fraud_risk_score": res.fraud_risk_score,
        "risk_level": res.risk_level,
        "confidence": res.confidence,
        "trust_score": res.trust_score,
        "trust_breakdown": trust_breakdown,
        "issuer_trust_score": res.issuer_trust_score,
        "final_decision": res.final_result,
        "final_result": res.final_result,
        "explanation": res.explanation,
        "evidence_metadata": evidence_meta,
        "verified_record": verified_rec
    }
