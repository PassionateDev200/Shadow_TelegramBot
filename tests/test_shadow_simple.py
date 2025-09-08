"""
Simple test runner for shadow_utils functions without requiring pytest installation.
This can be run directly with Python to test the core functionality.
"""

import asyncio
import sys
import os
import tempfile
import json
from unittest.mock import AsyncMock, MagicMock, patch

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.shadow_utils import Shadow
from models.pool import Pool


async def test_withdraw_basic():
    """Basic test for withdraw function"""
    print("Testing withdraw function...")
    
    # Mock browser and page
    browser = MagicMock()
    shadow = Shadow(browser)
    
    # Mock withdraw page
    withdraw_page = AsyncMock()
    withdraw_page.get_by_role = MagicMock(return_value=AsyncMock())
    
    # Mock state functions
    with patch('utils.shadow_utils.load_state', return_value={"pools": [], "settings": {}}):
        with patch('utils.shadow_utils.save_state'):
            try:
                await shadow.withdraw(None, withdraw_page, "test-pool-link")
                print("✅ Withdraw function executed without errors")
                return True
            except Exception as e:
                print(f"❌ Withdraw function failed: {e}")
                return False


async def test_rebalance_basic():
    """Basic test for rebalance function"""
    print("Testing rebalance function...")
    
    # Mock browser and page
    browser = MagicMock()
    shadow = Shadow(browser)
    
    # Mock trade page
    trade_page = AsyncMock()
    trade_page.goto = AsyncMock()
    trade_page.locator = MagicMock(return_value=AsyncMock())
    trade_page.click = AsyncMock()
    trade_page.fill = AsyncMock()
    
    # Mock swap button
    swap_button = AsyncMock()
    swap_button.is_visible.return_value = True
    trade_page.get_by_role = MagicMock(return_value=swap_button)
    
    try:
        await shadow.rebalance(trade_page, ["SOL", "USDC"], "100")
        print("✅ Rebalance function executed without errors")
        return True
    except Exception as e:
        print(f"❌ Rebalance function failed: {e}")
        return False


async def test_track_basic():
    """Basic test for track function"""
    print("Testing track function...")
    
    # Mock browser with pages
    browser = MagicMock()
    browser.pages = []  # Empty pages to exit loop immediately
    shadow = Shadow(browser)
    
    # Mock shadow page
    shadow_page = AsyncMock()
    shadow_page.goto = AsyncMock()
    shadow_page.locator = MagicMock(return_value=AsyncMock())
    
    # Mock pool data
    pool_data = {
        "link": "test-pool-link",
        "range": "wide",
        "token": "SOL",
        "amount": 100,
        "upper_range": 2.0,
        "lower_range": 1.0
    }
    
    # Mock state data
    state_data = {
        "pools": [pool_data],
        "settings": {"threshold": 90, "balance_tolerance": 2}
    }
    
    with patch('utils.shadow_utils.load_state', return_value=state_data):
        with patch.object(shadow, 'get_pool_data_by_link', return_value=pool_data):
            try:
                await shadow.track(None, shadow_page, "test-pool-link")
                print("✅ Track function executed without errors")
                return True
            except Exception as e:
                print(f"❌ Track function failed: {e}")
                return False


def test_get_pool_data_by_link():
    """Test pool data retrieval function"""
    print("Testing get_pool_data_by_link function...")
    
    browser = MagicMock()
    shadow = Shadow(browser)
    
    # Create test pool data
    pool_data = {
        "link": "test-pool-link",
        "range": "wide",
        "token": "SOL",
        "amount": 100
    }
    
    state_data = {
        "pools": [pool_data],
        "settings": {}
    }
    
    with patch('utils.shadow_utils.load_state', return_value=state_data):
        result = shadow.get_pool_data_by_link("test-pool-link")
        
        if result and result.get("link") == "test-pool-link":
            print("✅ get_pool_data_by_link function working correctly")
            return True
        else:
            print("❌ get_pool_data_by_link function failed")
            return False


async def test_monitor_threshold_logic():
    """Test monitor function threshold logic including balance tolerance"""
    print("Testing monitor threshold logic...")
    
    browser = MagicMock()
    shadow = Shadow(browser)
    
    # Test threshold detection
    upper_range = 2.0
    lower_range = 1.0
    threshold = 90  # 90%
    balance_tolerance = 2  # 2%
    
    # Test case 1: Price very close to upper threshold should trigger (90% means 10% margin)
    current_price = 1.95  # Very close to upper bound (2.0)
    result1 = await shadow.monitor(None, "test-pool", upper_range, lower_range, threshold, current_price, balance_tolerance)
    
    # Test case 2: Price very close to lower threshold should trigger
    current_price = 1.05  # Very close to lower bound (1.0)
    result2 = await shadow.monitor(None, "test-pool", upper_range, lower_range, threshold, current_price, balance_tolerance)
    
    # Test case 3: Price in middle should not trigger threshold (but may trigger balance tolerance)
    current_price = 1.5  # Middle of range
    result3 = await shadow.monitor(None, "test-pool", upper_range, lower_range, threshold, current_price, balance_tolerance)
    
    # Test case 4: Price beyond balance tolerance from center should trigger (2% of range = 0.02)
    current_price = 1.53  # 0.03 away from center (1.5), exceeds 2% tolerance (0.02)
    result4 = await shadow.monitor(None, "test-pool", upper_range, lower_range, threshold, current_price, balance_tolerance)
    
    # Test case 5: Price within balance tolerance should not trigger
    current_price = 1.51  # 0.01 away from center, within 2% tolerance
    result5 = await shadow.monitor(None, "test-pool", upper_range, lower_range, threshold, current_price, balance_tolerance)
    
    if result1 and result2 and not result3 and result4 and not result5:
        print("✅ Monitor threshold and balance tolerance logic working correctly")
        return True
    else:
        print(f"❌ Monitor logic failed: threshold_upper={result1}, threshold_lower={result2}, middle={result3}, balance_tolerance={result4}, close_to_center={result5}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("=== Shadow Utils Test Suite ===")
    
    tests = [
        test_get_pool_data_by_link,
        test_withdraw_basic,
        test_rebalance_basic,
        test_track_basic,
        test_monitor_threshold_logic
    ]
    
    results = []
    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()  # Add spacing between tests
    
    print("=== Test Results ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
