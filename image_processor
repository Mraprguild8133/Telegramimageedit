import os
import logging
from PIL import Image, ImageFilter, ImageEnhance
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        self.processed_dir = "processed"
        os.makedirs(self.processed_dir, exist_ok=True)
    
    def _generate_filename(self, prefix, extension="jpg"):
        """Generate unique filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}_{timestamp}_{unique_id}.{extension}"
    
    def resize_image(self, input_path, width, height):
        """Resize image to specified dimensions"""
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Calculate aspect ratio preserving dimensions
                original_width, original_height = img.size
                aspect_ratio = original_width / original_height
                
                if width / height > aspect_ratio:
                    # Height is the limiting factor
                    new_height = height
                    new_width = int(height * aspect_ratio)
                else:
                    # Width is the limiting factor
                    new_width = width
                    new_height = int(width / aspect_ratio)
                
                # Resize with high quality
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Save processed image
                output_filename = self._generate_filename("resized")
                output_path = os.path.join(self.processed_dir, output_filename)
                resized_img.save(output_path, "JPEG", quality=95, optimize=True)
                
                logger.info(f"Image resized from {original_width}x{original_height} to {new_width}x{new_height}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            raise
    
    def crop_image(self, input_path, x, y, width, height):
        """Crop image to specified coordinates and dimensions"""
        try:
            with Image.open(input_path) as img:
                # Ensure crop coordinates are within image bounds
                img_width, img_height = img.size
                x = max(0, min(x, img_width))
                y = max(0, min(y, img_height))
                width = min(width, img_width - x)
                height = min(height, img_height - y)
                
                # Crop image
                cropped_img = img.crop((x, y, x + width, y + height))
                
                # Save processed image
                output_filename = self._generate_filename("cropped")
                output_path = os.path.join(self.processed_dir, output_filename)
                cropped_img.save(output_path, "JPEG", quality=95, optimize=True)
                
                logger.info(f"Image cropped to {width}x{height} at ({x}, {y})")
                return output_path
                
        except Exception as e:
            logger.error(f"Error cropping image: {e}")
            raise
    
    def smart_crop(self, input_path, crop_type):
        """Smart cropping based on type"""
        try:
            with Image.open(input_path) as img:
                img_width, img_height = img.size
                
                if crop_type == "square":
                    # Square crop from center
                    size = min(img_width, img_height)
                    left = (img_width - size) // 2
                    top = (img_height - size) // 2
                    cropped_img = img.crop((left, top, left + size, top + size))
                    
                elif crop_type == "portrait":
                    # 9:16 aspect ratio
                    if img_width / img_height > 9/16:
                        # Image is too wide, crop width
                        new_width = int(img_height * 9/16)
                        left = (img_width - new_width) // 2
                        cropped_img = img.crop((left, 0, left + new_width, img_height))
                    else:
                        # Image is too tall, crop height
                        new_height = int(img_width * 16/9)
                        top = (img_height - new_height) // 2
                        cropped_img = img.crop((0, top, img_width, top + new_height))
                
                elif crop_type == "landscape":
                    # 16:9 aspect ratio
                    if img_width / img_height < 16/9:
                        # Image is too tall, crop height
                        new_height = int(img_width * 9/16)
                        top = (img_height - new_height) // 2
                        cropped_img = img.crop((0, top, img_width, top + new_height))
                    else:
                        # Image is too wide, crop width
                        new_width = int(img_height * 16/9)
                        left = (img_width - new_width) // 2
                        cropped_img = img.crop((left, 0, left + new_width, img_height))
                
                elif crop_type == "smart":
                    # Basic smart crop - remove 10% from each edge
                    margin_x = int(img_width * 0.1)
                    margin_y = int(img_height * 0.1)
                    cropped_img = img.crop((margin_x, margin_y, 
                                         img_width - margin_x, img_height - margin_y))
                else:
                    # Default to center crop
                    cropped_img = img
                
                # Save processed image
                output_filename = self._generate_filename(f"crop_{crop_type}")
                output_path = os.path.join(self.processed_dir, output_filename)
                cropped_img.save(output_path, "JPEG", quality=95, optimize=True)
                
                logger.info(f"Smart crop applied: {crop_type}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error smart cropping image: {e}")
            raise
    
    def remove_background(self, input_path):
        """Remove background (mock AI implementation)"""
        try:
            with Image.open(input_path) as img:
                # Convert to RGBA for transparency
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                
                # Simple background removal simulation
                # This is a mock implementation - in production, you'd use rembg or similar
                data = img.getdata()
                new_data = []
                
                # Get the background color (assume it's the corner pixel)
                bg_pixel = img.getpixel((0, 0))
                bg_color = bg_pixel[:3] if isinstance(bg_pixel, tuple) else (bg_pixel, bg_pixel, bg_pixel)
                threshold = 50  # Color similarity threshold
                
                for item in data:
                    # Calculate color difference
                    if len(item) >= 3:
                        r_diff = abs(item[0] - bg_color[0])
                        g_diff = abs(item[1] - bg_color[1])
                        b_diff = abs(item[2] - bg_color[2])
                        
                        if r_diff < threshold and g_diff < threshold and b_diff < threshold:
                            # Make background transparent
                            new_data.append((item[0], item[1], item[2], 0))
                        else:
                            # Keep original pixel
                            new_data.append(item if len(item) == 4 else item + (255,))
                    else:
                        new_data.append(item)
                
                img.putdata(new_data)
                
                # Save as PNG to preserve transparency
                output_filename = self._generate_filename("bg_removed", "png")
                output_path = os.path.join(self.processed_dir, output_filename)
                img.save(output_path, "PNG")
                
                logger.info("Background removal applied (mock)")
                return output_path
                
        except Exception as e:
            logger.error(f"Error removing background: {e}")
            raise
    
    def generate_background(self, input_path):
        """Generate new background (mock AI implementation)"""
        try:
            with Image.open(input_path) as img:
                # Create a gradient background
                width, height = img.size
                
                # Create gradient background
                background = Image.new("RGB", (width, height))
                
                # Generate a simple gradient
                for y in range(height):
                    for x in range(width):
                        # Create a blue to purple gradient
                        r = int(100 + (x / width) * 100)
                        g = int(150 + (y / height) * 50)
                        b = int(200 + ((x + y) / (width + height)) * 55)
                        background.putpixel((x, y), (r, g, b))
                
                # If original image has transparency, composite it
                if img.mode == "RGBA":
                    result = Image.alpha_composite(
                        background.convert("RGBA"), 
                        img.convert("RGBA")
                    )
                else:
                    # Simple blend
                    result = Image.blend(background, img.convert("RGB"), 0.7)
                
                # Save processed image
                output_filename = self._generate_filename("new_bg")
                output_path = os.path.join(self.processed_dir, output_filename)
                result.convert("RGB").save(output_path, "JPEG", quality=95, optimize=True)
                
                logger.info("New background generated (mock)")
                return output_path
                
        except Exception as e:
            logger.error(f"Error generating background: {e}")
            raise
    
    def enhance_quality(self, input_path):
        """Enhance image quality"""
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Apply various enhancements
                
                # 1. Sharpen the image
                sharpened = img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
                
                # 2. Enhance contrast
                contrast_enhancer = ImageEnhance.Contrast(sharpened)
                contrast_enhanced = contrast_enhancer.enhance(1.2)
                
                # 3. Enhance color
                color_enhancer = ImageEnhance.Color(contrast_enhanced)
                color_enhanced = color_enhancer.enhance(1.1)
                
                # 4. Enhance brightness slightly
                brightness_enhancer = ImageEnhance.Brightness(color_enhanced)
                brightness_enhanced = brightness_enhancer.enhance(1.05)
                
                # Save processed image
                output_filename = self._generate_filename("enhanced")
                output_path = os.path.join(self.processed_dir, output_filename)
                brightness_enhanced.save(output_path, "JPEG", quality=98, optimize=True)
                
                logger.info("Image quality enhanced")
                return output_path
                
        except Exception as e:
            logger.error(f"Error enhancing image quality: {e}")
            raise
    
    def convert_format(self, input_path, output_format):
        """Convert image to different format"""
        try:
            with Image.open(input_path) as img:
                # Handle format-specific conversions
                if output_format.lower() == "jpeg":
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    extension = "jpg"
                    save_kwargs = {"quality": 95, "optimize": True}
                    
                elif output_format.lower() == "png":
                    extension = "png"
                    save_kwargs = {"optimize": True}
                    
                elif output_format.lower() == "webp":
                    extension = "webp"
                    save_kwargs = {"quality": 95, "method": 6}
                    
                else:
                    raise ValueError(f"Unsupported format: {output_format}")
                
                # Save in new format
                output_filename = self._generate_filename(f"converted_{output_format.lower()}", extension)
                output_path = os.path.join(self.processed_dir, output_filename)
                img.save(output_path, output_format.upper(), **save_kwargs)
                
                logger.info(f"Image converted to {output_format.upper()}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error converting image format: {e}")
            raise
    
    def cleanup_old_files(self, max_age_hours=24):
        """Clean up old processed files"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.processed_dir):
                if filename == ".gitkeep":
                    continue
                    
                filepath = os.path.join(self.processed_dir, filename)
                if os.path.isfile(filepath):
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        logger.info(f"Cleaned up old file: {filename}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")
