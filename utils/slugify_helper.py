# utils.py (or wherever you keep helpers)
from sqlalchemy.orm import Session
from models import Category
from slugify import slugify

def generate_unique_slug(name: str, db: Session) -> str:
    base_slug = slugify(name)
    slug = base_slug
    count = 1
    while db.query(Category).filter(Category.slug == slug).first():
        slug = f"{base_slug}-{count}"
        count += 1
    return slug
