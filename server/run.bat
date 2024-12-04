@echo off
echo Checking environment...

REM Change to server directory
cd server

REM Create venv if it doesn't exist
if not exist .venv (
    echo Virtual environment not found. Creating...
    python -m venv .venv
)

REM Activate venv
call .venv\Scripts\activate.bat

REM Now that we're in venv, check installation and install dependencies if needed
python -c "from modules.install.install import verify_installation, install_dependencies; install_dependencies() if not verify_installation() else None"
if errorlevel 1 (
    echo Failed to install dependencies
    exit /b 1
)

echo Starting server...
python main.py 