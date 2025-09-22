#!/usr/bin/env python3
"""
Build script to create executable for Shadow Liquidity Bot
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_exe():
    """Build the executable using PyInstaller"""
    
    print("🚀 Building Shadow Liquidity Bot executable...")
    
    # Define paths
    project_root = Path(__file__).parent
    main_script = project_root / "main.py"
    
    if not main_script.exists():
        print("❌ Error: main.py not found. Please ensure main.py exists in the project root.")
        return False
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",                    # Create a single executable file
        "--console",                    # Show console window for debugging (change to --windowed to hide)
        "--name=ShadowLiquidityBot",    # Name of the executable
        "--add-data=services;services", # Include services directory
        "--add-data=utils;utils",       # Include utils directory
        "--add-data=models;models",     # Include models directory
        "--add-data=bot;bot",           # Include bot directory
        "--add-data=config.py;.",       # Include config.py file
        "--hidden-import=telegram",
        "--hidden-import=telegram.ext",
        "--hidden-import=telegram.ext.filters",
        "--hidden-import=telegram.ext.updater",
        "--hidden-import=telegram.ext.application",
        "--hidden-import=playwright",
        "--hidden-import=playwright.async_api",
        "--hidden-import=asyncio",
        "--hidden-import=logging",
        "--hidden-import=json",
        "--hidden-import=os",
        "--hidden-import=dataclasses",
        "--hidden-import=python-dotenv",
        "--hidden-import=dotenv",
        "--collect-all=telegram",
        "--collect-all=playwright",
        str(main_script)
    ]
    
    # Remove icon parameter if icon file doesn't exist
    if not (project_root / "icon.ico").exists():
        cmd = [arg for arg in cmd if not arg.startswith("--icon")]
    
    try:
        # Run PyInstaller
        print("📦 Running PyInstaller...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        
        # Show output location
        dist_dir = project_root / "dist"
        exe_file = dist_dir / "ShadowLiquidityBot.exe"
        
        if exe_file.exists():
            print(f"🎉 Executable created: {exe_file}")
            print(f"📁 Size: {exe_file.stat().st_size / (1024*1024):.1f} MB")
        else:
            print("⚠️ Executable not found in expected location")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def clean_build():
    """Clean build artifacts"""
    print("🧹 Cleaning build artifacts...")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    files_to_clean = ["*.spec"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"🗑️ Removed {dir_name}/")
    
    # Remove .spec files
    for spec_file in Path(".").glob("*.spec"):
        spec_file.unlink()
        print(f"🗑️ Removed {spec_file}")

def main():
    """Main build function"""
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_build()
        return
    
    # Install PyInstaller if not available
    try:
        import PyInstaller
    except ImportError:
        print("📦 Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Clean previous builds
    clean_build()
    
    # Build executable
    success = build_exe()
    
    if success:
        print("\n🎉 Build completed successfully!")
        print("📋 Next steps:")
        print("1. Test the executable: ./dist/ShadowLiquidityBot.exe")
        print("2. Copy your .env file to the same directory as the executable")
        print("3. Ensure all required credentials are configured")
    else:
        print("\n❌ Build failed. Please check the error messages above.")

if __name__ == "__main__":
    main() 