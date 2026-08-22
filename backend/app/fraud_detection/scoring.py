from typing import Tuple, List

def calculate_risk_score(
    registry_match: bool,
    hash_match: bool,
    issuer_valid: bool,
    qr_match: bool,
    name_match: bool,
    is_expired: bool,
    is_revoked: bool,
    ocr_anomaly: bool,
    missing_fields: bool,
    signature_valid: bool = True
) -> Tuple[float, str, List[str], float]:
    """
    Calculates the Fraud Risk Score (0-100), Risk Level (LOW, MEDIUM, HIGH, CRITICAL),
    explainable list of indicators, and confidence rating.
    """
    score = 0.0
    indicators = []
    
    if not registry_match:
        score += 45.0
        indicators.append("REGISTRY_NOT_FOUND: Credential ID does not exist in issuing registry")
        
    if not hash_match:
        score += 35.0
        indicators.append("HASH_MISMATCH: SHA-256 document vector hash does not match original file")
        
    if not signature_valid:
        score += 35.0
        indicators.append("SIGNATURE_INVALID: RSA-PSS digital signature verification failed")
        
    if not issuer_valid:
        score += 25.0
        indicators.append("ISSUER_UNVERIFIED: Issuing organization is unverified or suspended")
        
    if not qr_match:
        score += 25.0
        indicators.append("QR_MISMATCH: QR token does not resolve to the canonical payload")
        
    if not name_match:
        score += 30.0
        indicators.append("NAME_ANOMALY: Recipient name altered or not detected in OCR scan")
        
    if is_revoked:
        score += 60.0
        indicators.append("OFFICIALLY_REVOKED: Issuing authority has officially revoked this credential")
        
    if ocr_anomaly:
        score += 20.0
        indicators.append("OCR_ANOMALY: Font or layout discrepancies detected in extracted attributes")
        
    if missing_fields:
        score += 15.0
        indicators.append("MISSING_CRITICAL_FIELDS: Essential metadata or marks fields missing")
        
    if is_expired:
        score += 10.0
        indicators.append("EXPIRED: Credential validity term has passed")

    # Cap score at 100
    score = min(score, 100.0)
    score = max(score, 0.0)
    
    # Determine risk level
    if score <= 30.0:
        risk_level = "LOW"
    elif score <= 60.0:
        risk_level = "MEDIUM"
    elif score <= 80.0:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"
        
    # Calculate confidence based on factors evaluated
    confidence = 0.96 if (hash_match is not None and signature_valid is not None) else 0.85
    
    return round(score, 1), risk_level, indicators, confidence
