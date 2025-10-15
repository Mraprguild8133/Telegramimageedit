import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from io import BytesIO
import asyncio

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token, image_processor, bot_status):
        self.token = token
        self.image_processor = image_processor
        self.bot_status = bot_status
        self.application = None
        self.user_states = {}
        
        # Create directories if they don't exist
        os.makedirs("uploads", exist_ok=True)
        os.makedirs("processed", exist_ok=True)
    
    def start(self):
        """Start the Telegram bot"""
        try:
            # Create application
            self.application = Application.builder().token(self.token).build()
            
            # Add handlers - CORRECT ORDER
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))
            self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
            
            # Start the bot
            logger.info("Starting Telegram bot...")
            self.bot_status["running"] = True
            self.application.run_polling()
            
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {e}")
            self.bot_status["running"] = False
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        self.bot_status["users"] += 1
        welcome_text = """
🎨 *Welcome to AI Photo Editor Bot!*

I can help you edit your photos with these features:

📸 *Image Processing:*
• Resize images
• Crop images  
• Remove backgrounds
• Generate background images
• Convert formats (JPEG, PNG, WebP)

🤖 *AI Features:*
• Background removal
• Image quality enhancement
• Smart cropping

📋 *How to use:*
1. Send me a photo
2. Choose what you want to do
3. Get your edited image!

Type /help for more information or just send me a photo to get started! 🚀
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
📖 *Help - Photo Editor Bot*

*Available Commands:*
• /start - Start the bot
• /help - Show this help message
• /status - Check bot status

*How to Edit Photos:*
1. Send any photo to the bot
2. Choose from the editing options

*Supported Formats:*
• Input: JPEG, PNG, WebP
• Output: JPEG, PNG, WebP

Need help? Just send a photo and follow the menu! 📷✨
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        status_text = f"""
📊 *Bot Status*

• Status: {'🟢 Online' if self.bot_status['running'] else '🔴 Offline'}
• Users served: {self.bot_status['users']}
• Messages processed: {self.bot_status['messages_processed']}

Ready to edit your photos! 📸
        """
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo uploads"""
        try:
            self.bot_status["messages_processed"] += 1
            
            # Get the photo file
            photo = update.message.photo[-1]
            file = await photo.get_file()
            
            # Download photo to memory
            photo_data = BytesIO()
            await file.download_to_memory(photo_data)
            photo_data.seek(0)
            
            # Save photo temporarily
            user_id = update.effective_user.id
            temp_filename = f"temp_{user_id}_{photo.file_id}.jpg"
            temp_path = os.path.join("uploads", temp_filename)
            
            with open(temp_path, 'wb') as f:
                f.write(photo_data.read())
            
            # Store photo path in user state
            self.user_states[user_id] = {"photo_path": temp_path}
            
            # Create inline keyboard for editing options
            keyboard = [
                [
                    InlineKeyboardButton("📏 Resize", callback_data="resize"),
                    InlineKeyboardButton("✂️ Crop", callback_data="crop")
                ],
                [
                    InlineKeyboardButton("🎭 Remove BG", callback_data="remove_bg"),
                    InlineKeyboardButton("🖼️ Generate BG", callback_data="generate_bg")
                ],
                [
                    InlineKeyboardButton("⬆️ Enhance Quality", callback_data="enhance"),
                    InlineKeyboardButton("🔄 Convert Format", callback_data="convert")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📸 *Photo received!* What would you like to do?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error handling photo: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error processing your photo. Please try again."
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        action = query.data
        
        logger.info(f"Callback received: {action} from user {user_id}")
        
        try:
            if user_id not in self.user_states:
                await query.edit_message_text("❌ Please send a photo first!")
                return
            
            photo_path = self.user_states[user_id].get("photo_path")
            if not photo_path or not os.path.exists(photo_path):
                await query.edit_message_text("❌ Photo file expired. Please send a new photo!")
                if user_id in self.user_states:
                    del self.user_states[user_id]
                return

            # Handle different actions
            if action == "resize":
                keyboard = [
                    [
                        InlineKeyboardButton("8K (7680x4320)", callback_data="resize_8k"),
                        InlineKeyboardButton("4K (3840x2160)", callback_data="resize_4k")
                    ],
                    [
                        InlineKeyboardButton("1080p (1920x1080)", callback_data="resize_1080p"),
                        InlineKeyboardButton("720p (1280x720)", callback_data="resize_720p")
                    ],
                    [
                        InlineKeyboardButton("📱 Mobile (720x1280)", callback_data="resize_mobile"),
                        InlineKeyboardButton("🔙 Back", callback_data="back_main")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "📏 *Choose resize option:*",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            elif action.startswith("resize_"):
                await self.process_resize(query, photo_path, action)
                
            elif action == "crop":
                keyboard = [
                    [
                        InlineKeyboardButton("⭐ Smart Crop", callback_data="crop_smart"),
                        InlineKeyboardButton("⬜ Square (1:1)", callback_data="crop_square")
                    ],
                    [
                        InlineKeyboardButton("📱 Portrait (9:16)", callback_data="crop_portrait"),
                        InlineKeyboardButton("🖥️ Landscape (16:9)", callback_data="crop_landscape")
                    ],
                    [
                        InlineKeyboardButton("🔙 Back", callback_data="back_main")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "✂️ *Choose crop option:*",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            elif action.startswith("crop_"):
                await self.process_crop(query, photo_path, action)
                
            elif action == "remove_bg":
                await self.process_remove_background(query, photo_path)
                
            elif action == "generate_bg":
                await self.process_generate_background(query, photo_path)
                
            elif action == "enhance":
                await self.process_enhance_quality(query, photo_path)
                
            elif action == "convert":
                keyboard = [
                    [
                        InlineKeyboardButton("📄 JPEG", callback_data="convert_jpeg"),
                        InlineKeyboardButton("🖼️ PNG", callback_data="convert_png")
                    ],
                    [
                        InlineKeyboardButton("🌐 WebP", callback_data="convert_webp"),
                        InlineKeyboardButton("🔙 Back", callback_data="back_main")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "🔄 *Choose format:*",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            elif action.startswith("convert_"):
                await self.process_convert_format(query, photo_path, action)
                
            elif action == "back_main":
                # Show main menu again
                keyboard = [
                    [
                        InlineKeyboardButton("📏 Resize", callback_data="resize"),
                        InlineKeyboardButton("✂️ Crop", callback_data="crop")
                    ],
                    [
                        InlineKeyboardButton("🎭 Remove BG", callback_data="remove_bg"),
                        InlineKeyboardButton("🖼️ Generate BG", callback_data="generate_bg")
                    ],
                    [
                        InlineKeyboardButton("⬆️ Enhance Quality", callback_data="enhance"),
                        InlineKeyboardButton("🔄 Convert Format", callback_data="convert")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "📸 *What would you like to do with your photo?*",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
            await query.edit_message_text("❌ An error occurred. Please try again.")
    
    async def process_resize(self, query, photo_path, action):
        """Process image resizing"""
        try:
            await query.edit_message_text("🔄 Resizing image... Please wait.")
            
            size_map = {
                "resize_8k": (7680, 4320),
                "resize_4k": (3840, 2160),
                "resize_1080p": (1920, 1080),
                "resize_720p": (1280, 720),
                "resize_mobile": (720, 1280)
            }
            
            if action not in size_map:
                await query.edit_message_text("❌ Invalid resize option.")
                return
            
            width, height = size_map[action]
            result_path = self.image_processor.resize_image(photo_path, width, height)
            
            # Send processed image
            with open(result_path, 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=f"✅ *Image resized to {width}x{height}*",
                    parse_mode='Markdown'
                )
            
            await query.edit_message_text("✅ Image resized successfully!")
            
        except Exception as e:
            logger.error(f"Resize error: {e}")
            await query.edit_message_text("❌ Failed to resize image. Please try again.")
    
    async def process_crop(self, query, photo_path, action):
        """Process image cropping"""
        try:
            await query.edit_message_text("✂️ Cropping image... Please wait.")
            
            crop_mode = action.replace("crop_", "")
            result_path = self.image_processor.smart_crop(photo_path, crop_mode)
            
            # Send processed image
            with open(result_path, 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=f"✅ *Image cropped ({crop_mode.replace('_', ' ').title()})*",
                    parse_mode='Markdown'
                )
            
            await query.edit_message_text("✅ Image cropped successfully!")
            
        except Exception as e:
            logger.error(f"Crop error: {e}")
            await query.edit_message_text("❌ Failed to crop image. Please try again.")
    
    async def process_remove_background(self, query, photo_path):
        """Process background removal"""
        try:
            await query.edit_message_text("🎭 Removing background... Please wait.")
            
            result_path = self.image_processor.remove_background(photo_path)
            
            # Send processed image
            with open(result_path, 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption="✅ *Background removed successfully!*",
                    parse_mode='Markdown'
                )
            
            await query.edit_message_text("✅ Background removed!")
            
        except Exception as e:
            logger.error(f"Background removal error: {e}")
            await query.edit_message_text("❌ Failed to remove background. Please try again.")
    
    async def process_generate_background(self, query, photo_path):
        """Process background generation"""
        try:
            await query.edit_message_text("🖼️ Generating new background... Please wait.")
            
            result_path = self.image_processor.generate_background(photo_path)
            
            # Send processed image
            with open(result_path, 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption="✅ *New background generated!*",
                    parse_mode='Markdown'
                )
            
            await query.edit_message_text("✅ Background generated successfully!")
            
        except Exception as e:
            logger.error(f"Background generation error: {e}")
            await query.edit_message_text("❌ Failed to generate background. Please try again.")
    
    async def process_enhance_quality(self, query, photo_path):
        """Process quality enhancement"""
        try:
            await query.edit_message_text("⬆️ Enhancing image quality... Please wait.")
            
            result_path = self.image_processor.enhance_quality(photo_path)
            
            # Send processed image
            with open(result_path, 'rb') as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption="✅ *Image quality enhanced!*",
                    parse_mode='Markdown'
                )
            
            await query.edit_message_text("✅ Quality enhanced successfully!")
            
        except Exception as e:
            logger.error(f"Quality enhancement error: {e}")
            await query.edit_message_text("❌ Failed to enhance quality. Please try again.")
    
    async def process_convert_format(self, query, photo_path, action):
        """Process format conversion"""
        try:
            format_name = action.replace("convert_", "").upper()
            await query.edit_message_text(f"🔄 Converting to {format_name}... Please wait.")
            
            result_path = self.image_processor.convert_format(photo_path, format_name.lower())
            
            # Send processed image
            with open(result_path, 'rb') as photo:
                if format_name.lower() == 'png':
                    await query.message.reply_document(
                        document=photo,
                        filename=f"converted_image.{format_name.lower()}",
                        caption=f"✅ *Image converted to {format_name}*"
                    )
                else:
                    await query.message.reply_photo(
                        photo=photo,
                        caption=f"✅ *Image converted to {format_name}*",
                        parse_mode='Markdown'
                    )
            
            await query.edit_message_text(f"✅ Converted to {format_name} successfully!")
            
        except Exception as e:
            logger.error(f"Format conversion error: {e}")
            await query.edit_message_text("❌ Failed to convert format. Please try again.")