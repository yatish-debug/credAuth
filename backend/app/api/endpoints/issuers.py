from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.domain import Organization, Credential, FraudCase, User
from app.trust_engine.scoring import calculate_issuer_trust_score
from app.api.deps import get_current_active_user

router = APIRouter()

@router.get("/")
def list_issuers(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    orgs = db.query(Organization).filter(Organization.status == "ACTIVE").offset(skip).limit(limit).all()
    results = []
    for org in orgs:
        total_c = db.query(Credential).filter(Credential.institution_id == org.id).count()
        rev_c = db.query(Credential).filter(Credential.institution_id == org.id, Credential.status == "REVOKED").count()
        fraud_c = db.query(FraudCase).filter(FraudCase.organization_id == org.id).count()
        
        trust_data = calculate_issuer_trust_score(
            is_verified=(org.verification_status == "VERIFIED"),
            has_keys=bool(org.public_key),
            domain_present=bool(org.official_domain),
            total_credentials=total_c,
            revocation_count=rev_c,
            fraud_reports_count=fraud_c
        )
        
        results.append({
            "id": org.id,
            "name": org.name,
            "institution_code": org.institution_code,
            "organization_type": org.organization_type or "UNIVERSITY",
            "official_domain": org.official_domain,
            "verification_status": org.verification_status,
            "key_algorithm": org.key_algorithm or "RSA-2048",
            "key_fingerprint": org.key_fingerprint,
            "total_credentials": total_c,
            "trust_profile": trust_data
        })
    return results

@router.get("/{issuer_id}")
def get_issuer_profile(
    issuer_id: int,
    db: Session = Depends(get_db)
):
    org = db.query(Organization).filter(Organization.id == issuer_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Issuer organization not found")
        
    total_c = db.query(Credential).filter(Credential.institution_id == org.id).count()
    rev_c = db.query(Credential).filter(Credential.institution_id == org.id, Credential.status == "REVOKED").count()
    fraud_c = db.query(FraudCase).filter(FraudCase.organization_id == org.id).count()
    
    trust_data = calculate_issuer_trust_score(
        is_verified=(org.verification_status == "VERIFIED"),
        has_keys=bool(org.public_key),
        domain_present=bool(org.official_domain),
        total_credentials=total_c,
        revocation_count=rev_c,
        fraud_reports_count=fraud_c
    )
    
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
        "key_algorithm": org.key_algorithm or "RSA-2048",
        "key_fingerprint": org.key_fingerprint,
        "public_key": org.public_key,
        "trust_score": trust_data["issuer_trust_score"],
        "trust_profile": trust_data,
        "total_credentials": total_c,
        "revocation_count": rev_c,
        "fraud_cases_count": fraud_c
    }
