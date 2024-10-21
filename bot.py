import sqlite3
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import asyncio
import os

# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Set to keep track of chat IDs that received the welcome message
sent_welcome_messages = set()

# Database setup
def init_db():
    db_path = os.path.join('/app/db', 'messages.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            message TEXT,
            file_id TEXT,
            file_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Store message in database (both text and image metadata)
def store_message(chat_id, message=None, file_id=None, file_path=None):
    db_path = os.path.join('/app/db', 'messages.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT INTO messages (chat_id, message, file_id, file_path) VALUES (?, ?, ?, ?)',
              (chat_id, message, file_id, file_path))
    conn.commit()
    conn.close()

# Handle messages from users (text and images)
async def handle_message(update: Update, context):
    chat_id = update.message.chat_id
    message_text = update.message.text if update.message.text else None

    if update.message.photo:
        # Get the largest size photo (last in the list)
        photo = update.message.photo[-1]
        file_id = photo.file_id
        file = await context.bot.get_file(file_id)
        
        # Ensure the image directory exists
        image_dir = '/app/images/'
        os.makedirs(image_dir, exist_ok=True)
        
        file_path = f'{image_dir}{file_id}.jpg'
        
        # Download the photo and save it to the filesystem
        await file.download_to_drive(file_path)
        
        # Store file information in the database
        store_message(chat_id, file_id=file_id, file_path=file_path)
        response_message = await update.message.reply_text("Picture received! It will disappear soon.")
    else:
        # Store text message
        store_message(chat_id, message=message_text)
        response_message = await update.message.reply_text("Message received! It will disappear soon.")

    # Log message IDs for debugging
    logger.info(f"Your Message ID: {update.message.message_id}, Bot Response ID: {response_message.message_id}")

    # Delay for 10 seconds before deleting
    await asyncio.sleep(10)

    # Delete the user's message and bot's response
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)  # User message
        await context.bot.delete_message(chat_id=chat_id, message_id=response_message.message_id)  # Bot response
        logger.info("Deleted messages successfully.")
    except Exception as e:
        logger.error(f"Failed to delete messages: {e}")

    # Always send the welcome message if it hasn't been sent
    await send_welcome_message(chat_id, context)

# Send a welcome message
async def send_welcome_message(chat_id, context):
    if chat_id not in sent_welcome_messages:
        welcome_message = "Hi! Send me a message or a picture, and it will disappear after 10 seconds!"
        await context.bot.send_message(chat_id=chat_id, text=welcome_message)
        sent_welcome_messages.add(chat_id)

# Start command handler
async def start(update: Update, context):
    await send_welcome_message(update.message.chat_id, context)

if __name__ == '__main__':
    init_db()  # Initialize the database

    # Initialize the bot application with timeouts for requests
    app = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).connect_timeout(10).read_timeout(20).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    logger.info("Starting bot...")
    app.run_polling()
