import uuid

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Case(Base):
    __tablename__ = "cases"
    
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    
    case_label: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    
    image_source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    
    body_location : Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    
    status: Mapped[str] = mapped_column(
        String(30),
        default="new",
        nullable=False,
    )
    
    created_at:Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )