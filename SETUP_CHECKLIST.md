# Setup Checklist ✅

Use this checklist to ensure you've set up everything correctly.

## 📁 File Structure

- [ ] Created `nifty-options-bot/` main directory
- [ ] Created subdirectories: `config/`, `data/`, `strategy/`, `execution/`, `backtest/`, `utils/`, `logs/`, `trades/`
- [ ] Created all `__init__.py` files in each subdirectory

## 📄 Core Files Copied

### Root Directory
- [ ] `requirements.txt`
- [ ] `.env` (copied from `.env.example` and edited)
- [ ] `main.py`
- [ ] `run_backtest.py`
- [ ] `README.md`
- [ ] `QUICKSTART.md`

### config/
- [ ] `config/__init__.py`
- [ ] `config/settings.py`

### data/
- [ ] `data/__init__.py`
- [ ] `data/instruments.py`
- [ ] `data/broker_api.py`
- [ ] `data/instruments.csv` (populated with your strikes)

### strategy/
- [ ] `strategy/__init__.py`
- [ ] `strategy/indicators.py`
- [ ] `strategy/reference_levels.py`
- [ ] `strategy/strike_selector.py`
- [ ] `strategy/breakout_logic.py`
- [ ] `strategy/stop_loss.py`

### execution/
- [ ] `execution/__init__.py`
- [ ] `execution/order_manager.py`
- [ ] `execution/paper_trading.py`

### backtest/
- [ ] `backtest/__init__.py`
- [ ] `backtest/backtester.py`

### utils/
- [ ] `utils/__init__.py`
- [ ] `utils/logger.py`
- [ ] `utils/helpers.py`

## 🐍 Python Environment

- [ ] Python 3.8+ installed
- [ ] Virtual environment created (`python -m venv venv`)
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] All imports working (run `python -c "import pandas; import numpy; print('OK')"`)

## ⚙️ Configuration

### .env File Basics
- [ ] `LIVE_TRADING=false` (for paper trading)
- [ ] `STRIKE_OFFSET=200` (or your preferred value)
- [ ] `LOT_SIZE=75` (Nifty lot size)
- [ ] `DAILY_LOSS_LIMIT=10000` (or your risk limit)
- [ ] `TRAILING_INCREMENT=20`
- [ ] `RSI_EXIT_DROP=10`

### Optional (for live trading later)
- [ ] Broker API credentials configured
- [ ] AlgoTest API credentials configured
- [ ] Instruments CSV path verified

## 📊 Data Files

### instruments.csv
- [ ] File exists at `data/instruments.csv`
- [ ] Contains Nifty spot entry (with option_type='INDEX')
- [ ] Contains Call and Put strikes
- [ ] Has columns: symbol, token, strike, expiry, option_type, lot_size
- [ ] Tokens are correct for your broker
- [ ] Expiry dates are valid

### Historical Data (for backtesting)
- [ ] Created sample historical CSV if testing backtest
- [ ] Format matches: datetime, nifty_open, nifty_high, nifty_low, nifty_close, call_open, call_high, call_low, call_close, put_open, put_high, put_low, put_close

## 🧪 Testing

### Syntax Check
```bash
- [ ] python -m py_compile main.py (no errors)
- [ ] python -m py_compile run_backtest.py (no errors)
```

### Import Test
```bash
- [ ] python -c "from config.settings import settings; print('Config OK')"
- [ ] python -c "from data.instruments import instrument_manager; print('Data OK')"
- [ ] python -c "from strategy.breakout_logic import breakout_detector; print('Strategy OK')"
```

### Configuration Test
```bash
- [ ] python -c "from config.settings import settings; settings.print_config()"
```

## 🚀 Ready to Run

### Paper Trading Test
- [ ] Run: `python main.py`
- [ ] Bot starts without errors
- [ ] Configuration prints correctly
- [ ] Console shows trading mode: "📝 PAPER"
- [ ] Bot connects (even if using mock data)
- [ ] Logs created in `logs/` directory

### Backtest Test (Optional)
- [ ] Run: `python run_backtest.py --data sample_historical_data.csv`
- [ ] Backtest runs without errors
- [ ] Results CSV generated
- [ ] Summary printed

## 🔍 Verification

### Directory Structure Check
```bash
tree -L 2 nifty-options-bot/
```

Expected output:
```
nifty-options-bot/
├── backtest/
│   ├── __init__.py
│   └── backtester.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── data/
│   ├── __init__.py
│   ├── broker_api.py
│   ├── instruments.csv
│   └── instruments.py
├── execution/
│   ├── __init__.py
│   ├── order_manager.py
│   └── paper_trading.py
├── logs/
├── main.py
├── README.md
├── requirements.txt
├── run_backtest.py
├── strategy/
│   ├── __init__.py
│   ├── breakout_logic.py
│   ├── indicators.py
│   ├── reference_levels.py
│   ├── stop_loss.py
│   └── strike_selector.py
├── trades/
└── utils/
    ├── __init__.py
    ├── helpers.py
    └── logger.py
```

### File Count Check
```bash
- [ ] Total .py files: 18
- [ ] Total __init__.py files: 6
- [ ] Config files: .env, requirements.txt
- [ ] CSV files: instruments.csv
```

## 🎯 Pre-Flight Checklist (Before First Run)

### Safety Checks
- [ ] `LIVE_TRADING=false` in .env
- [ ] Understand that paper trading uses simulated data
- [ ] Know where logs are saved (`logs/trading.log`)
- [ ] Know where trade logs are saved (`trades/paper_trades_YYYYMMDD.csv`)

### Understanding
- [ ] Read README.md completely
- [ ] Read QUICKSTART.md
- [ ] Understand the strategy flow (Step 1-15)
- [ ] Know how to stop the bot (Ctrl+C)
- [ ] Know how to read the output

### Monitoring
- [ ] Can view live logs: `tail -f logs/trading.log`
- [ ] Can view trade logs: `cat trades/paper_trades_*.csv`
- [ ] Understand the console output format

## ✅ Final Verification

Run this command to verify everything:

```bash
cd nifty-options-bot
python -c "
from config.settings import settings
from data.instruments import instrument_manager
from utils.logger import setup_logger
import sys

print('='*60)
print('SETUP VERIFICATION')
print('='*60)

# Check settings
settings.print_config()

# Check instruments
try:
    inst_mgr = instrument_manager
    print('✅ Instruments manager loaded')
except Exception as e:
    print(f'❌ Instruments error: {e}')
    sys.exit(1)

# Check logger
try:
    logger = setup_logger('test', './logs/test.log', 'INFO')
    logger.info('Test log entry')
    print('✅ Logger working')
except Exception as e:
    print(f'❌ Logger error: {e}')
    sys.exit(1)

print('='*60)
print('✅ ALL CHECKS PASSED!')
print('='*60)
print('You can now run: python main.py')
print('='*60)
"
```

## 🎉 If All Checks Pass

**You're ready to run the bot!**

```bash
# Start paper trading
python main.py

# Or run backtest
python run_backtest.py --data your_data.csv
```

## 🐛 If Something Fails

### Common Issues

**Import errors:**
- Check virtual environment is activated
- Run `pip install -r requirements.txt` again
- Verify all __init__.py files exist

**Config errors:**
- Check .env file exists (not .env.example)
- Verify all required variables are set
- No spaces around = in .env file

**File not found:**
- Check you're in the correct directory
- Verify file paths in .env
- Check instruments.csv exists

**Module not found:**
- Ensure you're running from project root
- Check PYTHONPATH if needed
- Verify directory structure matches checklist

---

## 📞 Getting Help

If you're stuck:

1. Check the error message in console
2. Check logs in `logs/trading.log`
3. Review README.md troubleshooting section
4. Verify you've completed ALL items in this checklist

---

**Good luck with your trading bot! 🚀📈**