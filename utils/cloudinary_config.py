import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def upload_image_to_cloudinary(file_content: bytes, filename: str, folder: str = "ecommerce") -> str:
    try:
        # Generate unique public_id - DON'T include folder in public_id
        base_name = os.path.splitext(filename)[0]
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file_content,
            public_id=base_name,  # Just the filename, no folder here
            overwrite=True,
            resource_type="image",
            folder=folder  # Folder is handled separately
        )
        
        return result['secure_url']
    except Exception as e:
        raise Exception(f"Cloudinary upload failed: {str(e)}")

def delete_image_from_cloudinary(image_url: str) -> bool:
    """
    Delete image from Cloudinary using its URL
    
    Args:
        image_url: Full Cloudinary URL
    
    Returns:
        True if deleted successfully
    """
    if not image_url or "cloudinary.com" not in image_url:
        return False
    
    try:
        # Extract public_id from URL
        # Example: https://res.cloudinary.com/demo/image/upload/v1234/ecommerce/image.jpg
        # Extract: ecommerce/image
        parts = image_url.split('/upload/')
        if len(parts) < 2:
            return False
        
        path = parts[1].split('/')[1:]  # Skip version number
        public_id = '/'.join(path).rsplit('.', 1)[0]  # Remove extension
        
        # Delete from Cloudinary
        result = cloudinary.uploader.destroy(public_id)
        print(f"🗑️ Deleted from Cloudinary: {public_id}")
        return result.get('result') == 'ok'
    except Exception as e:
        print(f"⚠️ Failed to delete from Cloudinary: {str(e)}")
        return False