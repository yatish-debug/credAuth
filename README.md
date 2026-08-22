# CredAuth — B2B Credential Trust & Fraud Intelligence Platform

[![Status](https://img.shields.io/badge/Status-Production%20Ready-emerald.svg)]()
[![Platform](https://img.shields.io/badge/Architecture-B2B%20Multi--Tenant%20SaaS-blue.svg)]()
[![Cryptography](https://img.shields.io/badge/Signatures-RSA--PSS%202048--bit-indigo.svg)]()
[![Integrity](https://img.shields.io/badge/Digest-SHA--256-cyan.svg)]()
[![Test Suite](https://img.shields.io/badge/Tests-12%2F12%20Passed%20(100%25)-brightgreen.svg)]()

> **Positioning**: CredAuth is an enterprise **Credential Trust, Verification, and Fraud Intelligence Layer** enabling universities, corporations, certification bodies, and background verification recruiters to issue, risk-score, monitor, and audit digital credentials with cryptographic proof and AI document forensics.

---

## 🏛️ Executive Summary & Core Value Proposition

Modern organizations face severe credential fraud, moonlighting, forged experience certificates, and manipulated grades. CredAuth provides a **zero-trust verification infrastructure**:

1. **Cryptographic Issuance**: RSA-PSS 2048-bit asymmetric digital signatures, SHA-256 integrity digests, and high-entropy tamper-evident QR tokens.
2. **Modular 0–100 Trust Scoring**: Mathematical model computing 6 weighted trust vectors (Issuer Authenticity 25%, Cryptographic Signature 20%, Authoritative Registry Match 20%, QR Validation 15%, Document Forensics 10%, Metadata Consistency 10%).
3. **Deep AI Document Forensics**: OCR vector extraction comparing physical scans against authoritative database records to detect grade, name, and date alterations.
4. **B2B Multi-Tenant Isolation**: Strict tenant data segregation with role-based access control (RBAC) across 5 enterprise roles.
5. **Continuous Credential Monitoring**: Real-time watches alerting subscribers to credential revocations, expiry, or status changes.
6. **Developer REST API & Webhooks**: Scoped API keys, custom rate-limiting, and HMAC-SHA256 signed event broadcasting for ATS/HRMS integration.

---

## 📐 Multi-Domain Support

CredAuth is engineered for four mission-critical credential verticals:

| Domain | Credential Types | Key Verifications |
| :--- | :--- | :--- |
| **Academic & Higher Ed** | Degrees, Diplomas, Marksheets, Transcripts | Student PRN / Roll No, CGPA, Division, Department, Registrar Signature |
| **Recruitment & HR** | Experience Letters, Relieving Deeds, Service Certs | Employee ID, Exact Tenure, Designation, Appraisal Rating, HR Key Stamp |
| **Technical Certifications** | Cloud, DevOps, Cyber, Developer Badges | Exam & License Code, Score / Percentile, Tech Stack, Testing Body Key |
| **Hackathons & Merit** | Awards, Coding Contests, Research Honors | Rank Position, Track Category, Jury Validation, Unforgeable Award Proof |

---

## 🔐 5-Tier RBAC Access Control

CredAuth provides 5 distinct personas with full tenant isolation:

1. **Platform Super Admin** (`admin@ssbt.demo` / `admin123`): Root governance, tenant onboarding, keypair management, user provisioning, database reset.
2. **Organization Admin** (`univadmin@demo-university.edu` / `univadmin123`): Tenant workspace, staff management, fraud triage, registry oversight.
3. **Credential Issuer** (`chen.issuer@ssbt-university.edu` / `issuer123`): Digital signer studio, instant RSA-PSS generation, QR embedding.
4. **Verification Officer / HR Recruiter** (`tcs.verifier@tcs.demo` / `verifier123`): Single ID, QR, PDF forensics, and batch CSV candidate screening.
5. **Compliance & Fraud Auditor** (`auditor@kpmg.demo` / `auditor123`): Regulatory compliance, immutable audit inspection, resolution oversight.

---

## 🛠️ Technology Stack

* **Backend**: FastAPI (Python 3.12+), SQLAlchemy ORM, Pydantic V2, PyCryptodome / Cryptography (RSA-PSS), ReportLab (PDF Generation), PyMuPDF / OpenCV / Tesseract (OCR Forensics).
* **Frontend**: React 18, TypeScript, Tailwind CSS, Lucide Icons, Vite, Axios, React Router.
* **Database**: SQLite (Zero-config embedded DB in `backend/data/credverify.db`).

---

## 🚀 Quick Start Guide

### 1. Launch Backend API
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. Launch Frontend UI
```powershell
cd frontend
npm run dev
```

### 3. Reset Database to Clean State (Optional)
```powershell
cd backend
.\.venv\Scripts\python.exe scripts/reset_clean_database.py
```

### 4. Run Automated Test Suite
```powershell
cd backend
.\.venv\Scripts\pytest -v tests/test_ssbt_platform.py
```

---

## 📄 License & Compliance

* Proprietary Enterprise Software.
* Developed for advanced credential trust verification and fraud intelligence.
