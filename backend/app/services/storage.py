"""
Supabase Storage service for uploading citizen proof images.

Handles:
- MIME type validation (JPEG, PNG, WebP only)
- File size validation (≤ 10 MB)
- UUID-based safe filename generation
- Upload to the configured Supabase Storage bucket
- Returns the public URL of the uploaded image
"""

import os
import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile
from supabase import create_client, Client

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
SUPABASE_BUCKET: str = os.getenv("SUPABASE_BUCKET", "citizen-proofs")

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


def _get_supabase_client() -> Client:
    """Create and return a Supabase client. Raises if credentials are missing."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(
            status_code=500,
            detail="Supabase credentials are not configured on the server.",
        )
    return create_client(SUPABASE_URL, SUPABASE_KEY)


async def upload_image(
    file: UploadFile,
    verification_uuid: str,
) -> str:
    """
    Validate and upload a citizen proof image to Supabase Storage.

    Args:
        file: The uploaded file from the request.
        verification_uuid: A UUID string used to namespace the upload path.

    Returns:
        The public URL of the uploaded image.

    Raises:
        HTTPException 400: If the file type is invalid or file is too large.
        HTTPException 500: If the upload to Supabase fails.
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

    # --- 3. Generate a safe unique filename ---
    extension = MIME_TO_EXT.get(content_type, ".jpg")
    safe_filename = f"{uuid.uuid4().hex}{extension}"

    # Structured path: proofs/{verification_uuid}/{safe_filename}
    storage_path = f"proofs/{verification_uuid}/{safe_filename}"

    # --- 4. Upload to Supabase Storage ---
    try:
        supabase = _get_supabase_client()
        supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": content_type},
        )
    except HTTPException:
        # Re-raise our own HTTP exceptions (e.g. missing credentials)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload image to storage: {str(e)}",
        )

    # --- 5. Build and return the public URL ---
    public_url = (
        f"{SUPABASE_URL}/storage/v1/object/public/"
        f"{SUPABASE_BUCKET}/{storage_path}"
    )

    return public_url
