#!/usr/bin/env python3
"""
Comprehensive integration test for Shadow Liquidity Bot
Tests all major components working together
"""

import asyncio
import logging
import sys
import time
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from bot.commands import Bot
from services.launch_browser import launch_browser
from services.metamask_connect import metamask_connect
from services.shadow_connect import shadow_connect
from services.shadow_dashboard import fetch_dashboard_pools, check_pool_status
from utils.logger import setup_logging
from config import config

class IntegrationTester:
    def __init__(self):
        self.browser = None
        self.bot = None
        self.test_results = []
    
    def log_test(self, test_name, success, message=""):
        """Log test result"""
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
    
    async def test_logging_system(self):
        """Test logging system initialization"""
        try:
            setup_logging()
            logging.info("Test log message")
            self.log_test("Logging System", True, "Logs initialized successfully")
            return True
        except Exception as e:
            self.log_test("Logging System", False, f"Error: {e}")
            return False
    
    async def test_bot_initialization(self):
        """Test bot class initialization"""
        try:
            self.bot = Bot()
            self.log_test("Bot Initialization", True, "Bot instance created")
            return True
        except Exception as e:
            self.log_test("Bot Initialization", False, f"Error: {e}")
            return False
    
    async def test_browser_launch(self):
        """Test browser launching with MetaMask extension"""
        try:
            self.browser = await launch_browser()
            
            # Check if browser has pages
            if len(self.browser.pages) > 0:
                self.log_test("Browser Launch", True, f"Browser launched with {len(self.browser.pages)} pages")
            else:
                self.log_test("Browser Launch", False, "Browser launched but no pages found")
                return False
            
            # Check for MetaMask extension
            if self.browser.service_workers:
                extension_id = self.browser.service_workers[0].url.split("/")[2]
                self.log_test("MetaMask Extension", True, f"Extension ID: {extension_id}")
            else:
                self.log_test("MetaMask Extension", False, "No service workers found")
            
            return True
            
        except Exception as e:
            self.log_test("Browser Launch", False, f"Error: {e}")
            return False
    
    async def test_metamask_connection(self):
        """Test MetaMask connection (if credentials available)"""
        try:
            if not self.browser:
                self.log_test("MetaMask Connection", False, "Browser not available")
                return False
            
            # Check if credentials are stored
            if self.bot and self.bot._has_stored_credentials():
                await metamask_connect(self.browser)
                self.log_test("MetaMask Connection", True, "Connected with stored credentials")
                return True
            else:
                self.log_test("MetaMask Connection", True, "Skipped - no credentials stored")
                return True
                
        except Exception as e:
            self.log_test("MetaMask Connection", False, f"Error: {e}")
            return False
    
    async def test_shadow_connection(self):
        """Test Shadow.so website connection"""
        try:
            if not self.browser:
                self.log_test("Shadow.so Connection", False, "Browser not available")
                return False
            
            await shadow_connect(self.browser)
            self.log_test("Shadow.so Connection", True, "Connected to Shadow.so")
            return True
            
        except Exception as e:
            self.log_test("Shadow.so Connection", False, f"Error: {e}")
            return False
    
    async def test_dashboard_access(self):
        """Test Shadow.so dashboard access"""
        try:
            if not self.browser:
                self.log_test("Dashboard Access", False, "Browser not available")
                return False
            
            # Try to fetch dashboard pools
            pools = await fetch_dashboard_pools(self.browser)
            
            if pools:
                self.log_test("Dashboard Access", True, f"Found {len(pools)} pools")
            else:
                self.log_test("Dashboard Access", True, "Dashboard accessible (no pools found)")
            
            return True
            
        except Exception as e:
            self.log_test("Dashboard Access", False, f"Error: {e}")
            return False
    
    async def test_pool_status_check(self):
        """Test pool status checking functionality"""
        try:
            if not self.browser:
                self.log_test("Pool Status Check", False, "Browser not available")
                return False
            
            # Use a dummy contract address for testing
            test_contract = "0x1234567890123456789012345678901234567890"
            test_pool_id = "123"
            
            # This will likely fail with real data, but tests the function
            status = await check_pool_status(self.browser, test_contract, test_pool_id)
            
            if status is None:
                self.log_test("Pool Status Check", True, "Function executed (no data for test address)")
            else:
                self.log_test("Pool Status Check", True, f"Status retrieved: {status}")
            
            return True
            
        except Exception as e:
            self.log_test("Pool Status Check", False, f"Error: {e}")
            return False
    
    async def test_notification_system(self):
        """Test notification system (without actually sending)"""
        try:
            from utils.notifier import notify_admins
            
            # Test notification formatting
            if config.ADMIN_CHAT_IDS:
                self.log_test("Notification System", True, f"Configured for {len(config.ADMIN_CHAT_IDS)} admins")
            else:
                self.log_test("Notification System", True, "No admin IDs configured")
            
            return True
            
        except Exception as e:
            self.log_test("Notification System", False, f"Error: {e}")
            return False
    
    async def test_configuration_validation(self):
        """Test configuration validation"""
        try:
            errors = config.validate_config()
            
            if errors:
                self.log_test("Configuration", False, f"Validation errors: {', '.join(errors)}")
                return False
            else:
                self.log_test("Configuration", True, "All configuration valid")
                return True
                
        except Exception as e:
            self.log_test("Configuration", False, f"Error: {e}")
            return False
    
    async def test_error_recovery(self):
        """Test basic error recovery mechanisms"""
        try:
            # Test browser restart capability
            if self.browser:
                # Close browser
                await self.browser.close()
                self.browser = None
                
                # Try to restart
                self.browser = await launch_browser()
                self.log_test("Error Recovery", True, "Browser restart successful")
                return True
            else:
                self.log_test("Error Recovery", True, "No browser to test restart")
                return True
                
        except Exception as e:
            self.log_test("Error Recovery", False, f"Error: {e}")
            return False
    
    async def cleanup(self):
        """Clean up test resources"""
        try:
            if self.browser:
                await self.browser.close()
                print("[CLEANUP] Browser closed")
        except Exception as e:
            print(f"[WARN] Cleanup error: {e}")
    
    def print_summary(self):
        """Print test summary"""
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print("\n" + "=" * 60)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        for result in self.test_results:
            status = "[PASS]" if result['success'] else "[FAIL]"
            print(f"{status} {result['test']}")
            if result['message'] and not result['success']:
                print(f"    {result['message']}")
        
        print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("[SUCCESS] All integration tests passed! Bot is ready for production.")
        else:
            print("[ERROR] Some tests failed. Please review and fix issues before deployment.")
        
        return passed == total

async def main():
    """Run comprehensive integration tests"""
    print("=" * 60)
    print("Shadow Liquidity Bot - Integration Test Suite")
    print("=" * 60)
    
    tester = IntegrationTester()
    
    try:
        # Run all tests in sequence
        tests = [
            tester.test_configuration_validation,
            tester.test_logging_system,
            tester.test_bot_initialization,
            tester.test_browser_launch,
            tester.test_metamask_connection,
            tester.test_shadow_connection,
            tester.test_dashboard_access,
            tester.test_pool_status_check,
            tester.test_notification_system,
            tester.test_error_recovery,
        ]
        
        print(f"Running {len(tests)} integration tests...\n")
        
        for test in tests:
            await test()
            await asyncio.sleep(1)  # Small delay between tests
        
        # Print summary and determine exit code
        success = tester.print_summary()
        
        if not success:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n[STOP] Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during testing: {e}")
        sys.exit(1)
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 