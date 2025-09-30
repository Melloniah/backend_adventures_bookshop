
import os
IMAGE_DIR = "static/images"

def delete_file_if_exists(filename: str):
    """Delete a file if it exists."""
    if not filename:
        return
    path = os.path.join(IMAGE_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        print(f"🗑️ Deleted old image: {path}")