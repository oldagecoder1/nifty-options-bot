# Nifty Options Trading Bot

An automated intraday options trading bot for Nifty based on breakout strategy with progressive stop loss and trailing mechanisms.

## 📋 Features

- ✅ **Automated Strike Selection** - Dynamically selects Call/Put strikes based on spot price
- ✅ **Breakout Detection** - Identifies breakout with confirmation logic
- ✅ **Progressive Stop Loss** - Moves SL through BC → RC → Breakeven
- ✅ **Trailing Stop Loss** - Trails by configured increments after breakeven
- ✅ **RSI Exit** - Exits when RSI drops from peak
- ✅ **Paper Trading Mode** - Simulate trades without real money
- ✅ **Live Trading Mode** - Execute real orders via AlgoTest API
- ✅ **Backtesting** - Validate strategy on historical data
- ✅ **Daily Loss Limit** - Automatic risk management
- ✅ **Comprehensive Logging** - Track all trades and decisions

## 🏗️ Project Structure

```
nifty-options-bot/
├── main.py                   # Live/Paper trading entry point
├── run_backtest.py          # Backtesting entry point
├── requirements.txt         # Python dependencies
├── .env                     # Configuration (create from .env.example)
├── config/
│   ├── __init__.py
│   └── settings.py          # Settings loader
├── data/
│   ├── __init__.py
│   ├── broker_api.py        # Broker API integration
│   ├── instruments.py       # Instrument management
│   └── instruments.csv      # Strike data (you need to create this)
├── strategy/
│   ├── __init__.py
│   ├── reference_levels.py  # Reference level calculation
│   ├── strike_selector.py   # Strike selection logic
│   ├── breakout_logic.py    # Breakout & confirmation
│   ├── stop_loss.py         # SL progression & trailing
│   └── indicators.py        # RSI calculation
├── execution/
│   ├── __init__.py
│   ├── order_manager.py     # AlgoTest API orders
│   └── paper_trading.py     # Paper trading simulation
├── backtest/
│   ├── __init__.py
│   └── backtester.py        # Backtesting engine
├── utils/
│   ├── __init__.py
│   ├── logger.py            # Logging setup
│   └── helpers.py           # Utility functions
├── logs/                    # Log files (auto-created)
└── trades/                  # Trade logs (auto-created)
```

## 🚀 Setup Instructions

### 1. Create Project Structure

```bash
# Create main directory
mkdir nifty-options-bot
cd nifty-options-bot

# Create subdirectories
mkdir -p config data strategy execution backtest utils logs trades

# Create __init__.py files
touch config/__init__.py data/__init__.py strategy/__init__.py
touch execution/__init__.py backtest/__init__.py utils/__init__.py
```

### 2. Copy All Code Files

Copy each artifact from this chat into the corresponding file:
- `requirements.txt` → root directory
- `.env.example` → root directory (rename to `.env` after editing)
- `config/settings.py`
- `utils/logger.py`
- `utils/helpers.py`
- `data/instruments.py`
- `data/broker_api.py`
- `strategy/indicators.py`
- `strategy/reference_levels.py`
- `strategy/strike_selector.py`
- `strategy/breakout_logic.py`
- `strategy/stop_loss.py`
- `execution/order_manager.py`
- `execution/paper_trading.py`
- `backtest/backtester.py`
- `main.py`
- `run_backtest.py`
- `README.md`

### 3. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Create instruments.csv

Create `data/instruments.csv` with your strike data:

```csv
symbol,token,strike,expiry,option_type,lot_size
NIFTY,256265,0,2025-10-10,INDEX,75
NIFTY24OCT20100CE,12345,20100,2024-10-31,CE,75
NIFTY24OCT20100PE,67890,20100,2024-10-31,PE,75
NIFTY24OCT20150CE,12346,20150,2024-10-31,CE,75
NIFTY24OCT20150PE,67891,20150,2024-10-31,PE,75
...
```

**Note:** You need to populate this with real instrument tokens from your broker.

### 5. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use any text editor
```

**Important settings to configure:**

```bash
# Set to false for paper trading, true for live trading
LIVE_TRADING=false

# Strategy parameters (adjust as needed)
STRIKE_OFFSET=200
LOT_SIZE=75
DAILY_LOSS_LIMIT=10000
TRAILING_INCREMENT=20
RSI_EXIT_DROP=10

# Add your broker API credentials
BROKER_API_KEY=your_key_here
BROKER_API_SECRET=your_secret_here
BROKER_ACCESS_TOKEN=your_token_here

# Add AlgoTest API credentials (for live trading)
ALGOTEST_API_KEY=your_algotest_key
ALGOTEST_API_SECRET=your_algotest_secret
```

## 🎮 Running the Bot

### Paper Trading (No Real Money)

```bash
# Make sure LIVE_TRADING=false in .env
python main.py
```

This will:
- Connect to broker for market data
- Execute strategy logic
- Simulate all trades
- Log entries/exits to `trades/paper_trades_YYYYMMDD.csv`
- Show P&L summary at end of day

### Live Trading (Real Money) ⚠️

```bash
# Set LIVE_TRADING=true in .env
python main.py
```

**WARNING:** This will place real orders! Make sure you've tested thoroughly in paper trading first.

### Backtesting

```bash
# Run backtest on historical data
python run_backtest.py --data ./historical_data.csv --start 2024-01-01 --end 2024-12-31
```

**Historical data CSV format:**
```csv
datetime,nifty_open,nifty_high,nifty_low,nifty_close,call_open,call_high,call_low,call_close,put_open,put_high,put_low,put_close
2024-10-01 09:15:00,20300,20320,20295,20310,185,190,180,188,175,180,170,178
2024-10-01 09:16:00,20310,20325,20305,20320,188,195,185,192,178,183,173,180
...
```

## 📊 Output Files

### Paper Trading Logs
- Location: `trades/paper_trades_YYYYMMDD.csv`
- Contains: All entry/exit signals with prices, P&L, reasons

### Backtest Results
- Location: `backtest_results_YYYYMMDD_HHMMSS.csv`
- Contains: All trades with metrics, P&L analysis

### Application Logs
- Location: `logs/trading.log`
- Contains: Detailed execution logs, errors, decisions

## 🔧 Customization

### Modify Strike Offset

Edit `.env`:
```bash
STRIKE_OFFSET=150  # Change from default 200
```

### Adjust Trailing Stop Loss

Edit `.env`:
```bash
TRAILING_INCREMENT=30  # Trail by 30 instead of 20
```

### Change RSI Exit Threshold

Edit `.env`:
```bash
RSI_EXIT_DROP=15  # Exit when RSI drops 15 from peak
```

## 🐛 Troubleshooting

### "Instruments CSV not found"
- Create `data/instruments.csv` with your strike data
- Check the path in `.env`: `INSTRUMENTS_CSV_PATH`

### "Broker connection failed"
- Verify API credentials in `.env`
- Implement actual broker API in `data/broker_api.py`
- Currently uses mock data - integrate your broker's API

### "AlgoTest API error"
- Verify AlgoTest credentials in `.env`
- Implement actual AlgoTest integration in `execution/order_manager.py`
- Currently uses mock responses

### "No data in reference window"
- Ensure market is open (9:15 AM - 3:30 PM IST)
- Check broker API is returning historical data
- Verify time windows in `.env`

## ⚙️ Broker Integration

The code currently uses **MOCK data**. You need to implement actual broker API calls:

### For Zerodha (KiteConnect):

```python
# In data/broker_api.py, replace TODO sections with:
from kiteconnect import KiteConnect, KiteTicker

def connect(self):
    self.kite = KiteConnect(api_key=settings.BROKER_API_KEY)
    self.kite.set_access_token(settings.BROKER_ACCESS_TOKEN)
    
def get_historical_data(self, token, from_datetime, to_datetime, interval):
    data = self.kite.historical_data(
        instrument_token=token,
        from_date=from_datetime,
        to_date=to_datetime,
        interval=interval
    )
    df = pd.DataFrame(data)
    # Process and return
```

### For Angel One (SmartAPI):

```python
# In data/broker_api.py
from smartapi import SmartConnect

def connect(self):
    self.smartApi = SmartConnect(api_key=settings.BROKER_API_KEY)
    # Login and set access token
```

## 📈 Strategy Overview

1. **10:00-10:15**: Calculate reference levels (RN, GN, BN, RC, GC, BC, RP, GP, BP)
2. **10:15**: Select strikes based on Nifty spot ± offset
3. **10:15+**: Monitor for side selection (Nifty candle above RN = CALL, below GN = PUT)
4. **Entry**: Breakout + Confirmation (two green candles above reference high)
5. **Stop Loss**: Starts at GC/GP, progresses to BC/BP → RC/RP → Breakeven
6. **Trailing**: After breakeven, trail by configured increment
7. **Exit**: SL hit, RSI drop, or 3:15 PM hard exit

## 📝 Important Notes

- **Paper Trading First**: Always test in paper trading mode before going live
- **Risk Management**: Set appropriate daily loss limits
- **Market Hours**: Bot only trades during market hours (9:15 AM - 3:30 PM IST)
- **One Position**: Bot maintains maximum one position at a time
- **Broker API**: Implement actual broker API integration (currently uses mocks)
- **AlgoTest**: Configure AlgoTest API for live order execution

## 🤝 Support

For issues or questions:
1. Check logs in `logs/trading.log`
2. Review trade logs in `trades/` directory
3. Verify configuration in `.env`
4. Test with paper trading first

## ⚠️ Disclaimer

This is a trading bot that can place real orders and lose real money. Use at your own risk. Always:
- Test thoroughly in paper trading mode
- Start with small position sizes
- Monitor the bot actively
- Have proper risk management
- Understand the strategy completely

## 📜 License

Use this code at your own risk. No warranties provided.

---

**Happy Trading! 🚀📈**