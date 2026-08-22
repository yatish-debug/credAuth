#!/usr/bin/env python3
"""
CredAuth — Clean Database Reset Script
Wipes all demo data across all tables and sets up a fresh database with 
ONLY 1 user: the Root Super Admin.
"""

import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models.domain import (
    User, Organization, Credential, VerificationRequest, 
    VerificationResult, FraudCase, ApiKey, Webhook, 
    WebhookDelivery, MonitoringSubscription, MonitoringAlert, AuditLog
)

def reset_clean_database():
    print("=" * 70)
    print("CREDAUTH PLATFORM — CLEAN DATABASE RESET (ZERO DEMO DATA)")
    print("=" * 70)
    
    db = SessionLocal()
    try:
        print("[1/3] Wiping all existing records from database...")
        db.query(AuditLog).delete()
        db.query(MonitoringAlert).delete()
        db.query(MonitoringSubscription).delete()
        db.query(WebhookDelivery).delete()
        db.query(Webhook).delete()
        db.query(ApiKey).delete()
        db.query(FraudCase).delete()
        db.query(VerificationResult).delete()
        db.query(VerificationRequest).delete()
        db.query(Credential).delete()
        db.query(User).delete()
        db.query(Organization).delete()
        db.commit()
        print("      [OK] Database tables wiped successfully.")

        print("[2/3] Creating single Root Super Admin account...")
        super_admin = User(
            name="CredAuth Root Super Admin",
            email="admin@ssbt.demo",
            password_hash=get_password_hash("admin123"),
            role="SUPER_ADMIN",
            institution_id=None,
            is_active=True
        )
        db.add(super_admin)
        db.commit()
        db.refresh(super_admin)
        print(f"      [OK] Created Super Admin: {super_admin.email} (Role: {super_admin.role})")

        print("[3/3] Recording clean reset in immutable audit trail...")
        audit = AuditLog(
            action="DATABASE_RESET_TO_ZERO",
            resource="SYSTEM_DATABASE",
            resource_id="0",
            user_id=super_admin.id,
            result="SUCCESS",
            metadata_json='{"message": "Clean database reset executed via CLI.", "users_count": 1}'
        )
        db.add(audit)
        db.commit()
        print("      [OK] Clean audit entry recorded.")

        print("=" * 70)
        print("DATABASE SUCCESSFULLY RESET TO 0!")
        print("Active Users: 1 (Super Admin)")
        print("Organizations: 0")
        print("Credentials: 0")
        print("Fraud Cases: 0")
        print("API Keys: 0")
        print("Webhooks: 0")
        print("-" * 70)
        print("Super Admin Login Credentials:")
        print("  Email:    admin@ssbt.demo")
        print("  Password: admin123")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"ERROR during clean database reset: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    reset_clean_database()
