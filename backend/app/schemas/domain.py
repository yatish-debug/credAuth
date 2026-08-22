from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any, Dict
from datetime import datetime

# =========================================================================
# 1. FEATURES & SECURITY CONFIG
# =========================================================================
class FeaturesConfig(BaseModel):
    suspicious_threshold: float = 0.5 # 0.1 to 0.9 sensitivity
    allow_revocation: bool = True
    allow_reinstate: bool = True
    require_revocation_reason: bool = True
    qr_verification_enabled: bool = True
    ocr_document_check_enabled: bool = True
    digital_signatures_enabled: bool = True
    signature_algorithm: str = "RSA-PSS-SHA256"

# =========================================================================
# 2. USER SCHEMAS (RBAC)
# =========================================================================
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "VERIFICATION_OFFICER" # SUPER_ADMIN, ORGANIZATION_OWNER, ORGANIZATION_ADMIN, CREDENTIAL_ISSUER, VERIFICATION_OFFICER, AUDITOR, API_CLIENT
    organization: Optional[str] = None
    institution_id: Optional[int] = None
    permissions: Optional[List[str]] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    organization: Optional[str] = None
    institution_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    permissions: Optional[List[str]] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Backward-compat schemas for verifier admin endpoints
class VerifierAdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    organization: Optional[str] = "Independent Auditor"
    is_active: bool = True

class VerifierAdminUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    organization: Optional[str] = None
    is_active: Optional[bool] = None

# =========================================================================
# 3. ORGANIZATION / INSTITUTION SCHEMAS
# =========================================================================
class OrganizationBase(BaseModel):
    name: str
    institution_code: str
    organization_type: Optional[str] = "UNIVERSITY" # UNIVERSITY, COLLEGE, TRAINING_INSTITUTE, CORPORATION, EMPLOYER, CERTIFICATION_BODY, GOVERNMENT_ORGANIZATION, OTHER
    registration_number: Optional[str] = None
    official_domain: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    verification_status: Optional[str] = "VERIFIED" # PENDING, VERIFIED, SUSPENDED, REJECTED
    status: Optional[str] = "ACTIVE" # ACTIVE, SUSPENDED

class OrganizationCreate(OrganizationBase):
    admin_name: Optional[str] = None
    admin_email: Optional[EmailStr] = None
    admin_password: Optional[str] = None
    features: Optional[FeaturesConfig] = None

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    organization_type: Optional[str] = None
    registration_number: Optional[str] = None
    official_domain: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    verification_status: Optional[str] = None
    status: Optional[str] = None
    admin_name: Optional[str] = None
    admin_email: Optional[EmailStr] = None
    admin_password: Optional[str] = None
    features: Optional[FeaturesConfig] = None

class OrganizationResponse(OrganizationBase):
    id: int
    trust_score: Optional[float] = 95.0
    key_algorithm: Optional[str] = "RSA-2048"
    key_fingerprint: Optional[str] = None
    public_key: Optional[str] = None
    features_config: Optional[str] = None
    admin_email: Optional[str] = None
    total_credentials: Optional[int] = 0
    total_certificates: Optional[int] = 0 # Backward compat
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Backward compat aliases
InstitutionBase = OrganizationBase
InstitutionCreate = OrganizationCreate
InstitutionUpdate = OrganizationUpdate
InstitutionResponse = OrganizationResponse

# =========================================================================
# 4. CREDENTIAL / CERTIFICATE SCHEMAS
# =========================================================================
class CredentialBase(BaseModel):
    certificate_type: Optional[str] = "DEGREE" # DEGREE, DIPLOMA, CERTIFICATE, TRAINING_CERTIFICATE, INTERNSHIP_CERTIFICATE, EMPLOYMENT_CREDENTIAL, EXPERIENCE_LETTER, PROFESSIONAL_CERTIFICATION, LICENSE, ACHIEVEMENT, OTHER
    category: Optional[str] = "ACADEMIC" # ACADEMIC, RECRUITMENT, TECHNICAL_COURSE, ACHIEVEMENT
    holder_name: str
    student_id: Optional[str] = None # Holder Identifier (PRN / Roll / Employee ID / Candidate ID)
    course_name: str
    department: Optional[str] = None
    academic_year: Optional[str] = None
    marks_obtained: Optional[float] = None
    total_marks: Optional[float] = None
    percentage: Optional[float] = None
    cgpa: Optional[float] = None
    grade: Optional[str] = None
    remarks: Optional[str] = None
    
    # Recruitment & Technical fields
    role_designation: Optional[str] = None
    organization_company: Optional[str] = None
    skills_acquired: Optional[str] = None
    employment_type: Optional[str] = None
    license_number: Optional[str] = None
    score_or_rank: Optional[str] = None
    
    issue_date: datetime
    expiry_date: Optional[datetime] = None

class CredentialCreate(CredentialBase):
    organization_id: Optional[int] = None
    institution_id: Optional[int] = None
    extra_metadata: Optional[Dict[str, Any]] = None

class CredentialUpdate(BaseModel):
    certificate_type: Optional[str] = None
    category: Optional[str] = None
    holder_name: Optional[str] = None
    student_id: Optional[str] = None
    course_name: Optional[str] = None
    department: Optional[str] = None
    academic_year: Optional[str] = None
    marks_obtained: Optional[float] = None
    total_marks: Optional[float] = None
    percentage: Optional[float] = None
    cgpa: Optional[float] = None
    grade: Optional[str] = None
    remarks: Optional[str] = None
    role_designation: Optional[str] = None
    organization_company: Optional[str] = None
    skills_acquired: Optional[str] = None
    employment_type: Optional[str] = None
    license_number: Optional[str] = None
    score_or_rank: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    status: Optional[str] = None
    extra_metadata: Optional[Dict[str, Any]] = None

class CredentialResponse(CredentialBase):
    id: int
    certificate_id: str # Credential ID (e.g. CV-2026-XXXX)
    institution_id: int # Organization ID
    issuer_id: int
    document_path: Optional[str] = None
    document_hash: Optional[str] = None
    qr_token: str
    status: str
    suspicious_reason: Optional[str] = None
    digital_signature: Optional[str] = None
    signature_algorithm: Optional[str] = None
    signer_public_key_fingerprint: Optional[str] = None
    metadata_json: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Backward compat aliases
CertificateBase = CredentialBase
CertificateCreate = CredentialCreate
CertificateUpdate = CredentialUpdate
CertificateResponse = CredentialResponse

# =========================================================================
# 5. VERIFICATION & EVIDENCE SCHEMAS
# =========================================================================
class VerifyRequest(BaseModel):
    credential_id: Optional[str] = None
    qr_token: Optional[str] = None
    holder_name: Optional[str] = None
    expected_hash: Optional[str] = None

class EvidenceResponse(BaseModel):
    verification_id: str
    credential_id: str
    organization_name: str
    organization_code: str
    verification_method: str
    timestamp: datetime
    registry_check: str
    qr_check: Optional[str]
    hash_check: Optional[str]
    signature_check: Optional[str]
    issuer_check: str
    document_analysis: Optional[str]
    fraud_risk_score: float
    risk_level: str
    confidence: float
    trust_score: float
    trust_breakdown: Dict[str, Any]
    issuer_trust_score: float
    final_decision: str
    explanation: str
    evidence_metadata: Optional[Dict[str, Any]] = None
    verified_record: Optional[Dict[str, Any]] = None

# Batch verification item
class BatchItemResult(BaseModel):
    row_number: int
    candidate_name: Optional[str] = None
    credential_id: str
    verification_status: str
    trust_score: float
    fraud_risk_score: float
    risk_level: str
    decision: str
    explanation: str

class BatchVerificationResponse(BaseModel):
    batch_id: str
    total_processed: int
    verified_count: int
    high_risk_count: int
    not_found_count: int
    results: List[BatchItemResult]

# =========================================================================
# 6. FRAUD INVESTIGATION SCHEMAS
# =========================================================================
class FraudCaseCreate(BaseModel):
    credential_id: Optional[int] = None
    risk_score: float
    risk_level: str
    indicators: List[str]
    notes: Optional[str] = None

class FraudCaseUpdate(BaseModel):
    status: Optional[str] = None # OPEN, UNDER_REVIEW, CONFIRMED_FRAUD, FALSE_POSITIVE, RESOLVED
    assigned_to: Optional[int] = None
    notes: Optional[str] = None

class FraudCaseResponse(BaseModel):
    id: int
    case_id: str
    credential_id: Optional[int] = None
    credential_code: Optional[str] = None
    holder_name: Optional[str] = None
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None
    risk_score: float
    risk_level: str
    indicators: List[str]
    assigned_to: Optional[int] = None
    assigned_to_name: Optional[str] = None
    status: str
    notes_history: List[Dict[str, Any]] = []
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# =========================================================================
# 7. API KEY SCHEMAS
# =========================================================================
class ApiKeyCreate(BaseModel):
    name: str
    environment: str = "TEST" # TEST, PRODUCTION
    permissions: Optional[List[str]] = ["credential:read", "credential:verify", "verification:create"]
    rate_limit_per_minute: Optional[int] = 120

class ApiKeySecretResponse(BaseModel):
    id: int
    key_id: str
    name: str
    environment: str
    raw_api_key: str # Secret shown ONCE upon creation
    prefix: str
    permissions: List[str]
    rate_limit_per_minute: int
    created_at: datetime

class ApiKeyResponse(BaseModel):
    id: int
    key_id: str
    name: str
    environment: str
    prefix: str
    permissions: List[str]
    rate_limit_per_minute: int
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# =========================================================================
# 8. WEBHOOK SCHEMAS
# =========================================================================
class WebhookCreate(BaseModel):
    endpoint_url: str
    events: List[str] # credential.issued, credential.verified, credential.revoked, credential.expired, verification.completed, fraud.detected, risk.threshold_exceeded

class WebhookResponse(BaseModel):
    id: int
    webhook_id: str
    endpoint_url: str
    events: List[str]
    status: str
    secret_preview: str # Masked secret
    created_at: datetime

    class Config:
        from_attributes = True

class WebhookDeliveryResponse(BaseModel):
    id: int
    webhook_id: int
    event_type: str
    status_code: Optional[int]
    response_body: Optional[str]
    success: bool
    timestamp: datetime

    class Config:
        from_attributes = True

# =========================================================================
# 9. MONITORING SCHEMAS
# =========================================================================
class MonitoringSubscriptionCreate(BaseModel):
    credential_id: int
    subscriber_email: Optional[str] = None
    webhook_url: Optional[str] = None
    alert_on: Optional[str] = "ALL" # ALL, REVOCATION, EXPIRATION, SUSPICIOUS

class MonitoringSubscriptionResponse(BaseModel):
    id: int
    credential_id: int
    credential_code: Optional[str] = None
    holder_name: Optional[str] = None
    subscriber_email: Optional[str] = None
    webhook_url: Optional[str] = None
    last_status: str
    alert_on: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class MonitoringAlertResponse(BaseModel):
    id: int
    subscription_id: Optional[int] = None
    credential_id: int
    credential_code: Optional[str] = None
    previous_status: str
    new_status: str
    alert_type: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

# =========================================================================
# 10. AUDIT LOG SCHEMAS
# =========================================================================
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    result: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True
