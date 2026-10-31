import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


from app.db.database import Base


class Patient(Base):
    __tablename__ = "patients"

    __table_args__ = (
        CheckConstraint("age >= 0 AND age <= 120", name="ck_patient_age_range"),
        CheckConstraint(
            """
            (user_id IS NOT NULL AND clinician_id IS NULL)
            OR
            (user_id IS NULL AND clinician_id IS NOT NULL)
            """,
            name="ck_patient_exactly_one_owner",
        ),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    patient_code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    # Nullable so existing patient records remain valid after the additive migration.
    patient_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(30), nullable=False, default="prefer_not_to_say")
    medical_history: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    known_allergies: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    fitzpatrick_type: Mapped[str | None] = mapped_column(String(20), nullable=True)

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        unique=True,
        index=True,
    )
    clinician_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
