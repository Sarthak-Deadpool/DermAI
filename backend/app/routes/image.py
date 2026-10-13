from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.controllers.image_controller import upload_case_image_controller

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.image import Image
from app.models.user import User

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["Images"],
)

@router.post(
    "/{case_id}/images",
    status_code=status.HTTP_201_CREATED
)
def upload_image_endpoint(
    case_id:UUID,
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
    
    return{
        "id": str(image.id),
        "case_id": str(image.case_id),
        "original_filename": image.original_filename,
        "content_type": image.content_type,
        "file_size": image.file_size,
        "created_at": image.created_at,
    }