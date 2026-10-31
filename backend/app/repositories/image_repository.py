from sqlalchemy.orm import Session

from uuid import UUID

from app.models.image import Image



def create_image(
    db: Session,
    image_data: dict,
) -> Image:
    new_image = Image(**image_data)
    
    try:
        db.add(new_image)
        db.flush()
        db.refresh(new_image)
        return new_image
    except Exception:
        db.rollback()
        raise


def get_image_by_id(db: Session, image_id: UUID) -> Image | None:
    return db.get(Image, image_id)
