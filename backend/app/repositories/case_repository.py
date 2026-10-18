from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


from app.models.case import Case
from app.schemas.case import CaseCreate



def create_case(
    db:Session,
    case_data: CaseCreate,
    owner_user_id:UUID,
)-> Case:
    try:
        new_case =Case(
            **case_data.model_dump(),
            owner_user_id=owner_user_id,
        )
        db.add(new_case)
        db.commit()
        db.refresh(new_case)
        return new_case
    except SQLAlchemyError:
        db.rollback()
        raise
    


def get_cases_by_owner(
    db:Session,
    owner_user_id:UUID,
) -> list[Case]:
    statement = (
        select(Case)
        .where(Case.owner_user_id == owner_user_id)
        .order_by(Case.created_at.desc())
    )
    
    return list(db.scalars(statement).all())

def get_case_by_id_and_owner(
    db:Session,
    case_id: UUID,
    owner_user_id:UUID,
) -> Case | None:
    statement = select(Case).where(
        Case.id == case_id,
        Case.owner_user_id == owner_user_id
    )
    
    return db.scalars(statement).first()


def get_cases_by_patient(
    db:Session,
    patient_id :UUID,
    owner_user_id: UUID,
) -> list[Case]:
    statement = (
        select(Case)
        .where(
            Case.patient_id == patient_id,
            Case.owner_user_id == owner_user_id,
        )
        .order_by(Case.created_at.desc())
    )
    
    return list(db.scalar(statement).all())