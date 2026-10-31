from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.dependencies.authorization import require_roles
from app.dependencies.database import get_db
from app.models.user import  User, UserRole
from app.services.audit_service import record_audit_event

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
    prefix="/api/v1/patients",
    tags=["Patients"],
)

@router.post(
    "/me",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_patient_route(
    patient_data:PatientCreate,
    request: Request,
    db:Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.USER)
    ),
):
    patient = create_user_patient_controller(
        db=db,
        patient_data=patient_data,
        current_user=current_user,
    )
    record_audit_event(db, "patient_created", "success", current_user.id, "patient", str(patient.id), request.client.host if request.client else None)
    return patient
    
@router.get(
    "/me",
    response_model=PatientResponse,
)
def get_my_patient_route(
    request: Request,
    db:Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.USER)
    ),
):
    patient = get_my_patient_controller(
        db=db,
        current_user=current_user,
    )
    record_audit_event(db, "patient_viewed", "success", current_user.id, "patient", str(patient.id), request.client.host if request.client else None)
    return patient

@router.patch(
    "/me",
    response_model=PatientResponse,
)
def update_my_patient_route(
    patient_data: PatientUpdate,
    request: Request,
    db: Session =Depends(get_db),
    current_user: User =Depends(
        require_roles(UserRole.USER)
    ),
):
    patient = update_my_patient_controller(
        db=db,
        patient_data=patient_data,
        current_user=current_user,
    )
    record_audit_event(db, "patient_updated", "success", current_user.id, "patient", str(patient.id), request.client.host if request.client else None)
    return patient

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_my_patient_route(
    request: Request,
    db: Session =Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.USER)
    ),
):
    patient = get_my_patient_controller(db=db, current_user=current_user)
    delete_my_patient_controller(
        db=db,
        current_user=current_user,
    )
    record_audit_event(db, "patient_archived", "success", current_user.id, "patient", str(patient.id), request.client.host if request.client else None)
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    
    
    

@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_patient_route(
    patient_data:PatientCreate,
    request: Request,
    db:Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.CLINICIAN)
    ),
):
    patient = create_patient_controller(
        db=db,
        patient_data=patient_data,
        current_user=current_user,
    )
    record_audit_event(db, "patient_created", "success", current_user.id, "patient", str(patient.id), request.client.host if request.client else None)
    return patient
    
    
@router.get(
    "/",
    response_model=list[PatientResponse],
    
)
def list_patient_route(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=40),
    db: Session = Depends(get_db),
    current_user : User = Depends(
        require_roles(UserRole.CLINICIAN)
    ),
):
    return list_patients_controller(
        db=db,
        current_user=current_user,
        offset=offset,
        limit=limit,
        search=search,
    )
 
 
@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
)   
def get_patient_route(
    patient_id:UUID,
    request: Request,
    db:Session = Depends(get_db),
    current_user : User = Depends(
        require_roles(UserRole.CLINICIAN)
    ),
):
    
    patient = get_patient_controller(
        db=db,
        patient_id=patient_id,
        current_user=current_user,
    )
    record_audit_event(db, "patient_viewed", "success", current_user.id, "patient", str(patient.id), request.client.host if request.client else None)
    return patient
    
@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
)
def update_patient_route(
    patient_id :UUID,
    patient_data : PatientUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user :User = Depends(
        require_roles(UserRole.CLINICIAN)
    ),
):
    patient = update_patient_controller(
        db=db,
        patient_id=patient_id,
        patient_data= patient_data,
        current_user=current_user,
    )
    record_audit_event(db, "patient_updated", "success", current_user.id, "patient", str(patient.id), request.client.host if request.client else None)
    return patient
    
@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_patient_route(
    patient_id:UUID,
    request: Request,
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
    record_audit_event(db, "patient_archived", "success", current_user.id, "patient", str(patient_id), request.client.host if request.client else None)
    
    return None
