#!/usr/bin/env python3
"""
Test script for the updated /list command functionality.
This script tests the Shadow.so dashboard scraping functionality.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.launch_browser import launch_browser
from services.shadow_dashboard import fetch_dashboard_pools

async def test_dashboard_scraping():
    """Test the dashboard scraping functionality"""
    print("🚀 Starting dashboard scraping test...")
    
    try:
        # Launch browser
        print("📱 Launching browser...")
        browser = await launch_browser()
        
        # Navigate to Shadow.so dashboard
        print("🌐 Navigating to Shadow.so dashboard...")
        page = await browser.new_page()
        await page.goto("https://www.shadow.so/liquidity")
        
        # Wait for page to load
        await asyncio.sleep(3)
        
        # Take a screenshot for debugging
        await page.screenshot(path="shadow_dashboard.png")
        print("📸 Screenshot saved as shadow_dashboard.png")
        
        # First, let's debug the page structure
        print("🔍 Debugging page structure...")
        from services.shadow_dashboard import debug_page_structure
        await debug_page_structure(browser)
        
        # Test our scraping function
        print("🔍 Testing pool data extraction...")
        pools = await fetch_dashboard_pools(browser)
        
        print(f"✅ Found {len(pools)} pools")
        
        if not pools:
            print("❌ No pools found. Let's check what elements are on the page...")
            
            # Check for various elements that might contain pool data
            manage_buttons = await page.locator('button:has-text("Manage")').count()
            manage_links = await page.locator('a:has-text("Manage")').count()
            my_pools_text = await page.locator(':has-text("My Pools")').count()
            all_buttons = await page.locator('button').count()
            all_links = await page.locator('a').count()
            
            print(f"   Manage buttons found: {manage_buttons}")
            print(f"   Manage links found: {manage_links}")
            print(f"   'My Pools' text found: {my_pools_text}")
            print(f"   Total buttons on page: {all_buttons}")
            print(f"   Total links on page: {all_links}")
            
            # Get all button texts
            buttons = await page.locator('button').all()
            button_texts = []
            for btn in buttons[:10]:  # First 10 buttons
                text = await btn.text_content()
                if text and text.strip():
                    button_texts.append(text.strip())
            print(f"   Sample button texts: {button_texts}")
        
        for i, pool in enumerate(pools, 1):
            print(f"\n📋 Pool #{i}:")
            print(f"   Pool ID: {pool.get('pool_id', 'N/A')}")
            print(f"   Contract Address: {pool.get('contract_address', 'N/A')}")
            print(f"   Pool Link: {pool.get('pool_link', 'N/A')}")
            print(f"   Tokens: {pool.get('tokens', 'N/A')}")
            print(f"   Liquidity: {pool.get('liquidity', 'N/A')}")
            print(f"   Range: {pool.get('range', 'N/A')}")
            print(f"   Status: {pool.get('status', 'N/A')}")
        
        await browser.close()
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dashboard_scraping()) 