#!/usr/bin/env python3
"""
Telegram Bot Webhook Server for Production Deployment
Optimized for Render.com and Docker environments with webhook support
"""

import os
import json
import logging
import asyncio
from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from ai_apis import AIImageProcessor
import requests
import tempfile
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
PORT = int(os.getenv('PORT', 5000))

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
    exit(1)

# Initialize image processor
image_processor = AIImageProcessor()

# Bot state management
bot_stats = {
    'users': 0,
    'messages_processed': 0,
    'photos_processed': 0,
    'start_time': datetime.now()
}

user_photos = {}  # Store user photo paths
user_states = {}  # Store user interaction states

def setup_webhook():
    """Set up Telegram webhook"""
    webhook_url = f"{WEBHOOK_URL}/webhook/{TELEGRAM_TOKEN}"
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
            json={
                "url": webhook_url,
                "allowed_updates": ["message", "callback_query"],
                "drop_pending_updates": True
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['ok']:
                logger.info(f"Webhook set successfully: {webhook_url}")
                return True
            else:
                logger.error(f"Failed to set webhook: {result}")
        else:
            logger.error(f"HTTP error setting webhook: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Exception setting webhook: {e}")
    
    return False

def send_message(chat_id, text, reply_markup=None):
    """Send message to Telegram"""
    try:
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
            
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json=data,
            timeout=30
        )
        return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return None

def send_photo(chat_id, photo_path, caption=""):
    """Send photo to Telegram"""
    try:
        with open(photo_path, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
                files=files,
                data=data,
                timeout=60
            )
            
        # Clean up temporary file
        try:
            os.remove(photo_path)
        except:
            pass
            
        return response.json()
    except Exception as e:
        logger.error(f"Error sending photo: {e}")
        return None

def edit_message_text(chat_id, message_id, text, reply_markup=None):
    """Edit message text"""
    try:
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
            
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText",
            json=data,
            timeout=30
        )
        return response.json()
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        return None

def download_photo(file_id):
    """Download photo from Telegram"""
    try:
        # Get file info
        response = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile",
            params={"file_id": file_id},
            timeout=30
        )
        
        if response.status_code != 200:
            return None
            
        file_info = response.json()
        if not file_info['ok']:
            return None
            
        file_path = file_info['result']['file_path']
        
        # Download file
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        file_response = requests.get(file_url, timeout=60)
        
        if file_response.status_code != 200:
            return None
            
        # Save to temporary file
        temp_filename = f"temp_{uuid.uuid4().hex}.jpg"
        temp_path = os.path.join("uploads", temp_filename)
        
        os.makedirs("uploads", exist_ok=True)
        with open(temp_path, 'wb') as f:
            f.write(file_response.content)
            
        return temp_path
        
    except Exception as e:
        logger.error(f"Error downloading photo: {e}")
        return None

def handle_start_command(chat_id):
    """Handle /start command"""
    welcome_text = """
🎨 *Welcome to AI Photo Editor Bot!*

I can help you edit your photos with professional AI-powered tools:

📏 *Basic Editing:*
• Resize images (8K, 4K, 1080p, 720p)
• Smart cropping with multiple styles
• Convert formats (JPEG, PNG, WebP)

🤖 *AI Features:*
• Background removal with Remove.bg
• AI background generation with PhotoRoom
• Quality enhancement and upscaling

📋 *How to use:*
1. Send me a photo
2. Choose what you want to do
3. Get your professionally edited image!

Just send me a photo to get started! 🚀
    """
    send_message(chat_id, welcome_text)
    
    # Update stats
    if chat_id not in user_states:
        bot_stats['users'] += 1
        user_states[chat_id] = {}

def handle_photo_message(message):
    """Handle photo uploads"""
    try:
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        
        # Get largest photo
        photos = message["photo"]
        largest_photo = max(photos, key=lambda p: p["width"] * p["height"])
        file_id = largest_photo["file_id"]
        
        # Download photo
        photo_path = download_photo(file_id)
        if not photo_path:
            send_message(chat_id, "❌ Failed to download photo. Please try again.")
            return
            
        # Store photo path
        user_photos[user_id] = photo_path
        bot_stats['photos_processed'] += 1
        
        # Create editing menu
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
        
        send_message(
            chat_id,
            "📸 *Photo received! What would you like to do?*",
            keyboard
        )
        
        bot_stats['messages_processed'] += 1
        
    except Exception as e:
        logger.error(f"Error handling photo: {e}")
        send_message(chat_id, "❌ Error processing photo. Please try again.")

def handle_callback_query(callback_query):
    """Handle callback button presses"""
    try:
        chat_id = callback_query["message"]["chat"]["id"]
        message_id = callback_query["message"]["message_id"]
        user_id = callback_query["from"]["id"]
        action = callback_query["data"]
        
        # Answer callback query
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery",
            json={"callback_query_id": callback_query["id"]},
            timeout=10
        )
        
        photo_path = user_photos.get(user_id)
        if not photo_path or not os.path.exists(photo_path):
            edit_message_text(
                chat_id, message_id,
                "❌ Photo expired. Please send a new photo."
            )
            return
        
        # Handle different actions
        if action == "remove_bg":
            edit_message_text(chat_id, message_id, "🎭 Removing background... Please wait.")
            try:
                result_path = image_processor.remove_background_removebg(photo_path)
                send_photo(chat_id, result_path, "✅ *Background removed with AI!*")
                edit_message_text(chat_id, message_id, "✅ Background removed successfully!")
            except Exception as e:
                logger.error(f"Background removal error: {e}")
                edit_message_text(chat_id, message_id, "❌ Failed to remove background.")
                
        elif action.startswith("resize_"):
            size_map = {
                "resize_8k": (7680, 4320),
                "resize_4k": (3840, 2160), 
                "resize_1080p": (1920, 1080),
                "resize_720p": (1280, 720)
            }
            
            if action in size_map:
                edit_message_text(chat_id, message_id, "📏 Resizing... Please wait.")
                try:
                    width, height = size_map[action]
                    result_path = image_processor.resize_image(photo_path, width, height)
                    send_photo(chat_id, result_path, f"✅ *Resized to {width}x{height}*")
                    edit_message_text(chat_id, message_id, "✅ Resize completed!")
                except Exception as e:
                    logger.error(f"Resize error: {e}")
                    edit_message_text(chat_id, message_id, "❌ Failed to resize image.")
        
        # Add more action handlers as needed...
        
    except Exception as e:
        logger.error(f"Error handling callback: {e}")

@app.route('/')
def index():
    """Health check and info page"""
    uptime = datetime.now() - bot_stats['start_time']
    return jsonify({
        "status": "running",
        "bot": "Telegram Photo Editor Bot",
        "uptime_seconds": int(uptime.total_seconds()),
        "stats": bot_stats,
        "webhook_url": f"{WEBHOOK_URL}/webhook/{TELEGRAM_TOKEN}"
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "bot_running": True,
        "uptime": "running",
        "ai_apis": image_processor.get_api_status()
    })

@app.route('/api/ai-status')
def ai_status():
    """AI API status endpoint"""
    return jsonify(image_processor.get_api_status())

@app.route(f'/webhook/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    try:
        update = request.get_json()
        
        if not update:
            return jsonify({"ok": False, "error": "No JSON data"})
        
        # Handle message updates
        if "message" in update:
            message = update["message"]
            
            if "text" in message:
                text = message["text"]
                chat_id = message["chat"]["id"]
                
                if text.startswith('/start'):
                    handle_start_command(chat_id)
                elif text.startswith('/help'):
                    handle_start_command(chat_id)  # Same as start for now
                    
            elif "photo" in message:
                handle_photo_message(message)
        
        # Handle callback queries
        elif "callback_query" in update:
            handle_callback_query(update["callback_query"])
        
        return jsonify({"ok": True})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"ok": False, "error": str(e)})

if __name__ == '__main__':
    logger.info("Starting Telegram Bot Webhook Server...")
    
    # Create necessary directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("processed", exist_ok=True)
    
    # Set up webhook
    if setup_webhook():
        logger.info(f"Starting Flask server on port {PORT}")
        app.run(host='0.0.0.0', port=PORT, debug=False)
    else:
        logger.error("Failed to set up webhook. Exiting.")
        exit(1)