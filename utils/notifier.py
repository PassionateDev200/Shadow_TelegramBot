from typing import Iterable
from config import config

async def notify_admins(context, message: str):
    """Send a message to all admin chat IDs if notifications are enabled.

    context: telegram.ext.CallbackContext or Application context within handlers
    message: text to send
    """
    if not config.ENABLE_NOTIFICATIONS:
        return
    if not config.ADMIN_CHAT_IDS:
        return
    for chat_id in config.ADMIN_CHAT_IDS:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception:
            # Avoid raising in notifier
            pass
