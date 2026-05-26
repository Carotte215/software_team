import hashlib
import secrets


def hash_password(plain: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(plain: str, stored: str) -> bool:
    if not plain or not stored:
        return False
    try:
        scheme, salt, digest_hex = stored.split("$", 2)
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()
    return secrets.compare_digest(digest, digest_hex)


def default_initial_password(student_id: str) -> str:
    tail = student_id[-6:] if len(student_id) >= 6 else student_id
    return f"Stu@{tail}"
