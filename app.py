import os
import logging
from flask import Flask, render_template, jsonify, request, send_file
from werkzeug.middleware.proxy_fix import ProxyFix
import threading
from bot_simple import SimpleTelegramBot
from image_processor import ImageProcessor
from ai_apis import AIImageProcessor

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize components
image_processor = ImageProcessor()
ai_processor = AIImageProcessor()
telegram_bot = None
bot_thread = None
bot_status = {"running": False, "users": 0, "messages_processed": 0}

def start_bot():
    """Start the Telegram bot in a separate thread"""
    global telegram_bot, bot_status
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "your-bot-token-here")
        telegram_bot = SimpleTelegramBot(bot_token, ai_processor, bot_status)
        telegram_bot.start()
        bot_status["running"] = True
        logger.info("Telegram bot started successfully")
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")
        bot_status["running"] = False

@app.route("/")
def index():
    """Main dashboard page"""
    return render_template("index.html", bot_status=bot_status)

@app.route("/api/bot/status")
def bot_status_api():
    """API endpoint for bot status"""
    return jsonify(bot_status)

@app.route("/api/bot/start", methods=["POST"])
def start_bot_api():
    """Start the bot via API"""
    global bot_thread
    if not bot_status["running"]:
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()
        return jsonify({"message": "Bot starting...", "status": "starting"})
    return jsonify({"message": "Bot is already running", "status": "running"})

@app.route("/api/bot/stop", methods=["POST"])
def stop_bot_api():
    """Stop the bot via API"""
    global telegram_bot, bot_status
    if telegram_bot and bot_status["running"]:
        telegram_bot.stop()
        bot_status["running"] = False
        return jsonify({"message": "Bot stopped", "status": "stopped"})
    return jsonify({"message": "Bot is not running", "status": "stopped"})

@app.route("/health")
def health_check():
    """Health check endpoint for monitoring"""
    api_status = ai_processor.get_api_status()
    return jsonify({
        "status": "healthy",
        "bot_running": bot_status["running"],
        "uptime": "running",
        "ai_apis": api_status
    })

@app.route("/api/ai-status")
def ai_status_api():
    """API endpoint for AI service status"""
    return jsonify(ai_processor.get_api_status())

@app.route("/api/test-image", methods=["POST"])
def test_image_processing():
    """Test image processing endpoint"""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    try:
        # Save uploaded file
        filename = file.filename or "uploaded_image.jpg"
        upload_path = os.path.join("uploads", filename)
        file.save(upload_path)
        
        # Process image
        action = request.form.get('action', 'resize')
        if action == 'resize':
            width = int(request.form.get('width', 800))
            height = int(request.form.get('height', 600))
            result_path = image_processor.resize_image(upload_path, width, height)
        elif action == 'crop':
            x = int(request.form.get('x', 0))
            y = int(request.form.get('y', 0))
            width = int(request.form.get('width', 300))
            height = int(request.form.get('height', 300))
            result_path = image_processor.crop_image(upload_path, x, y, width, height)
        elif action == 'remove_bg':
            result_path = ai_processor.remove_background_removebg(upload_path)
        else:
            return jsonify({"error": "Invalid action"}), 400
        
        return send_file(result_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Image processing error: {e}")
        return jsonify({"error": str(e)}), 500

# Create necessary directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("processed", exist_ok=True)

# Auto-start bot if token is available
if os.getenv("TELEGRAM_BOT_TOKEN"):
    start_bot_thread = threading.Thread(target=start_bot, daemon=True)
    start_bot_thread.start()
