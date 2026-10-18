from uuid import UUID


from fastapi import HTTPException, status
from sqlalchemy.orm import Session



from app.models.case import Case
from app.models.user import User
from app.schemas.case import CaseCreate
from app.services.case_service import(
    create_new_case,
    get_user_case,
    list_user_cases,
    list_patient_cases,
)


def handle_controller_error(exc:Exception) -> None:
    if isinstance(exc, HTTPException):
        raise exc
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred while processing the case request.",
    ) from exc



def create_case_controller(
    db:Session,
    case_data: CaseCreate,
    current_user: User,
): 
    try:
        return create_new_case(
            db=db,
            case_data=case_data,
            owner_user_id=current_user.id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        handle_controller_error(exc)
        
        
        
def list_cases_controller(
    db:Session,
    current_user: User,
):
    try:
        
        return list_user_cases(
            db=db,
            owner_user_id=current_user.id,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        handle_controller_error(exc)
        
        

def get_case_controller(
    db: Session,
    case_id: UUID,
    current_user: User,
):
    try:
        
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
    
    except HTTPException:
        raise
    except Exception as exc:
        handle_controller_error(exc)
        
        
def list_patient_cases_controller(
    db: Session,
    patient_id: UUID,
    current_user: User,
) -> list[Case]:
    try:
        return list_patient_cases(
            db=db,
            patient_id=patient_id,
            owner_user_id=current_user.id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        handle_controller_error(exc)

