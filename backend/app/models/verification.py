"""
MongoDB document helpers and representations for Jan Nidhi Spotter Backend.

Provides lightweight model classes and serializes documents from MongoDB collections:
- users
- citizen_verifications
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional


class User:
    """Represents a User document from MongoDB."""

    def __init__(self, **kwargs):
        self.id: int = kwargs.get("id", 0)
        self.email: str = kwargs.get("email", "")
        self.name: str = kwargs.get("name", "")
        self.hashed_password: str = kwargs.get("hashed_password", "")
        self.xp: int = kwargs.get("xp", 0)
        self.level: int = kwargs.get("level", 1)
        self.is_admin: bool = bool(kwargs.get("is_admin", False))
        self.created_at: datetime = kwargs.get("created_at") or datetime.now(timezone.utc)

    @classmethod
    def from_doc(cls, doc: Optional[Dict[str, Any]]) -> Optional["User"]:
        if not doc:
            return None
        return cls(**doc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "hashed_password": self.hashed_password,
            "xp": self.xp,
            "level": self.level,
            "is_admin": self.is_admin,
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', xp={self.xp}, level={self.level})>"


class CitizenVerification:
    """Represents a CitizenVerification document from MongoDB."""

    def __init__(self, **kwargs):
        self.id: int = kwargs.get("id", 0)
        self.user_id: int = kwargs.get("user_id", 0)
        self.work_id: Optional[str] = kwargs.get("work_id")
        self.citizen_handle: str = kwargs.get("citizen_handle", "")
        self.locality_name: str = kwargs.get("locality_name", "")
        self.structure_type: str = kwargs.get("structure_type", "")
        self.ground_observation: str = kwargs.get("ground_observation", "")
        self.observation: Optional[str] = kwargs.get("observation") or self.ground_observation
        self.latitude: float = float(kwargs.get("latitude", 0.0))
        self.longitude: float = float(kwargs.get("longitude", 0.0))
        self.comment: Optional[str] = kwargs.get("comment")
        self.citizen_name: Optional[str] = kwargs.get("citizen_name")
        self.image_url: str = kwargs.get("image_url", "")
        self.image_storage_path: Optional[str] = kwargs.get("image_storage_path")
        self.review_status: str = kwargs.get("review_status", "Pending")
        self.xp_awarded: int = kwargs.get("xp_awarded", 0)
        self.xp_claimed: bool = bool(kwargs.get("xp_claimed", False))
        self.xp_claimed_at: Optional[datetime] = kwargs.get("xp_claimed_at")
        self.xp_awarded_at: Optional[datetime] = kwargs.get("xp_awarded_at")
        self.admin_comment: Optional[str] = kwargs.get("admin_comment")
        self.reviewed_by: Optional[int] = kwargs.get("reviewed_by")
        self.reviewed_at: Optional[datetime] = kwargs.get("reviewed_at")
        self.created_at: datetime = kwargs.get("created_at") or datetime.now(timezone.utc)
        self.updated_at: datetime = kwargs.get("updated_at") or datetime.now(timezone.utc)

    @classmethod
    def from_doc(cls, doc: Optional[Dict[str, Any]]) -> Optional["CitizenVerification"]:
        if not doc:
            return None
        return cls(**doc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "work_id": self.work_id,
            "citizen_handle": self.citizen_handle,
            "locality_name": self.locality_name,
            "structure_type": self.structure_type,
            "ground_observation": self.ground_observation,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "comment": self.comment,
            "citizen_name": self.citizen_name,
            "image_url": self.image_url,
            "image_storage_path": self.image_storage_path,
            "review_status": self.review_status,
            "xp_awarded": self.xp_awarded,
            "xp_claimed": self.xp_claimed,
            "xp_claimed_at": self.xp_claimed_at,
            "xp_awarded_at": self.xp_awarded_at,
            "admin_comment": self.admin_comment,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        return (
            f"<CitizenVerification(id={self.id}, handle='{self.citizen_handle}', "
            f"locality='{self.locality_name}', status='{self.review_status}')>"
        )
