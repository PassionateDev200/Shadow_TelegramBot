# Troubleshooting Guide

## Bot Stuck at "Bot is polling..."

If your bot gets stuck at the "Bot is polling..." message, here are the most common causes and solutions:

### 1. **Invalid Bot Token** (Most Common)
**Symptoms:** Bot hangs at polling, no error messages
**Solution:**
- Check your `.env` file has the correct `TELEGRAM_BOT_TOKEN`
- Token format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
- Get a new token from [@BotFather](https://t.me/botfather) if needed

**Test:** Run `python test_bot_connection.py` to verify your token

### 2. **Network Connectivity Issues**
**Symptoms:** Bot hangs, timeout errors
**Solution:**
- Check your internet connection
- Try: `curl https://api.telegram.org`
- Check if you're behind a firewall/proxy

### 3. **Missing Dependencies**
**Symptoms:** Import errors, module not found
**Solution:**
```bash
pip install -r requirements.txt
# or specifically:
pip install python-telegram-bot python-dotenv
```

### 4. **Configuration Issues**
**Symptoms:** Configuration errors on startup
**Solution:**
- Copy `.env.example` to `.env`
- Fill in all required values
- Update paths to match your system

### 5. **Bot Token Revoked/Inactive**
**Symptoms:** API errors, unauthorized errors
**Solution:**
- Message your bot directly on Telegram
- If no response, regenerate token with @BotFather

## Quick Diagnostic Steps

1. **Run the test script:**
   ```bash
   python test_bot_connection.py
   ```

2. **Check configuration:**
   ```bash
   python -c "from config import config; print(config.validate_config())"
   ```

3. **Test network connectivity:**
   ```bash
   curl -s "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
   ```

4. **Check bot status on Telegram:**
   - Open Telegram
   - Search for your bot username
   - Send `/start` command
   - If no response, token is likely invalid

## Common Error Messages

- **`Unauthorized`**: Invalid bot token
- **`Conflict: terminated by other getUpdates request`**: Bot running elsewhere
- **`Network is unreachable`**: Internet/firewall issues
- **`Timeout`**: Slow network or server issues

## Getting Help

If you're still having issues:
1. Run `python test_bot_connection.py` and share the output
2. Check the bot logs for specific error messages
3. Verify your `.env` file has all required values (don't share the actual token!)
