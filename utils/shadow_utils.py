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
        """
        Perform 100% withdrawal from a Shadow.so liquidity pool.
        Uses multiple methods to ensure the slider is set to 100%.
        """
        print(f"Starting withdrawal process for pool: {pool_link}")
        
        # Step 1: Click "Decrease Liquidity"
        try:
            decrease_btn = withdraw_page.get_by_role("button", name="Decrease Liquidity")
            await decrease_btn.click()
            await asyncio.sleep(3)
            print("Clicked Decrease Liquidity button")
        except Exception as e:
            print(f"Error clicking Decrease Liquidity: {e}")
            raise
        
        # Step 2: Set to 100% using multiple methods
        await self._set_to_100_percent(withdraw_page)
        
        # Step 3: Wait for Withdraw button to become enabled, then click it
        try:
            withdraw_btn = withdraw_page.get_by_role("button", name="Withdraw")
            
            # Check if button is currently disabled
            is_disabled = await withdraw_btn.is_disabled()
            print(f"Withdraw button disabled status: {is_disabled}")
            
            if is_disabled:
                print("Withdraw button is disabled, waiting for it to become enabled...")
                # Wait up to 60 seconds for the button to become enabled
                try:
                    await withdraw_btn.wait_for(state="attached", timeout=60000)
                    await withdraw_page.wait_for_function(
                        "() => !document.querySelector('button:has-text(\"Withdraw\")').disabled",
                        timeout=60000
                    )
                    print("Withdraw button is now enabled")
                except Exception as wait_error:
                    print(f"Timeout waiting for Withdraw button to enable: {wait_error}")
                    # Try to force-enable it or proceed anyway
                    try:
                        await withdraw_btn.evaluate("button => button.disabled = false")
                        print("Force-enabled the Withdraw button")
                    except:
                        print("Could not force-enable button, proceeding anyway...")
            
            # Now try to click the button
            await withdraw_btn.click()
            await asyncio.sleep(2)
            print("Successfully clicked Withdraw button")
            
        except Exception as e:
            print(f"Error clicking Withdraw: {e}")
            # Try alternative approach - find withdraw button by different selectors
            try:
                print("Trying alternative withdraw button selectors...")
                alt_selectors = [
                    'button:has-text("Withdraw")',
                    '[class*="btn"]:has-text("Withdraw")',
                    'input[type="submit"][value*="Withdraw"]',
                    'button[type="submit"]:has-text("Withdraw")'
                ]
                
                for selector in alt_selectors:
                    try:
                        alt_btn = withdraw_page.locator(selector)
                        if await alt_btn.count() > 0:
                            await alt_btn.first.click()
                            print(f"Successfully clicked withdraw using selector: {selector}")
                            break
                    except:
                        continue
                else:
                    raise Exception("Could not click withdraw button with any method")
                    
            except Exception as final_error:
                print(f"Final withdraw click attempt failed: {final_error}")
                raise
        
        # Step 4: Handle MetaMask confirmation if needed
        # This would be handled by the calling code
        
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
    
    async def _set_to_100_percent(self, page):
        """
        Set the liquidity removal slider to 100% using multiple methods.
        This ensures both the UI button and underlying slider are properly set.
        """
        print("Setting liquidity removal to 100%...")
        
        # Step 1: First try to click the 100% button (from the HTML structure provided)
        button_clicked = False
        hundred_percent_selectors = [
            # Try the exact structure from the HTML
            'div.btn.btn-lg.w-full.cursor-pointer:has-text("100")',
            'div[class*="btn"][class*="cursor-pointer"]:has-text("100")',
            'div[class*="btn-primary"]:has-text("100")',
            # Fallback selectors
            'div:has-text("100%")',
            'button:has-text("100%")',
            '[class*="btn"]:has-text("100%")',
            'div[class*="cursor-pointer"]:has-text("100%")',
            'span:has-text("100%")'
        ]
        
        for selector in hundred_percent_selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()
                print(f"Trying 100% button selector '{selector}': found {count} elements")
                
                if count > 0:
                    # Try each element that matches
                    for i in range(count):
                        try:
                            element = elements.nth(i)
                            if await element.is_visible():
                                text = await element.text_content()
                                print(f"Element {i} text: '{text.strip() if text else 'No text'}'")
                                
                                # Check if this contains "100" (since % might be separate)
                                if text and ("100%" in text.strip() or ("100" in text and "%" in text)):
                                    await element.click()
                                    await asyncio.sleep(2)
                                    print(f"Successfully clicked 100% button using selector: {selector}")
                                    button_clicked = True
                                    break
                        except Exception as e:
                            print(f"Failed to click element {i}: {e}")
                            continue
                    
                    if button_clicked:
                        break
                        
            except Exception as e:
                print(f"100% button selector '{selector}' failed: {e}")
                continue
        
        # Step 2: ALWAYS also set the slider value directly (this is crucial!)
        print("Setting slider value to ensure it's at 100%...")
        try:
            slider = page.locator('input[type="range"]')
            slider_count = await slider.count()
            print(f"Found {slider_count} range sliders")
            
            if slider_count > 0:
                slider_element = slider.first
                
                # Get slider attributes
                max_value = await slider_element.get_attribute('max') or '100'
                min_value = await slider_element.get_attribute('min') or '0'
                current_value = await slider_element.get_attribute('value') or '0'
                
                print(f"Slider - min: {min_value}, max: {max_value}, current: {current_value}")
                
                # Method A: Use fill() to set the value
                await slider_element.fill(max_value)
                await asyncio.sleep(1)
                
                # Method B: Use JavaScript to set value and trigger events
                await slider_element.evaluate(f"""
                    (element) => {{
                        element.value = {max_value};
                        
                        // Trigger all possible events that the UI might listen for
                        element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        element.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                        
                        // Also trigger mouse events in case the UI listens for those
                        element.dispatchEvent(new MouseEvent('mouseup', {{ bubbles: true }}));
                        element.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                    }}
                """)
                await asyncio.sleep(1)
                
                # Method C: Physical interaction - drag to the end
                try:
                    slider_box = await slider_element.bounding_box()
                    if slider_box:
                        # Click at the far right of the slider
                        right_x = slider_box['x'] + slider_box['width'] - 5
                        center_y = slider_box['y'] + slider_box['height'] / 2
                        await page.mouse.click(right_x, center_y)
                        await asyncio.sleep(1)
                        print(f"Clicked slider at position ({right_x}, {center_y})")
                except Exception as e:
                    print(f"Physical slider click failed: {e}")
                
                # Verify the final value
                final_value = await slider_element.get_attribute('value')
                print(f"Final slider value: {final_value} (target was {max_value})")
                
                if final_value == max_value:
                    print(f"✅ Slider successfully set to maximum: {max_value}")
                else:
                    print(f"⚠️ Warning: Slider value {final_value} doesn't match target {max_value}")
                    
        except Exception as e:
            print(f"Slider manipulation failed: {e}")
        
        # Step 3: If nothing worked, try finding any element with exactly "100%"
        if not button_clicked:
            print("Searching for any clickable element with exactly '100%' text...")
            try:
                # Get all potentially clickable elements
                all_elements = await page.locator('*').all()
                
                for i, element in enumerate(all_elements):
                    try:
                        text = await element.text_content()
                        if text and ("100%" in text.strip() or ("100" in text and "%" in text)):
                            if await element.is_visible():
                                print(f"Found 100% match at element {i}: '{text.strip()}'")
                                await element.click()
                                await asyncio.sleep(2)
                                print("Successfully clicked 100% element")
                                button_clicked = True
                                break
                    except Exception:
                        continue
                        
            except Exception as e:
                print(f"Error in final search: {e}")
        
        # Final wait to ensure all UI updates are processed
        await asyncio.sleep(3)
        
        if button_clicked:
            print("✅ Successfully set withdrawal amount to 100%")
        else:
            print("⚠️ Could not click 100% button, but slider should be set to maximum")

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
