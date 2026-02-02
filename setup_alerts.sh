#!/bin/bash

# Low Stock Alert System - Setup Script
# This script helps you quickly set up the low stock alert system

echo "🚀 Low Stock Alert System Setup"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created. Please edit it with your credentials."
    echo ""
    echo "Required configurations:"
    echo "  - EMAIL_SENDER: Your Gmail address"
    echo "  - EMAIL_PASSWORD: Gmail App Password (not regular password)"
    echo "  - TWILIO_* (optional): For WhatsApp notifications"
    echo ""
else
    echo "✅ .env file already exists"
fi

# Check Python version
echo "🐍 Checking Python version..."
python3 --version

# Install requirements
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo ""
echo "🗄️ Running database migrations..."
alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your email and Twilio credentials"
echo "2. Run: uvicorn app.main:app --reload"
echo "3. Test the API at http://localhost:8000/docs"
echo ""
echo "To test the alert system:"
echo "1. Create a user and log in"
echo "2. Update preferences: PUT /alerts/preferences/update"
echo "3. Create an item with quantity 100"
echo "4. Update item quantity to 3: PUT /items/{id}"
echo "5. Check your email and WhatsApp!"
echo ""
echo "Documentation: See LOW_STOCK_ALERT_SYSTEM.md"
