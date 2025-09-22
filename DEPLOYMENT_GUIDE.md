# Shadow Liquidity Bot - Production Deployment Guide

## 🚀 Overview

This guide covers deploying the Shadow Liquidity Rebalancing Bot in a production environment with full automation, monitoring, and error recovery capabilities.

## 📋 Pre-Deployment Checklist

### System Requirements
- ✅ Windows 10/11 (64-bit)
- ✅ 8GB+ RAM recommended
- ✅ 10GB+ free disk space
- ✅ Stable internet connection
- ✅ Chrome/Edge browser installed

### Required Credentials
- ✅ Telegram Bot Token from [@BotFather](https://t.me/botfather)
- ✅ Telegram User ID (get from [@userinfobot](https://t.me/userinfobot))
- ✅ MetaMask seed phrase (12 words)
- ✅ MetaMask password
- ✅ Shadow.so account with liquidity pools

## 🔧 Installation Steps

### 1. Download & Extract
```powershell
# Download the latest release
# Extract to: C:\ShadowLiquidityBot\
```

### 2. Configuration Setup
```powershell
# Navigate to bot directory
cd C:\ShadowLiquidityBot\

# Copy configuration template
copy env.example .env

# Edit configuration
notepad .env
```

### 3. Essential Configuration
Edit `.env` file with your settings:

```env
# REQUIRED - Get from @BotFather
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# REQUIRED - Your Telegram User ID
ALLOWED_USER_IDS=123456789
ADMIN_CHAT_IDS=123456789

# REQUIRED - MetaMask credentials
METAMASK_PHRASE=your twelve word seed phrase here
METAMASK_PASSWORD=your_metamask_password

# MONITORING SETTINGS
MONITOR_INTERVAL=60
REBALANCE_THRESHOLD=90
BALANCE_TOLERANCE=2
ENABLE_NOTIFICATIONS=true
```

### 4. Test Installation
```powershell
# Test bot connection
ShadowLiquidityBot.exe --test

# If successful, you should see:
# ✅ Configuration valid
# ✅ Telegram bot connected
# ✅ Browser launch successful
# ✅ MetaMask extension loaded
```

## 🎯 Production Setup

### 1. Windows Service Installation
```powershell
# Run as Administrator
# Install as Windows Service
sc create "ShadowLiquidityBot" binPath="C:\ShadowLiquidityBot\ShadowLiquidityBot.exe" start=auto

# Start the service
sc start ShadowLiquidityBot

# Verify service status
sc query ShadowLiquidityBot
```

### 2. Firewall Configuration
```powershell
# Allow outbound connections (if needed)
netsh advfirewall firewall add rule name="ShadowBot-Out" dir=out action=allow program="C:\ShadowLiquidityBot\ShadowLiquidityBot.exe"
```

### 3. Auto-Start Configuration
- ✅ Service set to start automatically
- ✅ Runs under SYSTEM account
- ✅ Restarts on failure

## 📊 Monitoring & Maintenance

### 1. Log Monitoring
Monitor these log files:
```
logs/shadow_bot.log      - Main application log
logs/errors.log          - Error-specific events
logs/rebalancing.log     - Rebalancing activities
```

### 2. Telegram Notifications
You'll receive notifications for:
- 🔄 Rebalancing started/completed
- ❌ Errors and failures
- 📊 Daily monitoring summaries
- 🔧 System status changes

### 3. Health Checks
```powershell
# Check service status
sc query ShadowLiquidityBot

# View recent logs
Get-Content logs\shadow_bot.log -Tail 50

# Check process
Get-Process -Name "ShadowLiquidityBot" -ErrorAction SilentlyContinue
```

## 🛡️ Security Best Practices

### 1. File Permissions
```powershell
# Secure the bot directory
icacls "C:\ShadowLiquidityBot" /grant:r "SYSTEM:(OI)(CI)F" /inheritance:r
icacls "C:\ShadowLiquidityBot" /grant:r "Administrators:(OI)(CI)F"
```

### 2. Credential Security
- ✅ `.env` file encrypted at rest
- ✅ MetaMask credentials stored securely
- ✅ No credentials in logs
- ✅ User access restricted via `ALLOWED_USER_IDS`

### 3. Network Security
- ✅ Only required outbound connections
- ✅ No inbound ports opened
- ✅ HTTPS-only communications

## 🔄 Backup & Recovery

### 1. Backup Strategy
```powershell
# Create backup script: backup.bat
@echo off
set BACKUP_DIR=C:\Backups\ShadowBot\%date:~-4,4%-%date:~-10,2%-%date:~-7,2%
mkdir "%BACKUP_DIR%"
copy "C:\ShadowLiquidityBot\.env" "%BACKUP_DIR%\"
copy "C:\ShadowLiquidityBot\data\*" "%BACKUP_DIR%\data\"
xcopy "C:\ShadowLiquidityBot\logs" "%BACKUP_DIR%\logs\" /E /I
echo Backup completed to %BACKUP_DIR%
```

### 2. Recovery Procedure
```powershell
# Stop service
sc stop ShadowLiquidityBot

# Restore configuration
copy "C:\Backups\ShadowBot\latest\.env" "C:\ShadowLiquidityBot\"

# Restore data
xcopy "C:\Backups\ShadowBot\latest\data\*" "C:\ShadowLiquidityBot\data\" /Y

# Start service
sc start ShadowLiquidityBot
```

## 📈 Performance Optimization

### 1. System Resources
- **CPU**: 2-4 cores recommended
- **RAM**: 4-8GB allocated
- **Disk**: SSD recommended for logs
- **Network**: Stable 10+ Mbps connection

### 2. Configuration Tuning
```env
# Optimize for your setup
MONITOR_INTERVAL=60          # Balance between responsiveness and resources
MAX_BROWSER_RETRIES=3        # Increase for unstable networks
TRANSACTION_TIMEOUT=120      # Adjust for network conditions
HEADLESS=true               # Reduce resource usage in production
```

## 🚨 Troubleshooting

### Common Issues

#### Bot Not Starting
```powershell
# Check service logs
Get-EventLog -LogName System -Source "Service Control Manager" | Where-Object {$_.Message -like "*ShadowLiquidityBot*"}

# Verify configuration
ShadowLiquidityBot.exe --validate-config
```

#### MetaMask Connection Issues
```powershell
# Check browser processes
Get-Process -Name "chrome", "msedge" -ErrorAction SilentlyContinue

# Verify extension path
dir "C:\ShadowLiquidityBot\metamask_extension"
```

#### Pool Monitoring Not Working
1. Check Telegram bot token validity
2. Verify user ID in `ALLOWED_USER_IDS`
3. Test with `/status` command
4. Check `logs/errors.log` for details

### Emergency Procedures

#### Immediate Stop
```powershell
# Stop service immediately
sc stop ShadowLiquidityBot

# Kill process if needed
taskkill /F /IM "ShadowLiquidityBot.exe"
```

#### Reset Configuration
```powershell
# Backup current config
copy ".env" ".env.backup"

# Reset to defaults
copy "env.example" ".env"

# Edit with correct values
notepad .env
```

## 📞 Support & Maintenance

### Regular Maintenance Tasks
- **Daily**: Check Telegram notifications
- **Weekly**: Review logs for errors
- **Monthly**: Update configuration if needed
- **Quarterly**: Full system backup

### Performance Monitoring
- Monitor CPU/RAM usage
- Check log file sizes
- Verify notification delivery
- Test rebalancing functionality

### Update Procedure
1. Stop the service
2. Backup current installation
3. Replace executable
4. Update configuration if needed
5. Test functionality
6. Restart service

---

## 🎉 Deployment Complete!

Your Shadow Liquidity Bot is now running in production with:

- ✅ **Automated Monitoring** - Continuous pool surveillance
- ✅ **Smart Rebalancing** - Automatic liquidity management
- ✅ **Real-time Alerts** - Telegram notifications
- ✅ **Error Recovery** - Automatic restart capabilities
- ✅ **Comprehensive Logging** - Full audit trail
- ✅ **Security** - User whitelisting and secure credentials

Monitor the Telegram notifications and logs to ensure everything is working correctly. The bot will now automatically manage your liquidity positions according to your configured thresholds.

**⚠️ Important**: Always monitor the bot's activities, especially during the first few days of operation, to ensure it's working as expected with your specific pools and market conditions. 