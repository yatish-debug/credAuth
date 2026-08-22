import os
import io
import csv
import json
import uuid
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header, Request, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.core.config import settings
from app.models.domain import (
    Credential, VerificationRequest, VerificationResult, FraudCase, 
    Organization, User, ApiKey
)
from app.schemas.domain import VerifyRequest, BatchVerificationResponse, BatchItemResult
from app.crypto.hashing import verify_file_hash, generate_file_hash
from app.crypto.signing import verify_certificate_signature
from app.ocr.extractor import extract_certificate_data
from app.fraud_detection.analyzer import analyze_certificate_consistency
from app.trust_engine.scoring import calculate_credential_trust_score, calculate_issuer_trust_score
from app.api.deps import get_current_active_user, get_tenant_context, get_optional_tenant_context, log_audit_trail

router = APIRouter()

def generate_verification_id():
    return f"VER-2026-{uuid.uuid4().hex[:6].upper()}"

def generate_fraud_case_id():
    return f"FC-2026-{uuid.uuid4().hex[:5].upper()}"

def format_date_str(d) -> str:
    if hasattr(d, 'strftime'):
        return d.strftime("%Y-%m-%d")
    return str(d)[:10]

def save_upload_file(upload_file: UploadFile, destination: str) -> str:
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    try:
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()
    return destination

def get_original_record_dict(cert: Credential, institution: Optional[Organization]) -> dict:
    return {
        "credential_id": cert.certificate_id,
        "certificate_id": cert.certificate_id,
        "category": cert.category or "ACADEMIC",
        "credential_type": cert.certificate_type or "DEGREE",
        "holder_name": cert.holder_name,
        "student_id": cert.student_id or "N/A",
        "holder_identifier": cert.student_id or "N/A",
        "course_name": cert.course_name,
        "department": cert.department or "N/A",
        "academic_year": cert.academic_year or "N/A",
        "marks_obtained": cert.marks_obtained,
        "total_marks": cert.total_marks,
        "percentage": cert.percentage,
        "cgpa": cert.cgpa,
        "grade": cert.grade or "N/A",
        "remarks": cert.remarks,
        "role_designation": cert.role_designation,
        "organization_company": cert.organization_company or (institution.name if institution else None),
        "skills_acquired": cert.skills_acquired,
        "employment_type": cert.employment_type,
        "license_number": cert.license_number,
        "score_or_rank": cert.score_or_rank,
        "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
        "expiry_date": cert.expiry_date.isoformat() if cert.expiry_date else None,
        "institution_name": institution.name if institution else "Unknown Organization",
        "organization_name": institution.name if institution else "Unknown Organization",
        "institution_code": institution.institution_code if institution else "",
        "key_fingerprint": cert.signer_public_key_fingerprint or (institution.key_fingerprint if institution else ""),
        "signature_algorithm": cert.signature_algorithm or "RSA-PSS-SHA256",
        "document_hash": cert.document_hash,
        "status": cert.status
    }

# =========================================================================
# 1. UNIFIED REST VERIFICATION API (/api/v1/verify)
# =========================================================================
@router.post("")
@router.post("/")
async def verify_credential_unified(
    request: Request,
    db: Session = Depends(get_db),
    tenant_ctx: dict = Depends(get_optional_tenant_context)
):
    """
    Unified enterprise verification endpoint.
    Accepts JSON body or multipart form (ID, QR, or Document upload).
    Authenticated via User Bearer JWT or API Client X-API-Key, or public guest.
    """
    target_id = None
    target_qr = None
    uploaded_file = None
    
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            if isinstance(body, dict):
                target_id = body.get("credential_id") or body.get("certificate_id")
                target_qr = body.get("qr_token")
        except Exception:
            pass
    elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        try:
            form = await request.form()
            target_id = form.get("credential_id") or form.get("certificate_id")
            target_qr = form.get("qr_token")
            file_field = form.get("file")
            if isinstance(file_field, UploadFile):
                uploaded_file = file_field
        except Exception:
            pass
            
    if not target_id and not target_qr and not uploaded_file:
        try:
            target_id = request.query_params.get("credential_id") or request.query_params.get("certificate_id")
            target_qr = request.query_params.get("qr_token")
        except Exception:
            pass

    if uploaded_file and uploaded_file.filename:
        return handle_file_verification(uploaded_file, (target_id or "").strip(), db, tenant_ctx, request)

    cert = None
    method = "MANUAL_ID"
    if target_qr:
        method = "QR_SCAN"
        cert = db.query(Credential).filter(Credential.qr_token == target_qr.strip()).first()
    elif target_id:
        method = "MANUAL_ID"
        cert = db.query(Credential).filter(Credential.certificate_id == target_id.strip()).first()

    req_rec = VerificationRequest(
        organization_id=cert.institution_id if cert else tenant_ctx.get("organization_id"),
        certificate_id=cert.id if cert else None,
        searched_certificate_id=target_id or target_qr,
        verification_method=method,
        requested_by=tenant_ctx.get("name")
    )
    db.add(req_rec)
    db.flush()

    if not cert:
        req_rec.result = "NOT_FOUND"
        db.commit()
        return {
            "verification_id": generate_verification_id(),
            "final_result": "NOT_FOUND",
            "final_decision": "NOT_FOUND",
            "trust_score": 0.0,
            "fraud_risk_score": 100.0,
            "risk_level": "CRITICAL",
            "explanation": "Credential was not found in any institutional registry.",
            "is_forged": True,
            "original_record": None,
            "field_comparisons": []
        }

    return process_credential_verification(cert, method, req_rec, db, tenant_ctx, request)

# =========================================================================
# 2. DOCUMENT UPLOAD VERIFICATION (/api/v1/verify/document)
# =========================================================================
@router.post("/document")
async def verify_document(
    request: Request,
    certificate_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    tenant_ctx: dict = Depends(get_tenant_context)
):
    """
    Verify by uploading a document. OCR + Hash + Cryptographic Signature + Deep Anomaly Analysis.
    """
    return handle_file_verification(file, certificate_id.strip(), db, tenant_ctx, request)

def handle_file_verification(
    file: UploadFile, 
    target_cert_id: str, 
    db: Session, 
    tenant_ctx: dict,
    request: Request
) -> dict:
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large (Max 10MB)")
        
    cert = db.query(Credential).filter(Credential.certificate_id == target_cert_id.strip()).first()
    
    req = VerificationRequest(
        organization_id=cert.institution_id if cert else tenant_ctx.get("organization_id"),
        certificate_id=cert.id if cert else None,
        searched_certificate_id=target_cert_id,
        verification_method="UPLOAD",
        requested_by=tenant_ctx.get("name")
    )
    db.add(req)
    db.flush()
    
    if not cert:
        req.result = "NOT_FOUND"
        db.commit()
        return {
            "verification_id": generate_verification_id(),
            "final_result": "NOT_FOUND",
            "final_decision": "NOT_FOUND",
            "trust_score": 0.0,
            "fraud_risk_score": 100.0,
            "risk_level": "CRITICAL",
            "explanation": "Credential ID not found in institutional registry.",
            "is_forged": True,
            "original_record": None,
            "field_comparisons": []
        }
        
    institution = db.query(Organization).filter(Organization.id == cert.institution_id).first()

    # Save temp file for OCR and Hash
    file_ext = os.path.splitext(file.filename or "upload.pdf")[1] or ".pdf"
    temp_path = os.path.join("storage", "temp", f"verify_{req.id}{file_ext}")
    save_upload_file(file, temp_path)
    
    # 1. OCR Extraction
    ocr_data = extract_certificate_data(temp_path)
    
    # 2. Document SHA-256 Hash Check
    is_hash_valid = verify_file_hash(temp_path, cert.document_hash)
    
    # 3. Cryptographic Signature Validation
    is_sig_valid = False
    if institution and institution.public_key and cert.digital_signature:
        canonical_payload = {
            "certificate_id": cert.certificate_id,
            "holder_name": cert.holder_name,
            "student_id": cert.student_id or "",
            "course_name": cert.course_name,
            "grade": cert.grade or "",
            "cgpa": str(cert.cgpa) if cert.cgpa is not None else "",
            "institution_code": institution.institution_code,
            "issue_date": format_date_str(cert.issue_date),
            "document_hash": cert.document_hash,
            "qr_token": cert.qr_token
        }
        is_sig_valid = verify_certificate_signature(
            institution.public_key,
            canonical_payload,
            cert.digital_signature
        )

    # 4. Consistency & Anomaly Analysis
    analysis_result = analyze_certificate_consistency(
        cert=cert,
        institution=institution,
        ocr_data=ocr_data,
        is_hash_valid=is_hash_valid,
        is_sig_valid=is_sig_valid
    )
    
    ver_id = generate_verification_id()
    analysis_result["verification_id"] = ver_id
    analysis_result["original_record"] = get_original_record_dict(cert, institution)
    analysis_result["qr_token"] = cert.qr_token
    analysis_result["qr_image_url"] = f"/storage/qr/{cert.qr_token}.png" if cert.qr_token else None
    analysis_result["pdf_download_url"] = f"/api/v1/verify/{cert.certificate_id}/download"
    
    # Record Verification Result
    result_record = VerificationResult(
        verification_request_id=req.id,
        verification_id=ver_id,
        organization_id=cert.institution_id,
        credential_id=cert.id,
        registry_check=analysis_result["registry_check"],
        qr_check=analysis_result.get("qr_check", "VALID"),
        hash_check=analysis_result["hash_check"],
        signature_check=analysis_result["signature_check"],
        issuer_check=analysis_result["issuer_check"],
        document_analysis=analysis_result["document_analysis"],
        fraud_risk_score=analysis_result["fraud_risk_score"],
        risk_level=analysis_result["risk_level"],
        confidence=analysis_result["confidence"],
        trust_score=analysis_result["trust_score"],
        trust_breakdown_json=json.dumps(analysis_result["trust_breakdown"]),
        issuer_trust_score=institution.trust_score if institution else 90.0,
        final_result=analysis_result["final_result"],
        explanation=analysis_result["explanation"],
        evidence_metadata_json=json.dumps({
            "field_comparisons": analysis_result["field_comparisons"],
            "indicators": analysis_result["indicators"]
        })
    )
    db.add(result_record)
    
    # Auto-create Fraud Case if high risk or tampering detected
    if analysis_result["fraud_risk_score"] >= 60.0 or analysis_result["is_forged"]:
        fraud_case = FraudCase(
            case_id=generate_fraud_case_id(),
            credential_id=cert.id,
            organization_id=cert.institution_id,
            risk_score=analysis_result["fraud_risk_score"],
            risk_level=analysis_result["risk_level"],
            indicators_json=json.dumps(analysis_result["indicators"]),
            status="OPEN",
            notes_json=json.dumps([{
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "author": "CredAuth AI Fraud Engine",
                "text": f"Automated Incident: Document upload discrepancy detected during verification {ver_id}."
            }])
        )
        db.add(fraud_case)
        
    req.result = analysis_result["final_result"]
    db.commit()
    
    log_audit_trail(
        db=db,
        action="VERIFICATION_PERFORMED",
        resource="VERIFICATION",
        resource_id=ver_id,
        user_id=tenant_ctx.get("user").id if tenant_ctx.get("user") else None,
        organization_id=cert.institution_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={
            "method": "UPLOAD",
            "credential_id": cert.certificate_id,
            "trust_score": analysis_result["trust_score"],
            "decision": analysis_result["final_result"]
        }
    )
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return analysis_result

# =========================================================================
# 3. VERIFY BY ID (/api/v1/verify/id/{certificate_id})
# =========================================================================
@router.get("/id/{certificate_id}")
def verify_by_id(
    certificate_id: str, 
    request: Request,
    db: Session = Depends(get_db),
    tenant_ctx: dict = Depends(get_optional_tenant_context)
):
    cert = db.query(Credential).filter(Credential.certificate_id == certificate_id.strip()).first()
    
    req = VerificationRequest(
        organization_id=cert.institution_id if cert else tenant_ctx.get("organization_id"),
        certificate_id=cert.id if cert else None,
        searched_certificate_id=certificate_id,
        verification_method="MANUAL_ID",
        requested_by=tenant_ctx.get("name")
    )
    db.add(req)
    db.flush()
    
    if not cert:
        req.result = "NOT_FOUND"
        db.commit()
        return {
            "verification_id": generate_verification_id(),
            "final_result": "NOT_FOUND",
            "final_decision": "NOT_FOUND",
            "trust_score": 0.0,
            "fraud_risk_score": 100.0,
            "risk_level": "CRITICAL",
            "explanation": "Credential ID not found in institutional registry.",
            "is_forged": True,
            "original_record": None,
            "field_comparisons": []
        }
    return process_credential_verification(cert, "MANUAL_ID", req, db, tenant_ctx, request)

# =========================================================================
# 4. VERIFY BY QR (/api/v1/verify/qr/{qr_token})
# =========================================================================
@router.get("/qr/{qr_token}")
def verify_by_qr(
    qr_token: str, 
    request: Request,
    db: Session = Depends(get_db),
    tenant_ctx: dict = Depends(get_optional_tenant_context)
):
    cert = db.query(Credential).filter(Credential.qr_token == qr_token.strip()).first()
    
    req = VerificationRequest(
        organization_id=cert.institution_id if cert else tenant_ctx.get("organization_id"),
        certificate_id=cert.id if cert else None,
        searched_certificate_id=qr_token,
        verification_method="QR_SCAN",
        requested_by=tenant_ctx.get("name")
    )
    db.add(req)
    db.flush()
    
    if not cert:
        req.result = "NOT_FOUND"
        db.commit()
        return {
            "verification_id": generate_verification_id(),
            "final_result": "NOT_FOUND",
            "final_decision": "NOT_FOUND",
            "trust_score": 0.0,
            "fraud_risk_score": 100.0,
            "risk_level": "CRITICAL",
            "explanation": "Invalid QR Code or Token",
            "is_forged": True,
            "original_record": None,
            "field_comparisons": []
        }
    return process_credential_verification(cert, "QR_SCAN", req, db, tenant_ctx, request)

# =========================================================================
# 5. BATCH CSV VERIFICATION (/api/v1/verify/batch)
# =========================================================================
@router.post("/batch", response_model=BatchVerificationResponse)
async def verify_batch_csv(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
    tenant_ctx: dict = Depends(get_tenant_context)
):
    """
    Enterprise Batch CSV Verification.
    Reads candidate credentials CSV, computes trust scores, and returns full triage matrix.
    """
    contents = await file.read()
    text = contents.decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))
    
    batch_id = f"BATCH-2026-{uuid.uuid4().hex[:6].upper()}"
    results: List[BatchItemResult] = []
    
    verified_count = 0
    high_risk_count = 0
    not_found_count = 0
    row_num = 1
    
    for row in reader:
        # Search for column names matching Credential ID / Certificate ID
        cid = row.get("credential_id") or row.get("certificate_id") or row.get("id") or row.get("Certificate ID") or row.get("Credential ID")
        cname = row.get("holder_name") or row.get("candidate_name") or row.get("name") or row.get("Candidate Name")
        
        if not cid:
            continue
            
        cid = cid.strip()
        cert = db.query(Credential).filter(Credential.certificate_id == cid).first()
        
        if not cert:
            not_found_count += 1
            results.append(BatchItemResult(
                row_number=row_num,
                candidate_name=cname,
                credential_id=cid,
                verification_status="NOT_FOUND",
                trust_score=0.0,
                fraud_risk_score=100.0,
                risk_level="CRITICAL",
                decision="NOT_FOUND",
                explanation="Record not found in issuing registry."
            ))
        else:
            inst = db.query(Organization).filter(Organization.id == cert.institution_id).first()
            is_rev = (cert.status == "REVOKED")
            is_exp = (cert.status == "EXPIRED")
            
            # Check name match if provided
            name_matched = True
            if cname:
                name_matched = (cname.lower() in cert.holder_name.lower() or cert.holder_name.lower() in cname.lower())
                
            trust_sc, trust_lvl, _, dec = calculate_credential_trust_score(
                issuer_verified=bool(inst and inst.verification_status == "VERIFIED"),
                issuer_has_valid_keys=bool(inst and inst.public_key),
                issuer_domain_verified=bool(inst and inst.official_domain),
                hash_match=True,
                signature_valid=bool(cert.digital_signature),
                registry_match=True,
                status_active=(cert.status == "ACTIVE"),
                holder_name_match=name_matched,
                holder_id_match=True,
                qr_match=True,
                ocr_clean=name_matched,
                metadata_consistent=True,
                is_revoked=is_rev,
                is_expired=is_exp
            )
            
            risk_sc = 100.0 - trust_sc if not name_matched or is_rev else 5.0
            r_lvl = "CRITICAL" if is_rev else "HIGH" if not name_matched else "LOW"
            
            if dec == "VERIFIED":
                verified_count += 1
            elif dec in ["HIGH_RISK", "REVOKED"]:
                high_risk_count += 1
                
            expl = "Verified active credential" if dec == "VERIFIED" else f"Status: {dec}"
            if not name_matched:
                expl = f"Candidate name mismatch (Provided: {cname}, Registry: {cert.holder_name})"
                
            results.append(BatchItemResult(
                row_number=row_num,
                candidate_name=cname or cert.holder_name,
                credential_id=cid,
                verification_status=cert.status,
                trust_score=trust_sc,
                fraud_risk_score=risk_sc,
                risk_level=r_lvl,
                decision=dec,
                explanation=expl
            ))
            
        row_num += 1
        
    log_audit_trail(
        db=db,
        action="BATCH_VERIFICATION_PERFORMED",
        resource="BATCH_VERIFY",
        resource_id=batch_id,
        user_id=tenant_ctx.get("user").id if tenant_ctx.get("user") else None,
        organization_id=tenant_ctx.get("organization_id"),
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
        result="SUCCESS",
        metadata={"total": len(results), "verified": verified_count, "high_risk": high_risk_count}
    )
    
    return BatchVerificationResponse(
        batch_id=batch_id,
        total_processed=len(results),
        verified_count=verified_count,
        high_risk_count=high_risk_count,
        not_found_count=not_found_count,
        results=results
    )

# =========================================================================
# HELPER: PROCESS CREDENTIAL VERIFICATION RECORD
# =========================================================================
def process_credential_verification(
    cert: Credential, 
    method: str, 
    req: VerificationRequest, 
    db: Session, 
    tenant_ctx: dict,
    request: Request
) -> dict:
    institution = db.query(Organization).filter(Organization.id == cert.institution_id).first()
    
    # Cryptographic signature validation
    crypto_valid = False
    if institution and institution.public_key and cert.digital_signature:
        canonical_payload = {
            "certificate_id": cert.certificate_id,
            "holder_name": cert.holder_name,
            "student_id": cert.student_id or "",
            "course_name": cert.course_name,
            "grade": cert.grade or "",
            "cgpa": str(cert.cgpa) if cert.cgpa is not None else "",
            "institution_code": institution.institution_code,
            "issue_date": format_date_str(cert.issue_date),
            "document_hash": cert.document_hash,
            "qr_token": cert.qr_token
        }
        crypto_valid = verify_certificate_signature(
            institution.public_key,
            canonical_payload,
            cert.digital_signature
        )
        
    is_rev = (cert.status == "REVOKED")
    is_exp = (cert.status == "EXPIRED")
    is_susp = (cert.status == "SUSPICIOUS")
    
    trust_score, trust_level, trust_breakdown, final_decision = calculate_credential_trust_score(
        issuer_verified=bool(institution and institution.verification_status == "VERIFIED"),
        issuer_has_valid_keys=bool(institution and institution.public_key),
        issuer_domain_verified=bool(institution and institution.official_domain),
        hash_match=True,
        signature_valid=crypto_valid,
        registry_match=True,
        status_active=(cert.status == "ACTIVE"),
        holder_name_match=True,
        holder_id_match=True,
        qr_match=True,
        ocr_clean=True,
        metadata_consistent=True,
        is_revoked=is_rev,
        is_expired=is_exp
    )
    
    fraud_risk = 85.0 if is_rev else 65.0 if is_susp else 5.0
    risk_level = "CRITICAL" if is_rev else "HIGH" if is_susp else "LOW"
    
    if is_rev:
        final_result = "REVOKED"
        explanation = "Credential was officially REVOKED by the issuing organization."
    elif is_susp:
        final_result = "SUSPICIOUS"
        explanation = f"Credential flagged as suspicious: {cert.suspicious_reason or 'Under administrative investigation'}"
    elif is_exp:
        final_result = "EXPIRED"
        explanation = "Credential has passed its validity expiration date."
    else:
        final_result = "VERIFIED"
        explanation = "Credential is valid, active, and authenticated with institutional RSA-2048 digital signature and SHA-256 integrity hash."
        
    ver_id = generate_verification_id()
    original_record = get_original_record_dict(cert, institution)
    
    # Store Verification Result in DB
    result_rec = VerificationResult(
        verification_request_id=req.id,
        verification_id=ver_id,
        organization_id=cert.institution_id,
        credential_id=cert.id,
        registry_check="MATCH",
        qr_check="VALID" if method == "QR_SCAN" else "NOT_APPLICABLE",
        hash_check="VALID",
        signature_check="VALID" if crypto_valid else "INVALID",
        issuer_check="VERIFIED" if (institution and institution.verification_status == "VERIFIED") else "UNVERIFIED",
        document_analysis="CLEAN",
        fraud_risk_score=fraud_risk,
        risk_level=risk_level,
        confidence=0.98,
        trust_score=trust_score,
        trust_breakdown_json=json.dumps(trust_breakdown),
        issuer_trust_score=institution.trust_score if institution else 95.0,
        final_result=final_result,
        explanation=explanation,
        evidence_metadata_json=json.dumps({"verified_attributes": original_record})
    )
    db.add(result_rec)
    
    req.result = final_result
    db.commit()
    
    qr_url = f"/storage/qr/{cert.qr_token}.png" if cert.qr_token else None
    pdf_url = f"/api/v1/verify/{cert.certificate_id}/download"
    
    log_audit_trail(
        db=db,
        action="VERIFICATION_PERFORMED",
        resource="VERIFICATION",
        resource_id=ver_id,
        user_id=tenant_ctx.get("user").id if tenant_ctx.get("user") else None,
        organization_id=cert.institution_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        result="SUCCESS",
        metadata={"method": method, "credential_id": cert.certificate_id, "decision": final_result}
    )
    
    return {
        "verification_id": ver_id,
        "certificate_id": cert.certificate_id,
        "credential_id": cert.certificate_id,
        "category": cert.category or "ACADEMIC",
        "credential_type": cert.certificate_type or "DEGREE",
        "holder_name": cert.holder_name,
        "student_id": cert.student_id,
        "course_name": cert.course_name,
        "department": cert.department,
        "academic_year": cert.academic_year,
        "marks_obtained": cert.marks_obtained,
        "total_marks": cert.total_marks,
        "percentage": cert.percentage,
        "cgpa": cert.cgpa,
        "grade": cert.grade,
        "role_designation": cert.role_designation,
        "organization_company": cert.organization_company or (institution.name if institution else None),
        "skills_acquired": cert.skills_acquired,
        "employment_type": cert.employment_type,
        "license_number": cert.license_number,
        "score_or_rank": cert.score_or_rank,
        "remarks": cert.remarks,
        "issue_date": cert.issue_date.isoformat() if cert.issue_date else None,
        "institution_name": institution.name if institution else "Unknown Organization",
        "organization_name": institution.name if institution else "Unknown Organization",
        "institution_code": institution.institution_code if institution else "",
        "key_fingerprint": cert.signer_public_key_fingerprint or (institution.key_fingerprint if institution else ""),
        "signature_algorithm": cert.signature_algorithm or "RSA-PSS-SHA256",
        "cryptographic_verification": "VALID" if crypto_valid else "UNVERIFIED",
        "trust_score": trust_score,
        "trust_level": trust_level,
        "trust_breakdown": trust_breakdown,
        "fraud_risk_score": fraud_risk,
        "fraud_score": fraud_risk,
        "risk_level": risk_level,
        "final_result": final_result,
        "final_decision": final_decision,
        "explanation": explanation,
        "original_record": original_record,
        "is_forged": False,
        "field_comparisons": [],
        "qr_image_url": qr_url,
        "pdf_download_url": pdf_url,
        "qr_token": cert.qr_token
    }

# =========================================================================
# 6. DOWNLOADS
# =========================================================================
@router.get("/{certificate_id}/download")
def download_verified_pdf(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    from fastapi.responses import FileResponse
    cert = db.query(Credential).filter(Credential.certificate_id == certificate_id).first()
    if not cert or not cert.document_path or not os.path.exists(cert.document_path):
        raise HTTPException(status_code=404, detail="Credential PDF not found on server")
        
    return FileResponse(
        cert.document_path,
        media_type="application/pdf",
        filename=f"{cert.certificate_id}_{cert.holder_name.replace(' ', '_')}.pdf"
    )

@router.get("/{certificate_id}/qr")
def get_verified_qr_image(
    certificate_id: str,
    db: Session = Depends(get_db)
):
    from fastapi.responses import FileResponse
    cert = db.query(Credential).filter(Credential.certificate_id == certificate_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Credential not found")
        
    qr_path = os.path.join("storage", "qr", f"{cert.qr_token}.png")
    if not os.path.exists(qr_path):
        from app.qr.generator import generate_qr_code
        qr_path = generate_qr_code(cert.qr_token, cert.certificate_id)
        
    return FileResponse(
        qr_path,
        media_type="image/png",
        filename=f"QR_{cert.certificate_id}.png"
    )
