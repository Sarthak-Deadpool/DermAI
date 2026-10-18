from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.dependencies.authorization import require_roles
from app.dependencies.database import get_db
from app.models.user import  User, UserRole

from app.schemas.patient import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
)


from app.controllers.patient_controller import (
    create_patient_controller,
    list_patients_controller,
    get_patient_controller,
    update_patient_controller,
    delete_patient_controller,
    create_user_patient_controller,
    get_my_patient_controller,
    update_my_patient_controller,
    delete_my_patient_controller,
)

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)

@router.post(
    "/me",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_patient_route(
    patient_data:PatientCreate,
    db:Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.USER)
    ),
):
    return create_user_patient_controller(
        db=db,
        patient_data=patient_data,
        current_user=current_user,
    )
    
@router.get(
    "/me",
    response_model=PatientResponse,
)
def get_my_patient_route(
    db:Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.USER)
    ),
):
    return get_my_patient_controller(
        db=db,
        current_user=current_user,
    )

@router.patch(
    "/me",
    response_model=PatientResponse,
)
def update_my_patient_route(
    patient_data: PatientUpdate,
    db: Session =Depends(get_db),
    current_user: User =Depends(
        require_roles(UserRole.USER)
    ),
):
    return update_my_patient_controller(
        db=db,
        patient_data=patient_data,
        current_user=current_user,
    )

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_my_patient_route(
    db: Session =Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.USER)
    ),
):
    delete_my_patient_controller(
        db=db,
        current_user=current_user,
    )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    
    
    

@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_patient_route(
    patient_data:PatientCreate,
    db:Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.CLINICIAN)
    ),
):
    return create_patient_controller(
        db=db,
        patient_data=patient_data,
        current_user=current_user,
    )
    
    
@router.get(
    "/",
    response_model=list[PatientResponse],
    
)
def list_patient_route(
    db: Session = Depends(get_db),
    current_user : User = Depends(
        require_roles(UserRole.CLINICIAN)
    ),
):
    return list_patients_controller(
        db=db,
        current_user=current_user,
    )
 
 
@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
)   
def get_patient_route(
    patient_id:UUID,
    db:Session = Depends(get_db),
    current_user : User = Depends(
        require_roles(UserRole.CLINICIAN)
    ),
):
    
    return get_patient_controller(
        db=db,
        patient_id=patient_id,
        current_user=current_user,
    )
    
@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
)
def update_patient_route(
    patient_id :UUID,
    patient_data : PatientUpdate,
    db: Session = Depends(get_db),
    current_user :User = Depends(
        require_roles(UserRole.CLINICIAN)
    ),
):
    return update_patient_controller(
        db=db,
        patient_id=patient_id,
        patient_data= patient_data,
        current_user=current_user,
    )
    
@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_patient_route(
    patient_id:UUID,
    db: Session =  Depends(get_db),
    current_user : User = Depends(
        require_roles(UserRole.CLINICIAN)
    )
):
    delete_patient_controller(
        db=db,
        patient_id=patient_id,
        current_user=current_user,
    )
    
    return None
