import os
import logging
from PIL import Image, ImageFilter, ImageEnhance
import random

logger = logging.getLogger(__name__)

class SimpleImageProcessor:
    """Simple image processor for testing"""
    
    def __init__(self):
        os.makedirs("processed", exist_ok=True)
        logger.info("SimpleImageProcessor initialized")
    
    def _get_output_path(self, input_path: str, suffix: str, extension: str = None) -> str:
        """Generate output path for processed images"""
        base_name = os.path.basename(input_path)
        name, orig_ext = os.path.splitext(base_name)
        
        if extension:
            new_ext = f".{extension}"
        else:
            new_ext = orig_ext
            
        output_filename = f"{name}_{suffix}{new_ext}"
        return os.path.join("processed", output_filename)
    
    def resize_image(self, image_path: str, width: int, height: int) -> str:
        """Resize image"""
        try:
            logger.info(f"Resizing image to {width}x{height}")
            with Image.open(image_path) as img:
                # Maintain aspect ratio
                original_width, original_height = img.size
                ratio = min(width/original_width, height/original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                
                resized = img.resize((new_width, new_height), Image.LANCZOS)
                output_path = self._get_output_path(image_path, f"resized_{new_width}x{new_height}")
                resized.save(output_path, quality=85)
                logger.info(f"Resized image saved to {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Resize error: {e}")
            raise
    
    def smart_crop(self, image_path: str, mode: str) -> str:
        """Crop image based on mode"""
        try:
            logger.info(f"Cropping image with mode: {mode}")
            with Image.open(image_path) as img:
                width, height = img.size
                
                if mode == "smart":
                    # Center crop for smart mode
                    size = min(width, height)
                    left = (width - size) // 2
                    top = (height - size) // 2
                elif mode == "square":
                    size = min(width, height)
                    left = (width - size) // 2
                    top = (height - size) // 2
                elif mode == "portrait":
                    # 9:16 ratio
                    new_height = min(height, int(width * 16/9))
                    new_width = int(new_height * 9/16)
                    left = (width - new_width) // 2
                    top = (height - new_height) // 2
                    size = new_width
                elif mode == "landscape":
                    # 16:9 ratio
                    new_width = min(width, int(height * 16/9))
                    new_height = int(new_width * 9/16)
                    left = (width - new_width) // 2
                    top = (height - new_height) // 2
                    size = new_width
                else:
                    # Default to square
                    size = min(width, height)
                    left = (width - size) // 2
                    top = (height - size) // 2
                
                if mode in ["portrait", "landscape"]:
                    cropped = img.crop((left, top, left + new_width, top + new_height))
                else:
                    cropped = img.crop((left, top, left + size, top + size))
                
                output_path = self._get_output_path(image_path, f"cropped_{mode}")
                cropped.save(output_path, quality=85)
                logger.info(f"Cropped image saved to {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Crop error: {e}")
            raise
    
    def remove_background(self, image_path: str) -> str:
        """Remove background (mock implementation)"""
        try:
            logger.info("Removing background")
            with Image.open(image_path) as img:
                # Simple mock - just return a slightly modified version
                if img.mode == 'RGBA':
                    # Create a simple transparent background effect
                    output_path = self._get_output_path(image_path, "no_bg", "png")
                    img.save(output_path)
                else:
                    # Convert to RGBA and add some transparency
                    rgba_img = img.convert('RGBA')
                    output_path = self._get_output_path(image_path, "no_bg", "png")
                    rgba_img.save(output_path)
                
                logger.info(f"Background removed image saved to {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Remove background error: {e}")
            raise
    
    def generate_background(self, image_path: str) -> str:
        """Generate new background (mock implementation)"""
        try:
            logger.info("Generating new background")
            with Image.open(image_path) as img:
                # Create a simple gradient background
                width, height = img.size
                background = Image.new('RGB', (width, height), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
                
                output_path = self._get_output_path(image_path, "new_bg")
                background.save(output_path, quality=85)
                logger.info(f"New background image saved to {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Generate background error: {e}")
            raise
    
    def enhance_quality(self, image_path: str) -> str:
        """Enhance image quality"""
        try:
            logger.info("Enhancing image quality")
            with Image.open(image_path) as img:
                # Enhance contrast
                enhancer = ImageEnhance.Contrast(img)
                enhanced = enhancer.enhance(1.2)
                
                # Enhance sharpness
                enhancer = ImageEnhance.Sharpness(enhanced)
                enhanced = enhancer.enhance(1.3)
                
                # Enhance color
                enhancer = ImageEnhance.Color(enhanced)
                enhanced = enhancer.enhance(1.1)
                
                output_path = self._get_output_path(image_path, "enhanced")
                enhanced.save(output_path, quality=90)
                logger.info(f"Enhanced image saved to {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Enhance quality error: {e}")
            raise
    
    def convert_format(self, image_path: str, format: str) -> str:
        """Convert image format"""
        try:
            logger.info(f"Converting image to {format}")
            with Image.open(image_path) as img:
                output_path = self._get_output_path(image_path, f"converted", format)
                
                if format.lower() == 'jpeg' or format.lower() == 'jpg':
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    img.save(output_path, 'JPEG', quality=85)
                elif format.lower() == 'png':
                    img.save(output_path, 'PNG')
                elif format.lower() == 'webp':
                    img.save(output_path, 'WEBP', quality=85)
                else:
                    img.save(output_path, quality=85)
                
                logger.info(f"Converted image saved to {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Convert format error: {e}")
            raise
