# liqbot

instructions to set up and run the Telegram bot that automates liquidity actions with a MetaMask browser profile.

## Overview
- Entry point: `main.py` runs `telegram_bot()`.
- Configuration is via `.env` (see `.env.example`).
- Uses a bundled MetaMask extension at `metamask_extension/` by default.

## Prerequisites
- Python 3.10+ (recommended 3.11)
- Google Chrome or Microsoft Edge installed
- A Telegram Bot token from @BotFather

## Quick start (Windows)
1. Clone the repo.
2. Create and activate a virtual environment:
   - PowerShell:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - CMD:
     ```bat
     python -m venv .venv
     .\.venv\Scripts\activate.bat
     ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Create your env file:
   ```powershell
   copy .env.example .env
   ```
   Edit `.env` and set at least:
   - `TELEGRAM_BOT_TOKEN`
   - Optional: `TELEGRAM_BOT_USERNAME`
   - Optional: adjust `EXTENSION_PATH` and `USER_DATA_DIR` if you need custom locations

   Notes:
   - By default, `EXTENSION_PATH` falls back to `metamask_extension/` inside the project.
   - `USER_DATA_DIR` defaults to `user_profile/` inside the project and will be created if missing.

5. Run the bot:
   ```powershell
   python main.py
   ```

## Quick start (macOS/Linux)
1. Create venv and install deps:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
2. Edit `.env` and set `TELEGRAM_BOT_TOKEN`.
3. Run:
   ```bash
   python3 main.py
   ```

## Environment variables
See `.env.example` for the full list. Important keys:
- `TELEGRAM_BOT_TOKEN` (required)
- `TELEGRAM_BOT_USERNAME` (optional)
- `METAMASK_PHRASE`, `METAMASK_PASSWORD` (optional; can be provided via bot flow)
- `EXTENSION_PATH` (optional; defaults to `metamask_extension/`)
- `USER_DATA_DIR` (optional; defaults to `user_profile/`)
- `HEADLESS`, `START_MAXIMIZED`, `COLOR_SCHEME` (browser behavior)

## Notes
- First run will create required directories (see `config.Config.ensure_directories()` in `config.py`).
- If you see an error about `EXTENSION_PATH` not existing, ensure the `metamask_extension/` directory is present or set a valid path in `.env`.
- The project uses Selenium/undetected-chromedriver and Playwright is present in requirements for potential future use. Chrome/Edge must be installed.

## Troubleshooting
See `TROUBLESHOOTING.md` for common issues and fixes.
