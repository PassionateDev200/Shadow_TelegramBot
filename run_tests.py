#!/usr/bin/env python3
"""
Master test runner for Shadow Liquidity Bot
Runs all available tests and provides comprehensive results
"""

import asyncio
import subprocess
import sys
import os
import time
from pathlib import Path

class TestRunner:
    def __init__(self):
        self.results = []
        self.start_time = time.time()
    
    def log_result(self, test_name, success, output="", error=""):
        """Log test result"""
        self.results.append({
            'name': test_name,
            'success': success,
            'output': output,
            'error': error
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        
        if not success and error:
            print(f"    Error: {error}")
    
    async def run_python_test(self, test_name, script_path):
        """Run a Python test script"""
        if not os.path.exists(script_path):
            self.log_result(test_name, False, "", f"Test script not found: {script_path}")
            return False
        
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            success = process.returncode == 0
            self.log_result(
                test_name, 
                success, 
                stdout.decode() if stdout else "",
                stderr.decode() if stderr else ""
            )
            
            return success
            
        except Exception as e:
            self.log_result(test_name, False, "", str(e))
            return False
    
    def run_command_test(self, test_name, command):
        """Run a shell command test"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            self.log_result(
                test_name,
                success,
                result.stdout,
                result.stderr
            )
            
            return success
            
        except subprocess.TimeoutExpired:
            self.log_result(test_name, False, "", "Test timed out")
            return False
        except Exception as e:
            self.log_result(test_name, False, "", str(e))
            return False
    
    def test_environment(self):
        """Test environment setup"""
        print("🔧 Testing Environment Setup...")
        
        # Test Python version
        python_version = sys.version_info
        if python_version >= (3, 10):
            self.log_result("Python Version", True, f"Python {python_version.major}.{python_version.minor}")
        else:
            self.log_result("Python Version", False, "", f"Python {python_version.major}.{python_version.minor} < 3.10")
        
        # Test required files
        required_files = [
            "main.py",
            "config.py",
            "requirements.txt",
            "env.example",
            "bot/commands.py",
            "services/launch_browser.py",
            "utils/logger.py",
            "utils/notifier.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            self.log_result("Required Files", False, "", f"Missing: {', '.join(missing_files)}")
        else:
            self.log_result("Required Files", True, f"All {len(required_files)} files present")
        
        # Test directories
        required_dirs = ["bot", "services", "utils", "models"]
        missing_dirs = [d for d in required_dirs if not os.path.exists(d)]
        
        if missing_dirs:
            self.log_result("Required Directories", False, "", f"Missing: {', '.join(missing_dirs)}")
        else:
            self.log_result("Required Directories", True, f"All {len(required_dirs)} directories present")
    
    def test_dependencies(self):
        """Test Python dependencies"""
        print("\n📦 Testing Dependencies...")
        
        # Test imports
        dependencies = [
            ("telegram", "python-telegram-bot"),
            ("playwright", "playwright"),
            ("asyncio", "built-in"),
            ("logging", "built-in"),
            ("os", "built-in"),
            ("json", "built-in")
        ]
        
        for module, package in dependencies:
            try:
                __import__(module)
                self.log_result(f"Import {module}", True, f"From {package}")
            except ImportError as e:
                self.log_result(f"Import {module}", False, "", f"Missing {package}: {e}")
    
    def test_configuration(self):
        """Test configuration loading"""
        print("\n⚙️ Testing Configuration...")
        
        # Test .env file
        if os.path.exists(".env"):
            self.log_result("Environment File", True, ".env file exists")
        else:
            self.log_result("Environment File", False, "", ".env file not found")
        
        # Test config loading
        try:
            from config import config
            self.log_result("Config Loading", True, "Configuration loaded successfully")
            
            # Test config validation
            errors = config.validate_config()
            if errors:
                self.log_result("Config Validation", False, "", f"Errors: {', '.join(errors)}")
            else:
                self.log_result("Config Validation", True, "No validation errors")
                
        except Exception as e:
            self.log_result("Config Loading", False, "", str(e))
    
    async def run_all_tests(self):
        """Run all available tests"""
        print("🚀 Starting Comprehensive Test Suite")
        print("=" * 60)
        
        # Environment tests
        self.test_environment()
        self.test_dependencies()
        self.test_configuration()
        
        # Python script tests
        print("\n🧪 Running Python Tests...")
        
        python_tests = [
            ("Bot Connection Test", "tests/test_bot_connection.py"),
            ("Integration Test", "tests/test_integration.py"),
        ]
        
        for test_name, script in python_tests:
            await self.run_python_test(test_name, script)
        
        # Compilation tests
        print("\n🔨 Testing Code Compilation...")
        
        compile_tests = [
            ("Compile main.py", "python -m py_compile main.py"),
            ("Compile config.py", "python -m py_compile config.py"),
            ("Compile bot/commands.py", "python -m py_compile bot/commands.py"),
            ("Compile services/launch_browser.py", "python -m py_compile services/launch_browser.py"),
        ]
        
        for test_name, command in compile_tests:
            self.run_command_test(test_name, command)
        
        # Optional tests (don't fail if missing)
        print("\n🔍 Running Optional Tests...")
        
        optional_tests = [
            ("Playwright Installation", "playwright --version"),
            ("Chrome/Edge Detection", "where chrome || where msedge"),
        ]
        
        for test_name, command in optional_tests:
            # These are informational only
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.log_result(test_name, True, result.stdout.strip())
                else:
                    self.log_result(test_name, False, "", "Not found or not working")
            except:
                self.log_result(test_name, False, "", "Could not test")
    
    def print_summary(self):
        """Print comprehensive test summary"""
        total_time = time.time() - self.start_time
        passed = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - passed
        
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        # Group results by category
        categories = {
            "Environment": [],
            "Dependencies": [],
            "Configuration": [],
            "Python Tests": [],
            "Compilation": [],
            "Optional": []
        }
        
        for result in self.results:
            name = result['name']
            if any(x in name for x in ["Python Version", "Required", "Environment File"]):
                categories["Environment"].append(result)
            elif "Import" in name:
                categories["Dependencies"].append(result)
            elif "Config" in name:
                categories["Configuration"].append(result)
            elif "Test" in name and "Compile" not in name:
                categories["Python Tests"].append(result)
            elif "Compile" in name:
                categories["Compilation"].append(result)
            else:
                categories["Optional"].append(result)
        
        for category, results in categories.items():
            if results:
                print(f"\n{category}:")
                for result in results:
                    status = "✅" if result['success'] else "❌"
                    print(f"  {status} {result['name']}")
                    if not result['success'] and result['error']:
                        print(f"      {result['error']}")
        
        print(f"\n📈 Overall Results:")
        print(f"   Total Tests: {len(self.results)}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {failed}")
        print(f"   Success Rate: {passed/len(self.results)*100:.1f}%")
        print(f"   Total Time: {total_time:.1f} seconds")
        
        # Determine overall status
        critical_failures = [r for r in self.results if not r['success'] and any(x in r['name'] for x in [
            "Python Version", "Required Files", "Config Loading", "Bot Connection"
        ])]
        
        if critical_failures:
            print(f"\n❌ CRITICAL FAILURES DETECTED ({len(critical_failures)} issues)")
            print("   The bot cannot run with these issues. Please fix:")
            for failure in critical_failures:
                print(f"   - {failure['name']}: {failure['error']}")
            return False
        elif failed > 0:
            print(f"\n⚠️ SOME TESTS FAILED ({failed} issues)")
            print("   The bot may run but with limited functionality.")
            return True
        else:
            print("\n🎉 ALL TESTS PASSED!")
            print("   The bot is ready for deployment.")
            return True

async def main():
    """Main test runner"""
    runner = TestRunner()
    
    try:
        await runner.run_all_tests()
        success = runner.print_summary()
        
        if not success:
            print("\n🔧 Next Steps:")
            print("1. Fix critical issues listed above")
            print("2. Run tests again: python run_tests.py")
            print("3. Once all tests pass, start the bot: python main.py")
            sys.exit(1)
        else:
            print("\n🚀 Ready to Deploy:")
            print("1. Build executable: python build_exe.py")
            print("2. Or run directly: python main.py")
            print("3. Follow deployment guide for production setup")
            
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 