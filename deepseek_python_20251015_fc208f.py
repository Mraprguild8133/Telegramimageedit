import os
import logging
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import cv2
from io import BytesIO
import requests
import random
from rembg import remove as remove_bg
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        self.supported_formats = ['jpeg', 'jpg', 'png', 'webp']
        self.quality_presets = {
            'low': 65,
            'medium': 80,
            'high': 95,
            'maximum': 100
        }
        
        # Create output directory
        os.makedirs("processed", exist_ok=True)
        
    def _get_output_path(self, input_path: str, suffix: str = "processed", extension: str = None) -> str:
        """Generate output path for processed images"""
        base_name = os.path.basename(input_path)
        name, orig_ext = os.path.splitext(base_name)
        
        if extension:
            new_ext = f".{extension.lower()}"
        else:
            new_ext = orig_ext
            
        output_filename = f"{name}_{suffix}{new_ext}"
        return os.path.join("processed", output_filename)
    
    def _open_image(self, image_path: str) -> Image.Image:
        """Open image with proper error handling"""
        try:
            with Image.open(image_path) as img:
                return img.copy()
        except Exception as e:
            logger.error(f"Error opening image {image_path}: {e}")
            raise
    
    def _save_image(self, image: Image.Image, output_path: str, quality: int = 95) -> str:
        """Save image with optimized settings"""
        try:
            # Convert to RGB if saving as JPEG
            if output_path.lower().endswith(('.jpg', '.jpeg')):
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
            
            image.save(output_path, quality=quality, optimize=True)
            return output_path
        except Exception as e:
            logger.error(f"Error saving image {output_path}: {e}")
            raise
    
    def resize_image(self, image_path: str, width: int, height: int, maintain_aspect: bool = True) -> str:
        """
        Resize image to specified dimensions
        
        Args:
            image_path: Path to input image
            width: Target width
            height: Target height
            maintain_aspect: Whether to maintain aspect ratio
        
        Returns:
            Path to resized image
        """
        try:
            image = self._open_image(image_path)
            original_width, original_height = image.size
            
            if maintain_aspect:
                # Calculate aspect ratio
                original_ratio = original_width / original_height
                target_ratio = width / height
                
                if original_ratio > target_ratio:
                    # Image is wider than target
                    new_width = width
                    new_height = int(width / original_ratio)
                else:
                    # Image is taller than target
                    new_height = height
                    new_width = int(height * original_ratio)
            else:
                new_width, new_height = width, height
            
            # Resize image
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            output_path = self._get_output_path(image_path, f"resized_{new_width}x{new_height}")
            return self._save_image(resized_image, output_path)
            
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            raise
    
    def smart_crop(self, image_path: str, mode: str) -> str:
        """
        Crop image based on different modes
        
        Args:
            image_path: Path to input image
            mode: Crop mode ('smart', 'square', 'portrait', 'landscape')
        
        Returns:
            Path to cropped image
        """
        try:
            image = self._open_image(image_path)
            width, height = image.size
            
            if mode == 'smart':
                # Auto-detect main subject and crop around it
                return self._smart_crop_auto(image_path)
            elif mode == 'square':
                # Crop to square (1:1 ratio)
                size = min(width, height)
                left = (width - size) // 2
                top = (height - size) // 2
                right = left + size
                bottom = top + size
            elif mode == 'portrait':
                # Crop to portrait (9:16 ratio)
                target_ratio = 9/16
                if width/height > target_ratio:
                    # Image is wider than portrait
                    new_width = int(height * target_ratio)
                    left = (width - new_width) // 2
                    top = 0
                    right = left + new_width
                    bottom = height
                else:
                    # Image is taller than portrait
                    new_height = int(width / target_ratio)
                    left = 0
                    top = (height - new_height) // 2
                    right = width
                    bottom = top + new_height
            elif mode == 'landscape':
                # Crop to landscape (16:9 ratio)
                target_ratio = 16/9
                if width/height > target_ratio:
                    # Image is wider than landscape
                    new_width = int(height * target_ratio)
                    left = (width - new_width) // 2
                    top = 0
                    right = left + new_width
                    bottom = height
                else:
                    # Image is taller than landscape
                    new_height = int(width / target_ratio)
                    left = 0
                    top = (height - new_height) // 2
                    right = width
                    bottom = top + new_height
            else:
                raise ValueError(f"Unknown crop mode: {mode}")
            
            cropped_image = image.crop((left, top, right, bottom))
            output_path = self._get_output_path(image_path, f"cropped_{mode}")
            return self._save_image(cropped_image, output_path)
            
        except Exception as e:
            logger.error(f"Error cropping image: {e}")
            raise
    
    def _smart_crop_auto(self, image_path: str) -> str:
        """Auto-crop to main subject using edge detection"""
        try:
            # Use OpenCV for better edge detection
            image_cv = cv2.imread(image_path)
            gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                # Fallback to center crop if no contours found
                return self.smart_crop(image_path, 'square')
            
            # Find largest contour (main subject)
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # Add some padding
            padding = 20
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(image_cv.shape[1] - x, w + 2 * padding)
            h = min(image_cv.shape[0] - y, h + 2 * padding)
            
            # Crop using PIL
            image_pil = self._open_image(image_path)
            cropped_image = image_pil.crop((x, y, x + w, y + h))
            
            output_path = self._get_output_path(image_path, "cropped_smart")
            return self._save_image(cropped_image, output_path)
            
        except Exception as e:
            logger.error(f"Error in smart crop: {e}")
            # Fallback to square crop
            return self.smart_crop(image_path, 'square')
    
    def remove_background(self, image_path: str) -> str:
        """
        Remove background from image
        
        Args:
            image_path: Path to input image
        
        Returns:
            Path to image with transparent background
        """
        try:
            with open(image_path, 'rb') as input_file:
                input_data = input_file.read()
                
            # Remove background
            output_data = remove_bg(input_data)
            
            # Save as PNG to preserve transparency
            output_path = self._get_output_path(image_path, "no_bg", "png")
            
            with open(output_path, 'wb') as output_file:
                output_file.write(output_data)
                
            return output_path
            
        except Exception as e:
            logger.error(f"Error removing background: {e}")
            raise
    
    def generate_background(self, image_path: str, style: str = "gradient") -> str:
        """
        Generate new background for image
        
        Args:
            image_path: Path to input image
            style: Background style ('gradient', 'blur', 'color', 'pattern')
        
        Returns:
            Path to image with new background
        """
        try:
            # First remove the original background
            no_bg_path = self.remove_background(image_path)
            foreground = self._open_image(no_bg_path)
            
            # Create background
            bg_width, bg_height = foreground.size
            
            if style == "gradient":
                background = self._create_gradient_background(bg_width, bg_height)
            elif style == "blur":
                background = self._create_blur_background(image_path, bg_width, bg_height)
            elif style == "color":
                background = self._create_color_background(bg_width, bg_height)
            elif style == "pattern":
                background = self._create_pattern_background(bg_width, bg_height)
            else:
                background = self._create_gradient_background(bg_width, bg_height)
            
            # Composite foreground onto background
            if foreground.mode == 'RGBA':
                # Use alpha channel for transparency
                result = Image.alpha_composite(background.convert('RGBA'), foreground)
            else:
                result = background
                result.paste(foreground, (0, 0), foreground.convert('RGBA') if foreground.mode != 'RGBA' else foreground)
            
            output_path = self._get_output_path(image_path, f"new_bg_{style}")
            return self._save_image(result, output_path)
            
        except Exception as e:
            logger.error(f"Error generating background: {e}")
            raise
    
    def _create_gradient_background(self, width: int, height: int) -> Image.Image:
        """Create gradient background"""
        background = Image.new('RGB', (width, height))
        
        # Create gradient
        for y in range(height):
            # Calculate color based on position
            r = int(255 * y / height)
            g = int(128 * y / height)
            b = int(255 * (height - y) / height)
            
            # Draw horizontal line
            for x in range(width):
                background.putpixel((x, y), (r, g, b))
        
        return background
    
    def _create_blur_background(self, image_path: str, width: int, height: int) -> Image.Image:
        """Create blurred version of original image as background"""
        original = self._open_image(image_path)
        blurred = original.resize((width // 8, height // 8), Image.Resampling.LANCZOS)
        blurred = blurred.filter(ImageFilter.GaussianBlur(radius=10))
        blurred = blurred.resize((width, height), Image.Resampling.LANCZOS)
        return blurred
    
    def _create_color_background(self, width: int, height: int) -> Image.Image:
        """Create solid color background"""
        colors = [
            (255, 255, 255),  # White
            (0, 0, 0),        # Black
            (240, 248, 255),  # Alice Blue
            (255, 250, 240),  # Floral White
            (245, 245, 220),  # Beige
        ]
        return Image.new('RGB', (width, height), random.choice(colors))
    
    def _create_pattern_background(self, width: int, height: int) -> Image.Image:
        """Create patterned background"""
        background = Image.new('RGB', (width, height), (255, 255, 255))
        
        # Draw simple pattern
        for x in range(0, width, 40):
            for y in range(0, height, 40):
                color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
                for i in range(20):
                    for j in range(20):
                        if x + i < width and y + j < height:
                            background.putpixel((x + i, y + j), color)
        
        return background
    
    def enhance_quality(self, image_path: str) -> str:
        """
        Enhance image quality using various filters
        
        Args:
            image_path: Path to input image
        
        Returns:
            Path to enhanced image
        """
        try:
            image = self._open_image(image_path)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # Enhance brightness
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.1)
            
            # Enhance color saturation
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.2)
            
            # Apply slight sharpening filter
            image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
            
            output_path = self._get_output_path(image_path, "enhanced")
            return self._save_image(image, output_path, quality=95)
            
        except Exception as e:
            logger.error(f"Error enhancing image quality: {e}")
            raise
    
    def convert_format(self, image_path: str, target_format: str) -> str:
        """
        Convert image to different format
        
        Args:
            image_path: Path to input image
            target_format: Target format ('jpeg', 'png', 'webp')
        
        Returns:
            Path to converted image
        """
        try:
            if target_format.lower() not in self.supported_formats:
                raise ValueError(f"Unsupported format: {target_format}")
            
            image = self._open_image(image_path)
            output_path = self._get_output_path(image_path, f"converted", target_format.lower())
            
            # Set quality based on format
            quality = 95 if target_format.lower() in ['jpeg', 'jpg', 'webp'] else None
            
            if target_format.lower() == 'webp':
                return self._save_image(image, output_path, quality=quality)
            else:
                return self._save_image(image, output_path, quality=quality)
            
        except Exception as e:
            logger.error(f"Error converting image format: {e}")
            raise
    
    def get_image_info(self, image_path: str) -> dict:
        """
        Get information about the image
        
        Args:
            image_path: Path to input image
        
        Returns:
            Dictionary with image information
        """
        try:
            with Image.open(image_path) as img:
                info = {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height,
                    'aspect_ratio': round(img.width / img.height, 2)
                }
                return info
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return {}
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up processed files older than specified hours"""
        try:
            import time
            current_time = time.time()
            
            for filename in os.listdir("processed"):
                file_path = os.path.join("processed", filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_hours * 3600:  # Convert hours to seconds
                        os.remove(file_path)
                        logger.info(f"Removed old file: {filename}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")


# Alternative Simple Image Processor for testing
class SimpleImageProcessor:
    """Simple image processor for testing without external dependencies"""
    
    def __init__(self):
        os.makedirs("processed", exist_ok=True)
    
    def _get_output_path(self, input_path: str, suffix: str) -> str:
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        output_filename = f"{name}_{suffix}{ext}"
        return os.path.join("processed", output_filename)
    
    def resize_image(self, image_path: str, width: int, height: int) -> str:
        """Simple resize implementation"""
        try:
            with Image.open(image_path) as img:
                # Maintain aspect ratio
                original_width, original_height = img.size
                ratio = min(width/original_width, height/original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                
                resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                output_path = self._get_output_path(image_path, f"resized_{new_width}x{new_height}")
                resized.save(output_path, quality=85)
                return output_path
        except Exception as e:
            logger.error(f"Simple resize error: {e}")
            # Return original path as fallback
            return image_path
    
    def smart_crop(self, image_path: str, mode: str) -> str:
        """Simple crop implementation"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                if mode == 'square':
                    size = min(width, height)
                    left = (width - size) // 2
                    top = (height - size) // 2
                    cropped = img.crop((left, top, left + size, top + size))
                else:
                    # For other modes, return center square crop
                    size = min(width, height)
                    left = (width - size) // 2
                    top = (height - size) // 2
                    cropped = img.crop((left, top, left + size, top + size))
                
                output_path = self._get_output_path(image_path, f"cropped_{mode}")
                cropped.save(output_path, quality=85)
                return output_path
        except Exception as e:
            logger.error(f"Simple crop error: {e}")
            return image_path
    
    def remove_background(self, image_path: str) -> str:
        """Simple background removal (mock)"""
        try:
            # For testing, just return a copy of the image
            with Image.open(image_path) as img:
                output_path = self._get_output_path(image_path, "no_bg")
                img.save(output_path, quality=85)
                return output_path
        except Exception as e:
            logger.error(f"Simple remove_bg error: {e}")
            return image_path
    
    def generate_background(self, image_path: str) -> str:
        """Simple background generation (mock)"""
        try:
            # For testing, just return a copy of the image
            with Image.open(image_path) as img:
                output_path = self._get_output_path(image_path, "new_bg")
                img.save(output_path, quality=85)
                return output_path
        except Exception as e:
            logger.error(f"Simple generate_bg error: {e}")
            return image_path
    
    def enhance_quality(self, image_path: str) -> str:
        """Simple quality enhancement"""
        try:
            with Image.open(image_path) as img:
                # Simple enhancement - increase contrast and sharpness
                from PIL import ImageEnhance
                
                enhancer = ImageEnhance.Contrast(img)
                enhanced = enhancer.enhance(1.2)
                
                enhancer = ImageEnhance.Sharpness(enhanced)
                enhanced = enhancer.enhance(1.3)
                
                output_path = self._get_output_path(image_path, "enhanced")
                enhanced.save(output_path, quality=90)
                return output_path
        except Exception as e:
            logger.error(f"Simple enhance error: {e}")
            return image_path
    
    def convert_format(self, image_path: str, format: str) -> str:
        """Simple format conversion"""
        try:
            with Image.open(image_path) as img:
                output_path = self._get_output_path(image_path, f"converted")
                output_path = output_path.rsplit('.', 1)[0] + f'.{format}'
                
                if format.lower() == 'jpeg':
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                
                img.save(output_path, quality=85)
                return output_path
        except Exception as e:
            logger.error(f"Simple convert error: {e}")
            return image_path