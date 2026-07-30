#!/bin/bash
# V2Ray Shop - Setup Script
# اسکریپت راه‌اندازی فروشگاه کانفیگ V2Ray

set -e

echo "🛡️  V2Ray Shop Setup"
echo "===================="
echo ""

# Check Python
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found! Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Python $PYTHON_VERSION found"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt -q
echo "✅ Dependencies installed"

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.sample .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  Please edit .env file with your settings!"
fi

# Initialize database
echo ""
echo "Initializing database..."
export FLASK_APP=app.py
flask init-db
echo "✅ Database initialized"

# Create sample data
echo ""
echo "Creating sample data..."
flask create-sample-data
echo "✅ Sample data created"

echo ""
echo "===================="
echo "🎉 Setup complete!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  flask run"
echo ""
echo "Then open: http://localhost:5000"
echo ""
echo "Default admin login:"
echo "  Username: admin"
echo "  Password: admin123"
echo "===================="
