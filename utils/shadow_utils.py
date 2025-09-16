import asyncio
from config import config
from utils.check_for_url import check_for_url
from utils.state import load_state, save_state
from models.pool import Pool

class Shadow:
    def __init__(self, browser):
        self.browser = browser

    def get_pool_data_by_link(self, pool_link):
        """Get pool data from JSON state by pool link"""
        try:
            state = load_state()
            pools = state.get("pools", [])
            for pool in pools:
                if pool.get("link") == pool_link:
                    return pool
            return None
        except Exception:
            return None

    async def shadow_connect(self):
        shadow = await check_for_url(self.browser, "https://www.shadow.so/")

        if shadow is None:
            raise RuntimeError("Failed to connect to https://www.shadow.so/, self.shadow is None.")

        await shadow.get_by_role("button", name="Connect Wallet").nth(0).click()
        await shadow.click("data-testid=rk-wallet-option-io.metamask")
        await asyncio.sleep(1)
        # metamask confirmation
        #await self.browser.pages[3].get_by_role("button", name="Connect").click()

        await shadow.get_by_role("button", name="Sign-in").click()
        await asyncio.sleep(1)
        # metamask confirmation
        #await self.browser.pages[3].get_by_role("button", name="Confirm").click()

        await shadow.get_by_role("button", name="Wrong Network").click()
        await asyncio.sleep(1)
        # metamask confirmation
        #await self.browser.pages[3].get_by_role("button", name="Approve").click()

    async def add_pool_link(self, update, shadow, range_type_index, token_index, price):
        range_type_class = '[class="card flex-grow cursor-pointer overflow-hidden"]'
        await shadow.locator(range_type_class).nth(range_type_index).click()

        input_class = '[class="w-full bg-transparent text-3xl font-bold outline-none placeholder:text-dark md:text-4xl text-light text-right"]'
        await shadow.locator(input_class).nth(token_index).fill(price)

        #get upper and lower price
        if token_index == 1:
            await shadow.click('[class="my-4 inline-flex cursor-pointer items-center rounded px-2 py-1 text-3xl font-bold text-dark hover:bg-dark"]')
        range_prices_class = '[class="absolute left-0 top-1/2 flex -translate-y-1/2 touch-none items-center rounded-full px-3 py-1 text-xs max-md:rounded-l-none max-md:pl-1.5 md:-translate-x-1/2 md:text-base  cursor-ns-resize bg-primary-light text-dark"]'
        range_prices_div = shadow.locator(range_prices_class)
        upper_range_text = await range_prices_div.nth(1).text_content()
        lower_range_text = await range_prices_div.nth(0).text_content()
        
        # Extract numeric values from the text (remove $ and any other characters)
        try:
            upper_range = float(upper_range_text.replace('$', '').replace(',', '').strip())
            lower_range = float(lower_range_text.replace('$', '').replace(',', '').strip())
        except (ValueError, AttributeError):
            upper_range = None
            lower_range = None
        print("=======upper_range ===> ", upper_range, "=======lower_range ===> ", lower_range);
        btn = shadow.get_by_role("button", name="Deposit")
        if await btn.is_disabled():
            await update.message.reply_text("Your Balance is insufficient")
            return None, None
        else:
            await btn.click()
            print("===========================================================");
            # await shadow.get_by_role("button", name="Confirm Swap").click()
            await update.message.reply_text("Liquidity added successfully!")
            return upper_range, lower_range

    async def current_price_monitor(self, shadow):
        current_price_class = '[class="absolute left-0 top-1/2 flex -translate-y-1/2 touch-none items-center rounded-full px-3 py-1 text-xs max-md:rounded-l-none max-md:pl-1.5 md:-translate-x-1/2 md:text-base  bg-muted"]'
        
        try:
            current_price_text = await shadow.locator(current_price_class).text_content()
            current_price = float(current_price_text.replace('$', '').replace(',', '').strip())
            self.current_price = current_price  # Store the current price
            return current_price
        except (ValueError, AttributeError):
            return None
        except Exception:
            return None

    async def withdraw(self, update, withdraw_page, pool_link):
        await withdraw_page.get_by_role("button", name="Decrease Liquidity").click()
        await withdraw_page.get_by_role("button", name="100%").click()
        await withdraw_page.get_by_role("button", name="Withdraw").click()
        #if confirm ...
        
        # Remove pool from JSON state after withdrawal
        try:
            state = load_state()
            pool_dicts = state.get("pools", [])
            settings = state.get("settings", {})
            
            # Convert dictionaries to Pool objects and filter out the withdrawn pool
            updated_pools = []
            for p in pool_dicts:
                if p.get("link") != pool_link:
                    pool_obj = Pool(
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
                    updated_pools.append(pool_obj)
            
            # Save updated state
            save_state(updated_pools, settings)
            print(f"Pool {pool_link} removed from state after withdrawal")
        except Exception as e:
            print(f"Error removing pool from state: {e}")

    async def rebalance(self, trade_page, tokens, amount):
        await trade_page.goto("https://www.shadow.so/trade")
        t = trade_page.locator('[class="flex items-center text-3xl font-medium"]')

        if tokens[0] == "SHADOW" or tokens[1] == "S" or (tokens[0] == "SHADOW" and tokens[1] == "S"):
            await trade_page.click('[class="size-5 text-primary-light"]')

        await t.nth(0).click()
        await trade_page.fill('[class="form-control bg-dark py-2 pl-10 text-lg md:py-3 md:pl-14 md:text-2xl"]', tokens[0])
        #first div
        await trade_page.locator('[class="flex cursor-pointer hover:bg-dark items-center py-2 pl-4 pr-0 font-medium md:rounded-lg"]').nth(0).click()

        await t.nth(1).click()
        await trade_page.fill('[class="form-control bg-dark py-2 pl-10 text-lg md:py-3 md:pl-14 md:text-2xl"]', tokens[1])
        #first div
        await trade_page.locator('[class="flex cursor-pointer hover:bg-dark items-center py-2 pl-4 pr-0 font-medium md:rounded-lg"]').nth(0).click()

        await trade_page.fill('[class="w-full bg-transparent text-3xl font-bold outline-none placeholder:text-dark md:text-4xl text-light text-right"]', amount)

        await asyncio.sleep(1)
        swap_btn = await trade_page.get_by_role("button", name="Swap")
        if swap_btn.is_visible():
            await swap_btn.click()

        # if confirm...

    async def track(self, update, shadow_page, pool_link): 
            # Get pool data from JSON state
        pool_data = self.get_pool_data_by_link(pool_link)
        if not pool_data:
                print(f"Pool data not found for link: {pool_link}")
                return
            
            # Get settings data from JSON state
        state = load_state()
        settings = state.get("settings", {})
        threshold = settings.get("threshold", 90)  # Default 90
        balance_tolerance = settings.get("balance_tolerance", 2)  # Default 2
        
        token = pool_data.get("token", "")
        range_type = pool_data.get("range", "")
        amount = pool_data.get("amount", 0)
        upper_range = pool_data.get("upper_range")
        lower_range = pool_data.get("lower_range")

            # go to withdraw page
        link_split = pool_link.rsplit("/", 1)
        await shadow_page.goto(link_split[0] + "/manage/" + link_split[1])

        t = (await shadow_page.locator('[class="my-4 inline-flex cursor-pointer items-center rounded px-2 py-1 text-3xl font-bold text-dark hover:bg-dark"]').text_content()).split("\u2002")
        if t[0] != token:
                await shadow_page.click('[class="my-4 inline-flex cursor-pointer items-center rounded px-2 py-1 text-3xl font-bold text-dark hover:bg-dark"]')
            
        while True:
            if not self.browser.pages:
                break
            # Get current price
            current_price = await self.current_price_monitor(shadow_page)

            # Monitor current price and trigger withdraw when threshold or balance tolerance is reached
            if current_price and await self.monitor(shadow_page, pool_link, upper_range, lower_range, threshold, current_price, balance_tolerance):
                await self.withdraw(None, shadow_page, pool_link)

                if t[0] != token:
                    reb_order = [t[2], t[0]]
                    token_index = 1
                else:
                    reb_order = [t[0], t[2]]
                    token_index = 0

                amt = (await shadow_page.locator('[class="flex items-center"]').nth(0).text_content()).split(":")[1]
                await self.rebalance(shadow_page, reb_order, amt)

                range_type_index = config.DEFAULT_RANGE_TYPES.index(range_type.lower())
                await self.add_pool_link(update, shadow_page, range_type_index, token_index, amount)

            await asyncio.sleep(5)

    async def monitor(self, shadow_page, pool_link, upper_range, lower_range, threshold, current_price, balance_tolerance):
        """Monitor current price and trigger withdraw when it reaches threshold percentage of range bounds or balance tolerance"""
        
        # Calculate threshold prices
        range_size = upper_range - lower_range
        threshold_distance = (threshold / 100) * range_size
        
        upper_threshold = upper_range - threshold_distance  # Price close to upper bound
        lower_threshold = lower_range + threshold_distance  # Price close to lower bound
        
        # Check if price has reached threshold near upper or lower bound
        if current_price >= upper_threshold or current_price <= lower_threshold:
            return True
            
        # Check if price has reached balance tolerance (distance from center)
        center_price = (upper_range + lower_range) / 2
        balance_distance = (balance_tolerance / 100) * range_size
        
        # If price moves beyond balance tolerance from center, trigger rebalance
        if abs(current_price - center_price) >= balance_distance:
            return True
            
        return False
