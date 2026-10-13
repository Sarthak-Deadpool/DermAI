from sqlalchemy.orm import Session

from app.models.image import Image



def create_image(
    db: Session,
    image_data: dict,
) -> Image:
    new_image = Image(**image_data)
    
    try:
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        return new_image
    except Exception:
        db.rollback()
        raise