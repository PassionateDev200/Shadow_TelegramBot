# Shadow Liquidity Rebalancing Bot

**Automated liquidity management bot for Shadow.so with Telegram interface and MetaMask integration.**

## 🚀 Features

### Core Automation
- ✅ **Continuous Pool Monitoring** - Automatically tracks multiple liquidity pools
- ✅ **Smart Rebalancing** - Detects approaching out-of-range conditions
- ✅ **Complete Workflow** - Remove → Rebalance → Re-add liquidity automatically
- ✅ **MetaMask Integration** - Seamless transaction confirmations
- ✅ **Real-time Notifications** - Telegram alerts for all activities

### Telegram Bot Commands
- `/connect [password] [12-word seed phrase]` — Connect MetaMask wallet
- `/disconnect` — Disconnect and clear credentials
- `/add [pool_link] [range_type] [token] [amount]` — Add pool for monitoring
- `/remove [link]` — Remove liquidity (100% withdrawal)
- `/list` — List all monitored pools with status
- `/status` — Force status check and update
- `/set_threshold [value]` — Set rebalance trigger threshold (default: 90%)
- `/set_balance_tolerance [value]` — Set balance tolerance (default: 2%)
- `/help` — Show available commands

### Security & Management
- ✅ **User Whitelisting** - Only authorized users can control the bot
- ✅ **Admin Notifications** - Real-time alerts for errors and activities
- ✅ **Comprehensive Logging** - Detailed logs with rotation
- ✅ **Error Recovery** - Automatic browser restart and error handling

## 📋 Prerequisites

- **Python 3.10+** (recommended 3.11)
- **Google Chrome or Microsoft Edge** installed
- **Telegram Bot Token** from [@BotFather](https://t.me/botfather)
- **MetaMask wallet** with seed phrase and password

## 🚀 Quick Start (Windows)

1. **Clone and setup:**
   ```powershell
   git clone <repository>
   cd shadow-liquidity-bot
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```powershell
   playwright install
   ```

3. **Configure environment:**
   ```powershell
   copy .env.example .env
   ```
   
   Edit `.env` and set:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ALLOWED_USER_IDS=your_telegram_user_id
   ADMIN_CHAT_IDS=your_telegram_user_id
   ENABLE_NOTIFICATIONS=true
   MONITOR_INTERVAL=60
   ```

4. **Run the bot:**
   ```powershell
   python main.py
   ```

## 🔧 Configuration

### Required Settings
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `ALLOWED_USER_IDS` - Comma-separated list of authorized user IDs
- `ADMIN_CHAT_IDS` - User IDs to receive notifications

### Optional Settings
- `MONITOR_INTERVAL=60` - Pool monitoring frequency (seconds)
- `REBALANCE_THRESHOLD=90` - Trigger threshold percentage
- `BALANCE_TOLERANCE=2` - Token balance tolerance percentage
- `HEADLESS=false` - Run browser in headless mode
- `ENABLE_NOTIFICATIONS=true` - Enable Telegram notifications

### Advanced Settings
- `MAX_BROWSER_RETRIES=3` - Browser restart attempts
- `TRANSACTION_TIMEOUT=120` - Transaction timeout (seconds)
- `MAX_REBALANCE_RETRIES=2` - Rebalancing retry attempts

## 🎯 How It Works

### 1. Pool Monitoring
- Continuously checks pool status every 60 seconds
- Detects when price approaches range boundaries
- Monitors multiple pools simultaneously

### 2. Automated Rebalancing
When a pool approaches the threshold:
1. **Remove Liquidity** - Withdraws 100% from the pool
2. **Check Balances** - Analyzes token balance ratios
3. **Rebalance Tokens** - Swaps tokens if needed to balance values
4. **Re-add Liquidity** - Deposits balanced liquidity back to pool

### 3. Notifications
- 🔄 Rebalancing started
- ✅ Rebalancing completed
- ❌ Errors and failures
- 📊 Monitoring summaries

## 📦 Building Executable

### Quick Build
```bash
# Using batch file (Windows)
build.bat

# Or manually
python build_exe.py
```

### Output
- `dist/ShadowLiquidityBot.exe` - Standalone executable
- No Python installation required on target machine
- Copy `.env` file alongside the executable
- Move `metamask_extension` directory to `dist`

## 📊 Monitoring & Logs

### Log Files
- `logs/shadow_bot.log` - Main application log
- `logs/errors.log` - Error-specific log
- `logs/rebalancing.log` - Rebalancing activity log

### Real-time Monitoring
- Telegram notifications for all activities
- Console output with timestamps
- Structured logging with rotation

## 🔍 Troubleshooting

### Common Issues
- **Bot not responding**: Check `TELEGRAM_BOT_TOKEN`
- **Browser launch failed**: Run `playwright install`
- **MetaMask connection issues**: Verify extension path
- **Pool monitoring not working**: Check credentials with `/connect`

### Debug Mode
Set environment variables:
```env
HEADLESS=false
LOG_LEVEL=DEBUG
```

## 🛡️ Security

- **Credential Storage** - Encrypted local storage
- **User Whitelisting** - Only authorized users
- **Admin Notifications** - Real-time security alerts
- **Error Handling** - Graceful failure recovery

## 📈 Performance

- **Efficient Monitoring** - 60-second intervals
- **Resource Management** - Browser process optimization
- **Error Recovery** - Automatic restart capabilities
- **Scalable** - Handles multiple pools simultaneously

## 🔄 Updates & Maintenance

The bot includes:
- Automatic error recovery
- Browser restart on failures
- Comprehensive logging
- Real-time status monitoring

For ongoing support and updates, monitor the logs and Telegram notifications.

---

**⚠️ Important**: This bot handles real cryptocurrency transactions. Always test with small amounts first and ensure you understand the risks involved.
