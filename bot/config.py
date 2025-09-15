import os

# Bot token dari environment variable atau fallback
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8384360540:AAFmWKTMCWxQftIKGswxIEDtMy-YQyYLXy8')
TOKEN = BOT_TOKEN  # Alias for compatibility

# Path to authorized users file
AUTHORIZED_IDS_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user.csv')

# Superuser IDs (can run /sudo and other privileged operations)
SUPERUSER_IDS = [796058175]  # Add superuser IDs as integers

# Log file for command execution
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bot_commands.log')

# Downloads directory
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Downloads')