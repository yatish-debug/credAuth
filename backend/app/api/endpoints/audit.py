import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.domain import AuditLog, User, Organization
from app.schemas.domain import AuditLogResponse
from app.api.deps import get_current_active_user, require_role

router = APIRouter()

@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    skip: int = 0,
    limit: int = 150,
    action: Optional[str] = None,
    resource: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN", "AUDITOR"]))
):
    """
    Query enterprise immutable audit trail.
    """
    query = db.query(AuditLog)
    if current_user.role != "SUPER_ADMIN" and current_user.institution_id:
        query = query.filter(AuditLog.organization_id == current_user.institution_id)
        
    if action and action.upper() != "ALL":
        query = query.filter(AuditLog.action.ilike(f"%{action.strip()}%"))
    if resource and resource.upper() != "ALL":
        query = query.filter(AuditLog.resource.ilike(f"%{resource.strip()}%"))
        
    logs = query.order_by(AuditLog.id.desc()).offset(skip).limit(limit).all()
    results = []
    
    for l in logs:
        u = db.query(User).filter(User.id == l.user_id).first() if l.user_id else None
        o = db.query(Organization).filter(Organization.id == l.organization_id).first() if l.organization_id else None
        
        meta = None
        if l.metadata_json:
            try:
                meta = json.loads(l.metadata_json)
            except Exception:
                meta = {"raw": l.metadata_json}
                
        results.append({
            "id": l.id,
            "user_id": l.user_id,
            "user_name": u.name if u else (l.user_agent[:25] if l.user_agent else "System"),
            "user_email": u.email if u else None,
            "organization_id": l.organization_id,
            "organization_name": o.name if o else "Platform Root",
            "action": l.action,
            "resource": l.resource,
            "resource_id": l.resource_id,
            "ip_address": l.ip_address,
            "user_agent": l.user_agent,
            "result": l.result or "SUCCESS",
            "metadata": meta,
            "timestamp": l.timestamp
        })
    return results
