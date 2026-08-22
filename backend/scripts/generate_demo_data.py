import os
import sys
import json
import uuid
import random
import hashlib
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives import serialization

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine, Base
from app.models.domain import (
    Organization, User, Credential, CredentialStatusHistory, 
    VerificationRequest, VerificationResult, FraudCase, 
    ApiKey, Webhook, WebhookDelivery, MonitoringSubscription, 
    MonitoringAlert, AuditLog
)
from app.core.security import get_password_hash, generate_api_key
from app.crypto.signing import generate_institution_keypair, sign_certificate_payload

def generate_synthetic_demo_data():
    print("==================================================================")
    print("[*] GENERATING REALISTIC B2B SYNTHETIC DATA FOR SSBT PLATFORM...")
    print("==================================================================")
    
    # Drop and recreate tables for clean schema migration
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # =========================================================================
    # 1. ORGANIZATIONS (4 Diverse Tenants)
    # =========================================================================
    org_configs = [
        {
            "name": "SSBT Demo University",
            "code": "SSBT_UNIV_01",
            "type": "UNIVERSITY",
            "reg_no": "UGC-IND-2018-842",
            "domain": "ssbt-university.edu",
            "email": "registrar@ssbt-university.edu",
            "phone": "+1 (555) 234-8901",
            "address": "400 Academic Way, Tech Corridor, California 94016",
            "desc": "Premier research institution offering accredited engineering, computing, and cybersecurity degrees.",
            "trust_score": 97.5
        },
        {
            "name": "Apex Technical Institute",
            "code": "APEX_TECH_02",
            "type": "TRAINING_INSTITUTE",
            "reg_no": "ISO-9001-TECH-789",
            "domain": "apextech.institute",
            "email": "contact@apextech.institute",
            "phone": "+1 (555) 456-7812",
            "address": "750 Innovation Blvd, Suite 400, Austin, Texas 78701",
            "desc": "Leading professional certification provider for Cloud Architecture, Full-Stack Engineering, and AI Systems.",
            "trust_score": 94.0
        },
        {
            "name": "Global Skills Certification Body",
            "code": "GLOBAL_SKILLS_03",
            "type": "CERTIFICATION_BODY",
            "reg_no": "ANSI-CERT-2024-0012",
            "domain": "globalskills.org",
            "email": "governance@globalskills.org",
            "phone": "+1 (555) 890-1234",
            "address": "1200 Standards Plaza, New York, NY 10001",
            "desc": "International credentialing council establishing benchmark examinations and cybersecurity licensure.",
            "trust_score": 98.2
        },
        {
            "name": "Vertex Enterprise Corporation",
            "code": "VERTEX_CORP_04",
            "type": "CORPORATION",
            "reg_no": "DELAWARE-CORP-C8912",
            "domain": "vertexcorp.demo",
            "email": "talent-verify@vertexcorp.demo",
            "phone": "+1 (555) 901-5678",
            "address": "100 Wall Street, 24th Floor, New York, NY 10005",
            "desc": "Global technology enterprise issuing verified employment credentials, experience letters, and engineering awards.",
            "trust_score": 93.8
        }
    ]

    created_orgs = []
    org_key_objects = {}

    for cfg in org_configs:
        priv_key_pem, pub_key_pem, fp = generate_institution_keypair()
        priv_obj = serialization.load_pem_private_key(priv_key_pem.encode('utf-8'), password=None)
        
        org = Organization(
            name=cfg["name"],
            institution_code=cfg["code"],
            organization_type=cfg["type"],
            registration_number=cfg["reg_no"],
            official_domain=cfg["domain"],
            description=cfg["desc"],
            contact_email=cfg["email"],
            contact_phone=cfg["phone"],
            address=cfg["address"],
            verification_status="VERIFIED",
            status="ACTIVE",
            trust_score=cfg["trust_score"],
            public_key=pub_key_pem,
            private_key=priv_key_pem,
            key_algorithm="RSA-2048",
            key_fingerprint=fp,
            features_config=json.dumps({
                "suspicious_threshold": 0.5,
                "allow_revocation": True,
                "allow_reinstate": True,
                "require_revocation_reason": True,
                "qr_verification_enabled": True,
                "ocr_document_check_enabled": True,
                "digital_signatures_enabled": True,
                "signature_algorithm": "RSA-PSS-SHA256"
            })
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        created_orgs.append(org)
        org_key_objects[org.id] = priv_obj
        print(f"  [+] Created Organization: {org.name} ({org.institution_code})")

    # =========================================================================
    # 2. USERS (Roles: Super Admin, Org Admin, Issuer, Verifier, Auditor)
    # =========================================================================
    users_data = [
        # Platform Root Super Admins
        {"name": "Super Admin", "email": "admin@ssbt.demo", "password": "admin123", "role": "SUPER_ADMIN", "org": None, "org_id": None},
        {"name": "Platform Root", "email": "admin@credverify.demo", "password": "admin123", "role": "SUPER_ADMIN", "org": None, "org_id": None},
        
        # Org Admins
        {"name": "Dr. Ramesh Kulkarni", "email": "univadmin@demo-university.edu", "password": "univadmin123", "role": "ORGANIZATION_ADMIN", "org": created_orgs[0].name, "org_id": created_orgs[0].id},
        {"name": "Institution Admin (Legacy)", "email": "instadmin@demo-institute.edu", "password": "instadmin123", "role": "INSTITUTION_ADMIN", "org": created_orgs[0].name, "org_id": created_orgs[0].id},
        {"name": "Sarah Jenkins", "email": "admin@apextech.institute", "password": "apexadmin123", "role": "ORGANIZATION_ADMIN", "org": created_orgs[1].name, "org_id": created_orgs[1].id},
        {"name": "Marcus Vance", "email": "admin@globalskills.org", "password": "globalskills123", "role": "ORGANIZATION_ADMIN", "org": created_orgs[2].name, "org_id": created_orgs[2].id},
        {"name": "Elena Rostova", "email": "admin@vertexcorp.demo", "password": "vertexadmin123", "role": "ORGANIZATION_ADMIN", "org": created_orgs[3].name, "org_id": created_orgs[3].id},
        
        # Credential Issuers
        {"name": "Prof. David Chen", "email": "chen.issuer@ssbt-university.edu", "password": "issuer123", "role": "CREDENTIAL_ISSUER", "org": created_orgs[0].name, "org_id": created_orgs[0].id},
        {"name": "Priya Nair", "email": "priya.nair@apextech.institute", "password": "issuer123", "role": "CREDENTIAL_ISSUER", "org": created_orgs[1].name, "org_id": created_orgs[1].id},
        {"name": "HR Talent Officer", "email": "hr.issuer@vertexcorp.demo", "password": "issuer123", "role": "CREDENTIAL_ISSUER", "org": created_orgs[3].name, "org_id": created_orgs[3].id},
        
        # Verification Officers / Recruiters
        {"name": "Rohit Recruiter", "email": "rohit.recruiter@infosys.com", "password": "infosys_verifier_pass", "role": "VERIFICATION_OFFICER", "org": "Infosys Global Recruitment", "org_id": None},
        {"name": "TCS Verification Lead", "email": "tcs.verifier@tcs.demo", "password": "verifier123", "role": "VERIFICATION_OFFICER", "org": "TCS Background Verification Team", "org_id": None},
        {"name": "Google Talent Screener", "email": "google.recruiter@google.demo", "password": "verifier123", "role": "VERIFICATION_OFFICER", "org": "Google Talent Operations", "org_id": None},
        
        # Auditors
        {"name": "Compliance Auditor", "email": "auditor@kpmg.demo", "password": "auditor123", "role": "AUDITOR", "org": "KPMG Audit & Assurance", "org_id": None},
    ]

    created_users = []
    for u in users_data:
        user = User(
            name=u["name"],
            email=u["email"],
            password_hash=get_password_hash(u["password"]),
            role=u["role"],
            organization=u["org"],
            institution_id=u["org_id"],
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        created_users.append(user)
    print(f"  [+] Created {len(created_users)} Multi-Role RBAC Users")

    # =========================================================================
    # 3. 500+ REALISTIC SYNTHETIC CREDENTIALS
    # =========================================================================
    first_names = [
        "Aarav", "Aditi", "Ananya", "Arjun", "Dev", "Diya", "Ishaan", "Kavya", 
        "Manish", "Neha", "Pooja", "Pranav", "Rahul", "Riya", "Rohan", "Sanjay", 
        "Shreya", "Sneha", "Tanvi", "Varun", "Vikas", "Yash", "Alexander", "Emily", 
        "Michael", "Sophia", "Daniel", "Olivia", "James", "Emma", "Liam", "Ava"
    ]
    last_names = [
        "Sharma", "Patel", "Bharambe", "Verma", "Kulkarni", "Deshmukh", "Gupta", 
        "Mehta", "Iyer", "Nair", "Reddy", "Chopra", "Joshi", "Bhat", "Kapoor", 
        "Singh", "Rao", "Mishra", "Patil", "Smith", "Johnson", "Williams", "Brown", 
        "Taylor", "Miller", "Davis", "Wilson"
    ]
    
    academic_courses = [
        ("B.Tech in Computer Engineering", "Computer Engineering", "First Class with Distinction", 9.4),
        ("B.Tech in Cybersecurity & Privacy", "Information Technology", "First Class with Distinction", 9.1),
        ("M.S. in Artificial Intelligence", "Computer Science", "First Class with Honors", 9.6),
        ("B.Sc in Data Science & Statistics", "Data Science", "First Class", 8.7),
        ("B.Tech in Electronics & Telecommunication", "Electronics", "First Class", 8.5),
        ("Master of Business Administration (MBA)", "Business Management", "Distinction", 8.9),
        ("Postgraduate Diploma in Cloud Security", "Security Operations", "First Class with Distinction", 9.2),
        ("B.Tech in Information Technology", "Information Technology", "First Class with Distinction", 8.8)
    ]
    
    recruitment_roles = [
        ("Senior Security Engineer", "Information Security", "Full-Time", "Exceeds Expectations"),
        ("Lead Cloud Infrastructure Architect", "Cloud Operations", "Full-Time", "Outstanding"),
        ("Machine Learning Research Scientist", "AI Labs", "Full-Time", "Top 5% Performer"),
        ("Full-Stack Software Engineer", "Product Engineering", "Full-Time", "Exceeds Expectations"),
        ("DevSecOps Specialist", "Platform Reliability", "Full-Time", "Strong Performance"),
        ("Cyber Threat Intelligence Analyst", "SOC & Threat Intel", "Full-Time", "Exceeds Expectations")
    ]
    
    tech_certs = [
        ("Certified Enterprise Cloud Architect", "AWS & Kubernetes", "EXAM-AWS-902", "96.5 Percentile"),
        ("Offensive Security & Ethical Hacking Expert", "Penetration Testing", "OS-EH-2026-44", "Top 2% Globally"),
        ("Deep Learning & LLM Systems Specialist", "PyTorch, CUDA & Transformers", "AI-LLM-891", "98.0 Score"),
        ("Kubernetes Security Specialist (CKS)", "Container Security", "CKS-2026-912", "Pass with Merit"),
        ("Certified Information Systems Security Professional", "Zero Trust Architecture", "CISSP-8912-V", "Certified Master")
    ]
    
    award_titles = [
        ("1st Place Grand Winner — National AI Hackathon", "Generative AI Track", "Gold Trophy & $25,000 Award"),
        ("Excellence in Cybersecurity Innovation Award", "Zero-Trust Architecture", "Outstanding Research Citation"),
        ("Top Researcher in Distributed Systems", "ACM Research Chapter", "Honorary Fellowship Medal"),
        ("Champion — International Smart India Hackathon", "Fintech Fraud Defense", "National Gold Medal")
    ]

    print("  [*] Generating 525 Cryptographically Signed Credentials...")
    
    created_creds = []
    
    for i in range(525):
        h_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        cert_num = 10000 + i
        cert_id = f"CV-2026-{cert_num}"
        qr_tok = uuid.uuid4().hex
        
        # Pick category
        cat_rand = random.random()
        if cat_rand < 0.45:
            # ACADEMIC (45%)
            org = created_orgs[0] # SSBT Univ
            cat = "ACADEMIC"
            ctype = "Bachelor Degree" if "B.Tech" in academic_courses[i % len(academic_courses)][0] else "Master Degree"
            course_tpl = academic_courses[i % len(academic_courses)]
            c_name = course_tpl[0]
            dept = course_tpl[1]
            grade = course_tpl[2]
            cgpa = round(course_tpl[3] + random.uniform(-0.6, 0.4), 2)
            cgpa = min(10.0, max(6.5, cgpa))
            student_id = f"PRN-2026-{random.randint(10000, 99999)}"
            marks_ob = round(cgpa * 95.0, 1)
            tot_marks = 1000.0
            pct = round((marks_ob / tot_marks) * 100, 2)
            role_desig = None
            skills = None
            emp_type = None
            lic_no = None
            score_rk = None
            ayear = "2022-2026"
            remarks = "Graduated with official academic distinction."
        elif cat_rand < 0.70:
            # RECRUITMENT / EMPLOYMENT (25%)
            org = created_orgs[3] # Vertex Corp
            cat = "RECRUITMENT"
            ctype = "Experience Letter"
            role_tpl = recruitment_roles[i % len(recruitment_roles)]
            c_name = role_tpl[0]
            role_desig = role_tpl[0]
            dept = role_tpl[1]
            emp_type = role_tpl[2]
            grade = role_tpl[3]
            cgpa = None
            marks_ob = None
            tot_marks = None
            pct = None
            student_id = f"EMP-{random.randint(10000, 99999)}"
            skills = "Distributed Systems, Microservices, Python, Go, Docker, Kubernetes"
            lic_no = None
            score_rk = "Rating: 4.8/5.0"
            ayear = "2022-2025"
            remarks = "Relieved in good standing with exemplary contributions."
        elif cat_rand < 0.90:
            # TECHNICAL COURSE (20%)
            org = created_orgs[1] # Apex Tech
            cat = "TECHNICAL_COURSE"
            ctype = "Professional Certification"
            tech_tpl = tech_certs[i % len(tech_certs)]
            c_name = tech_tpl[0]
            role_desig = None
            dept = "Professional Certifications Council"
            skills = tech_tpl[1]
            lic_no = tech_tpl[2]
            score_rk = tech_tpl[3]
            grade = "Certified with Distinction"
            cgpa = None
            marks_ob = None
            tot_marks = None
            pct = None
            student_id = f"CAND-{random.randint(10000, 99999)}"
            emp_type = None
            ayear = "2025-2026"
            remarks = "Demonstrated master-level proficiency in practical exams."
        else:
            # ACHIEVEMENT / AWARDS (10%)
            org = created_orgs[2] # Global Skills
            cat = "ACHIEVEMENT"
            ctype = "Honorary Merit Award"
            aw_tpl = award_titles[i % len(award_titles)]
            c_name = aw_tpl[0]
            role_desig = None
            dept = aw_tpl[1]
            skills = "Innovation, High-Speed Execution, AI Algorithms"
            lic_no = f"MEDAL-2026-{random.randint(100, 999)}"
            score_rk = aw_tpl[2]
            grade = "1st Place Gold"
            cgpa = None
            marks_ob = None
            tot_marks = None
            pct = None
            student_id = f"TEAM-{random.randint(100, 999)}"
            emp_type = None
            ayear = "2026"
            remarks = "Recognized by industry jury for groundbreaking technical excellence."

        # Assign Lifecycle Status
        # 465 ACTIVE, 25 REVOKED, 20 EXPIRED, 15 SUSPICIOUS
        if i < 25:
            status = "REVOKED"
            susp_reason = "Officially revoked following disciplinary compliance review."
        elif i < 45:
            status = "EXPIRED"
            susp_reason = None
        elif i < 60:
            status = "SUSPICIOUS"
            susp_reason = "Flagged for manual OCR attribute discrepancy review."
        else:
            status = "ACTIVE"
            susp_reason = None

        issue_dt = datetime(2026, 1, 15) - timedelta(days=random.randint(10, 400))
        exp_dt = (issue_dt + timedelta(days=365*3)) if status != "EXPIRED" else (issue_dt + timedelta(days=30))

        # Synthetic SHA-256 digest
        raw_to_hash = f"{cert_id}:{h_name}:{c_name}:{org.institution_code}:{issue_dt.isoformat()}"
        doc_hash = hashlib.sha256(raw_to_hash.encode('utf-8')).hexdigest()
        
        canonical_payload = {
            "certificate_id": cert_id,
            "holder_name": h_name,
            "student_id": student_id or "",
            "course_name": c_name,
            "grade": grade or "",
            "cgpa": str(cgpa) if cgpa is not None else "",
            "institution_code": org.institution_code,
            "issue_date": issue_dt.strftime("%Y-%m-%d"),
            "document_hash": doc_hash,
            "qr_token": qr_tok
        }
        sig = sign_certificate_payload(org_key_objects[org.id], canonical_payload)
        
        cred = Credential(
            certificate_id=cert_id,
            institution_id=org.id,
            issuer_id=created_users[2].id, # Default issuer
            certificate_type=ctype,
            category=cat,
            holder_name=h_name,
            student_id=student_id,
            course_name=c_name,
            department=dept,
            academic_year=ayear,
            marks_obtained=marks_ob,
            total_marks=tot_marks,
            percentage=pct,
            cgpa=cgpa,
            grade=grade,
            remarks=remarks,
            role_designation=role_desig,
            organization_company=org.name,
            skills_acquired=skills,
            employment_type=emp_type,
            license_number=lic_no,
            score_or_rank=score_rk,
            issue_date=issue_dt,
            expiry_date=exp_dt,
            document_path=None,
            document_hash=doc_hash,
            qr_token=qr_tok,
            status=status,
            suspicious_reason=susp_reason,
            digital_signature=sig,
            signature_algorithm="RSA-PSS-SHA256",
            signer_public_key_fingerprint=org.key_fingerprint
        )
        db.add(cred)
        created_creds.append(cred)
        
    db.commit()
    print(f"  [+] Successfully seeded {len(created_creds)} Credentials in SQLite Registry.")

    # =========================================================================
    # 4. VERIFICATION REQUESTS & IMMUTABLE EVIDENCE (120+ Events)
    # =========================================================================
    print("  [*] Seeding 125 Verification Requests & Evidence Records...")
    methods = ["MANUAL_ID", "QR_SCAN", "UPLOAD", "API", "BATCH"]
    
    for i in range(125):
        target_cred = created_creds[i % len(created_creds)]
        ver_method = methods[i % len(methods)]
        ver_id = f"VER-2026-{100000 + i}"
        
        is_rev = (target_cred.status == "REVOKED")
        is_exp = (target_cred.status == "EXPIRED")
        is_susp = (target_cred.status == "SUSPICIOUS")
        
        if is_rev:
            res_val = "REVOKED"
            trust_sc = 15.0
            risk_sc = 85.0
            r_lvl = "CRITICAL"
            expl = "Credential was officially revoked by the issuing authority."
        elif is_susp:
            res_val = "SUSPICIOUS"
            trust_sc = 48.0
            risk_sc = 65.0
            r_lvl = "HIGH"
            expl = "Credential flagged for administrative integrity review."
        elif is_exp:
            res_val = "EXPIRED"
            trust_sc = 70.0
            risk_sc = 25.0
            r_lvl = "LOW"
            expl = "Credential validity date has expired."
        else:
            res_val = "VERIFIED"
            trust_sc = round(random.uniform(92.0, 98.5), 1)
            risk_sc = round(random.uniform(2.0, 8.0), 1)
            r_lvl = "LOW"
            expl = "Credential verified: Authenticated via RSA-PSS 2048-bit signature and SHA-256 integrity hash."
            
        req = VerificationRequest(
            organization_id=target_cred.institution_id,
            certificate_id=target_cred.id,
            searched_certificate_id=target_cred.certificate_id,
            verification_method=ver_method,
            requested_by="TCS Background Verification Team (tcs.verifier@tcs.demo)" if i % 2 == 0 else "Infosys Global Recruitment",
            timestamp=datetime.now(timezone.utc) - timedelta(hours=i*2),
            result=res_val
        )
        db.add(req)
        db.flush()
        
        result_rec = VerificationResult(
            verification_request_id=req.id,
            verification_id=ver_id,
            organization_id=target_cred.institution_id,
            credential_id=target_cred.id,
            registry_check="MATCH",
            qr_check="VALID",
            hash_check="VALID",
            signature_check="VALID",
            issuer_check="VERIFIED",
            document_analysis="CLEAN" if not is_susp else "ANOMALY_DETECTED",
            fraud_risk_score=risk_sc,
            risk_level=r_lvl,
            confidence=0.98,
            trust_score=trust_sc,
            trust_breakdown_json=json.dumps({
                "issuer_authenticity": {"score": 25.0, "max": 25.0},
                "cryptographic_integrity": {"score": 20.0, "max": 20.0},
                "registry_match": {"score": 20.0 if not is_rev else 0.0, "max": 20.0},
                "qr_verification": {"score": 15.0, "max": 15.0},
                "document_forensics": {"score": 10.0 if not is_susp else 0.0, "max": 10.0},
                "metadata_consistency": {"score": 10.0 if not is_exp else 0.0, "max": 10.0}
            }),
            issuer_trust_score=96.0,
            final_result=res_val,
            explanation=expl,
            timestamp=req.timestamp
        )
        db.add(result_rec)
        
    db.commit()
    print("  [+] Seeded 125 Verification Requests and Evidence Records.")

    # =========================================================================
    # 5. FRAUD INVESTIGATION CASES (12 Realistic Incidents)
    # =========================================================================
    print("  [*] Seeding 12 Enterprise Fraud Investigation Cases...")
    fraud_templates = [
        ("FC-2026-00101", 0, 94.0, "CRITICAL", ["CGPA_TAMPERING: Altered from 6.8 to 9.8 in PDF vector stream", "HASH_MISMATCH: File hash failed SHA-256 registry check"], "CONFIRMED_FRAUD"),
        ("FC-2026-00102", 1, 88.0, "CRITICAL", ["RECIPIENT_FORGERY: Recipient name altered to impersonate candidate", "SIGNATURE_INVALID: RSA-PSS signature failed"], "CONFIRMED_FRAUD"),
        ("FC-2026-00103", 2, 82.0, "CRITICAL", ["QR_TAMPERING: QR code points to fake domain", "ISSUER_MISMATCH: Unregistered institution code"], "UNDER_REVIEW"),
        ("FC-2026-00104", 3, 76.0, "HIGH", ["DATE_ANOMALY: Issue date precedes university charter date", "METADATA_INCONSISTENCY: PDF creator tool detected as Adobe Photoshop"], "OPEN"),
        ("FC-2026-00105", 4, 68.0, "HIGH", ["GRADE_MODIFICATION: Awarded grade altered from Pass to First Class Distinction"], "UNDER_REVIEW"),
        ("FC-2026-00106", 5, 45.0, "MEDIUM", ["OCR_SCAN_BLUR: Low quality scan triggered OCR text confidence warning"], "FALSE_POSITIVE"),
        ("FC-2026-00107", 6, 92.0, "CRITICAL", ["TENURE_TAMPERING: Employment tenure extended by 3 years on experience letter"], "CONFIRMED_FRAUD"),
        ("FC-2026-00108", 7, 72.0, "HIGH", ["LICENSE_NUMBER_DUPLICATION: Credential license code matches another active candidate"], "OPEN"),
        ("FC-2026-00109", 8, 35.0, "MEDIUM", ["MIDDLE_NAME_MISSING: OCR detected legal first & last name without middle initial"], "FALSE_POSITIVE"),
        ("FC-2026-00110", 9, 85.0, "CRITICAL", ["FONT_INCONSISTENCY: Detected non-standard typeface in Marks Table section"], "RESOLVED"),
        ("FC-2026-00111", 10, 78.0, "HIGH", ["UNAUTHORIZED_STAMP: Digital seal fingerprint differs from issuing authority key"], "OPEN"),
        ("FC-2026-00112", 11, 81.0, "HIGH", ["FORGED_SIGNATURE: Cryptographic block signature bytes corrupted"], "UNDER_REVIEW")
    ]

    for f_case in fraud_templates:
        case_id, c_idx, r_sc, r_lvl, inds, status = f_case
        target_c = created_creds[c_idx]
        
        fc = FraudCase(
            case_id=case_id,
            credential_id=target_c.id,
            organization_id=target_c.institution_id,
            risk_score=r_sc,
            risk_level=r_lvl,
            indicators_json=json.dumps(inds),
            assigned_to=created_users[2].id,
            status=status,
            notes_json=json.dumps([
                {
                    "timestamp": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
                    "author": "SSBT AI Fraud Engine",
                    "text": f"Incident Triaged: Detected {len(inds)} high-risk indicators during verification."
                },
                {
                    "timestamp": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
                    "author": "Dr. Ramesh Kulkarni (ORGANIZATION_ADMIN)",
                    "text": f"Investigator Review: Cross-checked institutional archive. Status set to {status}."
                }
            ]),
            created_at=datetime.now(timezone.utc) - timedelta(days=3),
            resolved_at=datetime.now(timezone.utc) if status in ["CONFIRMED_FRAUD", "FALSE_POSITIVE", "RESOLVED"] else None
        )
        db.add(fc)
    db.commit()
    print("  [+] Seeded 12 Fraud Investigation Cases.")

    # =========================================================================
    # 6. API KEYS & WEBHOOKS
    # =========================================================================
    print("  [*] Seeding Enterprise API Keys & Webhooks...")
    
    for org in created_orgs[:2]:
        raw_key, hashed_secret, key_id, prefix = generate_api_key("TEST")
        k_test = ApiKey(
            key_id=key_id,
            organization_id=org.id,
            name=f"{org.name} Sandbox Integration",
            environment="TEST",
            hashed_secret=hashed_secret,
            prefix=prefix,
            permissions_json=json.dumps(["credential:read", "credential:verify", "verification:create"]),
            rate_limit_per_minute=120,
            status="ACTIVE"
        )
        db.add(k_test)
        
        raw_key_p, hashed_secret_p, key_id_p, prefix_p = generate_api_key("LIVE")
        k_prod = ApiKey(
            key_id=key_id_p,
            organization_id=org.id,
            name=f"{org.name} Production HR Pipeline",
            environment="PRODUCTION",
            hashed_secret=hashed_secret_p,
            prefix=prefix_p,
            permissions_json=json.dumps(["credential:read", "credential:create", "credential:verify", "verification:create", "verification:read"]),
            rate_limit_per_minute=300,
            status="ACTIVE"
        )
        db.add(k_prod)
        
        wh = Webhook(
            webhook_id=f"wh_{uuid.uuid4().hex[:8]}",
            organization_id=org.id,
            endpoint_url=f"https://api.{org.official_domain}/webhooks/credential-events",
            secret=f"whsec_{uuid.uuid4().hex}",
            events_json=json.dumps(["credential.issued", "credential.verified", "credential.revoked", "fraud.detected"]),
            status="ACTIVE"
        )
        db.add(wh)
        db.flush()
        
        deliv = WebhookDelivery(
            webhook_id=wh.id,
            event_type="credential.verified",
            payload_json=json.dumps({"event": "credential.verified", "credential_id": "CV-2026-10024", "status": "VERIFIED", "trust_score": 96.5}),
            status_code=200,
            response_body='{"received": true}',
            success=True,
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=45)
        )
        db.add(deliv)
        
    db.commit()

    # =========================================================================
    # 7. CONTINUOUS MONITORING WATCHES & ALERTS
    # =========================================================================
    print("  [*] Seeding Continuous Credential Watches & Alert Stream...")
    for i in range(8):
        c = created_creds[i]
        sub = MonitoringSubscription(
            organization_id=c.institution_id,
            credential_id=c.id,
            subscriber_email="recruiter.watch@enterprise-hr.demo",
            webhook_url="https://hr-platform.demo/webhooks/alerts",
            last_status=c.status,
            alert_on="ALL",
            status="ACTIVE"
        )
        db.add(sub)
        db.flush()
        
        if c.status in ["REVOKED", "SUSPICIOUS"]:
            alert = MonitoringAlert(
                subscription_id=sub.id,
                organization_id=c.institution_id,
                credential_id=c.id,
                previous_status="ACTIVE",
                new_status=c.status,
                alert_type=c.status,
                message=f"Continuous Monitor Alert: Credential {c.certificate_id} for {c.holder_name} transitioned to {c.status}.",
                is_read=False
            )
            db.add(alert)
    db.commit()

    # =========================================================================
    # 8. CENTRALIZED AUDIT LOGS (80+ Events)
    # =========================================================================
    print("  [*] Seeding 85 Centralized Immutable Audit Trail Records...")
    audit_actions = [
        ("USER_LOGIN", "USER_AUTH", "SUCCESS"),
        ("CREDENTIAL_ISSUED", "CREDENTIAL", "SUCCESS"),
        ("VERIFICATION_PERFORMED", "VERIFICATION", "SUCCESS"),
        ("CREDENTIAL_REVOKED", "CREDENTIAL", "SUCCESS"),
        ("API_KEY_CREATED", "API_KEY", "SUCCESS"),
        ("FRAUD_CASE_TRIAGED", "FRAUD_CASE", "SUCCESS"),
        ("WEBHOOK_DISPATCHED", "WEBHOOK", "SUCCESS"),
        ("ORGANIZATION_SETTINGS_UPDATED", "ORGANIZATION", "SUCCESS")
    ]
    
    for i in range(85):
        act, res, outcome = audit_actions[i % len(audit_actions)]
        org = created_orgs[i % len(created_orgs)]
        user = created_users[i % len(created_users)]
        
        log_e = AuditLog(
            user_id=user.id,
            organization_id=org.id,
            action=act,
            resource=res,
            resource_id=f"RES-{1000 + i}",
            ip_address=f"192.168.1.{random.randint(10, 250)}",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
            result=outcome,
            metadata_json=json.dumps({"detail": f"Automated audit track event {i}", "tenant": org.institution_code}),
            timestamp=datetime.now(timezone.utc) - timedelta(hours=i * 3)
        )
        db.add(log_e)
        
    db.commit()
    db.close()
    
    print("==================================================================")
    print("[SUCCESS] SYNTHETIC DEMO DATA GENERATION COMPLETE!")
    print("   * 4 Multi-Tenant Organizations")
    print("   * 14 RBAC Users (Super Admin, Org Admins, Issuers, Verifiers, Auditors)")
    print("   * 525 Cryptographically Signed Credentials (Active, Revoked, Expired, Suspicious)")
    print("   * 125 Verification Requests & Evidence Dossiers")
    print("   * 12 Detailed Fraud Investigation Cases")
    print("   * 4 Enterprise API Keys (Test & Live)")
    print("   * Continuous Credential Monitoring Subscriptions & Live Alerts")
    print("   * 85 Centralized Immutable Audit Logs")
    print("==================================================================")

if __name__ == "__main__":
    generate_synthetic_demo_data()
