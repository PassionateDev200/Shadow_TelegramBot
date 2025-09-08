#!/usr/bin/env python3
"""
Test script to verify that the executable setup works correctly.
This script tests directory creation and basic functionality.
"""

import os
import sys
import tempfile
import shutil
from config import Config

def test_directory_creation():
    """Test that all necessary directories are created"""
    print("Testing directory creation...")
    
    # Test config initialization
    config = Config()
    print(f"Base directory: {config.BASE_DIR}")
    print(f"User data directory: {config.USER_DATA_DIR}")
    print(f"Extension path: {config.EXTENSION_PATH}")
    
    # Test directory creation
    config.ensure_directories()
    
    # Verify directories exist
    required_dirs = [
        config.USER_DATA_DIR,
        os.path.join(config.BASE_DIR, 'data'),
    ]
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")
            return False
    
    return True

def test_state_file():
    """Test that state.json is created correctly"""
    print("\nTesting state file creation...")
    
    from utils.state import load_state, save_state
    
    # Load state (should create default if not exists)
    state = load_state()
    print(f"✅ State loaded: {state}")
    
    # Test saving state
    try:
        save_state([], {"threshold": 90, "balance_tolerance": 2})
        print("✅ State saved successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to save state: {e}")
        return False

def test_credential_storage():
    """Test credential storage functionality"""
    print("\nTesting credential storage...")
    
    from bot.commands import Bot
    
    try:
        bot = Bot()
        print("✅ Bot initialized successfully")
        print(f"✅ Found {len(bot.pools)} pools")
        print(f"✅ Settings: {bot.settings}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize bot: {e}")
        return False

if __name__ == "__main__":
    print("=== Executable Test Suite ===")
    
    success = True
    success &= test_directory_creation()
    success &= test_state_file()
    success &= test_credential_storage()
    
    print("\n=== Test Results ===")
    if success:
        print("✅ All tests passed! Executable should work correctly.")
    else:
        print("❌ Some tests failed. Check the issues above.")
    
    sys.exit(0 if success else 1)
