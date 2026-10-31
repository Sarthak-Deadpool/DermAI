from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session


from app.controllers.case_controller import (
    create_case_controller,
    get_case_controller,
    list_cases_controller,
    list_patient_cases_controller,
)

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User, UserRole
from app.models.case import Case, CaseNote, CaseEvent
from app.dependencies.authorization import require_roles
from app.schemas.case import CaseCreate, CaseResponse, CaseNoteCreate, CaseNoteResponse, CaseStatusUpdate, CaseEventResponse
from app.services.case_service import transition_case_status
from app.services.audit_service import record_audit_event


router = APIRouter(prefix="/api/v1/cases", tags=["Cases"])


@router.post(
    "",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_case_route(
    case_data :CaseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = create_case_controller(db, case_data, current_user)
    record_audit_event(db, "case_created", "success", current_user.id, "case", str(case.id), request.client.host if request.client else None)
    return case


@router.get(
    "",
    response_model=list[CaseResponse],
)
def list_cases_route(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_cases_controller(db, current_user, offset, limit, status_filter)


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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = get_case_controller(db, case_id, current_user)
    record_audit_event(db, "case_viewed", "success", current_user.id, "case", str(case.id), request.client.host if request.client else None)
    return case


@router.patch("/{case_id}/status", response_model=CaseResponse)
def update_case_status(
    case_id: UUID,
    payload: CaseStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.query(Case).filter(Case.id == case_id, Case.owner_user_id == current_user.id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    try:
        transition_case_status(db, case, payload.status, current_user.id)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(case)
    record_audit_event(db, "case_status_updated", "success", current_user.id, "case", str(case.id), request.client.host if request.client else None)
    return case


@router.post("/{case_id}/notes", response_model=CaseNoteResponse, status_code=status.HTTP_201_CREATED)
def add_case_note(
    case_id: UUID,
    payload: CaseNoteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.CLINICIAN, UserRole.ADMIN)),
):
    case = db.query(Case).filter(Case.id == case_id, Case.owner_user_id == current_user.id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    note = CaseNote(case_id=case_id, author_user_id=current_user.id, note=payload.note.strip())
    db.add(note)
    db.add(CaseEvent(case_id=case_id, actor_user_id=current_user.id, event_type="note_added"))
    db.commit(); db.refresh(note)
    record_audit_event(db, "case_note_added", "success", current_user.id, "case", str(case_id), request.client.host if request.client else None)
    return note


@router.get("/{case_id}/notes", response_model=list[CaseNoteResponse])
def list_case_notes(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.query(Case).filter(Case.id == case_id, Case.owner_user_id == current_user.id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return db.query(CaseNote).filter(CaseNote.case_id == case_id).order_by(CaseNote.created_at.asc()).all()


@router.get("/{case_id}/events", response_model=list[CaseEventResponse])
def list_case_events(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.query(Case).filter(Case.id == case_id, Case.owner_user_id == current_user.id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return db.query(CaseEvent).filter(CaseEvent.case_id == case_id).order_by(CaseEvent.created_at.asc()).all()
