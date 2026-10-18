from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session


from app.controllers.case_controller import (
    create_case_controller,
    get_case_controller,
    list_cases_controller,
    list_patient_cases_controller,
)

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.case import CaseCreate, CaseResponse


router = APIRouter(prefix="/api/v1/cases", tags=["Cases"])


@router.post(
    "",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_case_route(
    case_data :CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_case_controller(db, case_data, current_user)


@router.get(
    "",
    response_model=list[CaseResponse],
)
def list_cases_route(
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_cases_controller(db, current_user);


@router.get(
    "/patient/{patient_id}",
    response_model=list[CaseResponse],
)
def list_patient_cases_route(
    patient_id :UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_patient_cases_controller(
        db,
        patient_id,
        current_user,
    )




@router.get(
    "/{case_id}",
    response_model=CaseResponse,
)
def get_case_route(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_case_controller(db, case_id, current_user)