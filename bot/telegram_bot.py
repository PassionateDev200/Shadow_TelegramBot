from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.commands import Bot
import time
from config import config
from utils.logger import setup_logging

def telegram_bot():
    # Validate configuration before starting
    errors = config.validate_config()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return

    # Logging first
    setup_logging()

    config.print_config()
    
    bot = Bot()
    
    print("Starting bot...")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Build app with timeout settings
            if not config.TELEGRAM_BOT_TOKEN:
                print("Error: TELEGRAM_BOT_TOKEN is not set")
                return
                
            app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).connect_timeout(120).read_timeout(120).write_timeout(120).build()
            
            # Add command handlers
            app.add_handler(CommandHandler("start", bot.start_command))
            app.add_handler(CommandHandler("connect", bot.connect_command))
            app.add_handler(CommandHandler("disconnect", bot.disconnect_command))
            app.add_handler(CommandHandler("add", bot.add_command))
            app.add_handler(CommandHandler("remove", bot.remove_command))
            app.add_handler(CommandHandler("list", bot.list_command))
            app.add_handler(CommandHandler("status", bot.status_command))
            app.add_handler(CommandHandler("set_threshold", bot.set_threshold_command))
            app.add_handler(CommandHandler("set_balance_tolerance", bot.set_balance_tolerance_command))
            app.add_handler(CommandHandler("help", bot.help_command))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
            app.add_error_handler(bot.error)
            
            # Schedule monitoring job - ENABLED
            try:
                print(f"📊 Scheduling monitoring job every {config.MONITOR_INTERVAL} seconds...")
                app.job_queue.run_repeating(bot.monitor_job, interval=config.MONITOR_INTERVAL, first=10)
                print("✅ Background monitoring enabled")
            except Exception as e:
                print(f"❌ Failed to schedule monitor job: {e}")
            
            print("Bot is polling...")
            print("If the bot seems stuck here, check:")
            print("1. Your TELEGRAM_BOT_TOKEN in .env is correct")
            print("2. Your internet connection is working")
            print("3. The bot token is active (try messaging your bot)")
            print("Press Ctrl+C to stop the bot")
            print()
            
            print(f"Starting bot (attempt {attempt + 1}/{max_retries})...")
            app.run_polling(timeout=120, poll_interval=1)
            break  # Success, exit retry loop
            
        except Exception as e:
            print(f"❌ Bot startup failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print("❌ All retry attempts failed. Please check your configuration.")
                return
            print(f"⏳ Retrying in 5 seconds...")
            time.sleep(5)

