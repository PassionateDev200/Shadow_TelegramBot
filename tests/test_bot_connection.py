#!/usr/bin/env python3
"""
Test script to verify Telegram bot token and connection
Run this before starting the main bot to diagnose issues
"""

import asyncio
import sys
from config import config

async def test_bot_connection():
    """Test if the bot token is valid and can connect to Telegram"""
    
    print("=== Bot Connection Test ===")
    
    # Check if config is loaded
    errors = config.validate_config()
    if errors:
        print("❌ Configuration errors found:")
        for error in errors:
            print(f"   - {error}")
        return False
    
    print("✅ Configuration loaded successfully")
    print(f"Bot Username: {config.TELEGRAM_BOT_USERNAME}")
    
    try:
        # Import telegram libraries
        from telegram import Bot
        from telegram.error import TelegramError
        
        print("✅ Telegram libraries imported successfully")
        
        # Create bot instance
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        print("✅ Bot instance created")
        
        # Test connection by getting bot info
        print("🔄 Testing connection to Telegram servers...")
        bot_info = await bot.get_me()
        
        print("✅ Successfully connected to Telegram!")
        print(f"Bot Name: {bot_info.first_name}")
        print(f"Bot Username: @{bot_info.username}")
        print(f"Bot ID: {bot_info.id}")
        
        # Test if bot can send messages (optional)
        print("\n🔄 Testing bot permissions...")
        
        return True
        
    except TelegramError as e:
        print(f"❌ Telegram API Error: {e}")
        print("This usually means:")
        print("  - Invalid bot token")
        print("  - Bot token has been revoked")
        print("  - Network connectivity issues")
        return False
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure python-telegram-bot is installed:")
        print("  pip install python-telegram-bot")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

async def test_network_connectivity():
    """Test basic network connectivity"""
    print("\n=== Network Connectivity Test ===")
    
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            print("🔄 Testing connection to Telegram API...")
            async with session.get("https://api.telegram.org", timeout=10) as response:
                if response.status == 200:
                    print("✅ Can reach Telegram API servers")
                    return True
                else:
                    print(f"⚠️  Telegram API returned status: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Network connectivity test failed: {e}")
        print("Check your internet connection")
        return False

if __name__ == "__main__":
    async def main():
        print("Starting bot diagnostics...\n")
        
        # Test network first
        network_ok = await test_network_connectivity()
        
        # Test bot connection
        bot_ok = await test_bot_connection()
        
        print("\n=== Summary ===")
        if network_ok and bot_ok:
            print("✅ All tests passed! Your bot should work correctly.")
            print("You can now run: python main.py")
        else:
            print("❌ Some tests failed. Please fix the issues above before running the bot.")
            sys.exit(1)
    
    asyncio.run(main())
