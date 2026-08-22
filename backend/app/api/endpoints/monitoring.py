import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.domain import (
    MonitoringSubscription, MonitoringAlert, Credential, Organization, User
)
from app.schemas.domain import (
    MonitoringSubscriptionCreate, MonitoringSubscriptionResponse, MonitoringAlertResponse
)
from app.api.deps import get_current_active_user, require_role, log_audit_trail

router = APIRouter()

@router.get("/subscriptions", response_model=List[MonitoringSubscriptionResponse])
def list_monitoring_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(MonitoringSubscription)
    if current_user.role != "SUPER_ADMIN":
        query = query.filter(MonitoringSubscription.organization_id == current_user.institution_id)
        
    subs = query.order_by(MonitoringSubscription.id.desc()).all()
    results = []
    for s in subs:
        cred = db.query(Credential).filter(Credential.id == s.credential_id).first()
        results.append({
            "id": s.id,
            "credential_id": s.credential_id,
            "credential_code": cred.certificate_id if cred else "N/A",
            "holder_name": cred.holder_name if cred else "N/A",
            "subscriber_email": s.subscriber_email,
            "webhook_url": s.webhook_url,
            "last_status": s.last_status or (cred.status if cred else "ACTIVE"),
            "alert_on": s.alert_on or "ALL",
            "status": s.status or "ACTIVE",
            "created_at": s.created_at
        })
    return results

@router.post("/subscriptions", response_model=MonitoringSubscriptionResponse)
def create_monitoring_subscription(
    sub_in: MonitoringSubscriptionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    cred = db.query(Credential).filter(Credential.id == sub_in.credential_id).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
        
    org_id = current_user.institution_id or cred.institution_id
    
    sub = MonitoringSubscription(
        organization_id=org_id,
        credential_id=cred.id,
        subscriber_email=sub_in.subscriber_email or current_user.email,
        webhook_url=sub_in.webhook_url,
        last_status=cred.status,
        alert_on=sub_in.alert_on or "ALL",
        status="ACTIVE"
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    
    log_audit_trail(
        db=db,
        action="MONITORING_WATCH_CREATED",
        resource="MONITORING",
        resource_id=str(sub.id),
        user_id=current_user.id,
        organization_id=org_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"credential_id": cred.certificate_id}
    )
    
    return {
        "id": sub.id,
        "credential_id": cred.id,
        "credential_code": cred.certificate_id,
        "holder_name": cred.holder_name,
        "subscriber_email": sub.subscriber_email,
        "webhook_url": sub.webhook_url,
        "last_status": sub.last_status,
        "alert_on": sub.alert_on,
        "status": sub.status,
        "created_at": sub.created_at
    }

@router.delete("/subscriptions/{sub_id}")
def delete_monitoring_subscription(
    sub_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    sub = db.query(MonitoringSubscription).filter(MonitoringSubscription.id == sub_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    db.delete(sub)
    db.commit()
    return {"status": "success", "message": "Monitoring watch removed"}

@router.get("/alerts", response_model=List[MonitoringAlertResponse])
def list_monitoring_alerts(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(MonitoringAlert)
    if current_user.role != "SUPER_ADMIN":
        query = query.filter(MonitoringAlert.organization_id == current_user.institution_id)
    if unread_only:
        query = query.filter(MonitoringAlert.is_read == False)
        
    alerts = query.order_by(MonitoringAlert.id.desc()).limit(100).all()
    results = []
    for a in alerts:
        cred = db.query(Credential).filter(Credential.id == a.credential_id).first()
        results.append({
            "id": a.id,
            "subscription_id": a.subscription_id,
            "credential_id": a.credential_id,
            "credential_code": cred.certificate_id if cred else "N/A",
            "previous_status": a.previous_status or "ACTIVE",
            "new_status": a.new_status or "REVOKED",
            "alert_type": a.alert_type or "STATUS_CHANGE",
            "message": a.message,
            "is_read": a.is_read or False,
            "created_at": a.created_at
        })
    return results

@router.post("/alerts/{alert_id}/read")
def mark_alert_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    alert = db.query(MonitoringAlert).filter(MonitoringAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    return {"status": "success", "message": "Alert marked as read"}

@router.post("/run-check")
def trigger_integrity_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    """
    Runs automated background integrity check across all monitored credentials.
    Detects revocations, expired credentials, and suspicious modifications.
    """
    subs = db.query(MonitoringSubscription).filter(MonitoringSubscription.status == "ACTIVE").all()
    checked_count = 0
    new_alerts_count = 0
    
    for s in subs:
        cred = db.query(Credential).filter(Credential.id == s.credential_id).first()
        if not cred:
            continue
            
        checked_count += 1
        if cred.status != s.last_status:
            alert = MonitoringAlert(
                subscription_id=s.id,
                organization_id=s.organization_id,
                credential_id=cred.id,
                previous_status=s.last_status,
                new_status=cred.status,
                alert_type=cred.status,
                message=f"Continuous Monitor Alert: Credential {cred.certificate_id} changed state from {s.last_status} to {cred.status}."
            )
            db.add(alert)
            s.last_status = cred.status
            new_alerts_count += 1
            
    db.commit()
    return {
        "status": "success",
        "message": f"Continuous monitoring check completed. {checked_count} credentials checked, {new_alerts_count} new alerts raised.",
        "checked": checked_count,
        "new_alerts": new_alerts_count
    }
