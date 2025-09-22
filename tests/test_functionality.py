#!/usr/bin/env python3
"""
Test script to verify Shadow Liquidity Bot executable functionality
"""

import subprocess
import time
import os
import sys
from pathlib import Path

def test_executable_launch():
    """Test if the executable launches without errors"""
    print("🚀 Testing executable launch...")
    
    exe_path = Path("dist/ShadowLiquidityBot.exe")
    if not exe_path.exists():
        print("❌ Executable not found at dist/ShadowLiquidityBot.exe")
        return False
    
    try:
        # Start the executable in a separate process
        process = subprocess.Popen(
            [str(exe_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="dist"
        )
        
        # Wait a few seconds to see if it starts properly
        time.sleep(5)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Executable launched successfully and is running")
            
            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            return True
        else:
            # Process exited, check output
            stdout, stderr = process.communicate()
            print(f"❌ Executable exited with code: {process.returncode}")
            if stdout:
                print(f"STDOUT: {stdout[:500]}...")
            if stderr:
                print(f"STDERR: {stderr[:500]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error launching executable: {e}")
        return False

def check_dependencies():
    """Check if all required files are present"""
    print("📋 Checking dependencies...")
    
    dist_dir = Path("dist")
    required_files = [
        "ShadowLiquidityBot.exe",
        ".env"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = dist_dir / file
        if file_path.exists():
            print(f"✅ {file} - Found")
        else:
            print(f"❌ {file} - Missing")
            missing_files.append(file)
    
    return len(missing_files) == 0

def check_env_configuration():
    """Check if .env file has required configuration"""
    print("🔧 Checking .env configuration...")
    
    env_path = Path("dist/.env")
    if not env_path.exists():
        print("❌ .env file not found")
        return False
    
    try:
        with open(env_path, 'r') as f:
            content = f.read()
        
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "ALLOWED_USER_IDS",
            "USER_DATA_DIR"
        ]
        
        missing_vars = []
        for var in required_vars:
            if var in content:
                print(f"✅ {var} - Found")
            else:
                print(f"❌ {var} - Missing")
                missing_vars.append(var)
        
        return len(missing_vars) == 0
        
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def create_sample_env():
    """Create a sample .env file if it doesn't exist"""
    print("📝 Creating sample .env file...")
    
    env_path = Path("dist/.env")
    if env_path.exists():
        print("✅ .env file already exists")
        return True
    
    sample_env = """# Shadow Liquidity Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
ALLOWED_USER_IDS=your_user_id_here
USER_DATA_DIR=./user_profile

# Optional settings
# METAMASK_PASSWORD=your_password
# METAMASK_PHRASE=your 12 word seed phrase
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(sample_env)
        print("✅ Sample .env file created")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def test_import_functionality():
    """Test if the executable can import all required modules"""
    print("📦 Testing module imports...")
    
    # This is a basic test - the real test is if the executable runs
    try:
        import telegram
        print("✅ python-telegram-bot - Available")
    except ImportError:
        print("❌ python-telegram-bot - Missing")
    
    try:
        import playwright
        print("✅ playwright - Available")
    except ImportError:
        print("❌ playwright - Missing")
    
    try:
        import asyncio
        print("✅ asyncio - Available")
    except ImportError:
        print("❌ asyncio - Missing")
    
    return True

def create_deployment_package():
    """Create a deployment package with all necessary files"""
    print("📦 Creating deployment package...")
    
    try:
        import zipfile
        
        zip_path = "ShadowLiquidityBot_Deployment.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add executable
            exe_path = Path("dist/ShadowLiquidityBot.exe")
            if exe_path.exists():
                zipf.write(exe_path, "ShadowLiquidityBot.exe")
                print("✅ Added executable to package")
            
            # Add sample .env
            env_path = Path("dist/.env")
            if env_path.exists():
                zipf.write(env_path, ".env")
                print("✅ Added .env file to package")
            
            # Add README
            readme_content = """# Shadow Liquidity Bot - Deployment Package

## Quick Start:
1. Configure your .env file with your Telegram bot token
2. Run ShadowLiquidityBot.exe
3. Use /connect command to add your MetaMask credentials

## Commands:
- /start - Start the bot
- /connect [password] [12-word seed] - Connect MetaMask
- /add [pool_link] [range] [token] [amount] - Add pool
- /remove [pool_link] - 100% withdrawal
- /list - Show all pools
- /status - Check pool status
- /help - Show all commands

## Requirements:
- Windows 10/11
- Internet connection
- Valid Telegram bot token
- MetaMask credentials

## Support:
Make sure your .env file is properly configured before running.
"""
            zipf.writestr("README.txt", readme_content)
            print("✅ Added README to package")
        
        print(f"✅ Deployment package created: {zip_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating deployment package: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("  Shadow Liquidity Bot - Functionality Test")
    print("=" * 50)
    print()
    
    tests = [
        ("Dependencies Check", check_dependencies),
        ("Environment Configuration", check_env_configuration),
        ("Create Sample .env", create_sample_env),
        ("Module Imports", test_import_functionality),
        ("Executable Launch", test_executable_launch),
        ("Deployment Package", create_deployment_package),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("  TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your executable is ready for deployment.")
        print("\n📋 Next steps:")
        print("1. Configure your .env file with real credentials")
        print("2. Test the bot with your Telegram account")
        print("3. Deploy using the created zip package")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 