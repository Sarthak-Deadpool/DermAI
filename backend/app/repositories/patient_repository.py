from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.patient import Patient


class PatientRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_patient(self, patient: Patient) -> Patient:
        try:
            self.db.add(patient)
            self.db.commit()
            self.db.refresh(patient)
            return patient
        except Exception:
            self.db.rollback()
            raise

    def get_patient_by_id(self, patient_id: UUID) -> Patient | None:
        return self.db.query(Patient).filter(
            Patient.id == patient_id, Patient.archived_at.is_(None)
        ).first()

    def get_patient_by_clinician(
        self, clinician_id: UUID, offset: int = 0, limit: int = 20, search: str | None = None
    ) -> list[Patient]:
        query = self.db.query(Patient).filter(
            Patient.clinician_id == clinician_id, Patient.archived_at.is_(None)
        )
        if search:
            query = query.filter(Patient.patient_code.ilike(f"%{search}%"))
        return query.order_by(Patient.created_at.desc()).offset(offset).limit(limit).all()

    def update_patient(self, patient: Patient) -> Patient:
        try:
            self.db.commit()
            self.db.refresh(patient)
            return patient
        except Exception:
            self.db.rollback()
            raise

    def delete_patient(self, patient: Patient) -> None:
        try:
            patient.archived_at = datetime.now(timezone.utc)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def get_patient_by_user(self, user_id: UUID, include_archived: bool = False) -> Patient | None:
        query = self.db.query(Patient).filter(Patient.user_id == user_id)
        if not include_archived:
            query = query.filter(Patient.archived_at.is_(None))
        return query.first()
