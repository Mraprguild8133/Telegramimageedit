import os
import logging
import asyncio
import json
import requests
from datetime import datetime
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

class SimpleTelegramBot:
    def __init__(self, token, image_processor, bot_status):
        self.token = token
        self.image_processor = image_processor
        self.bot_status = bot_status
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.running = False
        self.offset = 0
        
    def start(self):
        """Start the Telegram bot using polling"""
        if not self.token or self.token == "your-bot-token-here":
            logger.error("Bot token not provided")
            return
            
        self.running = True
        self.bot_status["running"] = True
        logger.info("Starting simple Telegram bot...")
        
        # Set up webhook info (set to empty to use polling)
        try:
            self.api_request("deleteWebhook")
        except:
            pass
            
        # Start polling loop in new event loop
        import threading
        def run_bot():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.poll_updates())
            
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
    
    def stop(self):
        """Stop the Telegram bot"""
        self.running = False
        self.bot_status["running"] = False
        logger.info("Simple Telegram bot stopped")
    
    async def poll_updates(self):
        """Poll for updates from Telegram"""
        while self.running:
            try:
                updates = self.get_updates()
                for update in updates:
                    await self.process_update(update)
                    self.offset = update['update_id'] + 1
                
                await asyncio.sleep(1)  # Poll every second
            except Exception as e:
                logger.error(f"Error polling updates: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    def get_updates(self):
        """Get updates from Telegram API"""
        try:
            response = self.api_request("getUpdates", {
                "offset": self.offset,
                "timeout": 10
            })
            return response.get("result", [])
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []
    
    def api_request(self, method, params=None):
        """Make API request to Telegram"""
        url = f"{self.base_url}/{method}"
        try:
            response = requests.post(url, json=params or {}, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def send_message(self, chat_id, text, reply_markup=None):
        """Send text message"""
        params = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)
        
        return self.api_request("sendMessage", params)
    
    def send_photo(self, chat_id, photo_path, caption=""):
        """Send photo message"""
        try:
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': chat_id,
                    'caption': caption,
                    'parse_mode': 'Markdown'
                }
                
                url = f"{self.base_url}/sendPhoto"
                response = requests.post(url, files=files, data=data, timeout=30)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            raise
    
    def edit_message_text(self, chat_id, message_id, text, reply_markup=None):
        """Edit message text"""
        params = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)
        
        return self.api_request("editMessageText", params)
    
    async def process_update(self, update):
        """Process incoming update"""
        try:
            self.bot_status["messages_processed"] += 1
            
            if "message" in update:
                message = update["message"]
                chat_id = message["chat"]["id"]
                user_id = message["from"]["id"]
                
                if "text" in message:
                    text = message["text"]
                    if text.startswith("/start"):
                        await self.handle_start_command(chat_id)
                    elif text.startswith("/help"):
                        await self.handle_help_command(chat_id)
                    elif text.startswith("/status"):
                        await self.handle_status_command(chat_id)
                
                elif "photo" in message:
                    await self.handle_photo(message)
            
            elif "callback_query" in update:
                await self.handle_callback_query(update["callback_query"])
                
        except Exception as e:
            logger.error(f"Error processing update: {e}")
    
    async def handle_start_command(self, chat_id):
        """Handle /start command"""
        self.bot_status["users"] += 1
        welcome_text = """
🎨 *Welcome to AI Photo Editor Bot!*

I can help you edit your photos with these features:

📸 *Image Processing:*
• Resize images (8K, 4K, 1080p, 720p, original)
• Crop images
• Remove backgrounds
• Generate background images
• Convert formats (JPEG, PNG, WebP)

🤖 *AI Features:*
• Background removal
• Image quality enhancement
• Smart cropping suggestions

📋 *How to use:*
1. Send me a photo
2. Choose what you want to do
3. Get your edited image!

Type /help for more information or just send me a photo to get started! 🚀
        """
        self.send_message(chat_id, welcome_text)
    
    async def handle_help_command(self, chat_id):
        """Handle /help command"""
        help_text = """
📖 *Help - Photo Editor Bot*

*Available Commands:*
• /start - Start the bot
• /help - Show this help message
• /status - Check bot status

*How to Edit Photos:*
1. Send any photo to the bot
2. Choose from the editing options:
   - 📏 Resize (8K/4K/1080p/720p/Original)
   - ✂️ Crop image
   - 🎭 Remove background
   - 🖼️ Generate background
   - 🔄 Convert format

*Supported Formats:*
• Input: JPEG, PNG, WebP, GIF
• Output: JPEG, PNG, WebP

*Tips:*
• Send high-quality images for best results
• Background removal works best with clear subjects
• Cropping allows precise selection of image areas
• Quality enhancement preserves original aspect ratio

Need help? Just send a photo and follow the menu! 📷✨
        """
        self.send_message(chat_id, help_text)
    
    async def handle_status_command(self, chat_id):
        """Handle /status command"""
        status_text = f"""
📊 *Bot Status*

• Status: {'🟢 Online' if self.bot_status['running'] else '🔴 Offline'}
• Users served: {self.bot_status['users']}
• Messages processed: {self.bot_status['messages_processed']}
• Available features: ✅ All systems operational

Ready to edit your photos! 📸
        """
        self.send_message(chat_id, status_text)
    
    async def handle_photo(self, message):
        """Handle photo uploads"""
        try:
            chat_id = message["chat"]["id"]
            user_id = message["from"]["id"]
            
            # Get the photo file info
            photos = message["photo"]
            largest_photo = max(photos, key=lambda p: p["width"] * p["height"])
            file_id = largest_photo["file_id"]
            
            # Get file info from Telegram
            file_info = self.api_request("getFile", {"file_id": file_id})
            file_path = file_info["result"]["file_path"]
            
            # Download the file
            file_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
            response = requests.get(file_url)
            response.raise_for_status()
            
            # Save file locally
            temp_filename = f"temp_{user_id}_{file_id}.jpg"
            temp_path = os.path.join("uploads", temp_filename)
            
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            # Store photo path for user (simple in-memory storage)
            if not hasattr(self, 'user_photos'):
                self.user_photos = {}
            self.user_photos[user_id] = temp_path
            
            # Create inline keyboard
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "📏 Resize", "callback_data": "resize"},
                        {"text": "✂️ Crop", "callback_data": "crop"}
                    ],
                    [
                        {"text": "🎭 Remove BG", "callback_data": "remove_bg"},
                        {"text": "🖼️ Generate BG", "callback_data": "generate_bg"}
                    ],
                    [
                        {"text": "⬆️ Enhance Quality", "callback_data": "enhance"},
                        {"text": "🔄 Convert Format", "callback_data": "convert"}
                    ]
                ]
            }
            
            self.send_message(
                chat_id,
                "📸 *Photo received!* What would you like to do?",
                keyboard
            )
            
        except Exception as e:
            logger.error(f"Error handling photo: {e}")
            # Get chat_id for error handling if available
            error_chat_id = message.get("chat", {}).get("id") if 'message' in locals() else None
            if error_chat_id:
                self.send_message(error_chat_id, "❌ Sorry, there was an error processing your photo. Please try again.")
    
    async def handle_callback_query(self, callback_query):
        """Handle callback queries from inline keyboards"""
        try:
            query_id = callback_query["id"]
            user_id = callback_query["from"]["id"]
            chat_id = callback_query["message"]["chat"]["id"]
            message_id = callback_query["message"]["message_id"]
            action = callback_query["data"]
            
            # Answer callback query
            self.api_request("answerCallbackQuery", {"callback_query_id": query_id})
            
            # Check if user has uploaded a photo
            if not hasattr(self, 'user_photos') or user_id not in self.user_photos:
                self.edit_message_text(chat_id, message_id, "❌ Please send a photo first!")
                return
            
            photo_path = self.user_photos[user_id]
            
            if action == "resize":
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "8K (7680x4320)", "callback_data": "resize_8k"},
                            {"text": "4K (3840x2160)", "callback_data": "resize_4k"}
                        ],
                        [
                            {"text": "1080p (1920x1080)", "callback_data": "resize_1080p"},
                            {"text": "720p (1280x720)", "callback_data": "resize_720p"}
                        ],
                        [
                            {"text": "📱 Mobile (720x1280)", "callback_data": "resize_mobile"},
                            {"text": "🔙 Back", "callback_data": "back"}
                        ]
                    ]
                }
                self.edit_message_text(
                    chat_id, message_id,
                    "📏 *Choose resize option:*",
                    keyboard
                )
                
            elif action.startswith("resize_"):
                await self.process_resize(chat_id, message_id, photo_path, action)
                
            elif action == "crop":
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "⭐ Smart Crop", "callback_data": "crop_smart"},
                            {"text": "⬜ Square (1:1)", "callback_data": "crop_square"}
                        ],
                        [
                            {"text": "📱 Portrait (9:16)", "callback_data": "crop_portrait"},
                            {"text": "🖥️ Landscape (16:9)", "callback_data": "crop_landscape"}
                        ],
                        [
                            {"text": "🔙 Back", "callback_data": "back"}
                        ]
                    ]
                }
                self.edit_message_text(
                    chat_id, message_id,
                    "✂️ *Choose crop option:*",
                    keyboard
                )
                
            elif action.startswith("crop_"):
                await self.process_crop(chat_id, message_id, photo_path, action)
                
            elif action == "remove_bg":
                await self.process_remove_background(chat_id, message_id, photo_path)
                
            elif action == "generate_bg":
                await self.process_generate_background(chat_id, message_id, photo_path)
                
            elif action == "enhance":
                await self.process_enhance_quality(chat_id, message_id, photo_path)
                
            elif action == "convert":
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "📄 JPEG", "callback_data": "convert_jpeg"},
                            {"text": "🖼️ PNG", "callback_data": "convert_png"}
                        ],
                        [
                            {"text": "🌐 WebP", "callback_data": "convert_webp"},
                            {"text": "🔙 Back", "callback_data": "back"}
                        ]
                    ]
                }
                self.edit_message_text(
                    chat_id, message_id,
                    "🔄 *Choose format:*",
                    keyboard
                )
                
            elif action.startswith("convert_"):
                await self.process_convert_format(chat_id, message_id, photo_path, action)
            
            elif action.startswith("enhance_"):
                await self.process_enhance_resolution(chat_id, message_id, photo_path, action)
                
            elif action == "back":
                # Show main menu again
                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "📏 Resize", "callback_data": "resize"},
                            {"text": "✂️ Crop", "callback_data": "crop"}
                        ],
                        [
                            {"text": "🎭 Remove BG", "callback_data": "remove_bg"},
                            {"text": "🖼️ Generate BG", "callback_data": "generate_bg"}
                        ],
                        [
                            {"text": "⬆️ Enhance Quality", "callback_data": "enhance"},
                            {"text": "🔄 Convert Format", "callback_data": "convert"}
                        ]
                    ]
                }
                self.edit_message_text(
                    chat_id, message_id,
                    "📸 *What would you like to do with your photo?*",
                    keyboard
                )
            
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            try:
                # Get chat_id and message_id from callback_query for error handling
                error_chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
                error_message_id = callback_query.get("message", {}).get("message_id")
                if error_chat_id and error_message_id:
                    self.edit_message_text(error_chat_id, error_message_id, "❌ An error occurred. Please try again.")
            except:
                pass
    
    async def process_resize(self, chat_id, message_id, photo_path, action):
        """Process image resizing"""
        try:
            self.edit_message_text(chat_id, message_id, "🔄 Resizing image... Please wait.")
            
            size_map = {
                "resize_8k": (7680, 4320),
                "resize_4k": (3840, 2160),
                "resize_1080p": (1920, 1080),
                "resize_720p": (1280, 720),
                "resize_mobile": (720, 1280)
            }
            
            width, height = size_map[action]
            result_path = self.image_processor.resize_image(photo_path, width, height)
            
            # Send processed image
            self.send_photo(
                chat_id, result_path,
                f"✅ *Image resized to {width}x{height}*"
            )
            
            self.edit_message_text(chat_id, message_id, "✅ Image resized successfully!")
            
        except Exception as e:
            logger.error(f"Resize error: {e}")
            self.edit_message_text(chat_id, message_id, "❌ Failed to resize image. Please try again.")
    
    async def process_crop(self, chat_id, message_id, photo_path, action):
        """Process image cropping"""
        try:
            self.edit_message_text(chat_id, message_id, "✂️ Cropping image... Please wait.")
            
            result_path = self.image_processor.smart_crop(photo_path, action.replace("crop_", ""))
            
            # Send processed image
            self.send_photo(
                chat_id, result_path,
                f"✅ *Image cropped ({action.replace('crop_', '').title()})*"
            )
            
            self.edit_message_text(chat_id, message_id, "✅ Image cropped successfully!")
            
        except Exception as e:
            logger.error(f"Crop error: {e}")
            self.edit_message_text(chat_id, message_id, "❌ Failed to crop image. Please try again.")
    
    async def process_remove_background(self, chat_id, message_id, photo_path):
        """Process background removal using AI APIs"""
        try:
            self.edit_message_text(chat_id, message_id, "🎭 Removing background with AI... Please wait.")
            
            result_path = self.image_processor.remove_background_removebg(photo_path)
            
            # Send processed image
            self.send_photo(
                chat_id, result_path,
                "✅ *Background removed with AI-powered Remove.bg!*"
            )
            
            self.edit_message_text(chat_id, message_id, "✅ Background removed using AI!")
            
        except Exception as e:
            logger.error(f"Background removal error: {e}")
            self.edit_message_text(chat_id, message_id, "❌ Failed to remove background. Please try again.")
    
    async def process_generate_background(self, chat_id, message_id, photo_path):
        """Process background generation using AI APIs"""
        try:
            self.edit_message_text(chat_id, message_id, "🖼️ Generating new background with AI... Please wait.")
            
            result_path = self.image_processor.generate_background_photoroom(photo_path)
            
            # Send processed image
            self.send_photo(
                chat_id, result_path,
                "✅ *New background generated with PhotoRoom AI!*"
            )
            
            self.edit_message_text(chat_id, message_id, "✅ Background generated using AI!")
            
        except Exception as e:
            logger.error(f"Background generation error: {e}")
            self.edit_message_text(chat_id, message_id, "❌ Failed to generate background. Please try again.")
    
    async def process_enhance_quality(self, chat_id, message_id, photo_path):
        """Process AI quality enhancement with resolution options"""
        try:
            # Show resolution options first
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "8K Enhancement", "callback_data": "enhance_8k"},
                        {"text": "4K Enhancement", "callback_data": "enhance_4k"}
                    ],
                    [
                        {"text": "1080p Enhancement", "callback_data": "enhance_1080p"},
                        {"text": "720p Enhancement", "callback_data": "enhance_720p"}
                    ],
                    [
                        {"text": "Original+ (2x)", "callback_data": "enhance_original"},
                        {"text": "🔙 Back", "callback_data": "back"}
                    ]
                ]
            }
            self.edit_message_text(
                chat_id, message_id,
                "⬆️ *Choose enhancement quality:*",
                keyboard
            )
            
        except Exception as e:
            logger.error(f"Quality enhancement menu error: {e}")
            self.edit_message_text(chat_id, message_id, "❌ Failed to show enhancement options. Please try again.")
    
    async def process_convert_format(self, chat_id, message_id, photo_path, action):
        """Process format conversion"""
        try:
            self.edit_message_text(chat_id, message_id, "🔄 Converting format... Please wait.")
            
            format_map = {
                "convert_jpeg": "JPEG",
                "convert_png": "PNG", 
                "convert_webp": "WebP"
            }
            
            output_format = format_map[action]
            result_path = self.image_processor.convert_format(photo_path, output_format)
            
            # Send processed image
            self.send_photo(
                chat_id, result_path,
                f"✅ *Image converted to {output_format}*"
            )
            
            self.edit_message_text(chat_id, message_id, "✅ Format converted successfully!")
            
        except Exception as e:
            logger.error(f"Format conversion error: {e}")
            self.edit_message_text(chat_id, message_id, "❌ Failed to convert format. Please try again.")
    
    async def process_enhance_resolution(self, chat_id, message_id, photo_path, action):
        """Process quality enhancement with specific resolution"""
        try:
            self.edit_message_text(chat_id, message_id, "⬆️ Enhancing image quality... Please wait.")
            
            resolution_map = {
                "enhance_8k": "8k",
                "enhance_4k": "4k", 
                "enhance_1080p": "1080p",
                "enhance_720p": "720p",
                "enhance_original": "original"
            }
            
            target_resolution = resolution_map[action]
            result_path = self.image_processor.enhance_quality_ai(photo_path, target_resolution)
            
            # Send processed image
            self.send_photo(
                chat_id, result_path,
                f"✅ *Image enhanced to {target_resolution.upper()} quality with AI!*"
            )
            
            self.edit_message_text(chat_id, message_id, f"✅ Quality enhanced to {target_resolution.upper()}!")
            
        except Exception as e:
            logger.error(f"Quality enhancement error: {e}")
            self.edit_message_text(chat_id, message_id, "❌ Failed to enhance quality. Please try again.")