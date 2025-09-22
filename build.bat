@echo off
echo ========================================
echo   Shadow Liquidity Bot - Build Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed
echo.

REM Install Playwright browsers
echo 🌐 Installing Playwright browsers...
playwright install
if errorlevel 1 (
    echo ❌ Failed to install Playwright browsers
    pause
    exit /b 1
)

echo ✅ Playwright browsers installed
echo.

REM Build executable
echo 🚀 Building executable...
python build_exe.py
if errorlevel 1 (
    echo ❌ Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build Complete! 🎉
echo ========================================
echo.
echo Your executable is located at: dist\ShadowLiquidityBot.exe
echo.
echo Next steps:
echo 1. Copy your .env file to the dist\ folder
echo 2. Run the executable: dist\ShadowLiquidityBot.exe
echo.
pause 