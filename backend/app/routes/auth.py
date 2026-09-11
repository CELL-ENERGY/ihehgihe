"""
Authentication routes for Jan Nidhi Spotter Backend.

Endpoints:
    POST /auth/register - Register a new citizen account
    POST /auth/login    - Log in and obtain JWT Bearer token
    GET  /auth/me       - Get authenticated user profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
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
def register(
    payload: UserRegister,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Register a new citizen or admin account."""
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    hashed = hash_password(payload.password)
    user = User(
        email=payload.email.lower(),
        name=payload.name.strip(),
        hashed_password=hashed,
        xp=0,
        level=1,
        is_admin=bool(payload.is_admin),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email, user.is_admin)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in to obtain JWT Bearer token",
    description="Authenticates citizen or admin by username or email and password.",
)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Log in with email or username and password."""
    identifier = (payload.username or payload.email or "").strip().lower()
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide an email or username.",
        )

    # Search by email or username
    user = (
        db.query(User)
        .filter(
            (User.email == identifier)
            | (User.email == f"{identifier}@jannidhi.gov.in")
        )
        .first()
    )

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please check your username/email and password.",
        )

    # Sync level just in case
    user.level = calculate_level(user.xp)
    db.commit()

    token = create_access_token(user.id, user.email, user.is_admin)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns profile information for the authenticated user.",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return profile for currently logged-in user."""
    return UserResponse.model_validate(current_user)
