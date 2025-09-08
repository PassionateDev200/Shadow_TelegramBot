import os
from playwright.async_api import async_playwright
import asyncio
from services.metamask_connect import metamask_connect
from services.shadow_connect import shadow_connect
from utils.shadow_utils import Shadow
from services.metamask_popup import MetamaskPopup
from config import config

async def metamask_confirmation(browser, popup_url):
    while True:
        if not browser.pages:
            break
        try:
            if (browser.pages[-1].url).startswith(popup_url) :
                    confirm_page = browser.pages[-1]
                    buttons = ["Connect", "Confirm", "Approve", "Sign"]
                    for button in buttons:
                        btn = confirm_page.get_by_role("button", name=button)
                        if await btn.is_visible():
                            await btn.click()
                            break
                    
        except Exception as e:
            print(f"Error occurred: {e}")

        await asyncio.sleep(1)

async def launch_browser():
    p = await async_playwright().start()
    
    # Build browser args
    args = [
        f"--disable-extensions-except={config.EXTENSION_PATH}",
        f"--load-extension={config.EXTENSION_PATH}",
    ]
    
    if config.START_MAXIMIZED:
        args.append("--start-maximized")
    
    browser = await p.chromium.launch_persistent_context(
            user_data_dir=config.USER_DATA_DIR,
            headless=config.HEADLESS,
            args=args,
            no_viewport=True,
            color_scheme=config.COLOR_SCHEME,
        )

        # Open a blank page just to get a page object
    page = await browser.new_page()
    await browser.pages[0].close()
    await page.goto("https://www.google.com")

    await asyncio.sleep(1)
    
    service_worker = browser.service_workers[0]
    extension_id = service_worker.url.split("/")[2]
    popup_url = f"chrome-extension://{extension_id}/notification.html"

    asyncio.create_task(metamask_confirmation(browser, popup_url))

    # add pool link
    #await add_pool_link(browser, POOL_LINK)

    #metamask_popup = browser.pages[3]
    #popup = MetamaskPopup(metamask_popup)
    #await popup.popup_viewport()

    return browser

