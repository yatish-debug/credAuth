import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.models.domain import FraudCase, Credential, Organization, User, CredentialStatusHistory
from app.schemas.domain import FraudCaseResponse, FraudCaseCreate, FraudCaseUpdate
from app.api.deps import get_current_active_user, require_role, log_audit_trail

router = APIRouter()

class ResolveCaseRequest(BaseModel):
    resolution: str # CONFIRMED_FRAUD, FALSE_POSITIVE, RESOLVED
    notes: str
    auto_revoke_credential: Optional[bool] = True

class AddNoteRequest(BaseModel):
    note: str

@router.get("/cases", response_model=List[FraudCaseResponse])
def get_fraud_cases(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List fraud investigation cases. Super Admin sees all; Org Admin/Auditor sees their tenant's cases.
    """
    query = db.query(FraudCase)
    if current_user.role != "SUPER_ADMIN" and current_user.institution_id:
        query = query.filter(FraudCase.organization_id == current_user.institution_id)
        
    if status_filter and status_filter.upper() != "ALL":
        query = query.filter(FraudCase.status == status_filter.upper())
    if risk_level and risk_level.upper() != "ALL":
        query = query.filter(FraudCase.risk_level == risk_level.upper())
        
    cases = query.order_by(FraudCase.id.desc()).offset(skip).limit(limit).all()
    results = []
    
    for c in cases:
        cred = db.query(Credential).filter(Credential.id == c.credential_id).first() if c.credential_id else None
        org = db.query(Organization).filter(Organization.id == c.organization_id).first() if c.organization_id else None
        investigator = db.query(User).filter(User.id == c.assigned_to).first() if c.assigned_to else None
        
        indicators = []
        if c.indicators_json:
            try:
                indicators = json.loads(c.indicators_json)
            except Exception:
                indicators = [c.indicators_json]
                
        notes = []
        if c.notes_json:
            try:
                notes = json.loads(c.notes_json)
            except Exception:
                pass
                
        results.append({
            "id": c.id,
            "case_id": c.case_id or f"FC-2026-{c.id:05d}",
            "credential_id": c.credential_id,
            "credential_code": cred.certificate_id if cred else "N/A",
            "holder_name": cred.holder_name if cred else "N/A",
            "organization_id": c.organization_id,
            "organization_name": org.name if org else "Platform",
            "risk_score": c.risk_score,
            "risk_level": c.risk_level,
            "indicators": indicators,
            "assigned_to": c.assigned_to,
            "assigned_to_name": investigator.name if investigator else None,
            "status": c.status,
            "notes_history": notes,
            "created_at": c.created_at,
            "resolved_at": c.resolved_at
        })
    return results

@router.get("/cases/{case_id}", response_model=FraudCaseResponse)
def get_fraud_case(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    case = db.query(FraudCase).filter(
        (FraudCase.case_id == case_id.strip()) | (FraudCase.id == (int(case_id) if case_id.isdigit() else -1))
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Fraud investigation case not found")
        
    if current_user.role != "SUPER_ADMIN" and case.organization_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    cred = db.query(Credential).filter(Credential.id == case.credential_id).first() if case.credential_id else None
    org = db.query(Organization).filter(Organization.id == case.organization_id).first() if case.organization_id else None
    investigator = db.query(User).filter(User.id == case.assigned_to).first() if case.assigned_to else None
    
    indicators = []
    if case.indicators_json:
        try:
            indicators = json.loads(case.indicators_json)
        except Exception:
            indicators = [case.indicators_json]
            
    notes = []
    if case.notes_json:
        try:
            notes = json.loads(case.notes_json)
        except Exception:
            pass
            
    return {
        "id": case.id,
        "case_id": case.case_id,
        "credential_id": case.credential_id,
        "credential_code": cred.certificate_id if cred else "N/A",
        "holder_name": cred.holder_name if cred else "N/A",
        "organization_id": case.organization_id,
        "organization_name": org.name if org else "Platform",
        "risk_score": case.risk_score,
        "risk_level": case.risk_level,
        "indicators": indicators,
        "assigned_to": case.assigned_to,
        "assigned_to_name": investigator.name if investigator else None,
        "status": case.status,
        "notes_history": notes,
        "created_at": case.created_at,
        "resolved_at": case.resolved_at
    }

@router.post("/cases/{case_id}/note")
def add_case_note(
    case_id: str,
    note_in: AddNoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    case = db.query(FraudCase).filter(
        (FraudCase.case_id == case_id.strip()) | (FraudCase.id == (int(case_id) if case_id.isdigit() else -1))
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    notes = []
    if case.notes_json:
        try:
            notes = json.loads(case.notes_json)
        except Exception:
            pass
            
    notes.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "author": f"{current_user.name} ({current_user.role})",
        "text": note_in.note
    })
    case.notes_json = json.dumps(notes)
    db.commit()
    return {"status": "success", "message": "Note recorded"}

@router.post("/cases/{case_id}/assign")
def assign_investigator(
    case_id: str,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    case = db.query(FraudCase).filter(
        (FraudCase.case_id == case_id.strip()) | (FraudCase.id == (int(case_id) if case_id.isdigit() else -1))
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    investigator = db.query(User).filter(User.id == user_id).first()
    if not investigator:
        raise HTTPException(status_code=404, detail="Investigator user not found")
        
    case.assigned_to = user_id
    case.status = "UNDER_REVIEW"
    
    notes = []
    if case.notes_json:
        try:
            notes = json.loads(case.notes_json)
        except Exception:
            pass
    notes.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "author": current_user.name,
        "text": f"Assigned case to investigator {investigator.name}."
    })
    case.notes_json = json.dumps(notes)
    db.commit()
    return {"status": "success", "message": f"Assigned to {investigator.name}"}

@router.post("/cases/{case_id}/resolve")
def resolve_fraud_case(
    case_id: str,
    req_in: ResolveCaseRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN", "AUDITOR"]))
):
    case = db.query(FraudCase).filter(
        (FraudCase.case_id == case_id.strip()) | (FraudCase.id == (int(case_id) if case_id.isdigit() else -1))
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    if req_in.resolution not in ["CONFIRMED_FRAUD", "FALSE_POSITIVE", "RESOLVED"]:
        raise HTTPException(status_code=400, detail="Invalid resolution status")
        
    case.status = req_in.resolution
    case.resolved_at = datetime.now(timezone.utc)
    
    notes = []
    if case.notes_json:
        try:
            notes = json.loads(case.notes_json)
        except Exception:
            pass
    notes.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "author": f"{current_user.name} ({current_user.role})",
        "text": f"Case resolved as {req_in.resolution}. Notes: {req_in.notes}"
    })
    case.notes_json = json.dumps(notes)
    
    # Auto-revoke credential if confirmed fraud
    if req_in.resolution == "CONFIRMED_FRAUD" and req_in.auto_revoke_credential and case.credential_id:
        cred = db.query(Credential).filter(Credential.id == case.credential_id).first()
        if cred and cred.status != "REVOKED":
            prev_st = cred.status
            cred.status = "REVOKED"
            cred.suspicious_reason = f"Revoked following Fraud Investigation {case.case_id}: {req_in.notes}"
            history = CredentialStatusHistory(
                certificate_id=cred.id,
                previous_status=prev_st,
                new_status="REVOKED",
                reason=f"Fraud Case {case.case_id} Confirmed: {req_in.notes}",
                changed_by=current_user.id
            )
            db.add(history)
            
    db.commit()
    
    log_audit_trail(
        db=db,
        action="FRAUD_CASE_RESOLVED",
        resource="FRAUD_CASE",
        resource_id=case.case_id,
        user_id=current_user.id,
        organization_id=case.organization_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"case_id": case.case_id, "resolution": req_in.resolution}
    )
    
    return {"status": "success", "message": f"Fraud case resolved as {req_in.resolution}"}

@router.get("/analytics")
def get_fraud_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(FraudCase)
    if current_user.role != "SUPER_ADMIN" and current_user.institution_id:
        query = query.filter(FraudCase.organization_id == current_user.institution_id)
        
    all_cases = query.all()
    
    open_c = sum(1 for c in all_cases if c.status == "OPEN")
    under_review_c = sum(1 for c in all_cases if c.status == "UNDER_REVIEW")
    confirmed_c = sum(1 for c in all_cases if c.status == "CONFIRMED_FRAUD")
    false_pos_c = sum(1 for c in all_cases if c.status == "FALSE_POSITIVE")
    resolved_c = sum(1 for c in all_cases if c.status == "RESOLVED")
    
    critical_c = sum(1 for c in all_cases if c.risk_level == "CRITICAL")
    high_c = sum(1 for c in all_cases if c.risk_level == "HIGH")
    med_c = sum(1 for c in all_cases if c.risk_level == "MEDIUM")
    low_c = sum(1 for c in all_cases if c.risk_level == "LOW")
    
    return {
        "total_cases": len(all_cases),
        "open_cases": open_c,
        "under_review": under_review_c,
        "confirmed_fraud": confirmed_c,
        "false_positive": false_pos_c,
        "resolved": resolved_c,
        "risk_breakdown": {
            "CRITICAL": critical_c,
            "HIGH": high_c,
            "MEDIUM": med_c,
            "LOW": low_c
        }
    }
