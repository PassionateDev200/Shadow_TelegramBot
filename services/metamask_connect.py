import logging
from utils.get_extension_id import get_extension_id
from utils.metamask_utils import MetamaskFunc
from utils.check_for_url import check_for_url
import asyncio

async def metamask_connect(browser):
    """Open the MetaMask extension UI and perform first-time/login flow.
    Robust to variable page ordering; derives extension id from service worker or open pages.
    """
    # Discover extension id
    extension_id = await get_extension_id(browser)

    if not extension_id:
        raise RuntimeError("MetaMask extension not found. Ensure EXTENSION_PATH is correct and loaded.")

    await asyncio.sleep(2)
    # Find or open MetaMask home page
    url = f"chrome-extension://{extension_id}/home.html"
    metamask = await check_for_url(browser, url)
    if metamask is None:
        metamask = await browser.new_page()
        await metamask.goto(url)

    metamask_func = MetamaskFunc(metamask)
    
    # Wait for MetaMask to load with increased timeout and better error handling
    try:
        await metamask.wait_for_load_state("networkidle", timeout=60000)  # Increase to 60 seconds
    except Exception as e:
        logging.warning(f"MetaMask networkidle timeout, trying domcontentloaded: {e}")
        try:
            await metamask.wait_for_load_state("domcontentloaded", timeout=30000)  # Fallback to 30 seconds
        except Exception as e2:
            logging.warning(f"MetaMask domcontentloaded also failed, continuing anyway: {e2}")
            # Continue anyway - sometimes MetaMask works even if load state detection fails
            await asyncio.sleep(3)  # Give it a bit more time

    btn = metamask.get_by_role('button', name='GET STARTED')
    for _ in range(3):
        try:
            if await btn.is_visible():
                await metamask_func.metamask_first_time_signin()
                break
            await asyncio.sleep(1)
            btn = metamask.get_by_role('button', name='GET STARTED')
        except Exception as e:
            logging.error(f"Error occurred: {e}")
    else:
        await metamask_func.metamask_login()
