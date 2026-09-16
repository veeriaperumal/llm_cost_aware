import os
import base64
import hashlib
from cryptography.fernet import Fernet
from typing import Optional

def _get_encryption_key() -> bytes:
    custom_key = os.getenv("ENCRYPTION_SECRET_KEY", "").strip()
    if custom_key:
        # If user passed a 32-urlsafe base64 key or a regular passphrase, hash it to 32 bytes
        try:
            # Test if already valid 32-byte urlsafe base64
            decoded = base64.urlsafe_b64decode(custom_key)
            if len(decoded) == 32:
                return custom_key.encode("utf-8")
        except Exception:
            pass
        # Derive 32 bytes key via SHA256
        key_bytes = hashlib.sha256(custom_key.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(key_bytes)
    
    # Fallback to a stable derived salt from workspace path / app name
    salt = "cost_aware_cascading_router_secure_key_salt_2026"
    key_bytes = hashlib.sha256(salt.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(key_bytes)


_fernet: Optional[Fernet] = None

def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_get_encryption_key())
    return _fernet


def encrypt_secret(raw_value: str) -> str:
    """Encrypts plaintext string to base64 encrypted token."""
    if not raw_value:
        return ""
    f = get_fernet()
    return f.encrypt(raw_value.encode("utf-8")).decode("utf-8")


def decrypt_secret(encrypted_value: str) -> str:
    """Decrypts base64 encrypted token to plaintext string."""
    if not encrypted_value:
        return ""
    try:
        f = get_fernet()
        return f.decrypt(encrypted_value.encode("utf-8")).decode("utf-8")
    except Exception:
        return ""


def mask_key(raw_key: str) -> str:
    """Returns a masked representation of the API key for safe UI display (e.g. AIzaSy...9x0a)."""
    if not raw_key:
        return ""
    clean = raw_key.strip()
    if len(clean) <= 8:
        return clean[:2] + "..." + clean[-2:] if len(clean) >= 4 else "..."
    if len(clean) <= 16:
        return clean[:4] + "..." + clean[-3:]
    return clean[:6] + "..." + clean[-4:]
