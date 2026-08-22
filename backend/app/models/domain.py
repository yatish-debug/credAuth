from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Organization(Base):
    """
    B2B Multi-Tenant Organization (e.g. University, College, Employer, Certification Body).
    Uses 'institutions' table name for backward-compatibility with existing records.
    """
    __tablename__ = "institutions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    institution_code = Column(String, unique=True, index=True) # Organization code (e.g. SSBT_UNIV_01)
    organization_type = Column(String, default="UNIVERSITY") # UNIVERSITY, COLLEGE, TRAINING_INSTITUTE, CORPORATION, EMPLOYER, CERTIFICATION_BODY, GOVERNMENT_ORGANIZATION, OTHER
    registration_number = Column(String, nullable=True)
    official_domain = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    logo_url = Column(String, nullable=True)
    verification_status = Column(String, default="VERIFIED") # PENDING, VERIFIED, SUSPENDED, REJECTED
    status = Column(String, default="ACTIVE") # ACTIVE, SUSPENDED
    trust_score = Column(Float, default=94.5) # Platform-derived Issuer Trust Score (0-100)
    
    # Cryptographic keys (RSA-2048 keypair for credential signing)
    public_key = Column(Text, nullable=True)
    private_key = Column(Text, nullable=True)
    key_algorithm = Column(String, default="RSA-2048")
    key_fingerprint = Column(String, nullable=True)
    
    # Feature configurations (JSON formatted string)
    features_config = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    users = relationship("User", back_populates="organization_rel", cascade="all, delete-orphan", foreign_keys="[User.institution_id]")
    credentials = relationship("Credential", back_populates="organization_rel", cascade="all, delete-orphan", foreign_keys="[Credential.institution_id]")
    api_keys = relationship("ApiKey", back_populates="organization", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="organization", cascade="all, delete-orphan")
    fraud_cases = relationship("FraudCase", back_populates="organization", cascade="all, delete-orphan")
    monitoring_subscriptions = relationship("MonitoringSubscription", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")

    @property
    def certificates(self):
        return self.credentials

    @property
    def organization_code(self):
        return self.institution_code

    @organization_code.setter
    def organization_code(self, value):
        self.institution_code = value

# Backward compatibility alias
Institution = Organization


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    # Role: SUPER_ADMIN, ORGANIZATION_OWNER, ORGANIZATION_ADMIN, CREDENTIAL_ISSUER, VERIFICATION_OFFICER, AUDITOR, API_CLIENT
    role = Column(String, default="VERIFICATION_OFFICER")
    organization = Column(String, nullable=True) # Text display name
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True)
    permissions = Column(Text, nullable=True) # Optional JSON array of specific permissions
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    organization_rel = relationship("Organization", back_populates="users", foreign_keys=[institution_id])
    issued_credentials = relationship("Credential", back_populates="issuer", foreign_keys="[Credential.issuer_id]")

    @property
    def institution(self):
        return self.organization_rel

    @property
    def issued_certificates(self):
        return self.issued_credentials

    @property
    def organization_id(self):
        return self.institution_id

    @organization_id.setter
    def organization_id(self, value):
        self.institution_id = value


class Credential(Base):
    """
    Generalized Credential entity.
    Uses 'certificates' table name for backward-compatibility with existing records.
    """
    __tablename__ = "certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(String, unique=True, index=True) # Unique ID (e.g. CV-2026-83921 / SSBT-2026-...)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"))
    issuer_id = Column(Integer, ForeignKey("users.id"))
    
    # Credential Type: DEGREE, DIPLOMA, CERTIFICATE, TRAINING_CERTIFICATE, INTERNSHIP_CERTIFICATE,
    # EMPLOYMENT_CREDENTIAL, EXPERIENCE_LETTER, PROFESSIONAL_CERTIFICATION, LICENSE, ACHIEVEMENT, OTHER
    certificate_type = Column(String, default="DEGREE")
    category = Column(String, default="ACADEMIC") # ACADEMIC, RECRUITMENT, TECHNICAL_COURSE, ACHIEVEMENT
    
    holder_name = Column(String)
    student_id = Column(String, nullable=True) # Holder Identifier (PRN / Employee ID / Candidate ID / License ID)
    course_name = Column(String) # Degree / Program / Role / Certification Title
    department = Column(String, nullable=True)
    academic_year = Column(String, nullable=True) # Session / Tenure
    marks_obtained = Column(Float, nullable=True)
    total_marks = Column(Float, nullable=True)
    percentage = Column(Float, nullable=True)
    cgpa = Column(Float, nullable=True)
    grade = Column(String, nullable=True)
    remarks = Column(String, nullable=True)
    
    # Recruitment & Technical Domain Fields
    role_designation = Column(String, nullable=True)
    organization_company = Column(String, nullable=True)
    skills_acquired = Column(String, nullable=True)
    employment_type = Column(String, nullable=True) # Full-Time, Internship, Contract
    license_number = Column(String, nullable=True)
    score_or_rank = Column(String, nullable=True)
    
    issue_date = Column(DateTime)
    expiry_date = Column(DateTime, nullable=True)
    document_path = Column(String, nullable=True)
    document_hash = Column(String, nullable=True) # SHA-256 Digest
    qr_token = Column(String, unique=True, index=True)
    
    # Lifecycle: DRAFT, ISSUED, ACTIVE, EXPIRED, REVOKED, SUSPICIOUS
    status = Column(String, default="ACTIVE")
    suspicious_reason = Column(Text, nullable=True)
    
    # Cryptographic digital signature (RSA-PSS with SHA-256)
    digital_signature = Column(Text, nullable=True)
    signature_algorithm = Column(String, default="RSA-PSS-SHA256")
    signer_public_key_fingerprint = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=True) # Arbitrary domain metadata
    
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    
    organization_rel = relationship("Organization", back_populates="credentials", foreign_keys=[institution_id])
    issuer = relationship("User", back_populates="issued_credentials", foreign_keys=[issuer_id])
    
    status_history = relationship("CredentialStatusHistory", back_populates="credential", cascade="all, delete-orphan")
    verification_requests = relationship("VerificationRequest", back_populates="credential")
    fraud_analyses = relationship("FraudAnalysis", back_populates="credential")
    fraud_cases = relationship("FraudCase", back_populates="credential")
    monitoring_subscriptions = relationship("MonitoringSubscription", back_populates="credential", cascade="all, delete-orphan")

    @property
    def institution(self):
        return self.organization_rel

    @property
    def credential_id(self):
        return self.certificate_id

    @credential_id.setter
    def credential_id(self, value):
        self.certificate_id = value

    @property
    def organization_id(self):
        return self.institution_id

    @organization_id.setter
    def organization_id(self, value):
        self.institution_id = value

    @property
    def credential_type(self):
        return self.certificate_type

    @credential_type.setter
    def credential_type(self, value):
        self.certificate_type = value

    @property
    def holder_identifier(self):
        return self.student_id

    @holder_identifier.setter
    def holder_identifier(self, value):
        self.student_id = value

# Backward compatibility alias
Certificate = Credential


class CredentialStatusHistory(Base):
    __tablename__ = "certificate_status_history"
    
    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(Integer, ForeignKey("certificates.id"))
    previous_status = Column(String)
    new_status = Column(String)
    reason = Column(Text, nullable=True)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime, default=utcnow)
    
    credential = relationship("Credential", back_populates="status_history", foreign_keys=[certificate_id])
    changer = relationship("User")

    @property
    def certificate(self):
        return self.credential

# Backward compatibility alias
CertificateStatusHistory = CredentialStatusHistory


class VerificationRequest(Base):
    __tablename__ = "verification_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True)
    certificate_id = Column(Integer, ForeignKey("certificates.id"), nullable=True)
    searched_certificate_id = Column(String, nullable=True)
    verification_method = Column(String, default="MANUAL_ID") # MANUAL_ID, QR_SCAN, UPLOAD, API, BATCH
    requested_by = Column(String, nullable=True) # User ID / Name / API Key Client / IP
    timestamp = Column(DateTime, default=utcnow)
    result = Column(String) # VERIFIED, REVIEW_REQUIRED, HIGH_RISK, REVOKED, EXPIRED, NOT_FOUND
    
    credential = relationship("Credential", back_populates="verification_requests", foreign_keys=[certificate_id])
    results = relationship("VerificationResult", back_populates="request", uselist=False, cascade="all, delete-orphan")

    @property
    def certificate(self):
        return self.credential


class VerificationResult(Base):
    __tablename__ = "verification_results"
    
    id = Column(Integer, primary_key=True, index=True)
    verification_request_id = Column(Integer, ForeignKey("verification_requests.id"))
    verification_id = Column(String, unique=True, index=True, nullable=True) # VER-2026-000918
    organization_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True)
    credential_id = Column(Integer, ForeignKey("certificates.id", ondelete="SET NULL"), nullable=True)
    
    # Check outcomes
    registry_check = Column(String, default="MATCH") # MATCH, MISMATCH, NOT_FOUND
    qr_check = Column(String, nullable=True) # VALID, INVALID, NOT_APPLICABLE
    hash_check = Column(String, nullable=True) # VALID, FAILED, NOT_APPLICABLE
    signature_check = Column(String, nullable=True) # VALID, INVALID, NOT_APPLICABLE
    issuer_check = Column(String, default="VERIFIED") # VERIFIED, UNVERIFIED
    metadata_check = Column(String, nullable=True)
    document_analysis = Column(String, nullable=True) # CLEAN, ANOMALY_DETECTED
    
    # Intelligence Scoring
    fraud_risk_score = Column(Float, default=0.0) # 0-100
    risk_level = Column(String, default="LOW") # LOW, MEDIUM, HIGH, CRITICAL
    confidence = Column(Float, default=0.95)
    trust_score = Column(Float, default=95.0) # 0-100
    trust_breakdown_json = Column(Text, nullable=True) # JSON scoring weights
    issuer_trust_score = Column(Float, default=94.0) # 0-100
    
    final_result = Column(String) # VERIFIED, REVIEW_REQUIRED, HIGH_RISK, REVOKED, EXPIRED, NOT_FOUND
    explanation = Column(Text)
    evidence_metadata_json = Column(Text, nullable=True) # Full tamper & comparison breakdown
    timestamp = Column(DateTime, default=utcnow)
    
    request = relationship("VerificationRequest", back_populates="results")


class FraudCase(Base):
    """
    Dedicated Enterprise Fraud Investigation Center Case.
    """
    __tablename__ = "fraud_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String, unique=True, index=True) # FC-2026-00812
    credential_id = Column(Integer, ForeignKey("certificates.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String, default="HIGH") # LOW, MEDIUM, HIGH, CRITICAL
    indicators_json = Column(Text, nullable=True) # List of detected fraud factors
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, default="OPEN") # OPEN, UNDER_REVIEW, CONFIRMED_FRAUD, FALSE_POSITIVE, RESOLVED
    notes_json = Column(Text, nullable=True) # Investigator notes timeline
    created_at = Column(DateTime, default=utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    credential = relationship("Credential", back_populates="fraud_cases")
    organization = relationship("Organization", back_populates="fraud_cases")
    investigator = relationship("User", foreign_keys=[assigned_to])


class ApiKey(Base):
    """
    Enterprise API Key for B2B Client integration.
    """
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(String, unique=True, index=True) # ssbt_key_...
    organization_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"))
    name = Column(String) # e.g. "Workday HR Integration"
    environment = Column(String, default="TEST") # TEST, PRODUCTION
    hashed_secret = Column(String, index=True) # SHA-256 hash of secret key
    prefix = Column(String) # First 8 chars of key for identification
    permissions_json = Column(Text, nullable=True) # Scoped permissions JSON
    rate_limit_per_minute = Column(Integer, default=120)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    status = Column(String, default="ACTIVE") # ACTIVE, REVOKED
    created_at = Column(DateTime, default=utcnow)
    
    organization = relationship("Organization", back_populates="api_keys")


class Webhook(Base):
    """
    Enterprise Webhook subscription for automated event broadcasting.
    """
    __tablename__ = "webhooks"
    
    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(String, unique=True, index=True) # wh_...
    organization_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"))
    endpoint_url = Column(String)
    secret = Column(String) # HMAC secret for payload signing
    events_json = Column(Text) # JSON list of subscribed events
    status = Column(String, default="ACTIVE") # ACTIVE, INACTIVE
    created_at = Column(DateTime, default=utcnow)
    
    organization = relationship("Organization", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id", ondelete="CASCADE"))
    event_type = Column(String)
    payload_json = Column(Text)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    success = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=utcnow)
    
    webhook = relationship("Webhook", back_populates="deliveries")


class MonitoringSubscription(Base):
    """
    Continuous Credential Monitoring Watch.
    """
    __tablename__ = "monitoring_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"))
    credential_id = Column(Integer, ForeignKey("certificates.id", ondelete="CASCADE"))
    subscriber_email = Column(String, nullable=True)
    webhook_url = Column(String, nullable=True)
    last_status = Column(String, default="ACTIVE")
    alert_on = Column(String, default="ALL") # ALL, REVOCATION, EXPIRATION, SUSPICIOUS
    status = Column(String, default="ACTIVE") # ACTIVE, PAUSED
    created_at = Column(DateTime, default=utcnow)
    
    organization = relationship("Organization", back_populates="monitoring_subscriptions")
    credential = relationship("Credential", back_populates="monitoring_subscriptions")
    alerts = relationship("MonitoringAlert", back_populates="subscription", cascade="all, delete-orphan")


class MonitoringAlert(Base):
    __tablename__ = "monitoring_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("monitoring_subscriptions.id", ondelete="CASCADE"), nullable=True)
    organization_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"))
    credential_id = Column(Integer, ForeignKey("certificates.id", ondelete="CASCADE"))
    previous_status = Column(String)
    new_status = Column(String)
    alert_type = Column(String) # REVOKED, EXPIRED, FLAGGED_SUSPICIOUS, INTEGRITY_MISMATCH
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    
    subscription = relationship("MonitoringSubscription", back_populates="alerts")


class AuditLog(Base):
    """
    Immutable Centralized Audit Log.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True)
    action = Column(String) # USER_CREATED, LOGIN_SUCCESS, CREDENTIAL_ISSUED, VERIFICATION_PERFORMED, etc.
    resource = Column(String) # CREDENTIAL, ORGANIZATION, API_KEY, FRAUD_CASE, etc.
    resource_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    result = Column(String, default="SUCCESS") # SUCCESS, FAILURE, DENIED
    metadata_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utcnow)
    
    user = relationship("User", foreign_keys=[user_id])
    organization = relationship("Organization", foreign_keys=[organization_id])


class FraudAnalysis(Base):
    """
    Backward-compatibility table for existing fraud analysis entries.
    """
    __tablename__ = "fraud_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    certificate_id = Column(Integer, ForeignKey("certificates.id"), nullable=True)
    analysis_type = Column(String)
    risk_score = Column(Float)
    detected_indicators = Column(Text)
    confidence = Column(Float)
    created_at = Column(DateTime, default=utcnow)
    
    credential = relationship("Credential", back_populates="fraud_analyses", foreign_keys=[certificate_id])
