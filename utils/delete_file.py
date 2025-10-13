import os
from utils.cloudinary_config import delete_image_from_cloudinary

IMAGE_DIR = "static/images"

def delete_file_if_exists(filename_or_url: str):
    '''
    Delete a file from either local storage or Cloudinary
    
    Args:
        filename_or_url: Can be either:
            - Full Cloudinary URL (https://res.cloudinary.com/...)
            - Relative path (/static/images/filename.jpg)
            - Just filename (filename.jpg)
    '''
    if not filename_or_url:
        return
    
    # Check if it's a Cloudinary URL
    if "cloudinary.com" in filename_or_url:
        delete_image_from_cloudinary(filename_or_url)
        return
    
    # Otherwise, treat as local file
    # Handle both "/static/images/file.jpg" and "file.jpg"
    if filename_or_url.startswith("/static/images/"):
        filename = filename_or_url.replace("/static/images/", "")
    elif filename_or_url.startswith("static/images/"):
        filename = filename_or_url.replace("static/images/", "")
    else:
        filename = filename_or_url
    
    path = os.path.join(IMAGE_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        print(f"🗑️ Deleted local image: {path}")