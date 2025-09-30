# cleanup_orphans.py
import os
from sqlalchemy.orm import Session
from database import SessionLocal
from models import HeroBanner, Products # adjust import path to your actual models

def cleanup_orphans(model, image_field="image", image_dir="static/images"):
    db: Session = SessionLocal()

    try:
        # Get all image filenames in DB for the given model
        db_files = set()
        for obj in db.query(model).all():
            img = getattr(obj, image_field, None)
            if img:
                db_files.add(os.path.basename(img))

        # Get all files in static/images/
        if not os.path.exists(image_dir):
            print(f"{image_dir} does not exist")
            return

        all_files = set(os.listdir(image_dir))

        # Orphaned files = files on disk not in DB
        orphaned_files = all_files - db_files

        if not orphaned_files:
            print("✅ No orphaned images found.")
            return

        # Delete orphaned files
        for filename in orphaned_files:
            file_path = os.path.join(image_dir, filename)
            os.remove(file_path)
            print(f"🗑️ Deleted orphaned file: {file_path}")

        print("✅ Cleanup complete.")

    finally:
        db.close()

    if __name__ == "__main__":
    cleanup_orphans(Product)

        # or be specific and write
#         cleanup_orphans(Product, image_dir="static/images/products")
# cleanup_orphans(HeroBanner, image_dir="static/images/banners")