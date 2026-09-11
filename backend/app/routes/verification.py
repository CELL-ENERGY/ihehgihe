"""
API routes for citizen verification submissions using MongoDB.

Endpoints:
    POST   /verifications/                         - Submit citizen verification (all 6 fields mandatory)
    GET    /images/{file_id}                       - Retrieve proof image from MongoDB GridFS
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

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status

from app.database.database import (
    get_next_sequence,
    get_users_collection,
    get_verifications_collection,
)
from app.models.verification import User
from app.schemas.verification import (
    AdminReviewUpdate,
    GroundObservation,
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
from app.services.storage import get_image_response, upload_image

router = APIRouter(
    tags=["Citizen Verification"],
)


def _doc_to_verification_response(doc: dict) -> VerificationResponse:
    """Helper to convert MongoDB document to VerificationResponse schema."""
    return VerificationResponse(
        id=doc["id"],
        user_id=doc["user_id"],
        work_id=doc.get("work_id"),
        citizen_handle=doc.get("citizen_handle", ""),
        locality_name=doc.get("locality_name", ""),
        structure_type=doc.get("structure_type", ""),
        ground_observation=doc.get("ground_observation", ""),
        latitude=Decimal(str(doc.get("latitude", 0.0))),
        longitude=Decimal(str(doc.get("longitude", 0.0))),
        comment=doc.get("comment"),
        citizen_name=doc.get("citizen_name"),
        image_url=doc.get("image_url", ""),
        review_status=doc.get("review_status", "Pending"),
        xp_awarded=doc.get("xp_awarded", 0),
        xp_claimed=doc.get("xp_claimed", False),
        xp_claimed_at=doc.get("xp_claimed_at"),
        xp_awarded_at=doc.get("xp_awarded_at"),
        admin_comment=doc.get("admin_comment"),
        reviewed_by=doc.get("reviewed_by"),
        reviewed_at=doc.get("reviewed_at"),
        created_at=doc.get("created_at") or datetime.now(timezone.utc),
        updated_at=doc.get("updated_at") or datetime.now(timezone.utc),
    )


async def _resolve_user(creds) -> User:
    """Resolve authenticated user from Bearer token. Raises 401 if not authenticated."""
    if creds and creds.credentials:
        try:
            payload = decode_access_token(creds.credentials)
            user_id = int(payload.get("sub", 0))
            users_col = get_users_collection()
            user_doc = await users_col.find_one({"id": user_id})
            if user_doc:
                return User.from_doc(user_doc)
        except Exception:
            pass

    raise HTTPException(
        status_code=401,
        detail="Authentication required. Please log in to submit a verification.",
    )


# ---------------------------------------------------------------------------
# GET /images/{file_id} — Retrieve Proof Image from MongoDB GridFS
# ---------------------------------------------------------------------------

@router.get(
    "/images/{file_id}",
    summary="Retrieve proof image from MongoDB GridFS",
    description="Serves uploaded citizen proof image directly from MongoDB GridFS.",
)
async def get_image(file_id: str):
    """Retrieve and serve image from MongoDB GridFS by file_id."""
    return await get_image_response(file_id)


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
    request: Request,
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
) -> VerificationCreateResponse:
    """Validate mandatory fields, upload image to MongoDB GridFS, and record verification."""

    # --- 1. Validate Mandatory Citizen Handle ---
    if not citizen_handle or not citizen_handle.strip():
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
    user = await _resolve_user(creds)

    # --- 8. Upload Photo to MongoDB GridFS Storage ---
    verification_uuid = uuid.uuid4().hex
    image_url = await upload_image(
        file=proof_image,
        verification_uuid=verification_uuid,
        request=request,
    )

    # --- 9. Save Verification in MongoDB ---
    clean_work_id = work_id.strip() if work_id else None
    v_id = await get_next_sequence("verification_id")
    now = datetime.now(timezone.utc)

    new_doc = {
        "id": v_id,
        "user_id": user.id,
        "work_id": clean_work_id,
        "citizen_handle": citizen_handle,
        "locality_name": locality_name,
        "structure_type": structure_type,
        "ground_observation": obs_val,
        "observation": obs_val,
        "latitude": float(parsed_lat),
        "longitude": float(parsed_lon),
        "comment": comment,
        "citizen_name": citizen_name or citizen_handle,
        "image_url": image_url,
        "image_storage_path": f"proofs/{verification_uuid}",
        "review_status": "PENDING",
        "xp_awarded": 0,
        "xp_claimed": False,
        "xp_claimed_at": None,
        "xp_awarded_at": None,
        "admin_comment": None,
        "reviewed_by": None,
        "reviewed_at": None,
        "created_at": now,
        "updated_at": now,
    }

    verifications_col = get_verifications_collection()
    await verifications_col.insert_one(new_doc)

    return VerificationCreateResponse(
        status="success",
        message="Verification Submitted Successfully!",
        verification_id=v_id,
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
async def get_user_dashboard(
    current_user: User = Depends(get_current_user),
) -> UserDashboardResponse:
    """Return citizen dashboard metrics."""
    verifications_col = get_verifications_collection()

    total = await verifications_col.count_documents({"user_id": current_user.id})
    verified = await verifications_col.count_documents({
        "user_id": current_user.id,
        "review_status": {"$regex": "^verified$", "$options": "i"},
    })
    pending = await verifications_col.count_documents({
        "user_id": current_user.id,
        "review_status": {"$regex": "^pending$", "$options": "i"},
    })
    rejected = await verifications_col.count_documents({
        "user_id": current_user.id,
        "review_status": {"$regex": "^rejected$", "$options": "i"},
    })

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
async def get_user_submissions(
    current_user: User = Depends(get_current_user),
) -> List[VerificationResponse]:
    """List submissions for current user."""
    verifications_col = get_verifications_collection()
    cursor = verifications_col.find({"user_id": current_user.id}).sort("created_at", -1)
    docs = await cursor.to_list(length=1000)
    return [_doc_to_verification_response(d) for d in docs]


# ---------------------------------------------------------------------------
# Admin Portal Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/admin/verifications",
    summary="Admin view of all citizen verifications",
    description="Returns all citizen verifications with registered user info and evidence for admin review.",
)
async def get_admin_verifications(
    admin: User = Depends(get_admin_user),
):
    """Admin view showing all verifications with associated user info."""
    verifications_col = get_verifications_collection()
    users_col = get_users_collection()

    ver_docs = await verifications_col.find({}).sort("created_at", -1).to_list(length=1000)

    # Pre-fetch users
    user_ids = list({v.get("user_id") for v in ver_docs if v.get("user_id")})
    users_cursor = users_col.find({"id": {"$in": user_ids}})
    users_list = await users_cursor.to_list(length=len(user_ids) + 10)
    user_map = {u["id"]: u for u in users_list}

    data = []
    for ver in ver_docs:
        u = user_map.get(ver.get("user_id"), {})
        data.append({
            "id": ver["id"],
            "citizen_handle": ver.get("citizen_handle", ""),
            "locality_name": ver.get("locality_name", ""),
            "structure_type": ver.get("structure_type", ""),
            "ground_observation": ver.get("ground_observation", ""),
            "latitude": float(ver.get("latitude", 0.0)),
            "longitude": float(ver.get("longitude", 0.0)),
            "image_url": ver.get("image_url", ""),
            "review_status": ver.get("review_status", "Pending"),
            "admin_comment": ver.get("admin_comment"),
            "xp_awarded": ver.get("xp_awarded", 0),
            "xp_claimed": ver.get("xp_claimed", False),
            "xp_claimed_at": ver["xp_claimed_at"].isoformat() if ver.get("xp_claimed_at") else None,
            "xp_awarded_at": ver["xp_awarded_at"].isoformat() if ver.get("xp_awarded_at") else None,
            "reviewed_by": ver.get("reviewed_by"),
            "reviewed_at": ver["reviewed_at"].isoformat() if ver.get("reviewed_at") else None,
            "created_at": ver["created_at"].isoformat() if ver.get("created_at") else datetime.now(timezone.utc).isoformat(),
            "user": {
                "id": u.get("id", ver.get("user_id")),
                "name": u.get("name", "Unknown Citizen"),
                "email": u.get("email", ""),
                "xp": u.get("xp", 0),
                "level": u.get("level", 1),
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
async def admin_review_verification(
    verification_id: int,
    payload: AdminReviewUpdate,
    admin: User = Depends(get_admin_user),
) -> VerificationResponse:
    """Admin approve/reject verification. Auto-awards XP on VERIFIED."""
    verifications_col = get_verifications_collection()
    users_col = get_users_collection()

    ver = await verifications_col.find_one({"id": verification_id})
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
    xp_awarded = ver.get("xp_awarded", 0)
    xp_claimed = ver.get("xp_claimed", False)
    xp_claimed_at = ver.get("xp_claimed_at")
    xp_awarded_at = ver.get("xp_awarded_at")

    # --- Auto-award 150 XP when status becomes VERIFIED with duplicate protection ---
    if normalized_status == "VERIFIED":
        if not xp_claimed and xp_awarded == 0:
            citizen = await users_col.find_one({"id": ver["user_id"]})
            if citizen:
                new_xp = citizen.get("xp", 0) + XP_PER_VERIFICATION
                new_level = calculate_level(new_xp)
                await users_col.update_one(
                    {"id": citizen["id"]},
                    {"$set": {"xp": new_xp, "level": new_level}}
                )

            xp_awarded = XP_PER_VERIFICATION
            xp_claimed = True
            xp_claimed_at = now
            xp_awarded_at = now
    elif normalized_status == "REJECTED":
        if not xp_claimed:
            xp_awarded = 0

    update_fields = {
        "review_status": normalized_status,
        "reviewed_by": admin.id,
        "reviewed_at": now,
        "xp_awarded": xp_awarded,
        "xp_claimed": xp_claimed,
        "xp_claimed_at": xp_claimed_at,
        "xp_awarded_at": xp_awarded_at,
        "updated_at": now,
    }
    if payload.admin_comment is not None:
        update_fields["admin_comment"] = payload.admin_comment.strip()

    await verifications_col.update_one({"id": verification_id}, {"$set": update_fields})
    updated_ver = await verifications_col.find_one({"id": verification_id})
    return _doc_to_verification_response(updated_ver)


# ---------------------------------------------------------------------------
# General Verification Endpoints (Filters, Single ID, Stats)
# ---------------------------------------------------------------------------

@router.get(
    "/verifications/",
    response_model=List[VerificationResponse],
    summary="List citizen verifications",
    description="Returns citizen verification records. Supports optional filters.",
)
async def list_verifications(
    work_id: Optional[str] = None,
    observation: Optional[str] = None,
    review_status: Optional[str] = None,
) -> List[VerificationResponse]:
    """List verifications with optional filters."""
    verifications_col = get_verifications_collection()
    query = {}
    if work_id:
        query["work_id"] = work_id
    if observation:
        query["$or"] = [
            {"ground_observation": observation},
            {"observation": observation},
        ]
    if review_status:
        query["review_status"] = {"$regex": f"^{review_status}$", "$options": "i"}

    cursor = verifications_col.find(query).sort("created_at", -1)
    docs = await cursor.to_list(length=1000)
    return [_doc_to_verification_response(d) for d in docs]


@router.get(
    "/verifications/stats",
    response_model=StatsResponse,
    summary="Get verification statistics",
    description="Aggregated counts by review status and observation type.",
)
async def get_stats() -> StatsResponse:
    """Return aggregated stats from MongoDB."""
    verifications_col = get_verifications_collection()

    total = await verifications_col.count_documents({})
    pending = await verifications_col.count_documents({
        "review_status": {"$regex": "^pending$", "$options": "i"}
    })
    under_review = await verifications_col.count_documents({
        "review_status": {"$regex": "^under[ _-]review$", "$options": "i"}
    })
    verified = await verifications_col.count_documents({
        "review_status": {"$regex": "^verified$", "$options": "i"}
    })
    rejected = await verifications_col.count_documents({
        "review_status": {"$regex": "^rejected$", "$options": "i"}
    })

    no_work = await verifications_col.count_documents({
        "$or": [
            {"ground_observation": "NO_WORK_FOUND"},
            {"observation": "NO_WORK_FOUND"},
        ]
    })
    work_comp = await verifications_col.count_documents({
        "$or": [
            {"ground_observation": "WORK_COMPLETED"},
            {"observation": "WORK_COMPLETED"},
        ]
    })
    work_prog = await verifications_col.count_documents({
        "$or": [
            {"ground_observation": "WORK_IN_PROGRESS"},
            {"observation": "WORK_IN_PROGRESS"},
        ]
    })

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
async def get_verification(
    verification_id: int,
) -> VerificationResponse:
    """Get single verification record."""
    verifications_col = get_verifications_collection()
    ver = await verifications_col.find_one({"id": verification_id})
    if not ver:
        raise HTTPException(
            status_code=404,
            detail=f"Verification with ID {verification_id} not found.",
        )
    return _doc_to_verification_response(ver)


@router.get(
    "/verifications/work/{work_id:path}",
    response_model=List[VerificationResponse],
    summary="Get verifications by Work ID",
)
async def get_verifications_by_work(
    work_id: str,
) -> List[VerificationResponse]:
    """Get all verifications matching work_id."""
    verifications_col = get_verifications_collection()
    cursor = verifications_col.find({"work_id": work_id}).sort("created_at", -1)
    docs = await cursor.to_list(length=1000)
    return [_doc_to_verification_response(d) for d in docs]


@router.patch(
    "/verifications/{verification_id}/status",
    response_model=VerificationResponse,
    summary="Update verification review status",
)
async def update_verification_status(
    verification_id: int,
    status_update: VerificationStatusUpdate,
) -> VerificationResponse:
    """Update review status."""
    verifications_col = get_verifications_collection()
    ver = await verifications_col.find_one({"id": verification_id})
    if not ver:
        raise HTTPException(
            status_code=404,
            detail=f"Verification with ID {verification_id} not found.",
        )

    new_status = status_update.review_status or status_update.status or "Pending"
    now = datetime.now(timezone.utc)
    await verifications_col.update_one(
        {"id": verification_id},
        {"$set": {"review_status": new_status, "updated_at": now}}
    )
    updated = await verifications_col.find_one({"id": verification_id})
    return _doc_to_verification_response(updated)
