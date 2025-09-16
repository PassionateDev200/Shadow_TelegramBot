from telegram import Update
from telegram.ext import ContextTypes
import asyncio
import logging

from services.launch_browser import launch_browser
from services.metamask_connect import metamask_connect
from services.shadow_connect import shadow_connect
from services.add_pool import add_pool
from config import config
from utils.notifier import notify_admins
from models.pool import Pool
from utils.state import load_state, save_state

class Bot:
    def __init__(self):
        self.browser = None
        self.pools = []  # simple in-memory list of monitored pools
        
        # Ensure all necessary directories exist before proceeding
        config.ensure_directories()
        
        # Load stored credentials on startup
        self._load_stored_credentials_on_startup()
        
        # Load persisted state
        state = load_state()
        for p in state.get("pools", []):
            try:
                self.pools.append(
                    Pool(
                        link=p["link"],
                        range=p.get("range", ""),
                        token=p.get("token", ""),
                        amount=p.get("amount", 0),
                        upper_range=p.get("upper_range"),
                        lower_range=p.get("lower_range"),
                        owner_chat_id=p.get("owner_chat_id"),
                        last_status=p.get("last_status"),
                        meta=p.get("meta", {}),
                    )
                )
            except Exception:
                logging.exception("Failed to load pool from state")
        
        # Load and apply global settings with defaults
        self.settings = state.get("settings", {})
        # Set default values if not present in settings
        if "threshold" not in self.settings:
            self.settings["threshold"] = 90
        if "balance_tolerance" not in self.settings:
            self.settings["balance_tolerance"] = 2
            
        # Apply settings overrides if any
        try:
            if "REBALANCE_THRESHOLD" in self.settings:
                config.REBALANCE_THRESHOLD = float(self.settings["REBALANCE_THRESHOLD"])
            if "BALANCE_TOLERANCE" in self.settings:
                config.BALANCE_TOLERANCE = float(self.settings["BALANCE_TOLERANCE"])
        except Exception:
            logging.exception("Failed to apply settings overrides")

    def _load_stored_credentials_on_startup(self):
        """Load stored credentials on bot startup"""
        try:
            if self._has_stored_credentials():
                self._load_stored_credentials()
                logging.info("Loaded stored MetaMask credentials on startup")
            else:
                logging.info("No stored MetaMask credentials found")
        except Exception as e:
            logging.error(f"Failed to load credentials on startup: {e}")

    # Authorization helper
    def _is_authorized(self, update: Update) -> bool:
        user = update.effective_user
        if not user:
            return False
        # If no whitelist configured, allow all
        if not config.ALLOWED_USER_IDS:
            return True
        return user.id in config.ALLOWED_USER_IDS

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            if not self._is_authorized(update):
                await update.message.reply_text("Unauthorized.")
                return
            await update.message.reply_text("Hello! I'm your liquidity rebalance automation bot")

    async def connect_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            if not self._is_authorized(update):
                await update.message.reply_text("Unauthorized.")
                return
            
            args = context.args
            
            # Check if credentials are provided (password + 12 words)
            if args and len(args) >= 13:
                password = args[0]
                seed_phrase = " ".join(args[1:13])  # Take next 12 words
                
                # Store credentials in state
                self._store_credentials(password, seed_phrase)
                await update.message.reply_text("✅ MetaMask credentials stored successfully.")
                
            elif self._has_stored_credentials():
                # Use previously stored credentials
                self._load_stored_credentials()
                await update.message.reply_text("✅ Using previously stored MetaMask credentials.")
                
            else:
                await update.message.reply_text("❌ No credentials provided and none stored. Please provide password and 12-word seed phrase.\nUsage: /connect [password] [word1] [word2] ... [word12]")
                return
            
            if self.browser is None:
                await update.message.reply_text("Connecting to Browser...")
                self.browser = await launch_browser()
                await metamask_connect(self.browser)
                await shadow_connect(self.browser)
                await update.message.reply_text("Browser is connected.")
            else:
                await update.message.reply_text("Browser is already connected.")

    def _store_credentials(self, password: str, seed_phrase: str):
        """Store MetaMask credentials in user_profile directory and config"""
        import os
        import json
        
        # Update config for immediate use
        config.METAMASK_PASSWORD = password
        config.METAMASK_PHRASE = seed_phrase
        
        # Update environment variables for current session
        os.environ['METAMASK_PASSWORD'] = password
        os.environ['METAMASK_PHRASE'] = seed_phrase
        
        # Store credentials in user_profile directory for persistence
        try:
            if config.USER_DATA_DIR:
                credentials_file = os.path.join(config.USER_DATA_DIR, 'metamask_credentials.json')
                credentials_data = {
                    "password": password,
                    "seed_phrase": seed_phrase
                }
                
                # Ensure user_profile directory exists
                os.makedirs(config.USER_DATA_DIR, exist_ok=True)
                
                with open(credentials_file, 'w') as f:
                    json.dump(credentials_data, f, indent=2)
                    
                logging.info(f"Credentials stored to {credentials_file}")
            else:
                logging.warning("USER_DATA_DIR not configured, credentials stored in memory only")
        except Exception as e:
            logging.error(f"Failed to store credentials: {e}")
            # Fallback to environment variables only

    def _has_stored_credentials(self):
        """Check if credentials are stored in user_profile directory"""
        import os
        import json
        
        try:
            if not config.USER_DATA_DIR:
                return False
                
            credentials_file = os.path.join(config.USER_DATA_DIR, 'metamask_credentials.json')
            if os.path.exists(credentials_file):
                with open(credentials_file, 'r') as f:
                    data = json.load(f)
                    return bool(data.get("password") and data.get("seed_phrase"))
        except Exception as e:
            logging.error(f"Failed to check stored credentials: {e}")
        
        return False

    def _load_stored_credentials(self):
        """Load stored credentials from user_profile directory"""
        import os
        import json
        
        try:
            if not config.USER_DATA_DIR:
                return False
                
            credentials_file = os.path.join(config.USER_DATA_DIR, 'metamask_credentials.json')
            if os.path.exists(credentials_file):
                with open(credentials_file, 'r') as f:
                    data = json.load(f)
                    
                password = data.get("password")
                seed_phrase = data.get("seed_phrase")
                
                if password and seed_phrase:
                    # Update config and environment
                    config.METAMASK_PASSWORD = password
                    config.METAMASK_PHRASE = seed_phrase
                    os.environ['METAMASK_PASSWORD'] = password
                    os.environ['METAMASK_PHRASE'] = seed_phrase
                    return True
        except Exception as e:
            logging.error(f"Failed to load stored credentials: {e}")
            
        return False

    def _clear_stored_credentials(self):
        """Clear stored credentials from user_profile directory"""
        import os
        
        # Clear from environment
        if 'METAMASK_PASSWORD' in os.environ:
            del os.environ['METAMASK_PASSWORD']
        if 'METAMASK_PHRASE' in os.environ:
            del os.environ['METAMASK_PHRASE']
            
        # Clear from config
        config.METAMASK_PASSWORD = ''
        config.METAMASK_PHRASE = ''
        
        # Remove credentials file from user_profile directory
        try:
            if config.USER_DATA_DIR:
                credentials_file = os.path.join(config.USER_DATA_DIR, 'metamask_credentials.json')
                if os.path.exists(credentials_file):
                    os.remove(credentials_file)
                    logging.info(f"Removed credentials file: {credentials_file}")
        except Exception as e:
            logging.error(f"Failed to remove credentials file: {e}")

    async def disconnect_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            if not self._is_authorized(update):
                await update.message.reply_text("Unauthorized.")
                return
            if self.browser is not None:
                await self.browser.close()
                self.browser = None
                # Clear all pools when disconnecting
                pools_count = len(self.pools)
                self.pools = []
                # Reset settings to default values
                self.settings = {
                    "threshold": 90,
                    "balance_tolerance": 2
                }
                # Reset config values to defaults as well
                config.REBALANCE_THRESHOLD = 90
                config.BALANCE_TOLERANCE = 2
                # Clear stored credentials
                self._clear_stored_credentials()
                # Save the cleared state with default settings
                save_state(self.pools, self.settings)
                await update.message.reply_text(f"Browser is disconnected. Cleared {pools_count} pool(s) from monitoring. Settings and credentials reset to defaults.")
            else:
                await update.message.reply_text("Browser is not connected.")

    async def add_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            if not self._is_authorized(update):
                await update.message.reply_text("Unauthorized.")
                return
            
            # Check if MetaMask credentials are available before proceeding
            if not self._has_stored_credentials():
                await update.message.reply_text("❌ MetaMask credentials not found. Please use /connect first with your password and 12-word seed phrase.\nUsage: /connect [password] [word1] [word2] ... [word12]")
                return
                
            await update.message.reply_text("Starting add flow…")
            args = context.args
            if self.browser is None:
                # Load stored credentials before launching browser
                self._load_stored_credentials()
                self.browser = await launch_browser()
                await metamask_connect(self.browser)
            if args:
                try:
                    ok, pool_info = await add_pool(update, self.browser, args)
                    if ok:
                        # Track monitored pools as dataclass
                        pool = Pool(
                            link=pool_info["link"],
                            range=pool_info["range"],
                            token=pool_info["token"],
                            amount=pool_info["amount"],
                            upper_range=pool_info.get("upper_range"),
                            lower_range=pool_info.get("lower_range"),
                            owner_chat_id=update.effective_chat.id if update.effective_chat else None,
                        )
                        self.pools.append(pool)
                        save_state(self.pools, self.settings)
                        await update.message.reply_text("✅ Pool added and being monitored.")
                    else:
                        await update.message.reply_text("❌ Failed to add pool.")
                except Exception as e:
                    logging.exception("/add failed")
                    await update.message.reply_text(f"❌ Error: {e}")
                    await notify_admins(context, f"/add error from {update.effective_user.id}: {e}")
            else:
                await update.message.reply_text("Give Pool Link")

    async def remove_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            if not self._is_authorized(update):
                await update.message.reply_text("Unauthorized.")
                return
            args = context.args
            if not args:
                await update.message.reply_text("Usage: /remove [pool link]")
                return
            link = args[0]
            before = len(self.pools)
            self.pools = [p for p in self.pools if p.link != link]
            after = len(self.pools)
            if after < before:
                save_state(self.pools, self.settings)
                await update.message.reply_text("✅ Removed.")
            else:
                await update.message.reply_text("Not found.")

    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            if not self._is_authorized(update):
                await update.message.reply_text("Unauthorized.")
                return
            if not self.pools:
                await update.message.reply_text("No pools are being monitored.")
                return
            lines = [
                "Monitored pools:",
                f"📊 Global Settings: Threshold={self.settings['threshold']}% | Tolerance={self.settings['balance_tolerance']}%",
                ""
            ]
            for i, p in enumerate(self.pools, 1):
                range_info = f"range={p.range}"
                if p.upper_range is not None and p.lower_range is not None:
                    range_info += f" (${p.lower_range:.4f}-${p.upper_range:.4f})"
                lines.append(f"{i}. {p.link} | {range_info} | token={p.token} | amount={p.amount} | status={p.last_status or '-'}")
            await update.message.reply_text("\n".join(lines))

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            if not self._is_authorized(update):
                await update.message.reply_text("Unauthorized.")
                return
            if not self.pools:
                await update.message.reply_text("No pools are being monitored.")
                return
            
            # Check if MetaMask credentials are available before proceeding
            if not self._has_stored_credentials():
                await update.message.reply_text("❌ MetaMask credentials not found. Please use /connect first with your password and 12-word seed phrase.\nUsage: /connect [password] [word1] [word2] ... [word12]")
                return
                
            # Ensure browser exists
            if self.browser is None:
                # Load stored credentials before launching browser
                self._load_stored_credentials()
                self.browser = await launch_browser()
                await metamask_connect(self.browser)
            await update.message.reply_text("Checking status…")
            # Check first pool (or all?) – we'll check all and summarize
            results = []
            for p in self.pools:
                status = await check_status(self.browser, p)
                p.last_status = status
                results.append(f"{p.link} -> {status}")
            await update.message.reply_text("\n".join(results))

    async def set_threshold_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            if not self._is_authorized(update):
                await update.message.reply_text("Unauthorized.")
                return
            args = context.args
            if not args:
                await update.message.reply_text(f"Current threshold: {self.settings['threshold']}%\nUsage: /set_threshold [percent]")
                return
            try:
                val = float(args[0])
                if val < 1 or val > 100:
                    raise ValueError("out of range")
                self.settings["threshold"] = float(val)
                # Also update config for backwards compatibility
                config.REBALANCE_THRESHOLD = float(val)
                save_state(self.pools, self.settings)
                await update.message.reply_text(f"✅ Global threshold set to {val}%.")
            except Exception:
                await update.message.reply_text("Invalid value. Provide a number 1-100.")

    async def set_balance_tolerance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            if not self._is_authorized(update):
                await update.message.reply_text("Unauthorized.")
                return
            args = context.args
            if not args:
                await update.message.reply_text(f"Current tolerance: {self.settings['balance_tolerance']}%\nUsage: /set_balance_tolerance [percent]")
                return
            try:
                val = float(args[0])
                if val < 0 or val > 100:
                    raise ValueError("out of range")
                self.settings["balance_tolerance"] = val
                # Also update config for backwards compatibility
                config.BALANCE_TOLERANCE = val
                save_state(self.pools, self.settings)
                await update.message.reply_text(f"✅ Global balance tolerance set to {val}%.")
            except Exception:
                await update.message.reply_text("Invalid value. Provide a number 0-100.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            if not self._is_authorized(update):
                await update.message.reply_text("Unauthorized.")
                return
            txt = """○ /connect [password] [12-word seed phrase] — Connect browser (credentials required only first time)
○ /disconnect — Disconnect browser and clear all data including stored credentials
○ /add [pool_link] [range_type] [token] [amount] — Add a pool link to monitor
○ /remove [link] — Remove a pool link
○ /list — List all monitored pools and global settings
○ /status — Force status check and update
○ /set_threshold [value] — Set global rebalance trigger threshold (default: 90%)
○ /set_balance_tolerance [value] — Set global balance tolerance (default: 2%)
○ /help — List available commands
"""
            await update.message.reply_text(txt)


    def handle_response(self, text):
        if "add" in text:
            return "Add command received"
        elif "remove" in text:
            return "Remove command received"
        elif "list" in text:
            return "List command received"
        elif "set_threshold" in text:
            return "Set threshold command received"
        elif "set_balance_tolerance" in text:
            return "Set balance tolerance command received"
        elif "help" in text:
            return "Help command received"
        else:
            return "Unknown command"

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            if not self._is_authorized(update):
                return
            text = update.message.text
            response = self.handle_response(text)
            await update.message.reply_text(response)

    async def error(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        logging.exception("Update error: %s", context.error)
        try:
            await notify_admins(context, f"Bot error: {context.error}")
        except Exception:
            pass

    # Background monitor job (placeholder)
    async def monitor_job(self, context: ContextTypes.DEFAULT_TYPE):
        if not self.pools:
            return
        
        # Check if MetaMask credentials are available before proceeding
        if not self._has_stored_credentials():
            await notify_admins(context, "❌ Monitor: MetaMask credentials not found. Please use /connect first.")
            return
            
        # Ensure browser exists
        if self.browser is None:
            try:
                # Load stored credentials before launching browser
                self._load_stored_credentials()
                self.browser = await launch_browser()
                await metamask_connect(self.browser)
            except Exception as e:
                logging.exception("Failed to (re)launch browser for monitoring")
                await notify_admins(context, f"Monitor: failed to launch browser: {e}")
                return
        logging.info("Monitoring %d pools", len(self.pools))
        for pool in list(self.pools):
            try:
                changed, status = await check_and_rebalance(self.browser, pool, context)
                pool.last_status = status
            except Exception as e:
                logging.exception("Monitoring error for %s", pool.link)
                await notify_admins(context, f"Monitor error for {pool.link}: {e}")


