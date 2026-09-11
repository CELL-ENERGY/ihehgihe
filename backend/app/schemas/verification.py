"""
Pydantic schemas and enums for Jan Nidhi Spotter Backend.

Enforces:
- Mandatory structure types and ground observation values
- Authentication request/response validation
- Verification response with XP details
- Claim XP response
- User dashboard metrics
- Admin review updates
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class StructureType(str, Enum):
    """Allowed structure types as specified in requirements."""
    COMMUNITY_HALL = "Community Hall"
    SHELTER = "Shelter"
    SOLAR_STREET_LIGHT = "Solar Street Light"
    PUBLIC_WATER_RO = "Public Water RO Plant"
    PUBLIC_LIBRARY = "Public Library / Study Center"
    DRAINAGE = "Drainage"
    CONCRETE_ROAD = "Concrete Road"
    OTHER = "Other"


class GroundObservation(str, Enum):
    """Allowed ground observation values."""
    WORK_COMPLETED = "WORK_COMPLETED"
    WORK_IN_PROGRESS = "WORK_IN_PROGRESS"
    NO_WORK_FOUND = "NO_WORK_FOUND"


# Alias for backward compatibility
ObservationType = GroundObservation


class ReviewStatus(str, Enum):
    """Allowed review statuses."""
    PENDING = "Pending"
    UNDER_REVIEW = "Under Review"
    VERIFIED = "Verified"
    REJECTED = "Rejected"


# ---------------------------------------------------------------------------
# Authentication Schemas
# ---------------------------------------------------------------------------

class UserRegister(BaseModel):
    """Payload for POST /auth/register."""
    email: str = Field(..., min_length=3, max_length=255)
    name: str = Field(..., min_length=2, max_length=200)
    password: str = Field(..., min_length=6)
    is_admin: Optional[bool] = False


class UserLogin(BaseModel):
    """Payload for POST /auth/login."""
    email: Optional[str] = None
    username: Optional[str] = None
    password: str


class UserResponse(BaseModel):
    """User profile response."""
    id: int
    email: str
    name: str
    xp: int
    level: int
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT Token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---------------------------------------------------------------------------
# Verification Schemas
# ---------------------------------------------------------------------------

class VerificationResponse(BaseModel):
    """Detailed verification record."""
    id: int
    user_id: int
    work_id: Optional[str] = None
    citizen_handle: str
    locality_name: str
    structure_type: str
    ground_observation: str
    latitude: Decimal
    longitude: Decimal
    comment: Optional[str] = None
    citizen_name: Optional[str] = None
    image_url: str
    review_status: str
    xp_awarded: int = 0
    xp_claimed: bool = False
    xp_claimed_at: Optional[datetime] = None
    xp_awarded_at: Optional[datetime] = None
    admin_comment: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VerificationCreateResponse(BaseModel):
    """Response after submitting a verification."""
    status: str = "success"
    message: str = "Verification Submitted Successfully!"
    verification_id: int
    image_url: str
    review_status: str = "Pending"
    xp_awarded: int = 0
    xp_claimed: bool = False
    xp_eligible: int = 150


class VerificationStatusUpdate(BaseModel):
    """Body for PATCH /verifications/{id}/status."""
    review_status: Optional[str] = None
    status: Optional[str] = None


class AdminReviewUpdate(BaseModel):
    """Body for PATCH /admin/verifications/{id}/review or PATCH /admin/verifications/{id}."""
    review_status: Optional[str] = None
    status: Optional[str] = None
    admin_comment: Optional[str] = None


class UserDashboardResponse(BaseModel):
    """Dashboard statistics for authenticated citizen."""
    user_id: int
    name: str
    email: str
    current_xp: int
    current_level: int
    next_level_xp: int
    xp_to_next_level: int
    progress_percent: int
    total_submissions: int
    verified_submissions: int
    pending_submissions: int
    rejected_submissions: int


class StatsResponse(BaseModel):
    """Aggregated global verification statistics."""
    total: int = 0
    pending: int = 0
    under_review: int = 0
    verified: int = 0
    rejected: int = 0
    no_work_found: int = 0
    work_completed: int = 0
    work_in_progress: int = 0
