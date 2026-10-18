import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    CheckConstraint,
    Column, 
    DateTime, 
    ForeignKey,
    Integer, 
    String
    )
from sqlalchemy.dialects.postgresql import UUID


from app.db.database import Base


class Patient(Base) :
    __tablename__= "patients"
    
    __table_args__ = (
        CheckConstraint(
            """
            (user_id IS NOT NULL AND clinician_id IS NULL)
            OR
            (user_id IS NULL AND clinician_id IS NOT NULL)
            """,
            name="ck_patient_exactly_one_owner",
        ),
    )
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(30), nullable=True)
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        unique=True,
        index=True,
    )
    
    
    clinician_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )