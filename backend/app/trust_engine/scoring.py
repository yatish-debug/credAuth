from typing import Dict, Any, Tuple

def calculate_credential_trust_score(
    issuer_verified: bool = True,
    issuer_has_valid_keys: bool = True,
    issuer_domain_verified: bool = True,
    hash_match: bool = True,
    signature_valid: bool = True,
    registry_match: bool = True,
    status_active: bool = True,
    holder_name_match: bool = True,
    holder_id_match: bool = True,
    qr_match: bool = True,
    ocr_clean: bool = True,
    metadata_consistent: bool = True,
    is_revoked: bool = False,
    is_expired: bool = False
) -> Tuple[float, str, Dict[str, Any], str]:
    """
    Computes the Modular Credential Trust Score (0-100 points).
    
    Dimensions:
    1. Issuer Authenticity       (Max 25 pts)
    2. Cryptographic Integrity   (Max 20 pts)
    3. Registry Match            (Max 20 pts)
    4. QR Verification           (Max 15 pts)
    5. Document Forensics        (Max 10 pts)
    6. Metadata Consistency      (Max 10 pts)
    -------------------------------------------
    TOTAL                        (Max 100 pts)
    
    Returns:
    (trust_score, trust_level, breakdown_dict, final_decision)
    """
    breakdown = {
        "issuer_authenticity": {
            "score": 0.0,
            "max": 25.0,
            "details": []
        },
        "cryptographic_integrity": {
            "score": 0.0,
            "max": 20.0,
            "details": []
        },
        "registry_match": {
            "score": 0.0,
            "max": 20.0,
            "details": []
        },
        "qr_verification": {
            "score": 0.0,
            "max": 15.0,
            "details": []
        },
        "document_forensics": {
            "score": 0.0,
            "max": 10.0,
            "details": []
        },
        "metadata_consistency": {
            "score": 0.0,
            "max": 10.0,
            "details": []
        }
    }
    
    # 1. Issuer Authenticity (25 pts)
    if issuer_verified:
        breakdown["issuer_authenticity"]["score"] += 15.0
        breakdown["issuer_authenticity"]["details"].append("Organization officially verified")
    else:
        breakdown["issuer_authenticity"]["details"].append("Organization verification unconfirmed")
        
    if issuer_has_valid_keys:
        breakdown["issuer_authenticity"]["score"] += 5.0
        breakdown["issuer_authenticity"]["details"].append("Active RSA-2048 signing keys")
        
    if issuer_domain_verified:
        breakdown["issuer_authenticity"]["score"] += 5.0
        breakdown["issuer_authenticity"]["details"].append("Institutional domain verified")

    # 2. Cryptographic Integrity (20 pts)
    if hash_match:
        breakdown["cryptographic_integrity"]["score"] += 10.0
        breakdown["cryptographic_integrity"]["details"].append("SHA-256 document hash exact match")
    else:
        breakdown["cryptographic_integrity"]["details"].append("SHA-256 hash mismatch")
        
    if signature_valid:
        breakdown["cryptographic_integrity"]["score"] += 10.0
        breakdown["cryptographic_integrity"]["details"].append("RSA-PSS digital signature valid")
    else:
        breakdown["cryptographic_integrity"]["details"].append("Digital signature invalid / missing")

    # 3. Registry Match (20 pts)
    if registry_match:
        breakdown["registry_match"]["score"] += 10.0
        breakdown["registry_match"]["details"].append("Found in official institutional registry")
    else:
        breakdown["registry_match"]["details"].append("Not found in registry")
        
    if status_active and not is_revoked and not is_expired:
        breakdown["registry_match"]["score"] += 5.0
        breakdown["registry_match"]["details"].append("Status is ACTIVE")
        
    if holder_name_match and holder_id_match:
        breakdown["registry_match"]["score"] += 5.0
        breakdown["registry_match"]["details"].append("Holder name and identifier matched")

    # 4. QR Verification (15 pts)
    if qr_match:
        breakdown["qr_verification"]["score"] += 15.0
        breakdown["qr_verification"]["details"].append("Cryptographic QR token validated")
    else:
        breakdown["qr_verification"]["details"].append("QR token mismatch / invalid")

    # 5. Document Forensics (10 pts)
    if ocr_clean:
        breakdown["document_forensics"]["score"] += 10.0
        breakdown["document_forensics"]["details"].append("AI OCR extracted attributes consistent with registry")
    else:
        breakdown["document_forensics"]["details"].append("Discrepancies detected in extracted OCR text")

    # 6. Metadata Consistency (10 pts)
    if metadata_consistent and not is_expired:
        breakdown["metadata_consistency"]["score"] += 10.0
        breakdown["metadata_consistency"]["details"].append("Timelines and metadata verified")
    else:
        if is_expired:
            breakdown["metadata_consistency"]["details"].append("Credential validity period expired")
        else:
            breakdown["metadata_consistency"]["score"] += 5.0
            breakdown["metadata_consistency"]["details"].append("Minor metadata discrepancies")

    # Total Score
    total_score = sum(cat["score"] for cat in breakdown.values())
    total_score = max(0.0, min(100.0, total_score))
    
    # Specific override for hard revocations or non-existent credentials
    if is_revoked:
        total_score = min(total_score, 20.0)
        final_decision = "REVOKED"
        trust_level = "CRITICAL_RISK"
    elif not registry_match:
        total_score = min(total_score, 10.0)
        final_decision = "NOT_FOUND"
        trust_level = "CRITICAL_RISK"
    elif is_expired:
        final_decision = "EXPIRED"
        trust_level = "MODERATE"
    elif not hash_match or not signature_valid or not ocr_clean:
        if total_score >= 60.0:
            total_score = min(total_score, 45.0)
        final_decision = "HIGH_RISK"
        trust_level = "LOW"
    elif total_score >= 85.0:
        final_decision = "VERIFIED"
        trust_level = "VERY_HIGH" if total_score >= 92.0 else "HIGH"
    elif total_score >= 65.0:
        final_decision = "REVIEW_REQUIRED"
        trust_level = "MODERATE"
    else:
        final_decision = "HIGH_RISK"
        trust_level = "LOW"

    return round(total_score, 1), trust_level, breakdown, final_decision


def calculate_issuer_trust_score(
    is_verified: bool,
    has_keys: bool,
    domain_present: bool,
    total_credentials: int,
    revocation_count: int,
    fraud_reports_count: int,
    verification_success_rate: float = 0.98
) -> Dict[str, Any]:
    """
    Computes an Issuer Trust Score (0-100) based on institutional authenticity,
    signing infrastructure, credential volume, revocation ratio, and fraud track record.
    """
    score = 40.0 # Base score for registered entity
    
    factors = []
    
    if is_verified:
        score += 25.0
        factors.append("Institutional identity officially verified")
    if has_keys:
        score += 15.0
        factors.append("Active RSA-2048 cryptographic signing keypair")
    if domain_present:
        score += 10.0
        factors.append("Verified domain infrastructure")
        
    # Volume credit (up to 5 pts)
    if total_credentials > 100:
        score += 5.0
        factors.append(f"High historical volume ({total_credentials:,} credentials)")
    elif total_credentials > 10:
        score += 3.0
        
    # Penalty for excessive revocations
    if total_credentials > 0:
        rev_rate = revocation_count / total_credentials
        if rev_rate > 0.15:
            score -= 15.0
            factors.append(f"Elevated revocation rate ({rev_rate:.1%})")
            
    # Penalty for fraud reports
    if fraud_reports_count > 0:
        penalty = min(fraud_reports_count * 5.0, 20.0)
        score -= penalty
        factors.append(f"{fraud_reports_count} recorded fraud investigation cases")
        
    score = max(10.0, min(99.9, score))
    
    return {
        "issuer_trust_score": round(score, 1),
        "rating": "A+" if score >= 90 else "A" if score >= 80 else "B" if score >= 65 else "C",
        "verified_status": "VERIFIED" if is_verified else "PENDING",
        "has_keys": has_keys,
        "total_issued": total_credentials,
        "revocation_rate": f"{(revocation_count / max(1, total_credentials)):.1%}",
        "verification_reliability": f"{verification_success_rate * 100:.1f}%",
        "factors": factors
    }
