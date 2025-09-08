from playwright.async_api import async_playwright
import asyncio

async def main():
    async with async_playwright() as p:
        content = await p.chromium.launch(headless=False, args=["--start-maximized"])
        browser1 = await content.new_context(no_viewport=True)
        page = await browser1.new_page()
        await page.goto("https://www.shadow.so/liquidity/manage/0x324963c267c354c7660ce8ca3f5f167e05649970")

        t = (await page.locator("[class=\"my-4 inline-flex cursor-pointer items-center rounded px-2 py-1 text-3xl font-bold text-dark hover:bg-dark\"]").text_content()).split("\u2002")[0]
        print(t)

        await page.wait_for_load_state("networkidle")
        input("Press Enter to close...")
        await content.close()

asyncio.run(main())