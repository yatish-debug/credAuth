import hmac
import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any, List, Tuple
from jose import jwt
import bcrypt
from app.core.config import settings

# =========================================================================
# RBAC PERMISSIONS MAPPING
# =========================================================================
ALL_PERMISSIONS = [
    "credential:create",
    "credential:read",
    "credential:verify",
    "credential:revoke",
    "credential:delete",
    "verification:create",
    "verification:read",
    "fraud:read",
    "fraud:investigate",
    "fraud:resolve",
    "audit:read",
    "api:create",
    "api:read",
    "api:rotate",
    "api:revoke",
    "organization:manage",
    "user:manage",
    "settings:manage"
]

ROLE_PERMISSIONS = {
    "SUPER_ADMIN": ALL_PERMISSIONS,
    "ORGANIZATION_OWNER": [p for p in ALL_PERMISSIONS if p not in []],
    "ORGANIZATION_ADMIN": [
        "credential:create", "credential:read", "credential:verify", "credential:revoke", "credential:delete",
        "verification:create", "verification:read",
        "fraud:read", "fraud:investigate", "fraud:resolve",
        "audit:read",
        "api:create", "api:read", "api:rotate", "api:revoke",
        "organization:manage", "user:manage", "settings:manage"
    ],
    # Backward compatibility with existing INSTITUTION_ADMIN
    "INSTITUTION_ADMIN": [
        "credential:create", "credential:read", "credential:verify", "credential:revoke", "credential:delete",
        "verification:create", "verification:read",
        "fraud:read", "fraud:investigate", "fraud:resolve",
        "audit:read",
        "api:create", "api:read", "api:rotate", "api:revoke",
        "organization:manage", "user:manage", "settings:manage"
    ],
    "CREDENTIAL_ISSUER": [
        "credential:create", "credential:read", "credential:verify",
        "verification:create", "verification:read"
    ],
    # Backward compatibility with existing ISSUER
    "ISSUER": [
        "credential:create", "credential:read", "credential:verify",
        "verification:create", "verification:read"
    ],
    "VERIFICATION_OFFICER": [
        "credential:read", "credential:verify",
        "verification:create", "verification:read",
        "fraud:read"
    ],
    # Backward compatibility with existing VERIFIER
    "VERIFIER": [
        "credential:read", "credential:verify",
        "verification:create", "verification:read",
        "fraud:read"
    ],
    "AUDITOR": [
        "credential:read",
        "verification:read",
        "fraud:read",
        "audit:read"
    ],
    "API_CLIENT": [
        "credential:read",
        "credential:verify",
        "verification:create",
        "verification:read"
    ]
}

def get_role_permissions(role: str) -> List[str]:
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["VERIFICATION_OFFICER"])

# =========================================================================
# PASSWORD HASHING
# =========================================================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# =========================================================================
# JWT AUTHENTICATION
# =========================================================================
def create_access_token(
    subject: Union[str, Any], 
    role: Optional[str] = None,
    org_id: Optional[int] = None,
    permissions: Optional[List[str]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode = {
        "exp": expire, 
        "sub": str(subject)
    }
    if role:
        to_encode["role"] = role
    if org_id is not None:
        to_encode["org_id"] = org_id
    if permissions:
        to_encode["permissions"] = permissions
        
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

# =========================================================================
# API KEY GENERATION & HASHING
# =========================================================================
def hash_api_key_secret(raw_key: str) -> str:
    """Returns SHA-256 digest of raw API key for secure DB lookup."""
    return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

def generate_api_key(environment: str = "TEST") -> Tuple[str, str, str, str]:
    """
    Generate an enterprise API key.
    Format: ssbt_{env}_{32 random chars}
    Returns: (raw_key, hashed_secret, key_id, prefix)
    """
    env_str = "test" if environment.upper() == "TEST" else "live"
    rand_chars = secrets.token_hex(20)
    raw_key = f"ssbt_{env_str}_{rand_chars}"
    key_id = f"key_{env_str}_{secrets.token_hex(8)}"
    prefix = raw_key[:12] + "..."
    hashed_secret = hash_api_key_secret(raw_key)
    return raw_key, hashed_secret, key_id, prefix

# =========================================================================
# WEBHOOK HMAC SIGNING
# =========================================================================
def generate_webhook_signature(secret: str, payload_bytes: bytes) -> str:
    """Generate HMAC-SHA256 signature for webhook payload."""
    sig = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={sig}"

def verify_webhook_signature(secret: str, payload_bytes: bytes, signature_header: str) -> bool:
    """Verify webhook HMAC signature header securely."""
    expected = generate_webhook_signature(secret, payload_bytes)
    return hmac.compare_digest(expected, signature_header)
