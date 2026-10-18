from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.orm import Session


from app.models.case import Case
from app.models.patient import Patient

from app.repositories.case_repository import (
    create_case,
    get_cases_by_owner,
    get_case_by_id_and_owner,
    get_cases_by_patient,
)

from app.schemas.case import CaseCreate

def validate_patient_access(
    db:Session,
    patient_id :UUID,
    owner_user_id:UUID,
)-> Patient:
    try:
        patient = db.get(Patient, patient_id)
        
        if patient is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found.",
            )
            
        if(
            patient.user_id != owner_user_id
            and patient.clinician_id != owner_user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access this patient.",
            )
        return patient
    
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while validating the patient.",
        ) from exc




def create_new_case(
    db: Session,
    case_data: CaseCreate,
    owner_user_id: UUID,
) -> Case:
    
    try:
        validate_patient_access(
            db,
            case_data.patient_id,
            owner_user_id,
        )
        
        return create_case(
            db,
            case_data,
            owner_user_id,
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while creating the case.",
        ) from exc
        
   


def list_user_cases(
    db:Session,
    owner_user_id:UUID,
) -> list[Case]:
    
    try:
        
        return get_cases_by_owner(db, owner_user_id)
    
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while retrieving cases.",
        ) from exc




def get_user_case(
    db: Session,
    case_id:UUID,
    owner_user_id:UUID,
) -> Case | None:
    
    try:
        
        return get_case_by_id_and_owner(
            db, 
            case_id, 
            owner_user_id
        )
        
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while retrieving cases.",
        ) from exc
        
        
def list_patient_cases(
    db:Session,
    patient_id:UUID,
    owner_user_id:UUID,
)-> list[Case]:
    
    try:
        validate_patient_access(
            db,
            patient_id,
            owner_user_id,
        )
        
        return get_cases_by_patient(
            db,
            patient_id,
            owner_user_id,
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while retrieving patient cases.",
        ) from exc
