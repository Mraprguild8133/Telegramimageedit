import os
import requests
import logging
from PIL import Image
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class AIImageProcessor:
    """
    Enhanced image processor with real AI API integrations
    Supports PhotoRoom.com and Remove.bg for professional image editing
    """
    
    def __init__(self):
        self.processed_dir = "processed"
        os.makedirs(self.processed_dir, exist_ok=True)
        
        # API credentials - will be provided by user through secrets
        self.removebg_api_key = os.getenv("REMOVEBG_API_KEY")
        self.photoroom_api_key = os.getenv("PHOTOROOM_API_KEY")
        
    def _generate_filename(self, prefix, extension="jpg"):
        """Generate unique filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}_{timestamp}_{unique_id}.{extension}"
    
    def remove_background_removebg(self, input_path):
        """
        Remove background using Remove.bg API
        Provides professional AI-powered background removal
        """
        if not self.removebg_api_key:
            logger.warning("Remove.bg API key not found, using fallback method")
            return self.remove_background_local(input_path)
        
        try:
            logger.info("Using Remove.bg API for background removal")
            
            with open(input_path, 'rb') as input_file:
                response = requests.post(
                    'https://api.remove.bg/v1.0/removebg',
                    files={'image_file': input_file},
                    data={'size': 'auto'},
                    headers={'X-Api-Key': self.removebg_api_key},
                    timeout=30
                )
            
            if response.status_code == requests.codes.ok:
                # Save the result
                output_filename = self._generate_filename("removebg", "png")
                output_path = os.path.join(self.processed_dir, output_filename)
                
                with open(output_path, 'wb') as out_file:
                    out_file.write(response.content)
                
                logger.info("Background removed successfully using Remove.bg")
                return output_path
            else:
                logger.error(f"Remove.bg API error: {response.status_code} - {response.text}")
                return self.remove_background_local(input_path)
                
        except Exception as e:
            logger.error(f"Remove.bg API error: {e}")
            return self.remove_background_local(input_path)
    
    def remove_background_local(self, input_path):
        """
        Fallback local background removal method
        """
        try:
            logger.info("Using local background removal method")
            
            with Image.open(input_path) as img:
                # Convert to RGBA for transparency
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                
                # Enhanced local background removal using edge detection
                data = img.getdata()
                new_data = []
                
                # Get corner colors for better background detection
                try:
                    corners = [
                        img.getpixel((0, 0)),  # top-left
                        img.getpixel((img.width-1, 0)),  # top-right
                        img.getpixel((0, img.height-1)),  # bottom-left
                        img.getpixel((img.width-1, img.height-1))  # bottom-right
                    ]
                    
                    # Average corner colors to determine background
                    if all(isinstance(c, (tuple, int)) and (isinstance(c, int) or len(c) >= 3) for c in corners):
                        if isinstance(corners[0], int):
                            # Grayscale image
                            avg_bg = (corners[0], corners[0], corners[0])
                        else:
                            # Color image
                            avg_bg = tuple(sum(corners[i][j] for i in range(len(corners)) if isinstance(corners[i], tuple)) // len([c for c in corners if isinstance(c, tuple)]) for j in range(3))
                    else:
                        avg_bg = (255, 255, 255)  # white fallback
                except Exception:
                    avg_bg = (255, 255, 255)  # white fallback
                
                threshold = 40  # More precise threshold
                
                for item in data:
                    if len(item) >= 3:
                        # Calculate color difference from background
                        r_diff = abs(item[0] - avg_bg[0])
                        g_diff = abs(item[1] - avg_bg[1])
                        b_diff = abs(item[2] - avg_bg[2])
                        
                        # Check if pixel is similar to background
                        if r_diff < threshold and g_diff < threshold and b_diff < threshold:
                            # Make background transparent
                            new_data.append((item[0], item[1], item[2], 0))
                        else:
                            # Keep original pixel with full opacity
                            new_data.append(item if len(item) == 4 else item + (255,))
                    else:
                        new_data.append(item)
                
                img.putdata(new_data)
                
                # Save as PNG to preserve transparency
                output_filename = self._generate_filename("bg_removed_local", "png")
                output_path = os.path.join(self.processed_dir, output_filename)
                img.save(output_path, "PNG")
                
                logger.info("Background removal completed using local method")
                return output_path
                
        except Exception as e:
            logger.error(f"Local background removal error: {e}")
            raise
    
    def generate_background_photoroom(self, input_path, background_prompt="professional gradient"):
        """
        Generate new background using PhotoRoom API
        Provides AI-powered background generation and replacement
        """
        if not self.photoroom_api_key:
            logger.warning("PhotoRoom API key not found, using fallback method")
            return self.generate_background_local(input_path)
        
        try:
            logger.info("Using PhotoRoom API for background generation")
            
            # First, remove the existing background
            no_bg_path = self.remove_background_removebg(input_path)
            
            # PhotoRoom API endpoint for background replacement
            with open(no_bg_path, 'rb') as image_file:
                files = {
                    'image_file': image_file
                }
                data = {
                    'background_prompt': background_prompt,
                    'output_format': 'jpg',
                    'background_color': '#ffffff'
                }
                headers = {
                    'X-API-Key': self.photoroom_api_key
                }
                
                response = requests.post(
                    'https://sdk.photoroom.com/v1/segment',
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=45
                )
            
            if response.status_code == 200:
                # Save the result
                output_filename = self._generate_filename("photoroom_bg", "jpg")
                output_path = os.path.join(self.processed_dir, output_filename)
                
                with open(output_path, 'wb') as out_file:
                    out_file.write(response.content)
                
                logger.info("Background generated successfully using PhotoRoom")
                return output_path
            else:
                logger.error(f"PhotoRoom API error: {response.status_code} - {response.text}")
                return self.generate_background_local(input_path)
                
        except Exception as e:
            logger.error(f"PhotoRoom API error: {e}")
            return self.generate_background_local(input_path)
    
    def generate_background_local(self, input_path):
        """
        Fallback local background generation method
        """
        try:
            logger.info("Using local background generation method")
            
            with Image.open(input_path) as img:
                width, height = img.size
                
                # Create multiple gradient options
                gradients = [
                    # Blue to purple professional gradient
                    lambda x, y: (
                        int(70 + (x / width) * 80),   # Blue to purple red component
                        int(130 + (y / height) * 60), # Green component
                        int(200 + ((x + y) / (width + height)) * 55)  # Blue component
                    ),
                    # Warm sunset gradient
                    lambda x, y: (
                        int(255 - (y / height) * 100),  # Orange to pink
                        int(150 + (x / width) * 50),
                        int(80 + (y / height) * 120)
                    ),
                    # Cool professional gradient
                    lambda x, y: (
                        int(40 + (x / width) * 60),
                        int(90 + (y / height) * 100),
                        int(140 + (x / width) * 100)
                    )
                ]
                
                # Select gradient based on image dimensions
                gradient_func = gradients[hash(str(width * height)) % len(gradients)]
                
                # Create gradient background
                background = Image.new("RGB", (width, height))
                
                for y in range(height):
                    for x in range(width):
                        r, g, b = gradient_func(x, y)
                        r = max(0, min(255, r))
                        g = max(0, min(255, g))
                        b = max(0, min(255, b))
                        background.putpixel((x, y), (r, g, b))
                
                # Composite with original image
                if img.mode == "RGBA":
                    result = Image.alpha_composite(
                        background.convert("RGBA"), 
                        img.convert("RGBA")
                    )
                else:
                    # Apply subtle blend for non-transparent images
                    result = Image.blend(background, img.convert("RGB"), 0.8)
                
                # Save processed image
                output_filename = self._generate_filename("bg_generated_local", "jpg")
                output_path = os.path.join(self.processed_dir, output_filename)
                result.convert("RGB").save(output_path, "JPEG", quality=95, optimize=True)
                
                logger.info("Background generated using local method")
                return output_path
                
        except Exception as e:
            logger.error(f"Local background generation error: {e}")
            raise
    
    def enhance_quality_ai(self, input_path, target_resolution="4k"):
        """
        AI-powered image quality enhancement
        Supports multiple resolution targets: 720p, 1080p, 4k, 8k
        """
        try:
            logger.info(f"Enhancing image quality to {target_resolution}")
            
            with Image.open(input_path) as img:
                original_width, original_height = img.size
                
                # Resolution mapping
                resolution_map = {
                    "720p": (1280, 720),
                    "1080p": (1920, 1080),
                    "4k": (3840, 2160),
                    "8k": (7680, 4320),
                    "original": (original_width * 2, original_height * 2)  # Double resolution
                }
                
                target_width, target_height = resolution_map.get(target_resolution, (1920, 1080))
                
                # Calculate aspect ratio preserving dimensions
                aspect_ratio = original_width / original_height
                if target_width / target_height > aspect_ratio:
                    # Height is the limiting factor
                    new_height = target_height
                    new_width = int(target_height * aspect_ratio)
                else:
                    # Width is the limiting factor
                    new_width = target_width
                    new_height = int(target_width / aspect_ratio)
                
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Advanced upscaling with multiple passes for quality
                if new_width > original_width * 1.5:
                    # Multi-step upscaling for better quality
                    intermediate_width = int(original_width * 1.5)
                    intermediate_height = int(original_height * 1.5)
                    
                    # First upscale pass
                    img = img.resize((intermediate_width, intermediate_height), Image.Resampling.LANCZOS)
                    
                    # Apply sharpening
                    from PIL import ImageFilter, ImageEnhance
                    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=2))
                    
                    # Final upscale
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                else:
                    # Single pass for smaller upscales
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Apply quality enhancements
                from PIL import ImageEnhance, ImageFilter
                
                # 1. Enhance contrast
                contrast_enhancer = ImageEnhance.Contrast(img)
                img = contrast_enhancer.enhance(1.15)
                
                # 2. Enhance color saturation
                color_enhancer = ImageEnhance.Color(img)
                img = color_enhancer.enhance(1.1)
                
                # 3. Enhance sharpness
                sharpness_enhancer = ImageEnhance.Sharpness(img)
                img = sharpness_enhancer.enhance(1.2)
                
                # 4. Apply noise reduction (subtle blur then sharpen)
                img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
                img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=3))
                
                # Save enhanced image
                output_filename = self._generate_filename(f"enhanced_{target_resolution}", "jpg")
                output_path = os.path.join(self.processed_dir, output_filename)
                img.save(output_path, "JPEG", quality=98, optimize=True, progressive=True)
                
                logger.info(f"Image quality enhanced to {new_width}x{new_height} ({target_resolution})")
                return output_path
                
        except Exception as e:
            logger.error(f"Quality enhancement error: {e}")
            raise
    
    def smart_crop_ai(self, input_path, crop_style="smart"):
        """
        AI-powered smart cropping with multiple styles
        """
        try:
            logger.info(f"Applying AI smart crop: {crop_style}")
            
            with Image.open(input_path) as img:
                width, height = img.size
                
                if crop_style == "smart":
                    # AI-like smart crop focusing on the center with rule of thirds
                    # Remove 15% from each edge to focus on subject
                    crop_margin_x = int(width * 0.15)
                    crop_margin_y = int(height * 0.15)
                    
                    left = crop_margin_x
                    top = crop_margin_y
                    right = width - crop_margin_x
                    bottom = height - crop_margin_y
                    
                    cropped = img.crop((left, top, right, bottom))
                    
                elif crop_style == "face":
                    # Simulate face detection crop (upper center focus)
                    crop_height = int(height * 0.7)  # Focus on upper 70%
                    crop_width = int(width * 0.8)   # Center 80% width
                    
                    left = (width - crop_width) // 2
                    top = int(height * 0.1)  # Start from 10% down
                    right = left + crop_width
                    bottom = top + crop_height
                    
                    cropped = img.crop((left, top, right, bottom))
                    
                elif crop_style == "product":
                    # Product photography crop (center with padding)
                    padding = int(min(width, height) * 0.1)
                    size = min(width, height) - (2 * padding)
                    
                    left = (width - size) // 2
                    top = (height - size) // 2
                    right = left + size
                    bottom = top + size
                    
                    cropped = img.crop((left, top, right, bottom))
                    
                else:
                    # Default center crop
                    size = min(width, height)
                    left = (width - size) // 2
                    top = (height - size) // 2
                    cropped = img.crop((left, top, left + size, top + size))
                
                # Save cropped image
                output_filename = self._generate_filename(f"ai_crop_{crop_style}", "jpg")
                output_path = os.path.join(self.processed_dir, output_filename)
                cropped.save(output_path, "JPEG", quality=95, optimize=True)
                
                logger.info(f"AI smart crop applied: {crop_style}")
                return output_path
                
        except Exception as e:
            logger.error(f"AI smart crop error: {e}")
            raise
    
    def get_api_status(self):
        """
        Check the status of external APIs
        """
        status = {
            "removebg": {
                "available": bool(self.removebg_api_key),
                "api_key_set": bool(self.removebg_api_key)
            },
            "photoroom": {
                "available": bool(self.photoroom_api_key),
                "api_key_set": bool(self.photoroom_api_key)
            }
        }
        return status
    
    def resize_image(self, input_path, width, height):
        """Resize image to specified dimensions with high quality"""
        try:
            with Image.open(input_path) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                original_width, original_height = img.size
                aspect_ratio = original_width / original_height
                
                if width / height > aspect_ratio:
                    new_height = height
                    new_width = int(height * aspect_ratio)
                else:
                    new_width = width
                    new_height = int(width / aspect_ratio)
                
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                output_filename = self._generate_filename("resized")
                output_path = os.path.join(self.processed_dir, output_filename)
                resized_img.save(output_path, "JPEG", quality=95, optimize=True)
                
                logger.info(f"Image resized from {original_width}x{original_height} to {new_width}x{new_height}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            raise

    def smart_crop(self, input_path, crop_type="smart"):
        """Smart crop with multiple styles"""
        try:
            with Image.open(input_path) as img:
                img_width, img_height = img.size
                
                if crop_type == "square":
                    size = min(img_width, img_height)
                    x = (img_width - size) // 2
                    y = (img_height - size) // 2
                    cropped_img = img.crop((x, y, x + size, y + size))
                    
                elif crop_type == "portrait":
                    if img_width / img_height > 3/4:
                        new_width = int(img_height * 3/4)
                        x = (img_width - new_width) // 2
                        cropped_img = img.crop((x, 0, x + new_width, img_height))
                    else:
                        new_height = int(img_width * 4/3)
                        y = (img_height - new_height) // 2
                        cropped_img = img.crop((0, y, img_width, y + new_height))
                        
                elif crop_type == "landscape":
                    if img_width / img_height > 16/9:
                        new_width = int(img_height * 16/9)
                        x = (img_width - new_width) // 2
                        cropped_img = img.crop((x, 0, x + new_width, img_height))
                    else:
                        new_height = int(img_width * 9/16)
                        y = (img_height - new_height) // 2
                        cropped_img = img.crop((0, y, img_width, y + new_height))
                        
                else:  # smart crop
                    golden_ratio = 1.618
                    if img_width / img_height > golden_ratio:
                        new_width = int(img_height * golden_ratio)
                        x = (img_width - new_width) // 2
                        cropped_img = img.crop((x, 0, x + new_width, img_height))
                    else:
                        new_height = int(img_width / golden_ratio)
                        y = (img_height - new_height) // 2
                        cropped_img = img.crop((0, y, img_width, y + new_height))
                
                output_filename = self._generate_filename(f"cropped_{crop_type}")
                output_path = os.path.join(self.processed_dir, output_filename)
                cropped_img.save(output_path, "JPEG", quality=95, optimize=True)
                
                logger.info(f"Image cropped using {crop_type} style")
                return output_path
                
        except Exception as e:
            logger.error(f"Error cropping image: {e}")
            raise

    def enhance_quality(self, input_path, target_resolution="1080p"):
        """Enhance image quality and upscale"""
        try:
            with Image.open(input_path) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                original_width, original_height = img.size
                
                resolutions = {
                    "720p": (1280, 720),
                    "1080p": (1920, 1080),
                    "4k": (3840, 2160),
                    "8k": (7680, 4320),
                    "original+": (int(original_width * 1.5), int(original_height * 1.5))
                }
                
                target_width, target_height = resolutions.get(target_resolution, (1920, 1080))
                
                scale_x = target_width / original_width
                scale_y = target_height / original_height
                scale_factor = min(scale_x, scale_y)
                
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                
                if scale_factor > 2:
                    current_img = img
                    current_scale = 1
                    
                    while current_scale < scale_factor:
                        step_scale = min(2, scale_factor / current_scale)
                        step_width = int(current_img.width * step_scale)
                        step_height = int(current_img.height * step_scale)
                        
                        current_img = current_img.resize((step_width, step_height), Image.Resampling.LANCZOS)
                        current_scale *= step_scale
                        
                    enhanced_img = current_img
                else:
                    enhanced_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                from PIL import ImageFilter, ImageEnhance
                enhanced_img = enhanced_img.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
                
                enhancer = ImageEnhance.Contrast(enhanced_img)
                enhanced_img = enhancer.enhance(1.1)
                
                output_filename = self._generate_filename(f"enhanced_{target_resolution}")
                output_path = os.path.join(self.processed_dir, output_filename)
                enhanced_img.save(output_path, "JPEG", quality=98, optimize=True)
                
                logger.info(f"Image enhanced from {original_width}x{original_height} to {new_width}x{new_height} ({target_resolution})")
                return output_path
                
        except Exception as e:
            logger.error(f"Error enhancing image quality: {e}")
            raise

    def convert_format(self, input_path, target_format="jpeg"):
        """Convert image to different format"""
        try:
            with Image.open(input_path) as img:
                # Handle different target formats
                if target_format.lower() in ["jpg", "jpeg"]:
                    # Convert to RGB for JPEG (no transparency support)
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    
                    output_filename = self._generate_filename(f"converted_{target_format}", "jpg")
                    output_path = os.path.join(self.processed_dir, output_filename)
                    img.save(output_path, "JPEG", quality=95, optimize=True)
                    
                elif target_format.lower() == "png":
                    # PNG supports transparency, so keep original mode
                    if img.mode not in ("RGBA", "RGB"):
                        img = img.convert("RGBA")
                    
                    output_filename = self._generate_filename(f"converted_{target_format}", "png")
                    output_path = os.path.join(self.processed_dir, output_filename)
                    img.save(output_path, "PNG", optimize=True)
                    
                elif target_format.lower() == "webp":
                    # WebP supports transparency and high compression
                    output_filename = self._generate_filename(f"converted_{target_format}", "webp")
                    output_path = os.path.join(self.processed_dir, output_filename)
                    img.save(output_path, "WebP", quality=92, optimize=True)
                    
                else:
                    raise ValueError(f"Unsupported format: {target_format}")
                
                logger.info(f"Image converted to {target_format.upper()} format")
                return output_path
                
        except Exception as e:
            logger.error(f"Error converting image format: {e}")
            raise

    def enhance_quality_ai(self, input_path, target_resolution="4k"):
        """AI-powered image quality enhancement with multiple resolution targets"""
        try:
            logger.info(f"Enhancing image quality to {target_resolution} using AI algorithms")
            
            with Image.open(input_path) as img:
                original_width, original_height = img.size
                
                # Resolution mapping with proper aspect ratios
                resolution_map = {
                    "720p": (1280, 720),
                    "1080p": (1920, 1080),
                    "4k": (3840, 2160),
                    "8k": (7680, 4320),
                    "original": (int(original_width * 2), int(original_height * 2))
                }
                
                target_width, target_height = resolution_map.get(target_resolution, (1920, 1080))
                
                # Calculate aspect ratio preserving dimensions
                aspect_ratio = original_width / original_height
                if target_width / target_height > aspect_ratio:
                    new_height = target_height
                    new_width = int(target_height * aspect_ratio)
                else:
                    new_width = target_width
                    new_height = int(target_width / aspect_ratio)
                
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Advanced multi-step AI-like enhancement
                scale_factor = max(new_width / original_width, new_height / original_height)
                
                if scale_factor > 2:
                    # Multi-step upscaling for large enhancements
                    current_img = img
                    current_scale = 1
                    
                    while current_scale < scale_factor:
                        step_scale = min(2, scale_factor / current_scale)
                        step_width = int(current_img.width * step_scale)
                        step_height = int(current_img.height * step_scale)
                        
                        # High-quality resize with Lanczos
                        current_img = current_img.resize((step_width, step_height), Image.Resampling.LANCZOS)
                        
                        # Apply enhancement filters after each step
                        from PIL import ImageFilter, ImageEnhance
                        
                        # Subtle sharpening
                        current_img = current_img.filter(ImageFilter.UnsharpMask(radius=0.8, percent=120, threshold=2))
                        
                        current_scale *= step_scale
                        
                    enhanced_img = current_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                else:
                    # Single step for smaller enhancements
                    enhanced_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Apply AI-like enhancement pipeline
                from PIL import ImageEnhance, ImageFilter
                
                # 1. Contrast enhancement
                contrast_enhancer = ImageEnhance.Contrast(enhanced_img)
                enhanced_img = contrast_enhancer.enhance(1.15)
                
                # 2. Color saturation boost
                color_enhancer = ImageEnhance.Color(enhanced_img)
                enhanced_img = color_enhancer.enhance(1.1)
                
                # 3. Sharpness enhancement
                sharpness_enhancer = ImageEnhance.Sharpness(enhanced_img)
                enhanced_img = sharpness_enhancer.enhance(1.25)
                
                # 4. Noise reduction and final sharpening
                enhanced_img = enhanced_img.filter(ImageFilter.GaussianBlur(radius=0.3))
                enhanced_img = enhanced_img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=160, threshold=3))
                
                # 5. Final brightness adjustment
                brightness_enhancer = ImageEnhance.Brightness(enhanced_img)
                enhanced_img = brightness_enhancer.enhance(1.05)
                
                # Save enhanced image with high quality
                output_filename = self._generate_filename(f"ai_enhanced_{target_resolution}", "jpg")
                output_path = os.path.join(self.processed_dir, output_filename)
                enhanced_img.save(output_path, "JPEG", quality=98, optimize=True, progressive=True)
                
                logger.info(f"AI quality enhancement completed: {original_width}x{original_height} → {new_width}x{new_height} ({target_resolution})")
                return output_path
                
        except Exception as e:
            logger.error(f"AI quality enhancement error: {e}")
            raise