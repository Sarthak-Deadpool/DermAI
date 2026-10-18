from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


from app.models.user import User
from app.schemas.patient import PatientCreate, PatientUpdate
from app.services.patient_service import (
    create_patient,
    get_patient_by_id,
    get_patient_by_clinician,
    update_patient,
    delete_patient,
    create_user_patient,
    get_patient_by_user,
    update_user_patient,
    delete_user_patient,
)

def handle_controller_error(exc: Exception) -> None:
    if isinstance(exc, HTTPException):
        raise exc

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred while processing the patient request.",
    ) from exc
    
    
    

def create_patient_controller(
    db:Session,
    patient_data: PatientCreate,
    current_user : User,
):
    try:
        return create_patient(
            db=db,
            patient_data=patient_data,
            clinician_id=current_user.id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        handle_controller_error(exc)
        
        
    
def list_patients_controller(
    db:Session,
    current_user: User,
):
    try:
        
        return get_patient_by_clinician(
            db=db,
            clinician_id=current_user.id,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        handle_controller_error(exc)
        
        
    
def get_patient_controller(
    db:Session,
    patient_id:UUID,
    current_user:User,
):
    try:
        return get_patient_by_id(
            db=db,
            patient_id=patient_id,
            clinician_id=current_user.id,
        )
    except HTTPException:
            raise
    except Exception as exc:
            handle_controller_error(exc)
            
            
            
            
def update_patient_controller(
    db:Session,
    patient_id:UUID,
    patient_data :PatientUpdate,
    current_user: User,
):
    try:
        return update_patient(
            db=db,
            patient_id=patient_id,
            clinician_id=current_user.id,
            patient_data=patient_data,
        )
    except HTTPException:
            raise
    except Exception as exc:
            handle_controller_error(exc)
            
            
def delete_patient_controller(
    db:Session,
    patient_id:UUID,
    current_user:User,
):
    try:
        delete_patient(
            db=db,
            patient_id=patient_id,
            clinician_id=current_user.id,
        )
    except HTTPException:
            raise
    except Exception as exc:
            handle_controller_error(exc)
            
            
            
            
def create_user_patient_controller(
    db:Session,
    patient_data: PatientCreate,
    current_user: User,
): 
    
    try:
        return create_user_patient(
            db=db,
            patient_data=patient_data,
            user_id=current_user.id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        handle_controller_error(exc)
                
def get_my_patient_controller(
    db:Session,
    current_user: User,
):
    try:
        return get_patient_by_user(
            db=db,
            user_id=current_user.id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        handle_controller_error(exc)
        
def update_my_patient_controller(
    db:Session,
    patient_data:PatientUpdate,
    current_user: User,
):
    try:
        return update_user_patient(
            db=db,
            user_id=current_user.id,
            patient_data=patient_data,
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        handle_controller_error(exc)
        
def delete_my_patient_controller(
    db:Session,
    current_user:User,
)-> None:
    try:
        
        delete_user_patient(
            db=db,
            user_id=current_user.id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        handle_controller_error(exc)