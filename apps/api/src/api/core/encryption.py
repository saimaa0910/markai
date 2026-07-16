import base64
import hashlib
from cryptography.fernet import Fernet
from api.core.config import settings


def get_fernet() -> Fernet:
    """
    Derive a 32-byte Fernet key from settings.SECRET_KEY.
    """
    key_hash = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    key_b64 = base64.urlsafe_b64encode(key_hash)
    return Fernet(key_b64)


def encrypt_key(plain_key: str) -> str:
    """
    Encrypt a plain text API key.
    """
    if not plain_key:
        return ""
    f = get_fernet()
    return f.encrypt(plain_key.encode("utf-8")).decode("utf-8")


def decrypt_key(encrypted_key: str) -> str:
    """
    Decrypt an encrypted API key back to plain text.
    """
    if not encrypted_key:
        return ""
    f = get_fernet()
    return f.decrypt(encrypted_key.encode("utf-8")).decode("utf-8")
