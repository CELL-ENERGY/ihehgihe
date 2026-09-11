"""
API routes for citizen verification submissions.

Endpoints:
    POST   /verifications/                         - Submit citizen verification (all 6 fields mandatory)
    GET    /verifications/                         - List all verifications (supports filters)
    GET    /verifications/stats                    - Global verification statistics
    GET    /verifications/{id}                     - Single verification by ID
    GET    /verifications/work/{work_id:path}      - Verifications by Work ID
    PATCH  /verifications/{id}/status              - Update review status

Citizen Portal Endpoints:
    GET    /users/me/dashboard                     - Authenticated citizen dashboard & XP progression
    GET    /users/me/submissions                   - Authenticated citizen submission history

Admin Portal Endpoints:
    GET    /admin/verifications                    - Admin: all submissions with full detail
    PATCH  /admin/verifications/{id}/review        - Admin: approve/reject — auto-awards 150 XP on VERIFIED
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.verification import CitizenVerification, User
from app.schemas.verification import (
    AdminReviewUpdate,
    GroundObservation,
    ReviewStatus,
    StatsResponse,
    StructureType,
    UserDashboardResponse,
    VerificationCreateResponse,
    VerificationResponse,
    VerificationStatusUpdate,
)
from app.services.auth import (
    XP_PER_VERIFICATION,
    calculate_level,
    calculate_level_progress,
    decode_access_token,
    get_admin_user,
    get_current_user,
    security,
)
from app.services.storage import upload_image

router = APIRouter(
    tags=["Citizen Verification"],
)


def _resolve_user(creds, db: Session) -> User:
    """Resolve authenticated user from Bearer token. Raises 401 if not authenticated."""
    if creds and creds.credentials:
        try:
            payload = decode_access_token(creds.credentials)
            user_id = int(payload.get("sub", 0))
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return user
        except Exception:
            pass

    raise HTTPException(
        status_code=401,
        detail="Authentication required. Please log in to submit a verification.",
    )


# ---------------------------------------------------------------------------
# POST /verifications/ — Submit Citizen Verification (ALL 6 FIELDS MANDATORY)
# ---------------------------------------------------------------------------

@router.post(
    "/verifications/",
    response_model=VerificationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit citizen verification proof (MANDATORY FIELDS)",
    description=(
        "Submits ground verification with 6 mandatory fields:\n"
        "1. Citizen Handle / ID\n"
        "2. Locality Name\n"
        "3. Structure Type (Community Hall, Shelter, etc.)\n"
        "4. Ground Observation (WORK_COMPLETED, WORK_IN_PROGRESS, NO_WORK_FOUND)\n"
        "5. GPS Location (Latitude & Longitude)\n"
        "6. Photographic Proof (JPG/JPEG/PNG/WEBP, max 10MB)\n\n"
        "XP is NOT awarded upon submission. Exactly 150 XP is awarded automatically "
        "only after administrator review and approval."
    ),
)
async def create_verification(
    citizen_handle: str = Form(None, description="Citizen Handle / ID *"),
    locality_name: str = Form(None, description="Locality Name * (e.g. Salt Lake Sector V)"),
    structure_type: str = Form(None, description="Structure Type *"),
    ground_observation: str = Form(None, description="Ground Observation *"),
    latitude: str = Form(None, description="GPS Latitude * (e.g. 22.5726)"),
    longitude: str = Form(None, description="GPS Longitude * (e.g. 88.3639)"),
    proof_image: UploadFile = File(None, description="Upload Ground Photo * (Max 10 MB)"),
    # Optional legacy fields
    work_id: Optional[str] = Form(None, description="Optional MPLADS Work ID"),
    comment: Optional[str] = Form(None, description="Optional citizen comment"),
    citizen_name: Optional[str] = Form(None, description="Optional citizen name"),
    observation: Optional[str] = Form(None, description="Legacy observation field alias"),
    creds=Depends(security),
    db: Session = Depends(get_db),
) -> VerificationCreateResponse:
    """Validate mandatory fields, upload image, and record verification."""

    # --- 1. Validate Mandatory Citizen Handle ---
    if not citizen_handle or not citizen_handle.strip():
        # Fallback to citizen_name or raise
        if citizen_name and citizen_name.strip():
            citizen_handle = citizen_name.strip()
        else:
            raise HTTPException(
                status_code=400,
                detail="Citizen Handle / ID is mandatory.",
            )
    citizen_handle = citizen_handle.strip()

    # --- 2. Validate Mandatory Locality Name ---
    if not locality_name or not locality_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Locality Name is mandatory. (e.g. Salt Lake Sector V)",
        )
    locality_name = locality_name.strip()

    # --- 3. Validate Mandatory Structure Type ---
    if not structure_type or not structure_type.strip():
        raise HTTPException(
            status_code=400,
            detail="Structure Type is mandatory.",
        )
    structure_type = structure_type.strip()
    valid_structures = [s.value for s in StructureType]
    if structure_type not in valid_structures:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Structure Type: '{structure_type}'. Allowed: {', '.join(valid_structures)}",
        )

    # --- 4. Validate Mandatory Ground Observation ---
    obs_val = ground_observation or observation
    if not obs_val or not obs_val.strip():
        raise HTTPException(
            status_code=400,
            detail="Please select your ground observation.",
        )
    obs_val = obs_val.strip()
    try:
        GroundObservation(obs_val)
    except ValueError:
        valid_obs = [o.value for o in GroundObservation]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ground observation: '{obs_val}'. Allowed: {', '.join(valid_obs)}",
        )

    # --- 5. Validate Mandatory GPS Location ---
    if latitude is None or str(latitude).strip() == "" or longitude is None or str(longitude).strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Location is required to submit a verification.",
        )

    try:
        parsed_lat = Decimal(str(latitude).strip())
        parsed_lon = Decimal(str(longitude).strip())
    except (InvalidOperation, ValueError):
        raise HTTPException(
            status_code=400,
            detail="Invalid GPS coordinates format.",
        )

    # --- 6. Validate Mandatory Ground Photo ---
    if proof_image is None or not proof_image.filename:
        raise HTTPException(
            status_code=400,
            detail="Please upload a photo.",
        )

    # --- 7. Resolve Authenticated User ---
    user = _resolve_user(creds, db)

    # --- 8. Upload Photo to Supabase Storage ---
    verification_uuid = uuid.uuid4().hex
    image_url = await upload_image(
        file=proof_image,
        verification_uuid=verification_uuid,
    )

    # --- 9. Save Verification in PostgreSQL (XP is NOT awarded here) ---
    clean_work_id = work_id.strip() if work_id else None

    new_ver = CitizenVerification(
        user_id=user.id,
        work_id=clean_work_id,
        citizen_handle=citizen_handle,
        locality_name=locality_name,
        structure_type=structure_type,
        ground_observation=obs_val,
        observation=obs_val,
        latitude=parsed_lat,
        longitude=parsed_lon,
        comment=comment,
        citizen_name=citizen_name or citizen_handle,
        image_url=image_url,
        image_storage_path=f"proofs/{verification_uuid}",
        review_status="PENDING",
        xp_awarded=0,          # STRICT RULE: 0 awarded on submission
        xp_claimed=False,      # STRICT RULE: Awarded only after admin approval
        xp_claimed_at=None,
        xp_awarded_at=None,
        reviewed_by=None,
        reviewed_at=None,
    )

    try:
        db.add(new_ver)
        db.commit()
        db.refresh(new_ver)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save verification record: {str(e)}",
        )

    return VerificationCreateResponse(
        status="success",
        message="Verification Submitted Successfully!",
        verification_id=new_ver.id,
        image_url=image_url,
        review_status="PENDING",
        xp_awarded=0,
        xp_claimed=False,
        xp_eligible=XP_PER_VERIFICATION,
    )


# ---------------------------------------------------------------------------
# User Dashboard & Submission History Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/users/me/dashboard",
    response_model=UserDashboardResponse,
    summary="Get citizen dashboard stats & XP level",
    description="Returns current XP, level, progress to next level, and submission counts.",
)
def get_user_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserDashboardResponse:
    """Return citizen dashboard metrics."""
    # Compute counts
    total = (
        db.query(func.count(CitizenVerification.id))
        .filter(CitizenVerification.user_id == current_user.id)
        .scalar() or 0
    )
    verified = (
        db.query(func.count(CitizenVerification.id))
        .filter(
            CitizenVerification.user_id == current_user.id,
            func.upper(CitizenVerification.review_status) == "VERIFIED",
        )
        .scalar() or 0
    )
    pending = (
        db.query(func.count(CitizenVerification.id))
        .filter(
            CitizenVerification.user_id == current_user.id,
            func.upper(CitizenVerification.review_status) == "PENDING",
        )
        .scalar() or 0
    )
    rejected = (
        db.query(func.count(CitizenVerification.id))
        .filter(
            CitizenVerification.user_id == current_user.id,
            func.upper(CitizenVerification.review_status) == "REJECTED",
        )
        .scalar() or 0
    )

    prog = calculate_level_progress(current_user.xp)

    return UserDashboardResponse(
        user_id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        current_xp=current_user.xp,
        current_level=prog["level"],
        next_level_xp=prog["next_level_xp"],
        xp_to_next_level=prog["xp_needed"],
        progress_percent=prog["progress_percent"],
        total_submissions=total,
        verified_submissions=verified,
        pending_submissions=pending,
        rejected_submissions=rejected,
    )


@router.get(
    "/users/me/submissions",
    response_model=List[VerificationResponse],
    summary="Get current citizen submission history",
    description="Returns list of all ground verifications submitted by the logged-in citizen.",
)
def get_user_submissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[VerificationResponse]:
    """List submissions for current user."""
    return (
        db.query(CitizenVerification)
        .filter(CitizenVerification.user_id == current_user.id)
        .order_by(CitizenVerification.created_at.desc())
        .all()
    )


# ---------------------------------------------------------------------------
# Admin Portal Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/admin/verifications",
    summary="Admin view of all citizen verifications",
    description="Returns all citizen verifications with registered user info and evidence for admin review.",
)
def get_admin_verifications(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Admin view showing all verifications with associated user info."""
    results = (
        db.query(CitizenVerification, User)
        .join(User, CitizenVerification.user_id == User.id)
        .order_by(CitizenVerification.created_at.desc())
        .all()
    )

    data = []
    for ver, user in results:
        data.append({
            "id": ver.id,
            "citizen_handle": ver.citizen_handle,
            "locality_name": ver.locality_name,
            "structure_type": ver.structure_type,
            "ground_observation": ver.ground_observation,
            "latitude": float(ver.latitude),
            "longitude": float(ver.longitude),
            "image_url": ver.image_url,
            "review_status": ver.review_status,
            "admin_comment": ver.admin_comment,
            "xp_awarded": ver.xp_awarded,
            "xp_claimed": ver.xp_claimed,
            "xp_claimed_at": ver.xp_claimed_at.isoformat() if ver.xp_claimed_at else None,
            "xp_awarded_at": ver.xp_awarded_at.isoformat() if ver.xp_awarded_at else None,
            "reviewed_by": ver.reviewed_by,
            "reviewed_at": ver.reviewed_at.isoformat() if ver.reviewed_at else None,
            "created_at": ver.created_at.isoformat(),
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "xp": user.xp,
                "level": user.level,
            },
        })
    return data


@router.patch(
    "/admin/verifications/{verification_id}/review",
    response_model=VerificationResponse,
    summary="Admin review decision — auto-awards 150 XP on VERIFIED",
    description=(
        "Admin sets verification status. When status=VERIFIED:\n"
        "- Exactly 150 XP is awarded to the submitting citizen\n"
        "- Citizen level is recalculated\n"
        "- Duplicate XP protection: already-verified records do NOT award additional XP\n"
        "Requires admin authentication."
    ),
)
@router.patch(
    "/admin/verifications/{verification_id}",
    response_model=VerificationResponse,
    summary="Admin review decision alias",
)
def admin_review_verification(
    verification_id: int,
    payload: AdminReviewUpdate,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
) -> VerificationResponse:
    """Admin approve/reject verification. Auto-awards XP on VERIFIED."""
    ver = (
        db.query(CitizenVerification)
        .filter(CitizenVerification.id == verification_id)
        .first()
    )
    if not ver:
        raise HTTPException(
            status_code=404,
            detail=f"Verification with ID {verification_id} not found.",
        )

    raw_status = (payload.status or payload.review_status or "").strip()
    if not raw_status:
        raise HTTPException(
            status_code=400,
            detail="Status is required (e.g. VERIFIED or REJECTED).",
        )

    upper_status = raw_status.upper()
    if upper_status in ["VERIFIED", "VERIFY"]:
        normalized_status = "VERIFIED"
    elif upper_status in ["REJECTED", "REJECT"]:
        normalized_status = "REJECTED"
    elif upper_status in ["UNDER_REVIEW", "UNDER REVIEW", "UNDER-REVIEW"]:
        normalized_status = "UNDER_REVIEW"
    elif upper_status in ["PENDING"]:
        normalized_status = "PENDING"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: '{raw_status}'. Allowed: PENDING, UNDER_REVIEW, VERIFIED, REJECTED",
        )

    now = datetime.now(timezone.utc)

    # --- Auto-award 150 XP when status becomes VERIFIED with duplicate protection ---
    if normalized_status == "VERIFIED":
        if not ver.xp_claimed and ver.xp_awarded == 0:
            citizen = db.query(User).filter(User.id == ver.user_id).first()
            if citizen:
                citizen.xp += XP_PER_VERIFICATION
                citizen.level = calculate_level(citizen.xp)

            ver.xp_awarded = XP_PER_VERIFICATION
            ver.xp_claimed = True                    # Prevents double-awarding
            ver.xp_claimed_at = now
            ver.xp_awarded_at = now
    elif normalized_status == "REJECTED":
        if not ver.xp_claimed:
            ver.xp_awarded = 0

    # --- Record admin review metadata ---
    ver.review_status = normalized_status
    ver.reviewed_by = admin.id
    ver.reviewed_at = now
    if payload.admin_comment is not None:
        ver.admin_comment = payload.admin_comment.strip()

    db.commit()
    db.refresh(ver)
    return ver


# ---------------------------------------------------------------------------
# General Verification Endpoints (Filters, Single ID, Stats)
# ---------------------------------------------------------------------------

@router.get(
    "/verifications/",
    response_model=List[VerificationResponse],
    summary="List citizen verifications",
    description="Returns citizen verification records. Supports optional filters.",
)
def list_verifications(
    work_id: Optional[str] = None,
    observation: Optional[str] = None,
    review_status: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[VerificationResponse]:
    """List verifications with optional filters."""
    query = db.query(CitizenVerification)
    if work_id:
        query = query.filter(CitizenVerification.work_id == work_id)
    if observation:
        query = query.filter(
            (CitizenVerification.ground_observation == observation)
            | (CitizenVerification.observation == observation)
        )
    if review_status:
        query = query.filter(CitizenVerification.review_status == review_status)

    return query.order_by(CitizenVerification.created_at.desc()).all()


@router.get(
    "/verifications/stats",
    response_model=StatsResponse,
    summary="Get verification statistics",
    description="Aggregated counts by review status and observation type.",
)
def get_stats(db: Session = Depends(get_db)) -> StatsResponse:
    """Return aggregated stats using SQL queries."""
    total = db.query(func.count(CitizenVerification.id)).scalar() or 0
    pending = (
        db.query(func.count(CitizenVerification.id))
        .filter(CitizenVerification.review_status == "Pending")
        .scalar() or 0
    )
    under_review = (
        db.query(func.count(CitizenVerification.id))
        .filter(CitizenVerification.review_status == "Under Review")
        .scalar() or 0
    )
    verified = (
        db.query(func.count(CitizenVerification.id))
        .filter(CitizenVerification.review_status == "Verified")
        .scalar() or 0
    )
    rejected = (
        db.query(func.count(CitizenVerification.id))
        .filter(CitizenVerification.review_status == "Rejected")
        .scalar() or 0
    )

    no_work = (
        db.query(func.count(CitizenVerification.id))
        .filter(
            (CitizenVerification.ground_observation == "NO_WORK_FOUND")
            | (CitizenVerification.observation == "NO_WORK_FOUND")
        )
        .scalar() or 0
    )
    work_comp = (
        db.query(func.count(CitizenVerification.id))
        .filter(
            (CitizenVerification.ground_observation == "WORK_COMPLETED")
            | (CitizenVerification.observation == "WORK_COMPLETED")
        )
        .scalar() or 0
    )
    work_prog = (
        db.query(func.count(CitizenVerification.id))
        .filter(
            (CitizenVerification.ground_observation == "WORK_IN_PROGRESS")
            | (CitizenVerification.observation == "WORK_IN_PROGRESS")
        )
        .scalar() or 0
    )

    return StatsResponse(
        total=total,
        pending=pending,
        under_review=under_review,
        verified=verified,
        rejected=rejected,
        no_work_found=no_work,
        work_completed=work_comp,
        work_in_progress=work_prog,
    )


@router.get(
    "/verifications/{verification_id}",
    response_model=VerificationResponse,
    summary="Get verification by ID",
)
def get_verification(
    verification_id: int,
    db: Session = Depends(get_db),
) -> VerificationResponse:
    """Get single verification record."""
    ver = (
        db.query(CitizenVerification)
        .filter(CitizenVerification.id == verification_id)
        .first()
    )
    if not ver:
        raise HTTPException(
            status_code=404,
            detail=f"Verification with ID {verification_id} not found.",
        )
    return ver


@router.get(
    "/verifications/work/{work_id:path}",
    response_model=List[VerificationResponse],
    summary="Get verifications by Work ID",
)
def get_verifications_by_work(
    work_id: str,
    db: Session = Depends(get_db),
) -> List[VerificationResponse]:
    """Get all verifications matching work_id."""
    return (
        db.query(CitizenVerification)
        .filter(CitizenVerification.work_id == work_id)
        .order_by(CitizenVerification.created_at.desc())
        .all()
    )


@router.patch(
    "/verifications/{verification_id}/status",
    response_model=VerificationResponse,
    summary="Update verification review status",
)
def update_verification_status(
    verification_id: int,
    status_update: VerificationStatusUpdate,
    db: Session = Depends(get_db),
) -> VerificationResponse:
    """Update review status."""
    ver = (
        db.query(CitizenVerification)
        .filter(CitizenVerification.id == verification_id)
        .first()
    )
    if not ver:
        raise HTTPException(
            status_code=404,
            detail=f"Verification with ID {verification_id} not found.",
        )

    ver.review_status = status_update.review_status.value
    db.commit()
    db.refresh(ver)
    return ver
