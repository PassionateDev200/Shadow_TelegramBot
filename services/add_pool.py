import asyncio
from utils.shadow_utils import Shadow
from config import config

async def add_pool(update, browser, args):
    shadow_page = None
    try:
        # Validate we have exactly 4 arguments
        if len(args) != 4:
            await update.message.reply_text(
                "❌ Invalid command format.\n\n"
                "Usage: /add [pool_link] [range_type] [token] [amount]\n"
                "Example: /add https://www.shadow.so/liquidity/0x123... aggressive USDC 30\n"
                "Range types: passive, wide, narrow, aggressive, insane"
            )
            return False, None
            
        pool_link, range_type, token, price = args

        if not pool_link.startswith(config.SHADOW_BASE_URL):
            await update.message.reply_text("Give a valid pool link.")
            return False, None

        elif range_type.lower() not in config.DEFAULT_RANGE_TYPES:
            await update.message.reply_text("Give a valid range type.")
            return False, None

        elif float(price) <= 0:
            await update.message.reply_text("Give a valid amount.")
            return False, None

        await update.message.reply_text("Opening pool page…")
        # shadow.so/liquidity/pool_link
        shadow_page = await browser.new_page()
        await shadow_page.goto(pool_link)
        await shadow_page.wait_for_load_state("networkidle", timeout=0)

        tokens = (await shadow_page.locator('[class="text-3xl font-bold"]').text_content()).split("/")

        if token.upper() not in tokens:
            await update.message.reply_text("Give a valid token.")
            await shadow_page.close()
            return False, None

        shadow = Shadow(browser)
        # connect wallet in shadow.so
        btn = shadow_page.locator("button:has-text('Connect Wallet')").first
        if await btn.is_visible():
            await update.message.reply_text("Connecting wallet…")
            await shadow.shadow_connect()

        range_type_index = config.DEFAULT_RANGE_TYPES.index(range_type.lower())
        token_index = tokens.index(token.upper())

        await update.message.reply_text("Submitting add liquidity transaction…")
        upper_range, lower_range = await shadow.add_pool_link(update, shadow_page, range_type_index, token_index, price)

        # If add_pool_link failed (returns None, None), close the page
        if upper_range is None and lower_range is None:
            await shadow_page.close()
            return False, None

        asyncio.create_task(shadow.track(update, shadow_page, pool_link))

        pool_info = {
            "link": pool_link,
            "range": range_type.lower(),
            "token": token.upper(),
            "amount": float(price),
            "upper_range": upper_range,
            "lower_range": lower_range,
        }
        return True, pool_info

    except Exception as e:
        await update.message.reply_text("❌ Failed to process /add. Please check your inputs and try again.")
        print(e)
        # Close the page if it was created and an error occurred
        if shadow_page is not None:
            try:
                await shadow_page.close()
            except:
                pass  # Ignore errors when closing page
        return False, None
