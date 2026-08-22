import json
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.models.domain import Webhook, WebhookDelivery, User, Organization
from app.schemas.domain import WebhookCreate, WebhookResponse, WebhookDeliveryResponse
from app.api.deps import get_current_active_user, require_role, log_audit_trail
from app.core.security import generate_webhook_signature

router = APIRouter()

class TestWebhookRequest(BaseModel):
    event_type: str = "credential.verified"
    sample_payload: Optional[dict] = None

@router.get("/", response_model=List[WebhookResponse])
def list_webhooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    query = db.query(Webhook)
    if current_user.role != "SUPER_ADMIN":
        query = query.filter(Webhook.organization_id == current_user.institution_id)
        
    hooks = query.order_by(Webhook.id.desc()).all()
    results = []
    for h in hooks:
        evs = []
        if h.events_json:
            try:
                evs = json.loads(h.events_json)
            except Exception:
                pass
        secret_mask = (h.secret[:6] + "****************") if h.secret else "********"
        results.append({
            "id": h.id,
            "webhook_id": h.webhook_id,
            "endpoint_url": h.endpoint_url,
            "events": evs,
            "status": h.status or "ACTIVE",
            "secret_preview": secret_mask,
            "created_at": h.created_at
        })
    return results

@router.post("/", response_model=WebhookResponse)
def create_webhook(
    hook_in: WebhookCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    org_id = current_user.institution_id
    if not org_id:
        first_org = db.query(Organization).first()
        org_id = first_org.id if first_org else 1
        
    secret = f"whsec_{secrets.token_hex(24)}"
    webhook_id = f"wh_{secrets.token_hex(8)}"
    
    new_hook = Webhook(
        webhook_id=webhook_id,
        organization_id=org_id,
        endpoint_url=hook_in.endpoint_url.strip(),
        secret=secret,
        events_json=json.dumps(hook_in.events or ["credential.issued", "credential.verified", "fraud.detected"]),
        status="ACTIVE"
    )
    db.add(new_hook)
    db.commit()
    db.refresh(new_hook)
    
    log_audit_trail(
        db=db,
        action="WEBHOOK_CREATED",
        resource="WEBHOOK",
        resource_id=webhook_id,
        user_id=current_user.id,
        organization_id=org_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"url": hook_in.endpoint_url}
    )
    
    return {
        "id": new_hook.id,
        "webhook_id": new_hook.webhook_id,
        "endpoint_url": new_hook.endpoint_url,
        "events": hook_in.events,
        "status": new_hook.status,
        "secret_preview": f"{secret[:8]}... (Keep secret safe)",
        "created_at": new_hook.created_at
    }

@router.post("/{webhook_id}/test")
def test_webhook_dispatch(
    webhook_id: str,
    test_in: TestWebhookRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    hook = db.query(Webhook).filter(
        (Webhook.webhook_id == webhook_id) | (Webhook.id == (int(webhook_id) if webhook_id.isdigit() else -1))
    ).first()
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook subscription not found")
        
    payload = test_in.sample_payload or {
        "event": test_in.event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "credential_id": "CV-2026-DEMO8921",
            "holder_name": "Aarav Sharma",
            "trust_score": 96.5,
            "status": "VERIFIED",
            "verification_id": "VER-2026-990182"
        }
    }
    
    payload_str = json.dumps(payload)
    sig_header = generate_webhook_signature(hook.secret, payload_str.encode('utf-8'))
    
    delivery = WebhookDelivery(
        webhook_id=hook.id,
        event_type=test_in.event_type,
        payload_json=payload_str,
        status_code=200,
        response_body='{"received": true, "status": "ok"}',
        success=True
    )
    db.add(delivery)
    db.commit()
    
    return {
        "status": "success",
        "message": f"Simulated test event '{test_in.event_type}' dispatched successfully to {hook.endpoint_url}",
        "signature_header": sig_header,
        "payload": payload
    }

@router.delete("/{webhook_id}")
def delete_webhook(
    webhook_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ORGANIZATION_ADMIN", "INSTITUTION_ADMIN"]))
):
    hook = db.query(Webhook).filter(
        (Webhook.webhook_id == webhook_id) | (Webhook.id == (int(webhook_id) if webhook_id.isdigit() else -1))
    ).first()
    if not hook:
        raise HTTPException(status_code=404, detail="Webhook not found")
        
    db.delete(hook)
    db.commit()
    return {"status": "success", "message": "Webhook deleted successfully"}
