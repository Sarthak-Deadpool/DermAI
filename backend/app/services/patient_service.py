from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


from app.models.patient import Patient
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import PatientCreate, PatientUpdate


def create_patient(
    db:Session,
    patient_data: PatientCreate,
    clinician_id:UUID,
) -> Patient:
    repository = PatientRepository(db)
    
    try:
        patient = Patient(
            patient_code=f"PAT-{uuid4().hex.upper()}",
            patient_name=patient_data.patient_name,
            age= patient_data.age,
            gender=patient_data.gender,
            medical_history=patient_data.medical_history,
            known_allergies=patient_data.known_allergies,
            fitzpatrick_type=patient_data.fitzpatrick_type,
            clinician_id=clinician_id,
            user_id = None,
    
        )
        
        return repository.create_patient(patient)
    
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create patient due to a database error.",
        ) from exc
        
def get_patient_by_id(
        db:Session,
        patient_id:UUID,
        clinician_id:UUID,
) -> Patient:
        repository = PatientRepository(db)
        
        try:
            patient = repository.get_patient_by_id(patient_id)
            
            if patient is None or patient.clinician_id != clinician_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Patient not found",
                )
            return patient
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not retrieve patient due to a database error"
            ) from exc
            
def get_patient_by_clinician(
    db:Session,
    clinician_id:UUID,
    offset: int = 0,
    limit: int = 20,
    search: str | None = None,
) -> list[Patient]:
    
    repository = PatientRepository(db)
    
    try:
        return repository.get_patient_by_clinician(clinician_id, offset, limit, search)
    
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve patients due to a database error.",
        ) from exc
        
        
def update_patient(
    db: Session,
    patient_id:UUID,
    clinician_id:UUID,
    patient_data: PatientUpdate,
) -> Patient:
    
    repository = PatientRepository(db)
    patient = get_patient_by_id(db, patient_id, clinician_id)
    
    updates = patient_data.model_dump(exclude_unset=True)
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update.",
        )
    
    if any(value is None for value in updates.values()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Patient fields cannot be null.",
        )
    try:
        for field, value in updates.items():
            setattr(patient, field, value)
            
        return repository.update_patient(patient)
    
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update patient due to a database error.",
        ) from exc
        
def delete_patient(
    db:Session,
    patient_id:UUID,
    clinician_id:UUID,
) -> None:
    repository = PatientRepository(db)
    
    patient = get_patient_by_id(db, patient_id, clinician_id)
    
    try:
        repository.delete_patient(patient)
        
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete patient due to a database error.",
        ) from exc
        
        
def get_patient_by_user(
    db:Session,
    user_id:UUID,
    
)-> Patient:
    repository = PatientRepository(db)
    
    try:
        patient =  repository.get_patient_by_user(user_id)
        
        if patient is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found.",
            )
        return patient
    
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve patient profile.",
        ) from exc
        
def create_user_patient(
    db:Session,
    patient_data: PatientCreate,
    user_id: UUID,
) -> Patient:
    repository = PatientRepository(db)
    try:
        existing_patient = repository.get_patient_by_user(user_id, include_archived=True)
        
        if existing_patient is not None and existing_patient.archived_at is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a patient profile.",
            )
            
        if existing_patient is not None:
            existing_patient.archived_at = None
            if patient_data.patient_name is not None:
                existing_patient.patient_name = patient_data.patient_name
            existing_patient.age = patient_data.age
            existing_patient.gender = patient_data.gender
            existing_patient.medical_history = patient_data.medical_history
            existing_patient.known_allergies = patient_data.known_allergies
            existing_patient.fitzpatrick_type = patient_data.fitzpatrick_type
            return repository.update_patient(existing_patient)

        patient  = Patient(
            patient_code=f"PAT-{uuid4().hex.upper()}",
            patient_name=patient_data.patient_name,
            age = patient_data.age,
            gender = patient_data.gender,
            medical_history=patient_data.medical_history,
            known_allergies=patient_data.known_allergies,
            fitzpatrick_type=patient_data.fitzpatrick_type,
            user_id = user_id,
            clinician_id = None,
        ) 
        
        return repository.create_patient(patient)
    
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create patient profile.",
        ) from exc
        
def update_user_patient(
    db:Session,
    user_id:UUID,
    patient_data: PatientUpdate,
)-> Patient:
    repository = PatientRepository(db)
    patient = get_patient_by_user(db, user_id)
    
    updates = patient_data.model_dump(exclude_unset=True)
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update.",
        )
        
    if any(value is None for value in updates.values()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Patient fields cannot be null.",
        )
        
    try:
        for field, value in updates.items():
            setattr(patient, field, value)
            
        return repository.update_patient(patient)
    
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update patient profile.",
        ) from exc
        
def delete_user_patient(
    db:Session,
    user_id:UUID,
    
)-> None:
    
    repository = PatientRepository(db)
    patient = get_patient_by_user(db, user_id)
    
    try:
        repository.delete_patient(patient)
        
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not delete patient profile.",
        ) from exc
