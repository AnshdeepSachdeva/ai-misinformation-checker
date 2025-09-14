#!/bin/bash

# Setup script for AI Misinformation Checker

echo "🔍 Setting up AI Misinformation Checker..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file and add your GEMINI_API_KEY"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your GEMINI_API_KEY"
echo "2. Run: source .venv/bin/activate"
echo "3. Run: python app2.py"
echo "4. Open http://127.0.0.1:7862 in your browser"
echo ""
