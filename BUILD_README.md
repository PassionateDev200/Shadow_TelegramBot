# Shadow Liquidity Bot - Executable Build Guide

## 🚀 Quick Build (Recommended)

### Option 1: Using Batch File (Windows)
1. Double-click `build.bat`
2. Wait for the build to complete
3. Your executable will be in the `dist/` folder

### Option 2: Manual Build
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Playwright browsers:
   ```bash
   playwright install
   ```

3. Build the executable:
   ```bash
   python build_exe.py
   ```

## 📁 Output

After building, you'll find:
- `dist/ShadowLiquidityBot.exe` - Your executable file
- The executable is self-contained and doesn't need Python installed on the target machine

## 🔧 Configuration

1. Copy your `.env` file to the same directory as the executable
2. Ensure your `.env` contains:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ALLOWED_USER_IDS=your_user_id_here
   USER_DATA_DIR=./user_profile
   ```

## 📋 Requirements

### For Building:
- Python 3.8+
- All dependencies in `requirements.txt`
- Playwright browsers

### For Running the Executable:
- Windows 10/11
- Internet connection
- Valid Telegram bot token
- MetaMask credentials (provided via /connect command)

## 🎯 Features Included

The executable includes:
- ✅ Telegram bot interface
- ✅ Browser automation (Playwright)
- ✅ MetaMask integration
- ✅ Shadow.so liquidity management
- ✅ 100% withdrawal functionality
- ✅ Pool monitoring
- ✅ Credential storage

## 🔍 Troubleshooting

### Build Issues:
- **"Python not found"**: Install Python and add to PATH
- **"Module not found"**: Run `pip install -r requirements.txt`
- **"Playwright browsers missing"**: Run `playwright install`

### Runtime Issues:
- **"Bot token invalid"**: Check your `.env` file
- **"Browser launch failed"**: Ensure Playwright browsers are installed
- **"Permission denied"**: Run as administrator

## 📦 Build Options

### Console Version (shows logs):
Edit `build_exe.py` and remove the `--windowed` flag

### Debug Version:
Add `--debug` flag to PyInstaller command in `build_exe.py`

### Smaller Executable:
Remove `--onefile` flag to create a folder distribution instead

## 🔄 Clean Build

To clean build artifacts:
```bash
python build_exe.py clean
```

## 📊 Expected File Sizes

- Executable: ~80-120 MB (includes Python runtime and all dependencies)
- With Playwright: Additional ~200-300 MB for browser binaries

## 🚀 Distribution

The executable is portable and can be:
- Copied to other Windows machines
- Run without Python installation
- Distributed as a single file

Just remember to include:
- The `.env` configuration file
- Any custom configuration files
- Ensure target machines have internet access 