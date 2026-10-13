from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.image import Image
from app.models.user import User
from app.services.image_service import upload_case_image

def upload_case_image_controller(
    db:Session,
    case_id: UUID,
    file: UploadFile,
    current_user: User,
) -> Image:
    return upload_case_image(
        db=db,
        case_id=case_id,
        owner_user_id=current_user.id,
        file=file
    )