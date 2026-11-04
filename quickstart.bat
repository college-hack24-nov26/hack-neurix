@echo off
REM HomeCare+ Quick Start Script for Windows

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║        HomeCare+ Healthcare AI Platform - Quick Start       ║
echo ║                     Version 2.0 (IMPROVED)                  ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if running from correct directory
if not exist "backend" (
    echo ❌ Error: Please run this script from the project root directory
    echo.
    echo Usage: Place this script in homecare-plus-improved folder and run
    pause
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python not found. Please install Python 3.9+
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Node.js not found. Please install Node.js 16+
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Python and Node.js found
echo.

REM Backend Setup
echo [1/5] Setting up Backend...
cd backend
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing Python packages...
pip install -q -r requirements.txt

if not exist ".env" (
    echo.
    echo ⚠️  No .env file found in backend folder
    echo.
    echo Please create backend\.env file with:
    echo.
    echo DATABASE_URL=postgresql+asyncpg://homecare:homecare@localhost:5432/homecare_plus
    echo OPENAI_API_KEY=your_openai_api_key
    echo OPENAI_MODEL=gpt-4o-mini
    echo.
    echo Get API keys from:
    echo - PostgreSQL: https://www.postgresql.org/download/  (or use: docker compose up -d postgres)
    echo - OpenAI: https://platform.openai.com/account/api-keys
    echo.
    pause
    exit /b 1
)

echo ✅ Backend dependencies installed
echo.

REM Frontend Setup
echo [2/5] Setting up Frontend...
cd ../frontend

if not exist "node_modules" (
    echo Installing Node packages (this may take a moment)...
    call npm install -q
)

if not exist ".env" (
    echo Creating frontend .env...
    (
        echo VITE_API_BASE_URL=http://localhost:8000
        echo VITE_APP_NAME=HomeCare+
        echo VITE_DEFAULT_LANGUAGE=en
    ) > .env
)

echo ✅ Frontend dependencies installed
echo.

REM Summary
echo ╔════════════════════════════════════════════════════════════╗
echo ║                    Setup Complete! ✅                       ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📋 Next Steps:
echo.
echo 1️⃣  Start Backend (new terminal):
echo    cd backend
echo    venv\Scripts\activate
echo    python main.py
echo.
echo 2️⃣  Start Frontend (another new terminal):
echo    cd frontend
echo    npm run dev
echo.
echo 3️⃣  Open browser:
echo    http://localhost:5173
echo.
echo 📚 Full Setup Guide: Read SETUP_GUIDE.md
echo.
pause
