from typing import Iterable
from config import config
import logging
import asyncio
from datetime import datetime

async def notify_admins(context, message: str, parse_mode=None):
    """Enhanced admin notification system with better error handling and formatting.

    context: telegram.ext.CallbackContext or Application context within handlers
    message: text to send
    parse_mode: 'HTML' or 'Markdown' for formatted messages
    """
    if not config.ENABLE_NOTIFICATIONS:
        logging.debug("Notifications disabled, skipping admin notification")
        return
        
    if not config.ADMIN_CHAT_IDS:
        logging.debug("No admin chat IDs configured, skipping notification")
        return
    
    # Add timestamp to message
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {message}"
    
    # Limit message length to avoid Telegram limits
    if len(formatted_message) > 4000:
        formatted_message = formatted_message[:3900] + "... (truncated)"
    
    successful_sends = 0
    failed_sends = 0
    
    for chat_id in config.ADMIN_CHAT_IDS:
        try:
            await context.bot.send_message(
                chat_id=chat_id, 
                text=formatted_message,
                parse_mode=parse_mode,
                disable_web_page_preview=True
            )
            successful_sends += 1
            logging.debug(f"Notification sent to admin {chat_id}")
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
            
        except Exception as e:
            failed_sends += 1
            logging.warning(f"Failed to send notification to admin {chat_id}: {e}")
    
    if failed_sends > 0:
        logging.warning(f"Notification delivery: {successful_sends} successful, {failed_sends} failed")

async def notify_user(context, chat_id: int, message: str, parse_mode=None):
    """Send notification to a specific user with error handling.
    
    context: telegram.ext.CallbackContext or Application context
    chat_id: Target user's chat ID
    message: Message to send
    parse_mode: 'HTML' or 'Markdown' for formatted messages
    """
    try:
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Limit message length
        if len(formatted_message) > 4000:
            formatted_message = formatted_message[:3900] + "... (truncated)"
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=formatted_message,
            parse_mode=parse_mode,
            disable_web_page_preview=True
        )
        logging.debug(f"Notification sent to user {chat_id}")
        return True
        
    except Exception as e:
        logging.warning(f"Failed to send notification to user {chat_id}: {e}")
        return False

async def notify_rebalance_start(context, pool_id: str, current_price: float, bounds: tuple):
    """Send formatted notification when rebalancing starts"""
    message = f"""🔄 **REBALANCING STARTED**
Pool ID: `{pool_id}`
Current Price: ${current_price:,.2f}
Range: ${bounds[0]:,.2f} - ${bounds[1]:,.2f}
Status: Removing liquidity..."""
    
    await notify_admins(context, message, parse_mode='Markdown')

async def notify_rebalance_complete(context, pool_id: str, duration_seconds: int):
    """Send formatted notification when rebalancing completes"""
    message = f"""✅ **REBALANCING COMPLETED**
Pool ID: `{pool_id}`
Duration: {duration_seconds}s
Status: Liquidity re-added successfully"""
    
    await notify_admins(context, message, parse_mode='Markdown')

async def notify_rebalance_error(context, pool_id: str, error: str, step: str):
    """Send formatted notification when rebalancing fails"""
    message = f"""❌ **REBALANCING FAILED**
Pool ID: `{pool_id}`
Step: {step}
Error: {error[:200]}
Status: Manual intervention may be required"""
    
    await notify_admins(context, message, parse_mode='Markdown')

async def notify_system_status(context, status: str, details: str = ""):
    """Send system status notifications"""
    emoji_map = {
        "online": "🟢",
        "offline": "🔴", 
        "warning": "🟡",
        "error": "❌",
        "maintenance": "🔧"
    }
    
    emoji = emoji_map.get(status.lower(), "ℹ️")
    message = f"{emoji} **SYSTEM STATUS: {status.upper()}**"
    
    if details:
        message += f"\nDetails: {details}"
    
    await notify_admins(context, message, parse_mode='Markdown')
