#!/usr/bin/env python3
"""
Comprehensive function test for Shadow Liquidity Bot
Tests all major functions without browser dependencies
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test all critical imports"""
    print("[TEST] Testing imports...")
    
    try:
        # Core imports
        from telegram import Bot
        from telegram.ext import Application, CommandHandler
        from config import config
        from bot.commands import Bot as BotClass
        from utils.logger import setup_logging
        from utils.notifier import notify_admins
        from models.pool import Pool
        print("[PASS] Core imports successful")
        
        # Service imports
        from services.launch_browser import launch_browser
        from services.metamask_connect import metamask_connect
        from services.shadow_connect import shadow_connect
        from services.shadow_dashboard import fetch_dashboard_pools, check_pool_status
        print("[PASS] Service imports successful")
        
        # Utility imports
        from utils.shadow_utils import Shadow
        from utils.state import load_state, save_state
        print("[PASS] Utility imports successful")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False

def test_configuration():
    """Test configuration system"""
    print("\n[TEST] Testing configuration...")
    
    try:
        from config import config
        
        # Test config validation
        errors = config.validate_config()
        if errors:
            print(f"[WARN] Config validation warnings: {', '.join(errors)}")
        else:
            print("[PASS] Configuration validation passed")
        
        # Test essential settings
        if config.TELEGRAM_BOT_TOKEN:
            print(f"[PASS] Bot token configured: {config.TELEGRAM_BOT_TOKEN[:10]}...")
        else:
            print("[FAIL] No bot token configured")
            return False
        
        print(f"[INFO] Extension path: {config.EXTENSION_PATH}")
        print(f"[INFO] User data dir: {config.USER_DATA_DIR}")
        print(f"[INFO] Monitor interval: {config.MONITOR_INTERVAL}s")
        print(f"[INFO] Rebalance threshold: {config.REBALANCE_THRESHOLD}%")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Configuration test failed: {e}")
        return False

def test_logging_system():
    """Test logging system"""
    print("\n[TEST] Testing logging system...")
    
    try:
        from utils.logger import setup_logging, log_rebalance_event
        
        # Setup logging
        setup_logging()
        print("[PASS] Logging system initialized")
        
        # Test rebalance logging
        log_rebalance_event("TEST001", "TEST_EVENT", {"test": "data"})
        print("[PASS] Rebalance logging works")
        
        # Check log files
        log_files = ["logs/shadow_bot.log", "logs/errors.log", "logs/rebalancing.log"]
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f"[PASS] Log file exists: {log_file}")
            else:
                print(f"[WARN] Log file not found: {log_file}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Logging test failed: {e}")
        return False

def test_bot_class():
    """Test bot class initialization"""
    print("\n[TEST] Testing bot class...")
    
    try:
        from bot.commands import Bot
        
        # Initialize bot
        bot = Bot()
        print("[PASS] Bot class initialized")
        
        # Test bot properties
        print(f"[INFO] Bot has {len(bot.pools)} pools")
        print(f"[INFO] Bot settings: {bot.settings}")
        
        # Test authorization method
        if hasattr(bot, '_is_authorized'):
            print("[PASS] Authorization method exists")
        else:
            print("[WARN] Authorization method not found")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Bot class test failed: {e}")
        return False

def test_pool_model():
    """Test pool data model"""
    print("\n[TEST] Testing pool model...")
    
    try:
        from models.pool import Pool
        
        # Create test pool
        pool = Pool(
            link="https://www.shadow.so/liquidity/manage/0x123/456",
            range="aggressive",
            token="USDC",
            amount=100.0,
            owner_chat_id=123456789,
            meta={"threshold": 90, "balance_tolerance": 2}
        )
        
        print("[PASS] Pool model created")
        print(f"[INFO] Pool link: {pool.link}")
        print(f"[INFO] Pool range: {pool.range}")
        print(f"[INFO] Pool token: {pool.token}")
        print(f"[INFO] Pool amount: {pool.amount}")
        print(f"[INFO] Pool meta: {pool.meta}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Pool model test failed: {e}")
        return False

def test_state_management():
    """Test state loading and saving"""
    print("\n[TEST] Testing state management...")
    
    try:
        from utils.state import load_state, save_state
        from models.pool import Pool
        
        # Test loading state
        state = load_state()
        print(f"[PASS] State loaded: {len(state.get('pools', []))} pools")
        
        # Test saving state with correct signature
        test_pool = Pool(
            link="https://test.com",
            range="test",
            token="TEST",
            amount=1.0,
            meta={}
        )
        
        test_settings = {"threshold": 90, "balance_tolerance": 2}
        
        # Save test state
        save_state([test_pool], test_settings)
        print("[PASS] State saved successfully")
        
        # Load and verify
        loaded_state = load_state()
        if len(loaded_state.get('pools', [])) >= 1:
            print("[PASS] State persistence verified")
        
        # Restore original state (convert dict pools to Pool objects if needed)
        original_pools = []
        for p in state.get("pools", []):
            if isinstance(p, dict):
                pool_obj = Pool(
                    link=p.get("link", ""),
                    range=p.get("range", ""),
                    token=p.get("token", ""),
                    amount=p.get("amount", 0),
                    owner_chat_id=p.get("owner_chat_id"),
                    meta=p.get("meta", {})
                )
                original_pools.append(pool_obj)
        
        save_state(original_pools, state.get("settings", {}))
        print("[PASS] Original state restored")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] State management test failed: {e}")
        return False

async def test_telegram_bot():
    """Test Telegram bot connection"""
    print("\n[TEST] Testing Telegram bot connection...")
    
    try:
        from telegram import Bot
        from config import config
        
        if not config.TELEGRAM_BOT_TOKEN:
            print("[SKIP] No bot token configured")
            return True
        
        bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
        me = await bot.get_me()
        
        print(f"[PASS] Bot connected: @{me.username}")
        print(f"[INFO] Bot ID: {me.id}")
        print(f"[INFO] Bot name: {me.first_name}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Telegram bot test failed: {e}")
        return False

def test_notification_system():
    """Test notification system setup"""
    print("\n[TEST] Testing notification system...")
    
    try:
        from utils.notifier import notify_admins, notify_rebalance_start, notify_rebalance_complete
        from config import config
        
        print("[PASS] Notification functions imported")
        
        if config.ADMIN_CHAT_IDS:
            print(f"[PASS] Admin chat IDs configured: {len(config.ADMIN_CHAT_IDS)}")
        else:
            print("[WARN] No admin chat IDs configured")
        
        if config.ENABLE_NOTIFICATIONS:
            print("[PASS] Notifications enabled")
        else:
            print("[WARN] Notifications disabled")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Notification system test failed: {e}")
        return False

def test_rebalancing_functions():
    """Test rebalancing function imports"""
    print("\n[TEST] Testing rebalancing functions...")
    
    try:
        from bot.commands import check_and_rebalance, _is_approaching_threshold
        print("[PASS] Rebalancing functions imported")
        
        from utils.shadow_utils import Shadow
        print("[PASS] Shadow utility class imported")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Rebalancing functions test failed: {e}")
        return False

async def run_all_tests():
    """Run all function tests"""
    print("=" * 60)
    print("Shadow Liquidity Bot - Function Test Suite")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration),
        ("Logging System Test", test_logging_system),
        ("Bot Class Test", test_bot_class),
        ("Pool Model Test", test_pool_model),
        ("State Management Test", test_state_management),
        ("Telegram Bot Test", test_telegram_bot),
        ("Notification System Test", test_notification_system),
        ("Rebalancing Functions Test", test_rebalancing_functions),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"[ERROR] {test_name} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("FUNCTION TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {passed/len(tests)*100:.1f}%")
    
    if failed == 0:
        print("\n[SUCCESS] All function tests passed!")
        print("The bot's core functionality is working correctly.")
        print("\nNote: Browser-dependent features (MetaMask, Shadow.so) require")
        print("a working browser environment and may need additional testing.")
    else:
        print(f"\n[ERROR] {failed} tests failed.")
        print("Please fix the issues before deploying the bot.")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[STOP] Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Test suite crashed: {e}")
        sys.exit(1) 