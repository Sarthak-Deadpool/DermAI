from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.case import CaseCreate
from app.services.case_service import(
    create_new_case,
    get_user_case,
    list_user_cases
)

def create_case_controller(
    db:Session,
    case_data: CaseCreate,
    current_user: User,
):
    return create_new_case(
        db=db,
        case_data=case_data,
        owner_user_id=current_user.id,
    )
    
def list_cases_controller(
    db:Session,
    current_user: User,
):
    return list_user_cases(
        db=db,
        owner_user_id=current_user.id,
    )

def get_case_controller(
    db: Session,
    case_id: UUID,
    current_user: User,
):
    case = get_user_case(
        db= db,
        case_id=case_id,
        owner_user_id=current_user.id,
    )
    
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
        
    return case

