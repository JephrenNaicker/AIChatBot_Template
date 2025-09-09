import os
import uuid
from datetime import datetime
import streamlit as st
from PIL import Image
import io


class ImageService:
    def __init__(self, upload_dir="avatars", max_size_mb=5, allowed_types=["png", "jpg", "jpeg"]):
        self.upload_dir = upload_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.allowed_types = allowed_types
        self._ensure_upload_dir()

    def _ensure_upload_dir(self):
        """Create upload directory if it doesn't exist"""
        os.makedirs(self.upload_dir, exist_ok=True)

    def is_valid_image(self, uploaded_file):
        """Check if uploaded file is a valid image"""
        if uploaded_file is None:
            return False

        # Check file size
        if uploaded_file.size > self.max_size_bytes:
            st.error(f"File too large. Maximum size is {self.max_size_bytes // (1024 * 1024)}MB")
            return False

        # Check file type
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension not in self.allowed_types:
            st.error(f"Invalid file type. Allowed types: {', '.join(self.allowed_types)}")
            return False

        # Verify it's actually an image
        try:
            image = Image.open(io.BytesIO(uploaded_file.getvalue()))
            image.verify()  # Verify that it is, in fact, an image
            return True
        except Exception:
            st.error("Invalid image file")
            return False

    def generate_unique_filename(self, original_filename, bot_name):
        """Generate a unique filename for the uploaded image"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_extension = original_filename.split('.')[-1].lower()
        safe_bot_name = "".join(c for c in bot_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_bot_name = safe_bot_name.replace(' ', '_')[:30]

        return f"{safe_bot_name}_{timestamp}_{unique_id}.{file_extension}"

    def save_uploaded_file(self, uploaded_file, bot_name):
        """Save uploaded file to disk and return file info"""
        if not self.is_valid_image(uploaded_file):
            return None

        try:
            # Generate unique filename
            filename = self.generate_unique_filename(uploaded_file.name, bot_name)
            filepath = os.path.join(self.upload_dir, filename)

            # Read and process the image
            image = Image.open(io.BytesIO(uploaded_file.getvalue()))

            # Resize image if too large (max 400x400)
            if image.width > 400 or image.height > 400:
                image.thumbnail((400, 400), Image.Resampling.LANCZOS)

            # Convert to RGB if necessary (for JPEG compatibility)
            if image.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            # Save the image
            image.save(filepath, 'JPEG', quality=85)

            # Get file size after processing
            file_size = os.path.getsize(filepath)

            return {
                "filename": filename,
                "original_name": uploaded_file.name,
                "filepath": filepath,
                "content_type": "image/jpeg",
                "size": file_size,
                "dimensions": image.size,
                "saved_at": datetime.now().isoformat()
            }

        except Exception as e:
            st.error(f"Error saving image: {str(e)}")
            return None

    def get_image_url(self, file_info):
        """Get the URL or path for the saved image"""
        if file_info and "filepath" in file_info:
            return file_info["filepath"]
        return None

    def delete_image(self, file_info):
        """Delete an uploaded image file"""
        if file_info and "filepath" in file_info and os.path.exists(file_info["filepath"]):
            try:
                os.remove(file_info["filepath"])
                return True
            except Exception as e:
                st.error(f"Error deleting image: {str(e)}")
                return False
        return False

    def get_image_preview(self, file_info, width=100):
        """Get image preview for display"""
        if file_info and "filepath" in file_info and os.path.exists(file_info["filepath"]):
            try:
                image = Image.open(file_info["filepath"])
                return image
            except Exception as e:
                st.error(f"Error loading image preview: {str(e)}")
        return None