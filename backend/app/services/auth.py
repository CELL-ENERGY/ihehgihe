"""
Authentication & XP calculation services for Jan Nidhi Spotter Backend.

Provides:
- Secure password hashing with PBKDF2 HMAC SHA-256
- JWT creation and validation
- XP constants and level progression calculator
- FastAPI dependency for extracting the authenticated User from MongoDB
"""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database.database import get_users_collection
from app.models.verification import User

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# ---------------------------------------------------------------------------
# Constants & Configuration
# ---------------------------------------------------------------------------

JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY", "jan-nidhi-spotter-secret-key-2026-secure")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 72

# Constant XP awarded per claimed verification (NEVER trust client XP)
XP_PER_VERIFICATION = 150

# Level progression: 300 XP per level
XP_PER_LEVEL = 300

security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Password Hashing
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique salt."""
    salt = secrets.token_hex(16)
    iterations = 100_000
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return f"{salt}${iterations}${pwd_hash}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against PBKDF2-HMAC-SHA256 hash."""
    try:
        salt, iterations_str, original_hash = hashed_password.split("$")
        iterations = int(iterations_str)
        test_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        ).hex()
        return hmac.compare_digest(test_hash, original_hash)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT Token Generation & Verification
# ---------------------------------------------------------------------------

def create_access_token(user_id: int, email: str, is_admin: bool = False) -> str:
    """Generate a signed JWT token."""
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "is_admin": is_admin,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please log in again.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )


# ---------------------------------------------------------------------------
# XP & Level Calculation
# ---------------------------------------------------------------------------

def calculate_level(xp: int) -> int:
    """
    Calculate user level from total XP.
    Level 1: 0 - 299 XP
    Level 2: 300 - 599 XP
    Level 3: 600 - 899 XP
    """
    if xp < 0:
        return 1
    return (xp // XP_PER_LEVEL) + 1


def calculate_level_progress(xp: int) -> dict:
    """Return current level, XP within current level, and progress percentage."""
    level = calculate_level(xp)
    base_xp_for_level = (level - 1) * XP_PER_LEVEL
    next_level_xp = level * XP_PER_LEVEL
    current_in_level = xp - base_xp_for_level
    percent = min(100, int((current_in_level / XP_PER_LEVEL) * 100))
    return {
        "level": level,
        "current_xp": xp,
        "next_level_xp": next_level_xp,
        "xp_needed": next_level_xp - xp,
        "progress_percent": percent,
    }


# ---------------------------------------------------------------------------
# FastAPI Dependency for Authenticated User
# ---------------------------------------------------------------------------

async def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """
    Extract and validate authenticated user from Bearer token using MongoDB.
    Raises HTTP 401 if missing or invalid.
    """
    if not creds or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a Bearer token.",
        )

    payload = decode_access_token(creds.credentials)
    user_id = int(payload.get("sub", 0))

    users_col = get_users_collection()
    doc = await users_col.find_one({"id": user_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
        )

    return User.from_doc(doc)


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Validate that the authenticated user has admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )
    return current_user
