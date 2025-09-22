#!/usr/bin/env python3
"""
Simple browser launch test
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from services.launch_browser import launch_browser

async def test_browser():
    print("[TEST] Testing browser launch...")
    
    try:
        browser = await launch_browser()
        print(f"[PASS] Browser launched with {len(browser.pages)} pages")
        
        # Check for MetaMask extension
        if browser.service_workers:
            extension_id = browser.service_workers[0].url.split("/")[2]
            print(f"[PASS] MetaMask extension loaded: {extension_id}")
        else:
            print("[WARN] No MetaMask extension found")
        
        await browser.close()
        print("[PASS] Browser closed successfully")
        return True
        
    except Exception as e:
        print(f"[FAIL] Browser test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_browser())
    if success:
        print("[SUCCESS] Browser test completed successfully")
    else:
        print("[ERROR] Browser test failed")
        exit(1) 