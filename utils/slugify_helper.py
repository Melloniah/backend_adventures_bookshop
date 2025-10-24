from sqlalchemy.orm import Session
from models import Category
from slugify import slugify

def generate_unique_slug(name: str, db: Session, exclude_id: int | None = None) -> str:
    """Generate a unique slug for a category name.
    Optionally exclude a specific category ID (useful during updates).
    """
    base_slug = slugify(name)
    slug = base_slug
    count = 1

    while True:
        query = db.query(Category).filter(Category.slug == slug)
        if exclude_id:
            query = query.filter(Category.id != exclude_id)

        if not query.first():
            break

        slug = f"{base_slug}-{count}"
        count += 1

    return slug
