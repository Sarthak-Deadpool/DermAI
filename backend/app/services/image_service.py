import uuid
from io import BytesIO
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from PIL import Image as PILImage, UnidentifiedImageError
from sqlalchemy.orm import Session


from app.models.case import Case
from app.models.image import Image
from app.repositories.image_repository import create_image


#upload configuration

MAX_FILE_SIZE = 20*1024*1024
MAX_IMAGE_PIXELS = 25_000_000
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
                detail="Maximum image size is 20 MB",
            )
            
        try:
            with PILImage.open(BytesIO(content)) as image:
                actual_format = image.format
                width, height  =  image.size
                
                
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
                     
                if width * height > MAX_IMAGE_PIXELS:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail="Image dimensions are too large",
                    )
                    
                image.verify()
            
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
            
        extension = ".jpg" if actual_format == "JPEG" else ".png"
        safe_filename = f"{uuid.uuid4().hex}{extension}"
        
        
        case_dir = UPLOAD_DIR/str(case_id)
        file_path = case_dir/ safe_filename
        
        case_dir.mkdir(parents=True, exist_ok=True)
        
        with file_path.open("xb") as destination:
            destination.write(content)
            
        image_data = {
            "case_id": case_id,
            "file_path": str(file_path.resolve()),
            "original_filename": (file.filename or "upload")[:255],
            "content_type": expected_type,
            "file_size": len(content),
        }
        
        return create_image(db, image_data)
    
    except HTTPException:
        db.rollback()
        
        if file_path is not None:
            try:
                file_path.unlink(missing_ok=True)
            except OSError:
                pass
        
        raise
    
    except Exception:
        db.rollback()
        
        if file_path is not None:
            try:
                file_path.unlink(missing_ok=True)
            except OSError:
                pass
            
        raise
    
    finally:
        file.file.close()
        
        
   