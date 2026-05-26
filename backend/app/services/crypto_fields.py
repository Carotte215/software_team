import base64
import hashlib

from app.core.config import get_settings


def _derive_key() -> bytes:
    secret = get_settings().auth_secret.encode("utf-8")
    return hashlib.sha256(secret).digest()


def encrypt_text(plain: str) -> str:
    if not plain:
        return ""
    key = _derive_key()
    data = plain.encode("utf-8")
    masked = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.urlsafe_b64encode(masked).decode("ascii")


def decrypt_text(cipher: str) -> str:
    if not cipher:
        return ""
    key = _derive_key()
    data = base64.urlsafe_b64decode(cipher.encode("ascii"))
    plain = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return plain.decode("utf-8")


def mask_id_card(value: str) -> str:
    if len(value) < 8:
        return "****"
    return f"{value[:4]}**********{value[-4:]}"
