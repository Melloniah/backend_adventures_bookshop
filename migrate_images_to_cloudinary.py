import os
from sqlalchemy.orm import Session
from database import engine, get_db
from models import Product, HeroBanner, Category
from utils.cloudinary_config import upload_image_to_cloudinary

def migrate_existing_images():
    db = next(get_db())
    
    print("🚀 Starting image migration to Cloudinary...")
    
    # Migrate Product images
    products = db.query(Product).filter(Product.image.isnot(None)).all()
    print(f"\n📦 Migrating {len(products)} product images...")
    
    for product in products:
        if not product.image:
            continue
            
        # Skip if already a Cloudinary URL
        if "cloudinary.com" in product.image:
            print(f"⏭️ Product '{product.name}' already migrated")
            continue
        
        # Handle both "/static/images/file.jpg" and just "file.jpg"
        if product.image.startswith("/static/images/"):
            filename = product.image.replace("/static/images/", "")
        elif product.image.startswith("static/images/"):
            filename = product.image.replace("static/images/", "")
        else:
            filename = product.image  # Just the filename
        
        local_path = f"static/images/{filename}"
        
        if os.path.exists(local_path):
            try:
                with open(local_path, "rb") as f:
                    file_content = f.read()
                
                cloudinary_url = upload_image_to_cloudinary(
                    file_content,
                    filename,
                    folder="ecommerce/products"
                )
                
                product.image = cloudinary_url
                print(f"✅ Migrated product '{product.name}': {cloudinary_url}")
            except Exception as e:
                print(f"❌ Failed to migrate product '{product.name}': {str(e)}")
        else:
            print(f"⚠️ File not found for product '{product.name}': {local_path}")
    
    # Migrate Banner images
    banners = db.query(HeroBanner).all()
    print(f"\n🎨 Migrating {len(banners)} banner images...")
    
    for banner in banners:
        if not banner.image:
            continue
            
        # Skip if already a Cloudinary URL
        if "cloudinary.com" in banner.image:
            print(f"⏭️ Banner '{banner.title}' already migrated")
            continue
        
        # Handle both "/static/images/file.jpg" and just "file.jpg"
        if banner.image.startswith("/static/images/"):
            filename = banner.image.replace("/static/images/", "")
        elif banner.image.startswith("static/images/"):
            filename = banner.image.replace("static/images/", "")
        else:
            filename = banner.image
        
        local_path = f"static/images/{filename}"
        
        if os.path.exists(local_path):
            try:
                with open(local_path, "rb") as f:
                    file_content = f.read()
                
                cloudinary_url = upload_image_to_cloudinary(
                    file_content,
                    filename,
                    folder="ecommerce/banners"
                )
                
                banner.image = cloudinary_url
                print(f"✅ Migrated banner '{banner.title}': {cloudinary_url}")
            except Exception as e:
                print(f"❌ Failed to migrate banner '{banner.title}': {str(e)}")
        else:
            print(f"⚠️ File not found for banner '{banner.title}': {local_path}")
    
    # Migrate Category images (if any)
    categories = db.query(Category).filter(Category.image.isnot(None)).all()
    print(f"\n📂 Migrating {len(categories)} category images...")
    
    for category in categories:
        if not category.image:
            continue
            
        # Skip if already a Cloudinary URL
        if "cloudinary.com" in category.image:
            print(f"⏭️ Category '{category.name}' already migrated")
            continue
        
        # Handle both "/static/images/file.jpg" and just "file.jpg"
        if category.image.startswith("/static/images/"):
            filename = category.image.replace("/static/images/", "")
        elif category.image.startswith("static/images/"):
            filename = category.image.replace("static/images/", "")
        else:
            filename = category.image
        
        local_path = f"static/images/{filename}"
        
        if os.path.exists(local_path):
            try:
                with open(local_path, "rb") as f:
                    file_content = f.read()
                
                cloudinary_url = upload_image_to_cloudinary(
                    file_content,
                    filename,
                    folder="ecommerce/categories"
                )
                
                category.image = cloudinary_url
                print(f"✅ Migrated category '{category.name}': {cloudinary_url}")
            except Exception as e:
                print(f"❌ Failed to migrate category '{category.name}': {str(e)}")
        else:
            print(f"⚠️ File not found for category '{category.name}': {local_path}")
    
    db.commit()
    print("\n✨ Migration complete!")
    print("⚠️ IMPORTANT: Backup your database before deleting static/images folder")

if __name__ == "__main__":
    migrate_existing_images()