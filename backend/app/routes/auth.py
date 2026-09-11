"""
Authentication routes for Jan Nidhi Spotter Backend using MongoDB.

Endpoints:
    POST /auth/register - Register a new citizen account
    POST /auth/login    - Log in and obtain JWT Bearer token
    GET  /auth/me       - Get authenticated user profile
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from app.database.database import get_next_sequence, get_users_collection
from app.models.verification import User
from app.schemas.verification import TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.auth import (
    calculate_level,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new citizen account",
    description="Registers a new user account and returns an access token.",
)
async def register(
    payload: UserRegister,
) -> TokenResponse:
    """Register a new citizen or admin account in MongoDB."""
    users_col = get_users_collection()
    email_clean = payload.email.lower().strip()

    existing = await users_col.find_one({"email": email_clean})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    user_id = await get_next_sequence("user_id")
    hashed = hash_password(payload.password)
    now = datetime.now(timezone.utc)

    user_doc = {
        "id": user_id,
        "email": email_clean,
        "name": payload.name.strip(),
        "hashed_password": hashed,
        "xp": 0,
        "level": 1,
        "is_admin": bool(payload.is_admin),
        "created_at": now,
    }
    await users_col.insert_one(user_doc)

    token = create_access_token(user_id, email_clean, bool(payload.is_admin))
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user_id,
            email=email_clean,
            name=payload.name.strip(),
            xp=0,
            level=1,
            is_admin=bool(payload.is_admin),
            created_at=now,
        ),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in to obtain JWT Bearer token",
    description="Authenticates citizen or admin by username or email and password.",
)
async def login(
    payload: UserLogin,
) -> TokenResponse:
    """Log in with email or username and password."""
    identifier = (payload.username or payload.email or "").strip().lower()
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide an email or username.",
        )

    users_col = get_users_collection()
    user_doc = await users_col.find_one({
        "$or": [
            {"email": identifier},
            {"email": f"{identifier}@jannidhi.gov.in"},
        ]
    })

    if not user_doc or not verify_password(payload.password, user_doc.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please check your username/email and password.",
        )

    user_id = user_doc["id"]
    current_xp = user_doc.get("xp", 0)
    current_level = calculate_level(current_xp)

    if current_level != user_doc.get("level", 1):
        await users_col.update_one({"id": user_id}, {"$set": {"level": current_level}})
        user_doc["level"] = current_level

    token = create_access_token(user_id, user_doc["email"], bool(user_doc.get("is_admin", False)))
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user_id,
            email=user_doc["email"],
            name=user_doc.get("name", ""),
            xp=current_xp,
            level=current_level,
            is_admin=bool(user_doc.get("is_admin", False)),
            created_at=user_doc.get("created_at") or datetime.now(timezone.utc),
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns profile information for the authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return profile for currently logged-in user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        xp=current_user.xp,
        level=current_user.level,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
    )
