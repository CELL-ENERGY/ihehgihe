"""
MongoDB Storage service for uploading citizen proof images using GridFS.

Handles:
- MIME type validation (JPEG, PNG, WebP only)
- File size validation (≤ 10 MB)
- Upload to MongoDB GridFS bucket
- Returns the public URL of the uploaded image (/images/{file_id})
"""

import os
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from dotenv import load_dotenv
from fastapi import HTTPException, Request, UploadFile
from fastapi.responses import Response
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from app.database.database import get_database

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# Allowed MIME types for proof images
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Map MIME types to file extensions
MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

# Maximum upload size: 10 MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def get_gridfs_bucket() -> AsyncIOMotorGridFSBucket:
    """Get AsyncIOMotorGridFSBucket instance bound to active database."""
    db = get_database()
    return AsyncIOMotorGridFSBucket(db)


async def upload_image(
    file: UploadFile,
    verification_uuid: str,
    request: Optional[Request] = None,
) -> str:
    """
    Validate and upload a citizen proof image to MongoDB GridFS.

    Args:
        file: The uploaded file from the request.
        verification_uuid: A UUID string used to namespace or reference the upload.
        request: FastAPI Request instance used to build absolute URLs.

    Returns:
        The public URL of the uploaded image (/images/{file_id}).

    Raises:
        HTTPException 400: If the file type is invalid or file is too large.
        HTTPException 500: If the upload to MongoDB fails.
    """

    # --- 1. Validate MIME type ---
    content_type = file.content_type or ""
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid image type: '{content_type}'. "
                f"Allowed types: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
            ),
        )

    # --- 2. Read file content and validate size ---
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Image too large: {file_size / (1024 * 1024):.1f} MB. "
                f"Maximum allowed size is 10 MB."
            ),
        )

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # --- 3. Generate filename ---
    extension = MIME_TO_EXT.get(content_type, ".jpg")
    filename = f"proof_{verification_uuid}{extension}"

    # --- 4. Upload to MongoDB GridFS ---
    try:
        bucket = get_gridfs_bucket()
        file_id = await bucket.upload_from_stream(
            filename,
            file_content,
            metadata={
                "content_type": content_type,
                "verification_uuid": verification_uuid,
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload image to MongoDB storage: {str(e)}",
        )

    # --- 5. Build and return public image URL ---
    if request:
        base_url = str(request.base_url).rstrip("/")
        return f"{base_url}/images/{file_id}"

    return f"/images/{file_id}"


async def get_image_response(file_id_str: str) -> Response:
    """
    Retrieve image from MongoDB GridFS and return as a FastAPI Response.

    Args:
        file_id_str: String representation of the GridFS file ObjectId.

    Returns:
        FastAPI Response containing image bytes and correct media_type.
    """
    try:
        file_id = ObjectId(file_id_str)
    except InvalidId:
        raise HTTPException(status_code=404, detail="Image not found.")

    bucket = get_gridfs_bucket()
    try:
        grid_out = await bucket.open_download_stream(file_id)
        content = await grid_out.read()
        metadata = grid_out.metadata or {}
        content_type = metadata.get("content_type", "image/jpeg")
        return Response(content=content, media_type=content_type)
    except Exception:
        raise HTTPException(status_code=404, detail="Image not found.")
