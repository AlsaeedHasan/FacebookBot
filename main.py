import logging
import os
import shutil

from colorlog import ColoredFormatter
from dotenv import load_dotenv
from pyrogram import Client, idle
from pyrogram.types import BotCommand

from database import Database

# Load environment variables
load_dotenv()

# Configure logging
color_formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(color_formatter)

file_handler = logging.FileHandler("bot.log")
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)

logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])

logger = logging.getLogger(__name__)

# Get environment variables
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DB_PATH = os.environ.get("DB_PATH", "./database/bot_data.json")
SCREENSHOTS_DIR = os.environ.get("SCREENSHOTS_DIR", "./screenshots")
SUPERUSER_USERNAME = os.environ.get("SUSERNAME")
SUPERUSER_PASSWORD = os.environ.get("PASSWORD")

# Check if required environment variables are set
if not all([API_ID, API_HASH, BOT_TOKEN, SUPERUSER_USERNAME, SUPERUSER_PASSWORD]):
    logger.error("Missing required environment variables. Please check your .env file.")
    exit(1)

# Initialize the bot
bot = Client(
    "FacebookBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="handlers"),
)

# Initialize database
db = Database(DB_PATH, {"username": SUPERUSER_USERNAME, "password": SUPERUSER_PASSWORD})

# Attach database to bot
bot.db = db

# Bot commands
BOT_COMMANDS = [
    BotCommand("start", "بدء استخدام البوت"),
    BotCommand("help", "عرض المساعدة"),
    BotCommand("cancel", "إلغاء الأمر الحالي"),
    BotCommand("login", "تسجيل الدخول إلى حساب فيسبوك"),
    BotCommand("services", "عرض الخدمات المتاحة"),
    BotCommand("accounts", "إدارة الحسابات"),
]


def clean_screenshots_folder():
    """Clean the screenshots folder"""
    if os.path.exists(SCREENSHOTS_DIR):
        shutil.rmtree(SCREENSHOTS_DIR)
        os.makedirs(SCREENSHOTS_DIR)
    logger.info("Screenshots folder cleaned.")


async def main():
    """Start the bot"""
    await bot.start()

    # Set bot commands
    await bot.set_bot_commands(BOT_COMMANDS)

    logger.info("Bot started successfully!")

    # Keep the bot running
    await idle()

    # Stop the bot
    await bot.stop()

    # Clean the screenshots folder before quitting
    clean_screenshots_folder()


if __name__ == "__main__":
    import asyncio

    try:
        # Run the bot
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped due to error: {e}")
