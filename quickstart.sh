#!/bin/bash

# HomeCare+ Quick Start Script for Mac/Linux

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        HomeCare+ Healthcare AI Platform - Quick Start       ║"
echo "║                     Version 2.0 (IMPROVED)                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if running from correct directory
if [ ! -d "backend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo ""
    echo "Usage: chmod +x quickstart.sh && ./quickstart.sh"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 not found. Please install Python 3.9+"
    echo "On Mac: brew install python3"
    echo "On Linux: sudo apt install python3"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js not found. Please install Node.js 16+"
    echo "Download from: https://nodejs.org/"
    exit 1
fi

echo "✅ Python and Node.js found"
echo ""

# Backend Setup
echo "[1/5] Setting up Backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing Python packages..."
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found in backend folder"
    echo ""
    echo "Please create backend/.env file with:"
    echo ""
    echo "DATABASE_URL=postgresql+asyncpg://homecare:homecare@localhost:5432/homecare_plus"
    echo "OPENAI_API_KEY=your_openai_api_key"
    echo "OPENAI_MODEL=gpt-4o-mini"
    echo ""
    echo "Get API keys from:"
    echo "- PostgreSQL: https://www.postgresql.org/download/  (or use: docker compose up -d postgres)"
    echo "- OpenAI: https://platform.openai.com/account/api-keys"
    echo ""
    exit 1
fi

echo "✅ Backend dependencies installed"
echo ""

# Frontend Setup
echo "[2/5] Setting up Frontend..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node packages (this may take a moment)..."
    npm install -q
fi

if [ ! -f ".env" ]; then
    echo "Creating frontend .env..."
    cat > .env << EOF
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=HomeCare+
VITE_DEFAULT_LANGUAGE=en
EOF
fi

echo "✅ Frontend dependencies installed"
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete! ✅                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1️⃣  Start Backend (new terminal):"
echo "    cd backend"
echo "    source venv/bin/activate"
echo "    python main.py"
echo ""
echo "2️⃣  Start Frontend (another new terminal):"
echo "    cd frontend"
echo "    npm run dev"
echo ""
echo "3️⃣  Open browser:"
echo "    http://localhost:5173"
echo ""
echo "📚 Full Setup Guide: Read SETUP_GUIDE.md"
echo ""
