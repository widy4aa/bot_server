import os
from dotenv import load_dotenv
from typing import List

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for bot settings"""
    
    # Bot Configuration
    BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # AI Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    AI_TEMPLATE = os.getenv('AI_TEMPLATE') or None
    
    # Server Configuration
    DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', './Downloads')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Security Configuration
    SUPERUSER_IDS = [int(id.strip()) for id in os.getenv('SUPERUSER_IDS', '796058175').split(',') if id.strip()]
    
    # File Paths
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    AUTHORIZED_IDS_FILE_PATH = os.path.join(BASE_DIR, 'user.csv')
    LOG_FILE_PATH = os.path.join(BASE_DIR, 'bot_commands.log')
    
    # Ensure download directory exists
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        os.makedirs(cls.DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(cls.LOG_FILE_PATH), exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return list of missing required values"""
        missing = []
        
        if not cls.BOT_TOKEN:
            missing.append('TELEGRAM_BOT_TOKEN')
            
        # GEMINI_API_KEY is optional but warn
        if not cls.GEMINI_API_KEY:
            missing.append('GEMINI_API_KEY (optional but required for AI features)')
            
        return missing

# For backward compatibility
TOKEN = Config.BOT_TOKEN
BOT_TOKEN = Config.BOT_TOKEN
SUPERUSER_IDS = Config.SUPERUSER_IDS
DOWNLOAD_DIR = Config.DOWNLOAD_DIR
AUTHORIZED_IDS_FILE_PATH = Config.AUTHORIZED_IDS_FILE_PATH
LOG_FILE_PATH = Config.LOG_FILE_PATH
AI_TEMPLATE = Config.AI_TEMPLATE