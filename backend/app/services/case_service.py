from uuid import UUID

from sqlalchemy.orm import Session


from app.models.case import Case

from app.repositories.case_repository import (
    create_case,
    get_cases_by_owner,
    get_case_by_id_and_owner,
)

from app.schemas.case import CaseCreate

def create_new_case(
    db: Session,
    case_data: CaseCreate,
    owner_user_id: UUID,
) -> Case:
    return create_case(db, case_data, owner_user_id)


def list_user_cases(
    db:Session,
    owner_user_id:UUID,
) -> list[Case]:
    return get_cases_by_owner(db, owner_user_id)

def get_user_case(
    db: Session,
    case_id:UUID,
    owner_user_id:UUID,
) -> Case | None:
    return get_case_by_id_and_owner(db, case_id, owner_user_id)