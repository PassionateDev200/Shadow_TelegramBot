from playwright.sync_api import sync_playwright
import time
import os

EXTENSION_PATH = r"C:\Users\deboj\VSCODE\project_liquidity_rebalance\nkbihfbeogaeaoehlefnkodbefgpgknn"
USER_DATA_DIR = r"C:\Users\deboj\VSCODE\project_liquidity_rebalance\playwright_profile"

with sync_playwright() as p:
    chromium = p.chromium
    browser = chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,
        args=[
            f"--disable-extensions-except={EXTENSION_PATH}",
            f"--load-extension={EXTENSION_PATH}",
            "--disable-web-security",
            "--allow-running-insecure-content",
            "--disable-features=VizDisplayCompositor"
        ]
    )
    time.sleep(5) 

    # Navigate to a webpage first
    page = browser.new_page()
    page.goto("https://google.com")
    time.sleep(3)
    
    print("Trying to open MetaMask popup...")
    
    # Method 1: Use the keyboard shortcut
    try:
        print("Using keyboard shortcut Alt+Shift+M...")
        page.keyboard.press("Alt+Shift+M")
        time.sleep(3)
        
        # Check if popup opened by looking for extension pages
        popup_found = False
        for page_obj in browser.pages:
            if "chrome-extension" in page_obj.url and ("popup" in page_obj.url or "nkbihfbeogaeaoehlefnkodbefgpgknn" in page_obj.url):
                print(f"Popup found: {page_obj.url}")
                page_obj.bring_to_front()
                page_obj.set_viewport_size({"width": 357, "height": 600})
                popup_found = True
                break
        
        if not popup_found:
            print("Popup not found via keyboard shortcut")
            
            # Method 2: Try clicking on extension icon
            print("Trying to click extension icon...")
            
            # Look for the extensions menu button (3 dots or puzzle piece)
            try:
                # Try different selectors for the extensions button
                extensions_selectors = [
                    '[data-test-id="extensions-menu-button"]',
                    '[aria-label*="Extension"]',
                    'button[title*="Extension"]',
                    '#extensions-menu-button'
                ]
                
                for selector in extensions_selectors:
                    try:
                        button = page.locator(selector).first
                        if button.is_visible():
                            print(f"Found extensions button with selector: {selector}")
                            button.click()
                            time.sleep(2)
                            
                            # Look for MetaMask in the dropdown
                            metamask_selectors = [
                                'text="MetaMask"',
                                '[title*="MetaMask"]',
                                '[aria-label*="MetaMask"]'
                            ]
                            
                            for mm_selector in metamask_selectors:
                                try:
                                    mm_button = page.locator(mm_selector).first
                                    if mm_button.is_visible():
                                        print("Found MetaMask button, clicking...")
                                        mm_button.click()
                                        time.sleep(2)
                                        popup_found = True
                                        break
                                except:
                                    continue
                            
                            if popup_found:
                                break
                    except:
                        continue
                        
            except Exception as e:
                print(f"Error clicking extension icon: {e}")
            
            # Method 3: Try to navigate to popup directly with different approach
            if not popup_found:
                print("Trying direct popup access...")
                try:
                    # Create a new tab and try to access popup
                    popup_page = browser.new_page()
                    extension_id = "nkbihfbeogaeaoehlefnkodbefgpgknn"
                    
                    # Try different popup URLs
                    popup_urls = [
                        f"chrome-extension://{extension_id}/popup.html",
                        f"chrome-extension://{extension_id}/popup-init.html",
                        f"chrome-extension://{extension_id}/home.html#popup"
                    ]
                    
                    for url in popup_urls:
                        try:
                            print(f"Trying URL: {url}")
                            popup_page.goto(url, wait_until="domcontentloaded", timeout=10000)
                            popup_page.set_viewport_size({"width": 357, "height": 600})
                            print(f"Successfully opened: {url}")
                            popup_found = True
                            break
                        except Exception as url_error:
                            print(f"Failed to open {url}: {str(url_error)}")
                            continue
                    
                    if not popup_found:
                        popup_page.close()
                        
                except Exception as e:
                    print(f"Error with direct access: {e}")
        
        if popup_found:
            print("MetaMask popup is now open!")
        else:
            print("Could not open MetaMask popup. Browser will stay open for manual interaction.")
            
    except Exception as e:
        print(f"Error: {e}")
    
    print("\nBrowser is ready. You can manually click on the MetaMask extension icon if needed.")
    input("Press Enter to close...")
    browser.close()
