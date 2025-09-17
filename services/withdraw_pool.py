import asyncio
from utils.shadow_utils import Shadow
from config import config
from utils.check_for_url import check_for_url

async def withdraw_pool(update, browser, pool_link, percentage):
    """
    Withdraw liquidity from a Shadow pool
    
    Args:
        update: Telegram update object
        browser: Browser instance
        pool_link: Pool link to withdraw from
        percentage: Percentage to withdraw (1-100)
    
    Returns:
        bool: True if withdrawal was successful, False otherwise
    """
    withdraw_page = None
    try:
        await update.message.reply_text("Navigating to pool management page...")
        
        # Navigate to the pool's manage page
        # Convert pool link to manage page URL
        # Example: https://www.shadow.so/liquidity/0x123... -> https://www.shadow.so/liquidity/manage/0x123...
        if "/manage/" not in pool_link:
            # Extract the pool ID from the link
            pool_id = pool_link.split("/")[-1]
            manage_url = pool_link.replace(f"/{pool_id}", f"/manage/{pool_id}")
        else:
            manage_url = pool_link
        
        # Open new page for withdrawal
        withdraw_page = await browser.new_page()
        await withdraw_page.goto(manage_url)
        await withdraw_page.wait_for_load_state("networkidle", timeout=120000)
        
        await update.message.reply_text("Connecting to Shadow...")
        
        # Check if we need to connect wallet
        connect_btn = withdraw_page.locator("button:has-text('Connect Wallet')").first
        if await connect_btn.is_visible():
            await connect_btn.click()
            await asyncio.sleep(2)
            
            # Click MetaMask option
            metamask_btn = withdraw_page.locator("data-testid=rk-wallet-option-io.metamask")
            if await metamask_btn.is_visible():
                await metamask_btn.click()
                await asyncio.sleep(2)
        
        # Check if we need to sign in
        signin_btn = withdraw_page.get_by_role("button", name="Sign-in")
        if await signin_btn.is_visible():
            await signin_btn.click()
            await asyncio.sleep(2)
        
        # Check if we need to switch network
        network_btn = withdraw_page.get_by_role("button", name="Wrong Network")
        if await network_btn.is_visible():
            await network_btn.click()
            await asyncio.sleep(2)
        
        await update.message.reply_text("Performing withdrawal...")
        
        # Create Shadow instance and perform withdrawal
        shadow = Shadow(browser)
        
        # Handle percentage-based withdrawal
        if percentage < 100:
            # For partial withdrawal, we need to set the percentage first
            # Look for percentage input or buttons
            try:
                # Try to find percentage input field
                percentage_input = withdraw_page.locator('input[type="number"], input[placeholder*="%"], input[placeholder*="percent"]').first
                print("============================percentage_input================= ", percentage_input)
                if await percentage_input.is_visible():
                    await percentage_input.fill(str(percentage))
                    await asyncio.sleep(1)
                else:
                    # Try to find percentage buttons (25%, 50%, 75%, 100%)
                    percentage_buttons = {
                        25: withdraw_page.get_by_role("button", name="25%"),
                        50: withdraw_page.get_by_role("button", name="50%"),
                        75: withdraw_page.get_by_role("button", name="75%"),
                        100: withdraw_page.get_by_role("button", name="100%")
                    }
                    # Find closest percentage button
                    closest_percentage = min(percentage_buttons.keys(), key=lambda x: abs(x - percentage))
                    print("============================closest_percentage================= ", closest_percentage)
                    if closest_percentage in percentage_buttons:
                        btn = percentage_buttons[closest_percentage]
                        if await btn.is_visible():
                            await btn.click()
                            await asyncio.sleep(1)
                            await update.message.reply_text(f"Selected {closest_percentage}% (closest to requested {percentage}%)")
            except Exception as e:
                await update.message.reply_text(f"Warning: Could not set specific percentage, proceeding with default withdrawal")
        
        # Perform the withdrawal using the existing withdraw method
        await shadow.withdraw(update, withdraw_page, pool_link)
        
        await update.message.reply_text("✅ Withdrawal completed successfully!")
        return True
        
    except Exception as e:
        await update.message.reply_text(f"❌ Withdrawal failed: {str(e)}")
        return False
        
    finally:
        # Close the withdraw page
        if withdraw_page:
            try:
                await withdraw_page.close()
            except Exception:
                pass

