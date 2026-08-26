import base64
import hashlib
import logging
from cryptography.fernet import Fernet
from api.core.config import settings

logger = logging.getLogger(__name__)


def get_fernet() -> Fernet:
    """
    Return a Fernet cipher backed by the dedicated ENCRYPTION_KEY.
    Falls back to a key derived from SECRET_KEY only when ENCRYPTION_KEY is
    unset, so previously encrypted values remain readable during migration.
    """
    master = settings.ENCRYPTION_KEY
    if not master:
        logger.warning(
            "ENCRYPTION_KEY is not configured; deriving the Fernet key from "
            "SECRET_KEY. Set ENCRYPTION_KEY to a dedicated secret."
        )
        master = settings.SECRET_KEY
    key_hash = hashlib.sha256(master.encode()).digest()
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
