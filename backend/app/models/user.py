import uuid
import enum

from sqlalchemy import DateTime, Enum as SQLAlchemyEnum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column



from app.db.database import Base

class UserRole(str, enum.Enum):
    USER = "user"
    CLINICIAN = "clinician"
    RESEARCHER = "researcher"
    DATA_SCIENTIST = "data_scientist"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"


    id:Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False,

    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SQLAlchemyEnum(
            UserRole,
            name = "user_role_enum",
            values_callable=lambda enum_cls:[
                member.value for member in enum_cls
            ],
            validate_string=True,
        ),

        default=UserRole.USER,
        nullable=False,
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )