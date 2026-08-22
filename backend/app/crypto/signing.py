import base64
import hashlib
import json
from typing import Dict, Any, Tuple, Union
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

def generate_institution_keypair() -> Tuple[str, str, str]:
    """
    Generate an RSA-2048 keypair for an institution.
    Returns (private_key_pem, public_key_pem, key_fingerprint).
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    # Calculate SHA-256 fingerprint of the public key
    raw_public_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    fingerprint = hashlib.sha256(raw_public_der).hexdigest()
    formatted_fingerprint = ":".join(fingerprint[i:i+2].upper() for i in range(0, len(fingerprint), 2))[:47]
    
    return private_pem, public_pem, formatted_fingerprint

def canonicalize_payload(payload: Dict[str, Any]) -> bytes:
    """
    Produce deterministic JSON representation of a payload for signing/verification.
    """
    canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return canonical_json.encode('utf-8')

def sign_certificate_payload(private_key_or_pem: Union[str, rsa.RSAPrivateKey], payload: Dict[str, Any]) -> str:
    """
    Sign a certificate payload dictionary using the institution's private key.
    Uses RSA-PSS with SHA-256 and returns a URL-safe Base64 signature.
    """
    if isinstance(private_key_or_pem, str):
        private_key = serialization.load_pem_private_key(
            private_key_or_pem.encode('utf-8'),
            password=None
        )
    else:
        private_key = private_key_or_pem
    
    message_bytes = canonicalize_payload(payload)
    
    signature = private_key.sign(
        message_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    return base64.b64encode(signature).decode('utf-8')

def verify_certificate_signature(public_key_or_pem: Union[str, rsa.RSAPublicKey], payload: Dict[str, Any], signature_b64: str) -> bool:
    """
    Verify a digital signature against a certificate payload using the institution's public key.
    """
    try:
        if isinstance(public_key_or_pem, str):
            public_key = serialization.load_pem_public_key(
                public_key_or_pem.encode('utf-8')
            )
        else:
            public_key = public_key_or_pem
            
        signature = base64.b64decode(signature_b64.encode('utf-8'))
        message_bytes = canonicalize_payload(payload)
        
        public_key.verify(
            signature,
            message_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False
