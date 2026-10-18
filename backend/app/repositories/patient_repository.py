from uuid import UUID


from sqlalchemy.orm import Session

from app.models.patient import Patient

class PatientRepository:
    
    def __init__(self, db:Session):
        self.db = db
        
        
    def create_patient(self, patient:Patient) -> Patient:
        try:
            self.db.add(patient)
            self.db.commit()
            self.db.refresh(patient)
            return patient
        except Exception:
            self.db.rollback()
            raise
    
    def get_patient_by_id(self, patient_id:UUID) -> Patient | None:
        
        return(
            self.db.query(Patient)
            .filter(Patient.id == patient_id)
            .first()
        )
        
    def get_patient_by_clinician(self, clinician_id:UUID) -> list[Patient]:
        
        return(
            self.db.query(Patient)
            .filter(Patient.clinician_id == clinician_id)
            .order_by(Patient.created_at.desc())
            .all()
        )
        
    def update_patient(self, patient:Patient) -> Patient:
        try:
            self.db.commit()
            self.db.refresh(patient)
            return patient
        except Exception:
            self.db.rollback()
            raise
    
    def delete_patient(self, patient:Patient) -> None:
        try:
            self.db.delete(patient)
            self.db.commit()
        except:
            self.db.rollback()
            raise
        
    def get_patient_by_user(self, user_id: UUID) -> Patient | None:
        try:
            return(
                self.db.query(Patient)
                .filter(Patient.user_id == user_id)
                .first()
            )
        except:
            self.db.rollback()
            raise