import os
import sys
from dotenv import load_dotenv
from typing import List

# Load environment variables from .env file
load_dotenv()

def get_base_dir():
    """Get the base directory for the application (handles both development and executable)"""
    if getattr(sys, 'frozen', False):
        # Running as executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

class Config:
    """Configuration class to manage all application settings"""
    
    # Get base directory
    BASE_DIR = get_base_dir()
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME', '@liquidity_rebalance_bot')
    
    # MetaMask Configuration (will be set dynamically via /connect command)
    METAMASK_PHRASE = os.getenv('METAMASK_PHRASE', '')
    METAMASK_PASSWORD = os.getenv('METAMASK_PASSWORD', '')
    
    # Browser Configuration with fallbacks
    EXTENSION_PATH = os.getenv('EXTENSION_PATH') or os.path.join(BASE_DIR, 'metamask_extension')
    USER_DATA_DIR = os.getenv('USER_DATA_DIR') or os.path.join(BASE_DIR, 'user_profile')
    
    # Browser Settings
    HEADLESS = os.getenv('HEADLESS', 'false').lower() == 'true'
    START_MAXIMIZED = os.getenv('START_MAXIMIZED', 'true').lower() == 'true'
    COLOR_SCHEME = os.getenv('COLOR_SCHEME', 'dark')
    
    # Pool Configuration
    DEFAULT_RANGE_TYPES = os.getenv('DEFAULT_RANGE_TYPES', 'passive,wide,narrow,aggressive,insane').split(',')
    SHADOW_BASE_URL = os.getenv('SHADOW_BASE_URL', 'https://www.shadow.so/liquidity/')
    
    # Monitoring Settings
    POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '1'))
    REBALANCE_THRESHOLD = float(os.getenv('REBALANCE_THRESHOLD', '90'))
    BALANCE_TOLERANCE = float(os.getenv('BALANCE_TOLERANCE', '2'))
    MONITOR_INTERVAL = int(os.getenv('MONITOR_INTERVAL', '30'))

    # Security & Notifications
    # Comma-separated list of Telegram user IDs allowed to use the bot. If empty, allow all.
    ALLOWED_USER_IDS = [
        int(x) for x in os.getenv('ALLOWED_USER_IDS', '').split(',') if x.strip().isdigit()
    ]
    # Admin chat IDs to receive alerts/notifications
    ADMIN_CHAT_IDS = [
        int(x) for x in os.getenv('ADMIN_CHAT_IDS', '').split(',') if x.strip().isdigit()
    ]
    ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'true').lower() == 'true'

    # Logging
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        directories_to_create = [
            cls.USER_DATA_DIR,
            os.path.join(cls.BASE_DIR, 'data'),
            cls.LOG_DIR if os.path.isabs(cls.LOG_DIR) else os.path.join(cls.BASE_DIR, cls.LOG_DIR)
        ]
        
        for directory in directories_to_create:
            if directory:
                try:
                    os.makedirs(directory, exist_ok=True)
                    print(f"✅ Directory ensured: {directory}")
                except Exception as e:
                    print(f"❌ Failed to create directory {directory}: {e}")
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate that all required configuration values are set"""
        # First ensure directories exist
        cls.ensure_directories()
        
        errors = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        # MetaMask credentials are optional - provided via /connect command
        # if not cls.METAMASK_PHRASE:
        #     errors.append("METAMASK_PHRASE is required")
            
        # if not cls.METAMASK_PASSWORD:
        #     errors.append("METAMASK_PASSWORD is required")
            
        # Extension path is now optional with fallback
        # if not cls.EXTENSION_PATH:
        #     errors.append("EXTENSION_PATH is required")
            
        # User data dir is now optional with fallback
        # if not cls.USER_DATA_DIR:
        #     errors.append("USER_DATA_DIR is required")
            
        # Check if extension path exists (create if doesn't exist)
        if cls.EXTENSION_PATH and not os.path.exists(cls.EXTENSION_PATH):
            errors.append(f"EXTENSION_PATH does not exist: {cls.EXTENSION_PATH}")
            
        return errors
    
    @classmethod
    def print_config(cls):
        """Print current configuration (hiding sensitive data)"""
        print("=== Configuration ===")
        print(f"Bot Username: {cls.TELEGRAM_BOT_USERNAME}")
        print(f"Extension Path: {cls.EXTENSION_PATH}")
        print(f"User Data Dir: {cls.USER_DATA_DIR}")
        print(f"Headless: {cls.HEADLESS}")
        print(f"Range Types: {cls.DEFAULT_RANGE_TYPES}")
        print(f"Poll Interval: {cls.POLL_INTERVAL}")
        print(f"Monitor Interval: {cls.MONITOR_INTERVAL}s")
        print(f"Rebalance Threshold: {cls.REBALANCE_THRESHOLD}%")
        print(f"Balance Tolerance: {cls.BALANCE_TOLERANCE}%")
        print(f"Allowed Users: {cls.ALLOWED_USER_IDS if cls.ALLOWED_USER_IDS else 'ALL'}")
        print(f"Admin Chat IDs: {cls.ADMIN_CHAT_IDS}")
        print(f"Log Dir: {cls.LOG_DIR}")
        print("====================")

# Create a global config instance
config = Config()
