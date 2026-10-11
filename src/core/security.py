"""
Security utilities: Password hashing, verification, and validation for MEMMS.
"""
import bcrypt
from config import MIN_PASSWORD_LENGTH


def hash_password(plain_password: str) -> str:
    """
    Hashes a plain-text password using bcrypt with salt.
    Returns the string representation of the hashed password.
    """
    if not plain_password or len(plain_password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
    
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against the stored bcrypt hash.
    Safe against timing attacks.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validates password complexity.
    """
    if not password:
        return False, "Password cannot be empty."
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
    return True, ""
