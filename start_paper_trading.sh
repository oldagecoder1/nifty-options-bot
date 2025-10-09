#!/bin/bash

# Nifty Options Bot - Paper Trading Launcher
# This script starts the bot in Phase 2 (Real data + Paper trading)

echo "=========================================="
echo "🚀 NIFTY OPTIONS BOT - PAPER TRADING"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with your configuration"
    exit 1
fi

# Check if TRADING_PHASE is set to 2
PHASE=$(grep "^TRADING_PHASE=" .env | cut -d'=' -f2)
if [ "$PHASE" != "2" ]; then
    echo "⚠️  Warning: TRADING_PHASE is set to $PHASE"
    echo "For paper trading, it should be 2"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if instruments file exists
if [ ! -f data/instruments.csv ] && [ ! -f data/instruments_06_10.csv ]; then
    echo "⚠️  Warning: No instruments file found!"
    echo "Run: python download_instruments.py"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create logs directory if it doesn't exist
mkdir -p logs
mkdir -p trades

echo "✅ Configuration verified"
echo ""
echo "📊 Starting bot in Paper Trading mode..."
echo "   - Real market data from KiteConnect"
echo "   - No real orders will be placed"
echo "   - All trades logged to trades/ directory"
echo ""
echo "Press Ctrl+C to stop the bot"
echo ""
echo "=========================================="
echo ""

# Start the bot
python main.py

echo ""
echo "=========================================="
echo "🛑 Bot stopped"
echo "=========================================="