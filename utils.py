import os
from PIL import Image
import magic
from functools import wraps
from flask import current_app
from werkzeug.utils import secure_filename
import time
from contextlib import contextmanager
from . import db

@contextmanager
def transaction():
    """Context manager for database transactions"""
    try:
        yield
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Transaction error: {str(e)}")
        raise
    finally:
        db.session.close()

def save_poster(file):
    """Save and process show poster"""
    try:
        # Check actual file type
        file_content = file.read(2048)
        file.seek(0)  # Reset file pointer
        mime = magic.from_buffer(file_content, mime=True)
        if mime not in ['image/jpeg', 'image/png']:
            raise ValueError('Invalid file type. Only JPEG and PNG are allowed.')
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        base, ext = os.path.splitext(filename)
        filename = f"{base}_{int(time.time())}{ext}"
        
        # Process and save image
        img = Image.open(file)
        
        # Convert RGBA to RGB if necessary
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Resize image while maintaining aspect ratio
        max_size = (800, 800)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Prepare file path
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        # Save optimized image
        img.save(file_path, optimize=True, quality=85)
        
        # Return relative path for database
        return os.path.join('posters', filename).replace('\\', '/')
    
    except Exception as e:
        current_app.logger.error(f"Error processing image: {str(e)}")
        raise ValueError(f"Error processing image: {str(e)}")

def delete_poster(poster_path):
    """Safely delete a poster file"""
    if not poster_path:
        return
    
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                os.path.basename(poster_path))
        if os.path.exists(file_path):
            os.remove(file_path)
            current_app.logger.info(f"Deleted poster: {file_path}")
    except Exception as e:
        current_app.logger.error(f"Error deleting poster: {str(e)}")
        # Don't raise the error as this is not critical
