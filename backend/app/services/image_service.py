import uuid
import hashlib
from io import BytesIO
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from PIL import Image as PILImage, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session


from app.models.case import Case, CaseEvent
from app.models.image import Image
from app.repositories.image_repository import create_image
from app.core.config import settings
from app.services.case_service import transition_case_status
from app.services.image_cleanup import cleanup_uploaded_file


#upload configuration

MAX_FILE_SIZE = settings.MAX_UPLOAD_BYTES
MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS
ALLOWED_FORMATS = {
    "JPEG" : "image/jpeg",
    "PNG" : "image/png",
}

#backend/uploads/

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"


def upload_case_image(
    db:Session,
    case_id: UUID,
    owner_user_id: UUID,
    file: UploadFile,
) -> Image:
    
    file_path: Path | None = None
    
    try:
        
        case = (
            db.query(Case)
            .filter(
                Case.id == case_id,
                Case.owner_user_id == owner_user_id,
            )
            .first()
        )
        
        if case is None :
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found",
            )
            
        if file.content_type not in ALLOWED_FORMATS.values():
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Only JPEG and PNG images are allowed",
            )
        
        try:
            content = file.file.read(MAX_FILE_SIZE +1)
        except Exception :
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to read uploaded file",
            ) from None
            
            
        if not content:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )
             
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail=f"Maximum image size is {MAX_FILE_SIZE // (1024 * 1024)} MB",
            )
            
        try:
            with PILImage.open(BytesIO(content)) as image:
                actual_format = image.format
                width, height = image.size
                if actual_format not in ALLOWED_FORMATS:
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail="Only JPEG and PNG images are allowed",
                    )
                    
                if width <= 0 or height <= 0:
                     raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid image dimensions",
                    )

                if min(width, height) < settings.MIN_IMAGE_SIDE:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Image sides must be at least {settings.MIN_IMAGE_SIDE} pixels",
                    )
                     
                if width * height > MAX_IMAGE_PIXELS:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail="Image dimensions are too large",
                    )
                image.verify()

            with PILImage.open(BytesIO(content)) as image:
                oriented = ImageOps.exif_transpose(image)
                width, height = oriented.size
            if min(width, height) < settings.MIN_IMAGE_SIDE:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Image sides must be at least {settings.MIN_IMAGE_SIDE} pixels",
                )
            
        except HTTPException:
            raise
        except (
            UnidentifiedImageError,
            OSError,
            SyntaxError,
            ValueError,
            PILImage.DecompressionBombError,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or corrupted image",
            ) from None
        
        expected_type = ALLOWED_FORMATS[actual_format]
        
        
        if file.content_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="File content does not match its declared content type",
            )
            
        # Re-encode after orientation correction. This strips GPS and other
        # source EXIF metadata from the stored image.
        sanitized = BytesIO()
        with PILImage.open(BytesIO(content)) as source:
            oriented = ImageOps.exif_transpose(source).convert("RGB")
            if actual_format == "JPEG":
                oriented.save(sanitized, format="JPEG", quality=95, optimize=True, exif=b"")
            else:
                oriented.save(sanitized, format="PNG", optimize=True)
        stored_content = sanitized.getvalue()
        digest = hashlib.sha256(stored_content).hexdigest()

        extension = ".jpg" if actual_format == "JPEG" else ".png"
        safe_filename = f"{uuid.uuid4().hex}{extension}"
        
        
        case_dir = UPLOAD_DIR/str(case_id)
        file_path = case_dir/ safe_filename
        
        case_dir.mkdir(parents=True, exist_ok=True)
        
        with file_path.open("xb") as destination:
            destination.write(stored_content)
            
        image_data = {
            "case_id": case_id,
            "file_path": str(file_path.resolve()),
            "original_filename": "upload",
            "content_type": expected_type,
            "file_size": len(stored_content),
            "width": width,
            "height": height,
            "sha256": digest,
        }

        # Keep the image row, case status, and event in one DB transaction.
        # The filesystem write is compensated below if this transaction fails.
        stored_image = create_image(db, image_data)
        transition_case_status(
            db, case, "image_uploaded", owner_user_id, record_same_status=True
        )
        db.commit()
        return stored_image
    
    except Exception:
        db.rollback()
        
        if file_path is not None:
            cleanup_uploaded_file(file_path)
            
        raise
    
    finally:
        file.file.close()
        
        

