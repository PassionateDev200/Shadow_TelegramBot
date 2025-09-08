import asyncio
from utils.shadow_utils import Shadow

async def shadow_connect(browser):
    shadow_page = await browser.new_page()
    await shadow_page.goto("https://www.shadow.so/")
    
    shadow = Shadow(browser)
    for _ in range(3):
        btn = shadow_page.get_by_role("button", name="Connect Wallet")
        if await btn.is_visible():
            await shadow.shadow_connect()
            break
        await asyncio.sleep(1)

