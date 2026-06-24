"""
Security utilities for authentication and authorization
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import re
import logging

logger = logging.getLogger(__name__)

# =========================================================
# Password hashing (Argon2 primary, bcrypt fallback)
# =========================================================
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],   # argon2 for new hashes, bcrypt for old ones
    deprecated="auto",
    argon2__time_cost=3,
    argon2__memory_cost=65536,      # 64 MB
    argon2__parallelism=2
)

# =========================================================
# JWT settings
# =========================================================
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    ""
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30 * 24 * 60)
)  # 30 days default

# =========================================================
# Password constraints (UX-level, not crypto limits)
# =========================================================
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 50  # user-friendly limit


def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password meets requirements BEFORE hashing

    Requirements:
    - Minimum 8 characters
    - Maximum 50 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """
    if not password:
        return False, "Password is required"

    # Character length check
    length = len(password)
    if length < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"

    if length > MAX_PASSWORD_LENGTH:
        return False, f"Password must be less than {MAX_PASSWORD_LENGTH} characters long"

    # Complexity checks
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    return True, None


def get_password_hash(password: str) -> str:
    """
    Hash a password with validation
    """
    try:
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            raise ValueError(error_msg)

        return pwd_context.hash(password)

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        raise ValueError("Failed to hash password")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    """
    to_encode = data.copy()

    expire = (
        datetime.utcnow() + expires_delta
        if expires_delta
        else datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise credentials_exception


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate Indian phone number format"""
    pattern = r"^(\+91|91)?[6-9]\d{9}$"
    cleaned = re.sub(r"[\s\-]", "", phone)
    return bool(re.match(pattern, cleaned))
