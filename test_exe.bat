@echo off
echo ========================================
echo   Testing Shadow Liquidity Bot EXE
echo ========================================
echo.

cd dist

echo 📁 Current directory: %CD%
echo 📋 Files in directory:
dir /b

echo.
echo 🚀 Executable info:
echo File: ShadowLiquidityBot.exe
for %%A in (ShadowLiquidityBot.exe) do echo Size: %%~zA bytes

echo.
echo ✅ Executable built successfully!
echo.
echo 📋 To run the bot:
echo 1. Make sure you have a .env file in this directory
echo 2. Run: ShadowLiquidityBot.exe
echo.
echo 🔧 Configuration needed in .env:
echo TELEGRAM_BOT_TOKEN=your_bot_token_here
echo ALLOWED_USER_IDS=your_user_id_here
echo USER_DATA_DIR=./user_profile
echo.
pause 