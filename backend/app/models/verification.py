"""
SQLAlchemy models for Jan Nidhi Spotter Backend.

Includes:
- User: Citizen & admin accounts with XP and level tracking.
- CitizenVerification: Citizen-submitted ground verification records with
  photo proof metadata, GPS coordinates, structure details, review status,
  and deferred XP claim tracking.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.database import Base


class User(Base):
    """Registered user account (citizen or admin)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    xp = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    verifications = relationship(
        "CitizenVerification",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', xp={self.xp}, level={self.level})>"


class CitizenVerification(Base):
    """
    Citizen-submitted ground proof/verification for public works.
    Every citizen submission requires:
      1. Citizen Handle / ID
      2. Locality Name
      3. Structure Type
      4. Ground Observation
      5. GPS Location (Latitude, Longitude)
      6. Photographic Proof (stored in Supabase Storage)
    """

    __tablename__ = "citizen_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Authenticated user account ownership
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Optional linkage to MPLADS work
    work_id = Column(String(100), nullable=True, index=True)

    # Citizen-entered handle / identifier
    citizen_handle = Column(String(100), nullable=False)

    # Locality (e.g. "Salt Lake Sector V")
    locality_name = Column(String(200), nullable=False)

    # Structure Type (e.g. "Community Hall", "Shelter", etc.)
    structure_type = Column(String(100), nullable=False)

    # Ground Observation: WORK_COMPLETED | WORK_IN_PROGRESS | NO_WORK_FOUND
    ground_observation = Column(String(50), nullable=False)

    # Alias for backward compatibility
    observation = Column(String(50), nullable=True)

    # GPS coordinates (mandatory in business logic)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)

    # Optional citizen notes / legacy name
    comment = Column(Text, nullable=True)
    citizen_name = Column(String(200), nullable=True)

    # Photographic proof in Supabase Storage
    image_url = Column(Text, nullable=False)
    image_storage_path = Column(Text, nullable=True)

    # Review status: Pending | Under Review | Verified | Rejected
    review_status = Column(String(50), default="Pending", nullable=False)

    # XP Gamification — awarded automatically by backend when admin sets VERIFIED
    xp_awarded = Column(Integer, default=0, nullable=False)
    xp_claimed = Column(Boolean, default=False, nullable=False, index=True)  # True = XP was awarded
    xp_claimed_at = Column(DateTime, nullable=True)
    xp_awarded_at = Column(DateTime, nullable=True)  # When XP was awarded by admin

    # Admin review tracking
    admin_comment = Column(Text, nullable=True)
    reviewed_by = Column(Integer, nullable=True)    # Admin user ID who reviewed
    reviewed_at = Column(DateTime, nullable=True)   # When admin reviewed

    # Timestamps
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship to user
    user = relationship("User", back_populates="verifications")

    def __repr__(self) -> str:
        return (
            f"<CitizenVerification(id={self.id}, handle='{self.citizen_handle}', "
            f"locality='{self.locality_name}', status='{self.review_status}', xp_awarded={self.xp_awarded})>"
        )

