from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column


from app.db.database import Base


class RevokedToken(Base):
    __tablename__="revoked_token"

    jti:Mapped[str] = mapped_column(
        String(64),
        primary_key=True,

    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
