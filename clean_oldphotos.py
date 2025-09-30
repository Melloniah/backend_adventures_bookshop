# cleanup_orphans.py
import os
from sqlalchemy.orm import Session
from database import SessionLocal
from models import HeroBanner  # adjust import path to your actual models

# Folder where banner images are stored
IMAGE_DIR = "static/images"

def cleanup_orphans():
    db: Session = SessionLocal()

    try:
        # Get all banner image filenames in DB
        db_files = set()
        for banner in db.query(HeroBanner).all():
            if banner.image:
                db_files.add(os.path.basename(banner.image))

        # Get all files in static/images/
        if not os.path.exists(IMAGE_DIR):
            print(f"{IMAGE_DIR} does not exist")
            return

        all_files = set(os.listdir(IMAGE_DIR))

        # Find orphaned files
        orphaned_files = all_files - db_files

        if not orphaned_files:
            print("✅ No orphaned images found.")
            return

        # Delete orphaned files
        for filename in orphaned_files:
            file_path = os.path.join(IMAGE_DIR, filename)
            os.remove(file_path)
            print(f"🗑️ Deleted orphaned file: {file_path}")

        print("✅ Cleanup complete.")

    finally:
        db.close()

if __name__ == "__main__":
    cleanup_orphans()
