"""Storage service for file uploads."""
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_IMAGE_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})


def upload_image(file, folder: str = 'uploads') -> str:
    """
    Upload an image file.

    Uses Cloudinary if configured, otherwise falls back to local storage.

    Args:
        file: FileStorage object from request.files
        folder: Folder/path prefix for the upload

    Returns:
        URL of the uploaded image
    """
    if not file or not file.filename:
        raise ValueError("No file provided")

    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")

    cloudinary_url = current_app.config.get('CLOUDINARY_URL')

    if cloudinary_url:
        return upload_to_cloudinary(file, folder)
    else:
        return upload_to_local(file, folder)


def upload_to_cloudinary(file, folder: str) -> str:
    """Upload file to Cloudinary."""
    try:
        import cloudinary
        import cloudinary.uploader

        # Cloudinary is auto-configured from CLOUDINARY_URL env var
        result = cloudinary.uploader.upload(
            file,
            folder=f"solio/{folder}",
            resource_type="image",
            allowed_formats=['png', 'jpg', 'jpeg', 'gif', 'webp'],
            transformation=[
                {'width': 1200, 'height': 1200, 'crop': 'limit'},
                {'quality': 'auto'},
                {'fetch_format': 'auto'}
            ]
        )

        return result['secure_url']

    except ImportError:
        current_app.logger.error("Cloudinary library not installed")
        raise ValueError("Cloud storage not configured")
    except Exception as e:
        current_app.logger.error(f"Cloudinary upload error: {e}")
        raise ValueError(f"Upload failed: {str(e)}")


def upload_to_local(file, folder: str) -> str:
    """Upload file to local storage (development fallback)."""
    # Create upload directory
    upload_dir = os.path.join(
        current_app.root_path,
        'static',
        'uploads',
        folder
    )
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    unique_filename = f"{uuid.uuid4().hex}{ext}"

    # Save file
    filepath = os.path.join(upload_dir, unique_filename)
    file.save(filepath)

    # Return URL
    return f"/static/uploads/{folder}/{unique_filename}"


def delete_image(url: str) -> bool:
    """
    Delete an image by URL.

    Returns True if successful.
    """
    cloudinary_url = current_app.config.get('CLOUDINARY_URL')

    if cloudinary_url and 'cloudinary' in url:
        return delete_from_cloudinary(url)
    else:
        return delete_from_local(url)


def delete_from_cloudinary(url: str) -> bool:
    """Delete file from Cloudinary."""
    try:
        import cloudinary
        import cloudinary.uploader

        # Extract public_id from URL
        # URL format: https://res.cloudinary.com/xxx/image/upload/v123/folder/filename.ext
        parts = url.split('/')
        # Find the upload part and get everything after
        try:
            upload_idx = parts.index('upload')
            # Skip version number (v123)
            public_id_parts = parts[upload_idx + 2:]  # Skip 'upload' and version
            public_id = '/'.join(public_id_parts)
            # Remove file extension
            public_id = os.path.splitext(public_id)[0]

            result = cloudinary.uploader.destroy(public_id)
            return result.get('result') == 'ok'
        except (ValueError, IndexError):
            return False

    except ImportError:
        return False
    except Exception as e:
        current_app.logger.error(f"Cloudinary delete error: {e}")
        return False


def delete_from_local(url: str) -> bool:
    """Delete file from local storage."""
    try:
        # URL format: /static/uploads/folder/filename
        if url.startswith('/static/uploads/'):
            filepath = os.path.join(
                current_app.root_path,
                url.lstrip('/')
            )
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        return False
    except Exception as e:
        current_app.logger.error(f"Local delete error: {e}")
        return False
