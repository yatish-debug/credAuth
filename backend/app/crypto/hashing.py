import hashlib
import os

def generate_file_hash(file_path: str) -> str:
    """
    Generate SHA-256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_file_hash(file_path: str, expected_hash: str) -> bool:
    """
    Verify if a file matches the expected hash.
    """
    if not os.path.exists(file_path):
        return False
    return generate_file_hash(file_path) == expected_hash
