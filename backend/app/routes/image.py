from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.controllers.image_controller import upload_case_image_controller

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.models.case import Case
from app.models.image import Image
from app.repositories.image_repository import get_image_by_id
from app.schemas.image_preprocessing import ImagePreprocessingResponse
from app.services.audit_service import record_audit_event
from app.services.image_preprocessing_report import build_image_preprocessing_report
from app.services.image_service import UPLOAD_DIR
from app.services.image_storage import resolve_upload_path

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["Images"],
)


@router.get("/{case_id}/images")
def list_case_images(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.query(Case).filter(Case.id == case_id, Case.owner_user_id == current_user.id).first()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    images = db.query(Image).filter(Image.case_id == case_id).order_by(Image.created_at.desc()).all()
    return [{"id": str(item.id), "case_id": str(item.case_id), "original_filename": item.original_filename, "content_type": item.content_type, "file_size": item.file_size, "width": item.width, "height": item.height, "sha256": item.sha256, "created_at": item.created_at} for item in images]

@router.post(
    "/{case_id}/images",
    status_code=status.HTTP_201_CREATED
)
def upload_image_endpoint(
    case_id:UUID,
    request: Request,
    file:UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User= Depends(get_current_user),
):
    image  = upload_case_image_controller(
        db=db,
        case_id=case_id,
        file=file,
        current_user=current_user,
    )
    record_audit_event(db, "image_upload", "success", current_user.id, "image", str(image.id), request.client.host if request.client else None)
    
    return{
        "id": str(image.id),
        "case_id": str(image.case_id),
        "original_filename": image.original_filename,
        "content_type": image.content_type,
        "file_size": image.file_size,
        "width": image.width,
        "height": image.height,
        "sha256": image.sha256,
        "created_at": image.created_at,
    }


@router.get("/{case_id}/images/{image_id}/file")
def get_case_image_file(
    case_id: UUID,
    image_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.query(Case).filter(
        Case.id == case_id, Case.owner_user_id == current_user.id
    ).first()
    image = get_image_by_id(db, image_id)
    if case is None or image is None or image.case_id != case_id:
        raise HTTPException(status_code=404, detail="Image not found")
    path = resolve_upload_path(image.file_path, UPLOAD_DIR)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Image file not found")
    record_audit_event(db, "image_view", "success", current_user.id, "image", str(image.id), request.client.host if request.client else None)
    return FileResponse(path, media_type=image.content_type, filename=f"{image.id}{path.suffix}")


@router.post(
    "/{case_id}/images/{image_id}/preprocessing",
    response_model=ImagePreprocessingResponse,
)
def get_case_image_preprocessing(
    case_id: UUID,
    image_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.owner_user_id == current_user.id,
    ).first()
    image = get_image_by_id(db, image_id)
    if case is None or image is None or image.case_id != case_id:
        raise HTTPException(status_code=404, detail="Image not found")

    path = resolve_upload_path(image.file_path, UPLOAD_DIR)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Image file not found")

    try:
        report = build_image_preprocessing_report(image, path)
    except (OSError, ValueError):
        raise HTTPException(
            status_code=422,
            detail="This image could not be preprocessed.",
        ) from None

    record_audit_event(
        db,
        "image_preprocessed",
        "success",
        current_user.id,
        "image",
        str(image.id),
        request.client.host if request.client else None,
    )
    return report
