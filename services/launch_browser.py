import os
from playwright.async_api import async_playwright
import asyncio
from services.metamask_connect import metamask_connect
from services.shadow_connect import shadow_connect
from utils.shadow_utils import Shadow
from services.metamask_popup import MetamaskPopup
from config import config
import logging

async def metamask_confirmation(browser, popup_url):
    """Enhanced MetaMask confirmation handler for all transaction types"""
    logging.info("🔄 Starting MetaMask confirmation handler...")
    
    while True:
        if not browser.pages:
            break
        try:
            # Check all pages for MetaMask popups
            for page in browser.pages:
                if page.url.startswith(popup_url) or 'notification.html' in page.url:
                    confirm_page = page
                    
                    # Wait for page to load
                    await asyncio.sleep(1)
                    
                    # Enhanced button detection for different transaction types
                    buttons_to_try = [
                        # Connection buttons
                        "Connect",
                        "Next",
                        "Confirm",
                        
                        # Transaction buttons  
                        "Approve",
                        "Sign",
                        "Submit",
                        
                        # Specific transaction types
                        "Swap",
                        "Add Liquidity", 
                        "Remove Liquidity",
                        "Withdraw",
                        
                        # Network switching
                        "Switch network",
                        "Add network",
                        "Approve",
                        
                        # Generic confirmations
                        "OK",
                        "Accept",
                        "Allow"
                    ]
                    
                    button_clicked = False
                    for button_text in buttons_to_try:
                        try:
                            # Try different button selectors
                            selectors = [
                                f"button:has-text('{button_text}')",
                                f"[data-testid*='{button_text.lower()}']",
                                f"[class*='btn']:has-text('{button_text}')",
                                f"[role='button']:has-text('{button_text}')"
                            ]
                            
                            for selector in selectors:
                                buttons = confirm_page.locator(selector)
                                if await buttons.count() > 0:
                                    button = buttons.first
                                    if await button.is_visible() and await button.is_enabled():
                                        logging.info(f"🔘 Clicking MetaMask button: {button_text}")
                                        await button.click()
                                        button_clicked = True
                                        await asyncio.sleep(2)  # Wait for action to process
                                        break
                            
                            if button_clicked:
                                break
                                
                        except Exception as e:
                            logging.debug(f"Button click attempt failed for {button_text}: {e}")
                            continue
                    
                    # If no button was clicked, try scrolling and looking for buttons
                    if not button_clicked:
                        try:
                            # Scroll down to reveal hidden buttons
                            await confirm_page.keyboard.press("PageDown")
                            await asyncio.sleep(1)
                            
                            # Try again with common button patterns
                            common_buttons = confirm_page.locator("button[class*='btn'], button[data-testid], [role='button']")
                            button_count = await common_buttons.count()
                            
                            if button_count > 0:
                                # Click the last button (usually the confirm/submit button)
                                last_button = common_buttons.nth(button_count - 1)
                                if await last_button.is_visible():
                                    button_text = await last_button.text_content()
                                    logging.info(f"🔘 Clicking last available button: {button_text}")
                                    await last_button.click()
                                    await asyncio.sleep(2)
                        except Exception as e:
                            logging.debug(f"Fallback button click failed: {e}")
                    
                    break  # Exit page loop after handling one popup
                    
        except Exception as e:
            logging.debug(f"MetaMask confirmation error: {e}")

        await asyncio.sleep(2)  # Check every 2 seconds

async def launch_browser():
    """Enhanced browser launch with better error handling"""
    try:
        p = await async_playwright().start()
        
        # Build browser args
        args = [
            f"--disable-extensions-except={config.EXTENSION_PATH}",
            f"--load-extension={config.EXTENSION_PATH}",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-gpu"
        ]
        
        if config.START_MAXIMIZED:
            args.append("--start-maximized")
        
        logging.info("🚀 Launching browser with MetaMask extension...")
        
        browser = await p.chromium.launch_persistent_context(
                user_data_dir=config.USER_DATA_DIR,
                headless=config.HEADLESS,
                args=args,
                no_viewport=True,
                color_scheme=config.COLOR_SCHEME,
                timeout=60000  # Increase timeout
            )

        # Open a blank page and close the default one
        page = await browser.new_page()
        if len(browser.pages) > 1:
            await browser.pages[0].close()
        
        # Navigate to a simple page and wait for it to load
        try:
            await page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=30000)
            logging.info("✅ Browser navigation test successful")
        except Exception as e:
            logging.warning(f"Browser navigation test failed, continuing anyway: {e}")

        # Give the browser and extensions more time to initialize
        await asyncio.sleep(5)
        
        # Get extension ID and setup confirmation handler
        try:
            if browser.service_workers and len(browser.service_workers) > 0:
                service_worker = browser.service_workers[0]
                extension_id = service_worker.url.split("/")[2]
                popup_url = f"chrome-extension://{extension_id}/notification.html"
                
                # Start MetaMask confirmation handler in background
                asyncio.create_task(metamask_confirmation(browser, popup_url))
                logging.info(f"✅ MetaMask confirmation handler started for extension: {extension_id}")
            else:
                logging.warning("⚠️ No service workers found - MetaMask extension may not be loaded")
                
        except Exception as e:
            logging.error(f"Failed to setup MetaMask confirmation handler: {e}")

        logging.info("✅ Browser launched successfully")
        return browser
        
    except Exception as e:
        logging.exception(f"Failed to launch browser: {e}")
        raise

