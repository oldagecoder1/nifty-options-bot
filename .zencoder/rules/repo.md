---
description: Repository Information Overview
alwaysApply: true
---

# Nifty Options Trading Bot Information

## Summary
An automated intraday options trading bot for Nifty index based on breakout strategy with progressive stop loss and trailing mechanisms. The bot supports paper trading, live trading, and backtesting modes with configurable parameters.

## Structure
- **backtest/**: Backtesting engine implementation
- **config/**: Configuration settings and environment variables
- **data/**: Broker API integration and instrument management
- **execution/**: Order execution and paper trading simulation
- **logs/**: Application logs (auto-created)
- **market_data/**: Stored market data (candles, ticks)
- **strategy/**: Trading strategy components (breakout, reference levels, indicators)
- **trades/**: Trade logs and performance tracking
- **utils/**: Helper utilities for logging, data storage, and candle aggregation

## Language & Runtime
**Language**: Python
**Version**: 3.12.x
**Build System**: None (script-based)
**Package Manager**: pip

## Dependencies
**Main Dependencies**:
- pandas (≥2.1.0): Data manipulation and analysis
- numpy (≥1.26.0): Numerical computing
- kiteconnect (≥4.2.0): Zerodha API integration
- python-dotenv (≥1.0.0): Environment variable management
- websocket-client (≥1.7.0): WebSocket connections
- pytz (≥2023.3): Timezone handling
- ta (≥0.11.0): Technical indicators

**Development Dependencies**:
- matplotlib (≥3.8.0): Visualization for backtesting
- tabulate (≥0.9.0): Formatted table output
- colorlog (≥6.8.0): Colored console logging

## Build & Installation
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Testing
**Framework**: Custom test scripts
**Test Location**: Root directory (test_*.py files)
**Naming Convention**: test_*.py
**Run Command**:
```bash
python test_historical_callbacks.py
python test_candle_windows.py
# etc.
```

## Main Entry Points
**Live/Paper Trading**: main.py
**Backtesting**: run_backtest.py
**Instrument Download**: download_instruments.py
**Token Generation**: generate_token.py, get_kite_token.py

## Configuration
**Environment Variables**: .env file
**Settings Module**: config/settings.py
**Trading Phases**:
- Phase 1: Mock data + Paper trading
- Phase 2: Real KiteConnect data + Paper trading
- Phase 3: Real KiteConnect data + Live trading

## Data Flow
1. **Market Data**: WebSocket connection to Zerodha for real-time ticks
2. **Candle Aggregation**: 1-minute and 5-minute candles from ticks
3. **Reference Levels**: Calculated from 10:00-10:15 AM window
4. **Strike Selection**: Based on Nifty spot price ± offset
5. **Entry/Exit**: Breakout detection, RSI-based exits, stop loss management

## Trading Strategy
- **Reference Window**: 10:00-10:15 AM
- **Strike Selection**: 10:15 AM
- **Entry Conditions**: Breakout + Confirmation
- **Stop Loss**: Progressive (GC/GP → BC/BP → RC/RP → Breakeven)
- **Trailing**: After breakeven, trail by configured increment
- **Exit Conditions**: SL hit, RSI drop, or 3:15 PM hard exit