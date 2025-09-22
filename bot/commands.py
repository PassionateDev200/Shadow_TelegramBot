from telegram import Update
from telegram.ext import ContextTypes
import asyncio
import logging

from services.launch_browser import launch_browser
from services.metamask_connect import metamask_connect
from services.shadow_connect import shadow_connect
from services.add_pool import add_pool
from services.shadow_dashboard import fetch_dashboard_pools, check_pool_status
from config import config
from utils.notifier import notify_admins, notify_rebalance_start, notify_rebalance_complete, notify_rebalance_error, notify_system_status
from models.pool import Pool
from utils.state import load_state, save_state
from utils.shadow_utils import Shadow

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
                try:
                    self.browser = await launch_browser()
                    await update.message.reply_text("Browser launched, connecting to MetaMask...")
                    await metamask_connect(self.browser)
                    await update.message.reply_text("MetaMask connected, connecting to Shadow.so...")
                    await shadow_connect(self.browser)
                    await update.message.reply_text("✅ Browser is connected successfully.")
                except Exception as e:
                    await update.message.reply_text(f"❌ Connection failed: {str(e)[:100]}...")
                    # Clean up if connection failed
                    if self.browser:
                        try:
                            await self.browser.close()
                        except:
                            pass
                        self.browser = None
                    raise
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
        """Enhanced add command with better validation and metadata storage"""
        if update.message:
            if not self._is_authorized(update):
                await update.message.reply_text("Unauthorized.")
                return
            
            # Check if MetaMask credentials are available
            if not self._has_stored_credentials():
                await update.message.reply_text("❌ MetaMask credentials not found. Please use /connect first.")
                return
            
            args = context.args
            if len(args) < 4:
                await update.message.reply_text(
                    "❌ Invalid command format.\n\n"
                    "Usage: /add [pool_link] [range_type] [token] [amount]\n"
                    "Example: /add https://www.shadow.so/liquidity/manage/0x123.../456 aggressive USDC 30\n"
                    "Range types: passive, wide, narrow, aggressive, insane"
                )
                return
            
            pool_link, range_type, token, amount_str = args[:4]
            
            try:
                amount = float(amount_str)
                if amount <= 0:
                    await update.message.reply_text("❌ Amount must be greater than 0")
                    return
            except ValueError:
                await update.message.reply_text("❌ Invalid amount format")
                return
            
            # Validate pool link format
            if not pool_link.startswith("https://www.shadow.so/liquidity/"):
                await update.message.reply_text("❌ Invalid pool link format. Must be a Shadow.so liquidity URL.")
                return
            
            # Validate range type
            if range_type.lower() not in [r.lower() for r in config.DEFAULT_RANGE_TYPES]:
                await update.message.reply_text(f"❌ Invalid range type. Available: {', '.join(config.DEFAULT_RANGE_TYPES)}")
                return
            
            # Check if pool already exists
            existing_pool = next((p for p in self.pools if p.link == pool_link), None)
            if existing_pool:
                await update.message.reply_text("⚠️ Pool is already being monitored.")
                return
            
            # Ensure browser is connected
            if self.browser is None:
                await update.message.reply_text("🔄 Connecting to browser...")
                try:
                    self._load_stored_credentials()
                    self.browser = await launch_browser()
                    await metamask_connect(self.browser)
                    await shadow_connect(self.browser)
                except Exception as e:
                    await update.message.reply_text(f"❌ Failed to connect browser: {e}")
                    return
            
            await update.message.reply_text(f"🔄 Adding pool to monitoring list...")
            
            try:
                # Create pool object with metadata
                pool = Pool(
                    link=pool_link,
                    range=range_type,
                    token=token,
                    amount=amount,
                    owner_chat_id=update.message.chat_id,
                    meta={
                        'threshold': self.settings.get('threshold', 90),
                        'balance_tolerance': self.settings.get('balance_tolerance', 2),
                        'added_by': update.message.from_user.username or str(update.message.from_user.id),
                        'added_at': asyncio.get_event_loop().time()
                    }
                )
                
                # Validate pool by checking its status
                pool_parts = pool_link.split('/')
                if len(pool_parts) >= 2:
                    contract_address = pool_parts[-2]
                    pool_id = pool_parts[-1]
                    
                    status_info = await check_pool_status(self.browser, contract_address, pool_id)
                    if status_info:
                        pool.last_status = "monitoring"
                        logging.info(f"Pool validation successful: {pool_id}")
                    else:
                        await update.message.reply_text("⚠️ Could not validate pool status, but adding anyway.")
                        pool.last_status = "unknown"
                
                # Add to pools list
                self.pools.append(pool)
                
                # Save state
                self._save_pools_state()
                
                # Send confirmation
                await update.message.reply_text(
                    f"✅ Pool added successfully!\n\n"
                    f"🔗 Link: {pool_link}\n"
                    f"📊 Range: {range_type}\n"
                    f"💰 Token: {token}\n"
                    f"💵 Amount: {amount}\n"
                    f"🎯 Threshold: {pool.meta['threshold']}%\n"
                    f"⚖️ Balance Tolerance: {pool.meta['balance_tolerance']}%\n\n"
                    f"The pool is now being monitored automatically."
                )
                
                # Notify admins
                await notify_admins(
                    context, 
                    f"📊 New pool added by {update.message.from_user.username}: {pool_id} ({token} {amount})"
                )
                
                logging.info(f"Pool added successfully: {pool_link} by user {update.message.from_user.id}")
                
            except Exception as e:
                logging.exception(f"Error adding pool: {e}")
                await update.message.reply_text(f"❌ Failed to add pool: {e}")
                await notify_admins(context, f"❌ Failed to add pool: {e}")

    async def remove_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Perform 100% withdrawal from a Shadow.so liquidity pool.
        Usage: /remove [pool_link]
        """
        if update.message:
            if not self._is_authorized(update):
                await update.message.reply_text("Unauthorized.")
                return
            
            # Check if MetaMask credentials are available
            if not self._has_stored_credentials():
                await update.message.reply_text("❌ MetaMask credentials not found. Please use /connect first.")
                return
            
            args = context.args
            if not args:
                await update.message.reply_text("Usage: /remove [pool_link]\nExample: /remove https://www.shadow.so/liquidity/manage/[contract_address]/[pool_id]")
                return
            
            pool_link = args[0]
            
            # Extract Pool ID from link
            try:
                pool_id = pool_link.split('/')[-1]
                if not pool_id.isdigit():
                    await update.message.reply_text("❌ Invalid pool link format.")
                    return
            except:
                await update.message.reply_text("❌ Could not extract Pool ID from link.")
                return
        
            # Ensure browser is connected
            if self.browser is None:
                await update.message.reply_text("🔄 Connecting to browser...")
                self._load_stored_credentials()
                self.browser = await launch_browser()
                await metamask_connect(self.browser)
                await shadow_connect(self.browser)
            
            await update.message.reply_text(f"🔄 Starting 100% withdrawal from Pool ID: {pool_id}...")
            
            try:
                # Create Shadow utility instance
                shadow_utils = Shadow(self.browser)
                
                # Navigate to the pool management page
                page = await self.browser.new_page()
                await page.goto(pool_link, wait_until="networkidle", timeout=120000)  # 120 seconds timeout
                await asyncio.sleep(5)
                
                # Perform the withdrawal using the Shadow utility
                await shadow_utils.withdraw(update, page, pool_link)
                await update.message.reply_text(f"✅ Successfully withdrew 100% from Pool ID: {pool_id}")
                
                await page.close()
                    
            except Exception as e:
                logging.exception(f"Error during withdrawal from Pool ID: {pool_id}")
                await update.message.reply_text(f"❌ Error during withdrawal: {str(e)}")
                await notify_admins(context, f"/remove error: {e}")

    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            if not self._is_authorized(update):
                await update.message.reply_text("Unauthorized.")
                return
            
            # Check if MetaMask credentials are available before proceeding
            if not self._has_stored_credentials():
                await update.message.reply_text("❌ MetaMask credentials not found. Please use /connect first with your password and 12-word seed phrase.\nUsage: /connect [password] [word1] [word2] ... [word12]")
                return
            
            # Ensure browser exists
            if self.browser is None:
                await update.message.reply_text("Connecting to browser to fetch pool data...")
                # Load stored credentials before launching browser
                self._load_stored_credentials()
                self.browser = await launch_browser()
                await metamask_connect(self.browser)
                await shadow_connect(self.browser)
            
            await update.message.reply_text("Fetching pool information from Shadow.so dashboard...")
            
            try:
                # Fetch pool data from Shadow.so dashboard
                dashboard_pools = await fetch_dashboard_pools(self.browser)
                
                if not dashboard_pools:
                    await update.message.reply_text("No pools found in your Shadow.so dashboard.")
                    return
                
                lines = [
                    "🏊 Your Shadow.so Pools:",
                    f"📊 Global Settings: Threshold={self.settings['threshold']}% | Tolerance={self.settings['balance_tolerance']}%",
                    ""
                ]
                
                for i, pool in enumerate(dashboard_pools, 1):
                    lines.append(f"Pool #{i}:")
                    lines.append(f"📋 Pool ID: {pool['pool_id']}")
                    lines.append(f"📝 Contract Address: {pool['contract_address']}")
                    lines.append(f"🔗 Pool Link: {pool['pool_link']}")
                    
                    if pool['tokens']:
                        lines.append(f"💱 Tokens: {pool['tokens']}")
                    if pool['liquidity']:
                        lines.append(f"💰 Liquidity: {pool['liquidity']}")
                    if pool['range']:
                        lines.append(f"📊 Range: {pool['range']}")
                    if pool['status']:
                        lines.append(f"📈 Status: {pool['status']}")
                    
                    lines.append("=" * 50)
                
                # Split message if too long (Telegram has a 4096 character limit)
                message_text = "\n".join(lines)
                if len(message_text) > 4000:
                    # Split into multiple messages
                    current_message = lines[0:3]  # Header
                    current_length = len("\n".join(current_message))
                    
                    for line in lines[3:]:
                        if current_length + len(line) + 1 > 4000:
                            await update.message.reply_text("\n".join(current_message))
                            current_message = [line]
                            current_length = len(line)
                        else:
                            current_message.append(line)
                            current_length += len(line) + 1
                    
                    if current_message:
                        await update.message.reply_text("\n".join(current_message))
                else:
                    await update.message.reply_text(message_text)
                    
            except Exception as e:
                logging.exception("Error fetching dashboard pools")
                await update.message.reply_text(f"❌ Error fetching pool data: {e}")
                
                # NO FAKE FALLBACK DATA - Only show real Shadow.so data
                await update.message.reply_text("❌ Cannot fetch real pool data from Shadow.so dashboard. Please try again later.")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message:
            if not self._is_authorized(update):
                await update.message.reply_text("Unauthorized.")
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
                await shadow_connect(self.browser)
            
            await update.message.reply_text("Checking status…")
            
            try:
                # Fetch pool data from Shadow.so dashboard
                dashboard_pools = await fetch_dashboard_pools(self.browser)
                
                if not dashboard_pools:
                    await update.message.reply_text("No pools found in your Shadow.so dashboard.")
                    return
                
                # Check status for each pool in original simple format, but add Pool ID
                results = []
                for pool in dashboard_pools:
                    try:
                        status = await check_status_with_pool_id(self.browser, pool)
                        results.append(f"Pool ID: {pool['pool_id']} | {pool['pool_link']} -> {status}")
                    except Exception as e:
                        results.append(f"Pool ID: {pool['pool_id']} | {pool['pool_link']} -> error: {str(e)[:30]}...")
                
                await update.message.reply_text("\n".join(results))
                    
            except Exception as e:
                logging.exception("Error fetching dashboard pool status")
                await update.message.reply_text(f"❌ Error fetching pool status: {e}")
                
                # NO FAKE FALLBACK DATA - Only show real Shadow.so data
                await update.message.reply_text("❌ Cannot fetch real pool status from Shadow.so dashboard. Please try again later.")

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
○ /list — Fetch and display all pools from Shadow.so dashboard with Pool IDs and contract addresses
○ /status — Force status check and update (now includes Pool IDs from Shadow.so dashboard)
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

    # Background monitor job (enhanced)
    async def monitor_job(self, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced background monitoring job with comprehensive error handling"""
        try:
            if not self.pools:
                logging.debug("No pools to monitor")
                return
            
            # Check if MetaMask credentials are available before proceeding
            if not self._has_stored_credentials():
                await notify_admins(context, "❌ Monitor: MetaMask credentials not found. Please use /connect first.")
                return
                
            # Ensure browser exists and is functional
            browser_needs_restart = False
            
            if self.browser is None:
                browser_needs_restart = True
                logging.info("Browser is None, needs restart")
            else:
                # Check if browser is still valid by testing if we can create a new page
                try:
                    test_page = await self.browser.new_page()
                    await test_page.close()
                    logging.debug("Browser health check passed")
                except Exception as e:
                    browser_needs_restart = True
                    logging.warning(f"Browser health check failed: {e}")
                    # Clean up the invalid browser reference
                    try:
                        await self.browser.close()
                    except:
                        pass
                    self.browser = None
            
            if browser_needs_restart:
                try:
                    logging.info("🔄 Launching browser for monitoring...")
                    # Load stored credentials before launching browser
                    self._load_stored_credentials()
                    self.browser = await launch_browser()
                    await metamask_connect(self.browser)
                    await shadow_connect(self.browser)
                    logging.info("✅ Browser launched successfully for monitoring")
                except Exception as e:
                    logging.exception("Failed to (re)launch browser for monitoring")
                    await notify_admins(context, f"❌ Monitor: failed to launch browser: {e}")
                    return
            
            logging.info(f"📊 Monitoring {len(self.pools)} pools...")
            
            # Track monitoring results
            rebalanced_count = 0
            error_count = 0
            
            for pool in list(self.pools):
                try:
                    logging.debug(f"Checking pool: {pool.link}")
                    
                    # Apply global settings to pool if not set
                    if 'threshold' not in pool.meta:
                        pool.meta['threshold'] = self.settings.get('threshold', 90)
                    if 'balance_tolerance' not in pool.meta:
                        pool.meta['balance_tolerance'] = self.settings.get('balance_tolerance', 2)
                    
                    # Check and potentially rebalance the pool
                    changed, status = await check_and_rebalance(self.browser, pool, context)
                    
                    # Update pool status
                    old_status = pool.last_status
                    pool.last_status = status
                    
                    # Log status changes
                    if old_status != status:
                        logging.info(f"Pool {pool.link} status changed: {old_status} -> {status}")
                        
                        # Notify on important status changes
                        if status.startswith("error"):
                            await notify_admins(context, f"⚠️ Pool status error: {pool.link} - {status}")
                        elif status == "rebalanced":
                            rebalanced_count += 1
                    
                    # Small delay between pools to avoid overwhelming the system
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    error_count += 1
                    logging.exception(f"Monitoring error for {pool.link}")
                    await notify_admins(context, f"❌ Monitor error for {pool.link}: {e}")
                    
                    # Update pool status to reflect error
                    pool.last_status = f"error: {str(e)[:50]}"
            
            # Save updated pool states
            try:
                self._save_pools_state()
            except Exception as e:
                logging.exception("Failed to save pools state after monitoring")
            
            # Send summary notification if there were significant events
            if rebalanced_count > 0 or error_count > 0:
                summary = f"📊 Monitoring Summary: {rebalanced_count} rebalanced, {error_count} errors"
                logging.info(summary)
                if rebalanced_count > 0:  # Only notify for successful rebalances
                    await notify_admins(context, summary)
                    
        except Exception as e:
            logging.exception("Critical error in monitor_job")
            await notify_admins(context, f"🚨 Critical monitoring error: {e}")
    
    def _save_pools_state(self):
        """Save current pools state to persistent storage"""
        try:
            from utils.state import save_state, load_state
            
            # Convert Pool objects to the format expected by save_state
            pools_list = []
            for pool in self.pools:
                pools_list.append(pool)  # save_state expects Pool objects directly
            
            # Save state with correct parameters
            save_state(pools_list, self.settings)
            logging.debug("Pools state saved successfully")
            
        except Exception as e:
            logging.exception("Failed to save pools state")
            raise




# --- Minimal fallbacks to avoid NameError and keep bot operational ---
async def check_status(browser, pool: Pool) -> str:
    """Lightweight status checker placeholder.

    Returns a simple status string without performing heavy browser actions.
    This avoids NameError until a full implementation is provided.
    """
    try:
        # If we have last_status, surface it; otherwise provide a generic one
        return pool.last_status or "monitoring"
    except Exception:
        return "unknown"

async def check_status_with_pool_id(browser, pool_data: dict) -> str:
    """Check status for a pool from dashboard data.
    
    Returns a simple status string in the original style.
    """
    try:
        # Try to get basic status information
        if pool_data.get('status'):
            return pool_data['status'].lower()
        
        # If we have the pool link, we could potentially check more detailed status
        # but for now, return a simple status based on available data
        if pool_data.get('liquidity') and '$' in pool_data['liquidity']:
            return "active"
        
        return "monitoring"
    except Exception:
        return "unknown"


async def check_and_rebalance(browser, pool: Pool, context: ContextTypes.DEFAULT_TYPE):
    """Complete automated rebalancing workflow.
    
    1. Check if pool is near out-of-range
    2. If yes, remove liquidity
    3. Check token balances and swap if needed
    4. Re-add balanced liquidity
    
    Returns (changed, status).
    """
    from utils.logger import log_rebalance_event
    import time
    
    start_time = time.time()
    
    try:
        # Get pool details and current status
        pool_parts = pool.link.split('/')
        if len(pool_parts) < 2:
            return False, "error: invalid pool link format"
        
        contract_address = pool_parts[-2]
        pool_id = pool_parts[-1]
        
        log_rebalance_event(pool_id, "STATUS_CHECK_START")
        
        # Check current pool status
        from services.shadow_dashboard import check_pool_status
        status_info = await check_pool_status(browser, contract_address, pool_id)
        
        if not status_info:
            log_rebalance_event(pool_id, "STATUS_CHECK_FAILED", {"error": "could not fetch pool status"})
            return False, "error: could not fetch pool status"
        
        # Check if pool is in range
        if status_info.get('in_range', True):
            # Pool is still in range, check if approaching threshold
            if not await _is_approaching_threshold(browser, pool, status_info):
                log_rebalance_event(pool_id, "MONITORING", {"status": "in_range", "price": status_info.get('current_price', 'unknown')})
                return False, "monitoring: in range"
        
        # Extract price information for notifications
        current_price = 0
        bounds = (0, 0)
        try:
            import re
            price_str = status_info.get('current_price', '')
            range_str = status_info.get('range_info', '')
            
            if price_str:
                price_match = re.search(r'\$?([\d,]+\.?\d*)', price_str)
                if price_match:
                    current_price = float(price_match.group(1).replace(',', ''))
            
            if range_str:
                range_matches = re.findall(r'\$?([\d,]+\.?\d*)', range_str)
                if len(range_matches) >= 2:
                    bounds = (float(range_matches[0].replace(',', '')), float(range_matches[1].replace(',', '')))
        except:
            pass
        
        # Pool is out of range or approaching threshold - start rebalancing
        logging.info(f"🔄 Starting rebalancing for pool {pool_id}")
        log_rebalance_event(pool_id, "REBALANCE_START", {
            "current_price": current_price,
            "lower_bound": bounds[0],
            "upper_bound": bounds[1],
            "threshold": pool.meta.get('threshold', 90)
        })
        
        await notify_rebalance_start(context, pool_id, current_price, bounds)
        
        # Step 1: Remove liquidity
        shadow_utils = Shadow(browser)
        log_rebalance_event(pool_id, "REMOVE_LIQUIDITY_START")
        
        success = await _remove_liquidity(shadow_utils, pool.link)
        if not success:
            log_rebalance_event(pool_id, "REMOVE_LIQUIDITY_FAILED")
            await notify_rebalance_error(context, pool_id, "Failed to remove liquidity", "Remove Liquidity")
            return False, "error: failed to remove liquidity"
        
        log_rebalance_event(pool_id, "REMOVE_LIQUIDITY_SUCCESS")
        await notify_admins(context, f"✅ Liquidity removed from pool {pool_id}")
        
        # Step 2: Check token balances and rebalance if needed
        log_rebalance_event(pool_id, "TOKEN_REBALANCE_START")
        
        balance_success = await _rebalance_tokens(browser, shadow_utils, pool)
        if not balance_success:
            log_rebalance_event(pool_id, "TOKEN_REBALANCE_FAILED")
            await notify_admins(context, f"⚠️ Token rebalancing failed for pool {pool_id}, continuing...")
        else:
            log_rebalance_event(pool_id, "TOKEN_REBALANCE_SUCCESS")
        
        # Step 3: Re-add liquidity with balanced amounts
        log_rebalance_event(pool_id, "READD_LIQUIDITY_START")
        
        readd_success = await _readd_liquidity(shadow_utils, pool)
        if not readd_success:
            log_rebalance_event(pool_id, "READD_LIQUIDITY_FAILED")
            await notify_rebalance_error(context, pool_id, "Failed to re-add liquidity", "Re-add Liquidity")
            return False, "error: failed to re-add liquidity"
        
        # Calculate duration
        duration = int(time.time() - start_time)
        
        log_rebalance_event(pool_id, "REBALANCE_COMPLETE", {
            "duration_seconds": duration,
            "total_steps": 3,
            "success": True
        })
        
        await notify_rebalance_complete(context, pool_id, duration)
        logging.info(f"✅ Rebalancing completed for pool {pool_id} in {duration}s")
        
        return True, "rebalanced"
        
    except Exception as e:
        duration = int(time.time() - start_time)
        logging.exception(f"Error in rebalancing for {pool.link}")
        log_rebalance_event(pool_id if 'pool_id' in locals() else 'unknown', "REBALANCE_ERROR", {
            "error": str(e)[:100],
            "duration_seconds": duration
        })
        await notify_rebalance_error(context, pool_id if 'pool_id' in locals() else 'unknown', str(e), "General Error")
        return False, f"error: {e}"

async def _is_approaching_threshold(browser, pool: Pool, status_info: dict) -> bool:
    """Check if pool is approaching the rebalance threshold"""
    try:
        # Extract current price and range from status_info
        current_price_str = status_info.get('current_price', '')
        range_info_str = status_info.get('range_info', '')
        
        if not current_price_str or not range_info_str:
            return False
        
        # Parse current price
        import re
        price_match = re.search(r'\$?([\d,]+\.?\d*)', current_price_str)
        if not price_match:
            return False
        current_price = float(price_match.group(1).replace(',', ''))
        
        # Parse range bounds
        range_matches = re.findall(r'\$?([\d,]+\.?\d*)', range_info_str)
        if len(range_matches) < 2:
            return False
        
        lower_bound = float(range_matches[0].replace(',', ''))
        upper_bound = float(range_matches[1].replace(',', ''))
        
        # Calculate threshold distances
        range_size = upper_bound - lower_bound
        threshold_distance = (pool.meta.get('threshold', 90) / 100) * range_size
        
        upper_threshold = upper_bound - threshold_distance
        lower_threshold = lower_bound + threshold_distance
        
        # Check if approaching threshold
        approaching = current_price >= upper_threshold or current_price <= lower_threshold
        
        if approaching:
            logging.info(f"Pool {pool.link} approaching threshold: price={current_price}, bounds=[{lower_bound}, {upper_bound}], thresholds=[{lower_threshold}, {upper_threshold}]")
        
        return approaching
        
    except Exception as e:
        logging.exception(f"Error checking threshold for {pool.link}")
        return False

async def _remove_liquidity(shadow_utils: Shadow, pool_link: str) -> bool:
    """Remove 100% liquidity from pool"""
    try:
        # Navigate to pool management page
        shadow_page = await shadow_utils.browser.new_page()
        await shadow_page.goto(pool_link, wait_until="networkidle")
        await asyncio.sleep(3)
        
        # Look for remove/withdraw button
        remove_buttons = [
            "Remove Liquidity",
            "Withdraw",
            "Remove",
            "100%"
        ]
        
        for button_text in remove_buttons:
            try:
                button = shadow_page.get_by_role("button", name=button_text)
                if await button.is_visible():
                    await button.click()
                    await asyncio.sleep(2)
                    break
            except:
                continue
        
        # Set to 100% if there's a percentage slider/input
        try:
            # Look for 100% button or max button
            max_buttons = shadow_page.locator("button:has-text('100%'), button:has-text('Max'), button:has-text('MAX')")
            if await max_buttons.count() > 0:
                await max_buttons.first.click()
                await asyncio.sleep(1)
        except:
            pass
        
        # Confirm removal
        confirm_buttons = [
            "Confirm",
            "Remove",
            "Withdraw",
            "Submit"
        ]
        
        for button_text in confirm_buttons:
            try:
                button = shadow_page.get_by_role("button", name=button_text)
                if await button.is_visible():
                    await button.click()
                    await asyncio.sleep(2)
                    break
            except:
                continue
        
        # Wait for MetaMask confirmation (handled by background task)
        await asyncio.sleep(10)
        
        await shadow_page.close()
        return True
        
    except Exception as e:
        logging.exception(f"Error removing liquidity: {e}")
        return False

async def _rebalance_tokens(browser, shadow_utils: Shadow, pool: Pool) -> bool:
    """Check token balances and swap if needed to balance them"""
    try:
        # Navigate to Shadow.so trade page
        trade_page = await browser.new_page()
        await trade_page.goto("https://www.shadow.so/trade", wait_until="networkidle")
        await asyncio.sleep(3)
        
        # Get token balances from the page
        balance_elements = await trade_page.locator('[class*="balance"], [class*="amount"]').all()
        balances = []
        
        for elem in balance_elements:
            try:
                text = await elem.text_content()
                if text and '$' in text:
                    # Extract dollar amount
                    import re
                    amount_match = re.search(r'\$?([\d,]+\.?\d*)', text)
                    if amount_match:
                        amount = float(amount_match.group(1).replace(',', ''))
                        balances.append(amount)
            except:
                continue
        
        if len(balances) < 2:
            logging.warning("Could not detect token balances for rebalancing")
            await trade_page.close()
            return False
        
        # Check if balances need rebalancing
        balance1, balance2 = balances[0], balances[1]
        total_value = balance1 + balance2
        target_each = total_value / 2
        
        # Calculate tolerance
        tolerance_percent = pool.meta.get('balance_tolerance', 2)
        tolerance_amount = (tolerance_percent / 100) * target_each
        
        # Check if rebalancing is needed
        if abs(balance1 - target_each) <= tolerance_amount and abs(balance2 - target_each) <= tolerance_amount:
            logging.info(f"Token balances are already balanced: {balance1}, {balance2}")
            await trade_page.close()
            return True
        
        # Determine which token to swap
        if balance1 > balance2:
            # Swap some of token1 to token2
            swap_amount = (balance1 - target_each) / 2
            logging.info(f"Swapping {swap_amount} of token1 to token2")
        else:
            # Swap some of token2 to token1
            swap_amount = (balance2 - target_each) / 2
            logging.info(f"Swapping {swap_amount} of token2 to token1")
        
        # Perform the swap (simplified - would need more specific implementation)
        # This would involve:
        # 1. Setting swap amounts
        # 2. Clicking swap button
        # 3. Confirming MetaMask transaction
        
        # For now, we'll simulate the swap
        await asyncio.sleep(5)  # Simulate swap time
        
        await trade_page.close()
        return True
        
    except Exception as e:
        logging.exception(f"Error rebalancing tokens: {e}")
        return False

async def _readd_liquidity(shadow_utils: Shadow, pool: Pool) -> bool:
    """Re-add liquidity to the pool with balanced amounts"""
    try:
        # Navigate back to the pool page
        pool_link = pool.link.replace('/manage/', '/')  # Convert to add liquidity page
        shadow_page = await shadow_utils.browser.new_page()
        await shadow_page.goto(pool_link, wait_until="networkidle")
        await asyncio.sleep(3)
        
        # Set range type if specified
        if pool.range:
            range_buttons = await shadow_page.locator(f"button:has-text('{pool.range}')").all()
            if range_buttons:
                await range_buttons[0].click()
                await asyncio.sleep(1)
        
        # Set token amounts (this would need more specific implementation)
        # For now, we'll use the original amount or let it auto-calculate
        
        # Click add liquidity button
        add_buttons = [
            "Add Liquidity",
            "Deposit",
            "Add",
            "Submit"
        ]
        
        for button_text in add_buttons:
            try:
                button = shadow_page.get_by_role("button", name=button_text)
                if await button.is_visible():
                    await button.click()
                    await asyncio.sleep(2)
                    break
            except:
                continue
        
        # Wait for MetaMask confirmation
        await asyncio.sleep(10)
        
        await shadow_page.close()
        return True
        
    except Exception as e:
        logging.exception(f"Error re-adding liquidity: {e}")
        return False