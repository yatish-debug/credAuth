"""
SSBT Platform Automated Test Suite
Tests authentication, multi-tenancy, user management, credential issuance, 
RSA-PSS cryptographic signing, unified verification, evidence dossiers, 
fraud workflows, API key authentication, continuous monitoring, and clean database reset.
"""

import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal
from app.models.domain import User, Organization, Credential, FraudCase
from app.core.security import get_password_hash
from app.crypto.signing import generate_institution_keypair

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure at least the Super Admin user exists before tests run"""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@ssbt.demo").first()
        if not admin:
            admin = User(
                name="CredAuth Root Super Admin",
                email="admin@ssbt.demo",
                password_hash=get_password_hash("admin123"),
                role="SUPER_ADMIN",
                institution_id=None,
                is_active=True
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

def test_platform_health_root():
    """Verify platform health and metadata at root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert "CredAuth" in data["platform"]
    assert data["version"] == "2.5.0"

def test_rbac_authentication_flow():
    """Verify login authentication returns scoped role and JWT access token"""
    res = client.post("/api/v1/auth/login", data={
        "username": "admin@ssbt.demo",
        "password": "admin123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "SUPER_ADMIN"

    token = data["access_token"]
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@ssbt.demo"

def test_credential_issuance_and_cryptographic_signature():
    """Verify Super Admin can onboard an organization, create user, and issue RSA-PSS signed credential"""
    # 1. Login as Super Admin
    login_res = client.post("/api/v1/auth/login", data={
        "username": "admin@ssbt.demo",
        "password": "admin123"
    })
    assert login_res.status_code == 200
    admin_token = login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Ensure test organization exists
    db = SessionLocal()
    org = db.query(Organization).filter(Organization.institution_code == "DEMO_UNIV").first()
    if not org:
        priv, pub, fp = generate_institution_keypair()
        org = Organization(
            name="Demo University of Technology",
            institution_code="DEMO_UNIV",
            organization_type="UNIVERSITY",
            official_domain="demo-university.edu",
            description="Leading technical institute.",
            private_key=priv,
            public_key=pub,
            key_fingerprint=fp,
            trust_score=98.5,
            status="ACTIVE"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
    org_id = org.id
    db.close()

    # 3. Issue credential
    payload = {
        "certificate_type": "Bachelor Degree",
        "category": "ACADEMIC",
        "holder_name": "Test Candidate Alpha",
        "student_id": "PRN-2026-TEST01",
        "course_name": "B.Tech in Artificial Intelligence",
        "department": "Computer Science & Engineering",
        "academic_year": "2022-2026",
        "cgpa": 9.5,
        "grade": "First Class with Distinction",
        "issue_date": "2026-06-15T00:00:00",
        "organization_id": org_id
    }

    issue_res = client.post("/api/v1/certificates", json=payload, headers=admin_headers)
    assert issue_res.status_code == 200
    cert = issue_res.json()
    assert cert["certificate_id"].startswith("CV-2026-")
    assert cert["holder_name"] == "Test Candidate Alpha"
    assert cert["digital_signature"] is not None
    assert cert["signature_algorithm"] == "RSA-PSS-SHA256"
    assert cert["document_hash"] is not None

def test_unified_verification_and_trust_score():
    """Verify unified verification endpoint returns trust score (0-100) and evidence record"""
    db = SessionLocal()
    sample_cred = db.query(Credential).filter(Credential.status == "ACTIVE").first()
    assert sample_cred is not None
    cred_id = sample_cred.certificate_id
    db.close()

    ver_res = client.post("/api/v1/verify", json={
        "credential_id": cred_id,
        "verification_method": "API"
    })
    assert ver_res.status_code == 200
    data = ver_res.json()
    assert data["credential_id"] == cred_id
    assert data["final_result"] in ["VERIFIED", "REVIEW_REQUIRED", "HIGH_RISK"]
    assert "trust_score" in data
    assert 0 <= data["trust_score"] <= 100
    assert "trust_breakdown" in data
    assert "fraud_risk_score" in data
    assert "verification_id" in data
    assert data["verification_id"].startswith("VER-2026-")

def test_qr_code_verification():
    """Verify QR token verification endpoint"""
    db = SessionLocal()
    sample_cred = db.query(Credential).filter(Credential.status == "ACTIVE").first()
    assert sample_cred is not None
    qr_token = sample_cred.qr_token
    cred_id = sample_cred.certificate_id
    db.close()

    qr_res = client.get(f"/api/v1/verify/qr/{qr_token}")
    assert qr_res.status_code == 200
    data = qr_res.json()
    assert data["final_result"] == "VERIFIED"
    assert data["credential_id"] == cred_id

def test_evidence_dossier_retrieval():
    """Verify immutable evidence dossier lookup by verification ID"""
    db = SessionLocal()
    sample_cred = db.query(Credential).filter(Credential.status == "ACTIVE").first()
    assert sample_cred is not None
    cred_id = sample_cred.certificate_id
    db.close()

    ver_res = client.post("/api/v1/verify", json={
        "credential_id": cred_id,
        "verification_method": "MANUAL_ID"
    })
    assert ver_res.status_code == 200
    ver_id = ver_res.json()["verification_id"]

    ev_res = client.get(f"/api/v1/evidence/{ver_id}")
    assert ev_res.status_code == 200
    evidence = ev_res.json()
    assert evidence["verification_id"] == ver_id
    assert evidence["trust_score"] >= 0
    assert evidence["verified_record"] is not None

def test_fraud_investigation_workflow():
    """Verify fraud case triage, investigator note, and resolution"""
    login_res = client.post("/api/v1/auth/login", data={
        "username": "admin@ssbt.demo",
        "password": "admin123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Ensure at least 1 fraud case exists for testing
    db = SessionLocal()
    case = db.query(FraudCase).first()
    if not case:
        cred = db.query(Credential).first()
        case = FraudCase(
            case_id="FC-2026-TEST01",
            credential_id=cred.id if cred else None,
            organization_id=cred.institution_id if cred else None,
            risk_score=88.5,
            risk_level="HIGH_RISK",
            status="OPEN",
            indicators_json='["Digital Signature Verification Failed", "OCR tampering detected"]'
        )
        db.add(case)
        db.commit()
    case_id = case.case_id
    db.close()

    # Add investigator note
    note_res = client.post(f"/api/v1/fraud/cases/{case_id}/note", json={
        "note": "Pytest automated compliance audit check passed."
    }, headers=headers)
    assert note_res.status_code == 200
    assert note_res.json()["status"].lower() == "success"

    # Resolve fraud case
    resolve_res = client.post(f"/api/v1/fraud/cases/{case_id}/resolve", json={
        "resolution": "CONFIRMED_FRAUD",
        "notes": "Pytest resolved case confirming fraud.",
        "auto_revoke_credential": False
    }, headers=headers)
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"].lower() == "success"

def test_api_key_management_and_authentication():
    """Verify scoped API key generation and header authentication"""
    login_res = client.post("/api/v1/auth/login", data={
        "username": "admin@ssbt.demo",
        "password": "admin123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate API key
    key_res = client.post("/api/v1/api-keys", json={
        "name": "Pytest Test Suite ATS Integration",
        "environment": "TEST",
        "rate_limit_per_minute": 60,
        "permissions": ["credential:read", "credential:verify"]
    }, headers=headers)
    assert key_res.status_code == 200
    key_data = key_res.json()
    raw_api_key = key_data["raw_api_key"]
    assert raw_api_key.startswith("ssbt_test_")

    # Fetch active credential
    db = SessionLocal()
    sample_cred = db.query(Credential).filter(Credential.status == "ACTIVE").first()
    assert sample_cred is not None
    cred_id = sample_cred.certificate_id
    db.close()

    # Use raw API key in X-API-Key header to query verification
    api_ver_res = client.post("/api/v1/verify", json={
        "credential_id": cred_id,
        "verification_method": "API"
    }, headers={"X-API-Key": raw_api_key})
    assert api_ver_res.status_code == 200
    assert api_ver_res.json()["final_result"] == "VERIFIED"

def test_continuous_monitoring_integrity_scan():
    """Verify continuous monitoring integrity scan trigger"""
    login_res = client.post("/api/v1/auth/login", data={
        "username": "admin@ssbt.demo",
        "password": "admin123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    scan_res = client.post("/api/v1/monitoring/run-check", headers=headers)
    assert scan_res.status_code == 200
    assert scan_res.json()["status"] == "success"
    assert "checked" in scan_res.json()

def test_immutable_audit_logs_retrieval():
    """Verify audit log compliance trail retrieval"""
    login_res = client.post("/api/v1/auth/login", data={
        "username": "admin@ssbt.demo",
        "password": "admin123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    audit_res = client.get("/api/v1/audit/logs?limit=20", headers=headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) > 0
    assert "action" in logs[0]
    assert "resource" in logs[0]

def test_user_management_by_super_admin():
    """Verify Super Admin can list, create, and delete users of any role"""
    login_res = client.post("/api/v1/auth/login", data={
        "username": "admin@ssbt.demo",
        "password": "admin123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a custom Organization Admin user
    create_res = client.post("/api/v1/users", json={
        "name": "Custom Dean Admin",
        "email": "custom.dean@demo-test.edu",
        "password": "password123",
        "role": "ORGANIZATION_ADMIN",
        "organization_id": None
    }, headers=headers)
    assert create_res.status_code == 200
    new_user = create_res.json()
    assert new_user["email"] == "custom.dean@demo-test.edu"
    assert new_user["role"] == "ORGANIZATION_ADMIN"
    user_id = new_user["id"]

    # 2. List users
    list_res = client.get("/api/v1/users", headers=headers)
    assert list_res.status_code == 200
    users = list_res.json()
    assert any(u["id"] == user_id for u in users)

    # 3. Delete the created user
    del_res = client.delete(f"/api/v1/users/{user_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "SUCCESS"

def test_database_reset_to_zero_and_super_admin_retention():
    """Verify clean database reset wipes demo data and retains only 1 Super Admin"""
    login_res = client.post("/api/v1/auth/login", data={
        "username": "admin@ssbt.demo",
        "password": "admin123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Execute clean database reset
    reset_res = client.post("/api/v1/admin/reset-database", json={
        "confirm_reset": True,
        "super_admin_email": "admin@ssbt.demo",
        "super_admin_password": "admin123",
        "super_admin_name": "CredAuth Root Super Admin"
    }, headers=headers)
    assert reset_res.status_code == 200
    res_data = reset_res.json()
    assert res_data["status"] == "CLEAN_DATABASE_RESET"
    assert res_data["stats"]["users"] == 1
    assert res_data["stats"]["credentials"] == 0
    assert res_data["stats"]["organizations"] == 0

    # Verify Super Admin can authenticate immediately on clean slate
    post_login = client.post("/api/v1/auth/login", data={
        "username": "admin@ssbt.demo",
        "password": "admin123"
    })
    assert post_login.status_code == 200
    new_token = post_login.json()["access_token"]
    assert new_token is not None
