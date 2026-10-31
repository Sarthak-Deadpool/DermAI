from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AuthRateLimitBucket(Base):
    """Shared fixed-window counter; key hashes contain no raw email or IP."""

    __tablename__ = "auth_rate_limit_buckets"
    __table_args__ = (
        CheckConstraint("attempt_count > 0", name="ck_auth_rate_limit_attempt_count"),
    )

    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
