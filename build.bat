@echo off
echo 🔧 Creating clean virtual environment...

REM Create virtual environment
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

echo 📦 Installing dependencies in virtual environment...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo 🚀 Building executable...
python build_exe.py

echo ✅ Build complete! Check the dist folder.
pause

